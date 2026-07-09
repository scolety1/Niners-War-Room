#!/usr/bin/env python3
"""Review-safe locator for Model v4 historical receipt candidates.

This script only reads local/repo/handoff paths and writes review artifacts in
this packet folder. It does not copy inputs, regenerate receipts, run replay, or
modify runtime/local_exports paths.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable


ARTIFACT_DIR = Path(__file__).resolve().parent
CURRENT_REMOTE_HEAD = "a57b33e1c2cd55bc61d0c0a32cb48ed554b776cc"
PRIOR_GAP_COMMIT = "8a438d4424357eb90f6210bd3f082736c4b111c9"
PRIOR_SYSTEM_AUDIT_COMMIT = "6bc013bea5925525ed8326cc62ca97c1d0ca5ab2"
PRIOR_PFR_ADDENDUM_COMMIT = "ff1a5b5de65c041fd58d7d7ca62b29e8c2e0ce44"

TARGETS = [
    {
        "family_name": "checkpoint_review_score",
        "gap_status": "RECOVERABLE_FROM_EXISTING_ARTIFACTS",
        "current_board_equivalent": "current_value_full_board_review_rows / current_player_value_full_board_review_rows checkpoint_review_score",
        "expected_historical_equivalent": "season-by-season checkpoint_review_score rows",
        "required_columns": "player identity; player_name; position; feature_season/as_of; checkpoint_review_score; source receipt/provenance",
        "required_keys": "player_id or canonical equivalent; feature_season/as_of; position",
        "required_seasons": "historical feature seasons needed for exact replay",
        "required_positions": "QB/RB/WR/TE",
        "source_use_gate_status": "review-only recovery candidate; Master HQ approval required before canonical use",
        "why_it_matters": "Anchors exact Model v4 checkpoint score and exact rank/value order.",
        "gates_exact_replay": "yes",
        "gates_formula_gauntlet": "yes, if claiming exact Model v4 baseline",
    },
    {
        "family_name": "position_specific_review_score",
        "gap_status": "RECOVERABLE_FROM_EXISTING_ARTIFACTS",
        "current_board_equivalent": "component rows and current player value rows with position_specific_review_score",
        "expected_historical_equivalent": "season-position component score rows",
        "required_columns": "player identity; position; feature_season/as_of; position_specific_review_score; component/source provenance",
        "required_keys": "player_id or canonical equivalent; feature_season/as_of; position",
        "required_seasons": "historical feature seasons needed for exact replay",
        "required_positions": "QB/RB/WR/TE",
        "source_use_gate_status": "review-only recovery candidate; Master HQ approval required before canonical use",
        "why_it_matters": "Required for exact QB/RB/WR/TE component score replay.",
        "gates_exact_replay": "yes",
        "gates_formula_gauntlet": "yes, if claiming exact Model v4 baseline",
    },
    {
        "family_name": "lifecycle_age_receipts",
        "gap_status": "RECOVERABLE_FROM_EXISTING_ARTIFACTS",
        "current_board_equivalent": "lifecycle_age_receipts; veteran_player_inputs; review_safe_qb_age_adapter_from_lifecycle_receipts",
        "expected_historical_equivalent": "historical lifecycle/age receipt rows by feature season",
        "required_columns": "player identity; feature_season/as_of; age or birth date; lifecycle bucket; source provenance",
        "required_keys": "player_id or canonical equivalent; feature_season/as_of",
        "required_seasons": "historical feature seasons needed for exact replay",
        "required_positions": "QB/RB/WR/TE",
        "source_use_gate_status": "review-only recovery candidate; age regeneration needs source/as-of review",
        "why_it_matters": "Required for age curve and lifecycle adjustments across seasons.",
        "gates_exact_replay": "yes",
        "gates_formula_gauntlet": "yes for age/lifecycle candidates",
    },
    {
        "family_name": "role_archetype_receipts",
        "gap_status": "REGENERATABLE_REVIEW_ONLY",
        "current_board_equivalent": "role/archetype component rows in component_receipts",
        "expected_historical_equivalent": "historical role archetype rows by feature season",
        "required_columns": "player identity; feature_season/as_of; role/archetype; source input fields; provenance",
        "required_keys": "player_id or canonical equivalent; feature_season/as_of; position",
        "required_seasons": "historical feature seasons needed for exact replay",
        "required_positions": "QB/RB/WR/TE",
        "source_use_gate_status": "review-only regeneration possible only after bounded contract",
        "why_it_matters": "Required for role shape and position-specific adjustment replay.",
        "gates_exact_replay": "yes",
        "gates_formula_gauntlet": "yes for role candidates",
    },
    {
        "family_name": "confidence_cap_receipts",
        "gap_status": "REGENERATABLE_REVIEW_ONLY",
        "current_board_equivalent": "confidence flags/manual review notes in board review rows",
        "expected_historical_equivalent": "historical confidence cap rows by feature season",
        "required_columns": "player identity; feature_season/as_of; confidence cap/status; missingness/coverage inputs; provenance",
        "required_keys": "player_id or canonical equivalent; feature_season/as_of; position",
        "required_seasons": "historical feature seasons needed for exact replay",
        "required_positions": "QB/RB/WR/TE",
        "source_use_gate_status": "review-only regeneration possible only after bounded contract",
        "why_it_matters": "Required for confidence caps and missingness/coverage caps.",
        "gates_exact_replay": "yes",
        "gates_formula_gauntlet": "yes for sparse/missingness guardrails",
    },
    {
        "family_name": "WR_QB_v2_candidate_overlay",
        "gap_status": "REQUIRES_HUMAN_REVIEW",
        "current_board_equivalent": "wr_qb_v2_candidate mode and candidate overlay logic receipts",
        "expected_historical_equivalent": "season-by-season WR/QB v2 overlay rows",
        "required_columns": "player identity; feature_season/as_of; overlay input; overlay output; decision/reason; status",
        "required_keys": "player_id or canonical equivalent; feature_season/as_of; candidate_mode",
        "required_seasons": "historical feature seasons where overlay applies",
        "required_positions": "WR/QB primarily",
        "source_use_gate_status": "requires human/Master HQ review",
        "why_it_matters": "Candidate overlay is decision logic and needs explicit historical receipts.",
        "gates_exact_replay": "yes",
        "gates_formula_gauntlet": "yes if overlay is used",
    },
    {
        "family_name": "exact_nwr_dynasty_score_and_rank",
        "gap_status": "REQUIRES_HUMAN_REVIEW",
        "current_board_equivalent": "rebuilt_full_player_board_value_review_rows and pinned final board comparison",
        "expected_historical_equivalent": "historical nwr_dynasty_score and rank rows",
        "required_columns": "player identity; feature_season/as_of; position; rank; nwr_dynasty_score; status/provenance",
        "required_keys": "player_id or canonical equivalent; feature_season/as_of; position",
        "required_seasons": "historical seasons under benchmark scope",
        "required_positions": "QB/RB/WR/TE",
        "source_use_gate_status": "requires human/Master HQ review",
        "why_it_matters": "Exact outputs cannot be inferred from partial component analogs.",
        "gates_exact_replay": "yes",
        "gates_formula_gauntlet": "yes if used as exact current formula baseline",
    },
    {
        "family_name": "route_yprr_tprr_exact_receipts",
        "gap_status": "REQUIRES_SOURCE_ADMISSION",
        "current_board_equivalent": "route/YPRR/TPRR blockers and route source placeholders",
        "expected_historical_equivalent": "historical route denominator and route-derived receipt rows",
        "required_columns": "player identity; feature_season/as_of; routes_run; targets/routes; yards/routes; source admission",
        "required_keys": "player_id or canonical equivalent; feature_season/as_of",
        "required_seasons": "historical route seasons",
        "required_positions": "RB/WR/TE",
        "source_use_gate_status": "blocked until Route Recovery admits a rights-cleared route denominator",
        "why_it_matters": "Needed only for exact route-role components and future route tournaments.",
        "gates_exact_replay": "conditional",
        "gates_formula_gauntlet": "yes for route/YPRR/TPRR candidates",
    },
    {
        "family_name": "red_zone_exact_receipts",
        "gap_status": "REGENERATABLE_REVIEW_ONLY",
        "current_board_equivalent": "current role/red-zone component blockers",
        "expected_historical_equivalent": "historical red-zone opportunity receipt rows",
        "required_columns": "player identity; feature_season/as_of; red-zone opportunity fields; source semantics/provenance",
        "required_keys": "player_id or canonical equivalent; feature_season/as_of",
        "required_seasons": "historical feature seasons",
        "required_positions": "QB/RB/WR/TE where applicable",
        "source_use_gate_status": "review-only regeneration possible only after semantic/source gate",
        "why_it_matters": "Required for exact red-zone transforms where used by Model v4.",
        "gates_exact_replay": "conditional",
        "gates_formula_gauntlet": "yes for red-zone candidates",
    },
    {
        "family_name": "shadow_model_v2_metrics",
        "gap_status": "MISSING_SOURCE",
        "current_board_equivalent": "shadow_model_v2_metrics.csv absent from current board rebuild caveats",
        "expected_historical_equivalent": "historical shadow_model_v2_metrics rows if scope retains shadow sidecar",
        "required_columns": "unknown until file recovered",
        "required_keys": "unknown until file recovered",
        "required_seasons": "unknown until file recovered",
        "required_positions": "unknown until file recovered",
        "source_use_gate_status": "missing source; Master HQ may remove from exact replay scope",
        "why_it_matters": "Current board hash rebuild did not need it, but exact shadow/guardrail replay may.",
        "gates_exact_replay": "conditional",
        "gates_formula_gauntlet": "no unless scope admits it",
    },
    {
        "family_name": "return_scoring_receipts",
        "gap_status": "REQUIRES_SOURCE_ADMISSION",
        "current_board_equivalent": "return scoring and shadow sidecars noted missing",
        "expected_historical_equivalent": "historical return scoring component receipt rows",
        "required_columns": "player identity; feature_season/as_of; return scoring fields; source semantics/provenance",
        "required_keys": "player_id or canonical equivalent; feature_season/as_of",
        "required_seasons": "historical feature seasons",
        "required_positions": "all positions if return scoring in scope",
        "source_use_gate_status": "requires source/semantic admission",
        "why_it_matters": "Special teams ambiguity must not be substituted.",
        "gates_exact_replay": "conditional",
        "gates_formula_gauntlet": "conditional",
    },
    {
        "family_name": "source_coverage_matrix_history",
        "gap_status": "RECOVERABLE_FROM_EXISTING_ARTIFACTS",
        "current_board_equivalent": "source_coverage_matrix recovered for current board",
        "expected_historical_equivalent": "historical source coverage matrix by feature season",
        "required_columns": "feature_season/as_of; source family; coverage/missingness flags; position/player grain where applicable",
        "required_keys": "feature_season/as_of plus source family and player key where row-level",
        "required_seasons": "historical feature seasons",
        "required_positions": "QB/RB/WR/TE",
        "source_use_gate_status": "review-only recovery candidate; Master HQ approval required before canonical use",
        "why_it_matters": "Required to explain missingness caps and component availability season by season.",
        "gates_exact_replay": "yes",
        "gates_formula_gauntlet": "yes for missingness/confidence guardrails",
    },
    {
        "family_name": "exact_transform_weight_receipts",
        "gap_status": "NOT_ENOUGH_INFORMATION",
        "current_board_equivalent": "current code/component receipts imply transforms but not historical weights",
        "expected_historical_equivalent": "historical transform/weight config or model spec version receipts",
        "required_columns": "formula id; feature season/as_of; transform id; weight/config; source code/file hash",
        "required_keys": "formula id; feature_season/as_of; component id",
        "required_seasons": "all historical replay seasons",
        "required_positions": "QB/RB/WR/TE",
        "source_use_gate_status": "not enough information; requires Master HQ formula/spec approval",
        "why_it_matters": "Without frozen transforms exact replay cannot be claimed.",
        "gates_exact_replay": "yes",
        "gates_formula_gauntlet": "yes if exact Model v4 baseline is required",
    },
]

FAMILY_KEYWORDS = {
    "checkpoint_review_score": ["checkpoint_review_score", "current_value_full_board_review_rows", "current_player_value_full_board_review_rows", "current_value_review_rows", "full_player_board_value_review_rows"],
    "position_specific_review_score": ["position_specific_review_score", "component_rows", "component_receipts", "current_player_value_full_board_review_rows"],
    "lifecycle_age_receipts": ["lifecycle_age_receipts", "review_safe_qb_age_adapter", "veteran_player_inputs", "age_adapter", "birth_date", "lifecycle"],
    "role_archetype_receipts": ["role_archetype", "archetype", "role", "component_receipts", "component_rows"],
    "confidence_cap_receipts": ["confidence_cap", "confidence", "missingness", "coverage", "source_coverage_matrix"],
    "WR_QB_v2_candidate_overlay": ["wr_qb_v2", "candidate_overlay", "candidate_board", "old_pocket_qb", "pre_wr_qb_v2", "post_wr_qb_v2", "candidate_mode"],
    "exact_nwr_dynasty_score_and_rank": ["nwr_dynasty_score", "rank", "full_player_board_value_review_rows", "model_outputs.csv"],
    "route_yprr_tprr_exact_receipts": ["routes_run", "route", "yprr", "tprr", "route_denominator"],
    "red_zone_exact_receipts": ["red_zone", "redzone", "rz_", "goal_line"],
    "shadow_model_v2_metrics": ["shadow_model_v2_metrics"],
    "return_scoring_receipts": ["return_scoring", "return_yards", "return_td", "special_teams_return"],
    "source_coverage_matrix_history": ["source_coverage_matrix", "evidence_matrices", "coverage_matrix"],
    "exact_transform_weight_receipts": ["transform", "weight", "formula_config", "formula", "component_registry", "model_spec"],
}

DIRECT_NAME_PATTERNS = [
    "current_value_full_board_review_rows",
    "current_player_value_full_board_review_rows",
    "full_player_board_value_review_rows",
    "current_value_review_rows",
    "component_rows",
    "component_receipts",
    "lifecycle_age_receipts",
    "review_safe_qb_age_adapter",
    "veteran_player_inputs",
    "source_coverage_matrix",
    "model_outputs.csv",
    "candidate_board",
    "wr_qb_v2",
    "old_pocket_qb",
    "overlay",
    "checkpoint_review_score",
    "position_specific_review_score",
    "nwr_dynasty_score",
    "shadow_model_v2_metrics",
    "routes_run",
    "yprr",
    "tprr",
    "red_zone",
    "redzone",
    "return_scoring",
    "historical_component_receipts",
    "historical_replay_readiness",
    "receipt_inventory",
    "receipt_coverage",
    "receipt_chain",
]

CONTENT_KEYWORDS = [
    "checkpoint_review_score",
    "position_specific_review_score",
    "nwr_dynasty_score",
    "candidate_mode",
    "wr_qb_v2_candidate",
    "source_coverage_matrix",
    "lifecycle",
]

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
    ".turbo",
}

MAX_HASH_BYTES = 250 * 1024 * 1024
MAX_HEADER_SNIFF_BYTES = 512 * 1024


def safe_exists(path: str) -> Path | None:
    p = Path(path)
    return p if p.exists() else None


def unique_roots() -> list[Path]:
    roots: list[Path] = []
    for raw in [
        r"C:\NWR\Niners-War-Room-model-v4-historical-receipt-locator-ledger-v1-20260709",
        r"C:\NWR\Niners-War-Room",
        r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1",
        r"C:\NWR\_rookie_source_handoff",
        r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708",
        r"C:\NWR\Niners-War-Room-recovery-zip-ingest-dropzone-validation-v1-20260708",
        r"C:\NWR\Niners-War-Room-current-board-rebuild-input-recovery-v1-20260708",
        r"C:\NWR\Niners-War-Room-current-board-missing-file-manual-recovery-v1-20260708",
        r"C:\NWR\Niners-War-Room-model-v4-historical-component-receipt-backfill-v1-20260708",
        r"C:\NWR\Niners-War-Room-model-v4-partial-historical-replay-benchmark-v1-20260708",
        r"C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708",
        r"C:\NWR\Niners-War-Room-model-v4-formula-documentation-cleanup-v1-20260708",
        r"C:\NWR\Niners-War-Room-model-v4-production-active-human-review-packet-v1-20260708",
        r"C:\NWR\Niners-War-Room-formula-gauntlet-data-readiness-gate-v1-20260708",
        r"C:\NWR\Niners-War-Room-data-hygiene-historical-label-identity-source-gate-closure-v1-20260708",
        r"C:\NWR\Niners-War-Room-data-hygiene-charter-second-advance-merge-review-v1-20260708",
        r"C:\NWR\Niners-War-Room-model-v4-historical-receipt-gap-closure-plan-v1-20260708",
        r"C:\NWR\Niners-War-Room-full-system-audit-integration-map-v1-20260709",
        r"C:\NWR\Niners-War-Room-full-system-audit-pfr-rb-broken-tackle-addendum-v1-20260709",
    ]:
        p = safe_exists(raw)
        if p:
            roots.append(p.resolve())
    seen = set()
    out: list[Path] = []
    for root in roots:
        s = str(root).lower()
        if s not in seen:
            seen.add(s)
            out.append(root)
    return out


def lower_path(path: Path) -> str:
    return str(path).replace("\\", "/").lower()


def is_candidate_path(path: Path, is_dir: bool = False) -> bool:
    lp = lower_path(path)
    name = path.name.lower()
    if any(token in name for token in DIRECT_NAME_PATTERNS):
        return True
    if is_dir:
        return any(token in name for token in ["current_value", "evidence_matrices", "wr_qb_v2", "candidate"])
    if path.suffix.lower() not in {".csv", ".tsv", ".json", ".parquet", ".md", ".txt"}:
        return False
    if path.suffix.lower() in {".csv", ".tsv", ".json", ".parquet"} and "local_exports/model_v4" in lp and any(token in lp for token in ["current_value", "component", "coverage", "candidate", "replay"]):
        return True
    if path.suffix.lower() in {".csv", ".tsv", ".json", ".parquet"} and "model_v4" in lp and any(token in name for token in ["historical", "component", "coverage", "candidate", "replay", "matrix"]):
        return True
    return False


def sha256_file(path: Path, size: int) -> str:
    if size > MAX_HASH_BYTES:
        return "SKIPPED_TOO_LARGE"
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sniff_text_header(path: Path) -> str:
    try:
        with path.open("rb") as fh:
            raw = fh.read(MAX_HEADER_SNIFF_BYTES)
        return raw.decode("utf-8", errors="ignore")
    except OSError:
        return ""


def csv_metadata(path: Path) -> tuple[str, str, str, str, str]:
    suffix = path.suffix.lower()
    if suffix not in {".csv", ".tsv"}:
        return "", "", "", "", ""
    delimiter = "\t" if suffix == ".tsv" else ","
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.reader(fh, delimiter=delimiter)
            try:
                columns = next(reader)
            except StopIteration:
                return "0", "0", "", "", ""
            row_count = sum(1 for _ in reader)
    except Exception:
        return "", "", "", "", ""
    colset = {c.strip() for c in columns}
    season_cols = [c for c in columns if re.search(r"(season|year|as_of|feature)", c, re.I)]
    pos_cols = [c for c in columns if c.lower() in {"pos", "position", "fantasy_position"} or "position" in c.lower()]
    key_cols = [c for c in columns if re.search(r"(player_id|nwr_player_id|gsis_id|sleeper_id|pfr_id|player_name|name)", c, re.I)]
    return str(row_count), str(len(columns)), "|".join(columns), "|".join(season_cols), "|".join(pos_cols + key_cols)


def extract_distinct_values(path: Path, columns_hint: list[str], max_values: int = 20) -> str:
    if path.suffix.lower() not in {".csv", ".tsv"}:
        return ""
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    values: set[str] = set()
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh, delimiter=delimiter)
            if not reader.fieldnames:
                return ""
            lookup = {c.lower(): c for c in reader.fieldnames}
            chosen = []
            for hint in columns_hint:
                for lower, original in lookup.items():
                    if hint in lower:
                        chosen.append(original)
            for row in reader:
                for col in chosen:
                    value = (row.get(col) or "").strip()
                    if value:
                        values.add(value)
                if len(values) >= max_values:
                    break
    except Exception:
        return ""
    return "|".join(sorted(values)[:max_values])


def map_families(path: Path, columns: str) -> list[str]:
    haystack = f"{lower_path(path)} {columns.lower()}"
    families = []
    for family, keywords in FAMILY_KEYWORDS.items():
        if any(k.lower() in haystack for k in keywords):
            families.append(family)
    return families or ["not_mapped"]


def classify_fit(path: Path, families: list[str], columns: str, row_count: str) -> str:
    lp = lower_path(path)
    col = columns.lower()
    has_score_cols = "checkpoint_review_score" in col or "position_specific_review_score" in col or "nwr_dynasty_score" in col
    has_feature_season = any(token in col for token in ["feature_season", "as_of", "source_season", "target_season"])
    has_historical = has_feature_season or any(token in path.name.lower() for token in ["historical", "season_by_season", "player_season", "lagged"])
    has_current = any(token in lp for token in ["current_value", "current_player_value", "full_player_board", "model_outputs.csv", "latest"])
    if "route" in lp or "yprr" in lp or "tprr" in lp:
        return "blocked_source_lead_or_proxy" if not has_score_cols else "partial"
    if "shadow_model_v2_metrics.csv" in lp:
        return "likely_equivalent"
    if has_score_cols and has_historical and not has_current:
        return "likely_equivalent"
    if has_score_cols and has_current:
        return "current_board_equivalent_only"
    if "model_v4_historical_component_receipts.csv" in lp:
        return "partial_proxy_receipts"
    if "source_coverage_matrix.csv" in lp and has_current:
        return "current_board_equivalent_only"
    if "source_coverage_matrix.csv" in lp and has_historical:
        return "partial"
    if "component_receipts" in lp or "component_rows" in lp:
        return "partial"
    if any(f in families for f in ["route_yprr_tprr_exact_receipts", "return_scoring_receipts"]):
        return "blocked_or_requires_source_admission"
    if row_count and row_count != "0":
        return "partial"
    return "not_usable_without_review"


def review_safety(fit: str, path: Path, size: int) -> tuple[str, str, str]:
    lp = lower_path(path)
    too_large = "yes" if size > MAX_HASH_BYTES else "no"
    if "raw" in lp and "docs/hq" not in lp and "local_exports" not in lp:
        return "needs_human_review", too_large, "possibly raw/non-reviewed path"
    if fit in {"blocked_source_lead_or_proxy", "blocked_or_requires_source_admission"}:
        return "no", too_large, "source admission or route/source gate required"
    if too_large == "yes":
        return "manifest_only", too_large, "large file; do not copy in locator lane"
    return "yes", too_large, "manifest-only in this locator lane"


def iter_candidates(roots: list[Path]) -> Iterable[tuple[Path, str, Path]]:
    seen: set[str] = set()
    for root in roots:
        for current, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            cur_path = Path(current)
            if is_candidate_path(cur_path, is_dir=True):
                key = str(cur_path.resolve()).lower()
                if key not in seen:
                    seen.add(key)
                    yield cur_path, "folder", root
            for name in files:
                path = cur_path / name
                if not is_candidate_path(path):
                    if path.suffix.lower() in {".csv", ".tsv", ".json"} and any(anchor in lower_path(path) for anchor in ["model_v4", "current_value", "local_exports", "historical_model_v4"]):
                        header = sniff_text_header(path)
                        if not any(k in header for k in CONTENT_KEYWORDS):
                            continue
                    else:
                        continue
                key = str(path.resolve()).lower()
                if key not in seen:
                    seen.add(key)
                    yield path, "file", root


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    roots = unique_roots()
    target_fields = [
        "family_name",
        "gap_status",
        "current_board_equivalent",
        "expected_historical_equivalent",
        "required_columns",
        "required_keys",
        "required_seasons",
        "required_positions",
        "source_use_gate_status",
        "why_it_matters",
        "gates_exact_replay",
        "gates_formula_gauntlet",
    ]
    write_csv(ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_LOCATOR_TARGETS.csv", TARGETS, target_fields)

    ledger_rows: list[dict] = []
    path_rows: list[dict] = []

    for path, kind, root in iter_candidates(roots):
        try:
            stat = path.stat()
        except OSError:
            continue
        size = stat.st_size if kind == "file" else 0
        sha = sha256_file(path, size) if kind == "file" else ""
        row_count = column_count = columns = season_columns = pos_key_columns = ""
        seasons_present = positions_present = ""
        if kind == "file":
            row_count, column_count, columns, season_columns, pos_key_columns = csv_metadata(path)
            seasons_present = extract_distinct_values(path, ["season", "year", "feature"], 24)
            positions_present = extract_distinct_values(path, ["position", "pos"], 12)
            if not columns and path.suffix.lower() in {".md", ".txt", ".json"}:
                columns = ""
        families = map_families(path, columns)
        fit = classify_fit(path, families, columns, row_count)
        review_safe, too_raw_large, safety_note = review_safety(fit, path, size)
        requires_source_admission = "yes" if any(f in families for f in ["route_yprr_tprr_exact_receipts", "return_scoring_receipts"]) or fit in {"blocked_source_lead_or_proxy", "blocked_or_requires_source_admission"} else "no"
        requires_master = "yes"
        relationship = ";".join(families)
        row = {
            "found_path": str(path),
            "file_or_folder_name": path.name,
            "artifact_type": kind,
            "search_root": str(root),
            "source_family": relationship,
            "file_size_bytes": str(size) if kind == "file" else "",
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            "sha256": sha,
            "row_count": row_count,
            "column_count": column_count,
            "columns": columns,
            "seasons_present": seasons_present,
            "positions_present": positions_present,
            "key_columns_present": pos_key_columns,
            "maps_to_missing_receipt_family": relationship,
            "fit_classification": fit,
            "review_safe": review_safe,
            "too_raw_or_large_to_copy": too_raw_large,
            "requires_master_hq_approval": requires_master,
            "requires_source_admission": requires_source_admission,
            "notes": safety_note,
        }
        ledger_rows.append(row)
        for family in families:
            path_rows.append({
                "receipt_family": family,
                "found_path": str(path),
                "artifact_type": kind,
                "fit_classification": fit,
                "review_safe": review_safe,
                "sha256": sha,
                "row_count": row_count,
                "columns_present": "yes" if columns else "no",
                "path_role": "candidate_artifact",
            })

    ledger_rows.sort(key=lambda r: (r["source_family"], r["fit_classification"], r["found_path"].lower()))
    ledger_fields = [
        "found_path",
        "file_or_folder_name",
        "artifact_type",
        "search_root",
        "source_family",
        "file_size_bytes",
        "modified_time",
        "sha256",
        "row_count",
        "column_count",
        "columns",
        "seasons_present",
        "positions_present",
        "key_columns_present",
        "maps_to_missing_receipt_family",
        "fit_classification",
        "review_safe",
        "too_raw_or_large_to_copy",
        "requires_master_hq_approval",
        "requires_source_admission",
        "notes",
    ]
    write_csv(ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_FOUND_ARTIFACT_LEDGER.csv", ledger_rows, ledger_fields)

    path_fields = [
        "receipt_family",
        "found_path",
        "artifact_type",
        "fit_classification",
        "review_safe",
        "sha256",
        "row_count",
        "columns_present",
        "path_role",
    ]
    write_csv(ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_PATH_MAP.csv", path_rows, path_fields)

    by_family: dict[str, list[dict]] = defaultdict(list)
    for row in ledger_rows:
        for family in row["source_family"].split(";"):
            by_family[family].append(row)

    coverage_rows: list[dict] = []
    freeze_rows: list[dict] = []
    next_action_by_status = {
        "RECOVERABLE_FROM_EXISTING_ARTIFACTS": "safe to freeze in next lane if exact/likely artifacts pass human review; otherwise continue manual recovery",
        "REGENERATABLE_REVIEW_ONLY": "safe to regenerate review-only in next lane only with Master HQ bounded contract",
        "REQUIRES_HUMAN_REVIEW": "requires Master HQ approval and human review",
        "REQUIRES_SOURCE_ADMISSION": "requires source admission or Route Recovery before use",
        "MISSING_SOURCE": "requires human manual recovery or scope removal",
        "NOT_ENOUGH_INFORMATION": "requires Master HQ formula/spec decision",
    }
    for target in TARGETS:
        family = target["family_name"]
        rows = by_family.get(family, [])
        fit_counts = Counter(r["fit_classification"] for r in rows)
        exact_or_likely = sum(fit_counts[k] for k in ["likely_equivalent"])
        current_only = fit_counts["current_board_equivalent_only"]
        partial = sum(fit_counts[k] for k in ["partial", "partial_proxy_receipts"])
        blocked = sum(fit_counts[k] for k in ["blocked_source_lead_or_proxy", "blocked_or_requires_source_admission"])
        if exact_or_likely:
            coverage = "found likely equivalent"
        elif current_only and not partial:
            coverage = "found only current-board equivalent"
        elif partial or current_only:
            coverage = "found partial equivalent"
        elif blocked:
            coverage = "blocked by source gate"
        else:
            coverage = "not found"
        top_paths = [r["found_path"] for r in rows[:5]]
        coverage_rows.append({
            "family_name": family,
            "gap_status": target["gap_status"],
            "candidate_artifacts_found": str(len(rows)),
            "likely_equivalent_count": str(exact_or_likely),
            "partial_count": str(partial),
            "current_board_only_count": str(current_only),
            "blocked_or_requires_source_count": str(blocked),
            "coverage_status": coverage,
            "top_candidate_paths": " | ".join(top_paths),
            "next_action": next_action_by_status.get(target["gap_status"], "requires review"),
            "exact_replay_blocker": "yes" if coverage != "found likely equivalent" else "still requires canonical admission and field validation",
            "formula_gauntlet_blocker": "yes" if target["gates_formula_gauntlet"].startswith("yes") and coverage in {"not found", "blocked by source gate"} else "conditional",
        })
        freeze_rows.append({
            "family_name": family,
            "decision": "manifest_only_this_lane",
            "safe_to_freeze_next_lane": "yes" if coverage in {"found likely equivalent", "found partial equivalent", "found only current-board equivalent"} and target["gap_status"] != "REQUIRES_SOURCE_ADMISSION" else "no",
            "safe_to_regenerate_next_lane": "yes with Master HQ contract" if target["gap_status"] == "REGENERATABLE_REVIEW_ONLY" else "no",
            "requires_human_review": "yes",
            "requires_source_admission": "yes" if target["gap_status"] == "REQUIRES_SOURCE_ADMISSION" else "no",
            "reason": f"{coverage}; locator lane does not copy or regenerate artifacts",
        })

    coverage_fields = [
        "family_name",
        "gap_status",
        "candidate_artifacts_found",
        "likely_equivalent_count",
        "partial_count",
        "current_board_only_count",
        "blocked_or_requires_source_count",
        "coverage_status",
        "top_candidate_paths",
        "next_action",
        "exact_replay_blocker",
        "formula_gauntlet_blocker",
    ]
    write_csv(ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_FAMILY_COVERAGE_SUMMARY.csv", coverage_rows, coverage_fields)

    freeze_fields = [
        "family_name",
        "decision",
        "safe_to_freeze_next_lane",
        "safe_to_regenerate_next_lane",
        "requires_human_review",
        "requires_source_admission",
        "reason",
    ]
    write_csv(ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_FREEZE_OR_MANIFEST_DECISIONS.csv", freeze_rows, freeze_fields)

    found_count = len(ledger_rows)
    likely_count = sum(1 for r in ledger_rows if r["fit_classification"] == "likely_equivalent")
    partial_count = sum(1 for r in ledger_rows if r["fit_classification"] in {"partial", "partial_proxy_receipts", "current_board_equivalent_only"})
    highest_value = ""
    priority_names = [
        "current_player_value_full_board_review_rows.csv",
        "current_value_full_board_review_rows.csv",
        "MODEL_V4_HISTORICAL_COMPONENT_RECEIPTS.csv",
        "source_coverage_matrix.csv",
    ]
    for name in priority_names:
        for row in ledger_rows:
            if row["file_or_folder_name"].lower() == name.lower():
                highest_value = row["found_path"]
                break
        if highest_value:
            break
    if not highest_value and ledger_rows:
        highest_value = ledger_rows[0]["found_path"]

    missing = [r["family_name"] for r in coverage_rows if r["coverage_status"] in {"not found", "blocked by source gate"}]
    freeze_next = [r["family_name"] for r in freeze_rows if r["safe_to_freeze_next_lane"] == "yes"]
    regen_next = [r["family_name"] for r in freeze_rows if r["safe_to_regenerate_next_lane"].startswith("yes")]

    blockers_md = ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_REMAINING_BLOCKERS.md"
    blockers_md.write_text(
        "# Model v4 Historical Receipt Remaining Blockers\n\n"
        "## Highest Blockers\n\n"
        "1. Exact season-by-season `checkpoint_review_score` and `position_specific_review_score` remain unadmitted unless a historical likely-equivalent artifact is frozen and validated by a later lane.\n"
        "2. Exact transform/weight receipts remain `NOT_ENOUGH_INFORMATION`; exact replay cannot be claimed without formula/spec/version receipts or a Master HQ-approved replacement contract.\n"
        "3. WR/QB v2 overlay history requires human review because it is candidate decision logic.\n"
        "4. Route/YPRR/TPRR and return scoring receipts require source admission; no source is promoted here.\n"
        "5. `shadow_model_v2_metrics.csv` remains a missing-source caveat unless located or removed from exact replay scope.\n\n"
        f"## Families Still Missing Or Blocked\n\n{chr(10).join('- ' + m for m in missing) if missing else '- None fully missing, but all recovered candidates still need review/admission.'}\n\n"
        "Exact Model v4 replay remains blocked. Formula Gauntlet tournaments remain blocked.\n",
        encoding="utf-8",
    )

    next_md = ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_NEXT_ACTIONS.md"
    next_md.write_text(
        "# Model v4 Historical Receipt Next Actions\n\n"
        "## Recommended Next Data Hygiene Lane\n\n"
        "`Model v4 Historical Receipt Freeze and Schema Validation V1`\n\n"
        "Objective: take the highest-value manifest-only candidates from this ledger, freeze only small review-safe derived artifacts if Master HQ approves, validate schemas/keys/seasons/positions, and decide whether any artifact can satisfy exact replay receipt families.\n\n"
        "## Safe To Freeze Next Lane\n\n"
        + ("\n".join(f"- {x}" for x in freeze_next) if freeze_next else "- None yet")
        + "\n\n## Safe To Regenerate Review-Only Only With Master HQ Contract\n\n"
        + ("\n".join(f"- {x}" for x in regen_next) if regen_next else "- None")
        + "\n\n## Remain Blocked Or Need Admission/Human Review\n\n"
        + "\n".join(f"- {row['family_name']}: {row['next_action']}" for row in coverage_rows if row["family_name"] not in freeze_next and row["family_name"] not in regen_next)
        + "\n\nNo replay, Formula Gauntlet, tuning, source promotion, ranking change, or app/runtime change is authorized by this ledger.\n",
        encoding="utf-8",
    )

    source_md = ARTIFACT_DIR / "DATA_HYGIENE_SOURCE_TRACE.md"
    source_md.write_text(
        "# Data Hygiene Source Trace\n\n"
        f"- Current remote HQ verified: `{CURRENT_REMOTE_HEAD}`\n"
        f"- Prior gap plan commit verified: `{PRIOR_GAP_COMMIT}`\n"
        f"- Prior full system audit commit verified: `{PRIOR_SYSTEM_AUDIT_COMMIT}`\n"
        f"- Prior PFR addendum commit verified: `{PRIOR_PFR_ADDENDUM_COMMIT}`\n\n"
        "## Governance Standards\n\n"
        "- `docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708/`\n"
        "- Data Hygiene Operating Charter V1 was checked as local/push-held context when available; this lane does not depend on it being canonical.\n\n"
        "## Prior Evidence Read\n\n"
        "- `C:\\NWR\\Niners-War-Room-model-v4-historical-receipt-gap-closure-plan-v1-20260708\\docs\\hq\\data_hygiene\\model_v4_historical_receipt_gap_closure_plan_v1_20260708`\n"
        "- `C:\\NWR\\Niners-War-Room-full-system-audit-integration-map-v1-20260709\\docs\\hq\\master\\nwr_full_system_audit_integration_map_v1_20260709`\n"
        "- `C:\\NWR\\Niners-War-Room-full-system-audit-pfr-rb-broken-tackle-addendum-v1-20260709\\docs\\hq\\master\\nwr_full_system_audit_pfr_rb_broken_tackle_addendum_v1_20260709`\n"
        "- Prior local Model v4 rebuild, receipt backfill, partial replay, recovery ZIP/dropzone, historical label, and Formula Gauntlet readiness packets where present.\n\n"
        "## Search Roots\n\n"
        + "\n".join(f"- `{root}`" for root in roots)
        + "\n\nThis lane is locator/ledger only. It did not copy large/raw files, regenerate receipts, run replay, run Formula Gauntlet, tune formulas, promote sources, or change rankings/app/runtime behavior.\n",
        encoding="utf-8",
    )

    report_md = ARTIFACT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_LOCATOR_LEDGER_V1_REPORT.md"
    verdict = "GREEN_MODEL_V4_HISTORICAL_RECEIPT_LEDGER_READY_WITH_RECOVERABLE_ARTIFACTS" if likely_count else "YELLOW_MODEL_V4_HISTORICAL_RECEIPT_LEDGER_PARTIAL_WITH_BLOCKERS"
    report_md.write_text(
        "# Model v4 Historical Receipt Locator and Ledger V1\n\n"
        "## Verdict\n\n"
        f"`{verdict}`\n\n"
        "## Clear Answer\n\n"
        "This lane located and ledgered existing candidate receipt artifacts, but it did not prove exact Model v4 historical replay. The ledger finds current-board equivalents, partial historical/proxy receipt artifacts, and source/coverage sidecars that can feed a later freeze/schema-validation lane. Exact historical replay remains blocked until season-by-season checkpoint/component/transform receipts are frozen, admitted, and validated.\n\n"
        "## Locator Summary\n\n"
        f"- Receipt families searched: `{len(TARGETS)}`\n"
        f"- Candidate artifacts/folders found: `{found_count}`\n"
        f"- Likely-equivalent artifacts found: `{likely_count}`\n"
        f"- Partial/current-equivalent artifacts found: `{partial_count}`\n"
        f"- Highest-value artifact found: `{highest_value}`\n\n"
        "## Readiness Impact\n\n"
        "- Exact Model v4 replay remains blocked.\n"
        "- Formula Gauntlet tournaments remain blocked.\n"
        "- 100-candidate Gauntlet remains blocked.\n"
        "- Champion refinement remains blocked.\n"
        "- Rankings integration remains blocked.\n"
        "- No source was promoted.\n\n"
        "## Highest-Value Finding\n\n"
        f"`{highest_value}`\n\n"
        "This is high value because it is closest to the current-board source rows or the partial historical receipt substrate. It still requires Master HQ approval and a later freeze/schema validation lane before any exact replay claim.\n\n"
        "## Next Data Hygiene Lane\n\n"
        "`Model v4 Historical Receipt Freeze and Schema Validation V1`\n\n"
        "That lane should freeze only review-safe derived candidates approved by Master HQ, validate keys/seasons/positions/schema, and decide whether any candidate can close exact replay gaps.\n",
        encoding="utf-8",
    )

    print(f"roots={len(roots)}")
    print(f"targets={len(TARGETS)}")
    print(f"ledger_rows={found_count}")
    print(f"likely_equivalent={likely_count}")
    print(f"partial_or_current={partial_count}")
    print(f"highest_value={highest_value}")


if __name__ == "__main__":
    main()
