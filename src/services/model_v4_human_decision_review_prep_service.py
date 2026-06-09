from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_decision_board_validation_service import (
    DEFAULT_OUTPUT_ROOT as SPRINT1_ROOT,
)
from src.services.model_v4_sprint14b_cut_keep_pressure_service import DEFAULT_14B_OUTPUT_ROOT
from src.services.model_v4_sprint14c_trade_review_service import DEFAULT_OUTPUT_ROOT as TRADE_ROOT
from src.services.model_v4_sprint14d_pick_trade_defer_service import (
    DEFAULT_14D_OUTPUT_ROOT,
)
from src.services.model_v4_sprint14e_rookie_draft_review_service import (
    DEFAULT_14E_OUTPUT_ROOT,
)
from src.services.model_v4_sprint14f_june15_decision_board_service import (
    DEFAULT_14F_OUTPUT_ROOT,
)

HUMAN_REVIEW_PREP_VERSION = "model_v4_human_decision_review_prep_pack_0.1.0"
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/human_decision_review_prep/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/HUMAN_DECISION_REVIEW_PREP_PACK.md")
LEGACY_TRADE_ROOT = Path("local_exports/model_v4/trade_review/latest")
CURRENT_VALUE_ROWS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)
PROSPECT_VALUE_ROWS = Path(
    "local_exports/model_v4/prospect_value/latest/prospect_value_review_rows.csv"
)
DYNASTY_ASSET_ROWS = Path(
    "local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv"
)

SUMMARY_HEADER = (
    "summary_key",
    "summary_value",
    "review_note",
    "allowed_use",
    "formula_version",
)

CARD_HEADER = (
    "card_key",
    "review_area",
    "entity_label",
    "position",
    "review_band",
    "model_says",
    "why_it_says_it",
    "confidence_or_risk_warnings",
    "human_needs_to_decide",
    "receipt_pointer",
    "allowed_use",
    "blocked_use",
    "formula_version",
)


@dataclass(frozen=True)
class HumanDecisionReviewPrepResult:
    summary_rows: tuple[dict[str, object], ...]
    pick_review_cards: tuple[dict[str, object], ...]
    roster_pressure_cards: tuple[dict[str, object], ...]
    trade_review_cards: tuple[dict[str, object], ...]
    rookie_manual_scout_queue: tuple[dict[str, object], ...]
    veteran_risk_review_cards: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class HumanDecisionReviewPrepPaths:
    summary: Path
    pick_review_cards: Path
    roster_pressure_cards: Path
    trade_review_cards: Path
    rookie_manual_scout_queue: Path
    veteran_risk_review_cards: Path
    doc: Path


