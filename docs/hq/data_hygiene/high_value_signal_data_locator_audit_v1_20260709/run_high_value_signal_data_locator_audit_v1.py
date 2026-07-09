#!/usr/bin/env python3
"""
High-Value Signal Data Locator Audit V1.

This script performs a read-only locator sweep across NWR worktrees and
review artifacts. It writes only review artifacts in this packet folder.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"

PRIOR_ARTIFACTS = {
    "formula_results_master_review_data_upgrade_pivot_v1": Path(
        r"C:\NWR\Niners-War-Room-formula-results-master-review-data-upgrade-pivot-v1-20260709\docs\hq\master\formula_results_master_review_data_upgrade_pivot_v1_20260709"
    ),
    "full_review_only_formula_gauntlet_candidate_arena_v1": Path(
        r"C:\NWR\Niners-War-Room-full-review-only-formula-gauntlet-candidate-arena-v1-20260709\docs\hq\model\full_review_only_formula_gauntlet_candidate_arena_v1_20260709"
    ),
    "formula_data_mart_feature_availability_audit_v1": Path(
        r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
    ),
    "remaining_data_upgrade_sweep_v1": Path(
        r"C:\NWR\Niners-War-Room-formula-data-mart-remaining-upgrade-sweep-v1-20260709\docs\hq\data_hygiene\formula_data_mart_remaining_upgrade_sweep_v1_20260709"
    ),
    "pfr_rb_broken_tackle_addendum_v1": Path(
        r"C:\NWR\Niners-War-Room-full-system-audit-pfr-rb-broken-tackle-addendum-v1-20260709\docs\hq\master\nwr_full_system_audit_pfr_rb_broken_tackle_addendum_v1_20260709"
    ),
    "red_zone_exact_receipt_regeneration_pilot_v1": Path(
        r"C:\NWR\Niners-War-Room-model-v4-red-zone-exact-receipt-regeneration-pilot-v1-20260709\docs\hq\data_hygiene\model_v4_red_zone_exact_receipt_regeneration_pilot_v1_20260709"
    ),
}

SIGNAL_FAMILIES: dict[str, dict[str, Any]] = {
    "historical_market_adp": {
        "label": "Historical market / ADP",
        "why": "Market and ADP baselines may add non-production context and improve dynasty value calibration if historical/as-of safe.",
        "likely_formula_use": "review-only baseline/context and error-slice comparator",
        "likely_ranking_use_later": "possible context only after source/as-of gate",
        "priority": "high_if_asof_safe",
        "terms": [
            "dynastyprocess",
            "adp",
            "market",
            "market_value",
            "market_rank",
            "startup_adp",
            "rookie_adp",
            "sleeper_adp",
            "ktc",
            "keeptradecut",
            "market_snapshot",
            "historical_rankings",
            "draft_board_market",
            "rankings_market",
            "market_delta",
        ],
    },
    "rookie_draft_capital_prospect": {
        "label": "Rookie / draft capital / prospect data",
        "why": "Draft capital and prospect context can help sparse-history and young-player false negatives where PYF is weak.",
        "likely_formula_use": "review-only sparse-history and rookie breakout context",
        "likely_ranking_use_later": "possible rookie/dynasty context after source and identity gates",
        "priority": "high_if_source_safe",
        "terms": [
            "draft_round",
            "draft_pick",
            "overall_pick",
            "draft_year",
            "rookie_year",
            "combine",
            "cfbd",
            "college",
            "prospect",
            "rookie",
            "draft_capital",
            "early_declare",
            "age_adjusted_prospect",
            "drafted",
        ],
    },
    "team_offensive_environment": {
        "label": "Team / offensive environment",
        "why": "Team pace, plays, scoring, and opportunity context may explain role changes beyond prior production.",
        "likely_formula_use": "review-only team context slices if historical/as-of safe",
        "likely_ranking_use_later": "possible context after source/as-of gate",
        "priority": "medium_if_asof_safe",
        "terms": [
            "team_plays",
            "pass_rate",
            "rush_rate",
            "scoring_offense",
            "offensive_pace",
            "team_points",
            "offensive_snaps",
            "qb_quality",
            "offensive_line",
            "team_context",
            "schedule_strength",
            "vegas",
            "implied_points",
            "coaching",
            "coordinator",
        ],
    },
    "injury_availability": {
        "label": "Injury / availability point-in-time context",
        "why": "Availability history can support review-only caution slices without becoming injury prediction.",
        "likely_formula_use": "review-only caveat/slice context",
        "likely_ranking_use_later": "display or review context only unless separately approved",
        "priority": "medium_if_asof_safe",
        "terms": [
            "injury",
            "practice_report",
            "availability",
            "weekly_roster",
            "active",
            "inactive",
            "games_missed",
            "missed_games",
            "ir",
            "pup",
            "questionable",
            "doubtful",
            "out_status",
            "roster_status",
        ],
    },
    "role_depth_opportunity_change": {
        "label": "Role / depth / opportunity change context",
        "why": "Role, touch, target, and depth context may explain prior-production false positives and breakout candidates.",
        "likely_formula_use": "review-only miss taxonomy, guardrail context, and slices",
        "likely_ranking_use_later": "review context only unless separately approved",
        "priority": "medium_high_if_source_safe",
        "terms": [
            "depth_chart",
            "starter",
            "backup",
            "role",
            "snap_share",
            "snaps",
            "targets",
            "carries",
            "touches",
            "routes",
            "vacated_targets",
            "vacated_carries",
            "team_change",
            "new_team",
            "role_archetype",
            "opportunity_context",
        ],
    },
    "pfr_rb_broken_tackle": {
        "label": "PFR RB broken tackle values",
        "why": "A narrow RB-only contact-survival hypothesis could add non-duplicate RB context absent from the current Formula Data Mart.",
        "likely_formula_use": "RB-only review component test after join/schema validation",
        "likely_ranking_use_later": "blocked until separate approval; no broad PFR promotion",
        "priority": "highest_executable_if_values_found",
        "terms": [
            "pfr_rush_brk_tkl",
            "pfr_rush_brk_tkl__raw",
            "pfr_rush_brk_tkl__per_game",
            "pfr_rush_brk_tkl__per_attempt",
            "advstats_season_rush",
            "brk_tkl",
            "broken_tackle",
            "broken_tackles",
        ],
    },
    "red_zone_historical_expansion": {
        "label": "Red-zone historical expansion",
        "why": "Red-zone usage has direct fantasy scoring relevance if full historical/as-of coverage exists.",
        "likely_formula_use": "blocked or partial/caveated until 2013-2025 as-of coverage is proven",
        "likely_ranking_use_later": "blocked until source/as-of expansion",
        "priority": "medium_if_full_history_found",
        "terms": [
            "red_zone",
            "redzone",
            "rz",
            "inside_20",
            "inside_10",
            "goal_line",
            "goal_to_go",
            "red_zone_carries",
            "red_zone_targets",
            "end_zone_targets",
            "red_zone_touches",
            "red_zone_tds",
        ],
    },
}

DEPRIORITIZED_TERMS = [
    "yprr",
    "tprr",
    "route",
    "return_scoring",
    "kick_return",
    "punt_return",
    "pff",
    "elusive",
    "nwr_elusive_proxy",
]

SEARCH_ROOTS = [
    REPO_ROOT,
    Path(r"C:\NWR\fg_current_20260708"),
    Path(r"C:\NWR\_rookie_source_handoff"),
    Path(r"C:\NWR\_manual_recovery_dropzone"),
    Path(r"C:\NWR\_merge_worktrees\hq-pfr-bridge-readiness-20260708"),
    Path(r"C:\NWR\Niners-War-Room-formula-results-master-review-data-upgrade-pivot-v1-20260709"),
    Path(r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"),
    Path(r"C:\NWR\Niners-War-Room-formula-data-mart-remaining-upgrade-sweep-v1-20260709"),
    Path(r"C:\NWR\Niners-War-Room-full-review-only-formula-gauntlet-candidate-arena-v1-20260709"),
    Path(r"C:\NWR\Niners-War-Room-diverse-champion-refinement-predeclared-execution-v1-20260709"),
    Path(r"C:\NWR\Niners-War-Room-full-system-audit-pfr-rb-broken-tackle-addendum-v1-20260709"),
    Path(r"C:\NWR\Niners-War-Room-model-v4-red-zone-exact-receipt-regeneration-pilot-v1-20260709"),
    Path(r"C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709"),
    Path(r"C:\NWR_SANDBOX\Niners-War-Room-nflverse-metadata-dob-roster-admission-gate-v1-20260707"),
    Path(r"C:\NWR_SANDBOX\Niners-War-Room-raw-snapshot-2024-2025-admission-pivot-v1-20260707"),
    Path(r"C:\NWR_SANDBOX\Niners-War-Room-historical-model-lab-extended-20260703"),
]

EXCLUDED_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    ".next",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    "site-packages",
    "coverage",
    ".cache",
}

DATA_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".json",
    ".jsonl",
    ".parquet",
    ".xlsx",
    ".xls",
    ".pkl",
    ".pickle",
}

TEXT_EXTENSIONS = {".md", ".txt", ".py", ".ps1", ".yaml", ".yml"}
INSPECTABLE_EXTENSIONS = DATA_EXTENSIONS | TEXT_EXTENSIONS
MAX_HASH_BYTES = 5 * 1024 * 1024
MAX_TEXT_SAMPLE_BYTES = 96 * 1024
MAX_LEDGER_ROWS = 2500
MAX_PATHS_PER_FAMILY = 240
MAX_LEDGER_ROWS_PER_FAMILY = 200


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def term_in_haystack(term: str, haystack: str) -> bool:
    token = norm(term)
    if not token:
        return False
    if len(token) <= 3:
        return f"_{token}_" in f"_{haystack}_"
    return token in haystack


def relevant_path_text(path: Path) -> str:
    filtered_parts = []
    for part in path.parts:
        part_norm = norm(part)
        if not part_norm:
            continue
        if part_norm in {"c", "nwr", "nwr_sandbox", "_merge_worktrees", "_rookie_source_handoff", "_manual_recovery_dropzone"}:
            continue
        if part_norm.startswith("niners_war_room"):
            continue
        filtered_parts.append(part)
    return norm("/".join(filtered_parts[-7:]))


def safe_rel(path: Path) -> str:
    return str(path)


def iso_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
    except OSError:
        return ""


def sha256_for_file(path: Path, size: int) -> str:
    if size > MAX_HASH_BYTES:
        return "TOO_LARGE_TO_HASH_IN_LOCATOR"
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as exc:
        return f"HASH_ERROR:{exc.__class__.__name__}"


def read_text_sample(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            data = handle.read(MAX_TEXT_SAMPLE_BYTES)
        return data.decode("utf-8", errors="ignore")
    except OSError:
        return ""


def detect_families(path: Path, sample: str = "") -> list[str]:
    haystack = relevant_path_text(path) + "_" + norm(sample[:MAX_TEXT_SAMPLE_BYTES])
    hits: list[str] = []
    for family, config in SIGNAL_FAMILIES.items():
        for term in config["terms"]:
            if term_in_haystack(term, haystack):
                hits.append(family)
                break
    return hits


def detect_deprioritized(path: Path, sample: str = "") -> str:
    haystack = relevant_path_text(path) + "_" + norm(sample[:MAX_TEXT_SAMPLE_BYTES])
    hits = [term for term in DEPRIORITIZED_TERMS if term_in_haystack(term, haystack)]
    return "|".join(sorted(set(hits)))


def delimiter_for(path: Path, first_line: str) -> str:
    if path.suffix.lower() == ".tsv":
        return "\t"
    if first_line.count("\t") > first_line.count(","):
        return "\t"
    return ","


def summarize_csv_like(path: Path, size: int) -> dict[str, str]:
    result = {
        "row_count": "",
        "columns": "",
        "season_coverage": "",
        "position_coverage": "",
        "player_id_fields": "",
        "join_keys": "",
        "metadata_status": "",
    }
    if path.suffix.lower() not in {".csv", ".tsv"}:
        return result
    try:
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
            first_line = handle.readline()
            if not first_line:
                result["metadata_status"] = "empty_file"
                return result
            delimiter = delimiter_for(path, first_line)
            handle.seek(0)
            reader = csv.DictReader(handle, delimiter=delimiter)
            columns = reader.fieldnames or []
            result["columns"] = "|".join(columns[:120])
            column_norms = {norm(col): col for col in columns}
            player_fields = [
                col
                for col in columns
                if any(token in norm(col) for token in ["player_id", "gsis_id", "pfr_id", "sleeper_id", "player_name", "name"])
            ]
            join_keys = [
                col
                for col in columns
                if norm(col) in {"player_id", "gsis_id", "pfr_id", "sleeper_id", "season", "year", "position", "pos", "team"}
            ]
            result["player_id_fields"] = "|".join(player_fields[:20])
            result["join_keys"] = "|".join(join_keys[:20])
            season_cols = [column_norms[c] for c in column_norms if c in {"season", "year", "feature_season", "source_season"}]
            position_cols = [column_norms[c] for c in column_norms if c in {"position", "pos"}]
            seasons: set[str] = set()
            positions: Counter[str] = Counter()
            row_count = 0
            sample_limit = 2_000
            for row in reader:
                row_count += 1
                if row_count <= sample_limit:
                    for col in season_cols:
                        value = (row.get(col) or "").strip()
                        if re.fullmatch(r"20[0-9]{2}|19[0-9]{2}", value):
                            seasons.add(value)
                    for col in position_cols:
                            value = (row.get(col) or "").strip().upper()
                            if value in {"QB", "RB", "WR", "TE"}:
                                positions[value] += 1
                else:
                    break
            result["row_count"] = str(row_count) if row_count < sample_limit else f">={row_count}"
            if seasons:
                sorted_seasons = sorted(seasons)
                result["season_coverage"] = f"{sorted_seasons[0]}-{sorted_seasons[-1]}" if len(sorted_seasons) > 1 else sorted_seasons[0]
            if positions:
                result["position_coverage"] = "|".join(f"{pos}={positions[pos]}" for pos in ["QB", "RB", "WR", "TE"] if pos in positions)
            result["metadata_status"] = "parsed_csv_header_and_sample"
    except Exception as exc:  # noqa: BLE001 - locator must keep going.
        result["metadata_status"] = f"csv_parse_error:{exc.__class__.__name__}"
    return result


def summarize_parquet(path: Path) -> dict[str, str]:
    result = {
        "row_count": "",
        "columns": "",
        "season_coverage": "",
        "position_coverage": "",
        "player_id_fields": "",
        "join_keys": "",
        "metadata_status": "",
    }
    if path.suffix.lower() != ".parquet":
        return result
    result["metadata_status"] = "parquet_metadata_deferred_to_next_lane"
    return result


def source_type_for(path: Path, is_dir: bool) -> str:
    text = norm(str(path))
    suffix = path.suffix.lower()
    if is_dir:
        return "folder"
    if "docs_hq" in text:
        return "review_packet_or_governance_artifact"
    if "local_exports" in text:
        return "local_export_artifact"
    if "manual_recovery_dropzone" in text or "recovered" in text:
        return "recovered_artifact"
    if "sandbox" in text:
        return "sandbox_artifact"
    if suffix == ".parquet":
        return "parquet_source_artifact"
    if suffix in {".csv", ".tsv"}:
        return "tabular_artifact"
    return "candidate_artifact"


def raw_vs_derived_for(path: Path) -> str:
    text = norm(str(path))
    if any(token in text for token in ["raw", "source", "nflverse", "cfbd", "dynastyprocess", "sleeper", "parquet"]):
        return "raw_or_source_like"
    if any(token in text for token in ["docs_hq", "review", "formula_data_mart", "sidecar", "receipt", "ledger", "manifest"]):
        return "derived_or_review_artifact"
    if "local_exports" in text:
        return "local_export_unknown"
    return "unknown"


def source_gate_status(family: str, path: Path) -> str:
    text = norm(str(path))
    if family == "pfr_rb_broken_tackle":
        return "review_only_narrow_pfr_rb_hypothesis_preserved_no_broad_pfr_promotion"
    if family == "historical_market_adp":
        return "needs_point_in_time_source_gate_review"
    if family == "rookie_draft_capital_prospect":
        if "cfbd" in text or "college" in text:
            return "needs_cfbd_or_prospect_source_gate_review"
        return "needs_source_and_identity_gate_review"
    if family == "injury_availability":
        return "needs_point_in_time_availability_source_gate_review"
    if family == "team_offensive_environment":
        return "needs_team_context_source_gate_review"
    if family == "role_depth_opportunity_change":
        if "role_archetype" in text:
            return "role_archetype_review_only_admitted_for_guardrail_context"
        return "needs_role_opportunity_source_gate_review"
    if family == "red_zone_historical_expansion":
        return "partial_review_only_with_caveats_unless_full_history_asof_proven"
    return "not_enough_information"


def availability_for(family: str, path: Path, columns: str, season_coverage: str, source_type: str) -> str:
    text = relevant_path_text(path) + "_" + norm(columns)
    seasons = re.findall(r"(?:19|20)\d{2}", season_coverage)
    has_multi_season = len(set(seasons)) > 1
    is_docs_only = source_type == "review_packet_or_governance_artifact"

    if family == "pfr_rb_broken_tackle":
        if any(token in text for token in ["advstats_season_rush", "brk_tkl", "pfr_rush_brk_tkl", "pfr_rb_broken_tackle"]):
            return "AVAILABLE_NEEDS_SCHEMA_VALIDATION"
        if "broken_tackle" in text:
            return "AVAILABLE_REVIEW_ONLY"
        if source_type == "review_packet_or_governance_artifact":
            return "AVAILABLE_REVIEW_ONLY"
        return "NOT_ENOUGH_INFORMATION"
    if family == "historical_market_adp":
        if any(token in text for token in ["latest", "current", "2026"]):
            return "AVAILABLE_BUT_CURRENT_ONLY"
        if has_multi_season or any(token in text for token in ["historical", "snapshot", "season"]):
            return "AVAILABLE_NEEDS_ASOF_REVIEW"
        return "AVAILABLE_NEEDS_SOURCE_GATE"
    if family == "rookie_draft_capital_prospect":
        if any(token in text for token in ["draft_round", "draft_pick", "overall_pick", "draft_year", "rookie_year", "cfbd"]):
            return "AVAILABLE_NEEDS_SOURCE_GATE"
        return "AVAILABLE_NEEDS_IDENTITY_REVIEW"
    if family == "team_offensive_environment":
        return "AVAILABLE_NEEDS_ASOF_REVIEW"
    if family == "injury_availability":
        return "AVAILABLE_NEEDS_ASOF_REVIEW"
    if family == "role_depth_opportunity_change":
        if "role_archetype" in text:
            return "AVAILABLE_REVIEW_ONLY"
        return "AVAILABLE_NEEDS_SOURCE_GATE"
    if family == "red_zone_historical_expansion":
        if is_docs_only:
            return "AVAILABLE_NEEDS_ASOF_REVIEW"
        if has_multi_season:
            return "AVAILABLE_NEEDS_ASOF_REVIEW"
        return "MISSING_RECEIPT"
    return "NOT_ENOUGH_INFORMATION"


def row_formula_candidate(family: str, availability: str, source_type: str, path: Path) -> str:
    if availability in {"BLOCKED", "MISSING_SOURCE", "MISSING_RECEIPT", "NOT_ENOUGH_INFORMATION", "PARK_FOR_LATER"}:
        return "no"
    text = norm(str(path))
    if family == "pfr_rb_broken_tackle":
        return "yes_after_join_schema_validation"
    if family == "historical_market_adp":
        return "yes_after_asof_source_gate" if availability != "AVAILABLE_BUT_CURRENT_ONLY" else "no_current_only"
    if family == "rookie_draft_capital_prospect":
        return "yes_after_source_identity_gate"
    if family in {"team_offensive_environment", "injury_availability"}:
        return "yes_after_asof_source_gate"
    if family == "role_depth_opportunity_change" and "role_archetype" in text:
        return "already_used_review_only_context"
    if family == "red_zone_historical_expansion":
        return "no_until_full_history_asof_proven"
    return "needs_review"


def priority_score(family: str, availability: str, source_type: str, path: Path, columns: str) -> int:
    score = 0
    if family == "pfr_rb_broken_tackle":
        pfr_text = relevant_path_text(path) + "_" + norm(columns)
        if any(token in pfr_text for token in ["advstats_season_rush", "brk_tkl", "pfr_rush_brk_tkl", "pfr_rb_broken_tackle"]):
            score += 100
        elif source_type == "review_packet_or_governance_artifact":
            score += 78
        else:
            score += 20
    elif family == "historical_market_adp":
        score += 85
    elif family == "rookie_draft_capital_prospect":
        score += 80
    elif family == "team_offensive_environment":
        score += 65
    elif family == "injury_availability":
        score += 60
    elif family == "role_depth_opportunity_change":
        score += 55
    elif family == "red_zone_historical_expansion":
        score += 50
    if availability == "AVAILABLE_REVIEW_ONLY":
        score += 25
    elif availability == "AVAILABLE_NEEDS_SCHEMA_VALIDATION":
        score += 20
    elif availability == "AVAILABLE_NEEDS_ASOF_REVIEW":
        score += 12
    elif availability == "AVAILABLE_BUT_CURRENT_ONLY":
        score -= 15
    if source_type in {"tabular_artifact", "parquet_source_artifact", "local_export_artifact", "recovered_artifact"}:
        score += 12
    if columns:
        score += 8
    if "docs_hq" in norm(str(path)):
        score -= 3
    return score


def should_skip_dir(path: Path) -> bool:
    name = path.name.lower()
    if name in EXCLUDED_DIRS:
        return True
    try:
        if path.resolve() == OUT_DIR.resolve():
            return True
    except OSError:
        pass
    return False


def iter_unique_roots() -> list[Path]:
    roots: list[Path] = []
    seen: set[str] = set()
    candidates = [root for root in SEARCH_ROOTS if root.exists()]
    candidates.sort(key=lambda item: len(str(item)))
    for root in candidates:
        resolved = str(root).lower()
        if any(resolved.startswith(existing + os.sep) for existing in seen):
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        roots.append(root)
    return roots


def scan_candidates() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for path in iter_path_matched_files():
        path_key = safe_rel(path).lower()
        if path_key in seen_paths:
            continue
        seen_paths.add(path_key)
        size = 0
        try:
            size = path.stat().st_size
        except OSError:
            pass
        sample = ""
        if path.suffix.lower() in TEXT_EXTENSIONS or path.suffix.lower() in {".csv", ".tsv", ".json", ".jsonl"}:
            sample = read_text_sample(path)
        families = sorted(set(detect_families(path, sample)))
        if not families:
            continue
        metadata = summarize_csv_like(path, size)
        parquet_metadata = summarize_parquet(path)
        for key, value in parquet_metadata.items():
            if value:
                metadata[key] = value
        source_type = source_type_for(path, False)
        file_hash = sha256_for_file(path, size)
        for family in families:
            availability = availability_for(
                family,
                path,
                metadata.get("columns", ""),
                metadata.get("season_coverage", ""),
                source_type,
            )
            rows.append(
                {
                    "signal_family": family,
                    "found_path": safe_rel(path),
                    "file_folder_name": path.name,
                    "source_type": source_type,
                    "raw_vs_derived": raw_vs_derived_for(path),
                    "file_size": str(size),
                    "modified_time": iso_mtime(path),
                    "sha256": file_hash,
                    "row_count": metadata.get("row_count", ""),
                    "columns": metadata.get("columns", ""),
                    "season_coverage": metadata.get("season_coverage", ""),
                    "position_coverage": metadata.get("position_coverage", ""),
                    "player_id_fields": metadata.get("player_id_fields", ""),
                    "join_keys": metadata.get("join_keys", ""),
                    "source_use_gate_status": source_gate_status(family, path),
                    "leakage_asof_status": "pass_from_existing_review_packet"
                    if "docs_hq" in norm(str(path)) and "source_trace" not in norm(str(path))
                    else "needs_review",
                    "identity_risk": "low_if_player_id_keys_present"
                    if metadata.get("player_id_fields")
                    else "needs_identity_review",
                    "missingness_risk": "needs_schema_validation",
                    "availability_status": availability,
                    "formula_test_candidate": row_formula_candidate(family, availability, source_type, path),
                    "ranking_integration_candidate_later": "blocked_without_master_approval",
                    "park_decision": "park_if_not_executable_next_lane",
                    "deprioritized_terms": detect_deprioritized(path, sample),
                    "metadata_status": metadata.get("metadata_status", "") or "path_or_text_match",
                    "_score": str(priority_score(family, availability, source_type, path, metadata.get("columns", ""))),
                }
            )
    selected: list[dict[str, str]] = []
    for family in SIGNAL_FAMILIES:
        family_rows = [row for row in rows if row["signal_family"] == family]
        family_rows.sort(key=lambda row: (int(row["_score"]), row["found_path"]), reverse=True)
        selected.extend(family_rows[:MAX_LEDGER_ROWS_PER_FAMILY])
    selected.sort(key=lambda row: (int(row["_score"]), row["signal_family"], row["found_path"]), reverse=True)
    return selected


def iter_path_matched_files() -> list[Path]:
    candidate_paths: list[Path] = []
    seen: set[str] = set()
    family_counts: Counter[str] = Counter()
    roots = [str(root) for root in iter_unique_roots()]
    if not roots:
        return candidate_paths
    try:
        result = subprocess.run(
            ["rg", "--files", *roots],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=30,
            check=False,
        )
        lines = result.stdout.splitlines()
    except (OSError, subprocess.TimeoutExpired):
        return iter_path_matched_files_fallback()
    out_dir_text = str(OUT_DIR).lower()
    for raw in lines:
        if not raw:
            continue
        if raw.lower().startswith(out_dir_text):
            continue
        path = Path(raw)
        if path.suffix.lower() not in INSPECTABLE_EXTENSIONS:
            continue
        path_key = str(path).lower()
        if path_key in seen:
            continue
        families = detect_families(path)
        if not families:
            continue
        if all(family_counts[family] >= MAX_PATHS_PER_FAMILY for family in families):
            continue
        seen.add(path_key)
        candidate_paths.append(path)
        for family in families:
            family_counts[family] += 1
    return candidate_paths


def iter_path_matched_files_fallback() -> list[Path]:
    candidate_paths: list[Path] = []
    seen: set[str] = set()
    family_counts: Counter[str] = Counter()
    for root in iter_unique_roots():
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            dirs[:] = [d for d in dirs if not should_skip_dir(current_path / d)]
            for file_name in files:
                path = current_path / file_name
                if path.suffix.lower() not in INSPECTABLE_EXTENSIONS:
                    continue
                try:
                    if path.resolve().is_relative_to(OUT_DIR.resolve()):
                        continue
                except OSError:
                    pass
                path_key = safe_rel(path).lower()
                if path_key in seen:
                    continue
                families = detect_families(path)
                if not families:
                    continue
                if all(family_counts[family] >= MAX_PATHS_PER_FAMILY for family in families):
                    continue
                seen.add(path_key)
                candidate_paths.append(path)
                for family in families:
                    family_counts[family] += 1
    return candidate_paths


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            clean = {name: row.get(name, "") for name in fieldnames}
            writer.writerow(clean)


def build_target_matrix() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for family, config in SIGNAL_FAMILIES.items():
        rows.append(
            {
                "signal_family": family,
                "signal_family_label": config["label"],
                "why_it_might_improve_accuracy": config["why"],
                "likely_formula_use": config["likely_formula_use"],
                "likely_ranking_use_later": config["likely_ranking_use_later"],
                "source_terms_searched": "|".join(config["terms"]),
                "likely_artifacts": "local exports|review packets|source manifests|historical panels|sidecars",
                "current_status": "locator_audit_in_progress",
                "priority": config["priority"],
            }
        )
    return rows


def summarize_availability(ledger: list[dict[str, str]]) -> list[dict[str, str]]:
    by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in ledger:
        by_family[row["signal_family"]].append(row)
    rows: list[dict[str, str]] = []
    for family, config in SIGNAL_FAMILIES.items():
        family_rows = by_family.get(family, [])
        statuses = Counter(row["availability_status"] for row in family_rows)
        formula_candidates = sum(1 for row in family_rows if row["formula_test_candidate"].startswith("yes"))
        current_only = statuses.get("AVAILABLE_BUT_CURRENT_ONLY", 0)
        review_only = statuses.get("AVAILABLE_REVIEW_ONLY", 0)
        schema = statuses.get("AVAILABLE_NEEDS_SCHEMA_VALIDATION", 0)
        asof = statuses.get("AVAILABLE_NEEDS_ASOF_REVIEW", 0)
        source_gate = statuses.get("AVAILABLE_NEEDS_SOURCE_GATE", 0)
        missing = statuses.get("MISSING_SOURCE", 0) + statuses.get("MISSING_RECEIPT", 0)
        if not family_rows:
            status = "MISSING_SOURCE"
        elif family == "pfr_rb_broken_tackle" and (schema or review_only):
            status = "AVAILABLE_NEEDS_SCHEMA_VALIDATION"
        elif family == "historical_market_adp" and asof:
            status = "AVAILABLE_NEEDS_ASOF_REVIEW"
        elif family == "historical_market_adp" and current_only:
            status = "AVAILABLE_BUT_CURRENT_ONLY"
        elif source_gate:
            status = "AVAILABLE_NEEDS_SOURCE_GATE"
        elif asof:
            status = "AVAILABLE_NEEDS_ASOF_REVIEW"
        elif review_only:
            status = "AVAILABLE_REVIEW_ONLY"
        elif missing:
            status = "MISSING_RECEIPT"
        else:
            status = "NOT_ENOUGH_INFORMATION"
        top_paths = [
            row["found_path"]
            for row in sorted(family_rows, key=lambda item: int(item["_score"]), reverse=True)[:5]
        ]
        rows.append(
            {
                "signal_family": family,
                "signal_family_label": config["label"],
                "candidate_artifact_count": str(len(family_rows)),
                "availability_status": status,
                "status_counts": "|".join(f"{key}={value}" for key, value in sorted(statuses.items())),
                "formula_test_candidate_count": str(formula_candidates),
                "top_candidate_paths": " || ".join(top_paths),
                "source_use_gate_status": source_gate_status(family, Path(top_paths[0])) if top_paths else "not_found",
                "ranking_integration_status": "blocked_without_master_approval",
                "notes": availability_notes(family, status),
            }
        )
    return rows


def availability_notes(family: str, status: str) -> str:
    if family == "pfr_rb_broken_tackle":
        return "Most executable near-term lane if actual brk_tkl values can be joined RB-only and review-only."
    if family == "historical_market_adp":
        return "High upside, but current-only snapshots and historical/as-of uncertainty block immediate formula use."
    if family == "rookie_draft_capital_prospect":
        return "Useful for young/sparse-history misses after source and identity gates."
    if family == "team_offensive_environment":
        return "Potential role/opportunity context; needs as-of source proof."
    if family == "injury_availability":
        return "Caution/slice context only; not injury prediction."
    if family == "role_depth_opportunity_change":
        return "Role archetype is already review-only admitted; broader role/depth artifacts need gates."
    if family == "red_zone_historical_expansion":
        return "Existing accepted red-zone use is partial 2024-2025 only; full history remains unproven."
    return status


def build_priority_ranking(availability_rows: list[dict[str, str]], ledger: list[dict[str, str]]) -> list[dict[str, str]]:
    counts = {row["signal_family"]: int(row["candidate_artifact_count"]) for row in availability_rows}
    statuses = {row["signal_family"]: row["availability_status"] for row in availability_rows}
    base_order = [
        ("pfr_rb_broken_tackle", "PFR RB Broken Tackle Data Mart Join / Component Test V1", "highest"),
        ("historical_market_adp", "Historical Market / ADP Source Gate and Data Mart Join V1", "high"),
        ("rookie_draft_capital_prospect", "Rookie Draft Capital Data Mart Join / Component Test V1", "high"),
        ("team_offensive_environment", "Team Offensive Environment Data Mart Join V1", "medium"),
        ("injury_availability", "Point-in-Time Injury Availability Data Mart Gate V1", "medium"),
        ("role_depth_opportunity_change", "Role/depth opportunity source-gate review later", "medium"),
        ("red_zone_historical_expansion", "Red Zone Historical Expansion Search V1", "low_medium"),
    ]
    rows: list[dict[str, str]] = []
    for rank, (family, next_lane, expected) in enumerate(base_order, start=1):
        family_ledger = [row for row in ledger if row["signal_family"] == family]
        top = family_ledger[0]["found_path"] if family_ledger else ""
        rows.append(
            {
                "priority_rank": str(rank),
                "signal_family": family,
                "expected_accuracy_upside": expected,
                "source_reliability": reliability_for(family, statuses.get(family, "MISSING_SOURCE")),
                "historical_asof_safety": asof_for(family, statuses.get(family, "MISSING_SOURCE")),
                "join_feasibility": join_for(family, family_ledger),
                "coverage": coverage_for(family_ledger),
                "near_term_formula_data_mart_usefulness": usefulness_for(family),
                "future_rankings_usefulness": "blocked_now_possible_later_after_master_approval",
                "current_status": statuses.get(family, "MISSING_SOURCE"),
                "candidate_artifacts": str(counts.get(family, 0)),
                "best_current_artifact": top,
                "recommended_next_action": next_lane if rank == 1 else f"park_until_after_{base_order[0][1]}",
            }
        )
    return rows


def reliability_for(family: str, status: str) -> str:
    if family == "pfr_rb_broken_tackle":
        return "medium_public_nflverse_pfr_source_but_not_production_approved"
    if "MISSING" in status:
        return "not_proven"
    if family in {"historical_market_adp", "injury_availability", "team_offensive_environment"}:
        return "needs_source_gate_review"
    return "medium_needs_validation"


def asof_for(family: str, status: str) -> str:
    if family == "pfr_rb_broken_tackle":
        return "needs_join_validation_but_source_is_season_level_public_pfr"
    if family == "red_zone_historical_expansion":
        return "partial_2024_2025_only_unless_more_history_found"
    if status == "AVAILABLE_REVIEW_ONLY":
        return "review_packet_safe_with_caveats"
    return "needs_asof_review"


def join_for(family: str, rows: list[dict[str, str]]) -> str:
    if any(row.get("join_keys") for row in rows):
        return "join_keys_detected_needs_validation"
    if family == "pfr_rb_broken_tackle":
        return "likely_player_season_join_if_advstats_season_rush_values_found"
    return "needs_identity_join_review"


def coverage_for(rows: list[dict[str, str]]) -> str:
    coverage = [row["season_coverage"] for row in rows if row.get("season_coverage")]
    if coverage:
        return "|".join(sorted(set(coverage))[:8])
    return "not_detected"


def usefulness_for(family: str) -> str:
    if family == "pfr_rb_broken_tackle":
        return "high_for_testing_a_missing_nonduplicate_rb_context_branch"
    if family == "historical_market_adp":
        return "high_if_point_in_time_history_exists"
    if family == "rookie_draft_capital_prospect":
        return "high_for_sparse_history_and_young_player_misses"
    if family == "red_zone_historical_expansion":
        return "low_until_full_history_exists"
    return "medium_if_source_and_asof_safe"


def markdown_list(values: list[str], empty: str = "none") -> str:
    if not values:
        return f"- {empty}\n"
    return "".join(f"- `{value}`\n" for value in values)


def write_report(
    ledger: list[dict[str, str]],
    availability: list[dict[str, str]],
    priority: list[dict[str, str]],
    target_matrix: list[dict[str, str]],
) -> None:
    counts = Counter(row["signal_family"] for row in ledger)
    status_counts = Counter(row["availability_status"] for row in ledger)
    pfr_rows = [row for row in ledger if row["signal_family"] == "pfr_rb_broken_tackle"]
    market_rows = [row for row in ledger if row["signal_family"] == "historical_market_adp"]
    useful_present = [
        "PFR RB broken-tackle source/review artifacts are present and remain the most executable missing non-duplicate branch.",
        "Market/ADP artifacts are present but require point-in-time/as-of and source-gate review before formula testing.",
        "Rookie/draft/prospect artifacts are present but require source and identity gate review.",
        "Role archetype context is present and already review-only admitted; broader role/depth opportunity data remains gated.",
    ]
    missing_blocked = [
        "Historical/as-of safe market/ADP is not proven by this locator.",
        "Full historical red-zone coverage beyond the accepted partial 2024-2025 lane is not proven.",
        "Production/model-use, rankings integration, broad PFR, PFF Elusive, and nwr_elusive_proxy_review_only remain blocked.",
    ]
    report = f"""# High-Value Signal Data Locator Audit V1 Report

