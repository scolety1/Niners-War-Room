"""KHA decision shadow replay (section 12) -- retrospective case study.

Uses the REAL 157-pick live KHA draft board
(sample_data/kha_real_draft_2026/live_runtime_draft_board_157picks.json,
untouched, never modified) -- every pick identity, team, round, and the
`nwr_rank` NWR actually reported for that player AT THE TIME of the real
live draft is 100% real evidence, already captured live, not
regenerated. Original evidence is read-only throughout this script.

**Value-magnitude limitation, disclosed, not worked around**: the live
board's pick records carry `nwr_rank` (an ordinal) but not
`replacement_adjusted_value` (a points magnitude) for each player. The
only place that magnitude lives is the governed 2026 projection
snapshot -- which this session's own
docs/codex/PLAYER_UNIVERSE_SATURDAY_RENEWAL_PACKET.md already concluded
must not be reused beyond the single 2026-09-02 draft it was approved
for without fresh, real owner approval. This script does NOT load that
snapshot. Instead every Team Score / Championship Equity number below is
computed from a disclosed, uniform rank-to-value proxy
(`value = max(0, 609 - nwr_rank)`, 609 = 608 real universe rows + 1),
applied only to the 157 real players actually drafted (each keeping
their own real nwr_rank) -- never a fabricated per-player value, and
labeled a proxy, not the real magnitude, in every output column and the
CSV's own header comment. K/DST picks correctly carry no value (NWR
does not model K/DST -- same convention as production _asset_pool()).

**"Candidates" limitation, disclosed, not worked around**: the live
board only carries nwr_rank for the 157 players actually drafted -- not
for the ~450 real players who were NOT drafted in this window. Because
of that, this replay CANNOT compute "what NWR would have recommended
instead" or a Cost-of-Waiting figure (both need the full ranked
universe, not just the drafted subset) -- those columns are marked
NOT_COMPUTABLE_WITHOUT_FULL_RANKING_UNIVERSE rather than guessed. What
IS fully real and computable: the owner's own real Team Score and
Championship Equity before/after each of their real picks, evaluated
against the REAL other 15 teams' real rosters-so-far at that exact point
in the real draft (not a simulated population -- the actual field).

**No leakage**: at the owner's pick number P, every other team's roster
is built ONLY from picks with pick_number < P -- picks after P never
enter the comparison for that row.

Run: python -m scripts.run_kha_shadow_optimizer_replay_v1
Writes: docs/codex/KHA_SHADOW_OPTIMIZER_REPLAY.csv
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.services.redraft_engine_v1_service import (
    DraftContext,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.redraft_engine_v1_service import LeagueProfile as _LeagueProfile
from src.services.shadow_numeric_authorities_service import (
    ChampionshipEquityAssumptions,
    RosterPlayer,
    championship_equity,
    roster_composition_report,
    team_score,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = (
    REPO_ROOT / "sample_data" / "kha_real_draft_2026" / "live_runtime_draft_board_157picks.json"
)
OUT_PATH = REPO_ROOT / "docs" / "codex" / "KHA_SHADOW_OPTIMIZER_REPLAY.csv"

REAL_UNIVERSE_ROW_COUNT = 608
VALUE_PROXY_NOTE = "RANK_DERIVED_PROXY_NOT_REAL_MAGNITUDE"

# The real 2026 KHA High Stakes League: 16 teams, PPR, 1QB. Roster shape
# is a disclosed reconstruction (this profile is not itself carried in
# the live board fixture) matching this session's established KHA
# profile fixtures elsewhere.
KHA_PROFILE = _LeagueProfile(
    "kha-real-2026", "KHA High Stakes League", 2026, 16,
    RosterSettings(qb=1, rb=2, wr=2, te=1, flex=1, superflex=0, k=1, dst=1, bench_size=7),
    ScoringSettings(reception=1),
    DraftContext(rounds=16, draft_slot=9),
)


def rank_to_value_proxy(nwr_rank: int) -> float:
    return max(0.0, float(REAL_UNIVERSE_ROW_COUNT + 1 - nwr_rank))


def load_real_picks() -> tuple[dict, list[dict]]:
    document = json.loads(BOARD_PATH.read_text(encoding="utf-8"))
    return document, list(document["picks"])


def build_pool(all_picks: list[dict]) -> tuple[RankingResult, list[dict]]:
    """RankingResult/manual_assets covering exactly the 157 real players
    actually drafted, each with a rank_to_value_proxy(nwr_rank) value --
    see module docstring. Used only so team_score()/championship_equity()'s
    existing target_player_ids -> _asset_pool resolution path works
    unmodified, rather than special-casing around it."""
    rows: list[RedraftRankingRow] = []
    manual: list[dict] = []
    seen: set[str] = set()
    for pick in all_picks:
        player_id = str(pick["player_id"])
        if player_id in seen:
            continue
        seen.add(player_id)
        position = str(pick["position"]).upper()
        value = rank_to_value_proxy(int(pick["nwr_rank"]))
        if position in {"QB", "RB", "WR", "TE"}:
            rank = len(rows) + 1
            rows.append(
                RedraftRankingRow(
                    rank, rank, player_id, str(pick["player_name"]), position,
                    str(pick["team"]), value, 0.0, value, 0.0, "MEDIUM", 1,
                    "kha-replay", "KHA Replay", "GOVERNED", "AVAILABLE",
                    "2026-08-17", False, position_tier=1,
                )
            )
        else:  # K/DST -- manual, NWR does not model value (matches production).
            manual.append(
                {
                    "player_id": player_id, "player_name": str(pick["player_name"]),
                    "position": position, "team": str(pick["team"]),
                }
            )
    ranking = RankingResult(
        KHA_PROFILE, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "kha-replay"
    )
    return ranking, manual


def build_replay_rows() -> list[dict]:
    document, all_picks = load_real_picks()
    ranking, manual = build_pool(all_picks)
    owner_slot = int(document["owner_slot"])
    owner_picks = sorted(
        (p for p in all_picks if int(p["team_slot"]) == owner_slot),
        key=lambda p: int(p["pick_number"]),
    )
    other_slots = [slot for slot in range(1, KHA_PROFILE.team_count + 1) if slot != owner_slot]

    rows: list[dict] = []
    for pick in owner_picks:
        pick_number = int(pick["pick_number"])
        picks_before = [p for p in all_picks if int(p["pick_number"]) < pick_number]

        owner_ids_before = [
            str(p["player_id"]) for p in picks_before if int(p["team_slot"]) == owner_slot
        ]
        owner_ids_after = [*owner_ids_before, str(pick["player_id"])]
        field = {
            slot: [
                RosterPlayer(
                    str(p["player_id"]), str(p["position"]), rank_to_value_proxy(int(p["nwr_rank"]))
                )
                for p in picks_before
                if int(p["team_slot"]) == slot
            ]
            for slot in other_slots
        }
        comparable_leagues = [field] if any(field.values()) else []

        picks_by_id = {str(p["player_id"]): p for p in [*picks_before, pick]}

        def pool_players(ids: list[str], picks_by_id: dict = picks_by_id) -> list[RosterPlayer]:
            return [
                RosterPlayer(
                    pid,
                    str(picks_by_id[pid]["position"]),
                    rank_to_value_proxy(int(picks_by_id[pid]["nwr_rank"])),
                )
                for pid in ids
            ]

        before_report = roster_composition_report(pool_players(owner_ids_before), KHA_PROFILE)
        after_report = roster_composition_report(pool_players(owner_ids_after), KHA_PROFILE)

        team_score_before = ""
        team_score_after = ""
        equity_before = ""
        equity_after = ""
        if comparable_leagues:
            if owner_ids_before:
                team_score_before = team_score(
                    owner_ids_before, KHA_PROFILE, ranking, manual,
                    comparable_leagues=comparable_leagues,
                ).percentile
            team_score_after = team_score(
                owner_ids_after, KHA_PROFILE, ranking, manual,
                comparable_leagues=comparable_leagues,
            ).percentile
            if owner_ids_before:
                equity_before = championship_equity(
                    owner_ids_before, KHA_PROFILE, ranking, manual,
                    comparable_league=field, target_team_slot=owner_slot,
                    seasons=200, base_seed=20260903,
                    assumptions=ChampionshipEquityAssumptions(),
                ).win_probability
            equity_after = championship_equity(
                owner_ids_after, KHA_PROFILE, ranking, manual,
                comparable_league=field, target_team_slot=owner_slot,
                seasons=200, base_seed=20260903,
                assumptions=ChampionshipEquityAssumptions(),
            ).win_probability

        rows.append(
            {
                "pick_number": pick_number,
                "round": pick["round"],
                "player_name": pick["player_name"],
                "position": pick["position"],
                "team": pick["team"],
                "real_nwr_rank_at_time_of_pick": pick["nwr_rank"],
                "value_proxy": VALUE_PROXY_NOTE,
                "team_score_before": team_score_before,
                "team_score_after": team_score_after,
                "champ_equity_before": equity_before,
                "champ_equity_after": equity_after,
                "starter_holes_before": "; ".join(before_report.starter_holes) or "none",
                "starter_holes_after": "; ".join(after_report.starter_holes) or "none",
                "starting_lineup_value_delta": round(
                    after_report.starting_lineup_value - before_report.starting_lineup_value, 2
                ),
                "top_candidate_alternatives": "NOT_COMPUTABLE_WITHOUT_FULL_RANKING_UNIVERSE",
                "cost_of_waiting": "NOT_COMPUTABLE_WITHOUT_FULL_RANKING_UNIVERSE",
                "market_state_adp": "NOT_AVAILABLE_NO_REAL_ADP_CAPTURED_LIVE",
                "production_nwr_recommendation": "NOT_COMPUTABLE_WITHOUT_FULL_RANKING_UNIVERSE",
            }
        )
    return rows


def main() -> None:
    rows = build_replay_rows()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "# KHA_SHADOW_OPTIMIZER_REPLAY -- pick identity/team/round/"
            "real_nwr_rank_at_time_of_pick are 100% real evidence from the live "
            "157-pick KHA board. Team Score/Championship Equity values use a "
            "disclosed rank-derived value proxy (see script docstring), NOT the "
            "real replacement_adjusted_value magnitude (blocked by the expired "
            "governed snapshot -- see PLAYER_UNIVERSE_SATURDAY_RENEWAL_PACKET.md). "
            "Candidate-alternative and Cost-of-Waiting columns are "
            "NOT_COMPUTABLE_WITHOUT_FULL_RANKING_UNIVERSE: the live board only "
            "carries nwr_rank for drafted players, not the full undrafted pool.\n"
        )
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT_PATH} ({len(rows)} rows -- the owner's own real picks captured live)")
    def fmt(value: object) -> str:
        return "-" if value == "" else str(value)

    for row in rows:
        print(
            f"pick {row['pick_number']:>3} (R{row['round']}): {row['player_name']:<22} "
            f"nwr_rank={row['real_nwr_rank_at_time_of_pick']!s:<4} "
            f"team_score {fmt(row['team_score_before']):>5} -> {fmt(row['team_score_after']):>5} "
            f"champ_eq {fmt(row['champ_equity_before']):>6} -> {fmt(row['champ_equity_after']):>6}"
        )


if __name__ == "__main__":
    main()
