from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.services.personal_workspace_service import (
    WorkspaceLockError,
    WorkspaceValidationError,
    archive_decision,
    create_decision,
    create_workspace_backup,
    export_personal_board,
    import_personal_board,
    load_store,
    migrate_workspace,
    preview_workspace_restore,
    restore_workspace,
    save_personal_entry,
    save_scenario,
    summarize_workspace,
    update_decision,
)

REGISTRY = {
    "current:p1": "Current Player",
    "rookie:r1": "Rookie Review",
    "blocked-rookie:carson-beck": "Blocked Rookie",
    "pick:2026:1.01": "Draft Pick",
}


def personal(asset_id: str = "current:p1", asset_type: str = "Current Player") -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "source_authority_version": "Finished V1 sha256:fixture",
        "my_tier": "A",
        "my_rank": 1,
        "watchlist": True,
        "target": True,
        "avoid": False,
        "sleeper": False,
        "sell_high": False,
        "buy_low": True,
        "tags": ["core", "🔥"],
        "notes": "Unicode résumé — " + "long " * 1000,
        "conviction": "High",
        "team_window": "Contending",
    }


def decision(decision_id: str = "d1") -> dict[str, object]:
    return {
        "decision_id": decision_id,
        "decision_type": "trade considered",
        "status": "Considered",
        "assets": ["current:p1", "pick:2026:1.01"],
        "source_snapshot": {
            "current:p1": {
                "asset_type": "Current Player",
                "visible_rank": "1",
                "source_version": "v1",
            },
            "pick:2026:1.01": {"asset_type": "Draft Pick", "visible_rank": "1"},
        },
        "personal_snapshot": {"current:p1": {"my_tier": "A", "my_rank": 1}},
        "rationale": "User-entered rationale",
        "expected_outcome": "User-entered expectation",
        "confidence": "Medium",
        "team_window": "Balanced",
        "follow_up_date": "2026-12-01",
        "retrospective_notes": "",
    }


def scenario(kind: str = "trading_lab") -> dict[str, object]:
    return {
        "scenario_id": f"s-{kind}",
        "scenario_type": kind,
        "title": f"Saved {kind}",
        "assets": ["current:p1", "pick:2026:1.01"],
        "source_versions": {"Finished V1": "fixture"},
        "payload": {"notes": "manual context", "team_window": "Balanced"},
    }


