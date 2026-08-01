from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import src.services.personal_workspace_service as pws
from src.services.personal_workspace_service import (
    WorkspaceBackupResult,
    WorkspaceValidationError,
    create_decision,
    create_workspace_backup,
    delete_decision,
    import_personal_board,
    load_store,
    migrate_workspace,
    restore_workspace,
    save_personal_entry,
    save_scenario,
    scenario_source_status,
    update_decision,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = {
    "current:p1": "Current Player",
    "rookie:r1": "Rookie Review",
    "blocked-rookie:b1": "Blocked Rookie",
    "pick:2026:1.01": "Draft Pick",
}


def _personal(asset_id: str = "current:p1", asset_type: str = "Current Player") -> dict:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "source_authority_version": "fixture",
        "my_tier": "A",
        "my_rank": 1,
        "team_window": "Balanced",
    }


def _decision(decision_id: str = "d1") -> dict:
    return {
        "decision_id": decision_id,
        "decision_type": "trade considered",
        "status": "Considered",
        "assets": ["current:p1"],
        "source_snapshot": {"current:p1": {"asset_type": "Current Player", "source_version": "v1"}},
        "rationale": "manual",
    }


def _scenario(payload: dict | None = None) -> dict:
    return {
        "scenario_id": "s1",
        "scenario_type": "trading_lab",
        "title": "manual",
        "assets": ["current:p1"],
        "source_versions": {"Finished V1": "v1"},
        "payload": payload or {"notes": "manual"},
    }


def test_mutation_01_personal_rank_cannot_become_finished_v1_rank(tmp_path: Path) -> None:
    row = _personal()
    row["nwr_rank"] = 99
    with pytest.raises(WorkspaceValidationError, match="Canonical source"):
        save_personal_entry(row, asset_registry=REGISTRY, root=tmp_path)


def test_mutation_02_personal_tier_cannot_write_rookie_source(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceValidationError, match="protected source"):
        save_personal_entry(
            _personal("rookie:r1", "Rookie Review"),
            asset_registry=REGISTRY,
            root=tmp_path / "docs" / "rookie-review",
        )


def test_mutation_03_old_receipt_snapshot_cannot_be_rewritten(tmp_path: Path) -> None:
    create_decision(_decision(), asset_registry=REGISTRY, root=tmp_path)
    with pytest.raises(WorkspaceValidationError, match="immutable"):
        update_decision("d1", {"source_snapshot": {}}, root=tmp_path)


def test_mutation_04_name_join_is_not_an_asset_identity(tmp_path: Path) -> None:
    row = _personal("Player One")
    raw = json.dumps({"schema_version": 1, "store": "personal_board", "records": [row]})
    with pytest.raises(WorkspaceValidationError, match="Unknown asset"):
        import_personal_board(raw, asset_registry=REGISTRY, confirmed=True, root=tmp_path)


def test_mutation_05_unknown_asset_cannot_be_converted(tmp_path: Path) -> None:
    row = _personal("unknown")
    row["extensions"] = {"display_name": "Player One", "convert_to": "current:p1"}
    with pytest.raises(WorkspaceValidationError, match="Unknown asset"):
        save_personal_entry(row, asset_registry=REGISTRY, root=tmp_path)


def test_mutation_06_player_and_pick_source_types_cannot_be_swapped(tmp_path: Path) -> None:
    value = _decision()
    value["assets"] = ["current:p1", "pick:2026:1.01"]
    value["source_snapshot"] = {
        "current:p1": {"asset_type": "Draft Pick"},
        "pick:2026:1.01": {"asset_type": "Current Player"},
    }
    with pytest.raises(WorkspaceValidationError, match="type mismatch"):
        create_decision(value, asset_registry=REGISTRY, root=tmp_path)


def test_mutation_07_blocked_rookie_cannot_receive_source_rank(tmp_path: Path) -> None:
    value = _personal("blocked-rookie:b1", "Blocked Rookie")
    value["source_rank"] = 1
    with pytest.raises(WorkspaceValidationError, match="Canonical source"):
        save_personal_entry(value, asset_registry=REGISTRY, root=tmp_path)


def test_mutation_08_page_open_cannot_write_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    monkeypatch.setenv("NWR_PERSONAL_WORKSPACE_ROOT", str(workspace))
    at = AppTest.from_file(str(ROOT / "app/pages/51_saved_scenarios_v1.py")).run(timeout=40)
    assert not at.exception
    assert not workspace.exists()


def test_mutation_09_partial_json_store_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "stores/personal_board.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"schema_version":1', encoding="utf-8")
    assert load_store("personal_board", root=tmp_path).status == "CORRUPT"


def test_mutation_10_corrupted_checksum_is_not_accepted(tmp_path: Path) -> None:
    save_personal_entry(_personal(), asset_registry=REGISTRY, root=tmp_path)
    path = tmp_path / "stores/personal_board.json"
    path.write_text(path.read_text(encoding="utf-8").replace('"my_rank":1', '"my_rank":2'))
    assert load_store("personal_board", root=tmp_path).status == "CORRUPT"


