"""Real run: Gate 3 (official factual agreement), Gate 4 (coverage), and
Gate 5 (freshness) computation for the Live Player Intelligence V1 cycle
(Worker 3 / Work Unit 5).

Standalone script -- NOT imported by any production path, NOT exercised by
pytest (reads real local files only; the raw source snapshots it reads
were already fetched by
`scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py`, and this
pass additionally re-polled nflverse injuries twice more for real
freshness evidence -- see `local_exports/.../nflverse_injuries/`).

Reads:
  * `docs/codex/live_player_intelligence_v1/official_truth_benchmark_v1/
    nflverse_week1_2026_official_truth_benchmark.csv` (Worker 2's real
    182-row benchmark, already identity-mapped to the canonical pool).
  * `docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/
    GOVERNED_COMBINED_564_PROJECTION_SNAPSHOT.csv` (the real canonical
    pool, via the already-existing `load_canonical_pool`).
  * `local_exports/live_player_intelligence_shadow_v1/sleeper_players/
    latest/sleeper_players_snapshot.json` (real Sleeper catalog pull).
  * `local_exports/live_player_intelligence_shadow_v1/nflverse_injuries/
    {wu1_snapshot_20260913,wu2_snapshot_20260914_0303,latest}/
    injuries_2026.csv` -- three real, successive polls (Worker 1's
    original pull, Worker 2's re-pull ~11 min later, and this pass's own
    re-pull ~16 min after that) used only for Gate 5's revision-diff
    evidence.

Writes:
  * `docs/codex/live_player_intelligence_v1/source_quality_evaluation_v1/
    summary.json` -- the exact machine-readable numbers below, committed.

This script performs NO production wiring and modifies no production
file. It reuses the EXISTING `build_sleeper_shadow_records` /
`match_shadow_records_to_canonical` (from
`live_player_intelligence_shadow_v1_service.py`) and `load_canonical_pool`
(from `live_player_intelligence_identity_mapping_v1_service.py`) rather
than re-deriving Sleeper's shadow-record shape or the identity join a
second time.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(REPO_ROOT))

from src.services.live_player_intelligence_identity_mapping_v1_service import (  # noqa: E402
    classify_rows,
    common_rows_from_nflverse_depth_charts,
    latest_snapshot_only,
    load_canonical_pool,
)
from src.services.live_player_intelligence_shadow_v1_service import (  # noqa: E402
    build_sleeper_shadow_records,
    match_shadow_records_to_canonical,
)
from src.services.live_player_intelligence_source_quality_v1_service import (  # noqa: E402
    AgreementPair,
    compute_agreement,
    compute_coverage,
    diff_poll_rows,
    normalize_benchmark_report_status,
    normalize_sleeper_designation,
    summarize_seconds,
)

SHADOW_ROOT = REPO_ROOT / "local_exports" / "live_player_intelligence_shadow_v1"
BENCHMARK_CSV = (
    REPO_ROOT
    / "docs"
    / "codex"
    / "live_player_intelligence_v1"
    / "official_truth_benchmark_v1"
    / "nflverse_week1_2026_official_truth_benchmark.csv"
)
SLEEPER_SNAPSHOT = SHADOW_ROOT / "sleeper_players" / "latest" / "sleeper_players_snapshot.json"
OUTPUT_DIR = REPO_ROOT / "docs" / "codex" / "live_player_intelligence_v1" / "source_quality_evaluation_v1"

NFLVERSE_POLLS = (
    ("wu1_20260913_0252", SHADOW_ROOT / "nflverse_injuries" / "wu1_snapshot_20260913" / "injuries_2026.csv"),
    ("wu2_20260914_0303", SHADOW_ROOT / "nflverse_injuries" / "wu2_snapshot_20260914_0303" / "injuries_2026.csv"),
    ("wu3_20260914_0319", SHADOW_ROOT / "nflverse_injuries" / "latest" / "injuries_2026.csv"),
)


def load_benchmark_rows() -> list[dict]:
    with BENCHMARK_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_nflverse_poll(path: Path) -> dict[str, dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["gsis_id"]: row for row in csv.DictReader(handle) if row.get("gsis_id")}


def main() -> None:
    benchmark_rows = load_benchmark_rows()
    assert len(benchmark_rows) == 182, f"expected the real 182-row benchmark, got {len(benchmark_rows)}"

    in_scope_rows = [r for r in benchmark_rows if r["identityMatchMethod"] != "UNMATCHED_POSITION_OUT_OF_SCOPE"]
    canonical_matched_rows = [r for r in in_scope_rows if r["matchedCanonicalPlayerId"]]
    unmatched_in_scope_rows = [r for r in in_scope_rows if not r["matchedCanonicalPlayerId"]]

    canonical_pool = load_canonical_pool()

    # --- Sleeper: build shadow records (flagged-only, real production
    # function) and resolve to canonical ids (same production function
    # `waiver_engine_service`/the shadow module already use). ---
    with SLEEPER_SNAPSHOT.open(encoding="utf-8") as handle:
        sleeper_catalog = json.load(handle)
    sleeper_shadow = build_sleeper_shadow_records(sleeper_catalog)
    sleeper_shadow_matched = match_shadow_records_to_canonical(sleeper_shadow, canonical_pool)
    sleeper_by_canonical_id = {
        r.matched_canonical_player_id: r for r in sleeper_shadow_matched if r.matched_canonical_player_id
    }

    # ================= GATE 4: COVERAGE =================
    # Population = the real official-report fantasy-relevant players this
    # pass can actually identify inside NWR's own canonical pool (the 52
    # GSIS-direct-matched benchmark rows). Jonathon Brooks (the single
    # UNMATCHED in-scope-position row) is reported separately, NOT folded
    # into the population -- he is not a member of NWR's governed pool at
    # all (a real, already-documented exclusion, see IDENTITY_MAPPING_V1.md),
    # so no source in NWR's pipeline could ever "cover" him regardless of
    # quality; counting him against any source would be an artifact of
    # NWR's own pool boundary, not a real coverage gap.
    population_ids = [r["matchedCanonicalPlayerId"] for r in canonical_matched_rows]
    sleeper_covered_ids = list(sleeper_by_canonical_id)
    gate4_sleeper = compute_coverage(population_ids, sleeper_covered_ids)

    # Directional-only: nflverse depth charts carries no injury field at
    # all (Gate 3 does not apply to it), but its ROLE/depth-chart-context
    # coverage of this same official-report population is real, useful
    # evidence for the depth_chart_position/depth_chart_context factual
    # fields (Work Unit 4's schema), reusing the SAME production
    # classify_rows/common_rows_from_nflverse_depth_charts functions
    # Worker 2 already built -- not a second matcher.
    depth_charts_path = SHADOW_ROOT / "nflverse_depth_charts" / "latest" / "depth_charts_2026.csv"
    with depth_charts_path.open(newline="", encoding="utf-8") as handle:
        depth_rows_all = list(csv.DictReader(handle))
    depth_rows_latest = latest_snapshot_only(depth_rows_all)
    depth_common_rows = common_rows_from_nflverse_depth_charts(depth_rows_latest)
    depth_classified = classify_rows(depth_common_rows, canonical_pool)
    depth_matched_ids = [r.matched_canonical_player_id for r in depth_classified if r.matched_canonical_player_id]
    gate4_depth_charts = compute_coverage(population_ids, depth_matched_ids)

    # ================= GATE 3: AGREEMENT =================
    # (a) The 52 nflverse-injuries-matched benchmark rows vs. THE SAME
    #     nflverse injuries file used to build the benchmark -- explicitly
    #     disclosed as circular (100% agreement by construction), per the
    #     directive's own instruction to be honest about this rather than
    #     present it as real evidence.
    nflverse_self_pairs = [
        AgreementPair(
            r["matchedCanonicalPlayerId"],
            normalize_benchmark_report_status(r["reportStatusCategory"]),
            normalize_benchmark_report_status(r["reportStatusCategory"]),
        )
        for r in canonical_matched_rows
    ]
    gate3_nflverse_self = compute_agreement(nflverse_self_pairs)

    # (b) The real, meaningful Gate-3 computation: Sleeper's injury_status
    #     vs. the benchmark, for every canonical player BOTH sides cover.
    sleeper_pairs = []
    for r in canonical_matched_rows:
        cid = r["matchedCanonicalPlayerId"]
        shadow = sleeper_by_canonical_id.get(cid)
        if shadow is None:
            continue
        sleeper_pairs.append(
            AgreementPair(
                cid,
                normalize_benchmark_report_status(r["reportStatusCategory"]),
                normalize_sleeper_designation(shadow.injury_designation),
            )
        )
    gate3_sleeper = compute_agreement(sleeper_pairs)

    # ================= GATE 5: FRESHNESS =================
    # (a) nflverse injuries -- real revision-diff evidence across THREE
    #     successive polls this cycle has now made (Worker 1's original,
    #     Worker 2's re-pull ~11 min later, this pass's own re-pull ~16
    #     min after that).
    polls = {label: load_nflverse_poll(path) for label, path in NFLVERSE_POLLS}
    poll_labels = list(polls)
    nflverse_diffs = {}
    for i in range(len(poll_labels) - 1):
        a_label, b_label = poll_labels[i], poll_labels[i + 1]
        nflverse_diffs[f"{a_label}->{b_label}"] = diff_poll_rows(
            polls[a_label], polls[b_label], compare_fields=("report_status", "practice_status")
        )

    # (b) Sleeper -- real per-player `news_updated` epoch-ms timestamps on
    # the flagged (`injury_status` real-valued) subset, as a freshness
    # PROXY (honestly labeled: this is "time since Sleeper's own record
    # for that player was last touched," not proven to be specifically
    # the injury-status field's own last-change time -- Sleeper's public
    # API documents no finer-grained per-field timestamp).
    sleeper_fetched_at_ms = None
    fetch_log_path = SHADOW_ROOT / "sleeper_players" / "latest" / "fetch_log.json"
    if fetch_log_path.exists():
        from datetime import datetime

        fetch_log = json.loads(fetch_log_path.read_text(encoding="utf-8"))
        fetched_dt = datetime.fromisoformat(str(fetch_log["fetched_at_utc"]))
        sleeper_fetched_at_ms = fetched_dt.timestamp() * 1000

    sleeper_latency_seconds: list[float] = []
    age_buckets = {"under_1h": 0, "under_24h": 0, "under_7d": 0, "under_30d": 0, "under_180d": 0, "180d_or_more": 0}
    if sleeper_fetched_at_ms is not None:
        for _sid, player in sleeper_catalog.items():
            if not isinstance(player, dict):
                continue
            injury_status = str(player.get("injury_status") or "").strip()
            if not injury_status or injury_status == "NA":
                continue
            news_updated = player.get("news_updated")
            if not isinstance(news_updated, (int, float)) or news_updated <= 0:
                continue
            latency = (sleeper_fetched_at_ms - float(news_updated)) / 1000.0
            if latency < 0:  # a future-dated news_updated is not real latency evidence
                continue
            sleeper_latency_seconds.append(latency)
            hours = latency / 3600.0
            if hours < 1:
                age_buckets["under_1h"] += 1
            elif hours < 24:
                age_buckets["under_24h"] += 1
            elif hours < 24 * 7:
                age_buckets["under_7d"] += 1
            elif hours < 24 * 30:
                age_buckets["under_30d"] += 1
            elif hours < 24 * 180:
                age_buckets["under_180d"] += 1
            else:
                age_buckets["180d_or_more"] += 1
    sleeper_freshness_summary = summarize_seconds(sleeper_latency_seconds)

    # ================= WRITE RESULTS =================
    result = {
        "benchmark": {
            "totalRows": len(benchmark_rows),
            "inScopePositionRows": len(in_scope_rows),
            "canonicalMatchedRows": len(canonical_matched_rows),
            "unmatchedInScopeRows": len(unmatched_in_scope_rows),
            "unmatchedInScopePlayerNames": [r["playerName"] for r in unmatched_in_scope_rows],
        },
        "gate4Coverage": {
            "SLEEPER_PUBLIC_PLAYERS_CATALOG": gate4_sleeper.to_dict(),
            "NFLVERSE_DEPTH_CHARTS_ROLE_CONTEXT_ONLY_NOT_AN_INJURY_FIELD": gate4_depth_charts.to_dict(),
        },
        "gate3Agreement": {
            "NFLVERSE_OFFICIAL_INJURY_REPORT_SELF_COMPARISON_CIRCULAR": gate3_nflverse_self.to_dict(),
            "SLEEPER_PUBLIC_PLAYERS_CATALOG": gate3_sleeper.to_dict(),
        },
        "gate5Freshness": {
            "NFLVERSE_OFFICIAL_INJURY_REPORT": {
                "method": "repeated-poll-and-diff (no per-row update timestamp exists in the source)",
                "polls": {label: {"fetchedAtLabel": label} for label in poll_labels},
                "diffs": nflverse_diffs,
                "p95ComputableThisSession": False,
                "reason": (
                    "Zero changes observed across all three real polls spanning "
                    "~27 minutes at this point in Week 1 -- real evidence of "
                    "stability at THIS point in the week, but no actual update "
                    "EVENT was observed during the polling window, so no latency "
                    "value can be measured (there is nothing to time). Worker "
                    "1/2's own separately-disclosed two-day-apart diff (Out "
                    "27->31 between 2026-09-11 and 2026-09-13) proves the file "
                    "DOES revise earlier in a week, but that observation window "
                    "is too coarse (~2 days) to derive a P95 latency figure "
                    "either."
                ),
            },
            "SLEEPER_PUBLIC_PLAYERS_CATALOG": {
                "method": (
                    "real per-player news_updated epoch-ms timestamp vs. this "
                    "pull's own fetched_at_utc, for the flagged (real "
                    "injury_status) subset -- a genuine freshness PROXY, not "
                    "proven to be the injury-status field's own last-change "
                    "time specifically (Sleeper documents no finer-grained "
                    "per-field timestamp)"
                ),
                "flaggedPlayerCount": len(sleeper_latency_seconds),
                "summary": sleeper_freshness_summary,
                "ageBuckets": age_buckets,
                "p95ComputableThisSession": False,
                "reason": (
                    "The raw P50/P95 above are NOT a reliable Gate 5 latency "
                    "figure: only "
                    f"{round(100 * (age_buckets['under_1h'] + age_buckets['under_24h']) / len(sleeper_latency_seconds), 1)}"
                    "% of the flagged population's "
                    "news_updated timestamps fall within 24h of this pull "
                    "(age_buckets.under_1h + under_24h = "
                    f"{age_buckets['under_1h'] + age_buckets['under_24h']} of "
                    f"{len(sleeper_latency_seconds)}), while a real, "
                    f"non-trivial tail ({age_buckets['180d_or_more']}) is "
                    "180+ DAYS old -- multi-year-old values were directly "
                    "observed in this pull (e.g. real 2019/2022/2023 "
                    "timestamps on other, unrelated players' records), "
                    "proving `news_updated` is a whole-record 'last touched "
                    "for ANY reason' field, not a field specifically bumped "
                    "every time injury_status changes. A P95 computed over "
                    "this contaminated population would overstate real "
                    "latency for the (unknown) subset of players whose "
                    "injury_status truly was set at that same recorded "
                    "time, understate it for the (unknown) subset where it "
                    "wasn't. The under-24h bucket is real, directional, "
                    "positive evidence SOME status changes are reflected "
                    "quickly; the tail is real evidence the field cannot be "
                    "trusted as a general-purpose freshness clock."
                ),
            },
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
