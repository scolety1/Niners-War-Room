from __future__ import annotations

import re

# ruff: noqa: E402, E501
import sys
import tempfile
from dataclasses import asdict, replace
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.components.ui_framework import page_header
from src.services.redraft_engine_v1_service import (
    DYNASTY_AUTHORITY_LABEL,
    REDRAFT_AUTHORITY_LABEL,
    LeagueProfile,
    RedraftPersistenceError,
    RedraftValidationError,
    RosterSettings,
    active_profile_id,
    archive_profile,
    build_health_report,
    builtin_presets,
    create_profile,
    delete_profile,
    duplicate_profile,
    generate_rankings,
    install_projection_snapshot,
    list_profiles,
    load_draft_board,
    load_projection_snapshot,
    mark_player_drafted,
    profile_store_errors,
    projection_snapshot_path,
    redraft_store_root,
    restore_profile,
    save_profile,
    set_active_profile,
    undo_last_draft_pick,
)


def _profile_label(profile: LeagueProfile) -> str:
    format_label = "Superflex" if profile.roster.superflex else "1QB"
    return f"{profile.league_name} · {profile.team_count} teams · {format_label}"


def _render_redraft_accessibility_frame() -> None:
    st.markdown(
        """
        <span id="nwr-redraft-page" aria-hidden="true"></span>
        <style>
        body:has(#nwr-redraft-page) div[data-testid="stMetric"] label p,
        body:has(#nwr-redraft-page) div[data-testid="stMetricValue"] p,
        body:has(#nwr-redraft-page) div[data-testid="stAlert"] p {
            color: var(--nwr-ink) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _parse_roster_limits(value: str) -> dict[str, int]:
    limits: dict[str, int] = {}
    for item in (part.strip() for part in value.split(",")):
        if not item:
            continue
        try:
            position, raw_limit = item.split("=", 1)
            limits[position.strip().upper()] = int(raw_limit.strip())
        except (ValueError, TypeError) as exc:
            raise RedraftValidationError(
                "Roster limits must use comma-separated POSITION=COUNT values."
            ) from exc
    return limits


def _ranking_frame(result) -> pd.DataFrame:
    rows = [
        {
            "Rank": row.overall_rank,
            "Pos Rank": f"{row.position}{row.position_rank}",
            "Player": row.player_name,
            "Team": row.team,
            "Pos": row.position,
            "Projected Points": row.projected_points,
            "Replacement Value": row.replacement_adjusted_value,
            "Replacement Points": row.replacement_points,
            "Confidence": row.confidence,
            "Tier": row.tier,
            "Rookie": "Yes" if row.rookie else "No",
            "Profile": row.profile_name,
            "Evidence": row.evidence_status,
            "Source": row.source_status,
            "Authority": row.authority_label,
            "player_id": row.player_id,
        }
        for row in result.rows
    ]
    return pd.DataFrame(rows)


def _render_profile_creator(store: Path) -> None:
    st.markdown("### Create from a preset")
    presets = builtin_presets()
    preset_by_name = {profile.league_name: profile for profile in presets}
    columns = st.columns([1.4, 1.6, 1.0])
    preset_name = columns[0].selectbox("Preset", tuple(preset_by_name))
    league_name = columns[1].text_input("New league name", value=preset_name)
    if columns[2].button("Create profile", use_container_width=True):
        try:
            created = create_profile(store, preset_by_name[preset_name], league_name=league_name)
            set_active_profile(store, created.profile_id)
        except (RedraftValidationError, RedraftPersistenceError) as exc:
            st.error(str(exc))
        else:
            st.success(f"Created and activated {created.league_name}.")
            st.rerun()


def _render_archived_profiles(store: Path) -> None:
    archived = tuple(
        profile for profile in list_profiles(store, include_archived=True) if profile.archived
    )
    if not archived:
        return
    by_id = {profile.profile_id: profile for profile in archived}
    with st.expander(f"Archived profiles ({len(archived)})", expanded=False):
        selected_id = st.selectbox(
            "Archived league profile",
            tuple(by_id),
            format_func=lambda profile_id: _profile_label(by_id[profile_id]),
        )
        st.caption("Restoring preserves this profile's separate draft-board state.")
        if st.button("Restore archived profile", use_container_width=True):
            restore_profile(store, selected_id)
            st.success(f"Restored {by_id[selected_id].league_name}.")
            st.rerun()


def _render_profile_editor(store: Path, profile: LeagueProfile) -> None:
    with st.form(f"redraft_profile_editor_{profile.profile_id}"):
        st.markdown("### League identity and roster")
        identity = st.columns(3)
        league_name = identity[0].text_input("League name", value=profile.league_name)
        season = identity[1].number_input(
            "Season", min_value=2000, max_value=2100, value=profile.season, step=1
        )
        teams = identity[2].number_input(
            "Teams", min_value=2, max_value=32, value=profile.team_count, step=1
        )
        roster_cols = st.columns(5)
        qb = roster_cols[0].number_input("QB", 0, 4, profile.roster.qb)
        rb = roster_cols[1].number_input("RB", 0, 8, profile.roster.rb)
        wr = roster_cols[2].number_input("WR", 0, 8, profile.roster.wr)
        te = roster_cols[3].number_input("TE", 0, 4, profile.roster.te)
        flex = roster_cols[4].number_input("FLEX", 0, 6, profile.roster.flex)
        roster_cols_2 = st.columns(4)
        superflex = roster_cols_2[0].number_input("SUPERFLEX", 0, 3, profile.roster.superflex)
        k = roster_cols_2[1].number_input("K", 0, 2, profile.roster.k)
        dst = roster_cols_2[2].number_input("DST", 0, 2, profile.roster.dst)
        bench = roster_cols_2[3].number_input("Bench size", 0, 40, profile.roster.bench_size)

        st.markdown("### Scoring")
        scoring_cols = st.columns(4)
        passing_yards = scoring_cols[0].number_input(
            "Passing yard", value=profile.scoring.passing_yards, step=0.01, format="%.3f"
        )
        passing_td = scoring_cols[1].number_input(
            "Passing TD", value=profile.scoring.passing_td, step=0.5
        )
        interception = scoring_cols[2].number_input(
            "Interception", value=profile.scoring.interception, step=0.5
        )
        reception = scoring_cols[3].number_input(
            "Reception", value=profile.scoring.reception, step=0.25
        )
        scoring_cols_2 = st.columns(4)
        rushing_yards = scoring_cols_2[0].number_input(
            "Rushing yard", value=profile.scoring.rushing_yards, step=0.01, format="%.3f"
        )
        rushing_td = scoring_cols_2[1].number_input(
            "Rushing TD", value=profile.scoring.rushing_td, step=0.5
        )
        receiving_yards = scoring_cols_2[2].number_input(
            "Receiving yard",
            value=profile.scoring.receiving_yards,
            step=0.01,
            format="%.3f",
        )
        receiving_td = scoring_cols_2[3].number_input(
            "Receiving TD", value=profile.scoring.receiving_td, step=0.5
        )
        scoring_cols_3 = st.columns(5)
        passing_fd = scoring_cols_3[0].number_input(
            "Passing 1D", value=profile.scoring.passing_first_down, step=0.1
        )
        rushing_fd = scoring_cols_3[1].number_input(
            "Rushing 1D", value=profile.scoring.rushing_first_down, step=0.1
        )
        receiving_fd = scoring_cols_3[2].number_input(
            "Receiving 1D", value=profile.scoring.receiving_first_down, step=0.1
        )
        fumble = scoring_cols_3[3].number_input(
            "Fumble lost", value=profile.scoring.fumble_lost, step=0.5
        )
        te_premium = scoring_cols_3[4].number_input(
            "TE premium", value=profile.scoring.te_premium, step=0.25
        )
        return_cols = st.columns(2)
        return_yards = return_cols[0].number_input(
            "Return yard", value=profile.scoring.return_yards, step=0.01, format="%.3f"
        )
        return_td = return_cols[1].number_input(
            "Return TD", value=profile.scoring.return_td, step=0.5
        )
        bonus_cols = st.columns(3)
        passing_300_bonus = bonus_cols[0].number_input(
            "300-yard passing bonus",
            value=float(profile.scoring.bonuses.get("passing_300_game", 0.0)),
            step=0.5,
        )
        rushing_100_bonus = bonus_cols[1].number_input(
            "100-yard rushing bonus",
            value=float(profile.scoring.bonuses.get("rushing_100_game", 0.0)),
            step=0.5,
        )
        receiving_100_bonus = bonus_cols[2].number_input(
            "100-yard receiving bonus",
            value=float(profile.scoring.bonuses.get("receiving_100_game", 0.0)),
            step=0.5,
        )

        st.markdown("### Draft context")
        draft_cols = st.columns(5)
        draft_type = draft_cols[0].selectbox(
            "Draft type",
            ("snake", "auction"),
            index=0 if profile.draft.draft_type == "snake" else 1,
        )
        draft_slot_value = draft_cols[1].number_input(
            "Draft slot (0 = unset)", 0, int(teams), profile.draft.draft_slot or 0
        )
        rounds = draft_cols[2].number_input("Rounds", 1, 40, profile.draft.rounds)
        keeper_count = draft_cols[3].number_input("Keeper count", 0, 40, profile.draft.keeper_count)
        replacement_method = draft_cols[4].selectbox(
            "Replacement method",
            ("expected_available", "starter_cutoff"),
            index=0 if profile.draft.replacement_method == "expected_available" else 1,
        )
        advanced_cols = st.columns(3)
        auction_budget_value = advanced_cols[0].number_input(
            "Auction budget (0 = unset)",
            min_value=0,
            max_value=100000,
            value=profile.draft.auction_budget or 0,
            step=1,
        )
        roster_limits_value = advanced_cols[1].text_input(
            "Roster limits",
            value=", ".join(
                f"{position.upper()}={limit}"
                for position, limit in sorted(profile.draft.roster_limits.items())
            ),
            help="Optional comma-separated limits per team, for example QB=2, RB=6.",
        )
        adp_context_enabled = advanced_cols[2].checkbox(
            "Show optional ADP context",
            value=profile.draft.adp_context_enabled,
            help="Context only; ADP never replaces projected points or replacement value.",
        )
        submitted = st.form_submit_button("Save profile settings")
    if submitted:
        try:
            roster_limits = _parse_roster_limits(roster_limits_value)
            updated = replace(
                profile,
                league_name=league_name,
                season=int(season),
                team_count=int(teams),
                roster=RosterSettings(
                    qb=int(qb),
                    rb=int(rb),
                    wr=int(wr),
                    te=int(te),
                    flex=int(flex),
                    superflex=int(superflex),
                    k=int(k),
                    dst=int(dst),
                    bench_size=int(bench),
                ),
                scoring=replace(
                    profile.scoring,
                    passing_yards=float(passing_yards),
                    passing_td=float(passing_td),
                    interception=float(interception),
                    rushing_yards=float(rushing_yards),
                    rushing_td=float(rushing_td),
                    receiving_yards=float(receiving_yards),
                    reception=float(reception),
                    receiving_td=float(receiving_td),
                    passing_first_down=float(passing_fd),
                    rushing_first_down=float(rushing_fd),
                    receiving_first_down=float(receiving_fd),
                    return_yards=float(return_yards),
                    return_td=float(return_td),
                    fumble_lost=float(fumble),
                    te_premium=float(te_premium),
                    bonuses={
                        key: value
                        for key, value in {
                            "passing_300_game": float(passing_300_bonus),
                            "rushing_100_game": float(rushing_100_bonus),
                            "receiving_100_game": float(receiving_100_bonus),
                        }.items()
                        if value
                    },
                ),
                draft=replace(
                    profile.draft,
                    draft_type=draft_type,
                    draft_slot=int(draft_slot_value) or None,
                    rounds=int(rounds),
                    keeper_count=int(keeper_count),
                    auction_budget=int(auction_budget_value) or None,
                    roster_limits=roster_limits,
                    adp_context_enabled=adp_context_enabled,
                    replacement_method=replacement_method,
                ),
            )
            save_profile(store, updated)
        except (RedraftValidationError, RedraftPersistenceError) as exc:
            st.error(str(exc))
        else:
            st.success("Profile settings saved. Dynasty settings were not changed.")
            st.rerun()


def _render_projection_intake(store: Path, profile: LeagueProfile) -> None:
    st.markdown("### Current-season projection evidence")
    st.caption(
        "Upload a granular projection CSV plus a separately issued NWR Data Governance approval "
        "receipt that binds its SHA-256. The admitted snapshot is shared by redraft profiles for "
        "that season and is stored outside dynasty data packs."
    )
    uploaded = st.file_uploader("Projection CSV", type=("csv",), key="redraft_projection_csv")
    approval_uploaded = st.file_uploader(
        "Independent approval receipt",
        type=("json",),
        key="redraft_projection_approval",
        help="Must be issued separately by NWR Data Governance and bind the exact CSV SHA-256.",
    )
    if (
        uploaded is not None
        and approval_uploaded is not None
        and st.button("Install approved projection snapshot")
    ):
        temporary_path: Path | None = None
        approval_temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temporary:
                temporary.write(uploaded.getvalue())
                temporary_path = Path(temporary.name)
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as approval_temporary:
                approval_temporary.write(approval_uploaded.getvalue())
                approval_temporary_path = Path(approval_temporary.name)
            snapshot = install_projection_snapshot(
                store,
                profile.season,
                temporary_path,
                approval_temporary_path,
            )
        except (RedraftValidationError, RedraftPersistenceError, OSError) as exc:
            st.error(str(exc))
        else:
            st.success(
                f"Installed {len(snapshot.players)} rankable rows; "
                f"{len(snapshot.blocked_rows)} rows remain visibly blocked."
            )
            st.rerun()
        finally:
            if temporary_path:
                temporary_path.unlink(missing_ok=True)
            if approval_temporary_path:
                approval_temporary_path.unlink(missing_ok=True)
    with st.expander("Projection CSV contract", expanded=False):
        st.code(
            "player_id,player_name,position,team,season,source_status,evidence_status,"
            "source_as_of,rookie,games,passing_yards,passing_tds,interceptions,"
            "rushing_yards,rushing_tds,receiving_yards,receptions,receiving_tds,"
            "passing_first_downs,rushing_first_downs,receiving_first_downs,"
            "return_yards,return_tds,fumbles_lost,passing_300_games,rushing_100_games,"
            "receiving_100_games,projected_points_override,projection_low,projection_high,"
            "availability_probability",
            language="text",
        )


def _render_profile_actions(store: Path, profile: LeagueProfile) -> None:
    st.markdown("### Profile actions")
    columns = st.columns(3)
    if columns[0].button("Duplicate profile", use_container_width=True):
        duplicate_profile(store, profile.profile_id)
        st.success("Profile duplicated with separate state.")
        st.rerun()
    archive_confirmed = columns[1].checkbox("Confirm archive", key="redraft_archive_confirm")
    if columns[1].button(
        "Archive profile", disabled=not archive_confirmed, use_container_width=True
    ):
        archive_profile(store, profile.profile_id)
        st.success("Profile archived. Dynasty settings were not changed.")
        st.rerun()
    delete_confirmed = columns[2].checkbox("Confirm permanent delete", key="redraft_delete_confirm")
    if columns[2].button("Delete profile", disabled=not delete_confirmed, use_container_width=True):
        delete_profile(store, profile.profile_id, confirmed=True)
        st.success("Redraft profile and its draft-board state were deleted.")
        st.rerun()


def _render_rankings(result, frame: pd.DataFrame) -> None:
    if not result.ready:
        st.warning("Current redraft rankings are blocked until governed projections validate.")
        for error in result.errors:
            st.caption(error)
        return
    metrics = st.columns(4)
    metrics[0].metric("Ranked players", len(frame))
    metrics[1].metric("Blocked players", len(result.blocked_rows))
    metrics[2].metric("Profile", result.profile.league_name)
    metrics[3].metric("Model", "R2 flex-aware VOR")
    positions = ["ALL", *sorted(frame["Pos"].dropna().unique())]
    position = st.selectbox("Position", positions, key="redraft_position_filter")
    visible = frame if position == "ALL" else frame.loc[frame["Pos"].eq(position)]
    st.dataframe(
        visible.drop(columns=["player_id"]),
        use_container_width=True,
        hide_index=True,
        height=600,
    )
    with st.expander("Dynamic replacement levels", expanded=False):
        st.dataframe(
            pd.DataFrame([asdict(row) for row in result.replacement_levels]),
            use_container_width=True,
            hide_index=True,
        )


def _render_tiers(frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("No admitted ranking rows.")
        return
    for tier, tier_frame in frame.groupby("Tier", sort=True):
        st.markdown(f"### Tier {tier}")
        st.dataframe(
            tier_frame[
                ["Rank", "Pos Rank", "Player", "Team", "Projected Points", "Replacement Value"]
            ],
            use_container_width=True,
            hide_index=True,
        )


def _render_player_compare(frame: pd.DataFrame) -> None:
    if len(frame) < 2:
        st.info("At least two admitted redraft ranking rows are required for a comparison.")
        return
    st.caption(
        "Current-season comparison only. Dynasty rank, dynasty value, and rookie authority "
        "do not affect this view."
    )
    player_rows = frame.sort_values(["Rank", "Player"], kind="stable").reset_index(drop=True)
    options = tuple(player_rows["player_id"].astype(str))
    labels = player_rows.set_index(player_rows["player_id"].astype(str))["Player"].to_dict()
    selectors = st.columns(2)
    left_id = selectors[0].selectbox(
        "Player A",
        options,
        format_func=lambda player_id: labels[player_id],
        key="redraft_compare_left",
    )
    right_options = tuple(player_id for player_id in options if player_id != left_id)
    right_id = selectors[1].selectbox(
        "Player B",
        right_options,
        format_func=lambda player_id: labels[player_id],
        key="redraft_compare_right",
    )
    comparison = player_rows.loc[
        player_rows["player_id"].astype(str).isin((left_id, right_id)),
        [
            "Player",
            "Team",
            "Pos Rank",
            "Rank",
            "Projected Points",
            "Replacement Value",
            "Replacement Points",
            "Tier",
            "Confidence",
            "Evidence",
            "Source",
        ],
    ].copy()
    comparison["Season scope"] = "Current season"
    st.dataframe(comparison, use_container_width=True, hide_index=True)
    preferred = comparison.sort_values(["Rank", "Projected Points"], ascending=[True, False]).iloc[0]
    st.info(
        f"Redraft lean: {preferred['Player']} ranks higher for this league profile. "
        "Use projected points, replacement value, tier, and confidence together; this is "
        "advisory and does not execute a roster move."
    )


def _render_draft_board(store: Path, profile: LeagueProfile, frame: pd.DataFrame) -> None:
    if frame.empty:
        st.info("Draft board is blocked until rankings exist.")
        return
    try:
        state = load_draft_board(store, profile.profile_id)
    except RedraftPersistenceError as exc:
        st.error(str(exc))
        st.caption(
            "Other Redraft profiles and Dynasty state remain unchanged. Restore a known-good "
            "backup before continuing this draft."
        )
        return
    if state.get("recovered_from_backup"):
        st.warning("Recovered this draft board from its last exact local backup.")
    drafted_ids = {str(value) for value in state.get("drafted", [])}
    available = frame.loc[~frame["player_id"].astype(str).isin(drafted_ids)].copy()
    metrics = st.columns(4)
    pick_number = len(state.get("drafted", [])) + 1
    round_number = ((pick_number - 1) // profile.team_count) + 1
    metrics[0].metric("Current pick", f"{pick_number} · Round {round_number}")
    metrics[1].metric("Drafted", len(drafted_ids))
    metrics[2].metric("Available", len(available))
    metrics[3].metric("Profile", profile.league_name)
    st.caption(
        "Decision labels are descriptive: top remaining by redraft rank, value tier, "
        "positional need, and replacement gap. No automatic best-pick claim is made."
    )
    if not available.empty:
        top = available.iloc[0]
        st.info(
            f"Top remaining by redraft rank: {top['Player']} ({top['Pos Rank']}) · "
            f"Tier {top['Tier']} · replacement gap {top['Replacement Value']}."
        )
    player_options = frame.set_index("player_id")["Player"].to_dict()
    selected_id = st.selectbox(
        "Draft-board player",
        tuple(player_options),
        format_func=lambda player_id: player_options[player_id],
    )
    action_cols = st.columns(3)
    if action_cols[0].button("Mark drafted", use_container_width=True):
        mark_player_drafted(store, profile.profile_id, selected_id, drafted=True)
        st.rerun()
    if action_cols[1].button(
        "Undo last pick", disabled=not state.get("drafted"), use_container_width=True
    ):
        undo_last_draft_pick(store, profile.profile_id)
        st.rerun()
    if action_cols[2].button("Return selected to available", use_container_width=True):
        mark_player_drafted(store, profile.profile_id, selected_id, drafted=False)
        st.rerun()
    board = frame.copy()
    board["Draft Status"] = board["player_id"].map(
        lambda player_id: "Drafted" if str(player_id) in drafted_ids else "Available"
    )
    st.dataframe(
        board[["Rank", "Player", "Pos Rank", "Tier", "Replacement Value", "Draft Status"]],
        use_container_width=True,
        hide_index=True,
        height=560,
    )


def _render_cheat_sheet(profile: LeagueProfile, frame: pd.DataFrame, ranking) -> None:
    if frame.empty:
        st.info("Cheat sheets are blocked until rankings exist.")
        return
    st.markdown(f"### {profile.league_name} · {profile.season}")
    st.caption(
        f"{profile.team_count} teams · {profile.roster.qb} QB · {profile.roster.rb} RB · "
        f"{profile.roster.wr} WR · {profile.roster.te} TE · {profile.roster.flex} FLEX · "
        f"{profile.roster.superflex} SUPERFLEX · {profile.scoring.reception:g} PPR · "
        f"{profile.scoring.te_premium:g} TE premium. Use the browser print command for PDF."
    )
    sheet_type = st.radio("Sheet", ("Overall", "QB", "RB", "WR", "TE", "Tiers"), horizontal=True)
    if sheet_type in {"QB", "RB", "WR", "TE"}:
        sheet = frame.loc[frame["Pos"].eq(sheet_type)]
    else:
        sheet = frame
    columns = [
        "Rank",
        "Pos Rank",
        "Player",
        "Team",
        "Tier",
        "Projected Points",
        "Replacement Value",
    ]
    st.dataframe(sheet[columns], use_container_width=True, hide_index=True)
    export = sheet[columns + ["Rookie", "Evidence", "Source"]].copy()
    export.insert(0, "Projection SHA256", ranking.projection_sha256)
    export.insert(0, "Scoring", f"{profile.scoring.reception:g} PPR; {profile.scoring.te_premium:g} TE premium")
    export.insert(0, "Teams", profile.team_count)
    export.insert(0, "Season", profile.season)
    export.insert(0, "League Profile", profile.league_name)
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", profile.league_name).strip("._") or "redraft"
    st.download_button(
        "Download cheat sheet CSV",
        export.to_csv(index=False).encode("utf-8"),
        file_name=(
            f"{safe_name}_{profile.profile_id[:8]}_{profile.season}_{sheet_type}.csv"
        ),
        mime="text/csv",
    )


store = redraft_store_root(REPO_ROOT)
profiles = list_profiles(store)
active_id = active_profile_id(store)

_render_redraft_accessibility_frame()

page_header(
    "Niners War Room - Redraft",
    eyebrow=REDRAFT_AUTHORITY_LABEL,
    description=(
        "League-specific current-season scoring, replacement value, tiers, comparisons, "
        "draft boards, and cheat sheets. This is additive and separate from dynasty authority."
    ),
    status_items=((REDRAFT_AUTHORITY_LABEL, "review"), (DYNASTY_AUTHORITY_LABEL, "safe")),
)
st.warning(
    "REDRAFT - CURRENT SEASON. Redraft does not reuse or reorder Finished V1 dynasty ranks. "
    "Live rankings remain blocked without governed granular 2026 projections."
)

_render_profile_creator(store)
_render_archived_profiles(store)
for profile_error in profile_store_errors(store):
    st.error(f"Profile state needs recovery: {profile_error}")
if not profiles:
    st.info("No redraft profiles exist yet. Create one from a preset to begin.")
    st.stop()

profile_by_id = {profile.profile_id: profile for profile in profiles}
selected_id = st.selectbox(
    "League profile",
    tuple(profile_by_id),
    index=(tuple(profile_by_id).index(active_id) if active_id in profile_by_id else 0),
    format_func=lambda profile_id: _profile_label(profile_by_id[profile_id]),
)
profile = profile_by_id[selected_id]
active_cols = st.columns([2, 1])
active_cols[0].caption(
    f"Active redraft profile: {profile_by_id[active_id].league_name if active_id in profile_by_id else 'None'}"
)
if active_cols[1].button(
    "Set selected profile active",
    disabled=selected_id == active_id,
    use_container_width=True,
):
    set_active_profile(store, selected_id)
    st.success("Active redraft profile changed. Dynasty settings were not changed.")
    st.rerun()

snapshot = load_projection_snapshot(
    projection_snapshot_path(store, profile.season),
    season=profile.season,
    require_manifest=True,
)
ranking = generate_rankings(profile, snapshot)
frame = _ranking_frame(ranking)
health = build_health_report(profile, snapshot, ranking)

tabs = st.tabs(
    (
        "League Profile",
        "Rankings",
        "Tiers",
        "Position Rankings",
        "Player Compare",
        "Draft Board",
        "Cheat Sheet",
        "Data Health",
    )
)
with tabs[0]:
    _render_profile_editor(store, profile)
    _render_projection_intake(store, profile)
    _render_profile_actions(store, profile)
with tabs[1]:
    _render_rankings(ranking, frame)
with tabs[2]:
    _render_tiers(frame)
with tabs[3]:
    if frame.empty:
        st.info("No admitted ranking rows.")
    else:
        position = st.selectbox("Position ranking", sorted(frame["Pos"].unique()))
        st.dataframe(
            frame.loc[frame["Pos"].eq(position)].drop(columns=["player_id"]),
            use_container_width=True,
            hide_index=True,
        )
with tabs[4]:
    _render_player_compare(frame)
with tabs[5]:
    _render_draft_board(store, profile, frame)
with tabs[6]:
    _render_cheat_sheet(profile, frame, ranking)
with tabs[7]:
    status_cols = st.columns(4)
    status_cols[0].metric("Readiness", health.status)
    status_cols[1].metric("Ranked", health.ranked_players)
    status_cols[2].metric("Snapshot blocks", health.blocked_players)
    status_cols[3].metric("Last generated", health.last_generated_timestamp or "Never")
    st.dataframe(
        pd.DataFrame(
            (
                {"Check": "Player universe", "Ready": health.player_universe_available},
                {
                    "Check": "Current-season forecast evidence",
                    "Ready": health.current_season_forecast_available,
                },
                {"Check": "Scoring profile", "Ready": health.scoring_profile_valid},
                {
                    "Check": "Replacement calculation",
                    "Ready": health.replacement_calculation_valid,
                },
                {
                    "Check": "Stable identity uniqueness",
                    "Ready": bool(len(frame) and frame["player_id"].is_unique),
                },
                {
                    "Check": "Projection freshness",
                    "Ready": bool(snapshot.source_as_of),
                    "Detail": snapshot.source_as_of or "Not enough information",
                },
            )
        ),
        use_container_width=True,
        hide_index=True,
    )
    for message in health.messages:
        st.caption(message)
    st.info(
        "Governed scope: all 608 approved rows are rankable. Two position-conflict rookie "
        "candidates remain excluded and blocked. K/DST are unsupported; no projections are invented."
    )
    if ranking.blocked_rows:
        with st.expander("Blocked / missing players", expanded=True):
            st.dataframe(
                pd.DataFrame(ranking.blocked_rows), use_container_width=True, hide_index=True
            )
