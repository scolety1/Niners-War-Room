from __future__ import annotations

import csv
import hashlib
import subprocess
from collections import defaultdict
from pathlib import Path


ARTIFACT_DIR = Path(__file__).resolve().parent
ROOT = ARTIFACT_DIR.parents[3]
SOURCE_REVIEW = (
    ROOT
    / "docs"
    / "hq"
    / "model"
    / "unified_player_universe_v0"
    / "unified_player_universe_v1_review.csv"
)
OUTSIDE_DIR = Path(r"C:\NWR_REVIEW\current_board_shadow_input_gate_v1_20260702")
OUTSIDE_EXPORT = OUTSIDE_DIR / "current_board_baseline_shadow_input_review_only.csv"

BRANCH = "work/historical-formula-candidate-shadow-implementation-prep-v1-20260702"
STARTING_HEAD = "da29ab9d8e9984c0fa5f1c3aeed075b91241b615"
DECISION = "SAFE_EXPORT_GENERATED_REVIEW_ONLY"
SELECTED = "wr_boundary_breakout_sensitivity_guard"

REQUIRED_ARTIFACTS = [
    "artifact_manifest.md",
    "current_board_shadow_input_gate_summary.md",
    "approved_input_decision.md",
    "required_baseline_export_schema.csv",
    "current_board_input_source_inventory.csv",
    "safe_export_path_decision.md",
    "manual_export_contract.md",
    "blocked_input_fields_report.md",
    "candidate_shadow_join_contract.md",
    "guardrail_report.md",
    "merge_safety_report.md",
    "next_phase_handoff.md",
    "current_board_baseline_shadow_input_sample.csv",
    "current_board_baseline_shadow_input_schema.csv",
    "current_board_baseline_shadow_input_row_count_report.csv",
]

EXPORT_FIELDS = [
    "stable_player_id",
    "player_name",
    "position",
    "team",
    "current_baseline_rank",
    "current_baseline_position_rank",
    "current_baseline_tier_bucket",
    "current_baseline_score",
    "current_baseline_score_status",
    "data_quality_status",
    "manual_review_flag",
    "review_status",
    "warning_flags",
    "source_layer",
    "source_artifact",
    "review_only",
    "candidate_formula_output_present",
    "production_approved",
    "app_wiring_allowed",
    "model_input_allowed",
]


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    OUTSIDE_DIR.mkdir(parents=True, exist_ok=True)

    source_rows = read_csv(SOURCE_REVIEW)
    export_rows = build_export_rows(source_rows)
    write_csv_path(OUTSIDE_EXPORT, export_rows)
    write_csv("current_board_baseline_shadow_input_sample.csv", export_rows[:40])
    write_csv("current_board_baseline_shadow_input_schema.csv", export_schema_rows())
    write_csv("current_board_baseline_shadow_input_row_count_report.csv", row_count_rows(export_rows))

    context = {
        "branch": BRANCH,
        "starting_head": STARTING_HEAD,
        "current_head": git("rev-parse", "HEAD"),
        "decision": DECISION,
        "selected": SELECTED,
        "source_rows": len(source_rows),
        "export_rows": len(export_rows),
        "outside_export": str(OUTSIDE_EXPORT),
        "outside_export_sha256": sha256(OUTSIDE_EXPORT),
        "source_review": str(SOURCE_REVIEW.relative_to(ROOT)),
        "positions": position_counts(export_rows),
    }

    write_text("current_board_shadow_input_gate_summary.md", summary(context))
    write_text("approved_input_decision.md", approved_input_decision(context))
    write_csv("required_baseline_export_schema.csv", required_schema_rows())
    write_csv("current_board_input_source_inventory.csv", source_inventory_rows(context))
    write_text("safe_export_path_decision.md", safe_export_path_decision(context))
    write_text("manual_export_contract.md", manual_export_contract(context))
    write_text("blocked_input_fields_report.md", blocked_input_fields_report())
    write_text("candidate_shadow_join_contract.md", candidate_shadow_join_contract(context))
    write_text("guardrail_report.md", guardrail_report(context))
    write_text("merge_safety_report.md", merge_safety_report())
    write_text("next_phase_handoff.md", next_phase_handoff(context))
    write_text("artifact_manifest.md", artifact_manifest(context))
    write_outside_readme(context)


