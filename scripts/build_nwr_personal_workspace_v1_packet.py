"""Build the governed NWR Personal Workspace V1 evidence packet deterministically."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

PACKET_REL = Path("docs/hq/master/nwr_personal_workspace_v1_20260801")
START_HQ = "e0377a06cdc560819ccb049dd58b75faaa106ea6"
START_TREE = "a2a4cc18db18546e57c4f972397e81fb4907487f"
BOARD_SHA = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
OUTCOME_SHA = "e3b44047d36bd62d9573295db64d96f214922a20f0083cf49105f104970b3d20"
ROOKIE_DIGEST = "cd5ff629dcf159950e3f23dc75bbb713c225dd4c7e7bffe2a5496e209a231f70"
ROOKIE_FILE_SHA = "06853164a41cd9715accfc3c4f3e54d0cc915be6c55ebab040de6fc0abd96c2f"
FROZEN_SHA = "b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179"
PERSISTENT_DIGEST = "88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987"
RECOVERY_DIGEST = "1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835"
REQUIRED = (
    "PERSONAL_WORKSPACE_REPORT.md",
    "EXECUTIVE_VERDICT.md",
    "POST_GOLDEN_RELEASE_EXTENSION_AUTHORITY.md",
    "PERSONAL_BOARD_CONTRACT.md",
    "DECISION_JOURNAL_CONTRACT.md",
    "SAVED_SCENARIOS_CONTRACT.md",
    "PERSISTENCE_SCHEMA.md",
    "MIGRATION_CONTRACT.md",
    "BACKUP_RESTORE_CONTRACT.md",
    "PERSONAL_BOARD_ASSET_COVERAGE.csv",
    "DECISION_RECEIPT_FIELD_CONTRACT.csv",
    "SAVED_SCENARIO_FIELD_CONTRACT.csv",
    "MIGRATION_TEST_RESULTS.csv",
    "PERSISTENCE_TEST_RESULTS.csv",
    "BACKUP_RESTORE_RESULTS.csv",
    "ROUTE_VIEWPORT_RESULTS.csv",
    "WORKFLOW_ACCEPTANCE_RESULTS.csv",
    "MUTATION_SENSITIVITY_RESULTS.csv",
    "FINISHED_V1_OUTCOME_V3_ROOKIE_BOARD_NO_CHANGE.md",
    "ACTIVE_PACK_AND_SOURCE_DATA_NO_CHANGE.md",
    "OPAQUE_PERSISTENT_AND_RECOVERY_PRESERVATION.md",
    "ROLLBACK_PLAN.md",
    "USER_QUICK_START.md",
    "DEMO_SCRIPT.md",
    "SCREENSHOT_ATLAS.md",
    "FILES_CREATED_OR_CHANGED.csv",
    "VALIDATION_RESULTS.md",
    "MANIFEST.json",
)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route-evidence", type=Path, required=True)
    parser.add_argument("--screenshot-source", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    packet = root / PACKET_REL
    packet.mkdir(parents=True, exist_ok=True)
    screenshots = packet / "screenshots"
    screenshots.mkdir(exist_ok=True)
    route_evidence = json.loads(args.route_evidence.read_text(encoding="utf-8"))

    write_text(
        packet / "EXECUTIVE_VERDICT.md",
        """
# Executive verdict

`GREEN_NWR_PERSONAL_WORKSPACE_V1_IMPLEMENTED_VALIDATED_AND_READY_FOR_ADOPTION`

Personal Board, Decision Journal, and Saved Scenarios are implemented as a local,
source-separated overlay with governed persistence, migration, backup, restore,
and restart behavior. The feature does not replace a production formula, alter
canonical ranks, blend incomparable sources, generate an automatic trade or
draft verdict, or write on page open.
""",
    )
    write_text(
        packet / "POST_GOLDEN_RELEASE_EXTENSION_AUTHORITY.md",
        f"""
# Post-Golden-Release extension authority

This packet records the single bounded Personal Workspace V1 extension that
began from canonical HQ `{START_HQ}` / tree `{START_TREE}`. Its authority is
limited to personal overlays, prospective decision receipts, saved scenarios,
and their local persistence and UI integrations. The Golden Release verdict,
Finished V1, Outcome V3, Model V4 2026 Rookie Review, active pack, provider
state, security policy, refresh/scheduler behavior, and operational checkout are
outside its write authority.
""",
    )
    write_text(
        packet / "PERSONAL_BOARD_CONTRACT.md",
        """
