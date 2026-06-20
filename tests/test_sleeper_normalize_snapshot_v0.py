from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sleeper_normalize_snapshot_v0.py"
SPEC = importlib.util.spec_from_file_location("sleeper_normalize_snapshot_v0", MODULE_PATH)
assert SPEC is not None
NORMALIZER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["sleeper_normalize_snapshot_v0"] = NORMALIZER
SPEC.loader.exec_module(NORMALIZER)


def test_dry_run_reconstructs_pre_draft_pick_order_without_candidates(tmp_path: Path) -> None:
    snapshot = _write_snapshot(tmp_path / "snapshot")
    output_root = tmp_path / "lane_exchange"

    result = NORMALIZER.normalize_snapshot(
        snapshot_dir=snapshot,
        output_root=output_root,
        write_candidates=False,
        snapshot_label="test_candidate",
    )

    counts = {package.package_name: len(package.rows) for package in result.packages}
    assert counts["sleeper_state/draft_pick_ownership_snapshot"] == 50
    assert counts["league_state/pick_order"] == 50
    assert counts["league_state/nwr_picks"] == 5
    assert counts["sleeper_state/traded_picks_snapshot"] == 1
    assert counts["sleeper_state/transactions_snapshot"] == 1
    assert result.report_path.exists()
    assert not output_root.exists()

    pick_order = _package(result, "league_state/pick_order").rows
    assert len({row["overall_pick"] for row in pick_order}) == 50
    assert pick_order[2]["pick_label"] == "1.03"
    assert pick_order[2]["current_owner"] == "Team 3"
    assert pick_order[5]["pick_label"] == "1.06"
    assert pick_order[5]["current_owner"] == "Dirt Devils"
    assert pick_order[6]["pick_label"] == "1.07"
    assert pick_order[6]["current_owner"] == "Niners"


def test_duplicate_pick_detection_fails_closed(tmp_path: Path) -> None:
    snapshot = _write_snapshot(tmp_path / "snapshot", duplicate_slot=True)

    try:
        NORMALIZER.normalize_snapshot(
            snapshot_dir=snapshot,
            output_root=tmp_path / "lane_exchange",
            write_candidates=False,
            snapshot_label="bad_candidate",
        )
    except NORMALIZER.NormalizationError as exc:
        assert "duplicate draft slot" in str(exc)
    else:
        raise AssertionError("expected duplicate draft slot failure")


def test_write_candidates_creates_latest_candidate_only(tmp_path: Path) -> None:
    snapshot = _write_snapshot(tmp_path / "snapshot")
    output_root = tmp_path / "lane_exchange"

    result = NORMALIZER.normalize_snapshot(
        snapshot_dir=snapshot,
        output_root=output_root,
        write_candidates=True,
        snapshot_label="test_candidate",
    )

    assert result.wrote_candidates is True
    assert set(result.candidate_paths) == set(NORMALIZER.PACKAGE_NAMES)
    for package_name in NORMALIZER.PACKAGE_NAMES:
        source_lane, short_name = package_name.split("/", 1)
        package_root = output_root / source_lane / short_name
        pointer_path = package_root / "latest_candidate.json"
        approved_path = package_root / "latest_approved.json"
        snapshot_path = package_root / "test_candidate"
        manifest_path = snapshot_path / "manifest.json"

        assert pointer_path.exists()
        assert manifest_path.exists()
        assert not approved_path.exists()

        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert pointer["approval_status"] == "candidate"
        assert manifest["approval_status"] == "candidate"
        assert manifest["not_latest_approved"] is True
        assert pointer["manifest_path"] == str(manifest_path)


def test_nwr_picks_can_use_explicit_roster_id(tmp_path: Path) -> None:
    snapshot = _write_snapshot(tmp_path / "snapshot", nwr_team_name="Tim Team")

    result = NORMALIZER.normalize_snapshot(
        snapshot_dir=snapshot,
        output_root=tmp_path / "lane_exchange",
        write_candidates=False,
        snapshot_label="test_candidate",
        nwr_roster_id=7,
    )

    nwr_rows = _package(result, "league_state/nwr_picks").rows
    assert [row["overall_pick"] for row in nwr_rows] == [7, 17, 27, 37, 47]


def _package(result: Any, package_name: str) -> Any:
    return next(package for package in result.packages if package.package_name == package_name)


def _write_snapshot(
    snapshot_dir: Path,
    *,
    duplicate_slot: bool = False,
    nwr_team_name: str = "Niners",
) -> Path:
    snapshot_dir.mkdir(parents=True)
    users = [
        _user(
            index,
            team_name=(
                "Dirt Devils"
                if index == 1
                else nwr_team_name
                if index == 7
                else f"Team {index}"
            ),
        )
        for index in range(1, 11)
    ]
    rosters = [_roster(index) for index in range(1, 11)]
    draft_order = {f"u{index}": index for index in range(1, 11)}
    if duplicate_slot:
        draft_order["u10"] = 9
    draft = {
        "draft_id": "draft_1",
        "season": "2026",
        "status": "pre_draft",
        "type": "linear",
        "draft_order": draft_order,
        "settings": {"rounds": 5, "teams": 10},
    }
    traded_picks = [
        {"season": "2026", "round": 1, "roster_id": 6, "owner_id": 1},
    ]
    transactions = [
        {
            "transaction_id": "tx1",
            "type": "free_agent",
            "status": "complete",
            "roster_ids": [7],
            "adds": {"p100": 7},
            "drops": {"p099": 7},
        }
    ]
    metadata = {
        "snapshot_label": "raw_snapshot",
        "created_at": "2026-06-20T20:01:11+00:00",
        "league_id": "league_1",
        "draft_id": "draft_1",
        "season": "2026",
        "warnings": [],
        "endpoints": [
            {
                "name": "draft_picks",
                "warning": "Draft picks endpoint returned zero rows; this is expected.",
                "error": "",
            }
        ],
    }
    _write_json(snapshot_dir / "league.json", {"league_id": "league_1", "season": "2026"})
    _write_json(snapshot_dir / "users.json", users)
    _write_json(snapshot_dir / "rosters.json", rosters)
    _write_json(snapshot_dir / "drafts.json", [draft])
    _write_json(snapshot_dir / "traded_picks.json", traded_picks)
    _write_json(snapshot_dir / "draft_details.json", draft)
    _write_json(snapshot_dir / "draft_picks.json", [])
    _write_json(snapshot_dir / "transactions_round_1.json", transactions)
    _write_json(snapshot_dir / "snapshot_metadata.json", metadata)
    return snapshot_dir


def _user(index: int, team_name: str) -> dict[str, Any]:
    return {
        "user_id": f"u{index}",
        "display_name": team_name,
        "metadata": {"team_name": team_name},
    }


def _roster(index: int) -> dict[str, Any]:
    return {
        "roster_id": index,
        "owner_id": f"u{index}",
        "players": [f"p{index}_a", f"p{index}_b"],
        "starters": [f"p{index}_a"],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