def build_human_decision_review_prep(
    *,
    sprint1_root: str | Path = SPRINT1_ROOT,
    board_root: str | Path = DEFAULT_14F_OUTPUT_ROOT,
    pressure_root: str | Path = DEFAULT_14B_OUTPUT_ROOT,
    trade_root: str | Path = TRADE_ROOT,
    pick_root: str | Path = DEFAULT_14D_OUTPUT_ROOT,
    rookie_root: str | Path = DEFAULT_14E_OUTPUT_ROOT,
    current_value_path: str | Path = CURRENT_VALUE_ROWS,
    prospect_value_path: str | Path = PROSPECT_VALUE_ROWS,
    dynasty_asset_path: str | Path = DYNASTY_ASSET_ROWS,
) -> HumanDecisionReviewPrepResult:
    sprint1 = Path(sprint1_root)
    board = Path(board_root)
    pressure = Path(pressure_root)
    trade = Path(trade_root)
    picks = Path(pick_root)
    rookies = Path(rookie_root)

    focus_rows = _read_rows(sprint1 / "decision_board_validation_focus_rows.csv")
    board_rows = _read_rows(board / "june15_decision_board_review_rows.csv")
    pressure_rows = _read_rows(pressure / "cut_keep_pressure_review_rows.csv")
    trade_away_rows = _read_first_existing_rows(
        trade / "trade_away_candidate_review_rows.csv",
        LEGACY_TRADE_ROOT / "trade_away_candidate_review_rows.csv",
    )
    trade_for_rows = _read_first_existing_rows(
        trade / "external_asset_context_review_rows.csv",
        trade / "trade_for_candidate_review_rows.csv",
        LEGACY_TRADE_ROOT / "trade_for_candidate_review_rows.csv",
    )
    pick_rows = _read_rows(picks / "niners_pick_inventory_review_rows.csv")
    defer_rows = _read_rows(picks / "pick_defer_scenario_review_rows.csv")
    rookie_candidate_rows = _read_rows(rookies / "rookie_pick_candidate_review_rows.csv")
    rookie_board_rows = _read_rows(rookies / "rookie_draft_board_review_rows.csv")
    current_rows = _read_rows(Path(current_value_path))
    prospect_rows = _read_rows(Path(prospect_value_path))
    asset_rows = _read_rows(Path(dynasty_asset_path))

    defer_by_pick = {row["current_pick_label"]: row for row in defer_rows}
    pick_cards = tuple(_pick_card(row, defer_by_pick.get(row["pick_label"])) for row in pick_rows)
    sorted_pressure_rows = sorted(
        pressure_rows,
        key=lambda row: _float(row["pressure_score"]),
        reverse=True,
    )
    roster_cards = tuple(_roster_card(row) for row in sorted_pressure_rows)
    trade_cards = (
        *(_trade_away_card(row) for row in _priority_trade_away_rows(trade_away_rows)),
        *(_trade_for_card(row) for row in _priority_trade_for_rows(trade_for_rows)),
    )
    scout_queue = tuple(
        _rookie_scout_card(row, prospect_rows, rookie_board_rows)
        for row in _rookie_scout_rows(rookie_candidate_rows, rookie_board_rows)
    )
    veteran_cards = tuple(
        _veteran_card(row) for row in _veteran_risk_rows(current_rows, asset_rows)
    )
    summary = {
        "review_status": "review_only_human_decision_prep",
        "focus_rows_source_count": len(focus_rows),
        "decision_board_rows_source_count": len(board_rows),
        "pick_review_cards": len(pick_cards),
        "roster_pressure_review_cards": len(roster_cards),
        "trade_review_cards": len(trade_cards),
        "rookie_manual_scout_queue_rows": len(scout_queue),
        "veteran_risk_review_cards": len(veteran_cards),
        "final_recommendations_created": False,
        "my_team_changed": False,
        "war_board_changed": False,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
        "app_promotion_created": False,
    }
    summary_rows = tuple(
        {
            "summary_key": key,
            "summary_value": value,
            "review_note": _summary_note(key, value),
            "allowed_use": "review_only_human_decision_prep_not_final_action",
            "formula_version": HUMAN_REVIEW_PREP_VERSION,
        }
        for key, value in summary.items()
    )
    return HumanDecisionReviewPrepResult(
        summary_rows=summary_rows,
        pick_review_cards=pick_cards,
        roster_pressure_cards=roster_cards,
        trade_review_cards=trade_cards,
        rookie_manual_scout_queue=scout_queue,
        veteran_risk_review_cards=veteran_cards,
        summary=summary,
    )


def write_human_decision_review_prep(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    result: HumanDecisionReviewPrepResult | None = None,
) -> HumanDecisionReviewPrepPaths:
    result = result or build_human_decision_review_prep()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    paths = HumanDecisionReviewPrepPaths(
        summary=output / "human_decision_review_summary.csv",
        pick_review_cards=output / "pick_review_cards.csv",
        roster_pressure_cards=output / "roster_pressure_review_cards.csv",
        trade_review_cards=output / "trade_review_cards.csv",
        rookie_manual_scout_queue=output / "rookie_manual_scout_queue.csv",
        veteran_risk_review_cards=output / "veteran_risk_review_cards.csv",
        doc=Path(doc_path),
    )
    _write_csv(paths.summary, SUMMARY_HEADER, result.summary_rows)
    _write_csv(paths.pick_review_cards, CARD_HEADER, result.pick_review_cards)
    _write_csv(paths.roster_pressure_cards, CARD_HEADER, result.roster_pressure_cards)
    _write_csv(paths.trade_review_cards, CARD_HEADER, result.trade_review_cards)
    _write_csv(paths.rookie_manual_scout_queue, CARD_HEADER, result.rookie_manual_scout_queue)
    _write_csv(paths.veteran_risk_review_cards, CARD_HEADER, result.veteran_risk_review_cards)
    _write_text(paths.doc, _doc(result, paths))
    return paths