def build_export_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    candidates = []
    for row in source_rows:
        player_id = clean(row.get("player_id"))
        rank = clean(row.get("unified_display_rank")) or clean(row.get("dynasty_rank"))
        position = clean(row.get("position")).upper()
        name = clean(row.get("player_name"))
        if not player_id or not name or not position or not rank:
            continue
        candidates.append(
            {
                "stable_player_id": player_id,
                "player_name": name,
                "position": position,
                "team": clean(row.get("nfl_team")),
                "current_baseline_rank": rank,
                "current_baseline_position_rank": "",
                "current_baseline_tier_bucket": clean(row.get("tier")),
                "current_baseline_score": "",
                "current_baseline_score_status": "NOT_INCLUDED_SCORE_NOT_PRESENT_IN_TRACKED_REVIEW_SOURCE",
                "data_quality_status": clean(row.get("data_quality_status")),
                "manual_review_flag": clean(row.get("manual_review_flag")),
                "review_status": clean(row.get("review_status")),
                "warning_flags": safe_warning_flags(row),
                "source_layer": clean(row.get("source_layer")),
                "source_artifact": str(SOURCE_REVIEW.relative_to(ROOT)).replace("\\", "/"),
                "review_only": "true",
                "candidate_formula_output_present": "false",
                "production_approved": "false",
                "app_wiring_allowed": "false",
                "model_input_allowed": "false",
            }
        )

    candidates.sort(key=lambda item: numeric_rank(item["current_baseline_rank"]))
    position_index: dict[str, int] = defaultdict(int)
    for row in candidates:
        position_index[row["position"]] += 1
        row["current_baseline_position_rank"] = str(position_index[row["position"]])
    return candidates


def safe_warning_flags(row: dict[str, str]) -> str:
    flags = []
    for field in ("data_quality_status", "manual_review_flag", "review_status"):
        value = clean(row.get(field))
        if value:
            flags.append(f"{field}:{value}")
    if clean(row.get("caveats")):
        flags.append("source_caveats_present_not_copied")
    return "|".join(flags)


def summary(context: dict[str, object]) -> str:
    return f"""# Current Board Shadow Input Gate Summary

Decision: `{context['decision']}`

This gate admits a static, review-only current-board baseline input generated from the tracked unified-player-universe review artifact:

`{context['source_review']}`

The generated full export is local-only and outside live app paths:

`{context['outside_export']}`

The repo tracks only schema, row count/checksum, and a 40-row sample.

Key results:

- Source rows inspected: `{context['source_rows']}`
- Review-only export rows: `{context['export_rows']}`
- Export checksum: `{context['outside_export_sha256']}`
- Selected candidate for later static join: `{context['selected']}`

This does not create candidate formula output, app wiring, live preview, production rankings changes, hidden sort, recommendations, model behavior, source-truth promotion, runtime behavior, or production config changes.
"""


def approved_input_decision(context: dict[str, object]) -> str:
    return f"""# Approved Input Decision

Decision: `{context['decision']}`

Rationale:

- The raw app current-board export under `local_exports/` is not tracked in the clean worktree and must not be copied into git.
- A tracked review artifact exists at `{context['source_review']}` with stable player identifiers, player names, positions, teams, display ranks, data-quality fields, and explicit `app_wiring_allowed=no` / `model_input_allowed=no` guardrails.
- This gate generated a stripped review-only baseline input from that artifact and excluded market values, ADP/vendor/projection fields, candidate outputs, production approval flags, and score components that are not present in the tracked source.

Approved use:

- Static side-by-side shadow review input only.

Blocked use:

- Production rank source.
- App ranking replacement.
- Hidden sort.
- Recommendation.
- Model input.
- Source truth.
"""


