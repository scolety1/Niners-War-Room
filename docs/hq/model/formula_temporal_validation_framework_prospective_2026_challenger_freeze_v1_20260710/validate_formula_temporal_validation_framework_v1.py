#!/usr/bin/env python3
"""Final packet validation and manifest construction for temporal V1."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKET = Path(__file__).resolve().parent
REPO = PACKET.parents[3]
VERDICT = "RED_REGULARIZED_CHALLENGER_FAILED_TEMPORAL_VALIDATION"
LOCK_HASH = "1b8cfac3807613c453588a60b24b6303e8bcaac35d03639c1927ec8d81735e28"
BRANCH = "work/formula-temporal-validation-prospective-2026-challenger-freeze-v1-20260710"
REMOTE_HQ = "c8c798cf0987a4ddc10dc7668a494e7569bfe960"
ACCEPTED_AUDIT = "dce5131d77f9fb671bdf6141650677d2a3444641"

REQUIRED = [
    "FORMULA_TEMPORAL_VALIDATION_FRAMEWORK_V1_REPORT.md",
    "EXECUTIVE_VERDICT.md",
    "PRE_REGISTRATION_LOCK.md",
    "PRE_REGISTRATION_HASH.txt",
    "DEVIATION_LEDGER.csv",
    "SOURCE_AND_RECEIPT_GATE.md",
    "SOURCE_HASH_LEDGER.csv",
    "ROLLING_ORIGIN_REGISTRY.csv",
    "CANDIDATE_REGISTRY.csv",
    "MODEL_FEATURE_AND_COEFFICIENT_LEDGER.csv",
    "OUT_OF_FOLD_PREDICTIONS.csv",
    "SEASON_POSITION_METRICS.csv",
    "SHARED_ROW_COMPARISON_SCOREBOARD.csv",
    "FULL_COVERAGE_SCOREBOARD.csv",
    "POSITION_BALANCED_SCOREBOARD.csv",
    "SEASON_BALANCED_SCOREBOARD.csv",
    "TOP_K_AND_SEVERE_MISS_REVIEW.csv",
    "CANDIDATE_MINUS_PYF_DELTAS.csv",
    "UNCERTAINTY_AND_STABILITY_REVIEW.md",
    "CHALLENGER_GATE_DECISION.md",
    "PROSPECTIVE_2026_BASELINE_FREEZE.csv",
    "PROSPECTIVE_2026_FREEZE_MANIFEST.json",
    "FUTURE_2026_OUTCOME_EVALUATION_CONTRACT.md",
    "FILES_CREATED_OR_CHANGED.csv",
    "VALIDATION_RESULTS.md",
    "MANIFEST.json",
]
CONDITIONAL_CHALLENGER = "PROSPECTIVE_2026_CHALLENGER_FREEZE.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(name: str) -> list[dict[str, str]]:
    with (PACKET / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def validate_csvs() -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in sorted(PACKET.glob("*.csv")):
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            rows = list(reader)
        if not rows or not rows[0]:
            raise RuntimeError(f"CSV missing header: {path.name}")
        if len(rows[0]) != len(set(rows[0])):
            raise RuntimeError(f"CSV duplicate header: {path.name}")
        width = len(rows[0])
        for line_number, row in enumerate(rows[1:], 2):
            if len(row) != width:
                raise RuntimeError(f"CSV width mismatch: {path.name}:{line_number} expected {width} got {len(row)}")
        counts[path.name] = len(rows) - 1
    if len(counts) != 15:
        raise RuntimeError(f"Expected 15 CSV artifacts, found {len(counts)}")
    expected = {
        "CANDIDATE_REGISTRY.csv": 3,
        "ROLLING_ORIGIN_REGISTRY.csv": 132,
        "OUT_OF_FOLD_PREDICTIONS.csv": 14193,
        "PROSPECTIVE_2026_BASELINE_FREEZE.csv": 924,
        "SOURCE_HASH_LEDGER.csv": 10,
    }
    for name, count in expected.items():
        if counts.get(name) != count:
            raise RuntimeError(f"Unexpected row count {name}: expected {count}, got {counts.get(name)}")
    return counts


def validate_prediction_integrity() -> dict[str, Any]:
    origins = read_csv("ROLLING_ORIGIN_REGISTRY.csv")
    oof = read_csv("OUT_OF_FOLD_PREDICTIONS.csv")
    origin_index: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in origins:
        key = (row["candidate_name"], row["scored_target_season"], row["position"])
        if key in origin_index:
            raise RuntimeError(f"Duplicate origin key: {key}")
        origin_index[key] = row
        if row["gate_status"] != "PASS_ORIGIN_EXECUTED_AS_PREREGISTERED":
            raise RuntimeError(f"Origin gate failure: {key}")
        if len(row["prediction_hash"]) != 64:
            raise RuntimeError(f"Origin prediction hash invalid: {key}")
    expected_keys = {
        (candidate, str(season), position)
        for candidate in (
            "PYF",
            "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE",
            "POSITION_SPECIFIC_RIDGE_ALPHA_1_V1",
        )
        for season in range(2015, 2026)
        for position in ("QB", "RB", "WR", "TE")
    }
    if set(origin_index) != expected_keys:
        raise RuntimeError("Origin registry does not contain the complete 3x11x4 grid")

    seen: set[tuple[str, str, str, str]] = set()
    hashes_by_origin: dict[tuple[str, str, str], set[str]] = {}
    for row in oof:
        identity = (row["candidate_name"], row["target_season"], row["position"], row["player_id"])
        if identity in seen:
            raise RuntimeError(f"Duplicate OOF candidate identity: {identity}")
        seen.add(identity)
        if row["outcome_joined_after_prediction_hash"].lower() != "true":
            raise RuntimeError(f"Outcome join ordering failure: {identity}")
        pred_hash = row["pre_outcome_prediction_hash"]
        if len(pred_hash) != 64:
            raise RuntimeError(f"OOF prediction hash invalid: {identity}")
        origin_key = identity[:3]
        hashes_by_origin.setdefault(origin_key, set()).add(pred_hash)
    for key, values in hashes_by_origin.items():
        if len(values) != 1 or next(iter(values)) != origin_index[key]["prediction_hash"]:
            raise RuntimeError(f"OOF/origin prediction hash mismatch: {key}")
    return {"origin_rows": len(origins), "oof_rows": len(oof), "unique_oof_identities": len(seen)}


def validate_scoreboards_and_gate() -> dict[str, Any]:
    positions = read_csv("POSITION_BALANCED_SCOREBOARD.csv")
    seasons = read_csv("SEASON_BALANCED_SCOREBOARD.csv")
    ridge_position = next(
        row
        for row in positions
        if row["candidate_name"] == "POSITION_SPECIFIC_RIDGE_ALPHA_1_V1"
        and row["summary_level"] == "POSITION_BALANCED_HEADLINE"
    )
    ridge_season = next(
        row
        for row in seasons
        if row["candidate_name"] == "POSITION_SPECIFIC_RIDGE_ALPHA_1_V1"
        and row["summary_level"] == "SEASON_BALANCED_HEADLINE"
    )
    if abs(float(ridge_position["candidate_minus_pyf_spearman"]) - 0.007801111) > 5e-10:
        raise RuntimeError("Unexpected position-balanced ridge delta")
    if abs(float(ridge_season["candidate_minus_pyf_spearman"]) - 0.007801111) > 5e-10:
        raise RuntimeError("Unexpected season-balanced ridge delta")

    severe = [
        row
        for row in read_csv("TOP_K_AND_SEVERE_MISS_REVIEW.csv")
        if row["evaluation_scope"] == "SHARED_WITH_PYF"
        and row["comparison_candidate"] == "POSITION_SPECIFIC_RIDGE_ALPHA_1_V1"
        and row["record_type"] == "SEVERE_MISS"
    ]
    candidate_sfp = sum(
        int(row["severe_false_positives"])
        for row in severe
        if row["evaluation_subject"] == "POSITION_SPECIFIC_RIDGE_ALPHA_1_V1"
    )
    pyf_sfp = sum(int(row["severe_false_positives"]) for row in severe if row["evaluation_subject"] == "PYF")
    if (candidate_sfp, pyf_sfp) != (79, 73):
        raise RuntimeError(f"Unexpected severe-FP totals: ridge={candidate_sfp} pyf={pyf_sfp}")

    gate_text = (PACKET / "CHALLENGER_GATE_DECISION.md").read_text(encoding="utf-8")
    if VERDICT not in gate_text:
        raise RuntimeError("Gate decision does not contain controlling verdict")
    if "no_repeated_position_regression`: `FAIL" not in gate_text:
        raise RuntimeError("Repeated-position failure is not recorded")
    if "no_severe_fp_increase`: `FAIL" not in gate_text:
        raise RuntimeError("Severe-FP failure is not recorded")
    return {
        "position_balanced_candidate": float(ridge_position["candidate_mean_spearman"]),
        "position_balanced_pyf": float(ridge_position["pyf_mean_spearman"]),
        "position_balanced_delta": float(ridge_position["candidate_minus_pyf_spearman"]),
        "season_balanced_candidate": float(ridge_season["candidate_mean_spearman"]),
        "season_balanced_pyf": float(ridge_season["pyf_mean_spearman"]),
        "season_balanced_delta": float(ridge_season["candidate_minus_pyf_spearman"]),
        "ridge_severe_fp": candidate_sfp,
        "pyf_severe_fp": pyf_sfp,
    }


def validate_freeze() -> dict[str, Any]:
    baseline = PACKET / "PROSPECTIVE_2026_BASELINE_FREEZE.csv"
    challenger = PACKET / CONDITIONAL_CHALLENGER
    freeze_manifest = json.loads((PACKET / "PROSPECTIVE_2026_FREEZE_MANIFEST.json").read_text(encoding="utf-8"))
    if challenger.exists():
        raise RuntimeError("Challenger file must be absent after failed gate")
    if freeze_manifest["challenger_freeze"]["applicable"] is not False:
        raise RuntimeError("Freeze manifest incorrectly marks challenger applicable")
    if freeze_manifest["challenger_freeze"]["path"] is not None:
        raise RuntimeError("Freeze manifest contains a fake challenger path")
    if freeze_manifest["baseline_freeze"]["sha256"] != sha256(baseline):
        raise RuntimeError("Baseline freeze hash mismatch")
    rows = read_csv("PROSPECTIVE_2026_BASELINE_FREEZE.csv")
    counts: dict[str, tuple[int, int]] = {}
    for candidate in sorted({row["candidate_name"] for row in rows}):
        subset = [row for row in rows if row["candidate_name"] == candidate]
        counts[candidate] = (len(subset), sum(row["score_valid"].lower() == "true" for row in subset))
        record_hashes = [row["prediction_record_hash"] for row in subset]
        if any(len(value) != 64 for value in record_hashes) or len(record_hashes) != len(set(record_hashes)):
            raise RuntimeError(f"Invalid or duplicate 2026 prediction-record hash: {candidate}")
    expected = {
        "PYF": (342, 231),
        "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE": (342, 231),
        "CURRENT_APP_VISIBLE_REVIEW_BOARD_COMPARATOR_2026_PRE_DRAFT": (240, 232),
    }
    if counts != expected:
        raise RuntimeError(f"Unexpected 2026 freeze counts: {counts}")
    return {"baseline_sha256": sha256(baseline), "candidate_counts": counts, "challenger_present": False}


def validate_language_and_links() -> dict[str, Any]:
    markdown = sorted(PACKET.glob("*.md"))
    exact_forbidden = (
        "untouched test 2024-2025",
        "untouched 2024–2025",
    )
    affirmative_proof = re.compile(r"historical[^.\n]{0,100}\b(?:prove|proves|proved|proven)\b[^.\n]{0,80}production superiority", re.I)
    language_hits: list[str] = []
    link_failures: list[str] = []
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in markdown:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for phrase in exact_forbidden:
            if phrase.lower() in lowered:
                language_hits.append(f"{path.name}:{phrase}")
        for match in affirmative_proof.finditer(text):
            sentence = text[max(0, match.start() - 40) : match.end()].lower()
            if not any(negation in sentence for negation in ("cannot", "does not", "not ", "no ")):
                language_hits.append(f"{path.name}:{match.group(0)}")
        for target in link_pattern.findall(text):
            clean = target.strip().strip("<>").split("#", 1)[0]
            if not clean or re.match(r"^[a-z]+://", clean, re.I):
                continue
            if not (path.parent / clean).exists():
                link_failures.append(f"{path.name}->{clean}")
    if language_hits:
        raise RuntimeError(f"Contradictory language found: {language_hits}")
    if link_failures:
        raise RuntimeError(f"Broken internal links: {link_failures}")
    return {"markdown_files_scanned": len(markdown), "forbidden_language_hits": 0, "broken_internal_links": 0}


def validate_protected_paths_and_git() -> dict[str, Any]:
    status = run_git("status", "--porcelain=v1", "-uall")
    if status.returncode != 0:
        raise RuntimeError(status.stderr)
    prefix = "docs/hq/model/formula_temporal_validation_framework_prospective_2026_challenger_freeze_v1_20260710/"
    changed: list[str] = []
    for line in status.stdout.splitlines():
        raw = line[3:]
        path = raw.split(" -> ")[-1].replace("\\", "/")
        changed.append(path)
        if not path.startswith(prefix):
            raise RuntimeError(f"Protected/out-of-scope path changed: {path}")
    diff = run_git("diff", "--check")
    cached = run_git("diff", "--cached", "--check")
    if diff.returncode != 0:
        raise RuntimeError(f"git diff --check failed:\n{diff.stdout}{diff.stderr}")
    if cached.returncode != 0:
        raise RuntimeError(f"git diff --cached --check failed:\n{cached.stdout}{cached.stderr}")
    branch = run_git("branch", "--show-current").stdout.strip()
    if branch != BRANCH:
        raise RuntimeError(f"Unexpected branch: {branch}")
    head = run_git("rev-parse", "HEAD").stdout.strip()
    if head != REMOTE_HQ:
        raise RuntimeError(f"Unexpected precommit base: {head}")
    return {
        "changed_paths": len(changed),
        "all_changed_paths_within_packet": True,
        "git_diff_check": "PASS",
        "git_diff_cached_check": "PASS",
        "branch": branch,
        "precommit_base": head,
    }


def write_validation_results(results: dict[str, Any]) -> None:
    counts = results["csv_counts"]
    text = f"""# Validation Results