def _pick_card(row: dict[str, str], defer: dict[str, str] | None) -> dict[str, object]:
    pick = row["pick_label"]
    baseline = row.get("pick_value_review_score", "")
    if row.get("baseline_match_status") == "missing_pick_value_baseline":
        says = (
            f"{pick} is manual-only context with no admitted exact model baseline; "
            "exact pick equivalence is blocked."
        )
        human = (
            "Treat as manual-only watchlist context. Do not use it for exact trade, draft, "
            "or cut-equivalence math."
        )
    elif defer:
        delta = defer.get("value_delta_review", "")
        says = f"{pick} has a review score of {baseline}; same-slot defer delta is {delta}."
        human = "Compare use, trade-down, and defer offers before attaching this pick to a player."
    else:
        says = f"{pick} has a review score of {baseline} with no same-slot defer row."
        human = "Review player fit and market alternatives before using the pick."
    why = (
        f"tier={row.get('tier_label', '')}; baseline={row.get('baseline_match_status', '')}; "
        f"roster_context={row.get('roster_pressure_context', '')}"
    )
    if defer:
        why += f"; defer_band={defer.get('defer_review_band', '')}"
    band = (
        defer.get("defer_review_band", row.get("baseline_match_status", ""))
        if defer
        else row.get("baseline_match_status", "")
    )
    return _card(
        key=f"pick:{pick}",
        area="pick_by_pick_review",
        entity=pick,
        position="PICK",
        band=band,
        says=says,
        why=why,
        warnings=_combine(
            row.get("warning_flags", ""),
            defer.get("warning_flags", "") if defer else "",
        ),
        human=human,
        receipt=(
            "local_exports/model_v4/pick_trade_defer/latest/"
            "niners_pick_inventory_review_rows.csv"
        ),
        blocked="do_not_use_as_pick_trade_recommendation_or_offer",
    )


def _roster_card(row: dict[str, str]) -> dict[str, object]:
    says = (
        f"{row['player_name']} has pressure score {row['pressure_score']} "
        f"and band {row['pressure_band']}."
    )
    human = "Review roster fit, role evidence, trade market, and cut pressure before any action."
    if row["pressure_band"] == "required_pressure_zone_review":
        human = "This is a priority pressure row; check trade market before any cut decision."
    return _card(
        key=f"roster:{row['pressure_key']}",
        area="roster_pressure_review",
        entity=row["player_name"],
        position=row["position"],
        band=row["pressure_band"],
        says=says,
        why=(
            f"value={row['dynasty_asset_value_review_score']}; "
            f"roster_rank={row['roster_value_rank']}; "
            f"depth_rank={row['position_depth_rank']}; risks={row['risk_factors']}"
        ),
        warnings=row["warning_flags"],
        human=human,
        receipt="local_exports/model_v4/decision_pressure/latest/cut_keep_pressure_review_rows.csv",
        blocked="do_not_use_as_cut_keep_recommendation",
    )


def _priority_trade_away_rows(rows: list[dict[str, str]]) -> tuple[dict[str, str], ...]:
    interesting = [
        row
        for row in rows
        if row["trade_away_review_band"] != "hold_context_review"
        or _float(row.get("pressure_score", "")) >= 40
    ]
    return tuple(sorted(interesting, key=lambda row: _float(row["pressure_score"]), reverse=True))


def _priority_trade_for_rows(rows: list[dict[str, str]]) -> tuple[dict[str, str], ...]:
    interesting = [
        row
        for row in rows
        if row["position_fit_context"] == "premium_flex_asset_fit_review"
        or row["trade_for_review_band"] == "elite_target_review"
    ]
    return tuple(
        sorted(
            interesting,
            key=lambda row: _float(row["dynasty_asset_value_review_score"]),
            reverse=True,
        )[:18]
    )


