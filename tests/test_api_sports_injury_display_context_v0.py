from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "api_sports_injury_display_context_v0.py"
)
SPEC = importlib.util.spec_from_file_location("api_sports_injury_display_context_v0", MODULE_PATH)
assert SPEC is not None
INJURIES = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["api_sports_injury_display_context_v0"] = INJURIES
SPEC.loader.exec_module(INJURIES)


def test_missing_env_var_fails_closed_without_printing_key(monkeypatch: Any) -> None:
    monkeypatch.delenv("NWR_API_SPORTS_KEY", raising=False)

    try:
        INJURIES.run_api_sports_injury_display_context(
            output_root=Path("unused"),
            report_root=Path("unused"),
            diagnostic_root=Path("unused"),
        )
    except INJURIES.ApiSportsInjuryError as exc:
        assert "missing" in str(exc).lower()
        assert "secret" not in str(exc).lower()
    else:
        raise AssertionError("expected missing env var failure")


def test_normalization_and_candidate_manifest_are_display_only(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setenv("NWR_API_SPORTS_KEY", "TEST_SECRET_SHOULD_NOT_LEAK")
    result = INJURIES.run_api_sports_injury_display_context(
        season=2026,
        team_ids=[1],
        output_root=tmp_path / "lane_exchange",
        report_root=tmp_path / "reports",
        diagnostic_root=tmp_path / "diagnostics",
        crosswalk_root=tmp_path / "lane_exchange",
        write_candidate=True,
        snapshot_label="candidate",
        transport=FakeTransport(),
    )

    assert len(result.rows) == 2
    assert result.calls_used == 1
    assert result.matched_count == 0
    assert result.unmatched_count == 2
    assert result.ambiguous_count == 0
    assert result.candidate_path is not None
    assert result.latest_candidate_path is not None
    assert not (result.latest_candidate_path.parent / "latest_approved.json").exists()

    manifest_path = result.candidate_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["approval_status"] == "candidate"
    assert manifest["source_name"] == "API-SPORTS"
    assert manifest["source_risk"] == "YELLOW_LICENSE_AND_CURRENT_ONLY"
    assert manifest["contains_private_value"] is False
    assert manifest["contains_market_data"] is False
    assert manifest["contains_adp"] is False
    assert manifest["contains_health_status"] is True
    assert manifest["historical_coverage"] == "current_only_from_api"
    for blocked in (
        "private_value",
        "model_training",
        "rankings",
        "recommendations",
        "simulations",
        "final_draft_decisions",
    ):
        assert blocked in manifest["blocked_use"]

    data_path = result.candidate_path / INJURIES.DATA_FILE
    with data_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["player_name"] == "Drake Maye"
    assert rows[0]["injury_status"] == "Questionable"
    assert rows[0]["practice_status"] == "Limited"
    assert rows[0]["stale_flag"] == ""
    assert rows[1]["stale_flag"] == "missing_last_update"

    report = result.report_path.read_text(encoding="utf-8")
    diagnostics = result.diagnostic_path.read_text(encoding="utf-8")
    assert "TEST_SECRET_SHOULD_NOT_LEAK" not in report
    assert "TEST_SECRET_SHOULD_NOT_LEAK" not in diagnostics
    assert "Secret leakage check: passed" in report


def test_request_budget_guard_blocks_projected_calls(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setenv("NWR_API_SPORTS_KEY", "TEST_SECRET_SHOULD_NOT_LEAK")
    try:
        INJURIES.run_api_sports_injury_display_context(
            team_ids=[1, 2, 3],
            max_calls=2,
            output_root=tmp_path / "lane_exchange",
            report_root=tmp_path / "reports",
            diagnostic_root=tmp_path / "diagnostics",
            transport=FakeTransport(),
        )
    except INJURIES.ApiSportsInjuryError as exc:
        assert "request budget" in str(exc)
    else:
        raise AssertionError("expected request budget failure")


def test_team_discovery_uses_one_call_and_then_team_injury_calls(
    monkeypatch: Any, tmp_path: Path
) -> None:
    monkeypatch.setenv("NWR_API_SPORTS_KEY", "TEST_SECRET_SHOULD_NOT_LEAK")
    transport = FakeTransport()
    result = INJURIES.run_api_sports_injury_display_context(
        season=2026,
        output_root=tmp_path / "lane_exchange",
        report_root=tmp_path / "reports",
        diagnostic_root=tmp_path / "diagnostics",
        write_candidate=False,
        snapshot_label="team_discovery",
        transport=transport,
    )

    assert result.calls_used == 3
    assert transport.calls == [
        ("teams", {"league": 1, "season": 2026}),
        ("injuries", {"team": 1, "season": 2026}),
        ("injuries", {"team": 2, "season": 2026}),
    ]
    assert result.candidate_path is None


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((path, params))
        if path == "teams":
            return {
                "response": [
                    {"team": {"id": 1, "name": "Patriots"}},
                    {"team": {"id": 2, "name": "Steelers"}},
                ]
            }
        if params.get("team") == 2:
            return {"response": []}
        return {
            "response": [
                {
                    "team": {"id": 1, "name": "Patriots"},
                    "player": {"id": 101, "name": "Drake Maye", "position": "QB"},
                    "injury": {
                        "status": "Questionable",
                        "practice": "Limited",
                        "type": "Knee",
                        "comment": "Practice limited",
                    },
                    "game": {"week": "1", "date": "2026-09-10"},
                    "last_update": "2026-09-08T12:00:00Z",
                },
                {
                    "team": {"id": 1, "name": "Patriots"},
                    "player": {"id": 102, "name": "Test Player", "position": "WR"},
                    "injury": {"status": "Out", "type": "Hamstring"},
                    "game": {"week": "1"},
                },
            ]
        }