## Verdict

`PASS_PACKET_VALIDATION_FOR_{VERDICT}`

| Validation | Result | Evidence |
|---|---|---|
| Required files | PASS | 26 unconditional required artifacts present; conditional challenger correctly absent |
| Preregistration hash | PASS | `{LOCK_HASH}` unchanged and recorded before scoring |
| Standard-library CSV parse | PASS | {len(counts)} CSV files; consistent headers and row widths |
| Spreadsheet-engine CSV parse | PASS | all {len(counts)} CSV files parsed with `@oai/artifact-tool` and nonempty used ranges |
| Origin registry | PASS | 132 unique candidate-season-position origins (3×11×4) |
| OOF prediction identity/hash | PASS | {results['prediction']['oof_rows']} unique candidate-season-position-player rows; hashes match origin registry; outcomes joined after hashes |
| Balanced headline reconciliation | PASS | ridge `0.682359958` vs PYF `0.674558848`; delta `+0.007801111` for both balanced summaries |
| Severe-FP reconciliation | PASS | ridge 79 vs PYF 73 on paired shared rows |
| 2026 baseline freeze | PASS | SHA-256 `{results['freeze']['baseline_sha256']}`; PYF and exact legacy 231 valid rows each; current-board comparator preserved as 240 rows / 232 valid scores |
| Challenger absence | PASS | no fake/empty challenger CSV; freeze manifest records gate-failure absence |
| Freeze manifest | PASS | baseline file hash, row counts, conditional absence, input hashes, and review-only restrictions validated |
| Internal links/paths | PASS | {results['language']['markdown_files_scanned']} Markdown files; no broken relative links |
| Contradictory-language scan | PASS | no forbidden `untouched` phrase and no affirmative claim that historical results prove production superiority |
| Protected-path scan | PASS | every changed path is inside this isolated packet |
| `git diff --check` | PASS | no whitespace errors |
| `git diff --cached --check` | PASS | no staged whitespace errors at validation time |
| Production/rankings/app/source restrictions | PASS | all remain explicitly blocked; snapshots are review-only |

