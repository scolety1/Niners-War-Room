from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.components.demo_source_labels import demo_source_label
from app.components.human_labels import human_label
from src.services.nwr_outcome_status_display_service import (
    OutcomeStatusDisplay,
    build_default_app_status_registry,
)

MISSING = "-"
RANKINGS_CONTEXT = "rankings"
DRAFT_PREP_CONTEXT = "draft_prep"
LIVE_DRAFT_ROOM_CONTEXT = "live_draft_room"
OUTCOME_IN_DEVELOPMENT_NOTE = (
    "Outcome model is in development. No probabilities are released yet."
)
DISPLAY_ONLY_NOTE = (
    "Market and league ranks are display-only context and are never used in private "
    "NWR value, rank, tier, trust, risk, or outcome fields."
)
LEGACY_COMPARISON_ONLY_NOTE = (
    "Legacy active-pack scores are comparison-only and cannot drive NWR score, rank, "
    "tier, sorting, trust, or recommendations."
)

WARNING_EXPLANATIONS = {
    "missing_model_v4_current_player_row": "Missing current-player private model row.",
    "missing_score_disclosure_fields": (
        "Source path, column, lineage, or score metadata is missing."
    ),
    "unmatched_identity_join_key": (
        "Player identity needs verification against the current model rows."
    ),
    "duplicate_identity_join_key": "Duplicate player identity rows need verification.",
    "team_mismatch_or_missing_model_team": "Current team mapping needs verification.",
    "stale_team_or_status_evidence": "Current team or active status needs verification.",
    "missing_role_evidence_gate": "Missing role or volume evidence.",
    "missing_role_evidence": "Missing role or volume evidence.",
    "missing_or_review_route_target_snap_evidence": "Missing target, route, or snap evidence.",
    "licensed_route_metrics_not_available": "Route metrics source is not available.",
    "missing_or_review_first_down_evidence": "Missing first-down evidence.",
    "partial_first_down_confidence_cap": "First-down evidence is partial.",
    "one_qb_context_balance_upper_band_guard_v2": "1QB context balance guard is active.",
    "one_qb_small_vorp_gap_cap": "1QB small VORP gap cap is active.",
    "one_qb_replacement_level_qb_cap": "1QB replacement-level QB cap is active.",
    "te_upper_band_guard_v2_elite_exception": (
        "No-premium TE elite exception is active; review the private evidence receipts."
    ),
    "no_premium_te_small_gap_cap": "No-premium TE small-gap cap is active.",
    "rb_dynasty_age_curve_after_27_active": "RB dynasty age curve is active after age 27.",
    "rb_dynasty_age_curve_30_plus_active": "RB 30-plus age cliff is active.",
    "rb_extreme_age_cliff_active": "RB late-career age cliff is active.",
    "wr_dynasty_age_curve_after_30_active": "WR dynasty age curve is active after age 30.",
    "wr_mid_30s_age_cliff_active": "WR mid-30s age cliff is active.",
    "te_no_premium_age_curve_after_30_active": (
        "No-premium TE age curve is active after age 30."
    ),
    "te_age_33_plus_cliff_active": "TE 33-plus age cliff is active.",
    "missing_lifecycle_or_role_shape_evidence": "Missing lifecycle or role-shape evidence.",
    "missing_efficiency_context_evidence": "Missing efficiency context.",
    "source_limited_evidence_cap": "Source coverage is limited.",
    "partial_or_quarantined_join_evidence": (
        "Some contribution evidence is partial or quarantined."
    ),
    "identity_review_cap": "Identity verification cap is active.",
    "rb_age_cliff_guardrail_unavailable": "RB age-risk evidence needs verification.",
    "qb_rushing_age_caution_unavailable": "QB rushing-age evidence needs verification.",
    "no_premium_te_replacement_level_cap": (
        "No-premium TE replacement baseline needs verification."
    ),
    "legacy_score_comparison_only": "Legacy score is comparison-only.",
    "primary_score_guardrail_flagged": "Primary score guardrail suppressed this value.",
}


@dataclass(frozen=True)
class PlayerDetailMetric:
    label: str
    value: str
    note: str = ""


@dataclass(frozen=True)
class PlayerDetailReceipt:
    label: str
    value: str


