from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.services.redraft_2026_projection_model_service import (
    CURRENTLY_ROSTERED_STATUSES,
    MODEL_STAT_COLUMNS,
    score_half_ppr,
)

MODEL_ID = "NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1"
MODEL_POSITIONS = ("QB", "RB", "WR", "TE")
# NWR class-time hardening, Brooks-class source-gap fix (real, root-caused:
# docs/codex/NWR_BROOKS_DIGGS_JUDKINS_ROOT_CAUSE_V1_20260908.md). A current,
# active NFL player with real draft capital (e.g. a 2024 2nd-rounder who
# tore an ACL and recorded ~0 rookie-year games) is functionally in the same
# position as a true rookie: no usable own prior-season stat line for the
# persistence model to project from. `INSUFFICIENT_HISTORY_FALLBACK_MODEL_ID`
# reuses the exact same real position+round rookie-year cohort methodology
# already validated for true rookies below (cohort_projection/median_stats)
# -- no fabricated stat line for the specific player, only a real median of
# OTHER real players' real rookie-year outcomes at the same draft slot.
INSUFFICIENT_HISTORY_FALLBACK_MODEL_ID = (
    "NWR_REDRAFT_2026_INSUFFICIENT_HISTORY_DRAFT_CAPITAL_COHORT_FALLBACK_V1"
)
INSUFFICIENT_HISTORY_BLOCK_REASONS = frozenset(
    {
        "no prior-season NFL stat line; persistence forecast blocked",
        "prior-season games are zero; persistence forecast blocked",
    }
)
MIN_COHORT_ROWS = 8
SOURCE_STAT_COLUMNS = {
    "games": "games",
    "attempts": "attempts",
    "completions": "completions",
    "passing_yards": "passing_yards",
    "passing_tds": "passing_tds",
    "interceptions": "passing_interceptions",
    "carries": "carries",
    "rushing_yards": "rushing_yards",
    "rushing_tds": "rushing_tds",
    "targets": "targets",
    "receptions": "receptions",
    "receiving_yards": "receiving_yards",
    "receiving_tds": "receiving_tds",
    "passing_first_downs": "passing_first_downs",
    "rushing_first_downs": "rushing_first_downs",
    "receiving_first_downs": "receiving_first_downs",
    "return_tds": "special_teams_tds",
    "fumbles_lost": "fumbles_lost_total",
}
STAT_FILE_COLUMNS = tuple(dict.fromkeys(SOURCE_STAT_COLUMNS.values())) + (
    "punt_return_yards",
    "kickoff_return_yards",
)


@dataclass(frozen=True)
class RookieProjectionBuildResult:
    projections: pd.DataFrame
    blocked: pd.DataFrame
    identity: pd.DataFrame


def load_draft_evidence(path: str | Path, seasons: Iterable[int]) -> pd.DataFrame:
    """Load only identity and draft-day facts; career outcome fields are never selected."""
    allowed = [
        "season",
        "round",
        "pick",
        "team",
        "gsis_id",
        "pfr_player_id",
        "pfr_player_name",
        "position",
        "college",
        "age",
    ]
    frame = pd.read_parquet(path, columns=allowed)
    season_set = {int(value) for value in seasons}
    frame = frame[
        frame["season"].isin(season_set) & frame["position"].isin(MODEL_POSITIONS)
    ].copy()
    frame["season"] = frame["season"].astype(int)
    frame["round"] = frame["round"].astype(int)
    frame["pick"] = frame["pick"].astype(int)
    if frame.duplicated(["season", "pick"]).any():
        raise ValueError("Draft evidence contains duplicate season/pick identities.")
    return frame.sort_values(["season", "pick"], kind="stable").reset_index(drop=True)


def load_player_registry(path: str | Path) -> pd.DataFrame:
    columns = [
        "gsis_id",
        "display_name",
        "pfr_id",
        "position",
        "latest_team",
        "status",
        "rookie_season",
        "last_season",
    ]
    frame = pd.read_parquet(path, columns=columns)
    return frame[frame["gsis_id"].notna()].copy()