def required_schema_rows() -> list[dict[str, str]]:
    rows = [
        schema("stable_player_id", "string", "required", "Current board/player universe player id.", "identity join", "fabricated ids"),
        schema("player_name", "string", "required", "Audit/display name.", "display audit", "identity truth"),
        schema("position", "string", "required", "QB/RB/WR/TE and other current-board positions.", "filter/join", "current-only feature"),
        schema("team", "string", "optional", "Display team if available.", "display audit", "source truth feature"),
        schema("current_baseline_rank", "integer", "required", "Baseline display rank from approved review artifact.", "static comparison", "production rank replacement"),
        schema("current_baseline_position_rank", "integer", "required", "Derived from baseline rank within position for static review.", "static comparison", "hidden sort"),
        schema("current_baseline_tier_bucket", "string", "optional", "Tier/bucket if present in source artifact.", "display audit", "fabricated tier"),
        schema("current_baseline_score", "number", "optional", "Only if already display-safe in source artifact.", "static comparison", "model input"),
        schema("warning_flags", "string", "required", "Sanitized data-quality/review flags.", "human review queue", "recommendation"),
        schema("candidate_formula_output_present", "boolean", "required", "Must be false for baseline input.", "guardrail", "candidate output"),
        schema("production_approved", "boolean", "required", "Must be false.", "guardrail", "production approval"),
    ]
    return rows


def export_schema_rows() -> list[dict[str, str]]:
    descriptions = {
        "stable_player_id": "Stable current-board/player-universe id.",
        "player_name": "Display name for audit only.",
        "position": "Player position.",
        "team": "Display team where available.",
        "current_baseline_rank": "Static baseline display rank.",
        "current_baseline_position_rank": "Position rank derived from baseline order.",
        "current_baseline_tier_bucket": "Baseline tier/bucket if present.",
        "current_baseline_score": "Blank because tracked review source does not expose a safe score.",
        "current_baseline_score_status": "Why score is blank or included.",
        "data_quality_status": "Source review data-quality label.",
        "manual_review_flag": "Source review manual-review flag.",
        "review_status": "Source review status.",
        "warning_flags": "Sanitized warning summary.",
        "source_layer": "Source review layer label.",
        "source_artifact": "Tracked source artifact path.",
        "review_only": "Always true.",
        "candidate_formula_output_present": "Always false for baseline input.",
        "production_approved": "Always false.",
        "app_wiring_allowed": "Always false.",
        "model_input_allowed": "Always false.",
    }
    return [
        {
            "field_name": field,
            "field_type": infer_type(field),
            "description": descriptions[field],
            "review_only": "true",
            "production_approved": "false",
        }
        for field in EXPORT_FIELDS
    ]


def source_inventory_rows(context: dict[str, object]) -> list[dict[str, str]]:
    return [
        {
            "source_id": "raw_full_player_board_local_export",
            "path": "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv",
            "exists_in_clean_worktree": "false",
            "available_for_tracking": "false",
            "decision": "DO_NOT_TRACK_RAW_LOCAL_EXPORT",
            "notes": "Approved app source is local/ignored and not available in this clean worktree.",
        },
        {
            "source_id": "unified_player_universe_review",
            "path": context["source_review"],
            "exists_in_clean_worktree": str(SOURCE_REVIEW.exists()).lower(),
            "available_for_tracking": "true",
            "decision": "USED_FOR_SAFE_REVIEW_ONLY_EXPORT",
            "notes": "Tracked review artifact with app_wiring_allowed/model_input_allowed false; market fields stripped from generated export.",
        },
        {
            "source_id": "outcome_v2_current_player_display",
            "path": "docs/hq/outcomes/outcome_v2_horizon_20260630/outcome_v2_current_player_display.csv",
            "exists_in_clean_worktree": "true",
            "available_for_tracking": "true",
            "decision": "CONTEXT_ONLY_NOT_BASELINE",
            "notes": "Contains display probabilities/context but no baseline rank or score.",
        },
        {
            "source_id": "rankings_view_inventory",
            "path": "docs/hq/rankings_view_inventory_20260630/",
            "exists_in_clean_worktree": "true",
            "available_for_tracking": "true",
            "decision": "INVENTORY_ONLY",
            "notes": "Confirms current rank source but is not row-level baseline export.",
        },
        {
            "source_id": "shared_current_feature_gate",
            "path": r"C:\NWR_SHARED_DATA\outcome_v2_horizon\current_feature_gate\outcome_v2_current_feature_source_gate_audit.csv",
            "exists_in_clean_worktree": "external_read_only",
            "available_for_tracking": "false",
            "decision": "FEATURE_CONTEXT_ONLY_NOT_BASELINE",
            "notes": "Useful for future candidate feature input gate, not a baseline board source.",
        },
    ]