@dataclass(frozen=True)
class PlayerDetailCardPayload:
    context: str
    player: str
    position: str = MISSING
    age: str = MISSING
    team: str = MISSING
    roster_status: str = MISSING
    source_type: str = MISSING
    nwr_score: str = MISSING
    nwr_rank: str = MISSING
    trust_status: str = "Trust unknown"
    warning_summary: str = "No active warning."
    warning_messages: tuple[str, ...] = ()
    data_needed: tuple[str, ...] = ()
    market_rank_display_only: str = MISSING
    league_rank_display_only: str = MISSING
    market_gap_display_only: str = MISSING
    league_gap_display_only: str = MISSING
    source_path: str = MISSING
    source_column: str = MISSING
    lineage_class: str = MISSING
    allowed_use: str = MISSING
    blocked_use: str = MISSING
    legacy_comparison_score: str = ""
    context_tags: tuple[str, ...] = ()
    why_text: str = "Explanation not available from current source rows."
    outcome_status: str = OUTCOME_IN_DEVELOPMENT_NOTE
    outcome_model_statuses: tuple[OutcomeStatusDisplay, ...] = ()
    private_model_metrics: tuple[PlayerDetailMetric, ...] = ()
    ranking_context_metrics: tuple[PlayerDetailMetric, ...] = ()
    draft_prep_context_metrics: tuple[PlayerDetailMetric, ...] = ()
    live_draft_room_context_metrics: tuple[PlayerDetailMetric, ...] = ()
    user_context_metrics: tuple[PlayerDetailMetric, ...] = ()
    receipts: tuple[PlayerDetailReceipt, ...] = ()
    raw_warning_flags: str = ""
    display_only_note: str = DISPLAY_ONLY_NOTE
    legacy_note: str = LEGACY_COMPARISON_ONLY_NOTE


def build_player_detail_card_payload(
    row: Mapping[str, Any],
    *,
    context: str = RANKINGS_CONTEXT,
) -> PlayerDetailCardPayload:
    if context == RANKINGS_CONTEXT:
        return _build_rankings_payload(row)
    if context == DRAFT_PREP_CONTEXT:
        return _build_draft_prep_payload(row)
    if context == LIVE_DRAFT_ROOM_CONTEXT:
        return _build_live_draft_room_payload(row)
    raise ValueError(f"Unsupported player detail card context: {context}")


def _build_rankings_payload(row: Mapping[str, Any]) -> PlayerDetailCardPayload:
    player = _clean(_first(row, "player", "player_name"), missing="Player")
    position = _clean(row.get("position"))
    age = _clean(row.get("age"))
    team = _clean(row.get("nfl_team") or row.get("team"))
    nwr_rank = _clean(row.get("nwr_rank"))
    score = _score_text(_first(row, "private_score", "nwr_dynasty_score"))
    market_rank = _clean(_first(row, "market_rank", "dynasty_startup_adp"))
    league_rank = _clean(row.get("league_rank"))
    legacy_score = _score_text(row.get("legacy_active_pack_score"), missing="")
    warning_flags = _joined_warnings(row)
    warnings = _warning_flags(warning_flags)
    data_needed = _data_needed(row, warnings, score)
    trust = _trust_status(row, warnings, score)
    roster_status = _roster_status(row, trust)
    confidence_cap = _clean(row.get("confidence_cap"))
    confidence_status = _clean(row.get("confidence_status"))
    source_type = _clean(_first(row, "score_type", "lineage_class", "model_source_status"))
    source_note = (
        "Ranked by private NWR Dynasty Score from admitted Model v4 current-player "
        "lineage. Roster/team tags, market rank, league rank, and legacy scores are "
        "display-only context and do not affect this score."
    )
    why_text = _clean(
        _first(row, "manual_review_notes", "raw_source_repair_notes"),
        missing="",
    )
    why_text = f"{source_note} {why_text}".strip()

    private_metrics = (
        PlayerDetailMetric("NWR Dynasty Score", score),
        PlayerDetailMetric("NWR Rank", nwr_rank),
        PlayerDetailMetric("Trust", trust),
        PlayerDetailMetric("Confidence Cap", confidence_cap),
        PlayerDetailMetric("Confidence Status", confidence_status),
        PlayerDetailMetric("Lineage", _clean(row.get("lineage_class"))),
    )
    candidate_metrics = _candidate_model_metrics(row)
    ranking_metrics = (
        PlayerDetailMetric("Market Rank", market_rank, "display-only"),
        PlayerDetailMetric("NWR vs Market", _signed_gap(nwr_rank, market_rank), "display-only"),
        PlayerDetailMetric("League Rank", league_rank, "display-only"),
        PlayerDetailMetric("NWR vs League", _signed_gap(nwr_rank, league_rank), "display-only"),
    )
    receipts = _receipts(row, warning_flags)

    return PlayerDetailCardPayload(
        context=RANKINGS_CONTEXT,
        player=player,
        position=position,
        age=age,
        team=team,
        roster_status=roster_status,
        source_type=source_type,
        nwr_score=score,
        nwr_rank=nwr_rank,
        trust_status=trust,
        warning_summary=_warning_summary(warnings),
        warning_messages=tuple(_human_warning(flag) for flag in warnings),
        data_needed=tuple(data_needed),
        market_rank_display_only=market_rank,
        league_rank_display_only=league_rank,
        market_gap_display_only=_signed_gap(nwr_rank, market_rank),
        league_gap_display_only=_signed_gap(nwr_rank, league_rank),
        source_path=_source_label(row.get("source_path")),
        source_column=_clean(row.get("source_column")),
        lineage_class=_clean(row.get("lineage_class")),
        allowed_use=_clean(row.get("allowed_use")),
        blocked_use=_clean(row.get("blocked_use")),
        legacy_comparison_score=legacy_score,
        context_tags=tuple(
            tag
            for tag in (
                roster_status,
                source_type if source_type != MISSING else "",
            )
            if tag
        ),
        why_text=why_text,
        outcome_model_statuses=_outcome_model_statuses(row),
        private_model_metrics=tuple(
            metric for metric in (*private_metrics, *candidate_metrics) if metric.value != MISSING
        ),
        ranking_context_metrics=ranking_metrics,
        receipts=receipts,
        raw_warning_flags=warning_flags,
    )


