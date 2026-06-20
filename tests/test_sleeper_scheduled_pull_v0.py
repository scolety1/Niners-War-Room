from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sleeper_scheduled_pull_v0.py"
SPEC = importlib.util.spec_from_file_location("sleeper_scheduled_pull_v0", MODULE_PATH)
assert SPEC is not None
PULLER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["sleeper_scheduled_pull_v0"] = PULLER
SPEC.loader.exec_module(PULLER)


def test_sleeper_pull_writes_raw_snapshot_and_redacted_report(tmp_path: Path) -> None:
    result = PULLER.run_sleeper_pull(
        league_id="league_1",
        draft_id="draft_1",
        season="2026",
        league_name="Test League",
        output_root=tmp_path,
        transaction_rounds=[],
        snapshot_label="20260620_120000",
        client=FakeSleeperClient(),
    )

    assert result.snapshot_dir == tmp_path / "20260620_120000"
    assert result.report_path.exists()
    assert result.metadata_path.exists()
    assert (result.snapshot_dir / "league.json").exists()
    assert (result.snapshot_dir / "users.json").exists()
    assert (result.snapshot_dir / "draft_picks.json").exists()

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["creates_lane_exchange_packages"] is False
    assert metadata["updates_latest_candidate"] is False
    assert metadata["updates_latest_approved"] is False
    assert metadata["league_id"] == "league_1"
    assert metadata["draft_id"] == "draft_1"
    assert "transactions skipped" in "\n".join(metadata["warnings"])

    endpoints = {row["name"]: row for row in metadata["endpoints"]}
    assert endpoints["league"]["status"] == "ok"
    assert endpoints["league"]["row_count"] == len(_fake_payload()["league/league_1"])
    assert endpoints["users"]["row_count"] == 2
    assert endpoints["draft_picks"]["row_count"] == 0
    assert "pre-draft" in endpoints["draft_picks"]["warning"]

    league_body = (result.snapshot_dir / "league.json").read_bytes()
    assert endpoints["league"]["sha256"] == hashlib.sha256(league_body).hexdigest()
    report = result.report_path.read_text(encoding="utf-8")
    assert "No Lane Exchange packages were created" in report
    assert "final draft-day use" in report


def test_sleeper_pull_fetches_requested_transaction_rounds(tmp_path: Path) -> None:
    result = PULLER.run_sleeper_pull(
        league_id="league_1",
        draft_id="draft_1",
        season="2026",
        league_name="Test League",
        output_root=tmp_path,
        transaction_rounds=[1],
        snapshot_label="20260620_120000",
        client=FakeSleeperClient(),
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    endpoints = {row["name"]: row for row in metadata["endpoints"]}
    assert endpoints["transactions_round_1"]["status"] == "ok"
    assert endpoints["transactions_round_1"]["row_count"] == 1
    assert (result.snapshot_dir / "transactions_round_1.json").exists()
    assert not any("transactions skipped" in warning for warning in metadata["warnings"])


def test_optional_transaction_failure_is_warning(tmp_path: Path) -> None:
    result = PULLER.run_sleeper_pull(
        league_id="league_1",
        draft_id="draft_1",
        season="2026",
        league_name="Test League",
        output_root=tmp_path,
        transaction_rounds=[1],
        snapshot_label="20260620_120000",
        client=MissingTransactionClient(),
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    endpoints = {row["name"]: row for row in metadata["endpoints"]}
    assert endpoints["transactions_round_1"]["status"] == "warning"
    assert endpoints["transactions_round_1"]["row_count"] == 0
    assert endpoints["transactions_round_1"]["error"]
    assert (result.snapshot_dir / "transactions_round_1.json").read_text(encoding="utf-8") == ""


def test_parse_transaction_rounds_requires_positive_integers() -> None:
    assert PULLER.parse_transaction_rounds("") == []
    assert PULLER.parse_transaction_rounds("1, 3") == [1, 3]

    try:
        PULLER.parse_transaction_rounds("0")
    except ValueError as exc:
        assert "positive" in str(exc)
    else:
        raise AssertionError("expected ValueError")


class FakeSleeperClient:
    def get_json(self, path: str) -> Any:
        return _fake_payload()[path]


class MissingTransactionClient(FakeSleeperClient):
    def get_json(self, path: str) -> Any:
        if path.startswith("league/league_1/transactions/"):
            raise OSError("optional transaction endpoint failed")
        return super().get_json(path)


def _fake_payload() -> dict[str, Any]:
    league = {
        "league_id": "league_1",
        "name": "Test League",
        "season": "2026",
        "status": "pre_draft",
    }
    users = [
        {"user_id": "u1", "display_name": "Alpha"},
        {"user_id": "u2", "display_name": "Beta"},
    ]
    rosters = [
        {"roster_id": 1, "owner_id": "u1", "players": ["p1"]},
        {"roster_id": 2, "owner_id": "u2", "players": ["p2"]},
    ]
    draft = {
        "draft_id": "draft_1",
        "season": "2026",
        "status": "pre_draft",
        "draft_order": {"u1": 1, "u2": 2},
        "settings": {"rounds": 5, "teams": 2},
    }
    return {
        "league/league_1": league,
        "league/league_1/users": users,
        "league/league_1/rosters": rosters,
        "league/league_1/drafts": [draft],
        "league/league_1/traded_picks": [
            {"season": "2026", "round": 1, "roster_id": 1, "owner_id": 2}
        ],
        "draft/draft_1": draft,
        "draft/draft_1/picks": [],
        "league/league_1/transactions/1": [{"transaction_id": "tx1", "type": "free_agent"}],
    }
