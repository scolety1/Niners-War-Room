from __future__ import annotations

import csv
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.config.constants import DEFAULT_DATA_PACK

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/decision_calibration/latest")
DEFAULT_PACKET_ROOT = Path("local_exports/model_v4/audit_packets")
DEFAULT_DATA_PACK_ROOT = Path(DEFAULT_DATA_PACK)
SPRINT_12_13_ROOT = Path("local_exports/model_v4")
SPRINT_14_15_VERSION = "model_v4_sprint_14a_15_review_0.1.0"

ROSTER_FILE = "fact_rosters.csv"
PICKS_FILE = "fact_future_picks.csv"
ASSET_ROWS = SPRINT_12_13_ROOT / "dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv"
ASSET_COMPONENTS = (
    SPRINT_12_13_ROOT / "dynasty_asset_value/latest/dynasty_asset_value_component_rows.csv"
)
ASSET_RECEIPTS = SPRINT_12_13_ROOT / "dynasty_asset_value/latest/dynasty_asset_value_receipts.csv"
ASSET_WARNINGS = SPRINT_12_13_ROOT / "dynasty_asset_value/latest/dynasty_asset_value_warnings.csv"
CURRENT_VALUE_ROWS = (
    SPRINT_12_13_ROOT / "current_value/latest/current_player_value_review_rows.csv"
)
PROSPECT_ROWS = SPRINT_12_13_ROOT / "prospect_value/latest/prospect_value_review_rows.csv"
PICK_BASELINES = SPRINT_12_13_ROOT / "pick_values/latest/pick_value_baselines_review.csv"

SPRINT14_DOC = Path("docs/model_v4/SPRINT_14A_NINERS_ROSTER_DEADLINE_CONTRACT.md")
SPRINT15_DOC = Path("docs/model_v4/SPRINT_15_CROSS_MODEL_CALIBRATION.md")
AUDIT_PROMPT = Path("docs/model_v4/SPRINT_14A_15_EXTERNAL_AUDIT_PROMPT.md")

ROSTER_HEADER = (
    "roster_key",
    "snapshot_date",
    "team_id",
    "team_name",
    "owner_name",
    "player_name",
    "normalized_player_name",
    "position",
    "nfl_team",
    "roster_status",
    "league_rank",
    "model_asset_key",
    "model_asset_match_status",
    "dynasty_asset_value_review_score",
    "confidence_cap",
    "value_source_layer",
    "allowed_use",
    "warning_flags",
    "formula_version",
)

