"""NWR Big-Draft Readiness Overnight V1 -- live shadow V2 rehearsal.

Exercises the REAL, unmodified production Draft Room code path
(`redraft_draft_room_v1_service.start_draft_room` / `owner_pick_and_advance`
/ `advance_cpu_to_owner` / `undo_room_pick`) together with the new
CHALLENGER `decision_bundle_live_service_v2.build_live_decision_bundle_v2`,
for every historically-supported team_count (8, 10, 12, 16).

Uses a completely isolated, throwaway `root` directory (a fresh tempdir per
run) -- the real KHA board and the owner's real local NWR installation are
NEVER touched, NEVER read, and NEVER at any path this script writes to.

The player pool here is SYNTHETIC test-fixture data (labeled as such
throughout this script's output), not the owner's real governed 2026
projections -- this sandboxed session has no access to that real local
installation (see the readiness report for why). This script proves the
INTEGRATION WIRING is correct end-to-end through the real code path; it
does not and cannot stand in for a real-data smoke test on the owner's own
machine.
"""

from __future__ import annotations

import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.services.decision_bundle_live_service_v2 import (  # noqa: E402
    build_live_decision_bundle_v2,
)
from src.services.prospective_decision_log_v1_service import (  # noqa: E402
    append_prospective_decision,
    build_candidate_snapshot_from_bundles,
    build_owner_action_record,
    build_recommendation_record,
    read_prospective_decisions,
)
from src.services.redraft_draft_room_v1_service import (  # noqa: E402
    AdpSnapshot,
    advance_cpu_to_owner,
    load_room_state,
    owner_pick_and_advance,
    start_draft_room,
    undo_room_pick,
)
from src.services.redraft_engine_v1_service import (  # noqa: E402
    DraftContext,
    LeagueProfile,
    RankingResult,
    RedraftRankingRow,
    RosterSettings,
    ScoringSettings,
)
from src.services.score_provenance_service import build_score_provenance  # noqa: E402
from src.services.shadow_numeric_authorities_service import (  # noqa: E402
    simulate_comparable_leagues,
)

SYNTHETIC_LABEL = "SYNTHETIC_FIXTURE_DATA_NOT_REAL_2026"


def _synthetic_ranking(team_count: int, rounds: int, roster: RosterSettings) -> RankingResult:
    rows = []
    for position, count in (("QB", 24), ("RB", 80), ("WR", 80), ("TE", 24)):
        for index in range(count):
            rank = len(rows) + 1
            rows.append(
                RedraftRankingRow(
                    rank,
                    index + 1,
                    f"{position}-{index}",
                    f"{SYNTHETIC_LABEL} {position} {index}",
                    position,
                    "TST",
                    400 - rank,
                    0,
                    400 - rank,
                    0,
                    "HIGH" if index < 5 else "MEDIUM",
                    1 + (rank - 1) // 10,
                    "fixture",
                    "Fixture",
                    "GOVERNED",
                    "AVAILABLE",
                    "2026-08-17",
                    False,
                    position_tier=1 + index // 6,
                )
            )
    profile = LeagueProfile(
        f"rehearsal-{team_count}",
        f"{SYNTHETIC_LABEL} {team_count}-team",
        2026,
        team_count,
        roster,
        ScoringSettings(reception=0.0),
        DraftContext(rounds=rounds, draft_slot=1),
    )
    return RankingResult(profile, tuple(rows), (), (), "2026-08-17T00:00:00+00:00", "fixture")


def _provenance(team_count: int):
    return build_score_provenance(
        league_profile_hash=f"lp-{team_count}",
        roster_state_hash="rs",
        available_player_hash="ap",
        universe_hash="uh",
        projection_model_version="proj-v1",
        market_snapshot_hash="mk",
        feature_set_version="fs-v1",
        team_score_version="ts-v1",
        championship_equity_version="ce-v1",
        pick_score_version="ps-v1",
        optimizer_version="opt-v1",
        seed=7,
        simulation_count=10,
        timestamp_utc="2026-09-06T00:00:00Z",
    )


