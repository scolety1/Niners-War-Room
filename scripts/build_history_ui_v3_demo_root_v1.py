"""History UI V3 / class-specific summary (Work Units 13-14) -- a real,
runnable demonstration root for actually rendering the upgraded History
page.

**Honesty disclosure, read first**: this script builds a FIXTURE dataset,
not real 2026-season Sleeper data. Worker 4 (this cycle) confirmed the real
production AppData trace store has ZERO decision traces recorded in it, and
this cycle's own real-data evaluator exercises (Workers 2/3) found real
owner (Fantasy Gamers roster 9) WAIVER/FAAB/TRADE/K-DST outcome data still
does not exist. Every recommendation/outcome this script writes is
synthetic, chosen to exercise EVERY real `evaluationStatus` value and all 8
real evaluator payload shapes -- it exists so a human (or this pass's own
Chrome dogfood) can actually SEE the real, upgraded History UI V3 render
correctly, not to claim real outcome numbers exist today.

Writes into an ISOLATED, throwaway `redraft_root` -- NEVER the owner's real
production AppData store (`AppData/Local/com.ninerswarroom.redraft`). Zero
network I/O (every `ingest_*_outcome` call here is a PURE function over
fabricated, already-shaped JSON -- see
`prospective_outcome_ingestion_v1_service.py`'s own module docstring for
the real shapes these fixtures mirror).

Usage:
  `python scripts/build_history_ui_v3_demo_root_v1.py [--root PATH]`

Prints the real redraft_root path and profile_id to stdout so a follow-up
dev-server launch can point `NWR_REDRAFT_ROOT`/equivalent at it.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.application.desktop_facade import DesktopBackendFacade  # noqa: E402
from src.services.in_season_decision_trace_service import (  # noqa: E402
    record_decision_trace,
    record_outcome,
    record_owner_action,
)
from src.services.prospective_outcome_ingestion_v1_service import (  # noqa: E402
    ingest_add_drop_outcome,
    ingest_faab_outcome,
    ingest_start_sit_outcome,
    ingest_streamer_outcome,
    ingest_trade_finder_outcome,
    ingest_trade_outcome,
    ingest_waiver_outcome,
)

LEAGUE_ID = "demo-league-1"
OWNER_ROSTER_ID = 9
SEASON = 2026
OUTPUT_SUMMARY_PATH = (
    REPO_ROOT / "docs" / "codex" / "prospective_outcomes_v1" / "history_ui_v3_demo_v1" / "summary.json"
)


def _matchup(week: int, starters: list[str], points: dict[str, float]) -> dict:
    return {"roster_id": OWNER_ROSTER_ID, "starters": starters, "players_points": points, "points": sum(points.values())}


def _add_transaction(player_id: str, *, status: str = "complete", waiver_bid: float | None = None) -> dict:
    settings = {"waiver_bid": waiver_bid} if waiver_bid is not None else {}
    return {"type": "waiver" if waiver_bid is not None else "free_agent", "status": status, "adds": {player_id: str(OWNER_ROSTER_ID)}, "settings": settings}


def _trade_transaction(gives: list[str], receives: list[str]) -> dict:
    adds = {pid: str(OWNER_ROSTER_ID) for pid in receives}
    drops = {pid: str(OWNER_ROSTER_ID) for pid in gives}
    return {"type": "trade", "status": "complete", "adds": adds, "drops": drops}


def build(root: Path) -> str:
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=root)
    facade.redraft_bootstrap()
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="History UI V3 Demo League")
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)

    def trace(*, tool: str, week: int | None, recommendation: dict, roster_ids: tuple = ("p1", "p2", "p3")):
        return record_decision_trace(
            root, profile_id, league_id=LEAGUE_ID, season=SEASON, week=week, tool=tool,
            engine_version="demo-v1", data_versions={}, roster_state_player_ids=roster_ids,
            recommendation=recommendation,
        )

    # --- START_SIT: one EVALUATED positive-regret example (the directive's
    # own worked example -- "+4.8 pts over chosen starter"), one negative
    # example, one still-pending (no outcome recorded at all). ---
    rec1 = {"starters": ["ss-rec-1"], "projectedTotal": 14.0}
    t1 = trace(tool="START_SIT", week=1, recommendation=rec1, roster_ids=("ss-rec-1", "ss-owner-1", "ss-bench-1"))
    detail1 = ingest_start_sit_outcome(
        week=1, recommendation=rec1, roster_state_player_ids=("ss-rec-1", "ss-owner-1", "ss-bench-1"),
        actual_matchup_entry=_matchup(1, ["ss-owner-1"], {"ss-rec-1": 14.8, "ss-owner-1": 10.0, "ss-bench-1": 3.0}),
    )
    record_outcome(root, profile_id, t1.trace_id, outcome="OBSERVED", detail=detail1.to_detail_dict())

    rec2 = {"starters": ["ss-rec-2"], "projectedTotal": 9.0}
    t2 = trace(tool="START_SIT", week=1, recommendation=rec2, roster_ids=("ss-rec-2", "ss-owner-2"))
    detail2 = ingest_start_sit_outcome(
        week=1, recommendation=rec2, roster_state_player_ids=("ss-rec-2", "ss-owner-2"),
        actual_matchup_entry=_matchup(1, ["ss-owner-2"], {"ss-rec-2": 5.0, "ss-owner-2": 7.3}),
    )
    record_outcome(root, profile_id, t2.trace_id, outcome="OBSERVED", detail=detail2.to_detail_dict())

    trace(tool="START_SIT", week=2, recommendation={"starters": ["ss-rec-3"], "projectedTotal": 11.0}, roster_ids=("ss-rec-3",))

    # --- 22 more real EVALUATED START_SIT traces (Work Unit 14 proof: at
    # 20+ real samples, the class summary card actually shows a real
    # computed mean, not just NOT_ENOUGH_DATA_YET). ---
    for i in range(22):
        week = 1
        rec_id, owner_id = f"bulk-rec-{i}", f"bulk-owner-{i}"
        recommendation = {"starters": [rec_id], "projectedTotal": 10.0}
        bulk_trace = trace(tool="START_SIT", week=week, recommendation=recommendation, roster_ids=(rec_id, owner_id))
        regret = 1.5 if i % 3 else -0.5
        rec_pts, owner_pts = 10.0 + regret, 10.0
        bulk_detail = ingest_start_sit_outcome(
            week=week, recommendation=recommendation, roster_state_player_ids=(rec_id, owner_id),
            actual_matchup_entry=_matchup(week, [owner_id], {rec_id: rec_pts, owner_id: owner_pts}),
        )
        record_outcome(root, profile_id, bulk_trace.trace_id, outcome="OBSERVED", detail=bulk_detail.to_detail_dict())

    # --- WAIVER: one won claim with real subsequent value, one genuinely
    # not-submitted (a real, honest "adoption" fact, never a fabricated
    # failure). ---
    w_rec = {"topAdd": "Waiver Guy", "topAddCanonicalId": "wv-1"}
    t3 = trace(tool="WAIVER", week=2, recommendation=w_rec)
    detail3 = ingest_waiver_outcome(
        recommended_player_id="wv-1", owner_roster_id=OWNER_ROSTER_ID,
        transactions_for_period=[_add_transaction("wv-1", waiver_bid=12)],
        horizon_matchup_entries=[_matchup(3, ["wv-1"], {"wv-1": 9.0}), _matchup(4, ["wv-1"], {"wv-1": 11.5})],
    )
    record_outcome(root, profile_id, t3.trace_id, outcome="OBSERVED", detail=detail3.to_detail_dict())

    t4 = trace(tool="WAIVER", week=2, recommendation={"topAdd": "Waiver Gal", "topAddCanonicalId": "wv-2"})
    detail4 = ingest_waiver_outcome(
        recommended_player_id="wv-2", owner_roster_id=OWNER_ROSTER_ID, transactions_for_period=[],
    )
    record_outcome(root, profile_id, t4.trace_id, outcome="OBSERVED", detail=detail4.to_detail_dict())

    # --- FAAB: the directive's own worked example -- "Won at $18; suggested
    # $15-21". ---
    f_rec = {"playerName": "FAAB Guy", "bidLowDollars": 15, "bidHighDollars": 21}
    t5 = trace(tool="FAAB", week=2, recommendation=f_rec)
    detail5 = ingest_faab_outcome(
        recommended_player_id="faab-1", owner_roster_id=OWNER_ROSTER_ID, suggested_bid_low=15, suggested_bid_high=21,
        transactions_for_period=[_add_transaction("faab-1", waiver_bid=18)],
        horizon_matchup_entries=[_matchup(3, ["faab-1"], {"faab-1": 8.0})],
    )
    record_outcome(root, profile_id, t5.trace_id, outcome="OBSERVED", detail=detail5.to_detail_dict())

    # --- ADD_DROP ---
    ad_rec = {"addedPlayerId": "add-1", "droppedPlayerId": "drop-1"}
    t6 = trace(tool="ADD_DROP", week=2, recommendation=ad_rec)
    detail6 = ingest_add_drop_outcome(
        added_player_id="add-1", dropped_player_id="drop-1", owner_roster_id=OWNER_ROSTER_ID,
        transactions_for_period=[], horizon_matchup_entries=[_matchup(3, ["add-1"], {"add-1": 6.5})],
    )
    record_outcome(root, profile_id, t6.trace_id, outcome="OBSERVED", detail=detail6.to_detail_dict())

    # --- TRADE: one accepted with a real realized delta, one rejected
    # (never a scored counterfactual). ---
    tr_rec_accepted = {"gives": ["give-1"], "receives": ["recv-1"]}
    t7 = trace(tool="TRADE", week=3, recommendation=tr_rec_accepted)
    record_owner_action(root, profile_id, t7.trace_id, action="Followed it")
    detail7 = ingest_trade_outcome(
        gives_ids=["give-1"], receives_ids=["recv-1"], owner_roster_id=OWNER_ROSTER_ID,
        transactions_for_period=[_trade_transaction(["give-1"], ["recv-1"])],
        gives_horizon_matchup_entries={"give-1": [_matchup(4, [], {"give-1": 4.0})]},
        receives_horizon_matchup_entries={"recv-1": [_matchup(4, ["recv-1"], {"recv-1": 10.5})]},
    )
    record_outcome(root, profile_id, t7.trace_id, outcome="OBSERVED", detail=detail7.to_detail_dict())

    tr_rec_rejected = {"gives": ["give-2"], "receives": ["recv-2"]}
    t8 = trace(tool="TRADE", week=3, recommendation=tr_rec_rejected)
    record_owner_action(root, profile_id, t8.trace_id, action="Did something else")
    detail8 = ingest_trade_outcome(
        gives_ids=["give-2"], receives_ids=["recv-2"], owner_roster_id=OWNER_ROSTER_ID, transactions_for_period=[],
    )
    record_outcome(root, profile_id, t8.trace_id, outcome="OBSERVED", detail=detail8.to_detail_dict())

    # --- TRADE_FINDER: accepted package. ---
    tf_rec = {"myGivePlayerId": "tf-give-1", "opponentGivePlayerId": "tf-recv-1"}
    t9 = trace(tool="TRADE_FINDER", week=3, recommendation=tf_rec)
    record_owner_action(root, profile_id, t9.trace_id, action="SENT")
    detail9 = ingest_trade_finder_outcome(
        gives_ids=["tf-give-1"], receives_ids=["tf-recv-1"], owner_roster_id=OWNER_ROSTER_ID,
        owner_action={"action": "SENT"},
        transactions_for_period=[_trade_transaction(["tf-give-1"], ["tf-recv-1"])],
        gives_horizon_matchup_entries={"tf-give-1": [_matchup(4, [], {"tf-give-1": 3.0})]},
        receives_horizon_matchup_entries={"tf-recv-1": [_matchup(4, ["tf-recv-1"], {"tf-recv-1": 9.5})]},
    )
    record_outcome(root, profile_id, t9.trace_id, outcome="OBSERVED", detail=detail9.to_detail_dict())

    # --- K/DST STREAMER: the directive's own worked example -- "Recommended
    # 12.0 actual pts; current roster K scored 6.0". Identity resolution is
    # out of scope for the real live call site (Worker 3's own finding), so
    # this fixture supplies already-resolved ids directly, honestly labeled
    # as a fixture. ---
    k_rec = {"playerName": "Kicker Guy", "team": "SF", "recommendation": "START"}
    t10 = trace(tool="K_STREAMER", week=2, recommendation=k_rec)
    detail10 = ingest_streamer_outcome(
        position="K", week=2, recommended_player_id="k-rec-1", prior_roster_option_player_id="k-cur-1",
        available_alternative_ids_at_recommendation=["k-alt-1"],
        actual_matchup_entry=_matchup(2, ["k-rec-1"], {"k-rec-1": 12.0, "k-cur-1": 6.0}),
    )
    record_outcome(root, profile_id, t10.trace_id, outcome="OBSERVED", detail=detail10.to_detail_dict())

    d_rec = {"playerName": "Defense Guy", "team": "SF", "recommendation": "START"}
    t11 = trace(tool="DST_STREAMER", week=2, recommendation=d_rec)
    detail11 = ingest_streamer_outcome(
        position="DST", week=2, recommended_player_id="SF", prior_roster_option_player_id="d-cur-1",
        available_alternative_ids_at_recommendation=["d-alt-1"],
        actual_matchup_entry=_matchup(2, ["SF"], {"SF": 11.0, "d-cur-1": 4.0}),
    )
    record_outcome(root, profile_id, t11.trace_id, outcome="OBSERVED", detail=detail11.to_detail_dict())

    # --- INSUFFICIENT_DECISION_CONTEXT: a real, legacy-shaped bare
    # outcome/notes pair with no structured detail -- proves the History UI
    # renders this honestly, never as a fabricated regret. ---
    t12 = trace(tool="START_SIT", week=2, recommendation={"starters": ["ic-1"]}, roster_ids=("ic-1",))
    record_outcome(root, profile_id, t12.trace_id, outcome="OBSERVED", notes="legacy pre-schema outcome, no detail")

    return profile_id


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, default=None, help="Redraft root directory (default: a fresh temp dir).")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(tempfile.mkdtemp(prefix="nwr-history-ui-v3-demo-"))
    profile_id = build(root)

    summary = {
        "disclosure": (
            "FIXTURE data, not real 2026-season Sleeper data. See this script's own module docstring."
        ),
        "redraftRoot": str(root),
        "profileId": profile_id,
        "leagueId": LEAGUE_ID,
    }
    OUTPUT_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"redraft_root={root}")
    print(f"profile_id={profile_id}")
    print(f"summary written to {OUTPUT_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