def _candidate_model_metrics(row: Mapping[str, Any]) -> tuple[PlayerDetailMetric, ...]:
    candidate_version = _clean(row.get("candidate_model_version"), missing="")
    if not candidate_version:
        return ()
    return (
        PlayerDetailMetric("Candidate Model", candidate_version, "candidate mode"),
        PlayerDetailMetric(
            "Base NWR Score",
            _score_text(row.get("base_nwr_dynasty_score")),
            "production baseline",
        ),
        PlayerDetailMetric(
            "WR/QB v2 Adjustment",
            _clean(row.get("candidate_adjustment")),
            "candidate-only",
        ),
        PlayerDetailMetric(
            "Final Candidate Score",
            _score_text(_first(row, "nwr_dynasty_score", "candidate_score")),
            "candidate-only",
        ),
        PlayerDetailMetric(
            "WR/QB v2 Reason Codes",
            _clean(row.get("candidate_reason_codes")),
            "source-safe receipts",
        ),
        PlayerDetailMetric(
            "Evidence / Trust Caveat",
            _clean(row.get("candidate_confidence_trust_impact")),
            "warnings remain visible",
        ),
    )


def _build_draft_prep_payload(row: Mapping[str, Any]) -> PlayerDetailCardPayload:
    player = _clean(row.get("player"), missing="Player")
    position = _clean(row.get("position"))
    age = _clean(row.get("age"))
    team = _clean(row.get("nfl_team"))
    source_type = _display_text(row.get("source_type"))
    draftable_status = _display_text(row.get("draftable_status"))
    legal_draftable = _clean(row.get("legal_draftable"))
    trust = _clean(row.get("trust_status"), missing="Trust unknown")
    score = _score_text(_first(row, "nwr_draft_value", "nwr_rookie_score", "nwr_dynasty_score"))
    warning_flags = _joined_warnings(row)
    warnings = _warning_flags(warning_flags)
    data_needed = _data_needed(row, warnings, score)
    pick_window = _clean(row.get("pick_window"))
    fit_band = _clean(row.get("fit_band"))
    user_context = _clean(_first(row, "user_context_tags", "prior_draft_context"), missing="")
    why_bits = [
        "Shown from the Draft Prep scouting pool.",
        f"Pick window: {pick_window}." if pick_window != MISSING else "",
        f"Fit band: {fit_band}." if fit_band != MISSING else "",
        "Legal Pool Pending until dropped/released veteran data is supplied.",
    ]
    why_text = " ".join(bit for bit in why_bits if bit)
    private_metrics = (
        PlayerDetailMetric("NWR Draft Value / Rookie Score", score),
        PlayerDetailMetric("Trust", trust),
        PlayerDetailMetric("Lineage", _clean(row.get("lineage_class"))),
    )
    draft_metrics = (
        PlayerDetailMetric("Pick Window", pick_window, "context-only"),
        PlayerDetailMetric("Fit Band", fit_band, "context-only"),
        PlayerDetailMetric("Source Type", source_type, "context-only"),
        PlayerDetailMetric("Draftable Status", draftable_status, "source status"),
        PlayerDetailMetric("Legal Draftable", legal_draftable, "source status"),
        PlayerDetailMetric(
            "Prospect Talent",
            _clean(row.get("prospect_talent_context")),
            "context-only",
        ),
        PlayerDetailMetric(
            "Landing Spot",
            _clean(row.get("landing_spot_context")),
            "context-only",
        ),
        PlayerDetailMetric(
            "Draft Capital",
            _clean(row.get("draft_capital_context")),
            "context-only",
        ),
        PlayerDetailMetric("Role Path", _clean(row.get("role_path_context")), "context-only"),
    )
    user_metrics = (
        PlayerDetailMetric(
            "User / History Context",
            user_context or MISSING,
            "display-only context",
        ),
        PlayerDetailMetric(
            "Must Review At Cost",
            "Yes" if "Must Review At Cost" in user_context else MISSING,
            "context-only, not a final instruction",
        ),
    )
    receipts = _receipts(row, warning_flags)

    return PlayerDetailCardPayload(
        context=DRAFT_PREP_CONTEXT,
        player=player,
        position=position,
        age=age,
        team=team,
        roster_status=draftable_status,
        source_type=source_type,
        nwr_score=score,
        trust_status=trust,
        warning_summary=_warning_summary(warnings),
        warning_messages=tuple(_human_warning(flag) for flag in warnings),
        data_needed=tuple(data_needed),
        source_path=_source_label(row.get("source_path")),
        source_column=_clean(row.get("source_column")),
        lineage_class=_clean(row.get("lineage_class")),
        allowed_use=_clean(row.get("allowed_use")),
        blocked_use=_clean(row.get("blocked_use")),
        context_tags=tuple(
            tag for tag in (draftable_status, source_type, fit_band) if tag != MISSING
        ),
        why_text=why_text,
        outcome_model_statuses=_outcome_model_statuses(row),
        private_model_metrics=tuple(
            metric for metric in private_metrics if metric.value != MISSING
        ),
        draft_prep_context_metrics=tuple(
            metric for metric in draft_metrics if metric.value != MISSING
        ),
        user_context_metrics=tuple(metric for metric in user_metrics if metric.value != MISSING),
        receipts=receipts,
        raw_warning_flags=warning_flags,
        display_only_note=(
            "Draft Prep source status, prior draft history, spreadsheet highlights, and "
            "pick-window labels are display-only/context-only and never private model value."
        ),
    )


