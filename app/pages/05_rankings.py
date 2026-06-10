# ruff: noqa: E402

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.cache_keys import path_fingerprint
from app.components.data_pack_selector import render_data_pack_selector
from app.components.human_labels import human_label
from app.components.player_detail_card import render_player_detail_card
from app.components.trust_status import render_page_trust_banner
from app.components.ui_framework import page_header
from src.config.settings import get_settings
from src.services.data_pack_health_service import build_data_pack_health_report
from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS
from src.services.player_board_score_service import build_player_board_score_rows
from src.services.player_detail_card_service import build_player_detail_card_payload
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    RECEIPT_COLUMN_LABELS,
    RECEIPT_DISPLAY_COLUMNS,
    build_player_feature_receipts,
    receipt_rows_for_players,
)
from src.services.ranking_readiness_service import build_ranking_readiness

AGE_ROWS = Path("local_exports/model_v4/prospect_age/latest/player_age_2026.csv")
SLEEPER_AGE_ROWS = Path(
    "local_exports/model_v4/prospect_age/latest/sleeper_player_age_supplement_20260528.csv"
)
AGE_SOURCE_PATHS = (AGE_ROWS, SLEEPER_AGE_ROWS)
FULL_BOARD_VALUE_ROWS = REPO_ROOT / DEFAULT_FULL_PLAYER_BOARD_ROWS

MY_TEAM_NAME = "Niners"
NWR_SCORE_COLUMN = "private_score"
OUTCOME_NOTE = (
    "Outcome percentage model in development. No estimated percentages are shown until "
    "the private model supports these fields."
)
MARKET_DISPLAY_ONLY_NOTE = (
    "Market, league, ADP, consensus, projection, startup, and trade-calculator context "
    "is display-only and never used in private NWR Dynasty Score, rank, tier, trust, "
    "risk, or outcome fields."
)
DEFAULT_DYNASTY_COLUMNS = [
    "Rank",
    "Player",
    "Pos",
    "Age",
    "Team",
    "NWR Dynasty Score",
    "Trust",
    "Warnings",
    "Market Rank",
    "NWR vs Market",
    "League Rank",
    "NWR vs League",
    "Status",
    "Data Needed",
]
OUTCOME_GROUP_COLUMNS = {
    "Compact": [],
    "2026 Outcomes": ["T6 2026", "T12 2026", "T24 2026", "T36 2026", "T48 2026"],
    "2027 Outcomes": ["T6 2027", "T12 2027", "T24 2027", "T36 2027", "T48 2027"],
    "5-Year Outcomes": ["T6 5Y", "T12 5Y", "T24 5Y", "T36 5Y", "T48 5Y"],
}
POSITION_FILTERS = ("All", "QB", "RB", "WR", "TE", "FLEX")
PLAYER_POOL_FILTERS = ("All", "My Team", "Available", "Rookies", "Needs Data / No Private Score")
FLEX_POSITIONS = {"RB", "WR", "TE"}

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
    "missing_lifecycle_or_role_shape_evidence": "Missing lifecycle or role-shape evidence.",
    "missing_efficiency_context_evidence": "Missing efficiency context.",
    "source_limited_evidence_cap": "Source coverage is limited.",
    "partial_or_quarantined_join_evidence": "Some contribution evidence is partial or quarantined.",
    "identity_review_cap": "Identity verification cap is active.",
    "rb_age_cliff_guardrail_unavailable": "RB age-risk evidence needs verification.",
    "qb_rushing_age_caution_unavailable": "QB rushing-age evidence needs verification.",
    "no_premium_te_small_gap_cap": "No-premium TE replacement gap needs verification.",
    "no_premium_te_replacement_level_cap": "No-premium TE replacement baseline needs verification.",
    "legacy_score_comparison_only": "Legacy score is comparison-only.",
    "primary_score_guardrail_flagged": "Primary score guardrail suppressed this value.",
}