def test_mutation_11_failed_migration_cannot_continue(tmp_path: Path) -> None:
    result = migrate_workspace(root=tmp_path, fail_after_backup=True)
    assert result.status == "ROLLED_BACK"
    assert not (tmp_path / "workspace_schema.json").exists()


def test_mutation_12_migration_cannot_skip_verified_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        pws,
        "create_workspace_backup",
        lambda **_kwargs: WorkspaceBackupResult("FAILED", None, 0, message="injected"),
    )
    assert migrate_workspace(root=tmp_path).status == "BLOCKED_BACKUP"
    assert not (tmp_path / "workspace_schema.json").exists()


def test_mutation_13_corrupt_backup_cannot_restore(tmp_path: Path) -> None:
    save_personal_entry(_personal(), asset_registry=REGISTRY, root=tmp_path)
    backup = create_workspace_backup(root=tmp_path)
    (backup.path / "personal_board.json").write_text("{}", encoding="utf-8")
    assert restore_workspace(backup.path, confirmed=True, root=tmp_path).status == "BLOCKED_CORRUPT"


def test_mutation_14_restore_cannot_target_canonical_source_path(tmp_path: Path) -> None:
    save_personal_entry(_personal(), asset_registry=REGISTRY, root=tmp_path / "workspace")
    backup = create_workspace_backup(root=tmp_path / "workspace")
    with pytest.raises(WorkspaceValidationError, match="protected source"):
        restore_workspace(
            backup.path, confirmed=True, root=tmp_path / "local_exports" / "finished_v1"
        )


def test_mutation_15_decision_cannot_delete_without_confirmation(tmp_path: Path) -> None:
    create_decision(_decision(), asset_registry=REGISTRY, root=tmp_path)
    assert delete_decision("d1", confirmed=False, root=tmp_path).status.startswith("BLOCKED")
    assert len(load_store("decision_journal", root=tmp_path).records) == 1


def test_mutation_16_automatic_trade_winner_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceValidationError, match="recommendation"):
        save_scenario(_scenario({"winner": "Side A"}), asset_registry=REGISTRY, root=tmp_path)


def test_mutation_17_accept_reject_recommendation_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceValidationError, match="recommendation"):
        save_scenario(_scenario({"accept": True}), asset_registry=REGISTRY, root=tmp_path)


def test_mutation_18_credentials_cannot_enter_journal(tmp_path: Path) -> None:
    value = _decision()
    value["api_key"] = "secret"
    with pytest.raises(WorkspaceValidationError, match="Sensitive"):
        create_decision(value, asset_registry=REGISTRY, root=tmp_path)


def test_mutation_19_future_optional_fields_cannot_be_dropped(tmp_path: Path) -> None:
    row = _personal()
    row["future_optional"] = {"unicode": "café"}
    raw = json.dumps({"schema_version": 1, "store": "personal_board", "records": [row]})
    import_personal_board(raw, asset_registry=REGISTRY, confirmed=True, root=tmp_path)
    assert load_store("personal_board", root=tmp_path).records[0]["extensions"][
        "future_optional"
    ] == {"unicode": "café"}


def test_mutation_20_duplicate_journal_id_is_rejected(tmp_path: Path) -> None:
    create_decision(_decision(), asset_registry=REGISTRY, root=tmp_path)
    with pytest.raises(WorkspaceValidationError, match="Duplicate"):
        create_decision(_decision(), asset_registry=REGISTRY, root=tmp_path)


def test_mutation_21_duplicate_personal_asset_id_is_rejected(tmp_path: Path) -> None:
    raw = json.dumps(
        {"schema_version": 1, "store": "personal_board", "records": [_personal(), _personal()]}
    )
    with pytest.raises(WorkspaceValidationError, match="Duplicate"):
        import_personal_board(raw, asset_registry=REGISTRY, confirmed=True, root=tmp_path)


def test_mutation_22_source_version_mismatch_remains_visible() -> None:
    assert scenario_source_status(_scenario(), {"Finished V1": "v2"}) == "STALE_SOURCE_VERSION"


def test_mutation_23_personal_sort_cannot_change_canonical_rank(tmp_path: Path) -> None:
    canonical = tmp_path / "canonical.csv"
    canonical.write_text("player_id,nwr_rank\np1,1\n", encoding="utf-8")
    before = hashlib.sha256(canonical.read_bytes()).hexdigest()
    row = _personal()
    row["my_rank"] = 200
    save_personal_entry(row, asset_registry=REGISTRY, root=tmp_path / "workspace")
    sorted(
        load_store("personal_board", root=tmp_path / "workspace").records,
        key=lambda x: x["my_rank"],
    )
    assert hashlib.sha256(canonical.read_bytes()).hexdigest() == before


def test_mutation_24_active_pack_cannot_be_workspace_root(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceValidationError, match="protected source"):
        save_personal_entry(
            _personal(), asset_registry=REGISTRY, root=tmp_path / "data_packs" / "active_pack"
        )


def test_mutation_25_opaque_baseline_cannot_be_workspace_root(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceValidationError, match="protected source"):
        save_personal_entry(
            _personal(), asset_registry=REGISTRY, root=tmp_path / "opaque" / "baseline"
        )
