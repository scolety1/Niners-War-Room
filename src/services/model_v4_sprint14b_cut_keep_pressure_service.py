from __future__ import annotations

import csv
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.services.model_v4_sprint14_15_calibration_service import DEFAULT_OUTPUT_ROOT

SPRINT_14B_VERSION = "model_v4_sprint_14b_cut_keep_pressure_review_0.1.0"
SPRINT_14A_ROSTER = DEFAULT_OUTPUT_ROOT / "niners_roster_state_review.csv"
SPRINT_14A_CONTRACT = DEFAULT_OUTPUT_ROOT / "niners_deadline_contract.csv"
SPRINT_14A_RECEIPTS = DEFAULT_OUTPUT_ROOT / "niners_roster_asset_receipts.csv"
SPRINT_14A_WARNINGS = DEFAULT_OUTPUT_ROOT / "niners_roster_contract_warnings.csv"
SPRINT_15_FIXTURES = DEFAULT_OUTPUT_ROOT / "cross_model_calibration_fixture_rows.csv"
DEFAULT_14B_OUTPUT_ROOT = Path("local_exports/model_v4/decision_pressure/latest")
DEFAULT_PACKET_ROOT = Path("local_exports/model_v4/audit_packets")
SPRINT14B_DOC = Path("docs/model_v4/SPRINT_14B_CUT_KEEP_PRESSURE_MODEL.md")
SPRINT14B_AUDIT_PROMPT = Path("docs/model_v4/SPRINT_14B_EXTERNAL_AUDIT_PROMPT.md")