def safe_export_path_decision(context: dict[str, object]) -> str:
    return f"""# Safe Export Path Decision

Decision: `{context['decision']}`

Generated local-only export:

`{context['outside_export']}`

Checksum:

`{context['outside_export_sha256']}`

Regeneration command:

```powershell
python docs\\hq\\experiments\\current_board_shadow_input_gate_v1_20260702\\build_current_board_shadow_input_gate_v1.py
```

Why local-only:

- The generated file is a review-only baseline input derived from a tracked review artifact.
- Keeping the full export outside the repo avoids introducing a new source-of-truth-looking board file.
- The repo tracks a sample, schema, row-count report, and checksum.
"""


def manual_export_contract(context: dict[str, object]) -> str:
    return f"""# Manual Export Contract

Manual export is not required for this gate because a safe review-only export was generated.

If Tim wants a direct raw app-source baseline later, use this contract:

1. Start from a clean worktree or a read-only copy.
2. Confirm `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` exists and is the intended approved current board.
3. Export only the safe fields listed in `required_baseline_export_schema.csv`.
4. Write the resulting file outside the repo, for example:

   `C:\\NWR_REVIEW\\current_board_shadow_input_gate_v1_20260702\\current_board_baseline_shadow_input_review_only.csv`

5. Do not copy raw `local_exports` into git.
6. Do not include candidate formula outputs, market/ADP/vendor/projection fields as source truth, hidden sort fields, recommendations, production approval flags, or app wiring flags.
7. Record row count and checksum before any later static side-by-side shadow packet.

Current generated export from this gate:

- Rows: `{context['export_rows']}`
- SHA256: `{context['outside_export_sha256']}`
"""


def blocked_input_fields_report() -> str:
    return """# Blocked Input Fields Report

Blocked from baseline shadow input:

- Candidate formula output or candidate rank.
- Production approval flags.
- App wiring, live preview, hidden sort, recommendation, or model-use flags.
- Market, ADP, vendor, projection, or external value fields as source truth.
- DynastyProcess market value/rank fields as candidate inputs.
- Routes, TPRR, YPRR, route proxies, red-zone sidecars, and ambiguous `rz_att`.
- Current-only roster/status/injury/depth/schedule context as model features.
- Raw/local export paths or secrets.

The generated export keeps only static review identity, rank, position-rank, tier/bucket, and sanitized review-status fields.
"""


def candidate_shadow_join_contract(context: dict[str, object]) -> str:
    return f"""# Candidate Shadow Join Contract

Later static comparison target: `{context['selected']}`

Join keys for a future static side-by-side packet:

- Primary: `stable_player_id`
- Audit support: `player_name`, `position`, `team`

Baseline-side fields:

- `current_baseline_rank`
- `current_baseline_position_rank`
- `current_baseline_tier_bucket`
- `warning_flags`

Candidate-side fields to add later, only after a candidate feature input gate:

- `selected_candidate_shadow_score`
- `selected_candidate_shadow_rank`
- `selected_candidate_shadow_position_rank`
- `rank_delta`
- `position_rank_delta`
- `movement_bucket`
- `review_only_label`

Rules:

- Candidate rows must not overwrite baseline ranks.
- Candidate outputs must remain outside app/runtime paths.
- Missing candidate feature rows must stay missing or be labeled not-enough-information; do not convert missing values to zero.
- Non-QB/RB/WR/TE baseline rows stay baseline-only unless a future source gate explicitly admits a candidate feature path for them.
- This join may only produce static review artifacts.
"""


def guardrail_report(context: dict[str, object]) -> str:
    return f"""# Guardrail Report

Verdict: `GREEN_GUARDRAILS_INPUT_GATE_REVIEW_ONLY`

- No production formula changes.
- No model training or tuning.
- No formula promotion.
- No app wiring or live preview page.
- No production rankings behavior changes.
- No hidden sort or recommendations.
- No source-truth promotion.
- No runtime behavior or production config changes.
- No candidate output wired into NWR.
- No raw/shared/cache/local export/secrets files tracked.
- Market/ADP/vendor/projection fields are blocked as source truth.
- Routes, TPRR, YPRR, route proxies, red-zone sidecars, ambiguous `rz_att`, and current-only context remain blocked as model features.

Generated export is local-only and review-only: `{context['outside_export']}`.
"""


