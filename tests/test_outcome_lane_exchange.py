# ruff: noqa: E402,I001

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.services.outcome_lane_exchange import (
    OUTCOME_PACKAGE_NAME,
    LaneExchangeError,
    outcome_exchange_role,
    publish_outcome_candidate_snapshot,
    readiness_summary,
    sha256_file,
    validate_latest_approved_snapshot,
)


class OutcomeLaneExchangeTests(unittest.TestCase):
    def test_registry_reports_outcome_role_and_blocks_current_publish_gate(self) -> None:
        registry = _registry(outcome_publish_allowed=False)

        role = outcome_exchange_role(registry)

        self.assertEqual(role.lane_id, "outcome_v1")
        self.assertEqual(role.owned_packages, (OUTCOME_PACKAGE_NAME,))
        self.assertEqual(role.consumed_packages, ())
        self.assertFalse(role.publish_allowed)
        self.assertTrue(role.requires_explicit_approval_later)

    def test_validate_latest_approved_pointer_checks_hash_rows_and_allowed_use(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_path = _write_csv(
                root / "rookie_hq/frozen_rookie_mock_input/20260620_approved/rookies.csv",
                (("player_id", "player"), ("p1", "One"), ("p2", "Two")),
            )
            manifest_path = data_path.parent / "manifest.json"
            _write_json(
                manifest_path,
                _manifest(
                    package_name="rookie_hq/frozen_rookie_mock_input",
                    data_file=data_path.name,
                    row_count=2,
                    sha256=sha256_file(data_path),
                    allowed_use=["mock_draft_read_only_validation"],
                ),
            )
            _write_json(
                root / "rookie_hq/frozen_rookie_mock_input/latest_approved.json",
                {
                    "manifest_path": (
                        "rookie_hq/frozen_rookie_mock_input/"
                        "20260620_approved/manifest.json"
                    )
                },
            )

            result = validate_latest_approved_snapshot(
                "rookie_hq/frozen_rookie_mock_input",
                hub_root=root,
                required_use="mock_draft_read_only_validation",
            )

        self.assertEqual(result.package_name, "rookie_hq/frozen_rookie_mock_input")
        self.assertEqual(result.row_count, 2)
        self.assertEqual(result.approval_status, "approved")

    def test_validate_latest_approved_fails_closed_for_candidate_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_path = _write_csv(
                root / "league_state/pick_order/20260620_candidate/picks.csv",
                (("pick", "team"), ("1", "Niners")),
            )
            manifest_path = data_path.parent / "manifest.json"
            manifest = _manifest(
                package_name="league_state/pick_order",
                data_file=data_path.name,
                row_count=1,
                sha256=sha256_file(data_path),
                allowed_use=["draft_day_manual_review"],
            )
            manifest["approval_status"] = "candidate"
            _write_json(manifest_path, manifest)
            _write_json(
                root / "league_state/pick_order/latest_approved.json",
                {"manifest_path": "league_state/pick_order/20260620_candidate/manifest.json"},
            )

            with self.assertRaisesRegex(LaneExchangeError, "not approved"):
                validate_latest_approved_snapshot("league_state/pick_order", hub_root=root)

    def test_validate_latest_approved_fails_closed_for_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_path = _write_csv(
                root / "model_value/veteran_private_values/20260620_approved/values.csv",
                (("player_id", "value"), ("p1", "10")),
            )
            _write_json(
                data_path.parent / "manifest.json",
                _manifest(
                    package_name="model_value/veteran_private_values",
                    data_file=data_path.name,
                    row_count=1,
                    sha256="0" * 64,
                    allowed_use=["draft_day_manual_review"],
                ),
            )
            _write_json(
                root / "model_value/veteran_private_values/latest_approved.json",
                {"snapshot_path": "model_value/veteran_private_values/20260620_approved"},
            )

            with self.assertRaisesRegex(LaneExchangeError, "SHA256 mismatch"):
                validate_latest_approved_snapshot(
                    "model_value/veteran_private_values",
                    hub_root=root,
                )

    def test_publish_candidate_requires_explicit_registry_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            registry_path = root / "registry.json"
            _write_json(registry_path, _registry(outcome_publish_allowed=False))
            source_data = _write_csv(
                root / "candidate.csv",
                (("player_id", "QB T12"), ("p1", "11%")),
            )

            with self.assertRaisesRegex(LaneExchangeError, "does not explicitly allow"):
                publish_outcome_candidate_snapshot(
                    source_data,
                    registry_path=registry_path,
                    hub_root=root / "hub",
                )

    def test_publish_candidate_writes_only_outcome_candidate_when_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            registry_path = root / "registry.json"
            _write_json(registry_path, _registry(outcome_publish_allowed=True))
            source_data = _write_csv(
                root / "candidate.csv",
                (("player_id", "QB T12"), ("p1", "11%"), ("p2", "")),
            )

            published = publish_outcome_candidate_snapshot(
                source_data,
                registry_path=registry_path,
                hub_root=root / "hub",
                snapshot_label="test_candidate",
                source_repo="C:\\NWR\\Niners-War-Room-outcome",
                source_branch="main",
                source_head="6e47932",
            )

            manifest = _read_json(published.manifest_path)
            self.assertEqual(published.package_name, OUTCOME_PACKAGE_NAME)
            self.assertEqual(manifest["approval_status"], "candidate")
            self.assertEqual(manifest["row_count"], 2)
            self.assertEqual(manifest["sha256"], sha256_file(published.data_path))
            self.assertTrue(published.latest_candidate_path.exists())
            latest_approved = published.latest_candidate_path.parent / "latest_approved.json"
            self.assertFalse(latest_approved.exists())

    def test_readiness_summary_does_not_validate_packages_unless_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            registry_path = root / "registry.json"
            _write_json(registry_path, _registry(outcome_publish_allowed=False))

            summary = readiness_summary(registry_path=registry_path, hub_root=root / "hub")

        self.assertEqual(summary["owned_packages"], [OUTCOME_PACKAGE_NAME])
        self.assertEqual(summary["consumed_packages"], [])
        self.assertEqual(summary["validated_latest_approved"], [])


def _registry(*, outcome_publish_allowed: bool) -> dict[str, object]:
    outcome_entry: dict[str, object] = {
        "source_lane": "outcome_v1",
        "owns_packages": ["outcome_display_snapshot"],
        "requires_explicit_approval_later": not outcome_publish_allowed,
        "notes": "May publish only if explicitly approved later.",
    }
    if outcome_publish_allowed:
        outcome_entry["candidate_publish_allowed"] = True
    return {
        "contract_version": "lane_exchange_v0",
        "contract_owner": "Master/Main HQ",
        "hub_root": "C:\\NWR_SHARED_DATA\\lane_exchange",
        "local_only": True,
        "git_commit_allowed": False,
        "lane_ownership": [outcome_entry],
    }


def _manifest(
    *,
    package_name: str,
    data_file: str,
    row_count: int,
    sha256: str,
    allowed_use: list[str],
) -> dict[str, object]:
    return {
        "source_lane": package_name.split("/", 1)[0],
        "source_repo": "C:\\NWR\\fake",
        "source_branch": "main",
        "source_head": "abc123",
        "package_name": package_name,
        "schema_version": "test_schema_v1",
        "data_file": data_file,
        "row_count": row_count,
        "sha256": sha256,
        "created_at": "2026-06-20T00:00:00-06:00",
        "approval_status": "approved",
        "approved_for": allowed_use,
        "allowed_use": allowed_use,
        "forbidden_use": ["private_value_from_market"],
        "contains_private_value": False,
        "contains_market_data": False,
        "contains_adp": False,
        "notes": "Fake test manifest.",
    }


def _write_csv(path: Path, rows: tuple[tuple[str, ...], ...]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)
    return path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _read_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    unittest.main()