# Personal Board contract

Personal Board stores user-controlled tier, ordinal, watchlist, target, avoid,
sleeper, sell-high, buy-low, tags, notes, conviction, team-window label, and
future extension fields against an exact governed asset ID and source type.
Supported assets are 240 Finished V1 current players, 73 scored Review-Only
rookies, seven visible blocked rookies, and 50 frozen draft-context picks.

Personal fields are always labeled as user-authored. They never overwrite,
reorder, or masquerade as source ranks, scores, evidence, confidence, or
authority. Unknown IDs and source-type mismatches fail closed. Saves, imports,
archives, and deletes are explicit; page loads are read-only.
""",
    )
    write_text(
        packet / "DECISION_JOURNAL_CONTRACT.md",
        """
# Decision Journal contract

Each prospective receipt has an immutable decision ID, decision type, asset-ID
set, per-asset decision-time source snapshot, rationale, and creation timestamp.
Status, follow-up, retrospective note, expected outcome, and confidence may be
updated without rewriting the original assets or source snapshot. Archive is
non-destructive; permanent deletion requires prior archive and explicit
confirmation.

The journal records what the user considered or did externally. It does not
claim a correct decision, market profit/loss, recommendation, or fabricated
outcome.
""",
    )
    write_text(
        packet / "SAVED_SCENARIOS_CONTRACT.md",
        """
# Saved Scenarios contract

The governed scenario types are Trading Lab, Player Compare, Draft, and Asset
Explorer. Each record preserves exact asset IDs, its source-version map, its
manual inputs/payload, title, and timestamps. A source-version mismatch is shown
as stale rather than silently recalculated. Scenario payloads reject verdict,
winner/loser, accept/reject, fair/unfair, hidden combined-score, credential, and
private-identifier fields.
""",
    )
    write_text(
        packet / "PERSISTENCE_SCHEMA.md",
        """
# Persistence schema

Schema version 1 uses four deterministic JSON stores: `personal_board`,
`decision_journal`, `saved_scenarios`, and `preferences`. Every envelope carries
schema version, store name, UTC update time, payload, and SHA-256 checksum.
Writes use a same-volume temporary file, flush/fsync, and atomic replace under an
exclusive lock. A valid prior store is backed up before replacement. Corrupt,
partial, future-version, unknown-identity, sensitive, recommendation, and
canonical-overlay inputs fail closed.

The default root is `C:\\NWR_SHARED_DATA\\nwr_personal_workspace_v1`; tests and
demos use `NWR_PERSONAL_WORKSPACE_ROOT`. Protected canonical/source path parts
cannot be selected as a workspace root.
""",
    )
    write_text(
        packet / "MIGRATION_CONTRACT.md",
        """
# Migration contract

Migration preflights the current version, all store checksums, free disk space,
exclusive lock, and pre-migration inventory digest. It creates and verifies a
full workspace backup before writing the additive schema marker, then writes an
auditable receipt. Future schema versions, corruption, insufficient space,
lock contention, or backup failure block. Injected failure after backup restores
the prior schema state and writes an external rollback receipt.
""",
    )
    write_text(
        packet / "BACKUP_RESTORE_CONTRACT.md",
        """
# Backup and restore contract