PRESSURE_HEADER = (
    "pressure_key",
    "player_name",
    "position",
    "nfl_team",
    "league_rank",
    "dynasty_asset_value_review_score",
    "confidence_cap",
    "roster_value_rank",
    "position_depth_rank",
    "pressure_score",
    "pressure_band",
    "protection_factors",
    "risk_factors",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

COMPONENT_HEADER = (
    "pressure_key",
    "player_name",
    "component_name",
    "component_value",
    "component_direction",
    "component_weight",
    "component_contribution",
    "source_status",
    "receipt_pointer",
    "formula_version",
)

RECEIPT_HEADER = (
    "pressure_key",
    "player_name",
    "receipt_layer",
    "feature_group",
    "receipt_pointer",
    "source_status",
    "formula_version",
)

WARNING_HEADER = (
    "pressure_key",
    "player_name",
    "warning_layer",
    "severity",
    "warning_code",
    "warning_detail",
    "next_action",
    "formula_version",
)

SUMMARY_HEADER = (
    "summary_key",
    "summary_value",
    "source",
    "allowed_use",
    "formula_version",
)


@dataclass(frozen=True)
class CutKeepPressureResult:
    pressure_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class CutKeepPressurePaths:
    pressure_rows: Path
    component_rows: Path
    receipts: Path
    warnings: Path
    summary: Path
    doc: Path
    audit_prompt: Path
    audit_packet: Path


def build_cut_keep_pressure_outputs(
    *,
    roster_path: str | Path = SPRINT_14A_ROSTER,
    contract_path: str | Path = SPRINT_14A_CONTRACT,
) -> CutKeepPressureResult:
    roster_rows = _read_rows(Path(roster_path))
    contract_rows = _read_rows(Path(contract_path))
    protect_limit = _contract_int(contract_rows, "protect_limit_inferred", 23)
    pressure_count = _contract_int(contract_rows, "minimum_roster_pressure_count", 0)
    ranked_rows = sorted(
        roster_rows,
        key=lambda row: _float(row.get("dynasty_asset_value_review_score"), -1.0) or -1.0,
        reverse=True,
    )
    value_rank = {row["roster_key"]: index + 1 for index, row in enumerate(ranked_rows)}
    position_rank = _position_depth_ranks(ranked_rows)
    pressure_rows = tuple(
        _pressure_row(
            row,
            roster_value_rank=value_rank[row["roster_key"]],
            position_depth_rank=position_rank[row["roster_key"]],
            protect_limit=protect_limit,
            pressure_count=pressure_count,
        )
        for row in roster_rows
    )
    component_rows = tuple(
        component
        for row in pressure_rows
        for component in _component_rows(row)
    )
    receipt_rows = tuple(_receipt_row(row) for row in pressure_rows)
    warning_rows = _warning_rows(pressure_rows, pressure_count)
    summary_rows = _summary_rows(pressure_rows, protect_limit, pressure_count)
    summary = {
        "review_status": "review_only",
        "roster_rows": len(roster_rows),
        "pressure_rows": len(pressure_rows),
        "minimum_roster_pressure_count": pressure_count,
        "protect_limit": protect_limit,
        "final_recommendations_created": False,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return CutKeepPressureResult(
        pressure_rows=pressure_rows,
        component_rows=component_rows,
        receipt_rows=receipt_rows,
        warning_rows=warning_rows,
        summary_rows=summary_rows,
        summary=summary,
    )


def write_cut_keep_pressure_outputs(
    *,
    output_root: str | Path = DEFAULT_14B_OUTPUT_ROOT,
    packet_root: str | Path = DEFAULT_PACKET_ROOT,
    result: CutKeepPressureResult | None = None,
) -> CutKeepPressurePaths:
    result = result or build_cut_keep_pressure_outputs()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    packet_path = Path(packet_root) / "sprint14b_cut_keep_pressure_audit_packet_20260518.zip"
    paths = CutKeepPressurePaths(
        pressure_rows=output / "cut_keep_pressure_review_rows.csv",
        component_rows=output / "cut_keep_pressure_component_rows.csv",
        receipts=output / "cut_keep_pressure_receipts.csv",
        warnings=output / "cut_keep_pressure_warnings.csv",
        summary=output / "cut_keep_pressure_summary.csv",
        doc=SPRINT14B_DOC,
        audit_prompt=SPRINT14B_AUDIT_PROMPT,
        audit_packet=packet_path,
    )
    _write_csv(paths.pressure_rows, PRESSURE_HEADER, result.pressure_rows)
    _write_csv(paths.component_rows, COMPONENT_HEADER, result.component_rows)
    _write_csv(paths.receipts, RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_csv(paths.summary, SUMMARY_HEADER, result.summary_rows)
    _write_text(paths.doc, _doc(result, paths))
    _write_text(paths.audit_prompt, _audit_prompt(paths))
    _write_packet(paths, packet_path)
    return paths


def _pressure_row(
    row: dict[str, str],
    *,
    roster_value_rank: int,
    position_depth_rank: int,
    protect_limit: int,
    pressure_count: int,
) -> dict[str, object]:
    score = _float(row.get("dynasty_asset_value_review_score"), 0.0) or 0.0
    confidence = _float(row.get("confidence_cap"), 0.75) or 0.75
    league_rank = _float(row.get("league_rank"))
    rank_pressure = max(0.0, (roster_value_rank - protect_limit) * 12.0)
    value_pressure = max(0.0, 55.0 - score)
    confidence_pressure = max(0.0, (0.9 - confidence) * 30.0)
    league_rank_pressure = 0.0 if league_rank is None else max(0.0, (league_rank - 180.0) / 4.0)
    depth_pressure = max(0.0, (position_depth_rank - _position_soft_limit(row["position"])) * 5.0)
    pressure_score = round(
        min(
            100.0,
            rank_pressure
            + (value_pressure * 0.75)
            + confidence_pressure
            + league_rank_pressure
            + depth_pressure,
        ),
        4,
    )
    protection = _protection_factors(row, roster_value_rank, score)
    risk = _risk_factors(row, roster_value_rank, position_depth_rank, pressure_score)
    return {
        "pressure_key": row["roster_key"],
        "player_name": row["player_name"],
        "position": row["position"],
        "nfl_team": row["nfl_team"],
        "league_rank": row["league_rank"],
        "dynasty_asset_value_review_score": score,
        "confidence_cap": confidence,
        "roster_value_rank": roster_value_rank,
        "position_depth_rank": position_depth_rank,
        "pressure_score": pressure_score,
        "pressure_band": _pressure_band(
            pressure_score,
            roster_value_rank,
            protect_limit,
            pressure_count,
        ),
        "protection_factors": "|".join(protection),
        "risk_factors": "|".join(risk),
        "allowed_use": "review_only_cut_keep_pressure_not_final_decision",
        "blocked_use": "do_not_use_as_cut_keep_recommendation",
        "warning_flags": _join_flags(
            row.get("warning_flags"),
            "review_only_no_cut_keep_recommendation",
        ),
        "formula_version": SPRINT_14B_VERSION,
    }


def _position_soft_limit(position: str) -> int:
    return {"QB": 2, "RB": 6, "WR": 9, "TE": 3}.get(position, 6)


def _pressure_band(
    pressure_score: float,
    roster_value_rank: int,
    protect_limit: int,
    pressure_count: int,
) -> str:
    if roster_value_rank <= max(1, protect_limit - 4):
        return "protected_core_review"
    if roster_value_rank <= protect_limit:
        return "protectable_depth_review"
    if roster_value_rank <= protect_limit + max(1, pressure_count):
        return "required_pressure_zone_review"
    if pressure_score >= 50.0:
        return "extended_pressure_watch_review"
    return "depth_watch_review"


def _protection_factors(
    row: dict[str, str],
    roster_value_rank: int,
    score: float,
) -> tuple[str, ...]:
    factors: list[str] = []
    if roster_value_rank <= 12:
        factors.append("top_half_roster_value")
    if score >= 45.0:
        factors.append("above_depth_value_threshold")
    if row["position"] in {"QB", "TE"} and roster_value_rank <= 18:
        factors.append("positional_structure_protection")
    league_rank = _float(row.get("league_rank"))
    if league_rank is not None and league_rank <= 120:
        factors.append("league_rank_support")
    return tuple(factors or ["no_major_protection_factor"])


def _risk_factors(
    row: dict[str, str],
    roster_value_rank: int,
    position_depth_rank: int,
    pressure_score: float,
) -> tuple[str, ...]:
    flags = row.get("warning_flags", "")
    factors: list[str] = []
    if pressure_score >= 50.0:
        factors.append("high_review_pressure_score")
    if "missing_or_review_route_target_snap_evidence" in flags:
        factors.append("missing_role_evidence")
    if "first_down_missing_confidence_cap" in flags:
        factors.append("missing_first_down_evidence")
    if roster_value_rank > 23:
        factors.append("below_inferred_protect_line")
    if position_depth_rank > _position_soft_limit(row["position"]):
        factors.append("position_depth_pressure")
    return tuple(factors or ["no_major_pressure_factor"])


def _component_rows(row: dict[str, object]) -> tuple[dict[str, object], ...]:
    return (
        _component(
            row,
            "roster_value_rank",
            row["roster_value_rank"],
            "higher_rank_number_adds_pressure",
            0.35,
        ),
        _component(
            row,
            "dynasty_asset_value_review_score",
            row["dynasty_asset_value_review_score"],
            "lower_value_adds_pressure",
            0.30,
        ),
        _component(
            row,
            "confidence_cap",
            row["confidence_cap"],
            "lower_confidence_adds_review_pressure",
            0.15,
        ),
        _component(
            row,
            "league_rank",
            row["league_rank"],
            "lower_market_rank_adds_pressure",
            0.10,
        ),
        _component(
            row,
            "position_depth_rank",
            row["position_depth_rank"],
            "deeper_position_slot_adds_pressure",
            0.10,
        ),
    )


def _component(
    row: dict[str, object],
    name: str,
    value: object,
    direction: str,
    weight: float,
) -> dict[str, object]:
    return {
        "pressure_key": row["pressure_key"],
        "player_name": row["player_name"],
        "component_name": name,
        "component_value": value,
        "component_direction": direction,
        "component_weight": weight,
        "component_contribution": "review_visible_not_final_weight",
        "source_status": "review_only_sprint_14a_roster_contract",
        "receipt_pointer": str(SPRINT_14A_ROSTER),
        "formula_version": SPRINT_14B_VERSION,
    }


def _receipt_row(row: dict[str, object]) -> dict[str, object]:
    return {
        "pressure_key": row["pressure_key"],
        "player_name": row["player_name"],
        "receipt_layer": "sprint_14b_cut_keep_pressure",
        "feature_group": "roster_value_pressure",
        "receipt_pointer": f"{SPRINT_14A_ROSTER}|{SPRINT_14A_CONTRACT}",
        "source_status": "review_only_sprint_14a_contract",
        "formula_version": SPRINT_14B_VERSION,
    }


def _warning_rows(
    pressure_rows: tuple[dict[str, object], ...],
    pressure_count: int,
) -> tuple[dict[str, object], ...]:
    rows = [
        _warning(
            "sprint_14b",
            "Cut/keep pressure model",
            "review",
            "no_final_cut_keep_recommendations_created",
            "Sprint 14B creates pressure tiers only.",
            "Run external audit before Sprint 14C-F or any final decision board.",
        )
    ]
    pressure_zone = [
        row for row in pressure_rows if row["pressure_band"] == "required_pressure_zone_review"
    ]
    if len(pressure_zone) < pressure_count:
        rows.append(
            _warning(
                "sprint_14b_pressure_zone",
                "Required pressure zone",
                "review",
                "pressure_zone_smaller_than_minimum_pressure_count",
                "Pressure zone does not cover inferred roster pressure count.",
                "Review protect limit and roster count before decision recommendations.",
            )
        )
    rows.extend(
        _warning(
            str(row["pressure_key"]),
            str(row["player_name"]),
            "review",
            "player_in_required_pressure_zone_review",
            "Player falls immediately below inferred protect line.",
            "Review with trade and rookie-pick context before any final call.",
        )
        for row in pressure_zone
    )
    return tuple(rows)


def _warning(
    key: str,
    name: str,
    severity: str,
    code: str,
    detail: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "pressure_key": key,
        "player_name": name,
        "warning_layer": "sprint_14b_cut_keep_pressure",
        "severity": severity,
        "warning_code": code,
        "warning_detail": detail,
        "next_action": next_action,
        "formula_version": SPRINT_14B_VERSION,
    }


def _summary_rows(
    pressure_rows: tuple[dict[str, object], ...],
    protect_limit: int,
    pressure_count: int,
) -> tuple[dict[str, object], ...]:
    bands = sorted({str(row["pressure_band"]) for row in pressure_rows})
    rows = [
        _summary("roster_rows", len(pressure_rows), str(SPRINT_14A_ROSTER)),
        _summary("protect_limit", protect_limit, str(SPRINT_14A_CONTRACT)),
        _summary("minimum_roster_pressure_count", pressure_count, str(SPRINT_14A_CONTRACT)),
        _summary("final_recommendations_created", False, "sprint_14b_guardrail"),
    ]
    rows.extend(
        _summary(
            f"band_count:{band}",
            sum(1 for row in pressure_rows if row["pressure_band"] == band),
            str(DEFAULT_14B_OUTPUT_ROOT),
        )
        for band in bands
    )
    return tuple(rows)


def _summary(key: str, value: object, source: str) -> dict[str, object]:
    return {
        "summary_key": key,
        "summary_value": value,
        "source": source,
        "allowed_use": "review_only_cut_keep_pressure_summary",
        "formula_version": SPRINT_14B_VERSION,
    }


def _position_depth_ranks(rows: list[dict[str, str]]) -> dict[str, int]:
    counters: dict[str, int] = {}
    ranks: dict[str, int] = {}
    for row in rows:
        position = row["position"]
        counters[position] = counters.get(position, 0) + 1
        ranks[row["roster_key"]] = counters[position]
    return ranks


def _contract_int(rows: tuple[dict[str, str], ...], key: str, default: int) -> int:
    for row in rows:
        if row.get("contract_key") == key:
            try:
                return int(row.get("contract_value") or default)
            except ValueError:
                return default
    return default


def _doc(result: CutKeepPressureResult, paths: CutKeepPressurePaths) -> str:
    return "\n".join(
        [
            "# Sprint 14B Cut/Keep Pressure Model",
            "",
            "Sprint 14B translates the roster contract into review-only pressure tiers. "
            "It does not create cut, keep, trade, or draft recommendations.",
            "",
            "## Outputs",
            "",
            f"- `{paths.pressure_rows}`",
            f"- `{paths.component_rows}`",
            f"- `{paths.receipts}`",
            f"- `{paths.warnings}`",
            f"- `{paths.summary}`",
            "",
            "## Summary",
            "",
            f"- Roster rows: {result.summary['roster_rows']}",
            f"- Minimum roster pressure count: {result.summary['minimum_roster_pressure_count']}",
            "- Final recommendations created: False",
            "- Active rankings changed: False",
            "- Readiness unlocked: False",
        ]
    ) + "\n"


def _audit_prompt(paths: CutKeepPressurePaths) -> str:
    return "\n".join(
        [
            "# Sprint 14B External Audit Prompt",
            "",
            "Audit Sprint 14B for Model v4. The packet is review-only and must not be "
            "treated as final roster advice.",
            "",
            "Verify:",
            "- pressure bands are reasonable for a 24-player roster with protect limit 23",
            "- required pressure zone does not become a cut recommendation",
            "- protection factors and risk factors are visible and source-backed",
            "- missing evidence creates review warnings, not false certainty",
            "- market/league rank is only a secondary pressure context",
            "- no active rankings, My Team, War Board, readiness gates, or app promotion changed",
            "- whether Sprint 14C trade-away/trade-for can begin review-only",
            "",
            "Verdict options:",
            "- ready_for_sprint_14c_review_only_trade_work",
            "- needs_pressure_formula_repair",
            "- needs_roster_contract_repair",
            "- needs_source_or_identity_repair",
        ]
    ) + "\n"


def _write_packet(paths: CutKeepPressurePaths, packet_path: Path) -> None:
    files = (
        paths.pressure_rows,
        paths.component_rows,
        paths.receipts,
        paths.warnings,
        paths.summary,
        paths.doc,
        paths.audit_prompt,
        SPRINT_14A_ROSTER,
        SPRINT_14A_CONTRACT,
        SPRINT_14A_RECEIPTS,
        SPRINT_14A_WARNINGS,
        SPRINT_15_FIXTURES,
    )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    if packet_path.exists():
        packet_path.unlink()
    manifest = packet_path.with_suffix(".manifest.json")
    manifest.write_text(
        "{\n"
        f'  "created_at_utc": "{datetime.now(UTC).isoformat()}",\n'
        '  "packet_type": "model_v4_sprint14b_cut_keep_pressure_audit",\n'
        '  "review_only": true\n'
        "}\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(packet_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in (*files, manifest):
            if path.exists():
                archive.write(path, path.as_posix())


def _pressure_band_sort_key(row: dict[str, object]) -> tuple[int, float]:
    order = {
        "required_pressure_zone_review": 0,
        "extended_pressure_watch_review": 1,
        "depth_watch_review": 2,
        "protectable_depth_review": 3,
        "protected_core_review": 4,
    }
    return (
        order.get(str(row["pressure_band"]), 9),
        -(_float(row.get("pressure_score"), 0.0) or 0.0),
    )


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(rows, key=_pressure_band_sort_key) if header == PRESSURE_HEADER else rows
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _float(value: object, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _join_flags(*values: object) -> str:
    flags: list[str] = []
    for value in values:
        flags.extend(flag for flag in str(value or "").split("|") if flag)
    return "|".join(dict.fromkeys(flags))
