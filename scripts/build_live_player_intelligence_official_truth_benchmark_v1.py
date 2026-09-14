"""Real run: builds the Work Unit 2 OFFICIAL TRUTH BENCHMARK dataset.

Standalone script -- NOT imported by any production path, NOT exercised by
pytest (reads real local files only; the raw nflverse injuries file it
reads was fetched by the existing, already-admissible
`scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py`, which has
no restrictive rights posture -- see
`docs/codex/live_player_intelligence_v1/OFFICIAL_TRUTH_BENCHMARK_V1.md` for
the full rights rationale and the small, one-off, manually-issued NFL.com
cross-check that independently corroborated it).

THIS IS A TRUTH BENCHMARK FOR EVALUATION, NOT A PRODUCTION REDISTRIBUTION.
It exists so a later, separate promotion pass can measure Gate 3 (official
factual agreement) and Gate 5 (freshness) against something concrete.
Production admission of any source (Gate 9 -- rights compatible with
NWR's actual caching/redistribution/commercial-use pattern) is a SEPARATE
decision this script and doc do not make.

Joins the real nflverse Week 1 2026 injury report to NWR's canonical pool
via the SAME identity resolver used everywhere else in this cycle
(`live_player_intelligence_identity_mapping_v1_service.classify_rows`) so
every benchmark row already carries its own canonical match status --
no second join is invented downstream.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.services.live_player_intelligence_identity_mapping_v1_service import (  # noqa: E402
    classify_rows,
    common_rows_from_nflverse_injuries,
    load_canonical_pool,
)

SHADOW_ROOT = REPO_ROOT / "local_exports" / "live_player_intelligence_shadow_v1"
INJURIES_LATEST = SHADOW_ROOT / "nflverse_injuries" / "latest"
INJURIES_WU1_SNAPSHOT = SHADOW_ROOT / "nflverse_injuries" / "wu1_snapshot_20260913"
OUTPUT_ROOT = REPO_ROOT / "docs" / "codex" / "live_player_intelligence_v1" / "official_truth_benchmark_v1"

_REPORT_STATUS_CATEGORY = {
    "Out": "OUT",
    "Doubtful": "DOUBTFUL",
    "Questionable": "QUESTIONABLE",
    "": "CLEARED_OR_NOT_LISTED",
}
_PRACTICE_STATUS_CATEGORY = {
    "Full Participation in Practice": "FULL",
    "Limited Participation in Practice": "LIMITED",
    "Did Not Participate In Practice": "DNP",
    "": "NONE_RECORDED",
}

BENCHMARK_FIELDS = (
    "playerId",
    "playerName",
    "position",
    "team",
    "season",
    "week",
    "reportStatusRaw",
    "reportStatusCategory",
    "practiceStatusRaw",
    "practiceStatusCategory",
    "reportPrimaryInjury",
    "reportSecondaryInjury",
    "practicePrimaryInjury",
    "practiceSecondaryInjury",
    "source",
    "sourceUrl",
    "fetchedAtUtc",
    "sourceAsOf",
    "matchedCanonicalPlayerId",
    "identityMatchMethod",
)


def main() -> None:
    with (INJURIES_LATEST / "injuries_2026.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with (INJURIES_LATEST / "manifest_2026.json").open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    canonical_rows = load_canonical_pool()
    common_rows = common_rows_from_nflverse_injuries(rows)
    identity_results = classify_rows(common_rows, canonical_rows)
    identity_by_gsis = {r.provider_id: r for r in identity_results if r.provider_id}

    benchmark_rows: list[dict[str, str]] = []
    for row in rows:
        gsis_id = str(row.get("gsis_id") or "").strip()
        identity = identity_by_gsis.get(gsis_id)
        report_status = str(row.get("report_status") or "").strip()
        practice_status = str(row.get("practice_status") or "").strip()
        benchmark_rows.append(
            {
                "playerId": gsis_id,
                "playerName": row.get("full_name", ""),
                "position": row.get("position", ""),
                "team": str(row.get("team") or "").upper(),
                "season": row.get("season", ""),
                "week": row.get("week", ""),
                "reportStatusRaw": report_status,
                "reportStatusCategory": _REPORT_STATUS_CATEGORY.get(report_status, "UNKNOWN_RAW_VALUE"),
                "practiceStatusRaw": practice_status,
                "practiceStatusCategory": _PRACTICE_STATUS_CATEGORY.get(practice_status, "UNKNOWN_RAW_VALUE"),
                "reportPrimaryInjury": row.get("report_primary_injury", ""),
                "reportSecondaryInjury": row.get("report_secondary_injury", ""),
                "practicePrimaryInjury": row.get("practice_primary_injury", ""),
                "practiceSecondaryInjury": row.get("practice_secondary_injury", ""),
                "source": "NFLVERSE_OFFICIAL_INJURY_REPORT",
                "sourceUrl": manifest["source_url"],
                "fetchedAtUtc": manifest["fetched_at_utc"],
                # Real, disclosed gap: the file carries season/week only, no
                # finer in-file publication timestamp -- see the benchmark
                # doc's Gate 5 section.
                "sourceAsOf": f"{row.get('season')}-{row.get('season_type')}-week{row.get('week')}",
                "matchedCanonicalPlayerId": identity.matched_canonical_player_id if identity else "",
                "identityMatchMethod": identity.primary_classification if identity else "UNMATCHED",
            }
        )

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    out_csv = OUTPUT_ROOT / "nflverse_week1_2026_official_truth_benchmark.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BENCHMARK_FIELDS)
        writer.writeheader()
        writer.writerows(benchmark_rows)
    print(f"Wrote {len(benchmark_rows)} benchmark rows -> {out_csv}")

    # Revision-window evidence: diff against Worker 1's earlier same-day pull.
    revision_note = {
        "priorPullManifest": None,
        "revisionDetected": None,
    }
    prior_manifest_path = INJURIES_WU1_SNAPSHOT / "manifest_2026.json"
    prior_csv_path = INJURIES_WU1_SNAPSHOT / "injuries_2026.csv"
    if prior_manifest_path.exists() and prior_csv_path.exists():
        with prior_manifest_path.open(encoding="utf-8") as handle:
            prior_manifest = json.load(handle)
        with prior_csv_path.open(newline="", encoding="utf-8") as handle:
            prior_rows = {r["gsis_id"]: r for r in csv.DictReader(handle)}
        changed = []
        for row in rows:
            gid = row["gsis_id"]
            prior = prior_rows.get(gid)
            if prior is None:
                changed.append({"gsis_id": gid, "change": "NEW_ROW"})
            elif prior["report_status"] != row["report_status"] or prior["practice_status"] != row["practice_status"]:
                changed.append(
                    {
                        "gsis_id": gid,
                        "change": "STATUS_CHANGED",
                        "before": [prior["report_status"], prior["practice_status"]],
                        "after": [row["report_status"], row["practice_status"]],
                    }
                )
        revision_note = {
            "priorPullFetchedAtUtc": prior_manifest["fetched_at_utc"],
            "currentPullFetchedAtUtc": manifest["fetched_at_utc"],
            "rowsChangedBetweenPulls": len(changed),
            "changes": changed,
        }

    manifest_out = {
        "benchmarkApproach": "nflverse official weekly injury report, real fresh pull, joined to NWR canonical pool via the existing _identity resolver",
        "notAFullyIndependentThirdPartySource": True,
        "productionAdmissionIsASeparateGate9Decision": True,
        "season": 2026,
        "week": 1,
        "rowCount": len(benchmark_rows),
        "distinctTeams": len({r["team"] for r in benchmark_rows if r["team"]}),
        "sourceUrl": manifest["source_url"],
        "fetchedAtUtc": manifest["fetched_at_utc"],
        "revisionEvidence": revision_note,
    }
    (OUTPUT_ROOT / "manifest.json").write_text(json.dumps(manifest_out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote manifest -> {OUTPUT_ROOT / 'manifest.json'}")


if __name__ == "__main__":
    main()