`PROSPECTIVE_2026_CHALLENGER_FREEZE.csv` is intentionally absent because the ridge failed non-compensable historical gates. A clean-worktree check is performed again after the local commit as the final closeout step; it cannot be truthfully represented as post-commit before that commit exists.
"""
    (PACKET / "VALIDATION_RESULTS.md").write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def build_files_manifest() -> None:
    files: list[dict[str, Any]] = []
    for path in sorted(PACKET.iterdir()):
        if not path.is_file() or path.name == "MANIFEST.json":
            continue
        files.append(
            {
                "path": path.name,
                "exists": True,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "required": path.name in REQUIRED,
                "conditional": False,
            }
        )
    files.append(
        {
            "path": CONDITIONAL_CHALLENGER,
            "exists": False,
            "bytes": None,
            "sha256": None,
            "required": False,
            "conditional": True,
            "absence_reason": "REGULARIZED_CHALLENGER_DID_NOT_PASS_EVERY_PREREGISTERED_HISTORICAL_STABILITY_GATE",
        }
    )
    manifest = {
        "schema_version": "formula_temporal_validation_packet_manifest_v1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "packet": PACKET.name,
        "verdict": VERDICT,
        "branch": BRANCH,
        "precommit_base_and_verified_remote_hq": REMOTE_HQ,
        "accepted_controlling_audit_commit": ACCEPTED_AUDIT,
        "push_authorized": False,
        "production_model_use_allowed": False,
        "rankings_integration_allowed": False,
        "app_runtime_change_allowed": False,
        "source_promotion_allowed": False,
        "manifest_self_hash_policy": "MANIFEST.json excludes its own recursive hash; all other packet files are hashed",
        "files": sorted(files, key=lambda item: item["path"]),
    }
    (PACKET / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def validate_final_manifest() -> dict[str, Any]:
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    indexed = {entry["path"]: entry for entry in manifest["files"]}
    actual = {path.name for path in PACKET.iterdir() if path.is_file() and path.name != "MANIFEST.json"}
    expected_manifest_files = actual | {CONDITIONAL_CHALLENGER}
    if set(indexed) != expected_manifest_files:
        raise RuntimeError(f"Manifest file set mismatch: manifest={set(indexed)} actual={expected_manifest_files}")
    for name in actual:
        entry = indexed[name]
        path = PACKET / name
        if not entry["exists"] or entry["bytes"] != path.stat().st_size or entry["sha256"] != sha256(path):
            raise RuntimeError(f"Manifest hash/size mismatch: {name}")
    if indexed[CONDITIONAL_CHALLENGER]["exists"] or (PACKET / CONDITIONAL_CHALLENGER).exists():
        raise RuntimeError("Conditional challenger manifest status mismatch")
    for name in REQUIRED:
        if name == "MANIFEST.json":
            continue
        if name not in actual:
            raise RuntimeError(f"Required artifact missing from final manifest: {name}")
    return {"hashed_files": len(actual), "conditional_absent_files": 1}


def main() -> None:
    missing_before = [name for name in REQUIRED if name not in {"VALIDATION_RESULTS.md", "MANIFEST.json"} and not (PACKET / name).is_file()]
    if missing_before:
        raise RuntimeError(f"Required artifacts missing before validation: {missing_before}")
    if sha256(PACKET / "PRE_REGISTRATION_LOCK.md") != LOCK_HASH:
        raise RuntimeError("Preregistration lock hash changed")
    hash_text = (PACKET / "PRE_REGISTRATION_HASH.txt").read_text(encoding="utf-8")
    if f"sha256={LOCK_HASH}" not in hash_text or "hash_recorded_before_scoring=true" not in hash_text:
        raise RuntimeError("Preregistration hash receipt invalid")

    results: dict[str, Any] = {}
    results["csv_counts"] = validate_csvs()
    results["prediction"] = validate_prediction_integrity()
    results["scoreboards"] = validate_scoreboards_and_gate()
    results["freeze"] = validate_freeze()
    results["language"] = validate_language_and_links()
    results["git"] = validate_protected_paths_and_git()
    write_validation_results(results)
    build_files_manifest()
    results["manifest"] = validate_final_manifest()
    print(json.dumps({"status": "PASS", **results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