def _trade_away_card(row: dict[str, str]) -> dict[str, object]:
    return _card(
        key=row["trade_review_key"],
        area="trade_away_review",
        entity=row["player_name"],
        position=row["position"],
        band=row["trade_away_review_band"],
        says=f"{row['player_name']} is in {row['trade_away_review_band']}, not a sell call.",
        why=(
            f"pressure={row['pressure_score']}; "
            f"value={row['dynasty_asset_value_review_score']}; "
            f"{row['review_rationale']}"
        ),
        warnings=row["warning_flags"],
        human="Decide whether there is real market interest before any roster-pressure action.",
        receipt="local_exports/model_v4/trade_review/latest/trade_away_candidate_review_rows.csv",
        blocked="do_not_use_as_trade_offer_or_sell_call",
    )


def _trade_for_card(row: dict[str, str]) -> dict[str, object]:
    return _card(
        key=row["trade_review_key"],
        area="trade_for_target_review",
        entity=row["asset_name"],
        position=row["position"],
        band=row["trade_for_review_band"],
        says=(
            f"{row['asset_name']} is a {row['trade_for_review_band']} target context row "
            f"owned by {row['current_owner_team']}."
        ),
        why=(
            f"value={row['dynasty_asset_value_review_score']}; "
            f"fit={row['position_fit_context']}; {row['review_rationale']}"
        ),
        warnings=row["warning_flags"],
        human=(
            "Decide whether price, roster timeline, and owner behavior make an "
            "inquiry worthwhile."
        ),
        receipt="local_exports/model_v4/trade_review/latest/trade_for_candidate_review_rows.csv",
        blocked="do_not_use_as_trade_offer_or_buy_call",
    )


def _rookie_scout_rows(
    candidate_rows: list[dict[str, str]],
    board_rows: list[dict[str, str]],
) -> tuple[dict[str, str], ...]:
    selected: dict[str, dict[str, str]] = {}
    for row in candidate_rows:
        warning_flags = row.get("warning_flags", "")
        gap = abs(_float(row.get("pick_value_gap_review", "")))
        if (
            int(row.get("candidate_board_rank", "999")) <= 25
            or "missing" in warning_flags
            or "quarantined" in warning_flags
            or gap <= 8
            or row["pick_label"] == "2026 5.04"
        ):
            key = f"{row['pick_label']}:{row['prospect_name']}"
            selected[key] = row
    for row in board_rows[:20]:
        key = f"board:{row['prospect_name']}"
        warning_flags = row.get("warning_flags", "")
        if "missing" in warning_flags or "quarantined" in warning_flags:
            selected.setdefault(key, _board_as_candidate(row))
    return tuple(
        sorted(
            selected.values(),
            key=lambda row: (
                _pick_sort(row.get("pick_label", "9999 9.99")),
                int(row.get("candidate_board_rank", "999")),
            ),
        )
    )


def _rookie_scout_card(
    row: dict[str, str],
    prospect_rows: list[dict[str, str]],
    board_rows: list[dict[str, str]],
) -> dict[str, object]:
    prospect = _find_prospect(row["prospect_name"], prospect_rows)
    board = _find_board(row["prospect_name"], board_rows)
    score = row.get("league_format_adjusted_score", "")
    gap = row.get("pick_value_gap_review", "")
    pick = row.get("pick_label", "board_only")
    human = "Verify profile, evidence warnings, draft cost, and whether the score is real."
    if pick in {"2026 1.03", "2026 1.04"}:
        human = "Manual scout before using a premium pick; compare against trade-down/defer paths."
    elif pick == "2026 5.04":
        human = (
            "Treat as manual-only watchlist context; no exact 5.04 model baseline exists."
        )
    why_parts = [
        f"pick={pick}",
        f"rank={row.get('candidate_board_rank', '')}",
        f"score={score}",
        f"gap={gap}",
        f"candidate_band={row.get('candidate_window_band', '')}",
        f"fit={row.get('roster_fit_context', '')}",
    ]
    if prospect:
        why_parts.append(f"prospect_confidence={prospect.get('confidence_status', '')}")
        why_parts.append(f"component_weight={prospect.get('component_weight_available', '')}")
    if board:
        why_parts.append(f"board_band={board.get('draft_board_band', '')}")
    return _card(
        key=f"rookie:{pick}:{row['prospect_name']}",
        area="rookie_manual_scout_queue",
        entity=row["prospect_name"],
        position=row["position"],
        band=row.get("candidate_window_band", row.get("draft_board_band", "")),
        says=f"{row['prospect_name']} is in the {pick} scout queue with score {score}.",
        why="; ".join(part for part in why_parts if part),
        warnings=_combine(
            row.get("warning_flags", ""),
            prospect.get("warning_flags", "") if prospect else "",
            board.get("warning_flags", "") if board else "",
        ),
        human=human,
        receipt=(
            "local_exports/model_v4/rookie_draft_review/latest/"
            "rookie_pick_candidate_review_rows.csv"
        ),
        blocked="do_not_use_as_final_rookie_draft_recommendation",
    )