def _build_live_draft_room_payload(row: Mapping[str, Any]) -> PlayerDetailCardPayload:
    player = _clean(row.get("player"), missing="Player")
    position = _clean(row.get("position"))
    age = _clean(row.get("age"))
    team = _clean(row.get("nfl_team"))
    source_type = _display_text(_first(row, "source_type", "asset_type"))
    draftable_status = _display_text(_first(row, "draftable_status", "asset_lifecycle"))
    drafted_status = _display_text(row.get("drafted_status") or row.get("draft_status"))
    drafted_pick = _clean(row.get("drafted_pick"))
    current_pick = _clean(row.get("current_pick_context"))
    selected_pick = _clean(row.get("selected_pick_context"))
    legal_pool_status = _clean(row.get("legal_pool_status"), missing="Legal Pool Pending")
    scouting_pool_status = _clean(row.get("scouting_pool_status"), missing="Scouting pool")
    hide_drafted_status = _clean(row.get("hide_drafted_status"))
    mock_state_context = _clean(
        row.get("mock_state_context"),
        missing="Session/local mock state only.",
    )
    best_remaining_context = _clean(
        row.get("best_remaining_context"),
        missing="Selected from Best Remaining / Scouting Pool.",
    )
    trust = _clean(row.get("trust_status"), missing="Source/context only")
    score = _score_text(_first(row, "nwr_draft_value", "stats_model_value", "nwr_rookie_score"))
    warning_flags = _joined_warnings(row)
    warnings = _warning_flags(warning_flags)
    data_needed = _data_needed(row, warnings, score)

    why_bits = [
        best_remaining_context,
        f"Selected pick: {selected_pick}." if selected_pick != MISSING else "",
        f"Drafted pick: {drafted_pick}." if drafted_pick != MISSING else "",
        "Legal Pool Pending until dropped/released veteran data is supplied.",
    ]
    why_text = " ".join(bit for bit in why_bits if bit)

    private_metrics = (
        PlayerDetailMetric("NWR Draft Value / Scouting Score", score),
        PlayerDetailMetric("Trust", trust),
        PlayerDetailMetric("Lineage", _clean(row.get("lineage_class"))),
    )
    live_metrics = (
        PlayerDetailMetric("Legal Pool Status", legal_pool_status, "source status"),
        PlayerDetailMetric("Scouting Pool Status", scouting_pool_status, "source/context only"),
        PlayerDetailMetric("Drafted Status", drafted_status, "session/local mock state"),
        PlayerDetailMetric("Drafted Pick", drafted_pick, "session/local mock state"),
        PlayerDetailMetric("Current Pick", current_pick, "session/local mock state"),
        PlayerDetailMetric("Selected Pick", selected_pick, "session/local mock state"),
        PlayerDetailMetric("Hide Drafted", hide_drafted_status, "display setting"),
        PlayerDetailMetric("Source Type", source_type, "context-only"),
        PlayerDetailMetric("Draftable Status", draftable_status, "source status"),
        PlayerDetailMetric("Mock State", mock_state_context, "read-only display"),
    )

    return PlayerDetailCardPayload(
        context=LIVE_DRAFT_ROOM_CONTEXT,
        player=player,
        position=position,
        age=age,
        team=team,
        roster_status=drafted_status if drafted_status != MISSING else draftable_status,
        source_type=source_type,
        nwr_score=score,
        trust_status=trust,
        warning_summary=_warning_summary(warnings),
        warning_messages=tuple(_human_warning(flag) for flag in warnings),
        data_needed=tuple(data_needed),
        source_path=_source_label(row.get("source_path")),
        source_column=_clean(row.get("source_column")),
        lineage_class=_clean(row.get("lineage_class")),
        allowed_use=_clean(row.get("allowed_use")),
        blocked_use=_clean(row.get("blocked_use")),
        context_tags=tuple(
            tag
            for tag in (legal_pool_status, drafted_status, source_type)
            if tag != MISSING
        ),
        why_text=why_text,
        outcome_model_statuses=_outcome_model_statuses(row),
        private_model_metrics=tuple(
            metric for metric in private_metrics if metric.value != MISSING
        ),
        live_draft_room_context_metrics=tuple(
            metric for metric in live_metrics if metric.value != MISSING
        ),
        receipts=_receipts(row, warning_flags),
        raw_warning_flags=warning_flags,
        display_only_note=(
            "Live Draft Room player context is source/context only. Draft state is "
            "session/local mock state and does not mutate source data."
        ),
    )