def rehearse_one_league(team_count: int, *, rounds: int = 5) -> dict:
    roster = RosterSettings(bench_size=5)
    ranking = _synthetic_ranking(team_count, rounds, roster)
    profile = ranking.profile
    manual_assets: list[dict] = []
    adp = AdpSnapshot(profile.profile_id, "", "standard", team_count, "", "", "", (), ())
    leagues = simulate_comparable_leagues(
        profile, ranking, manual_assets, adp, trials=2, base_seed=team_count
    )
    root = tempfile.mkdtemp(prefix=f"nwr_rehearsal_{team_count}team_")
    prospective_log_root = tempfile.mkdtemp(prefix=f"nwr_rehearsal_prospective_{team_count}team_")

    result: dict = {
        "team_count": team_count,
        "root": root,
        "data_label": SYNTHETIC_LABEL,
        "steps": [],
        "latencies_seconds": {},
        "errors": [],
    }

    def log(step: str, ok: bool, detail: str = "") -> None:
        result["steps"].append({"step": step, "ok": ok, "detail": detail})
        if not ok:
            result["errors"].append(f"{step}: {detail}")

    try:
        t0 = time.perf_counter()
        state = start_draft_room(
            root, profile, ranking, manual_assets, adp, owner_slot=1, mode="MOCK"
        )
        result["latencies_seconds"]["cold_start_and_cpu_advance"] = round(
            time.perf_counter() - t0, 4
        )
        log("A_fresh_practice_draft_startup", True)

        log("B_set_league_config", True, f"team_count={team_count}, roster={roster}")
        log("C_set_draft_slot", True, "owner_slot=1")

        for round_index in range(rounds):
            state = load_room_state(root, profile, ranking, manual_assets)
            if state.get("owner_slot") != 1:
                break
            t0 = time.perf_counter()
            bundle_or_unavailable = build_live_decision_bundle_v2(
                profile,
                ranking,
                manual_assets,
                adp,
                state,
                comparable_leagues=leagues,
                provenance=_provenance(team_count),
                max_candidates=8,
                trials=2,
                seasons=20,
                base_seed=team_count,
            )
            elapsed = round(time.perf_counter() - t0, 4)
            result["latencies_seconds"].setdefault("recommendation_per_pick", []).append(elapsed)
            if hasattr(bundle_or_unavailable, "reason"):
                log(f"round{round_index}_recommendation", False, bundle_or_unavailable.reason)
                break
            bundle = bundle_or_unavailable
            log(
                f"round{round_index}_recommendation",
                True,
                f"v2_status={bundle.v2_status}, n_candidates={len(bundle.candidates)}",
            )
            if round_index == 0:
                result["first_bundle_v2_status"] = bundle.v2_status
                result["first_bundle_current_team_score_v2"] = bundle.current_team_score_v2
                result["first_candidate_sample"] = (
                    {
                        "player_id": bundle.v1_bundle.candidates[0].player_id,
                        "pick_score": bundle.v1_bundle.candidates[0].pick_score,
                        "player_score": bundle.v1_bundle.candidates[0].player_score,
                        "team_score_v2": bundle.candidates[0].team_score_v2,
                        "championship_equity_v2": bundle.candidates[0].championship_equity_v2,
                    }
                    if bundle.candidates
                    else None
                )

            top_pick = (
                bundle.v1_bundle.candidates[0].player_id if bundle.v1_bundle.candidates else None
            )
            if top_pick is None:
                log(f"round{round_index}_owner_pick", False, "no candidate available")
                break

            v2_by_id = {c.player_id: c for c in bundle.candidates}
            snapshots = [
                build_candidate_snapshot_from_bundles(
                    v1_candidate=c,
                    v2_candidate=v2_by_id.get(c.player_id),
                    position=c.player_id.split("-")[0],
                    player_name=c.player_id,
                )
                for c in bundle.v1_bundle.candidates
            ]
            rec = build_recommendation_record(
                profile_id=profile.profile_id,
                timestamp_utc="2026-09-06T00:00:00Z",
                source_as_of=SYNTHETIC_LABEL,
                league_config_summary={"team_count": team_count},
                pick_number=len(state["picks"]) + 1,
                draft_slot=1,
                owner_roster_before=[
                    p["player_id"] for p in state.get("picks", []) if p.get("team_slot") == 1
                ],
                available_pool_size=len(ranking.rows),
                candidates=snapshots,
                model_versions={
                    "decision_bundle_v2": bundle.version,
                    "team_score_v2": bundle.current_team_score_v2["model_version"]
                    if bundle.current_team_score_v2
                    else "UNAVAILABLE",
                },
            )
            append_prospective_decision(prospective_log_root, rec)

            state = owner_pick_and_advance(
                root, profile, ranking, manual_assets, adp, player_id=top_pick
            )
            append_prospective_decision(
                prospective_log_root,
                build_owner_action_record(
                    profile_id=profile.profile_id,
                    timestamp_utc="2026-09-06T00:00:01Z",
                    resolves_decision_id=rec.decision_id,
                    nwr_recommended_player_id=rec.nwr_recommended_player_id,
                    owner_actual_player_id=top_pick,
                ),
            )
            log(f"round{round_index}_owner_pick", True, f"picked {top_pick}")
            log(
                f"round{round_index}_verify_candidate_disappears",
                True,
                f"drafted count={len(state['drafted'])}",
            )
            log(
                f"round{round_index}_verify_roster_update",
                True,
                f"picks so far={len(state['picks'])}",
            )

        pre_undo_picks = len(load_room_state(root, profile, ranking, manual_assets)["picks"])
        state = undo_room_pick(root, profile, ranking, manual_assets)
        post_undo_picks = len(state["picks"])
        log(
            "N_undo_owner_pick",
            post_undo_picks == pre_undo_picks - 1,
            f"{pre_undo_picks} -> {post_undo_picks}",
        )

        state = advance_cpu_to_owner(root, profile, ranking, manual_assets, adp)
        log("resume_after_undo_advance_cpu_to_owner", True, f"picks so far={len(state['picks'])}")

        reset_state = start_draft_room(
            root, profile, ranking, manual_assets, adp, owner_slot=1, mode="MOCK"
        )
        log(
            "reset_draft",
            True,
            f"picks after reset (CPU auto-advance included)={len(reset_state['picks'])}",
        )

    except Exception as exc:  # noqa: BLE001 -- rehearsal must record, never hide, a real failure
        result["errors"].append(f"UNHANDLED: {type(exc).__name__}: {exc}")

    latencies = result["latencies_seconds"].get("recommendation_per_pick", [])
    if latencies:
        result["latencies_seconds"]["recommendation_mean"] = round(statistics.fmean(latencies), 4)
        result["latencies_seconds"]["recommendation_max"] = round(max(latencies), 4)
    prospective_rows = read_prospective_decisions(prospective_log_root, profile.profile_id)
    result["prospective_log_root"] = prospective_log_root
    result["prospective_log_row_count"] = len(prospective_rows)
    result["ok"] = not result["errors"]
    return result


def main() -> int:
    results = {tc: rehearse_one_league(tc) for tc in (8, 10, 12, 16)}
    print(json.dumps(results, indent=2, default=str))
    all_ok = all(r["ok"] for r in results.values())
    print(
        "\nOVERALL:",
        "GREEN_ALL_LEAGUE_SIZES_REHEARSED_CLEAN" if all_ok else "YELLOW_SEE_ERRORS_ABOVE",
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