def _veteran_risk_rows(
    current_rows: list[dict[str, str]],
    asset_rows: list[dict[str, str]],
) -> tuple[dict[str, str], ...]:
    asset_names = {
        row["asset_name"]
        for row in asset_rows
        if row["asset_type"] == "current_player"
        and _float(row["dynasty_asset_value_review_score"]) >= 40
    }
    risk_terms = (
        "age",
        "rushing",
        "no_premium",
        "pocket",
        "fragility",
        "te_",
        "qb_",
        "role",
    )
    selected = [
        row
        for row in current_rows
        if row["player_name"] in asset_names
        and (
            any(term in row.get("warning_flags", "") for term in risk_terms)
            or any(term in row.get("role_fragility_status", "") for term in risk_terms)
            or row["position"] in {"QB", "TE", "RB"}
        )
    ]
    sorted_selected = sorted(
        selected,
        key=lambda row: _float(row["checkpoint_review_score"]),
        reverse=True,
    )
    return tuple(sorted_selected[:30])


def _veteran_card(row: dict[str, str]) -> dict[str, object]:
    if row["position"] == "QB":
        human = (
            "Check 1QB replacement gap, rushing-age risk, and market price "
            "before any QB move."
        )
    elif row["position"] == "TE":
        human = "Check no-premium replacement gap and name-value trade market before paying up."
    elif row["position"] == "RB":
        human = "Check role durability, age/window, and contender timeline before acting."
    else:
        human = "Check role durability and target-earning confidence before acting."
    return _card(
        key=f"veteran:{row['canonical_player_key']}",
        area="veteran_age_risk_review",
        entity=row["player_name"],
        position=row["position"],
        band=row.get("role_archetype", ""),
        says=(
            f"{row['player_name']} has current review score {row['checkpoint_review_score']} "
            f"with confidence cap {row['confidence_cap']}."
        ),
        why=(
            f"archetype={row.get('role_archetype', '')}; "
            f"fragility={row.get('role_fragility_status', '')}; "
            f"discipline={row.get('discipline_status', '')}; "
            f"VORP={row.get('positive_vorp_points', '')}"
        ),
        warnings=row.get("warning_flags", ""),
        human=human,
        receipt="local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv",
        blocked="do_not_use_as_final_trade_or_roster_action",
    )


def _board_as_candidate(row: dict[str, str]) -> dict[str, str]:
    return {
        "pick_label": "board_only",
        "candidate_board_rank": row["board_rank"],
        "prospect_name": row["prospect_name"],
        "position": row["position"],
        "college": row["college"],
        "nfl_team": row["nfl_team"],
        "league_format_adjusted_score": row["league_format_adjusted_score"],
        "pick_value_gap_review": "",
        "candidate_window_band": row["draft_board_band"],
        "roster_fit_context": row["roster_fit_context"],
        "warning_flags": row["warning_flags"],
    }


def _find_prospect(name: str, rows: list[dict[str, str]]) -> dict[str, str]:
    return next((row for row in rows if row["prospect_name"] == name), {})


def _find_board(name: str, rows: list[dict[str, str]]) -> dict[str, str]:
    return next((row for row in rows if row["prospect_name"] == name), {})