def _first(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if _clean(value, missing=""):
            return value
    return ""


def _outcome_model_statuses(row: Mapping[str, Any]) -> tuple[OutcomeStatusDisplay, ...]:
    position = _clean(row.get("position"), missing="")
    return tuple(build_default_app_status_registry(position=position or None))


def _clean(value: Any, *, missing: str = MISSING) -> str:
    if value is None:
        return missing
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "age missing"}:
        return missing
    return text


def _score_text(value: Any, *, missing: str = MISSING) -> str:
    text = _clean(value, missing="")
    if not text:
        return missing
    try:
        return f"{float(text):.2f}"
    except ValueError:
        return text


def _display_text(value: Any) -> str:
    text = _clean(value)
    if text == MISSING:
        return text
    return text.replace("_", " ").title()


def _rank_value(value: Any) -> int | None:
    text = _clean(value, missing="")
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _signed_gap(nwr_rank: Any, comparison_rank: Any) -> str:
    nwr = _rank_value(nwr_rank)
    comparison = _rank_value(comparison_rank)
    if nwr is None or comparison is None:
        return MISSING
    return f"{comparison - nwr:+d}"


def _joined_warnings(row: Mapping[str, Any]) -> str:
    values = [
        _clean(row.get("warning_reasons"), missing=""),
        _clean(row.get("warning_flags"), missing=""),
        _clean(row.get("raw_model_warning_flags"), missing=""),
    ]
    flags: list[str] = []
    for value in values:
        for flag in _warning_flags(value):
            if flag not in flags:
                flags.append(flag)
    return "|".join(flags)