def merge_safety_report() -> str:
    return """# Merge Safety Report

Merge-safe changed paths:

- `docs/hq/experiments/current_board_shadow_input_gate_v1_20260702/`
- `tests/test_current_board_shadow_input_gate_v1_20260702.py`

No app/model/rank/source-truth/runtime files are changed. No raw/shared/cache/local export/secrets files are tracked.
"""


def next_phase_handoff(context: dict[str, object]) -> str:
    return f"""# Next Phase Handoff

Recommended next phase: `Historical Formula Candidate Static Current Board Shadow Packet V1`.

Use the local-only baseline input generated here:

`{context['outside_export']}`

Before adding candidate columns, run a candidate feature input gate that validates 2025 completed-season feature coverage and identity joins. Keep all outputs static and review-only.

Production promotion remains blocked.
"""


def row_count_rows(export_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = [
        {
            "metric": "total_rows",
            "value": str(len(export_rows)),
            "notes": "Rows in local-only generated baseline input export.",
        },
        {
            "metric": "outside_export_path",
            "value": str(OUTSIDE_EXPORT),
            "notes": "Full export is outside the repo and not tracked.",
        },
        {
            "metric": "outside_export_sha256",
            "value": sha256(OUTSIDE_EXPORT),
            "notes": "Checksum for local-only full export.",
        },
        {
            "metric": "sample_rows_tracked",
            "value": str(min(40, len(export_rows))),
            "notes": "Rows tracked in sample CSV.",
        },
    ]
    for position, count in sorted(position_counts(export_rows).items()):
        rows.append(
            {
                "metric": f"position_rows_{position}",
                "value": str(count),
                "notes": "Position count in generated baseline input.",
            }
        )
    return rows


def artifact_manifest(context: dict[str, object]) -> str:
    names = [name for name in REQUIRED_ARTIFACTS if name != "artifact_manifest.md"] + [
        Path(__file__).name
    ]
    rows = []
    for name in names:
        path = ARTIFACT_DIR / name
        if path.exists():
            rows.append(f"| `{name}` | `{path.stat().st_size}` | `{sha256(path)}` |")
    table = "\n".join(rows)
    return f"""# Artifact Manifest

Artifact directory: `docs/hq/experiments/current_board_shadow_input_gate_v1_20260702/`

Branch: `{context['branch']}`

Starting HEAD: `{context['starting_head']}`

Decision: `{context['decision']}`

Local-only export: `{context['outside_export']}`

| artifact | bytes | sha256 |
|---|---:|---|
{table}

All artifacts are review-only. No production approval is granted.
"""


def write_outside_readme(context: dict[str, object]) -> None:
    (OUTSIDE_DIR / "README.md").write_text(
        f"""# Current Board Shadow Input Gate V1

Decision: `{context['decision']}`

Generated file:

`{context['outside_export']}`

Use this file only for a future static side-by-side shadow review packet. Do not wire it into the app or production rankings.
""",
        encoding="utf-8",
        newline="\n",
    )


def schema(
    field_name: str,
    field_type: str,
    required: str,
    meaning: str,
    allowed_use: str,
    blocked_use: str,
) -> dict[str, str]:
    return {
        "field_name": field_name,
        "field_type": field_type,
        "required": required,
        "meaning": meaning,
        "allowed_use": allowed_use,
        "blocked_use": blocked_use,
    }


def infer_type(field: str) -> str:
    if field.endswith("_rank"):
        return "integer"
    if field in {"review_only", "candidate_formula_output_present", "production_approved", "app_wiring_allowed", "model_input_allowed"}:
        return "boolean"
    if field == "current_baseline_score":
        return "number_or_blank"
    return "string"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict[str, str]]) -> None:
    write_csv_path(ARTIFACT_DIR / name, rows)


def write_csv_path(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8", newline="\n")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_text(name: str, text: str) -> None:
    (ARTIFACT_DIR / name).write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def clean(value: object) -> str:
    return str(value or "").strip()


def numeric_rank(value: str) -> tuple[int, str]:
    try:
        return int(float(value)), value
    except ValueError:
        return 999999, value


def position_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["position"]] += 1
    return dict(counts)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


if __name__ == "__main__":
    main()
