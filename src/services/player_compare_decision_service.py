from __future__ import annotations

from dataclasses import dataclass
from typing import Any

NOT_ENOUGH_INFORMATION = "Not enough information"
MARKET_DISPLAY_ONLY_NOTE = (
    "Market context is display-only and does not determine the compare readout, "
    "rankings, trade value, or draft decision."
)
MULTI_PLAYER_COMPARE_NOTE = (
    "For 3-4 player comparisons, this page narrows review context. It does not "
    "produce a final ranking or recommendation."
)
NFLVERSE_WAIT_STATUS = "WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN"


@dataclass(frozen=True)
class PlayerDecisionSummary:
    """Visible Player Compare context summary with legacy accessors."""

    visible_context_read: str
    evidence_coverage: str
    context_note: str
    open_review_flags: tuple[str, ...]
    context_bullets: tuple[str, ...]
    display_only_market_note: str
    multi_player_note: str

    @property
    def lean(self) -> str:
        return self.visible_context_read

    @property
    def confidence(self) -> str:
        return self.evidence_coverage

    @property
    def best_use_case(self) -> str:
        return self.context_note

    @property
    def data_quality(self) -> str:
        return f"{len(self.open_review_flags)} open flag(s)"

    @property
    def reason_bullets(self) -> tuple[str, ...]:
        return self.context_bullets

    @property
    def red_flags(self) -> tuple[str, ...]:
        return self.open_review_flags


def build_player_compare_decision_summary(
    player_a: dict[str, Any],
    player_b: dict[str, Any],
    extra_players: list[dict[str, Any]] | None = None,
) -> PlayerDecisionSummary:
    """Build a visible-context readout without hidden sorting or recommendations."""

    candidates = [player_a, player_b, *(extra_players or [])]
    usable = [row for row in candidates if _player_name(row) != NOT_ENOUGH_INFORMATION]
    if len(usable) < 2:
        return PlayerDecisionSummary(
            visible_context_read=NOT_ENOUGH_INFORMATION,
            evidence_coverage=NOT_ENOUGH_INFORMATION,
            context_note="Select at least two players with visible context.",
            open_review_flags=(NOT_ENOUGH_INFORMATION,),
            context_bullets=("Select at least two players with visible context.",),
            display_only_market_note=MARKET_DISPLAY_ONLY_NOTE,
            multi_player_note="",
        )

    positions = {_field(row, "position").upper() for row in usable}
    same_position = len(positions) == 1
    context_read = _visible_context_read(usable, same_position=same_position)
    flags = _open_review_flags(usable)
    bullets = _context_bullets(usable, same_position=same_position)
    if not flags:
        flags.append("No major open review flag in visible context.")

    return PlayerDecisionSummary(
        visible_context_read=context_read,
        evidence_coverage=_evidence_coverage(usable),
        context_note=_context_note(usable, same_position=same_position),
        open_review_flags=tuple(flags[:8]),
        context_bullets=tuple(bullets[:8]) or (NOT_ENOUGH_INFORMATION,),
        display_only_market_note=MARKET_DISPLAY_ONLY_NOTE,
        multi_player_note=MULTI_PLAYER_COMPARE_NOTE if len(usable) > 2 else "",
    )


def decision_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        output.append(
            {
                "Player": _player_name(row),
                "Position": _field(row, "position"),
                "Read-only board context": _rank_signal(row),
                "Age": _field(row, "age"),
                "Tier / band": _tier_signal(row),
                "Outcome support": _outcome_signal(row),
                "Stability evidence": _stability_evidence(row),
                "Ceiling evidence": _ceiling_evidence(row),
                "Roster-window context": _roster_window_context(row),
                "Main review flags": _review_flag_signal(row),
            }
        )
    return output


def nflverse_spec_panel_rows() -> list[dict[str, str]]:
    return [
        _nflverse_spec_row(
            "Recent production",
            "player_stats weekly / seasonal",
            "Disabled until player_stats status, schema, coverage, freshness, and policy pass.",
        ),
        _nflverse_spec_row(
            "Usage / role",
            "snap_counts; player_stats weekly; depth_charts",
            "Disabled until usage datasets pass. Depth chart remains a review-only snapshot.",
        ),
        _nflverse_spec_row(
            "Availability transparency",
            "injuries; weekly_rosters; rosters; schedules; ID bridge",
            "Existing approved injury context may display; expanded nflverse panel waits.",
        ),
        _nflverse_spec_row(
            "Roster-window context",
            "ff_playerids; rosters; weekly_rosters; schedules",
            "Disabled until identity and roster-window statuses pass.",
        ),
        _nflverse_spec_row(
            "Identity and data coverage",
            "ff_playerids; rosters; weekly_rosters; player_stats; snap_counts",
            "Current page can show fallback-match notes only; deterministic bridge waits.",
        ),
    ]


def _nflverse_spec_row(panel: str, dataset: str, fallback: str) -> dict[str, str]:
    return {
        "Panel": panel,
        "Dataset dependency": dataset,
        "Status": NFLVERSE_WAIT_STATUS,
        "Safe to wire now": "No",
        "Current behavior": fallback,
    }


def _visible_context_read(rows: list[dict[str, Any]], *, same_position: bool) -> str:
    if not same_position:
        return "Different positions / roster-fit decision"
    ranks = [_visible_rank_value(row) for row in rows]
    available = [rank for rank in ranks if rank is not None]
    if len(available) < 2:
        return NOT_ENOUGH_INFORMATION
    if max(available) - min(available) <= 4:
        return "Too close to call from visible context"
    return "Visible board context differs"