def _warning_flags(value: Any) -> list[str]:
    return [flag for flag in str(value or "").split("|") if flag]


def _human_warning(flag: str) -> str:
    return WARNING_EXPLANATIONS.get(flag, human_label(flag))


def _warning_summary(warnings: list[str]) -> str:
    if not warnings:
        return "No active warning."
    return f"{len(warnings)} warning{'s' if len(warnings) != 1 else ''}"


def _data_needed(row: Mapping[str, Any], warnings: list[str], score: str) -> list[str]:
    existing = _clean(row.get("data_needed"), missing="")
    if existing:
        return [part.strip() for part in existing.split("|") if part.strip()]
    needs = [_human_warning(flag) for flag in warnings]
    if score == MISSING:
        needs.insert(0, "No private NWR Dynasty Score is available.")
    if not _clean(row.get("source_path"), missing=""):
        needs.append("Source path is missing.")
    if not _clean(row.get("source_column"), missing=""):
        needs.append("Source column is missing.")
    return list(dict.fromkeys(needs))


def _trust_status(row: Mapping[str, Any], warnings: list[str], score: str) -> str:
    trust = _clean(_first(row, "nwr_trust_status", "trust_status"), missing="")
    if trust:
        return trust
    if score == MISSING:
        return "No Private Score"
    confidence_cap = _clean(row.get("confidence_cap"), missing="")
    try:
        if confidence_cap and float(confidence_cap) < 1.0:
            return "Capped Score"
    except ValueError:
        pass
    if warnings:
        return "Scored + Warnings"
    confidence = _clean(row.get("confidence_status"), missing="")
    if confidence in {"Manual decision required", "Trust unknown", ""}:
        return "Scored"
    return confidence


def _roster_status(row: Mapping[str, Any], trust: str) -> str:
    statuses: list[str] = []
    pool_status = _clean(row.get("pool_status"), missing="")
    if pool_status:
        statuses.append(pool_status)
    elif _clean(row.get("is_my_team"), missing="") == "1":
        statuses.append("MY TEAM")
    elif _clean(row.get("is_available"), missing="") == "1":
        statuses.append("AVAILABLE")
    else:
        statuses.append("OTHER TEAM")
    if _clean(row.get("is_rookie"), missing="") == "1":
        statuses.append("ROOKIE")
    if trust in {"Source Repair Needed", "No Private Score", "Blocked", "No Baseline"}:
        statuses.append("NO PRIVATE SCORE")
    if _clean(row.get("lineage_class"), missing="") == "legacy_active_pack":
        statuses.append("LEGACY ONLY")
    return " | ".join(dict.fromkeys(statuses))


def _receipts(row: Mapping[str, Any], warning_flags: str) -> tuple[PlayerDetailReceipt, ...]:
    receipt_fields = (
        ("Source path", _source_label(row.get("source_path"))),
        ("Source column", row.get("source_column")),
        ("Upstream source path", _source_label(row.get("upstream_source_path"))),
        ("Upstream source column", row.get("upstream_source_column")),
        ("Lineage", row.get("lineage_class")),
        ("Model version", row.get("model_version")),
        ("Score as-of date", row.get("score_as_of_date")),
        ("Allowed use", row.get("allowed_use")),
        ("Blocked use", row.get("blocked_use")),
        ("Raw warnings", warning_flags),
        ("Raw source repair notes", row.get("raw_source_repair_notes")),
    )
    return tuple(
        PlayerDetailReceipt(label=label, value=_clean(value))
        for label, value in receipt_fields
        if _clean(value) != MISSING
    )


def _source_label(value: object) -> str:
    return _clean(demo_source_label(value, fallback_prefix="Source"), missing=MISSING)