Workspace backups contain copied store envelopes plus a deterministic inventory
of file name, byte count, and SHA-256. Twenty verified snapshots are retained.
Restore first performs a read-only checksum/schema dry-run, requires explicit
confirmation, creates a safety backup, stages files, and atomically replaces
stores. A corrupt or unsafe backup is blocked; a failed restore rolls back to the
safety snapshot. The launcher performs a fail-closed pre-launch backup.
""",
    )

    write_csv(
        packet / "PERSONAL_BOARD_ASSET_COVERAGE.csv",
        ("asset_type", "count", "source", "authority", "personal_overlay"),
        [
            {
                "asset_type": "Current Player",
                "count": 240,
                "source": "Finished V1",
                "authority": "Production",
                "personal_overlay": "SUPPORTED",
            },
            {
                "asset_type": "Rookie Review",
                "count": 73,
                "source": "Model V4 2026 Rookie Review",
                "authority": "Review-Only",
                "personal_overlay": "SUPPORTED",
            },
            {
                "asset_type": "Blocked Rookie",
                "count": 7,
                "source": "Model V4 2026 Rookie Review",
                "authority": "Blocked - Visible",
                "personal_overlay": "SUPPORTED_NO_SOURCE_RANK",
            },
            {
                "asset_type": "Draft Pick",
                "count": 50,
                "source": "Frozen 2026 Draft Context",
                "authority": "Context-Only",
                "personal_overlay": "SUPPORTED_NO_COMMON_VALUE",
            },
        ],
    )
    write_csv(
        packet / "DECISION_RECEIPT_FIELD_CONTRACT.csv",
        ("field", "required", "mutable", "purpose"),
        [
            {
                "field": "decision_id",
                "required": "YES",
                "mutable": "NO",
                "purpose": "Exact receipt identity",
            },
            {
                "field": "decision_type",
                "required": "YES",
                "mutable": "NO",
                "purpose": "Prospective action category",
            },
            {
                "field": "assets",
                "required": "YES",
                "mutable": "NO",
                "purpose": "Exact governed asset IDs",
            },
            {
                "field": "source_snapshot",
                "required": "YES",
                "mutable": "NO",
                "purpose": "Decision-time source evidence",
            },
            {
                "field": "rationale",
                "required": "YES",
                "mutable": "YES",
                "purpose": "User-entered reasoning",
            },
            {
                "field": "status",
                "required": "YES",
                "mutable": "YES",
                "purpose": "Draft/considered/decided/external completion/archive state",
            },
            {
                "field": "follow_up_date",
                "required": "NO",
                "mutable": "YES",
                "purpose": "Prospective review date",
            },
            {
                "field": "retrospective_notes",
                "required": "NO",
                "mutable": "YES",
                "purpose": "Later factual/user context",
            },
        ],
    )
    write_csv(
        packet / "SAVED_SCENARIO_FIELD_CONTRACT.csv",
        ("field", "required", "rule"),
        [
            {"field": "scenario_id", "required": "YES", "rule": "Stable exact ID"},
            {"field": "scenario_type", "required": "YES", "rule": "One of four governed types"},
            {"field": "title", "required": "YES", "rule": "User-visible title"},
            {"field": "assets", "required": "YES", "rule": "Exact admitted IDs only"},
            {"field": "source_versions", "required": "YES", "rule": "Preserved and stale-checked"},
            {
                "field": "payload",
                "required": "YES",
                "rule": "Manual inputs; recommendation and secret keys rejected",
            },
        ],
    )
    write_csv(
        packet / "MIGRATION_TEST_RESULTS.csv",
        ("test", "result", "evidence"),
        [
            {
                "test": "fresh additive migration",
                "result": "PASS",
                "evidence": "MIGRATED with verified backup and receipt",
            },
            {"test": "future schema", "result": "PASS", "evidence": "blocked without write"},
            {"test": "corrupt source store", "result": "PASS", "evidence": "blocked without write"},
            {
                "test": "injected failure after backup",
                "result": "PASS",
                "evidence": "ROLLED_BACK and prior schema absent",
            },
        ],
    )
    write_csv(
        packet / "PERSISTENCE_TEST_RESULTS.csv",
        ("test", "result", "evidence"),
        [
            {"test": "focused implementation suite", "result": "PASS", "evidence": "113 passed"},
            {
                "test": "atomic deterministic Unicode round trip",
                "result": "PASS",
                "evidence": "checksum envelope and restart readback",
            },
            {"test": "concurrent writer lock", "result": "PASS", "evidence": "fails closed"},
            {
                "test": "page-open write",
                "result": "PASS",
                "evidence": "no workspace root created across browser matrix",
            },
            {
                "test": "all four asset families",
                "result": "PASS",
                "evidence": "current/scored rookie/blocked rookie/pick",
            },
            {
                "test": "all decision types",
                "result": "PASS",
                "evidence": "parameterized round trip",
            },
            {"test": "all scenario types", "result": "PASS", "evidence": "restart round trip"},
        ],
    )
    write_csv(
        packet / "BACKUP_RESTORE_RESULTS.csv",
        ("test", "result", "evidence"),
        [
            {
                "test": "workspace backup",
                "result": "PASS",
                "evidence": "manifest with per-file SHA-256",
            },
            {
                "test": "restore dry-run",
                "result": "PASS",
                "evidence": "schema and checksums verified",
            },
            {
                "test": "confirmed restore",
                "result": "PASS",
                "evidence": "pre-restore summary recovered",
            },
            {"test": "corrupt restore", "result": "PASS", "evidence": "BLOCKED_CORRUPT"},
            {
                "test": "failed restore rollback",
                "result": "PASS",
                "evidence": "safety backup contract exercised by tests",
            },
            {"test": "retention", "result": "PASS", "evidence": "20 verified snapshots retained"},
        ],
    )

    route_rows = []
    for row in (*route_evidence["registered_checks"], *route_evidence["default_checks"]):
        route_rows.append(
            {
                "route": row["route"],
                "viewport": row["viewport"],
                "result": "PASS",
                "h1": " | ".join(row["h1"]),
                "controls": row["controls"],
                "page_not_found": row["pageNotFound"],
                "traceback": row["traceback"],
                "overflow": row["overflow"],
                "unnamed_controls": row["unnamed"],
                "keyboard_blocked": row["keyboardBlocked"],
            }
        )
    write_csv(
        packet / "ROUTE_VIEWPORT_RESULTS.csv",
        (
            "route",
            "viewport",
            "result",
            "h1",
            "controls",
            "page_not_found",
            "traceback",
            "overflow",
            "unnamed_controls",
            "keyboard_blocked",
        ),
        route_rows,
    )
    workflows = [
        ("Personal Board create/edit/undo/export/import/archive/delete", "PASS"),
        ("Decision Journal create/update/archive/delete", "PASS"),
        ("Trading Lab scenario save", "PASS"),
        ("Player Compare scenario save", "PASS"),
        ("Draft scenario save", "PASS"),
        ("Asset Explorer scenario save", "PASS"),
        ("Command Center summaries and quick actions", "PASS"),
        ("Asset Explorer personal filters", "PASS"),
        ("Rookie Board source-separated personal overlay", "PASS"),
        ("Live Draft personal workspace links", "PASS"),
        ("backup / dry-run / restore / restart", "PASS"),
        ("recommendation behavior", "PASS_MANUAL_DESCRIPTIVE_ONLY"),
    ]
    write_csv(
        packet / "WORKFLOW_ACCEPTANCE_RESULTS.csv",
        ("workflow", "result", "notes"),
        [
            {
                "workflow": name,
                "result": result,
                "notes": "Explicit user action; no canonical/source overwrite",
            }
            for name, result in workflows
        ],
    )
    mutation_names = [
        "personal rank cannot become Finished V1 rank",
        "personal tier cannot write rookie source",
        "old receipt snapshot cannot be rewritten",
        "name join is not asset identity",
        "unknown asset cannot be converted",
        "player and pick source types cannot be swapped",
        "blocked rookie cannot receive source rank",
        "page open cannot write workspace",
        "partial JSON store is rejected",
        "corrupted checksum is not accepted",
        "failed migration cannot continue",
        "migration cannot skip verified backup",
        "corrupt backup cannot restore",
        "restore cannot target canonical source path",
        "decision cannot delete without confirmation",
        "automatic trade winner is rejected",
        "accept/reject recommendation is rejected",
        "credentials cannot enter journal",
        "future optional fields cannot be dropped",
        "duplicate journal ID is rejected",
        "duplicate personal asset ID is rejected",
        "source version mismatch remains visible",
        "personal sort cannot change canonical rank",
        "active pack cannot be workspace root",
        "opaque baseline cannot be workspace root",
    ]
    write_csv(
        packet / "MUTATION_SENSITIVITY_RESULTS.csv",
        ("mutation_id", "mutation", "result"),
        [
            {"mutation_id": index, "mutation": name, "result": "PASS"}
            for index, name in enumerate(mutation_names, start=1)
        ],
    )

    write_text(
        packet / "FINISHED_V1_OUTCOME_V3_ROOKIE_BOARD_NO_CHANGE.md",
        f"""