def test_load_is_read_only_and_empty(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    assert load_store("personal_board", root=root).status == "MISSING"
    assert not root.exists()


def test_personal_entry_round_trip_is_atomic_deterministic_and_unicode_safe(tmp_path: Path) -> None:
    save_personal_entry(
        personal(), asset_registry=REGISTRY, root=tmp_path, now_utc="2026-08-01T12:00:00+00:00"
    )
    first = (tmp_path / "stores/personal_board.json").read_bytes()
    row = load_store("personal_board", root=tmp_path).records[0]
    assert row["notes"].startswith("Unicode résumé")
    save_personal_entry(
        personal(), asset_registry=REGISTRY, root=tmp_path, now_utc="2026-08-01T12:00:00+00:00"
    )
    assert (tmp_path / "stores/personal_board.json").read_bytes() == first
    assert not tuple((tmp_path / "stores").glob("*.tmp"))


def test_checksum_corruption_fails_closed(tmp_path: Path) -> None:
    save_personal_entry(personal(), asset_registry=REGISTRY, root=tmp_path)
    path = tmp_path / "stores/personal_board.json"
    path.write_text(path.read_text().replace("Contending", "Rebuilding"), encoding="utf-8")
    assert load_store("personal_board", root=tmp_path).status == "CORRUPT"
    with pytest.raises(Exception, match="checksum"):
        save_personal_entry(personal(), asset_registry=REGISTRY, root=tmp_path)


def test_concurrent_writer_lock_fails_closed(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / ".workspace.lock").write_text("other", encoding="utf-8")
    with pytest.raises(WorkspaceLockError):
        save_personal_entry(personal(), asset_registry=REGISTRY, root=tmp_path)


@pytest.mark.parametrize(
    ("asset_id", "asset_type", "message"),
    (
        ("unknown", "Current Player", "Unknown asset"),
        ("current:p1", "Rookie Review", "type mismatch"),
    ),
)
def test_exact_identity_and_source_type_are_required(
    tmp_path: Path, asset_id: str, asset_type: str, message: str
) -> None:
    with pytest.raises(WorkspaceValidationError, match=message):
        save_personal_entry(personal(asset_id, asset_type), asset_registry=REGISTRY, root=tmp_path)


def test_blocked_rookie_and_pick_allow_personal_context_without_source_rank(tmp_path: Path) -> None:
    blocked = personal("blocked-rookie:carson-beck", "Blocked Rookie")
    blocked.pop("my_rank")
    pick = personal("pick:2026:1.01", "Draft Pick")
    save_personal_entry(blocked, asset_registry=REGISTRY, root=tmp_path)
    save_personal_entry(pick, asset_registry=REGISTRY, root=tmp_path)
    rows = load_store("personal_board", root=tmp_path).records
    assert len(rows) == 2
    assert "source_rank" not in next(row for row in rows if row["asset_type"] == "Blocked Rookie")


def test_import_round_trip_preserves_future_optional_fields(tmp_path: Path) -> None:
    row = personal()
    row["future_optional"] = {"v": 2}
    raw = json.dumps({"schema_version": 1, "store": "personal_board", "records": [row]})
    result = import_personal_board(raw, asset_registry=REGISTRY, confirmed=True, root=tmp_path)
    assert result.status == "IMPORTED"
    exported = json.loads(export_personal_board(root=tmp_path))
    assert exported["records"][0]["extensions"]["future_optional"] == {"v": 2}


def test_import_duplicate_asset_rejected(tmp_path: Path) -> None:
    raw = json.dumps(
        {"schema_version": 1, "store": "personal_board", "records": [personal(), personal()]}
    )
    with pytest.raises(WorkspaceValidationError, match="Duplicate"):
        import_personal_board(raw, asset_registry=REGISTRY, confirmed=True, root=tmp_path)


def test_import_requires_confirmation(tmp_path: Path) -> None:
    raw = json.dumps({"schema_version": 1, "store": "personal_board", "records": []})
    assert (
        import_personal_board(raw, asset_registry=REGISTRY, confirmed=False, root=tmp_path).status
        == "BLOCKED_CONFIRMATION_REQUIRED"
    )
    assert not tuple(tmp_path.iterdir())


def test_decision_snapshot_is_immutable_and_later_context_does_not_rewrite(tmp_path: Path) -> None:
    create_decision(
        decision(), asset_registry=REGISTRY, root=tmp_path, now_utc="2026-08-01T12:00:00+00:00"
    )
    before = load_store("decision_journal", root=tmp_path).records[0]["source_snapshot"]
    with pytest.raises(WorkspaceValidationError, match="immutable"):
        update_decision(
            "d1", {"source_snapshot": {"current:p1": {"visible_rank": "99"}}}, root=tmp_path
        )
    update_decision("d1", {"retrospective_notes": "Later factual note"}, root=tmp_path)
    assert load_store("decision_journal", root=tmp_path).records[0]["source_snapshot"] == before


def test_duplicate_decision_and_unconfirmed_archive_fail_closed(tmp_path: Path) -> None:
    create_decision(decision(), asset_registry=REGISTRY, root=tmp_path)
    with pytest.raises(WorkspaceValidationError, match="Duplicate"):
        create_decision(decision(), asset_registry=REGISTRY, root=tmp_path)
    assert (
        archive_decision("d1", confirmed=False, root=tmp_path).status
        == "BLOCKED_CONFIRMATION_REQUIRED"
    )
    assert load_store("decision_journal", root=tmp_path).records[0]["status"] == "Considered"


def test_archive_is_non_destructive(tmp_path: Path) -> None:
    create_decision(decision(), asset_registry=REGISTRY, root=tmp_path)
    archive_decision("d1", confirmed=True, root=tmp_path)
    row = load_store("decision_journal", root=tmp_path).records[0]
    assert row["status"] == "Archived" and row["archived"] is True


@pytest.mark.parametrize("kind", ("trading_lab", "player_compare", "draft", "asset_explorer"))
def test_all_saved_scenario_types_survive_restart(tmp_path: Path, kind: str) -> None:
    save_scenario(scenario(kind), asset_registry=REGISTRY, root=tmp_path)
    rows = load_store("saved_scenarios", root=tmp_path).records
    assert any(row["scenario_type"] == kind for row in rows)


@pytest.mark.parametrize("key", ("winner", "accept", "combined_score", "automatic_counteroffer"))
def test_automatic_recommendation_fields_are_rejected(tmp_path: Path, key: str) -> None:
    value = scenario()
    value["payload"] = {key: "yes"}
    with pytest.raises(WorkspaceValidationError, match="recommendation"):
        save_scenario(value, asset_registry=REGISTRY, root=tmp_path)


@pytest.mark.parametrize("key", ("password", "api_key", "league_token", "email"))
def test_credentials_and_private_identifiers_are_rejected(tmp_path: Path, key: str) -> None:
    value = decision()
    value[key] = "secret"
    with pytest.raises(WorkspaceValidationError, match="Sensitive"):
        create_decision(value, asset_registry=REGISTRY, root=tmp_path)


def test_backup_dry_run_restore_and_corruption_rollback(tmp_path: Path) -> None:
    save_personal_entry(
        personal(), asset_registry=REGISTRY, root=tmp_path, now_utc="2026-08-01T12:00:00+00:00"
    )
    backup = create_workspace_backup(root=tmp_path, now_utc="2026-08-01T12:01:00+00:00")
    assert backup.file_count == 1 and preview_workspace_restore(backup.path).valid
    changed = personal()
    changed["my_tier"] = "D"
    save_personal_entry(
        changed, asset_registry=REGISTRY, root=tmp_path, now_utc="2026-08-01T12:02:00+00:00"
    )
    result = restore_workspace(backup.path, confirmed=True, root=tmp_path)
    assert result.status == "RESTORED"
    assert load_store("personal_board", root=tmp_path).records[0]["my_tier"] == "A"
    (backup.path / "personal_board.json").write_text("{}", encoding="utf-8")
    assert not preview_workspace_restore(backup.path).valid
    assert restore_workspace(backup.path, confirmed=True, root=tmp_path).status == "BLOCKED_CORRUPT"
    assert load_store("personal_board", root=tmp_path).records[0]["my_tier"] == "A"


def test_additive_migration_and_injected_failure_rollback(tmp_path: Path) -> None:
    migrated = migrate_workspace(root=tmp_path)
    assert migrated.status == "MIGRATED" and migrated.backup_path and migrated.receipt_path
    second = tmp_path / "failed"
    failed = migrate_workspace(root=second, fail_after_backup=True)
    assert failed.status == "ROLLED_BACK"
    assert not (second / "workspace_schema.json").exists()
    assert failed.backup_path and preview_workspace_restore(failed.backup_path).valid


def test_workspace_summary_is_read_only(tmp_path: Path) -> None:
    save_personal_entry(personal(), asset_registry=REGISTRY, root=tmp_path)
    create_decision(decision(), asset_registry=REGISTRY, root=tmp_path)
    save_scenario(scenario(), asset_registry=REGISTRY, root=tmp_path)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*.json")}
    assert summarize_workspace(root=tmp_path) == {
        "personal_entries": 1,
        "watchlist": 1,
        "targets": 1,
        "avoid": 0,
        "open_decisions": 1,
        "saved_scenarios": 1,
    }
    assert before == {path: path.read_bytes() for path in tmp_path.rglob("*.json")}
