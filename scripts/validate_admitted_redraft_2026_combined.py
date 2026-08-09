from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_redraft_2026_projection_admission_packet import settings_sanity  # noqa: E402
from scripts.finalize_redraft_2026_rookie_owner_approval import _write_manifest  # noqa: E402
from src.services.redraft_engine_v1_service import (  # noqa: E402
    builtin_presets,
    generate_rankings,
    load_projection_snapshot,
    player_compare_rows,
    projection_snapshot_path,
)

EXPECTED_GOVERNED_COMBINED_SHA = (
    "e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25"
)
EXPECTED_VETERAN_SHA = "6ee6dbff41e238fb925c8d8d4b5e5079f48de71b132888e5c75fea34e9831c63"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.4f")


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _ranking_frame(result: Any) -> pd.DataFrame:
    frame = pd.DataFrame(asdict(row) for row in result.rows)
    frame.insert(0, "admission_status", "ADMITTED_PRODUCTION")
    return frame


def validate(store: Path, packet: Path, veteran_path: Path) -> dict[str, Any]:
    installed_path = projection_snapshot_path(store, 2026)
    snapshot = load_projection_snapshot(installed_path, season=2026, require_manifest=True)
    if snapshot.errors:
        raise ValueError("Installed combined snapshot is invalid: " + "; ".join(snapshot.errors))
    if snapshot.source_sha256 != EXPECTED_GOVERNED_COMBINED_SHA:
        raise ValueError("Installed combined snapshot SHA differs from governed finalization.")
    if len(snapshot.players) != 608 or snapshot.blocked_rows:
        raise ValueError("Installed combined snapshot is not 608 admitted rows with zero blocks.")
    installed = pd.read_csv(installed_path)
    veterans = pd.read_csv(veteran_path)
    if _sha256(veteran_path) != EXPECTED_VETERAN_SHA:
        raise ValueError("Approved veteran source SHA changed before combined validation.")
    assert_frame_equal(
        installed.iloc[:530].reset_index(drop=True),
        veterans.reset_index(drop=True),
        check_dtype=False,
        check_exact=True,
    )
    if not installed_path.read_bytes().startswith(veteran_path.read_bytes()):
        raise ValueError("Installed combined bytes do not preserve the veteran CSV prefix.")
    rookie = installed.iloc[530:].copy()
    if len(rookie) != 78 or not rookie["rookie"].eq(True).all():
        raise ValueError("Installed rookie suffix is not the governed 78-row layer.")
    if not installed["source_status"].eq("GOVERNED").all():
        raise ValueError("One or more installed rows are not governed.")
    if not installed["evidence_status"].eq("ADMITTED_CURRENT_SEASON").all():
        raise ValueError("One or more installed rows are not admitted current-season evidence.")
    if installed["position"].isin(["K", "DST"]).any():
        raise ValueError("Installed combined snapshot unexpectedly contains K/DST.")

    results = {
        profile.preset_key: generate_rankings(profile, snapshot)
        for profile in builtin_presets()
    }
    failed = {key: result.errors for key, result in results.items() if not result.ready}
    if failed:
        raise ValueError(f"Combined production ranking generation failed: {failed}")
    filenames = {
        "10_TEAM_1QB_STANDARD": "GOVERNED_PROFILE_RANKINGS_10_TEAM_1QB_STANDARD.csv",
        "12_TEAM_1QB_HALF_PPR": "GOVERNED_PROFILE_RANKINGS_12_TEAM_1QB_HALF_PPR.csv",
        "12_TEAM_PPR": "GOVERNED_PROFILE_RANKINGS_12_TEAM_PPR.csv",
        "12_TEAM_SUPERFLEX_PPR": "GOVERNED_PROFILE_RANKINGS_12_TEAM_SUPERFLEX_PPR.csv",
    }
    ranking_hashes: dict[str, str] = {}
    for key, filename in filenames.items():
        frame = _ranking_frame(results[key])
        if len(frame) != 608 or int(frame["rookie"].sum()) != 78:
            raise ValueError(f"{key} did not rank all 608 rows and 78 rookies.")
        if frame["player_id"].duplicated().any() or frame["position"].isin(["K", "DST"]).any():
            raise ValueError(f"{key} contains duplicate IDs or K/DST.")
        path = packet / filename
        _write_csv(path, frame)
        ranking_hashes[key] = _sha256(path)
    sensitivity = settings_sanity(results, snapshot)
    if not sensitivity["status"].eq("PASS").all():
        raise ValueError("One or more governed combined sensitivity checks failed.")
    _write_csv(packet / "GOVERNED_PROFILE_SENSITIVITY_RESULTS.csv", sensitivity)

    half_ppr = results["12_TEAM_1QB_HALF_PPR"]
    compare = player_compare_rows(
        half_ppr,
        [
            {"player_id": "MEN516487", "player": "Fernando Mendoza", "position": "QB"},
            {"player_id": "00-0041081", "player": "Max Bredeson", "position": "RB"},
        ],
    )
    if compare[0].get("Redraft Status") != "REDRAFT V1 - REVIEW":
        raise ValueError("Governed rookie did not resolve in Player Compare.")
    if compare[1].get("Redraft Status") != "NOT_ENOUGH_INFORMATION":
        raise ValueError("Blocked position-conflict rookie did not remain fail-closed.")

    receipt = {
        "schema_version": 1,
        "status": "ADMITTED_COMBINED_PRODUCTION_VALIDATED",
        "projection_sha256": snapshot.source_sha256,
        "approved_veteran_sha256": EXPECTED_VETERAN_SHA,
        "veteran_rows": 530,
        "rookie_rows": 78,
        "combined_rows": 608,
        "blocked_snapshot_rows": 0,
        "k_dst_rows": 0,
        "all_profiles_ready": True,
        "profile_rows": {key: len(result.rows) for key, result in results.items()},
        "ranking_sha256": ranking_hashes,
        "settings_checks_passed": int(sensitivity["status"].eq("PASS").sum()),
        "settings_checks_total": len(sensitivity),
        "veteran_values_exact": True,
        "veteran_bytes_preserved_as_installed_prefix": True,
        "player_compare_governed_rookie": compare[0],
        "player_compare_blocked_position_conflict": compare[1],
    }
    _write_json(packet / "ADMITTED_COMBINED_VALIDATION_RECEIPT.json", receipt)
    _write_manifest(packet)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, default=Path("local_exports/redraft_v1"))
    parser.add_argument(
        "--packet",
        type=Path,
        default=Path(
            "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
        ),
    )
    parser.add_argument(
        "--veteran-path",
        type=Path,
        default=Path(
            "docs/hq/model/nwr_redraft_2026_projection_admission_v1_20260808/"
            "GOVERNED_PROJECTION_SNAPSHOT.csv"
        ),
    )
    args = parser.parse_args()
    print(
        json.dumps(
            validate(args.store.resolve(), args.packet.resolve(), args.veteran_path.resolve()),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