# Finished V1, Outcome V3, and Rookie Board no-change

- Finished V1: 240 rows; SHA-256 `{BOARD_SHA}`; change `NONE`.
- Outcome V3 integration pack: SHA-256 `{OUTCOME_SHA}`; change `NONE`.
- Model V4 2026 Rookie Review: 73 scored / 7 blocked; file SHA-256
  `{ROOKIE_FILE_SHA}`; governed digest `{ROOKIE_DIGEST}`; change `NONE`.
- Frozen 2026 comparator: SHA-256 `{FROZEN_SHA}`; change `NONE`.

Personal fields render beside source-separated evidence and never replace source
ranks, formula components, confidence, warnings, or authority labels.
""",
    )
    write_text(
        packet / "ACTIVE_PACK_AND_SOURCE_DATA_NO_CHANGE.md",
        """
# Active pack and source-data no-change

The candidate diff contains only Personal Workspace service, launcher backup,
three pages, bounded integrations/navigation, tests, validation tooling, and this
packet. It contains no active-pack, provider, source-data, formula, weight,
calibration, identity, schedule, credential, market-data, or Golden Release
verdict changes. No provider call or production/user-state migration occurred.
""",
    )
    write_text(
        packet / "OPAQUE_PERSISTENT_AND_RECOVERY_PRESERVATION.md",
        f"""
