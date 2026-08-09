from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.build_redraft_2026_projection_admission_packet import settings_sanity
from src.services.redraft_engine_v1_service import (
    build_health_report,
    builtin_presets,
    generate_rankings,
    load_projection_snapshot,
    player_compare_rows,
    projection_snapshot_path,
)


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.4f")


def _ranking_frame(result: Any) -> pd.DataFrame:
    frame = pd.DataFrame(asdict(row) for row in result.rows)
    frame.insert(0, "admission_status", "ADMITTED_PRODUCTION")
    return frame


def _sanity(results: dict[str, Any]) -> pd.DataFrame:
    default = _ranking_frame(results["12_TEAM_1QB_HALF_PPR"])
    superflex = _ranking_frame(results["12_TEAM_SUPERFLEX_PPR"])
    return pd.DataFrame(
        [
            [
                "Default top 100 duplicate IDs",
                int(default.head(100)["player_id"].duplicated().sum()),
                "PASS",
            ],
            [
                "Superflex top 100 duplicate IDs",
                int(superflex.head(100)["player_id"].duplicated().sum()),
                "PASS",
            ],
            [
                "Default top 100 zero projections",
                int(default.head(100)["projected_points"].le(0).sum()),
                "PASS",
            ],
            [
                "Superflex top 100 zero projections",
                int(superflex.head(100)["projected_points"].le(0).sum()),
                "PASS",
            ],
            [
                "Default top 100 rookie rows",
                int(default.head(100)["rookie"].sum()),
                "PASS_FAIL_CLOSED",
            ],
            [
                "Default top 100 K/DST rows",
                int(default.head(100)["position"].isin(["K", "DST"]).sum()),
                "PASS",
            ],
            [
                "Default top 25 QB count",
                int(default.head(25)["position"].eq("QB").sum()),
                "REVIEW_OBSERVATION",
            ],
            [
                "Superflex top 25 QB count",
                int(superflex.head(25)["position"].eq("QB").sum()),
                "REVIEW_OBSERVATION",
            ],
        ],
        columns=["check", "observed", "status"],
    )


def validate(store: Path, packet: Path) -> dict[str, Any]:
    installed_path = projection_snapshot_path(store, 2026)
    snapshot = load_projection_snapshot(installed_path, season=2026, require_manifest=True)
    if snapshot.errors:
        raise ValueError("Installed snapshot is invalid: " + "; ".join(snapshot.errors))
    results = {
        str(profile.preset_key): generate_rankings(profile, snapshot)
        for profile in builtin_presets()
    }
    failed = {key: result.errors for key, result in results.items() if not result.ready}
    if failed:
        raise ValueError(f"Production ranking generation failed: {failed}")
    filenames = {
        "10_TEAM_1QB_STANDARD": "PROFILE_RANKINGS_10_TEAM_1QB_STANDARD.csv",
        "12_TEAM_1QB_HALF_PPR": "DEFAULT_PROFILE_RANKINGS.csv",
        "12_TEAM_PPR": "PROFILE_RANKINGS_12_TEAM_PPR.csv",
        "12_TEAM_SUPERFLEX_PPR": "SUPERFLEX_PROFILE_RANKINGS.csv",
    }
    for key, filename in filenames.items():
        _write_csv(packet / filename, _ranking_frame(results[key]))
    settings = settings_sanity(results, snapshot)
    if not settings["status"].eq("PASS").all():
        raise ValueError("One or more installed settings sensitivity checks failed.")
    _write_csv(packet / "SETTINGS_SANITY_RESULTS.csv", settings)
    ranking_sanity = _sanity(results)
    _write_csv(packet / "CURRENT_RANKING_SANITY.csv", ranking_sanity)
    half_ppr = results["12_TEAM_1QB_HALF_PPR"]
    sample = [
        {
            "player_id": half_ppr.rows[0].player_id,
            "player": half_ppr.rows[0].player_name,
            "position": half_ppr.rows[0].position,
        },
        {"player_id": "rookie-blocked", "player": "Blocked Rookie", "position": "WR"},
    ]
    compare = player_compare_rows(half_ppr, sample)
    if compare[0].get("Redraft Status") != "REDRAFT V1 - REVIEW":
        raise ValueError("Admitted veteran did not resolve in Player Compare.")
    if compare[1].get("Redraft Status") != "NOT_ENOUGH_INFORMATION":
        raise ValueError("Unadmitted rookie did not remain blocked in Player Compare.")
    health = build_health_report(half_ppr.profile, snapshot, half_ppr)
    summary = {
        "schema_version": 1,
        "status": "ADMITTED_PRODUCTION_VALIDATED",
        "projection_sha256": snapshot.source_sha256,
        "admitted_players": len(snapshot.players),
        "blocked_snapshot_rows": len(snapshot.blocked_rows),
        "profile_rows": {key: len(result.rows) for key, result in results.items()},
        "all_profiles_ready": all(result.ready for result in results.values()),
        "settings_checks_passed": int(settings["status"].eq("PASS").sum()),
        "settings_checks_total": len(settings),
        "player_compare_admitted_veteran": compare[0],
        "player_compare_blocked_rookie": compare[1],
        "health": asdict(health),
        "top_25_default": [asdict(row) for row in half_ppr.rows[:25]],
        "top_25_superflex": [asdict(row) for row in results["12_TEAM_SUPERFLEX_PPR"].rows[:25]],
    }
    (packet / "ADMITTED_RANKING_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, default=Path("local_exports/redraft_v1"))
    parser.add_argument(
        "--packet",
        type=Path,
        default=Path("docs/hq/model/nwr_redraft_2026_projection_admission_v1_20260808"),
    )
    args = parser.parse_args()
    summary = validate(args.store.resolve(), args.packet.resolve())
    print(
        json.dumps(
            {
                "status": summary["status"],
                "projection_sha256": summary["projection_sha256"],
                "admitted_players": summary["admitted_players"],
                "profile_rows": summary["profile_rows"],
                "settings_checks": (
                    f"{summary['settings_checks_passed']}/{summary['settings_checks_total']}"
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