def _evidence_coverage(rows: list[dict[str, Any]]) -> str:
    total = len(rows)
    if total == 0:
        return NOT_ENOUGH_INFORMATION
    rank_count = sum(1 for row in rows if _visible_rank_value(row) is not None)
    age_count = sum(1 for row in rows if _field(row, "age") != NOT_ENOUGH_INFORMATION)
    outcome_count = sum(1 for row in rows if _outcome_signal(row) != NOT_ENOUGH_INFORMATION)
    return (
        f"Visible fields: board context {rank_count}/{total}; age {age_count}/{total}; "
        f"Outcome support {outcome_count}/{total}"
    )


def _context_note(rows: list[dict[str, Any]], *, same_position: bool) -> str:
    if len(rows) > 2:
        return "Review context only; no final ranking is produced."
    if same_position:
        return "Same-position factual review; human roster fit still decides."
    return "Cross-position review; compare facts by position and roster need."


def _context_bullets(rows: list[dict[str, Any]], *, same_position: bool) -> list[str]:
    bullets = [
        "Player Compare shows visible context only.",
        "Read-only board ranks may be shown below but do not create a recommendation.",
    ]
    if same_position:
        bullets.append("Same-position rows can be reviewed side by side without a hidden ladder.")
    else:
        bullets.append("Different positions are not converted into a single player preference.")
    if len(rows) > 2:
        bullets.append(MULTI_PLAYER_COMPARE_NOTE)
    return bullets


def _open_review_flags(rows: list[dict[str, Any]]) -> list[str]:
    flags: list[str] = []
    for row in rows:
        player = _player_name(row)
        if _field(row, "age") == NOT_ENOUGH_INFORMATION:
            flags.append(f"{player}: age is {NOT_ENOUGH_INFORMATION}.")
        if _visible_rank_value(row) is None:
            flags.append(f"{player}: read-only board context is {NOT_ENOUGH_INFORMATION}.")
        if _outcome_signal(row) == NOT_ENOUGH_INFORMATION:
            flags.append(f"{player}: outcome support is {NOT_ENOUGH_INFORMATION}.")
        if _has_review_notes(row):
            flags.append(f"{player}: review notes available below.")
    return _dedupe(flags)


def _visible_rank_value(row: dict[str, Any]) -> float | None:
    for key in ("dynasty_asset_rank", "cross_asset_candidate_rank", "final_board_rank"):
        value = _float_or_none(row.get(key))
        if value is not None:
            return value
    return None


def _rank_signal(row: dict[str, Any]) -> str:
    for label, key in (
        ("NWR/Dynasty Candidate Rank (Read-Only)", "dynasty_asset_rank"),
        ("Tuned Candidate Rank (Read-Only)", "cross_asset_candidate_rank"),
        ("Frozen Baseline Rank (Read-Only)", "final_board_rank"),
    ):
        value = _field(row, key)
        if value != NOT_ENOUGH_INFORMATION:
            return f"{label}: {value}"
    return NOT_ENOUGH_INFORMATION


def _tier_signal(row: dict[str, Any]) -> str:
    for key in (
        "dynasty_asset_tier",
        "on_clock_decision_tier",
        "candidate_value_band",
        "final_tier",
    ):
        value = _field(row, key)
        if value != NOT_ENOUGH_INFORMATION:
            return value
    return NOT_ENOUGH_INFORMATION


def _outcome_signal(row: dict[str, Any]) -> str:
    value = _field(row, "outcome_applicable_summary")
    if value.lower() in {"unsupported", "no", "none"}:
        return NOT_ENOUGH_INFORMATION
    return value


def _stability_evidence(row: dict[str, Any]) -> str:
    age = _field(row, "age")
    if _has_review_notes(row):
        return "Review notes available below"
    if age != NOT_ENOUGH_INFORMATION:
        return f"Age shown: {age}"
    return NOT_ENOUGH_INFORMATION


def _ceiling_evidence(row: dict[str, Any]) -> str:
    outcome = _outcome_signal(row)
    if outcome != NOT_ENOUGH_INFORMATION:
        return outcome
    band = _field(row, "candidate_value_band")
    if band != NOT_ENOUGH_INFORMATION:
        return "Review band shown below"
    return NOT_ENOUGH_INFORMATION


def _roster_window_context(row: dict[str, Any]) -> str:
    position = _field(row, "position")
    age = _float_or_none(row.get("age"))
    if age is None:
        return NOT_ENOUGH_INFORMATION
    if age >= 30:
        return "Age-window review"
    if position == "QB":
        return "1QB format context requires human roster fit"
    return "Age context shown; roster fit is a human decision"


def _review_flag_signal(row: dict[str, Any]) -> str:
    flags: list[str] = []
    if _field(row, "age") == NOT_ENOUGH_INFORMATION:
        flags.append("age missing")
    if _outcome_signal(row) == NOT_ENOUGH_INFORMATION:
        flags.append("outcome support missing")
    if _visible_rank_value(row) is None:
        flags.append("board context missing")
    if _has_review_notes(row):
        flags.append("review notes available below")
    return "; ".join(flags) if flags else "No major open review flag in visible context."


def _has_review_notes(row: dict[str, Any]) -> bool:
    for key in (
        "risk_notes",
        "candidate_key_caveat",
        "needs_manual_review",
        "human_review_flag",
        "on_clock_warning",
    ):
        if _field(row, key) != NOT_ENOUGH_INFORMATION:
            return True
    return False


def _player_name(row: dict[str, Any]) -> str:
    return _field(row, "player")


def _field(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return NOT_ENOUGH_INFORMATION
    return text


def _float_or_none(value: Any) -> float | None:
    text = str(value if value is not None else "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            output.append(value)
            seen.add(value)
    return output