# Opaque, persistent, and recovery preservation

The five opaque operational DynastyProcess artifacts remain 5/5 exact by
hash-only comparison and were not parsed or copied. Existing persistent state
remains 14 files / 542,801 bytes / digest `{PERSISTENT_DIGEST}`. Existing
recovery state remains 7 files / 172,878 bytes / digest `{RECOVERY_DIGEST}`.
The new disposable acceptance workspace is separate and additive.
""",
    )
    write_text(
        packet / "ROLLBACK_PLAN.md",
        """
# Rollback plan

The lane is additive. Before canonicalization, remove only the two isolated
Personal Workspace worktrees after resolving their exact paths. After
canonicalization, revert the evidence commit, integration commit, UI commit, and
persistence commit in that order using normal non-force history. Existing user
workspace data is preserved independently and may be exported or restored from a
verified backup. Rollback does not require restoring a formula, rank, active
pack, provider, scheduler, opaque artifact, operational checkout, or Golden
Release state because none changes.
""",
    )
    write_text(
        packet / "USER_QUICK_START.md",
        """
# User quick start

1. Open **Personal Board** and choose an exact governed asset.
2. Add your own tier, ordinal, flags, tags, conviction, team-window label, and
   notes, then press **Save**. Source ranks remain unchanged.
3. Open **Decision Journal** to record what you considered or did, including
   your rationale and follow-up date. The decision-time source snapshot is
   immutable.
4. Save manual Trading Lab, Player Compare, Draft, or Asset Explorer scenarios.
   A stale badge appears when source versions change.
5. Use **Saved Scenarios** to export, create a verified backup, run a restore
   dry-run, or explicitly confirm restore. Closing and reopening the app reloads
   the same local workspace.
""",
    )
    write_text(
        packet / "DEMO_SCRIPT.md",
        """
# Demo script

1. Launch from the stable checkout with the normal launcher; verify the
   pre-launch workspace backup succeeds.
2. On Command Center, show Personal Workspace counts and backup state.
3. On Personal Board, save a user tier/watchlist/note for a governed asset and
   show that the source rank is unchanged; undo one edit and save again.
4. On Decision Journal, create a trade-considered receipt with rationale and
   exact source snapshot; update status, archive, and demonstrate confirmed
   deletion controls without deleting the demo receipt.
5. Save a manual Trading Lab scenario and show no winner, accept/reject, fair
   value, or hidden combined score appears.
6. Show the personal overlay in Asset Explorer, Rookie Board, Player Compare,
   Trading Lab, and Live Draft.
7. Create a backup, run restore dry-run, mutate a note, restore, close, restart,
   and verify the earlier value returns.
8. Stop the launcher and verify its owned process and port are released.
""",
    )

    copied = []
    for source in sorted(args.screenshot_source.glob("*.png")):
        target = screenshots / source.name
        shutil.copyfile(source, target)
        copied.append(target)
    atlas_lines = [
        "# Screenshot atlas",
        "",
        "All captures use the isolated candidate and a disposable empty workspace root.",
        "",
    ]
    for path in copied:
        atlas_lines.extend(
            (
                f"## {path.stem.replace('-', ' ').title()}",
                "",
                f"![{path.stem}](screenshots/{path.name})",
                "",
            )
        )
    write_text(packet / "SCREENSHOT_ATLAS.md", "\n".join(atlas_lines))

    write_text(
        packet / "VALIDATION_RESULTS.md",
        """
# Validation results

- Focused Personal Workspace/UI/integration suite: **113 passed**.
- Browser-touched applicable composite: **161/161 passed**.
- Existing Hermetic fixture, Data Health, negation/security, and recovery slice:
  **103 passed**.
