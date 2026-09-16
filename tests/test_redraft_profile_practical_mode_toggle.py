"""NWR Mock-Draft QA Day: `update_redraft_profile`'s new `practical_mode`
parameter, and the improved REDRAFT_RANKINGS_UNAVAILABLE error message.

Real gap found during a QA rehearsal: `practical_mode=True` was previously
settable ONLY by the Sleeper-import code path -- a manually-created or
manually-edited profile (e.g. an ESPN league, which has no live-sync
import) that rosters K/DST as real starters had NO way to enable it, so
ranking generation failed with an opaque, unhelpful error."""

import csv
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.application.desktop_facade import DesktopBackendFacade
from src.services.redraft_engine_v1_service import install_projection_snapshot

REPO_ROOT = Path(__file__).resolve().parents[1]
_BUNDLED_SNAPSHOT_CSV = (
    REPO_ROOT
    / "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
    / "GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv"
)


def _install_fresh_test_snapshot(tmp_path: Path) -> None:
    """Full Cycle V1, Worker 5 (Section 3D item 3): this used to install the
    real bundled 608-player CSV UNCHANGED, with its own real, fixed
    `source_as_of=2026-08-08` baked into every row, under a freshly-dated
    RECEIPT (`valid_until=2099-01-01`). That freshened the receipt's own
    expiry (a real, separately-flagged finding from NWR_OWNER_MOCK_QA_V1 --
    the committed seed receipt's `valid_until` of 2026-08-29 is genuinely
    expired) but did nothing about `install_projection_snapshot`'s OWN,
    separate 30-day `source_as_of` freshness gate
    (`_source_as_of_reason`/`MAX_PROJECTION_AGE_DAYS`,
    redraft_engine_v1_service.py), which is computed against real wall-clock
    "today" independent of the receipt. Triaged 2026-09-16: as real time
    advanced past 2026-09-07 (`2026-08-08` + 30 days), this fixture started
    failing on its own -- confirmed NOT a product bug (`_source_as_of_reason`
    correctly computes `today = datetime.now(UTC).date()`, no off-by-one/
    timezone defect) and NOT a design flaw (the 30-day gate is the real,
    intentional "no stale projections without an explicit draft-day
    authorization" governance rule). It is fixture staleness, of the exact
    same class `test_redraft_engine_v1_service.py`'s own
    `_fresh_projection_rows()` already documents and fixes for its sibling
    tests (search that file for "environmental source_as_of date-cliff").
    Applying the same fix here: rewrite every row's `source_as_of` to a date
    that is always fresh relative to whenever this test actually runs
    (`today - 1 day`), write that to a temp CSV under `tmp_path`, and bind
    the receipt's `source_sha256` to THAT rewritten file's real hash (a
    receipt's `source_sha256` must match the exact bytes being installed --
    `_validate_approval_receipt` rejects a mismatch) instead of the original
    bundled file's now-irrelevant hash. This never touches the real
    committed CSV or its real receipt -- only this test's own hermetic
    tmp_path copy."""
    rows: list[dict[str, str]]
    with _BUNDLED_SNAPSHOT_CSV.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    fresh_date = (datetime.now(UTC).date() - timedelta(days=1)).isoformat()
    for row in rows:
        row["source_as_of"] = fresh_date

    fresh_csv_path = tmp_path / "fresh_test_snapshot.csv"
    with fresh_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    receipt_path = tmp_path / "fresh_test_receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "authority": "NWR_DATA_GOVERNANCE",
                "approval_status": "APPROVED_FOR_REDRAFT_V1",
                "season": 2026,
                "source_sha256": hashlib.sha256(fresh_csv_path.read_bytes()).hexdigest(),
                "source_id": "NWR_REDRAFT_2026_VETERAN_PLUS_ROOKIE_COMBINED_V1",
                "approved_by": "test fixture",
                "approved_at_utc": datetime.now(UTC).isoformat(),
                "valid_until": "2099-01-01",
            }
        ),
        encoding="utf-8",
    )
    install_projection_snapshot(tmp_path, 2026, fresh_csv_path, receipt_path)


def _roster(k: int, dst: int) -> dict:
    return {
        "qb": 1, "rb": 2, "wr": 2, "te": 1, "flex": 1, "superflex": 0,
        "k": k, "dst": dst, "benchSize": 6,
    }


def _scoring() -> dict:
    return {"reception": 0.0, "passingTd": 4.0, "interception": -2.0, "tePremium": 0.0}


def _draft() -> dict:
    return {"rounds": 16, "draftSlot": None, "replacementMethod": "expected_available"}


def test_update_redraft_profile_without_practical_mode_preserves_existing_value(
    tmp_path: Path,
) -> None:
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="L")
    profile_id = created.data["profile"]["profileId"]
    assert created.data["profile"]["practicalMode"] is False

    # No callers before this fix ever passed practical_mode -- confirm the
    # parameter is fully optional and changes nothing when omitted.
    edited = facade.update_redraft_profile(
        profile_id, league_name="L", team_count=12,
        roster=_roster(0, 0), scoring=_scoring(), draft=_draft(),
    )
    assert edited.data["profile"]["practicalMode"] is False