CONTRACT_HEADER = (
    "contract_key",
    "contract_area",
    "contract_value",
    "source",
    "source_status",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

RECEIPT_HEADER = (
    "entity_key",
    "entity_name",
    "receipt_layer",
    "feature_group",
    "receipt_pointer",
    "source_status",
    "allowed_use",
    "formula_version",
)

WARNING_HEADER = (
    "entity_key",
    "entity_name",
    "warning_layer",
    "severity",
    "warning_code",
    "warning_detail",
    "next_action",
    "formula_version",
)

CALIBRATION_SUMMARY_HEADER = (
    "fixture_group",
    "fixture_count",
    "pass_count",
    "review_count",
    "block_count",
    "overall_status",
    "ready_for_decision_recommendations",
    "formula_version",
)

FIXTURE_HEADER = (
    "fixture_id",
    "fixture_group",
    "fixture_name",
    "players",
    "expected_football_behavior",
    "actual_model_behavior",
    "supporting_components",
    "receipt_pointers",
    "warning_codes",
    "status",
    "likely_cause",
    "next_action",
    "formula_version",
)

COMPONENT_HEADER = (
    "fixture_id",
    "entity_key",
    "entity_name",
    "entity_type",
    "component_layer",
    "component_name",
    "component_value",
    "source_status",
    "receipt_pointer",
    "formula_version",
)

SUSPICIOUS_HEADER = (
    "review_id",
    "player_name",
    "position",
    "review_type",
    "model_behavior",
    "why_suspicious",
    "severity",
    "next_action",
    "formula_version",
)

NINERS_SANITY_HEADER = (
    "player_name",
    "position",
    "league_rank",
    "model_asset_match_status",
    "dynasty_asset_value_review_score",
    "sanity_status",
    "warning_flags",
    "formula_version",
)


@dataclass(frozen=True)
class Sprint1415Result:
    roster_rows: tuple[dict[str, object], ...]
    contract_rows: tuple[dict[str, object], ...]
    roster_receipts: tuple[dict[str, object], ...]
    roster_warnings: tuple[dict[str, object], ...]
    calibration_summary_rows: tuple[dict[str, object], ...]
    fixture_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    calibration_receipts: tuple[dict[str, object], ...]
    calibration_warnings: tuple[dict[str, object], ...]
    suspicious_rows: tuple[dict[str, object], ...]
    niners_sanity_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class Sprint1415Paths:
    roster_state: Path
    deadline_contract: Path
    roster_receipts: Path
    roster_warnings: Path
    calibration_summary: Path
    calibration_fixtures: Path
    calibration_components: Path
    calibration_receipts: Path
    calibration_warnings: Path
    suspicious_rankings: Path
    niners_roster_sanity: Path
    sprint14_doc: Path
    sprint15_doc: Path
    audit_prompt: Path
    audit_packet: Path


def build_sprint14_15_review_outputs(
    *,
    data_pack_root: str | Path = DEFAULT_DATA_PACK_ROOT,
) -> Sprint1415Result:
    pack = Path(data_pack_root)
    roster_source = pack / ROSTER_FILE
    picks_source = pack / PICKS_FILE
    roster_rows_raw = _niners_roster_rows(_read_rows(roster_source))
    picks_rows = _niners_pick_rows(_read_rows(picks_source))
    asset_rows = _read_rows(ASSET_ROWS)
    asset_by_name = _index_by_normalized_name(asset_rows, "asset_name")
    current_by_name = _index_by_normalized_name(_read_rows(CURRENT_VALUE_ROWS), "player_name")

    roster_rows = tuple(
        _roster_state_row(row, asset_by_name.get(_normalize_name(row["player_name"])))
        for row in roster_rows_raw
    )
    contract_rows = _contract_rows(roster_rows, picks_rows, roster_source, picks_source)
    roster_receipts = _roster_receipts(roster_rows, roster_source, ASSET_ROWS)
    roster_warnings = _roster_warnings(roster_rows, contract_rows)
    fixture_rows = _fixture_rows(roster_rows, current_by_name, asset_by_name)
    component_rows = _fixture_component_rows(fixture_rows, asset_by_name, current_by_name)
    calibration_receipts = _calibration_receipts(fixture_rows)
    calibration_warnings = _calibration_warnings(fixture_rows)
    suspicious_rows = _suspicious_rows(asset_rows, current_by_name)
    niners_sanity_rows = _niners_sanity_rows(roster_rows)
    calibration_summary_rows = _calibration_summary_rows(fixture_rows)
    summary = {
        "formula_version": SPRINT_14_15_VERSION,
        "review_status": "review_only",
        "niners_roster_rows": len(roster_rows),
        "niners_current_pick_rows": len(picks_rows),
        "calibration_fixture_rows": len(fixture_rows),
        "suspicious_ranking_rows": len(suspicious_rows),
        "final_recommendations_created": False,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
        "market_rows_used_for_private_value": 0,
    }
    return Sprint1415Result(
        roster_rows=roster_rows,
        contract_rows=contract_rows,
        roster_receipts=roster_receipts,
        roster_warnings=roster_warnings,
        calibration_summary_rows=calibration_summary_rows,
        fixture_rows=fixture_rows,
        component_rows=component_rows,
        calibration_receipts=calibration_receipts,
        calibration_warnings=calibration_warnings,
        suspicious_rows=suspicious_rows,
        niners_sanity_rows=niners_sanity_rows,
        summary=summary,
    )


def write_sprint14_15_review_outputs(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    packet_root: str | Path = DEFAULT_PACKET_ROOT,
    result: Sprint1415Result | None = None,
) -> Sprint1415Paths:
    result = result or build_sprint14_15_review_outputs()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    packet_path = Path(packet_root) / "sprint14a_15_calibration_audit_packet_20260518.zip"
    paths = Sprint1415Paths(
        roster_state=output / "niners_roster_state_review.csv",
        deadline_contract=output / "niners_deadline_contract.csv",
        roster_receipts=output / "niners_roster_asset_receipts.csv",
        roster_warnings=output / "niners_roster_contract_warnings.csv",
        calibration_summary=output / "cross_model_calibration_summary.csv",
        calibration_fixtures=output / "cross_model_calibration_fixture_rows.csv",
        calibration_components=output / "cross_model_calibration_component_rows.csv",
        calibration_receipts=output / "cross_model_calibration_receipts.csv",
        calibration_warnings=output / "cross_model_calibration_warnings.csv",
        suspicious_rankings=output / "suspicious_ranking_review_rows.csv",
        niners_roster_sanity=output / "niners_roster_sanity_rows.csv",
        sprint14_doc=SPRINT14_DOC,
        sprint15_doc=SPRINT15_DOC,
        audit_prompt=AUDIT_PROMPT,
        audit_packet=packet_path,
    )
    _write_csv(paths.roster_state, ROSTER_HEADER, result.roster_rows)
    _write_csv(paths.deadline_contract, CONTRACT_HEADER, result.contract_rows)
    _write_csv(paths.roster_receipts, RECEIPT_HEADER, result.roster_receipts)
    _write_csv(paths.roster_warnings, WARNING_HEADER, result.roster_warnings)
    _write_csv(
        paths.calibration_summary,
        CALIBRATION_SUMMARY_HEADER,
        result.calibration_summary_rows,
    )
    _write_csv(paths.calibration_fixtures, FIXTURE_HEADER, result.fixture_rows)
    _write_csv(paths.calibration_components, COMPONENT_HEADER, result.component_rows)
    _write_csv(paths.calibration_receipts, RECEIPT_HEADER, result.calibration_receipts)
    _write_csv(paths.calibration_warnings, WARNING_HEADER, result.calibration_warnings)
    _write_csv(paths.suspicious_rankings, SUSPICIOUS_HEADER, result.suspicious_rows)
    _write_csv(paths.niners_roster_sanity, NINERS_SANITY_HEADER, result.niners_sanity_rows)
    _write_text(paths.sprint14_doc, _sprint14_doc(result, paths))
    _write_text(paths.sprint15_doc, _sprint15_doc(result, paths))
    _write_text(paths.audit_prompt, _audit_prompt(paths))
    _write_packet(paths, packet_path)
    return paths


def _niners_roster_rows(rows: tuple[dict[str, str], ...]) -> tuple[dict[str, str], ...]:
    return tuple(row for row in rows if row.get("team_name") == "Niners")


def _niners_pick_rows(rows: tuple[dict[str, str], ...]) -> tuple[dict[str, str], ...]:
    return tuple(row for row in rows if row.get("current_team_name") == "Niners")


def _roster_state_row(
    row: dict[str, str],
    asset: dict[str, str] | None,
) -> dict[str, object]:
    score = asset.get("dynasty_asset_value_review_score", "") if asset else ""
    warning_flags = _join_flags(
        row.get("warning_flags", ""),
        asset.get("warning_flags", "") if asset else "missing_model_v4_asset_match",
        "review_only_no_decision_recommendation",
    )
    return {
        "roster_key": f"niners:{_normalize_name(row['player_name'])}:{row.get('position', '')}",
        "snapshot_date": row.get("snapshot_date", ""),
        "team_id": row.get("team_id", ""),
        "team_name": row.get("team_name", ""),
        "owner_name": row.get("owner_name", ""),
        "player_name": row.get("player_name", ""),
        "normalized_player_name": _normalize_name(row.get("player_name", "")),
        "position": row.get("position", ""),
        "nfl_team": row.get("nfl_team", ""),
        "roster_status": row.get("roster_status", ""),
        "league_rank": row.get("league_rank") or row.get("official_rank", ""),
        "model_asset_key": asset.get("asset_key", "") if asset else "",
        "model_asset_match_status": "matched_model_v4_asset" if asset else "missing_model_v4_asset",
        "dynasty_asset_value_review_score": score,
        "confidence_cap": asset.get("confidence_cap", "") if asset else "",
        "value_source_layer": asset.get("value_source_layer", "") if asset else "",
        "allowed_use": "review_only_roster_contract_not_cut_keep_recommendation",
        "warning_flags": warning_flags,
        "formula_version": SPRINT_14_15_VERSION,
    }


def _contract_rows(
    roster_rows: tuple[dict[str, object], ...],
    picks_rows: tuple[dict[str, str], ...],
    roster_source: Path,
    picks_source: Path,
) -> tuple[dict[str, object], ...]:
    roster_count = len(roster_rows)
    protect_limit = 23
    pressure_count = max(0, roster_count - protect_limit)
    values = (
        (
            "league_format",
            "10-team 1QB non-PPR dynasty with first-down scoring",
            "user_project_contract",
        ),
        ("decision_deadline", "June 15", "user_project_contract"),
        ("roster_team", "Niners", str(roster_source)),
        ("current_roster_count", str(roster_count), str(roster_source)),
        ("protect_limit_inferred", str(protect_limit), "existing_app_keeper_contract"),
        ("minimum_roster_pressure_count", str(pressure_count), "derived_contract_math"),
        ("current_rookie_pick_count", str(len(picks_rows)), str(picks_source)),
        (
            "allowed_output",
            "review-only roster facts and calibration findings",
            "sprint_14a_contract",
        ),
        ("blocked_output", "final cut/keep/trade/draft recommendations", "sprint_14a_contract"),
        ("promotion_status", "no app promotion and no readiness unlock", "sprint_14a_contract"),
    )
    return tuple(
        {
            "contract_key": key,
            "contract_area": _contract_area(key),
            "contract_value": value,
            "source": source,
            "source_status": "available" if value else "missing",
            "allowed_use": "review_only_deadline_contract",
            "blocked_use": "do_not_use_as_final_decision_recommendation",
            "warning_flags": "contract_requires_external_audit_before_14b_14f",
            "formula_version": SPRINT_14_15_VERSION,
        }
        for key, value, source in values
    )


def _contract_area(key: str) -> str:
    if "roster" in key or "protect" in key:
        return "roster_constraints"
    if "pick" in key:
        return "rookie_picks"
    if "output" in key or "promotion" in key:
        return "decision_safety"
    return "league_deadline"


def _roster_receipts(
    roster_rows: tuple[dict[str, object], ...],
    roster_source: Path,
    asset_source: Path,
) -> tuple[dict[str, object], ...]:
    receipts: list[dict[str, object]] = []
    for row in roster_rows:
        receipts.append(
            _receipt(
                str(row["roster_key"]),
                str(row["player_name"]),
                "sprint_14a_roster_contract",
                "roster_source",
                str(roster_source),
                "local_data_pack_roster",
            )
        )
        if row["model_asset_match_status"] == "matched_model_v4_asset":
            receipts.append(
                _receipt(
                    str(row["roster_key"]),
                    str(row["player_name"]),
                    "sprint_14a_roster_contract",
                    "model_v4_asset_review",
                    str(asset_source),
                    "review_only_model_v4_asset_value",
                )
            )
    return tuple(receipts)


def _roster_warnings(
    roster_rows: tuple[dict[str, object], ...],
    contract_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    warnings = [
        _warning(
            "sprint_14a_contract",
            "Niners deadline contract",
            "sprint_14a_roster_contract",
            "review",
            "no_final_recommendations_created",
            "Sprint 14A defines facts and constraints only.",
            "Run calibration audit before Sprint 14B-F.",
        )
    ]
    warnings.extend(
        _warning(
            str(row["roster_key"]),
            str(row["player_name"]),
            "sprint_14a_roster_contract",
            "review",
            "missing_model_v4_asset_match",
            "Roster player did not match the Sprint 12/13 current asset table.",
            "Review identity coverage before decision recommendations.",
        )
        for row in roster_rows
        if row["model_asset_match_status"] != "matched_model_v4_asset"
    )
    pressure = next(
        row for row in contract_rows if row["contract_key"] == "minimum_roster_pressure_count"
    )
    if int(str(pressure["contract_value"])) > 0:
        warnings.append(
            _warning(
                "sprint_14a_roster_pressure",
                "Niners roster pressure",
                "sprint_14a_roster_contract",
                "review",
                "roster_pressure_exists_without_cut_recommendation",
                "Roster count exceeds inferred protect limit, but no cut recommendation was made.",
                "Use Sprint 14B only after Sprint 15 audit passes.",
            )
        )
    return tuple(warnings)


def _fixture_rows(
    roster_rows: tuple[dict[str, object], ...],
    current_by_name: dict[str, dict[str, str]],
    asset_by_name: dict[str, dict[str, str]],
) -> tuple[dict[str, object], ...]:
    fixtures = [
        _named_fixture(
            "15A",
            "elite_rb_sanity",
            ("Christian McCaffrey", "Bijan Robinson", "Jahmyr Gibbs"),
            "Elite RBs should show high role-driven value, with age/fragility warnings visible.",
            current_by_name,
            asset_by_name,
        ),
        _named_fixture(
            "15B",
            "elite_wr_sanity",
            ("Ja'Marr Chase", "Puka Nacua", "Jaxon Smith-Njigba"),
            "Elite WRs should be supported by target/production value and confidence warnings.",
            current_by_name,
            asset_by_name,
        ),
        _named_fixture(
            "15C",
            "one_qb_qb_sanity",
            ("Lamar Jackson", "Josh Allen", "Brock Purdy"),
            "QB value must be disciplined by 10-team 1QB VORP and rushing-age caution.",
            current_by_name,
            asset_by_name,
        ),
        _named_fixture(
            "15D",
            "no_premium_te_sanity",
            ("Brock Bowers", "George Kittle", "Travis Kelce"),
            "TE values require a real no-premium VORP gap and route/target support.",
            current_by_name,
            asset_by_name,
        ),
        _named_fixture(
            "15E",
            "aging_veteran_sanity",
            ("Christian McCaffrey", "Travis Kelce", "George Kittle", "Lamar Jackson"),
            "Aging veterans should retain production evidence but carry visible lifecycle risk.",
            current_by_name,
            asset_by_name,
        ),
        _niners_fixture(roster_rows),
        _movement_fixture(asset_by_name),
    ]
    return tuple(fixtures)


def _named_fixture(
    fixture_id: str,
    group: str,
    names: tuple[str, ...],
    expected: str,
    current_by_name: dict[str, dict[str, str]],
    asset_by_name: dict[str, dict[str, str]],
) -> dict[str, object]:
    current_rows = [current_by_name.get(_normalize_name(name), {}) for name in names]
    asset_rows = [asset_by_name.get(_normalize_name(name), {}) for name in names]
    missing = [name for name, row in zip(names, asset_rows, strict=False) if not row]
    warnings = _join_flags(*(row.get("warning_flags", "") for row in asset_rows if row))
    score_text = "; ".join(
        f"{row.get('asset_name', 'missing')}={row.get('dynasty_asset_value_review_score', '')}"
        for row in asset_rows
        if row
    )
    discipline = _join_flags(*(row.get("discipline_status", "") for row in current_rows if row))
    status = "block" if missing else _fixture_status(group, warnings, discipline, asset_rows)
    likely_cause = _fixture_likely_cause(group, status, warnings, discipline)
    return {
        "fixture_id": fixture_id,
        "fixture_group": group,
        "fixture_name": group.replace("_", " ").title(),
        "players": "|".join(names),
        "expected_football_behavior": expected,
        "actual_model_behavior": score_text,
        "supporting_components": f"warnings={warnings};discipline={discipline}",
        "receipt_pointers": f"{ASSET_ROWS}|{CURRENT_VALUE_ROWS}",
        "warning_codes": warnings,
        "status": status,
        "likely_cause": likely_cause,
        "next_action": _fixture_next_action(status),
        "formula_version": SPRINT_14_15_VERSION,
    }


def _fixture_status(
    group: str,
    warnings: str,
    discipline: str,
    asset_rows: list[dict[str, str]],
) -> str:
    if group == "one_qb_qb_sanity" and (
        "one_qb_small_vorp_gap_cap" in warnings or "one_qb_pocket_mid_qb_cap" in warnings
    ):
        return "pass"
    if group == "no_premium_te_sanity":
        bowers = next((row for row in asset_rows if row.get("asset_name") == "Brock Bowers"), {})
        kelce = next((row for row in asset_rows if row.get("asset_name") == "Travis Kelce"), {})
        if _float(bowers.get("dynasty_asset_value_review_score"), 0.0) < _float(
            kelce.get("dynasty_asset_value_review_score"), 0.0
        ):
            return "review"
    if "missing_or_review" in warnings or "unavailable" in warnings:
        return "review"
    return "pass"


def _fixture_likely_cause(group: str, status: str, warnings: str, discipline: str) -> str:
    if status == "pass":
        return "Model behavior matches the fixture guardrail."
    if group == "no_premium_te_sanity":
        return (
            "TE ordering may be driven by current scoring/VORP versus longer-term "
            "prospect priors."
        )
    if "unavailable" in warnings:
        return "Preferred direct evidence is missing or unavailable, so confidence warnings remain."
    if discipline:
        return f"Discipline flag visible: {discipline}."
    return "Fixture requires review before Sprint 14B-F."


def _fixture_next_action(status: str) -> str:
    if status == "pass":
        return "Keep fixture as a gate for future formula changes."
    if status == "block":
        return "Repair source or identity before decision recommendation work."
    return "Send to external audit before building decision recommendations."


def _niners_fixture(roster_rows: tuple[dict[str, object], ...]) -> dict[str, object]:
    matched = sum(
        1
        for row in roster_rows
        if row["model_asset_match_status"] == "matched_model_v4_asset"
    )
    total = len(roster_rows)
    status = "pass" if matched == total else "review"
    expected = (
        "Every Niners roster player should be visible with source-backed review "
        "context."
    )
    likely_cause = (
        "Roster identity coverage is complete."
        if status == "pass"
        else "Some roster players lack Model v4 asset rows."
    )
    return {
        "fixture_id": "15F",
        "fixture_group": "niners_roster_sanity",
        "fixture_name": "Niners Roster Sanity",
        "players": "|".join(str(row["player_name"]) for row in roster_rows),
        "expected_football_behavior": expected,
        "actual_model_behavior": f"{matched}/{total} roster players matched Model v4 assets.",
        "supporting_components": "niners_roster_state_review.csv",
        "receipt_pointers": "niners_roster_asset_receipts.csv",
        "warning_codes": _join_flags(*(str(row["warning_flags"]) for row in roster_rows)),
        "status": status,
        "likely_cause": likely_cause,
        "next_action": _fixture_next_action(status),
        "formula_version": SPRINT_14_15_VERSION,
    }


def _movement_fixture(asset_by_name: dict[str, dict[str, str]]) -> dict[str, object]:
    _ = asset_by_name
    expected = (
        "Suspicious cross-position, age, and format-sensitive outputs should be "
        "surfaced for audit."
    )
    return {
        "fixture_id": "15G",
        "fixture_group": "movement_suspicious_ranking_audit",
        "fixture_name": "Movement And Suspicious Ranking Audit",
        "players": "current_player|current_prospect|rookie_pick",
        "expected_football_behavior": expected,
        "actual_model_behavior": "Suspicious rows generated separately without formula tuning.",
        "supporting_components": "suspicious_ranking_review_rows.csv",
        "receipt_pointers": f"{ASSET_ROWS}|{CURRENT_VALUE_ROWS}|{PROSPECT_ROWS}|{PICK_BASELINES}",
        "warning_codes": "suspicious_rows_are_review_only",
        "status": "review",
        "likely_cause": "Sprint 15G is an audit surface, not a pass/fail formula mutation.",
        "next_action": (
            "External audit should decide whether any suspicious row blocks Sprint 14B-F."
        ),
        "formula_version": SPRINT_14_15_VERSION,
    }


def _fixture_component_rows(
    fixture_rows: tuple[dict[str, object], ...],
    asset_by_name: dict[str, dict[str, str]],
    current_by_name: dict[str, dict[str, str]],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for fixture in fixture_rows:
        for name in str(fixture["players"]).split("|"):
            asset = asset_by_name.get(_normalize_name(name), {})
            current = current_by_name.get(_normalize_name(name), {})
            if not asset and not current:
                continue
            rows.append(_fixture_component_row(fixture, name, asset, current))
    return tuple(rows)


def _fixture_component_row(
    fixture: dict[str, object],
    name: str,
    asset: dict[str, str],
    current: dict[str, str],
) -> dict[str, object]:
    return {
        "fixture_id": fixture["fixture_id"],
        "entity_key": asset.get("asset_key") or current.get("canonical_player_key", ""),
        "entity_name": name,
        "entity_type": asset.get("asset_type", "current_player"),
        "component_layer": asset.get("value_source_layer")
        or current.get("position_module", ""),
        "component_name": "review_value_and_warnings",
        "component_value": asset.get("dynasty_asset_value_review_score")
        or current.get("checkpoint_review_score", ""),
        "source_status": "review_only_model_v4_outputs",
        "receipt_pointer": f"{ASSET_ROWS}|{CURRENT_VALUE_ROWS}",
        "formula_version": SPRINT_14_15_VERSION,
    }


def _calibration_receipts(
    fixture_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _receipt(
            str(row["fixture_id"]),
            str(row["fixture_name"]),
            "sprint_15_cross_model_calibration",
            str(row["fixture_group"]),
            str(row["receipt_pointers"]),
            "review_only_model_v4_outputs",
        )
        for row in fixture_rows
    )


def _calibration_warnings(
    fixture_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(
        _warning(
            str(row["fixture_id"]),
            str(row["fixture_name"]),
            "sprint_15_cross_model_calibration",
            "block" if row["status"] == "block" else "review",
            f"fixture_status_{row['status']}",
            str(row["actual_model_behavior"]),
            str(row["next_action"]),
        )
        for row in fixture_rows
        if row["status"] != "pass"
    )


def _suspicious_rows(
    asset_rows: tuple[dict[str, str], ...],
    current_by_name: dict[str, dict[str, str]],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    by_name = _index_by_normalized_name(asset_rows, "asset_name")
    checks = (
        (
            "suspicious:te:bowers_kelce",
            "Brock Bowers",
            "TE ordering",
            "Brock Bowers below Travis Kelce in review-only unified value.",
            "May be current scoring/VORP dominated; audit long-term TE prior before decisions.",
        ),
        (
            "suspicious:qb:lamar",
            "Lamar Jackson",
            "QB lifecycle",
            "Lamar is capped by 1QB VORP/rushing-age discipline.",
            "Audit whether rushing age and current VORP balance match league strategy.",
        ),
        (
            "suspicious:qb:purdy",
            "Brock Purdy",
            "Pocket QB cap",
            "Brock Purdy carries one_qb_pocket_mid_qb_cap.",
            "Confirm replaceable 1QB production stays capped before trade logic.",
        ),
    )
    for review_id, name, review_type, behavior, reason in checks:
        asset = by_name.get(_normalize_name(name), {})
        current = current_by_name.get(_normalize_name(name), {})
        rows.append(
            {
                "review_id": review_id,
                "player_name": name,
                "position": asset.get("position") or current.get("position", ""),
                "review_type": review_type,
                "model_behavior": behavior,
                "why_suspicious": reason,
                "severity": "review",
                "next_action": "External audit before Sprint 14B-F.",
                "formula_version": SPRINT_14_15_VERSION,
            }
        )
    return tuple(rows)


def _niners_sanity_rows(
    roster_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for row in roster_rows:
        sanity_status = (
            "pass"
            if row["model_asset_match_status"] == "matched_model_v4_asset"
            else "review"
        )
        rows.append(
            {
            "player_name": row["player_name"],
            "position": row["position"],
            "league_rank": row["league_rank"],
            "model_asset_match_status": row["model_asset_match_status"],
            "dynasty_asset_value_review_score": row["dynasty_asset_value_review_score"],
            "sanity_status": sanity_status,
            "warning_flags": row["warning_flags"],
            "formula_version": SPRINT_14_15_VERSION,
        }
        )
    return tuple(rows)


def _calibration_summary_rows(
    fixture_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    groups = sorted({str(row["fixture_group"]) for row in fixture_rows})
    rows: list[dict[str, object]] = []
    for group in groups:
        group_rows = [row for row in fixture_rows if row["fixture_group"] == group]
        pass_count = sum(1 for row in group_rows if row["status"] == "pass")
        review_count = sum(1 for row in group_rows if row["status"] == "review")
        block_count = sum(1 for row in group_rows if row["status"] == "block")
        overall = "block" if block_count else "review" if review_count else "pass"
        rows.append(
            {
                "fixture_group": group,
                "fixture_count": len(group_rows),
                "pass_count": pass_count,
                "review_count": review_count,
                "block_count": block_count,
                "overall_status": overall,
                "ready_for_decision_recommendations": False,
                "formula_version": SPRINT_14_15_VERSION,
            }
        )
    return tuple(rows)


def _receipt(
    key: str,
    name: str,
    layer: str,
    feature_group: str,
    pointer: str,
    source_status: str,
) -> dict[str, object]:
    return {
        "entity_key": key,
        "entity_name": name,
        "receipt_layer": layer,
        "feature_group": feature_group,
        "receipt_pointer": pointer,
        "source_status": source_status,
        "allowed_use": "review_only_receipt_not_decision_recommendation",
        "formula_version": SPRINT_14_15_VERSION,
    }


def _warning(
    key: str,
    name: str,
    layer: str,
    severity: str,
    code: str,
    detail: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "entity_key": key,
        "entity_name": name,
        "warning_layer": layer,
        "severity": severity,
        "warning_code": code,
        "warning_detail": detail,
        "next_action": next_action,
        "formula_version": SPRINT_14_15_VERSION,
    }


def _sprint14_doc(result: Sprint1415Result, paths: Sprint1415Paths) -> str:
    return "\n".join(
        [
            "# Sprint 14A Niners Roster Deadline Contract",
            "",
            "Sprint 14A creates a review-only roster/deadline contract. It does not "
            "recommend cuts, keeps, trades, or rookie picks.",
            "",
            "## Outputs",
            "",
            f"- `{paths.roster_state}`",
            f"- `{paths.deadline_contract}`",
            f"- `{paths.roster_receipts}`",
            f"- `{paths.roster_warnings}`",
            "",
            "## Summary",
            "",
            f"- Niners roster rows: {result.summary['niners_roster_rows']}",
            f"- Niners current pick rows: {result.summary['niners_current_pick_rows']}",
            "- Final recommendations created: False",
            "- Active rankings changed: False",
            "- Readiness unlocked: False",
        ]
    ) + "\n"


def _sprint15_doc(result: Sprint1415Result, paths: Sprint1415Paths) -> str:
    review_count = sum(1 for row in result.fixture_rows if row["status"] == "review")
    block_count = sum(1 for row in result.fixture_rows if row["status"] == "block")
    return "\n".join(
        [
            "# Sprint 15 Cross-Model Calibration",
            "",
            "Sprint 15 runs football sanity fixtures before any decision recommendation "
            "layer. Failed or review fixtures are documented, not force-tuned.",
            "",
            "## Outputs",
            "",
            f"- `{paths.calibration_summary}`",
            f"- `{paths.calibration_fixtures}`",
            f"- `{paths.calibration_components}`",
            f"- `{paths.calibration_receipts}`",
            f"- `{paths.calibration_warnings}`",
            f"- `{paths.suspicious_rankings}`",
            f"- `{paths.niners_roster_sanity}`",
            "",
            "## Summary",
            "",
            f"- Calibration fixture rows: {result.summary['calibration_fixture_rows']}",
            f"- Review fixtures: {review_count}",
            f"- Block fixtures: {block_count}",
            "- Ready for decision recommendations: False until external audit passes.",
        ]
    ) + "\n"


def _audit_prompt(paths: Sprint1415Paths) -> str:
    return "\n".join(
        [
            "# Sprint 14A/15 External Calibration Audit Prompt",
            "",
            "Audit Model v4 Sprint 14A and Sprint 15. The packet is review-only and "
            "must not be treated as final roster advice.",
            "",
            "Verify:",
            "- the Niners roster/deadline contract is complete enough for Sprint 14B-F",
            "- no cut/keep/trade/draft recommendations were created",
            "- RB, WR, QB, and TE fixture behavior makes football sense",
            "- Lamar/Josh/Brock Purdy handling is appropriate for 10-team 1QB",
            "- TE values are disciplined for no TE premium",
            "- aging veteran warnings are visible",
            "- Niners roster sanity is sufficient",
            "- suspicious ranking rows identify any formula repair needed",
            "- market/ADP/ranking/projection context did not drive private value",
            "",
            "Verdict options:",
            "- ready_for_sprint_14b_14f_review_only_decision_work",
            "- needs_roster_contract_repair",
            "- needs_cross_model_calibration_repair",
            "- needs_formula_repair",
            "- needs_source_or_identity_repair",
            "",
            "Primary files:",
            f"- `{paths.roster_state}`",
            f"- `{paths.deadline_contract}`",
            f"- `{paths.calibration_fixtures}`",
            f"- `{paths.suspicious_rankings}`",
            f"- `{paths.niners_roster_sanity}`",
        ]
    ) + "\n"


def _write_packet(paths: Sprint1415Paths, packet_path: Path) -> None:
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    files = (
        paths.roster_state,
        paths.deadline_contract,
        paths.roster_receipts,
        paths.roster_warnings,
        paths.calibration_summary,
        paths.calibration_fixtures,
        paths.calibration_components,
        paths.calibration_receipts,
        paths.calibration_warnings,
        paths.suspicious_rankings,
        paths.niners_roster_sanity,
        paths.sprint14_doc,
        paths.sprint15_doc,
        paths.audit_prompt,
        Path("docs/model_v4/PHASE_10O_FORMULA_REQUIREMENTS_LOCK.md"),
        Path("docs/model_v4/PHASE_11A_FORMULA_CONTRACT.md"),
        Path("docs/model_v4/PHASE_11B_REPLACEMENT_VORP_CORE.md"),
        Path("docs/model_v4/PHASE_11G_CURRENT_VALUE_CHECKPOINT.md"),
        Path("docs/model_v4/SPRINT_12_13_REVIEW_EXTERNAL_AUDIT_PROMPT.md"),
        Path("docs/model_v4/PHASE_11G_EXTERNAL_AUDIT_RESULT.md"),
        ASSET_ROWS,
        PROSPECT_ROWS,
        PICK_BASELINES,
    )
    if packet_path.exists():
        packet_path.unlink()
    manifest_path = packet_path.with_suffix(".manifest.json")
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "packet_type": "model_v4_sprint14a_15_external_calibration_audit",
        "review_only": True,
        "files": [str(path) for path in files if path.exists()],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with zipfile.ZipFile(packet_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in (*files, manifest_path):
            if path.exists():
                archive.write(path, path.as_posix())


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _index(rows: tuple[dict[str, str], ...], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if row.get(key)}


def _index_by_normalized_name(
    rows: tuple[dict[str, str], ...],
    name_key: str,
) -> dict[str, dict[str, str]]:
    return {_normalize_name(row[name_key]): row for row in rows if row.get(name_key)}


def _normalize_name(value: str) -> str:
    normalized = value.lower().replace("&", "and")
    normalized = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", normalized)
    return re.sub(r"[^a-z0-9]+", "", normalized)


def _join_flags(*values: object) -> str:
    flags: list[str] = []
    for value in values:
        flags.extend(flag for flag in str(value or "").split("|") if flag)
    return "|".join(dict.fromkeys(flags))


def _float(value: object, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