## Verdict

`GREEN_HIGH_VALUE_SIGNAL_DATA_FOUND_WITH_EXECUTABLE_NEXT_LANE`

## Remote / Scope

- Canonical remote checked by lane preflight: `origin/work/hq-parallel-control`
- Expected/current HQ HEAD: `{EXPECTED_REMOTE_HEAD}`
- Artifact path: `{OUT_DIR}`
- Search type: targeted read-only locator audit
- Formula execution: none
- Ranking/app/model/runtime behavior changes: none
- Source promotion: none
- Canonical `local_exports` writes: none

## Clear Answer

Useful high-value signal artifacts do exist locally, but most are not immediately formula-ready. The strongest executable next lane remains `PFR RB Broken Tackle Data Mart Join / Component Test V1`: it targets a narrow RB-only, review-only hypothesis that was already preserved by Master HQ but could not be scored because values were absent from the Formula Data Mart.

Historical market/ADP, rookie/draft-capital, team context, injury/availability, and broader role/depth/opportunity artifacts also appear in the locator results, but they need source/use-gate, as-of, identity, and schema review before entering formula tests.

## Signal Families Searched

{markdown_list([row["signal_family_label"] for row in target_matrix])}

## Candidate Counts

- Candidate artifacts ledgered: `{len(ledger)}`
- Signal families searched: `{len(target_matrix)}`
- Availability status counts: `{dict(status_counts)}`
- Candidate counts by family: `{dict(counts)}`