def _card(
    *,
    key: str,
    area: str,
    entity: str,
    position: str,
    band: str,
    says: str,
    why: str,
    warnings: str,
    human: str,
    receipt: str,
    blocked: str,
) -> dict[str, object]:
    return {
        "card_key": key,
        "review_area": area,
        "entity_label": entity,
        "position": position,
        "review_band": band,
        "model_says": says,
        "why_it_says_it": why,
        "confidence_or_risk_warnings": warnings,
        "human_needs_to_decide": human,
        "receipt_pointer": receipt,
        "allowed_use": "review_only_human_decision_prep_not_final_action",
        "blocked_use": blocked,
        "formula_version": HUMAN_REVIEW_PREP_VERSION,
    }


def _summary_note(key: str, value: object) -> str:
    if key == "final_recommendations_created":
        return "Must remain false; this prep pack is not an action board."
    if key.endswith("_changed") or key in {"readiness_unlocked", "app_promotion_created"}:
        return "Must remain false; no active surfaces may be mutated."
    return f"Review-only prep count/status: {value}"


def _doc(
    result: HumanDecisionReviewPrepResult,
    paths: HumanDecisionReviewPrepPaths,
) -> str:
    top_picks = "\n".join(
        f"- `{row['entity_label']}`: {row['model_says']}"
        for row in result.pick_review_cards
    )
    top_roster = "\n".join(
        f"- {row['entity_label']} ({row['position']}): {row['review_band']}"
        for row in result.roster_pressure_cards[:8]
    )
    top_rookies = "\n".join(
        f"- {row['entity_label']} ({row['position']}): {row['review_band']}"
        for row in result.rookie_manual_scout_queue[:12]
    )
    top_veterans = "\n".join(
        f"- {row['entity_label']} ({row['position']}): {row['review_band']}"
        for row in result.veteran_risk_review_cards[:10]
    )
    intro = (
        "This pack prepares the finished Model v4 review-only outputs for human "
        "final decision review. It does not create final cut, keep, trade, "
        "pick-defer, or rookie draft recommendations."
    )
    return f"""# Human Decision Review Prep Pack

{intro}

## Status

- Review status: `{result.summary["review_status"]}`
- Final recommendations created: {result.summary["final_recommendations_created"]}
- My Team changed: {result.summary["my_team_changed"]}
- War Board changed: {result.summary["war_board_changed"]}
- Active rankings changed: {result.summary["active_rankings_changed"]}
- Readiness unlocked: {result.summary["readiness_unlocked"]}

## Output Files

- `{paths.summary}`
- `{paths.pick_review_cards}`
- `{paths.roster_pressure_cards}`
- `{paths.trade_review_cards}`
- `{paths.rookie_manual_scout_queue}`
- `{paths.veteran_risk_review_cards}`

## Review First When You Return

1. Start with `pick_review_cards.csv`, especially `2026 1.03` and `2026 1.04`.
2. Then open `roster_pressure_review_cards.csv` and review the pressure line names.
3. Use `rookie_manual_scout_queue.csv` to scout outliers before trusting rookie scores.
4. Use `trade_review_cards.csv` for conversation targets, not offers.
5. Use `veteran_risk_review_cards.csv` for age, QB, TE, and role-window discussion.

## Pick Snapshot

{top_picks}

## Roster Pressure Snapshot

{top_roster}

## Rookie Scout Queue Snapshot

{top_rookies}

## Veteran Risk Snapshot

{top_veterans}

## Guardrail

Every row in this pack is review-only. Humans still make the final decisions.
"""


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_first_existing_rows(*paths: Path) -> list[dict[str, str]]:
    for path in paths:
        if path.exists():
            return _read_rows(path)
    return _read_rows(paths[0])


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _float(value: str | None) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def _pick_sort(pick_label: str) -> tuple[int, int, str]:
    try:
        year, slot = pick_label.split()
        round_text, pick_text = slot.split(".")
        return int(year), int(round_text) * 100 + int(pick_text), pick_label
    except ValueError:
        return 9999, 9999, pick_label


def _combine(*values: str) -> str:
    flags: dict[str, None] = {}
    for value in values:
        for flag in value.split("|"):
            if flag:
                flags[flag] = None
    return "|".join(flags)