def test_update_redraft_profile_can_now_enable_practical_mode(tmp_path: Path) -> None:
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="L")
    profile_id = created.data["profile"]["profileId"]

    edited = facade.update_redraft_profile(
        profile_id, league_name="L", team_count=12,
        roster=_roster(1, 1), scoring=_scoring(), draft=_draft(),
        practical_mode=True,
    )
    assert edited.data["profile"]["practicalMode"] is True

    # Can also be turned back off explicitly.
    reverted = facade.update_redraft_profile(
        profile_id, league_name="L", team_count=12,
        roster=_roster(0, 0), scoring=_scoring(), draft=_draft(),
        practical_mode=False,
    )
    assert reverted.data["profile"]["practicalMode"] is False


def test_rostering_k_dst_without_practical_mode_now_works_automatically(
    tmp_path: Path,
) -> None:
    """NWR LAST PRE-DRAFT BLOCKER CLOSURE (section 1, "remove the owner
    Practical Mode footgun"): this test used to assert the OPPOSITE --
    that rostering K/DST without first opting into Practical Mode raised
    a diagnostic error. That was a real, confirmed footgun: K/DST are
    NEVER part of the ranked universe in ANY mode (they are always
    separately-sourced manual assets, unconditionally, by design), so the
    old ranked-coverage check was never a meaningful signal for K/DST
    specifically -- it only forced the owner to discover and toggle an
    implementation detail to roster an ordinary K/DST slot. K/DST are now
    structurally exempt from that check whenever the roster actually
    configures them, independent of `practical_mode` -- confirmed here by
    calling `update_redraft_profile` WITHOUT `practical_mode` at all and
    still reaching a fully configured draft room."""
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="L")
    profile_id = created.data["profile"]["profileId"]
    updated = facade.update_redraft_profile(
        profile_id, league_name="L", team_count=12,
        roster=_roster(1, 1), scoring=_scoring(), draft=_draft(),
    )
    assert updated.data["profile"]["practicalMode"] is False
    facade.activate_redraft_profile(profile_id)
    _install_fresh_test_snapshot(tmp_path)

    state = facade.start_redraft_draft_room(
        profile_id=profile_id, owner_slot=1, seed=1, speed="FAST", mode="MOCK"
    )
    assert state.data["draftBoard"]["configured"] is True


def test_manual_kdst_assets_reach_bootstrap_without_practical_mode(
    tmp_path: Path,
) -> None:
    """NWR LAST PRE-DRAFT BLOCKER CLOSURE: a real, distinct bug found
    WHILE verifying the footgun-removal fix above -- `redraft_bootstrap()`
    only ever loaded manual K/DST assets from disk `if selected.
    practical_mode`, so even after K/DST rostering stopped requiring the
    flag, real imported manual K/DST assets would still never reach
    Suggestions/Draft Board unless the owner ALSO separately enabled
    Practical Mode -- silently reopening the same footgun. Fixed to the
    real structural condition (the roster configures K or DST),
    independent of the flag."""
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="L")
    profile_id = created.data["profile"]["profileId"]
    facade.update_redraft_profile(
        profile_id, league_name="L", team_count=12,
        roster=_roster(1, 1), scoring=_scoring(), draft=_draft(),
    )
    facade.import_udk_kdst_snapshot(
        profile_id=profile_id,
        csv_text=(
            "player_name_raw,position,team_name_raw,team_raw\n"
            "Test Kicker,K,,BUF\n"
            ",DST,Buffalo Bills,\n"
        ),
    )
    facade.activate_redraft_profile(profile_id)
    _install_fresh_test_snapshot(tmp_path)

    bootstrap = facade.redraft_bootstrap()
    manual_assets = bootstrap.data["manualAssets"]
    assert {row["position"] for row in manual_assets} == {"K", "DST"}
    assert len(manual_assets) == 2
    assert bootstrap.data["activeProfile"]["practicalMode"] is False


def test_enabling_practical_mode_lets_the_same_k_dst_profile_generate_a_ranking(
    tmp_path: Path,
) -> None:
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="L")
    profile_id = created.data["profile"]["profileId"]
    facade.update_redraft_profile(
        profile_id, league_name="L", team_count=12,
        roster=_roster(1, 1), scoring=_scoring(), draft=_draft(),
        practical_mode=True,
    )
    facade.activate_redraft_profile(profile_id)
    _install_fresh_test_snapshot(tmp_path)

    state = facade.start_redraft_draft_room(
        profile_id=profile_id, owner_slot=1, seed=1, speed="FAST", mode="MOCK"
    )
    assert state.data["draftBoard"]["configured"] is True