@st.cache_data
def _load_health(active_data_pack: str, data_pack_fingerprint: tuple[str, int, int, int]):
    _ = data_pack_fingerprint
    return build_data_pack_health_report(active_data_pack)


@st.cache_data
def _load_feature_receipts(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    veteran_model_dir: str,
    veteran_model_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, veteran_model_fingerprint
    return build_player_feature_receipts(
        active_data_pack,
        veteran_model_dir=veteran_model_dir,
    )


@st.cache_data
def _load_age_lookup(
    age_paths: tuple[str, ...],
    age_fingerprints: tuple[tuple[str, int, int, int], ...],
) -> dict[str, str]:
    _ = age_fingerprints
    lookup: dict[str, str] = {}
    for age_path in age_paths:
        path = Path(age_path)
        if not path.exists():
            continue
        frame = pd.read_csv(path, dtype=str).fillna("")
        for _, row in frame.iterrows():
            age = str(row.get("age_years_decimal") or row.get("age_years") or "").strip()
            if not age:
                continue
            for key in _age_lookup_keys(row):
                lookup.setdefault(key, age)
    return lookup


def _age_lookup_keys(row: pd.Series) -> tuple[str, ...]:
    player = str(row.get("player") or "")
    base_key = str(row.get("normalized_player_name") or _normalize_name(player))
    without_suffix = player
    for suffix in (" Jr.", " Sr.", " II", " III", " IV", " V"):
        without_suffix = without_suffix.replace(suffix, "")
    keys = [base_key, _normalize_name(without_suffix)]
    if base_key.endswith("i"):
        keys.append(base_key.rstrip("i"))
    return tuple(key for key in dict.fromkeys(keys) if key)


@st.cache_data
def _load_formula_board(
    active_data_pack: str,
    data_pack_fingerprint: tuple[str, int, int, int],
    age_lookup: dict[str, str],
    current_value_path: str,
    current_value_fingerprint: tuple[str, int, int, int],
):
    _ = data_pack_fingerprint, current_value_fingerprint
    return build_player_board_score_rows(
        active_data_pack,
        current_value_path=current_value_path,
        age_lookup=age_lookup,
    )


def _normalize_name(value: object) -> str:
    return "".join(character for character in str(value or "").lower() if character.isalnum())


def _clean_value(value: object, *, missing: str = "—") -> str:
    if value is None:
        return missing
    if isinstance(value, float) and pd.isna(value):
        return missing
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a", "age missing"}:
        return missing
    return text


def _score_value(value: object) -> float | None:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _rank_value(value: object) -> int | None:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _signed_gap(nwr_rank: object, comparison_rank: object) -> str:
    nwr = _rank_value(nwr_rank)
    comparison = _rank_value(comparison_rank)
    if nwr is None or comparison is None:
        return "—"
    delta = comparison - nwr
    return f"{delta:+d}"


def _warning_flags(value: object) -> list[str]:
    return [flag for flag in str(value or "").split("|") if flag]


def _warning_count(value: object) -> str:
    count = len(_warning_flags(value))
    if count == 0:
        return "0"
    return f"{count} warning{'s' if count != 1 else ''}"


def _human_warning(flag: str) -> str:
    return WARNING_EXPLANATIONS.get(flag, human_label(flag))


def _data_needed(row: pd.Series) -> list[str]:
    existing = _clean_value(row.get("data_needed"), missing="")
    if existing:
        return [part.strip() for part in existing.split("|") if part.strip()]
    needs = [_human_warning(flag) for flag in _warning_flags(row.get("warning_reasons"))]
    if _score_value(row.get(NWR_SCORE_COLUMN)) is None:
        needs.insert(0, "No private NWR Dynasty Score is available.")
    if not _clean_value(row.get("source_path"), missing=""):
        needs.append("Source path is missing.")
    if not _clean_value(row.get("source_column"), missing=""):
        needs.append("Source column is missing.")
    return list(dict.fromkeys(needs))


def _is_my_team(row: pd.Series) -> bool:
    if _clean_value(row.get("is_my_team"), missing="") == "1":
        return True
    return str(row.get("owner") or "").strip().lower() == MY_TEAM_NAME.lower()


def _is_available(row: pd.Series) -> bool:
    if _clean_value(row.get("is_available"), missing="") == "1":
        return True
    if _clean_value(row.get("pool_status"), missing="").upper() == "AVAILABLE":
        return True
    return not str(row.get("owner") or "").strip()


def _is_needs_data(row: pd.Series) -> bool:
    trust = _clean_value(row.get("nwr_trust_status"), missing="")
    if trust in {"Source Repair Needed", "No Private Score", "Blocked", "No Baseline"}:
        return True
    return _score_value(row.get(NWR_SCORE_COLUMN)) is None


def _is_rookie(row: pd.Series) -> bool:
    if _clean_value(row.get("is_rookie"), missing="") == "1":
        return True
    searchable = "|".join(
        str(row.get(column) or "").lower()
        for column in ("model_source_status", "warning_reasons", "score_type", "source_path")
    )
    return "rookie" in searchable


def _trust_label(row: pd.Series) -> str:
    trust_status = _clean_value(row.get("nwr_trust_status"), missing="")
    if trust_status:
        return trust_status
    if _score_value(row.get(NWR_SCORE_COLUMN)) is None:
        return "No Private Score"
    confidence_cap = _score_value(row.get("confidence_cap"))
    if confidence_cap is not None and confidence_cap < 1.0:
        return "Capped Score"
    if _warning_flags(row.get("warning_reasons")):
        return "Scored + Warnings"
    confidence = _clean_value(row.get("confidence_status"), missing="")
    if confidence in {"Manual decision required", "Trust unknown"}:
        return "Scored"
    return confidence


def _status_label(row: pd.Series) -> str:
    statuses: list[str] = []
    pool_status = _clean_value(row.get("pool_status"), missing="")
    if pool_status:
        statuses.append(pool_status)
    elif _is_my_team(row):
        statuses.append("MY TEAM")
    elif _is_available(row):
        statuses.append("AVAILABLE")
    else:
        statuses.append("OTHER TEAM")
    if _is_rookie(row):
        statuses.append("ROOKIE")
    trust = _trust_label(row)
    if trust in {"Source Repair Needed", "No Private Score", "Blocked", "No Baseline"}:
        statuses.append("NO PRIVATE SCORE")
    if _clean_value(row.get("lineage_class"), missing="") == "legacy_active_pack":
        statuses.append("LEGACY ONLY")
    return " | ".join(dict.fromkeys(statuses))


def _player_cell(row: pd.Series) -> str:
    return _clean_value(row.get("player"))


def _assign_valid_private_ranks(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    valid = frame[NWR_SCORE_COLUMN].map(_score_value).notna()
    frame["nwr_rank"] = ""
    valid_rows = frame[valid].copy()
    valid_rows["_score_sort"] = valid_rows[NWR_SCORE_COLUMN].map(_score_value)
    valid_rows["_name_sort"] = valid_rows["player"].astype(str).str.lower()
    valid_rows = valid_rows.sort_values(
        by=["_score_sort", "_name_sort"],
        ascending=[False, True],
        kind="mergesort",
    )
    for rank, index in enumerate(valid_rows.index, start=1):
        frame.at[index, "nwr_rank"] = str(rank)
    return frame


def _dynasty_display_frame(frame: pd.DataFrame, *, outcome_group: str) -> pd.DataFrame:
    display_rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        rank = _clean_value(row.get("nwr_rank"))
        market_rank = _clean_value(row.get("market_rank") or row.get("dynasty_startup_adp"))
        league_rank = _clean_value(row.get("league_rank"))
        display_row = {
            "Rank": rank,
            "Player": _player_cell(row),
            "Pos": _clean_value(row.get("position")),
            "Age": _clean_value(row.get("age")),
            "Team": _clean_value(row.get("nfl_team")),
            "NWR Dynasty Score": (
                f"{_score_value(row.get(NWR_SCORE_COLUMN)):.2f}"
                if _score_value(row.get(NWR_SCORE_COLUMN)) is not None
                else "—"
            ),
            "Trust": _trust_label(row),
            "Warnings": _warning_count(row.get("warning_reasons")),
            "Market Rank": market_rank,
            "NWR vs Market": _signed_gap(rank, market_rank),
            "League Rank": league_rank,
            "NWR vs League": _signed_gap(rank, league_rank),
            "Status": _status_label(row),
            "Data Needed": _data_needed_summary(row),
        }
        for outcome_column in OUTCOME_GROUP_COLUMNS[outcome_group]:
            display_row[outcome_column] = "—"
        display_rows.append(display_row)
    columns = DEFAULT_DYNASTY_COLUMNS + OUTCOME_GROUP_COLUMNS[outcome_group]
    return pd.DataFrame(display_rows, columns=columns)


def _apply_filters(
    frame: pd.DataFrame,
    *,
    player_pool: str,
    position: str,
    search: str,
    hide_qbs: bool,
    include_kickers: bool,
    hide_needs_data: bool,
) -> pd.DataFrame:
    filtered = frame.copy()
    if not include_kickers:
        filtered = filtered[filtered["position"].astype(str).str.upper() != "K"]
    if player_pool == "My Team":
        filtered = filtered[filtered.apply(_is_my_team, axis=1)]
    elif player_pool == "Available":
        filtered = filtered[filtered.apply(_is_available, axis=1)]
    elif player_pool == "Rookies":
        filtered = filtered[filtered.apply(_is_rookie, axis=1)]
    elif player_pool == "Needs Data / No Private Score":
        filtered = filtered[filtered.apply(_is_needs_data, axis=1)]
    if position == "FLEX":
        filtered = filtered[filtered["position"].astype(str).str.upper().isin(FLEX_POSITIONS)]
    elif position != "All":
        filtered = filtered[filtered["position"].astype(str).str.upper() == position]
    if hide_qbs:
        filtered = filtered[filtered["position"].astype(str).str.upper() != "QB"]
    if hide_needs_data:
        filtered = filtered[~filtered.apply(_is_needs_data, axis=1)]
    if search.strip():
        search_text = search.strip()
        mask = pd.Series(False, index=filtered.index)
        for column in ("player", "nfl_team", "position", "owner"):
            if column in filtered:
                mask = mask | filtered[column].astype(str).str.contains(
                    search_text,
                    case=False,
                    regex=False,
                )
        filtered = filtered[mask]
    return filtered


def _style_dynasty_table(
    frame: pd.DataFrame,
    source_frame: pd.DataFrame,
) -> pd.io.formats.style.Styler:
    my_team_by_player = {
        _clean_value(row.get("player"), missing=""): _is_my_team(row)
        for _, row in source_frame.iterrows()
    }

    def style_row(row: pd.Series) -> list[str]:
        player = str(row.get("Player") or "")
        if my_team_by_player.get(player):
            return ["background-color: #fff8e6"] * len(row)
        if "NO PRIVATE SCORE" in str(row.get("Status") or ""):
            return ["color: #6b7280; background-color: #f6f7f9"] * len(row)
        return [""] * len(row)

    return frame.style.apply(style_row, axis=1)


def _render_data_needed(row: pd.Series) -> None:
    needs = _data_needed(row)
    if not needs:
        st.write("No missing evidence is flagged for this row.")
        return
    for item in needs[:8]:
        st.write(f"- {item}")


def _data_needed_summary(row: pd.Series) -> str:
    needs = _data_needed(row)
    if not needs:
        return "—"
    if len(needs) == 1:
        return needs[0]
    return f"{needs[0]} (+{len(needs) - 1} more)"


def _render_player_detail(row: pd.Series) -> None:
    payload = build_player_detail_card_payload(row.to_dict(), context="rankings")
    render_player_detail_card(payload)

settings = get_settings()
active_data_pack = render_data_pack_selector(settings)
active_fingerprint = path_fingerprint(active_data_pack)
age_lookup = _load_age_lookup(
    tuple(str(path) for path in AGE_SOURCE_PATHS),
    tuple(path_fingerprint(path) for path in AGE_SOURCE_PATHS),
)
health = _load_health(active_data_pack, active_fingerprint)
ranking_readiness = build_ranking_readiness(active_data_pack)
feature_receipts = _load_feature_receipts(
    active_data_pack,
    active_fingerprint,
    str(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
    path_fingerprint(DEFAULT_RECEIPT_VETERAN_MODEL_DIR),
)
formula_rows = _load_formula_board(
    active_data_pack,
    active_fingerprint,
    age_lookup,
    str(FULL_BOARD_VALUE_ROWS),
    path_fingerprint(FULL_BOARD_VALUE_ROWS),
)

page_header(
    "Dynasty Rankings",
    eyebrow="Rankings",
    description=(
        "Private NWR dynasty board. Market and league ranks are display-only and never "
        "used in private value."
    ),
    status_items=(
        ("1QB", "safe"),
        ("No PPR / first-down scoring", "safe"),
        ("Market display-only", "review"),
    ),
)
st.caption(f"Active pack: `{Path(active_data_pack).name}`")
render_page_trust_banner(
    health,
    calibration_passed=ranking_readiness.calibration_passed,
    review_only_message=ranking_readiness.message if ranking_readiness.review_only else "",
    review_only_detail=(
        "Rankings are private-model review rows. Public market, league, ADP, consensus, "
        "projection, startup, and trade-calculator sources are comparison context only."
    )
    if ranking_readiness.review_only
    else "",
)

formula_frame = pd.DataFrame(formula_rows)
if formula_frame.empty:
    st.info("No private model rows are available in the active pack.")
else:
    formula_frame = _assign_valid_private_ranks(formula_frame)
    formula_frame["_needs_data"] = formula_frame.apply(_is_needs_data, axis=1)
    formula_frame["_is_my_team"] = formula_frame.apply(_is_my_team, axis=1)
    formula_frame["_is_rookie"] = formula_frame.apply(_is_rookie, axis=1)

    default_visible_frame = formula_frame[
        formula_frame["position"].astype(str).str.upper() != "K"
    ]
    summary_cols = st.columns(5)
    summary_cols[0].metric("Active players shown", len(default_visible_frame))
    summary_cols[1].metric("NWR scored", int(formula_frame["nwr_rank"].astype(bool).sum()))
    summary_cols[2].metric(
        "No private score",
        int(formula_frame[NWR_SCORE_COLUMN].map(_score_value).isna().sum()),
    )
    summary_cols[3].metric("My Team", int(default_visible_frame["_is_my_team"].sum()))
    summary_cols[4].metric("Outcome fields", "Planned")

    st.info(OUTCOME_NOTE)
    st.caption(
        "My Team highlighting and roster tags are display-only context and do not "
        "affect private NWR score or rank."
    )

    filter_cols = st.columns([1.4, 1.2, 1.2, 1.0])
    with filter_cols[0]:
        player_pool = st.radio(
            "Player pool",
            PLAYER_POOL_FILTERS,
            horizontal=True,
            key="dynasty_rankings_player_pool",
        )
    with filter_cols[1]:
        position_filter = st.radio(
            "Position",
            POSITION_FILTERS,
            horizontal=True,
            key="dynasty_rankings_position_filter",
            help="FLEX means RB + WR + TE only. QB is excluded because this is a 1QB league.",
        )
    with filter_cols[2]:
        outcome_group = st.radio(
            "Outcome columns",
            tuple(OUTCOME_GROUP_COLUMNS),
            horizontal=True,
            key="dynasty_rankings_outcome_group",
            help=(
                "Future outcome percentages must be private-model-only and cannot use "
                "market, ADP, consensus, projections, startup, or trade-calculator data."
            ),
        )
    with filter_cols[3]:
        search = st.text_input(
            "Search",
            "",
            key="dynasty_rankings_search",
            placeholder="Player, team, position",
        )

    option_cols = st.columns(4)
    hide_qbs = option_cols[0].checkbox("Hide QBs", value=False, key="dynasty_rankings_hide_qbs")
    hide_needs_data = option_cols[1].checkbox(
        "Hide No Private Score",
        value=False,
        key="dynasty_rankings_hide_needs_data",
    )
    include_kickers = option_cols[2].checkbox(
        "Include K",
        value=False,
        key="dynasty_rankings_include_kickers",
        help="Kickers are hidden by default on the dynasty board.",
    )
    include_picks = option_cols[3].checkbox(
        "Include picks",
        value=False,
        key="dynasty_rankings_include_picks",
        help=(
            "No pick rows are mixed into the current player source. Owned picks belong "
            "in Draft Room."
        ),
        disabled=True,
    )
    _ = include_picks

    filtered = _apply_filters(
        formula_frame,
        player_pool=player_pool,
        position=position_filter,
        search=search,
        hide_qbs=hide_qbs,
        include_kickers=include_kickers,
        hide_needs_data=hide_needs_data,
    )

    if filtered.empty:
        st.warning("No rows match the current filters.")
    else:
        display_frame = _dynasty_display_frame(filtered, outcome_group=outcome_group)
        st.dataframe(
            _style_dynasty_table(display_frame, filtered),
            use_container_width=True,
            hide_index=True,
            column_config={
                "NWR Dynasty Score": st.column_config.NumberColumn(
                    "NWR Dynasty Score",
                    help="Private NWR model value from checkpoint review score.",
                ),
                "Data Needed": st.column_config.TextColumn(
                    "Data Needed",
                    help="Human-readable source repair or missing-evidence note.",
                ),
                "Market Rank": st.column_config.TextColumn(
                    "Market Rank",
                    help="Display-only market/startup context; never private value input.",
                ),
                "League Rank": st.column_config.TextColumn(
                    "League Rank",
                    help="Display-only league rank/source context; never private value input.",
                ),
                "Warnings": st.column_config.TextColumn(
                    "Warnings",
                    help="Compact warning count. Open player detail for human-readable data needs.",
                ),
            },
        )

        selected_player = st.selectbox(
            "Player detail",
            filtered["player"].astype(str).tolist(),
            key="dynasty_rankings_detail_player",
        )
        detail_row = filtered[filtered["player"].astype(str) == selected_player]
        if not detail_row.empty:
            with st.expander(f"Details: {selected_player}", expanded=True):
                _render_player_detail(detail_row.iloc[0])

    with st.expander("Advanced: feature receipts", expanded=False):
        st.caption(
            "Receipts are audit support for the visible private model rows. They stay out "
            "of the default table so Rankings remains a fantasy-football board first."
        )
        receipt_source_rows = filtered.to_dict("records")[:25] if not filtered.empty else []
        receipt_rows = receipt_rows_for_players(
            feature_receipts,
            receipt_source_rows,
            player_column="player",
            position_column="position",
            page_source="Player Board",
        )
        if feature_receipts.issues:
            st.warning("; ".join(feature_receipts.issues))
        if not receipt_rows:
            st.info("No feature receipts for the current filtered rankings.")
        else:
            receipt_frame = pd.DataFrame(receipt_rows)
            st.dataframe(
                receipt_frame[list(RECEIPT_DISPLAY_COLUMNS)].rename(
                    columns=RECEIPT_COLUMN_LABELS
                ),
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Advanced: raw admitted row fields", expanded=False):
        st.caption(
            "Raw fields are for source auditing only. They do not add recommendations or "
            "change private model value."
        )
        st.dataframe(filtered, use_container_width=True, hide_index=True)