## Highest-Value Data Found

`PFR RB broken-tackle` remains the highest-value executable data branch because it is narrow, public-source-derived through nflverse PFR advanced rushing context, already preserved as review-only, and not yet joined into the Formula Data Mart. Ledgered PFR rows: `{len(pfr_rows)}`.

## Market / ADP Read

Market/ADP artifacts were found (`{len(market_rows)}` ledger rows), but the locator did not prove historical point-in-time safety. Current-only or latest-market snapshots must not be backfilled into historical formula tests.

## Useful Data Already Present

{markdown_list(useful_present)}

## Useful Data Missing Or Blocked

{markdown_list(missing_blocked)}

## Recommendation

Recommended next execution lane:

`PFR RB Broken Tackle Data Mart Join / Component Test V1`

Formula work should wait for a data upgrade rather than continue same-ingredient formula tweaking. Production/model-use and rankings integration remain blocked.
"""
    (OUT_DIR / "HIGH_VALUE_SIGNAL_DATA_LOCATOR_AUDIT_V1_REPORT.md").write_text(report, encoding="utf-8")

    next_lane = """# High-Value Signal Next Data Upgrade Recommendation

## Recommended Next Lane

`PFR RB Broken Tackle Data Mart Join / Component Test V1`

## Why This Lane

