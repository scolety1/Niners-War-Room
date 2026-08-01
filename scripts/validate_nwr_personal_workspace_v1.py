"""Run a deterministic disposable-root acceptance exercise for Personal Workspace V1."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from src.services.personal_workspace_service import (
    create_decision,
    create_workspace_backup,
    load_store,
    migrate_workspace,
    preview_workspace_restore,
    restore_workspace,
    save_personal_entry,
    save_scenario,
    scenario_source_status,
    summarize_workspace,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.reset and root.exists():
        shutil.rmtree(root)

    registry = {
        "current-player-1": "current_player",
        "rookie-1": "rookie_scored",
        "rookie-blocked-1": "rookie_blocked",
        "pick-2027-1": "draft_pick",
    }
    migration = migrate_workspace(root=root)
    assert migration.status == "MIGRATED"

    for index, (asset_id, asset_type) in enumerate(registry.items(), start=1):
        saved = save_personal_entry(
            {
                "asset_id": asset_id,
                "asset_type": asset_type,
                "source_authority_version": "golden-release-20260801",
                "my_tier": f"T{index}",
                "my_rank": index,
                "watchlist": index <= 2,
                "target": index == 2,
                "avoid": index == 3,
                "tags": ["demo", asset_type],
                "notes": "User-authored local demonstration note.",
                "extensions": {"custom_label": f"Demo {index}"},
            },
            asset_registry=registry,
            root=root,
            now_utc=f"2026-08-01T12:0{index}:00Z",
        )
        assert saved.status == "SAVED"

    decision = create_decision(
        {
            "decision_id": "decision-demo-1",
            "decision_type": "trade considered",
            "status": "Considered",
            "assets": ["current-player-1", "pick-2027-1"],
            "source_snapshot": {
                "current-player-1": {
                    "asset_type": "current_player",
                    "authority": "Finished V1",
                    "source_version": (
                        "263cc8aa050c4670bf5ed22701d7b0480"
                        "1d143480c5630b98e00dd08d2968ce4"
                    ),
                },
                "pick-2027-1": {
                    "asset_type": "draft_pick",
                    "authority": "User-described draft pick",
                    "source_version": "local-demo",
                },
            },
            "rationale": "Manual demo rationale; no recommendation is inferred.",
            "expected_outcome": "Review roster fit after the external decision.",
            "confidence": "Medium",
            "team_window": "Balanced",
            "follow_up_date": "2026-09-01",
            "retrospective_notes": "",
        },
        asset_registry=registry,
        root=root,
        now_utc="2026-08-01T12:10:00Z",
    )
    assert decision.status == "SAVED"

    versions = {"finished_v1": "v1", "outcome_v3": "v3", "rookie_review": "2026-v1"}
    for index, scenario_type in enumerate(
        ("trading_lab", "player_compare", "draft", "asset_explorer"), start=1
    ):
        saved = save_scenario(
            {
                "scenario_id": f"scenario-{index}",
                "scenario_type": scenario_type,
                "title": f"Demo {scenario_type}",
                "assets": ["current-player-1", "rookie-1"],
                "source_versions": versions,
                "payload": {
                    "manual_context": "User-authored, descriptive only.",
                    "notes": "Saved without an automatic verdict.",
                },
            },
            asset_registry=registry,
            root=root,
            now_utc=f"2026-08-01T12:2{index}:00Z",
        )
        assert saved.status == "SAVED"

    baseline_summary = summarize_workspace(root=root)
    backup = create_workspace_backup(root=root, now_utc="2026-08-01T12:30:00Z")
    assert backup.status == "CREATED" and backup.path is not None
    dry_run = preview_workspace_restore(backup.path)
    assert dry_run.valid

    save_personal_entry(
        {
            "asset_id": "current-player-1",
            "asset_type": "current_player",
            "source_authority_version": "golden-release-20260801",
            "my_tier": "CHANGED",
            "my_rank": 99,
            "watchlist": False,
            "target": False,
            "avoid": False,
            "tags": ["temporary"],
            "notes": "Temporary mutation before restore.",
            "extensions": {"custom_label": "Temporary"},
        },
        asset_registry=registry,
        root=root,
        now_utc="2026-08-01T12:31:00Z",
    )
    restored = restore_workspace(backup.path, confirmed=True, root=root)
    assert restored.status == "RESTORED"
    assert summarize_workspace(root=root) == baseline_summary

    failed_root = root.parent / f"{root.name}-injected-migration"
    if failed_root.exists():
        shutil.rmtree(failed_root)
    failed = migrate_workspace(root=failed_root, fail_after_backup=True)
    assert failed.status == "ROLLED_BACK"
    assert not (failed_root / "workspace_schema.json").exists()

    scenarios = load_store("saved_scenarios", root=root)
    stale = scenario_source_status(scenarios.records[0], {**versions, "outcome_v3": "v4"})
    assert stale == "STALE_SOURCE_VERSION"

    result = {
        "verdict": "PASS",
        "root": str(root),
        "migration": migration.status,
        "asset_types": sorted(set(registry.values())),
        "personal_entries": baseline_summary["personal_entries"],
        "decision_receipts": len(load_store("decision_journal", root=root).records),
        "scenario_types": sorted(str(row["scenario_type"]) for row in scenarios.records),
        "backup": backup.status,
        "restore_dry_run": dry_run.valid,
        "restore": restored.status,
        "restart_readback": all(
            load_store(name, root=root).status == "LOADED"
            for name in ("personal_board", "decision_journal", "saved_scenarios")
        ),
        "stale_source_detection": stale,
        "injected_migration_failure": failed.status,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