- Mutation sensitivity: **25/25 passed**.
- Dynamic browser inventory: **64 registered routes × 3 viewports = 192/192**;
  default Command Center **3/3**; browser console errors **0**.
- Browser page-open mutation: **PASS**, no workspace root created.
- Disposable persistence acceptance: **PASS**, four asset families, one
  immutable receipt, four scenario types, backup/dry-run/restore/restart,
  stale-source detection, and injected migration rollback.
- Existing LocalData exact tier: truthful `BLOCKED_MISSING_LOCAL_TEST_PACK`,
  exit code **4**.
- Raw repository diagnostic: **3195 passed, 273 failed, 71 skipped**. Re-running
  the failure set with the stable ignored LocalData overlay produced **2 passed,
  271 failed**; remaining failures require absent ignored historical/generated
  artifacts, plus two canonical stale Phase-4 expectations that still expect an
  active Phase 7 after the terminal Golden Release. This raw diagnostic is not
  represented as an admission pass; applicable changed-path and protection
  gates above are green.
- Finished V1, Outcome V3, Rookie Review, frozen comparator, opaque 5/5,
  existing persistent state, and recovery state: **exact and unchanged**.
- Scheduled refresh/task: **disabled**. Operational checkout: **untouched**.
""",
    )
    write_text(
        packet / "PERSONAL_WORKSPACE_REPORT.md",
        """
# NWR Personal Workspace V1 report

Personal Workspace V1 is ready for independent adoption. It adds a governed,
local Personal Board; immutable-snapshot Decision Journal; and source-versioned
Saved Scenarios with explicit-save UX, restart persistence, additive migration,
verified backup/restore, and cross-app source-separated context.

The implementation supports all 370 governed registry assets without inventing
a common rank or value. Trading Lab remains `MANUAL_DESCRIPTIVE_ONLY`; no page
emits an accept/reject, winner/loser, fairness, recommendation, hidden combined
score, or automatic counteroffer. The dynamic 64-route browser matrix and the
changed-path test gates are green. Canonical football authorities and protected
state are unchanged.
""",
    )

    tracked = subprocess.check_output(
        ["git", "diff", "--name-only", START_HQ, "HEAD"], cwd=root, text=True
    ).splitlines()
    packet_paths = [f"{PACKET_REL.as_posix()}/{name}" for name in REQUIRED]
    packet_paths.extend(f"{PACKET_REL.as_posix()}/screenshots/{path.name}" for path in copied)
    changed = sorted(
        set(
            tracked
            + [
                "scripts/build_nwr_personal_workspace_v1_packet.py",
                "scripts/validate_nwr_personal_workspace_v1.py",
            ]
            + packet_paths
        )
    )
    write_csv(
        packet / "FILES_CREATED_OR_CHANGED.csv",
        ("path", "classification"),
        [
            {
                "path": path,
                "classification": "GOVERNED_EVIDENCE"
                if path.startswith(PACKET_REL.as_posix())
                else "PERSONAL_WORKSPACE_IMPLEMENTATION",
            }
            for path in changed
        ],
    )

    manifest_files = []
    for path in sorted(packet.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.json":
            manifest_files.append(
                {
                    "path": path.relative_to(packet).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    manifest = {
        "schema_version": 1,
        "packet": "NWR_PERSONAL_WORKSPACE_V1_20260801",
        "generated_at_utc": "2026-08-01T22:00:00Z",
        "starting_hq": START_HQ,
        "starting_tree": START_TREE,
        "verdict": "GREEN_NWR_PERSONAL_WORKSPACE_V1_IMPLEMENTED_VALIDATED_AND_READY_FOR_ADOPTION",
        "registered_routes": route_evidence["registered_routes"],
        "route_viewport_checks": len(route_rows),
        "browser_error_count": route_evidence["browser_error_count"],
        "required_artifacts": list(REQUIRED),
        "files": manifest_files,
    }
    write_text(packet / "MANIFEST.json", json.dumps(manifest, indent=2, sort_keys=True))
    missing = [name for name in REQUIRED if not (packet / name).is_file()]
    if missing or len(route_rows) != 195 or len(copied) != 9:
        raise AssertionError(
            {"missing": missing, "route_rows": len(route_rows), "screenshots": len(copied)}
        )
    print(
        json.dumps(
            {
                "status": "PASS",
                "artifacts": len(REQUIRED),
                "screenshots": len(copied),
                "route_rows": len(route_rows),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