def attach_exact_identities(draft: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """Attach an exact GSIS identity by PFR ID, then unique normalized name+position.

    Name normalization removes punctuation, accents, whitespace, and common suffixes. It is an
    exact-key fallback, not a fuzzy or approximate join. PFR identity wins when both exist.
    """
    registry = players.copy()
    registry["identity_key"] = registry.apply(
        lambda row: f"{normalize_name(row['display_name'])}|{row['position']}", axis=1
    )
    key_counts = registry["identity_key"].value_counts()
    unique_registry = registry[
        registry["identity_key"].map(key_counts).eq(1)
    ].set_index("identity_key")
    pfr_registry = (
        registry[registry["pfr_id"].notna()]
        .sort_values(["pfr_id", "gsis_id"], kind="stable")
        .drop_duplicates("pfr_id", keep=False)
        .set_index("pfr_id")
    )
    output = draft.copy()
    output["identity_key"] = output.apply(
        lambda row: f"{normalize_name(row['pfr_player_name'])}|{row['position']}", axis=1
    )
    output["pfr_gsis_id"] = output["pfr_player_id"].map(pfr_registry["gsis_id"])
    output["name_gsis_id"] = output["identity_key"].map(unique_registry["gsis_id"])
    output["player_id"] = output["pfr_gsis_id"].fillna(output["name_gsis_id"])
    output["identity_method"] = "UNRESOLVED"
    output.loc[output["name_gsis_id"].notna(), "identity_method"] = (
        "EXACT_NORMALIZED_NAME_POSITION"
    )
    output.loc[output["pfr_gsis_id"].notna(), "identity_method"] = "EXACT_PFR_ID_BRIDGE"
    output["identity_conflict"] = (
        output["pfr_gsis_id"].notna()
        & output["name_gsis_id"].notna()
        & output["pfr_gsis_id"].ne(output["name_gsis_id"])
    )
    return output


def load_rookie_outcome_frame(
    raw_directory: str | Path,
    draft: pd.DataFrame,
    seasons: Iterable[int],
) -> pd.DataFrame:
    """Join rookie-year REG outcomes; a missing stat row is a genuine zero outcome."""
    raw_directory = Path(raw_directory)
    frames: list[pd.DataFrame] = []
    requested = sorted({int(value) for value in seasons})
    columns = ["player_id", "season", "season_type", *STAT_FILE_COLUMNS]
    for season in requested:
        path = raw_directory / f"player_stats_seasonal_{season}.parquet"
        frame = pd.read_parquet(path, columns=columns)
        frame = frame[frame["season_type"].eq("REG")].copy()
        if frame.duplicated(["season", "player_id"]).any():
            raise ValueError(f"{path.name} contains duplicate regular-season player rows.")
        frames.append(frame)
    stats = pd.concat(frames, ignore_index=True)
    resolved = draft[draft["player_id"].notna()].copy()
    output = resolved.merge(stats, on=["season", "player_id"], how="left", validate="1:1")
    output["outcome_row_found"] = output["games"].notna()
    for model_column, source_column in SOURCE_STAT_COLUMNS.items():
        output[model_column] = pd.to_numeric(output[source_column], errors="coerce").fillna(0.0)
    output["return_yards"] = (
        pd.to_numeric(output["punt_return_yards"], errors="coerce").fillna(0.0)
        + pd.to_numeric(output["kickoff_return_yards"], errors="coerce").fillna(0.0)
    )
    return output.sort_values(["season", "pick"], kind="stable").reset_index(drop=True)


def temporal_backtest(
    history: pd.DataFrame,
    *,
    seasons: Iterable[int],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Walk forward by draft class with no target/future class in its training pool."""
    prediction_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for target_season in sorted({int(value) for value in seasons}):
        training = history[history["season"].lt(target_season)].copy()
        actuals = history[history["season"].eq(target_season)].copy()
        for record in actuals.to_dict("records"):
            position = str(record["position"])
            round_number = int(record["round"])
            model_row, model_scope, cohort_rows = cohort_projection(
                training, position=position, round_number=round_number
            )
            baseline_row = median_stats(training[training["position"].eq(position)])
            predicted_points = score_half_ppr(model_row)
            baseline_points = score_half_ppr(baseline_row)
            actual_points = score_half_ppr(record)
            prediction_rows.append(
                {
                    "season": target_season,
                    "player_id": record["player_id"],
                    "player_name": record["pfr_player_name"],
                    "position": position,
                    "round": round_number,
                    "pick": int(record["pick"]),
                    "training_max_season": int(training["season"].max()),
                    "cohort_scope": model_scope,
                    "cohort_rows": cohort_rows,
                    "predicted_points": round(predicted_points, 4),
                    "baseline_points": round(baseline_points, 4),
                    "actual_points": round(actual_points, 4),
                    "absolute_error": round(abs(predicted_points - actual_points), 4),
                    "baseline_absolute_error": round(
                        abs(baseline_points - actual_points), 4
                    ),
                }
            )
        target_predictions = pd.DataFrame(
            [row for row in prediction_rows if row["season"] == target_season]
        )
        for position, group in target_predictions.groupby("position", sort=True):
            summary_rows.append(_backtest_summary_row(target_season, position, group))
        summary_rows.append(_backtest_summary_row(target_season, "ALL", target_predictions))
    predictions = pd.DataFrame(prediction_rows).sort_values(
        ["season", "pick"], kind="stable"
    )
    summaries = pd.DataFrame(summary_rows).sort_values(
        ["season", "position"], kind="stable"
    )
    return predictions, summaries


def build_current_rookie_candidate(
    current_draft: pd.DataFrame,
    players: pd.DataFrame,
    history: pd.DataFrame,
    *,
    season: int,
    source_as_of: str,
    uncertainty_by_position: dict[str, float],
) -> RookieProjectionBuildResult:
    attached = attach_exact_identities(current_draft, players)
    current_columns = {
        "gsis_id": "current_gsis_id",
        "display_name": "current_name",
        "position": "current_position",
        "latest_team": "current_team",
        "status": "current_status",
        "rookie_season": "current_rookie_season",
        "last_season": "current_last_season",
    }
    current = players[list(current_columns)].rename(columns=current_columns)
    attached = attached.merge(
        current,
        left_on="player_id",
        right_on="current_gsis_id",
        how="left",
        validate="m:1",
    )
    projection_rows: list[dict[str, object]] = []
    blocked_rows: list[dict[str, object]] = []
    identity_rows: list[dict[str, object]] = []
    for record in attached.sort_values("pick", kind="stable").to_dict("records"):
        reason = ""
        if pd.isna(record["player_id"]):
            reason = "exact current GSIS identity unresolved"
        elif bool(record["identity_conflict"]):
            reason = "PFR and exact normalized-name identity conflict"
        elif pd.isna(record["current_gsis_id"]):
            reason = "exact identity absent from current registry"
        elif int(record.get("current_rookie_season") or 0) != season:
            reason = "current registry does not classify player as a 2026 rookie"
        elif str(record.get("current_status")) not in CURRENTLY_ROSTERED_STATUSES:
            # NWR next-draft rookie/insufficient-history closure (2026-09-08):
            # same real, owner-approved distinction now applied to veterans
            # (redraft_2026_projection_model_service.py) -- PLAYER UNIVERSE
            # ELIGIBILITY is separate from FANTASY AVAILABILITY/RISK. A real
            # rookie on EXE/RSR/PUP remains on an NFL roster and realistically
            # startable later in the season; DEV (practice squad) and a
            # genuine departure (RET/INA/CUT/SUS/NWT/RLS) do not.
            reason = "current factual roster status is not a currently-rostered status"
        elif str(record.get("current_position")) != str(record["position"]):
            reason = "draft position conflicts with current factual registry position"
        identity_rows.append(
            {
                "season": season,
                "draft_pick": int(record["pick"]),
                "draft_round": int(record["round"]),
                "draft_name": record["pfr_player_name"],
                "draft_position": record["position"],
                "player_id": "" if pd.isna(record["player_id"]) else record["player_id"],
                "current_name": record.get("current_name") or "",
                "current_position": record.get("current_position") or "",
                "current_team": record.get("current_team") or "",
                "current_status": record.get("current_status") or "",
                "identity_method": record["identity_method"],
                "identity_conflict": bool(record["identity_conflict"]),
                "projection_status": "BLOCKED" if reason else "ELIGIBLE",
                "block_reason": reason,
            }
        )
        if reason:
            blocked_rows.append(identity_rows[-1])
            continue
        model_row, cohort_scope, cohort_rows = cohort_projection(
            history,
            position=str(record["position"]),
            round_number=int(record["round"]),
        )
        points = score_half_ppr(model_row)
        uncertainty = float(uncertainty_by_position[str(record["position"])])
        current_status = str(record.get("current_status") or "")
        provenance = (
            "nflverse 2012-2025 rookie outcomes by position+draft round; "
            "2026 draft capital; current exact GSIS registry status/team"
        )
        if current_status not in {"ACT", "RES"}:
            # Real, exact status preserved (not discarded) for a currently-
            # rostered-but-not-ACT/RES player -- deliberately NOT expressed as
            # a projection-value or availability_probability discount (no
            # validated calibration exists for this; availability_probability
            # is already known, from prior real research, to be a mechanical
            # restatement of `games` with no event-specific signal -- see
            # score_projection_availability_adjusted's own docstring in
            # redraft_engine_v1_service.py). Visible here as real, disclosed
            # provenance text; a live, scoring-neutral status/risk UI signal
            # for this is a real, disclosed follow-up, not built this pass.
            provenance = f"{provenance}; current NFL roster status: {current_status}"
        output: dict[str, object] = {
            "player_id": record["player_id"],
            "player_name": record["current_name"],
            "position": record["position"],
            "team": record["current_team"],
            "season": season,
            "source_id": MODEL_ID,
            "source_as_of": source_as_of,
            "source_status": "GOVERNANCE_PENDING",
            "evidence_status": "MODEL_VALIDATED_REVIEW_ONLY",
            "provenance": provenance,
            "rookie": True,
        }
        output.update(model_row)
        output["projection_low"] = round(max(0.0, points - uncertainty), 4)
        output["projection_high"] = round(points + uncertainty, 4)
        output["availability_probability"] = round(float(output["games"]) / 17.0, 4)
        output["_draft_round"] = int(record["round"])
        output["_draft_pick"] = int(record["pick"])
        output["_cohort_scope"] = cohort_scope
        output["_cohort_rows"] = cohort_rows
        projection_rows.append(output)
    projection_frame = pd.DataFrame(projection_rows)
    stable_columns = [
        "player_id",
        "player_name",
        "position",
        "team",
        "season",
        "source_id",
        "source_as_of",
        "source_status",
        "evidence_status",
        "provenance",
        "rookie",
        *MODEL_STAT_COLUMNS,
        "projection_low",
        "projection_high",
        "availability_probability",
        "_draft_round",
        "_draft_pick",
        "_cohort_scope",
        "_cohort_rows",
    ]
    return RookieProjectionBuildResult(
        projections=projection_frame.reindex(columns=stable_columns).sort_values(
            ["_draft_pick"], kind="stable"
        ),
        blocked=pd.DataFrame(blocked_rows).sort_values("draft_pick", kind="stable"),
        identity=pd.DataFrame(identity_rows).sort_values("draft_pick", kind="stable"),
    )


def build_insufficient_history_fallback_candidate(
    blocked: pd.DataFrame,
    draft: pd.DataFrame,
    rookie_outcome_history: pd.DataFrame,
    *,
    season: int,
    source_as_of: str,
    uncertainty_by_position: dict[str, float],
) -> RookieProjectionBuildResult:
    """Brooks-class fallback for a current, active NFL player with real draft capital
    but insufficient own prior-season production for the veteran persistence model.

    `blocked` is `build_current_projection_candidate(...).blocked` from the veteran
    persistence model (redraft_2026_projection_model_service.py) -- reused as-is so
    eligibility (current ACT/RES status, current position, admitted universe) is never
    re-derived or duplicated. Only rows whose block reason is a genuine "no usable own
    prior-season stat line" (`INSUFFICIENT_HISTORY_BLOCK_REASONS`) are considered here;
    a true 2026 rookie (blocked for a different reason) has its own dedicated lane in
    `build_current_rookie_candidate` and is never touched by this function.

    `draft` is real NFL draft-pick evidence (`load_draft_evidence`, any historical
    seasons) -- a player with no real draft record (undrafted) is left genuinely
    unprojectable here, not guessed at. `rookie_outcome_history` is the same real
    rookie-year outcome frame (`load_rookie_outcome_frame`) already used to train the
    true-rookie cohort model; no separate training pool is built for this fallback.
    """
    candidates = blocked[blocked["reason"].isin(INSUFFICIENT_HISTORY_BLOCK_REASONS)].copy()
    draft_by_gsis = (
        draft[draft["gsis_id"].notna()]
        .sort_values(["season", "gsis_id"], kind="stable")
        .drop_duplicates("gsis_id", keep="last")
        .set_index("gsis_id")
    )
    projection_rows: list[dict[str, object]] = []
    blocked_rows: list[dict[str, object]] = []
    identity_rows: list[dict[str, object]] = []
    for record in candidates.sort_values("player_id", kind="stable").to_dict("records"):
        player_id = str(record["player_id"])
        position = str(record["position"])
        draft_row = draft_by_gsis.loc[player_id] if player_id in draft_by_gsis.index else None
        reason = ""
        if draft_row is None:
            reason = "no real NFL draft-capital record; insufficient-history fallback not applicable"
        elif str(draft_row["position"]) != position:
            reason = "draft-record position conflicts with current factual registry position"
        identity_rows.append(
            {
                "player_id": player_id,
                "player_name": record["player_name"],
                "position": position,
                "team": record["team"],
                "draft_season": "" if draft_row is None else int(draft_row["season"]),
                "draft_round": "" if draft_row is None else int(draft_row["round"]),
                "draft_pick": "" if draft_row is None else int(draft_row["pick"]),
                "projection_status": "BLOCKED" if reason else "ELIGIBLE",
                "block_reason": reason,
            }
        )
        if reason:
            blocked_rows.append(identity_rows[-1])
            continue
        model_row, cohort_scope, cohort_rows = cohort_projection(
            rookie_outcome_history, position=position, round_number=int(draft_row["round"])
        )
        points = score_half_ppr(model_row)
        uncertainty = float(uncertainty_by_position.get(position, max(25.0, 0.40 * points)))
        output: dict[str, object] = {
            "player_id": player_id,
            "player_name": record["player_name"],
            "position": position,
            "team": record["team"],
            "season": season,
            "source_id": INSUFFICIENT_HISTORY_FALLBACK_MODEL_ID,
            "source_as_of": source_as_of,
            "source_status": "GOVERNANCE_PENDING",
            "evidence_status": "MODEL_VALIDATED_REVIEW_ONLY",
            "provenance": (
                f"real draft round {int(draft_row['round'])} (drafted season "
                f"{int(draft_row['season'])}); position+round rookie-year outcome cohort "
                "median from OTHER real players -- no fabricated stat line for this player"
            ),
            "rookie": False,
        }
        output.update(model_row)
        output["projection_low"] = round(max(0.0, points - uncertainty), 4)
        output["projection_high"] = round(points + uncertainty, 4)
        output["availability_probability"] = round(float(output["games"]) / 17.0, 4)
        output["_draft_round"] = int(draft_row["round"])
        output["_draft_pick"] = int(draft_row["pick"])
        output["_draft_season"] = int(draft_row["season"])
        output["_cohort_scope"] = cohort_scope
        output["_cohort_rows"] = cohort_rows
        projection_rows.append(output)
    projection_frame = pd.DataFrame(projection_rows)
    stable_columns = [
        "player_id",
        "player_name",
        "position",
        "team",
        "season",
        "source_id",
        "source_as_of",
        "source_status",
        "evidence_status",
        "provenance",
        "rookie",
        *MODEL_STAT_COLUMNS,
        "projection_low",
        "projection_high",
        "availability_probability",
        "_draft_round",
        "_draft_pick",
        "_draft_season",
        "_cohort_scope",
        "_cohort_rows",
    ]
    identity_columns = [
        "player_id",
        "player_name",
        "position",
        "team",
        "draft_season",
        "draft_round",
        "draft_pick",
        "projection_status",
        "block_reason",
    ]
    return RookieProjectionBuildResult(
        projections=projection_frame.reindex(columns=stable_columns).sort_values(
            ["_draft_pick"], kind="stable"
        )
        if projection_rows
        else pd.DataFrame(columns=stable_columns),
        blocked=pd.DataFrame(blocked_rows, columns=identity_columns).sort_values(
            "player_id", kind="stable"
        ),
        identity=pd.DataFrame(identity_rows, columns=identity_columns).sort_values(
            "player_id", kind="stable"
        ),
    )


def uncertainty_from_predictions(predictions: pd.DataFrame) -> dict[str, float]:
    return {
        str(position): round(float(group["absolute_error"].quantile(0.80)), 4)
        for position, group in predictions.groupby("position", sort=True)
    }


def promotion_gates(
    *,
    historical_draft: pd.DataFrame,
    predictions: pd.DataFrame,
    summaries: pd.DataFrame,
    candidate: RookieProjectionBuildResult,
) -> pd.DataFrame:
    overall = summaries[summaries["position"].eq("ALL")]
    position_totals = _aggregate_backtest(predictions)
    gates: list[dict[str, object]] = []

    def add(gate: str, passed: bool, evidence: str) -> None:
        gates.append({"gate": gate, "status": "PASS" if passed else "FAIL", "evidence": evidence})

    coverage = float(historical_draft["player_id"].notna().mean())
    add(
        "historical_exact_identity_coverage_gte_98pct",
        coverage >= 0.98,
        f"coverage={coverage:.4f}",
    )
    add(
        "walk_forward_training_precedes_target",
        bool((predictions["training_max_season"] < predictions["season"]).all()),
        "every prediction has training_max_season < target season",
    )
    all_lift = float(overall["mae_improvement"].mean())
    add(
        "selected_model_beats_position_median_overall",
        all_lift > 0,
        f"mean season lift={all_lift:.4f}",
    )
    position_pass = bool((position_totals["model_mae"] < position_totals["baseline_mae"]).all())
    add(
        "selected_model_beats_position_median_each_position",
        position_pass,
        "; ".join(
            f"{row.position}={row.baseline_mae - row.model_mae:.4f}"
            for row in position_totals.itertuples()
        ),
    )
    add(
        "current_identity_and_role_gate",
        len(candidate.projections) > 0
        and candidate.projections["player_id"].notna().all()
        and candidate.projections["position"].isin(MODEL_POSITIONS).all(),
        f"eligible={len(candidate.projections)} blocked={len(candidate.blocked)}",
    )
    numeric = candidate.projections[list(MODEL_STAT_COLUMNS)]
    add(
        "projection_numeric_nonnegative",
        bool(
            numeric.notna().all().all()
            and numeric.ge(0).all().all()
        ),
        "all granular projection values are finite and nonnegative",
    )
    projected_points = candidate.projections.apply(score_half_ppr, axis=1)
    coherent_bounds = (
        projected_points.ge(0)
        & candidate.projections["projection_low"].le(projected_points)
        & candidate.projections["projection_high"].ge(projected_points)
        & candidate.projections["projection_low"].le(
            candidate.projections["projection_high"]
        )
    )
    add(
        "projection_score_and_bounds_coherent",
        bool(coherent_bounds.all()),
        "half-PPR central scores are nonnegative and contained by low/high bounds",
    )
    add(
        "rookie_layer_not_governed_or_installed",
        candidate.projections["source_status"].eq("GOVERNANCE_PENDING").all(),
        "candidate remains review-only pending exact SHA owner approval",
    )
    add(
        "k_dst_blocked",
        not candidate.projections["position"].isin(["K", "DST"]).any(),
        "candidate positions limited to QB/RB/WR/TE",
    )
    return pd.DataFrame(gates)


def aggregate_backtest(predictions: pd.DataFrame) -> pd.DataFrame:
    return _aggregate_backtest(predictions)


def normalize_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", text.lower())
    return re.sub(r"[^a-z0-9]", "", text)


def cohort_projection(
    training: pd.DataFrame,
    *,
    position: str,
    round_number: int,
) -> tuple[dict[str, float], str, int]:
    position_pool = training[training["position"].eq(position)]
    cohort = position_pool[position_pool["round"].eq(round_number)]
    scope = "POSITION_ROUND"
    if len(cohort) < MIN_COHORT_ROWS:
        cohort = position_pool
        scope = "POSITION_FALLBACK"
    if cohort.empty:
        raise ValueError(f"No historical rookie cohort for {position} round {round_number}.")
    return median_stats(cohort), scope, len(cohort)


def median_stats(frame: pd.DataFrame) -> dict[str, float]:
    row = {
        column: round(float(pd.to_numeric(frame[column], errors="coerce").fillna(0.0).median()), 4)
        for column in MODEL_STAT_COLUMNS
    }
    # Component-wise medians can otherwise combine a zero opportunity median with a positive
    # event median. These deterministic constraints preserve valid stat relationships.
    if row["games"] <= 0:
        return {column: 0.0 for column in MODEL_STAT_COLUMNS}
    if row["attempts"] <= 0:
        for column in (
            "attempts",
            "completions",
            "passing_yards",
            "passing_tds",
            "interceptions",
            "passing_first_downs",
        ):
            row[column] = 0.0
    else:
        row["completions"] = min(row["completions"], row["attempts"])
    if row["carries"] <= 0:
        for column in ("carries", "rushing_yards", "rushing_tds", "rushing_first_downs"):
            row[column] = 0.0
    if row["targets"] <= 0:
        for column in (
            "targets",
            "receptions",
            "receiving_yards",
            "receiving_tds",
            "receiving_first_downs",
        ):
            row[column] = 0.0
    else:
        row["receptions"] = min(row["receptions"], row["targets"])
    if row["return_yards"] <= 0:
        row["return_tds"] = 0.0
    if row["attempts"] + row["carries"] + row["targets"] + row["return_yards"] <= 0:
        row["fumbles_lost"] = 0.0
    # Component medians can also combine low positive production with a higher median turnover
    # count and yield a negative central season score. Preserve the median turnover mix while
    # scaling it only as far as the deterministic half-PPR line can support.
    penalty_free = dict(row)
    penalty_free["interceptions"] = 0.0
    penalty_free["fumbles_lost"] = 0.0
    turnover_budget = max(0.0, score_half_ppr(penalty_free) / 2.0)
    turnovers = row["interceptions"] + row["fumbles_lost"]
    if turnovers > turnover_budget and turnovers > 0:
        scale = turnover_budget / turnovers
        row["interceptions"] = round(row["interceptions"] * scale, 4)
        row["fumbles_lost"] = round(row["fumbles_lost"] * scale, 4)
    return row


def _backtest_summary_row(
    season: int,
    position: str,
    frame: pd.DataFrame,
) -> dict[str, object]:
    model_mae = float(frame["absolute_error"].mean())
    baseline_mae = float(frame["baseline_absolute_error"].mean())
    spearman = _rank_correlation(frame["predicted_points"], frame["actual_points"])
    return {
        "season": season,
        "position": position,
        "player_count": len(frame),
        "model_mae": round(model_mae, 4),
        "position_median_mae": round(baseline_mae, 4),
        "mae_improvement": round(baseline_mae - model_mae, 4),
        "spearman": "" if pd.isna(spearman) else round(float(spearman), 4),
        "absolute_error_p80": round(float(frame["absolute_error"].quantile(0.80)), 4),
    }


def _aggregate_backtest(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for position, group in predictions.groupby("position", sort=True):
        model_mae = float(group["absolute_error"].mean())
        baseline_mae = float(group["baseline_absolute_error"].mean())
        spearman = _rank_correlation(group["predicted_points"], group["actual_points"])
        rows.append(
            {
                "position": position,
                "player_count": len(group),
                "model_mae": round(model_mae, 4),
                "baseline_mae": round(baseline_mae, 4),
                "mae_improvement": round(baseline_mae - model_mae, 4),
                "spearman": "" if pd.isna(spearman) else round(float(spearman), 4),
                "absolute_error_p80": round(float(group["absolute_error"].quantile(0.80)), 4),
            }
        )
    return pd.DataFrame(rows)


def _rank_correlation(left: pd.Series, right: pd.Series) -> float:
    left_rank = left.rank(method="average")
    right_rank = right.rank(method="average")
    if len(left_rank) < 2 or left_rank.nunique() < 2 or right_rank.nunique() < 2:
        return float("nan")
    return float(left_rank.corr(right_rank))