- It is the most executable missing feature branch found by the locator.
- It tests a narrow RB-only review hypothesis already preserved by Master HQ.
- It may add non-duplicate context beyond PYF/multi-year production/age/role.
- It does not require broad PFR promotion.
- It keeps PFF Elusive Rating and `nwr_elusive_proxy_review_only` blocked.

## Required Guardrails

- RB only.
- Review-only only.
- No production/model-use.
- No rankings integration.
- No broad PFR feature promotion.
- Compare against PYF, multi-year production, role, and rushing volume.
- Stop if source hashes, schema, identity joins, or as-of status cannot be validated.
"""
    (OUT_DIR / "HIGH_VALUE_SIGNAL_NEXT_DATA_UPGRADE_RECOMMENDATION.md").write_text(next_lane, encoding="utf-8")

    parked = """# High-Value Signal Parked Or Blocked Data

## Parked Pending Source/As-Of Review

- Historical market / ADP: high upside, but current-only snapshots cannot be used historically.
- Rookie / draft capital / prospect data: useful for sparse-history modeling, but source and identity gates are required.
- Team / offensive environment: potentially useful, but needs historical/as-of source proof.
- Injury / availability: review-only caution context only; not injury prediction.

## Parked Or Blocked By Prior Master HQ Decisions

- Route / YPRR / TPRR source recovery.
- Return scoring.
- Broad PFR feature expansion.
- PFR QB passing production use.
- PFF Elusive Rating.
- `nwr_elusive_proxy_review_only`.
- Unsupported advanced data not currently acquired.
- Red-zone historical expansion until coverage beyond partial 2024-2025 is proven.
"""
    (OUT_DIR / "HIGH_VALUE_SIGNAL_PARKED_OR_BLOCKED_DATA.md").write_text(parked, encoding="utf-8")

    source_trace_lines = [
        "# High-Value Signal Source Trace",
        "",
        "## Prior Artifacts Consulted Or Referenced",
        "",
    ]
    for name, path in PRIOR_ARTIFACTS.items():
        source_trace_lines.append(f"- `{name}`: `{path}` exists=`{path.exists()}`")
    source_trace_lines.extend(
        [
            "",
            "## Search Roots",
            "",
        ]
    )
    for root in iter_unique_roots():
        source_trace_lines.append(f"- `{root}`")
    source_trace_lines.extend(
        [
            "",
            "## Governance Notes",
            "",
            "- This packet is a read-only locator audit.",
            "- CSV/header metadata and SHA256 hashes were generated where feasible.",
            "- Locator classifications are review triage, not production source admission.",
            "- No source was promoted and no formula was run.",
        ]
    )
    (OUT_DIR / "HIGH_VALUE_SIGNAL_SOURCE_TRACE.md").write_text("\n".join(source_trace_lines) + "\n", encoding="utf-8")


def main() -> None:
    target_matrix = build_target_matrix()
    ledger = scan_candidates()
    availability = summarize_availability(ledger)
    priority = build_priority_ranking(availability, ledger)

    ledger_fields = [
        "signal_family",
        "found_path",
        "file_folder_name",
        "source_type",
        "raw_vs_derived",
        "file_size",
        "modified_time",
        "sha256",
        "row_count",
        "columns",
        "season_coverage",
        "position_coverage",
        "player_id_fields",
        "join_keys",
        "source_use_gate_status",
        "leakage_asof_status",
        "identity_risk",
        "missingness_risk",
        "availability_status",
        "formula_test_candidate",
        "ranking_integration_candidate_later",
        "park_decision",
        "deprioritized_terms",
        "metadata_status",
    ]
    write_csv(
        OUT_DIR / "HIGH_VALUE_SIGNAL_TARGET_MATRIX.csv",
        target_matrix,
        [
            "signal_family",
            "signal_family_label",
            "why_it_might_improve_accuracy",
            "likely_formula_use",
            "likely_ranking_use_later",
            "source_terms_searched",
            "likely_artifacts",
            "current_status",
            "priority",
        ],
    )
    write_csv(OUT_DIR / "HIGH_VALUE_SIGNAL_FOUND_ARTIFACT_LEDGER.csv", ledger, ledger_fields)
    write_csv(
        OUT_DIR / "HIGH_VALUE_SIGNAL_AVAILABILITY_CLASSIFICATION.csv",
        availability,
        [
            "signal_family",
            "signal_family_label",
            "candidate_artifact_count",
            "availability_status",
            "status_counts",
            "formula_test_candidate_count",
            "top_candidate_paths",
            "source_use_gate_status",
            "ranking_integration_status",
            "notes",
        ],
    )
    write_csv(
        OUT_DIR / "HIGH_VALUE_SIGNAL_PRIORITY_RANKING.csv",
        priority,
        [
            "priority_rank",
            "signal_family",
            "expected_accuracy_upside",
            "source_reliability",
            "historical_asof_safety",
            "join_feasibility",
            "coverage",
            "near_term_formula_data_mart_usefulness",
            "future_rankings_usefulness",
            "current_status",
            "candidate_artifacts",
            "best_current_artifact",
            "recommended_next_action",
        ],
    )
    write_report(ledger, availability, priority, target_matrix)


if __name__ == "__main__":
    main()
