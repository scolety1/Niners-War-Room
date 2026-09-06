"""NWR Mock-Draft QA Day: `update_redraft_profile`'s new `practical_mode`
parameter, and the improved REDRAFT_RANKINGS_UNAVAILABLE error message.

Real gap found during a QA rehearsal: `practical_mode=True` was previously
settable ONLY by the Sleeper-import code path -- a manually-created or
manually-edited profile (e.g. an ESPN league, which has no live-sync
import) that rosters K/DST as real starters had NO way to enable it, so
ranking generation failed with an opaque, unhelpful error."""

import json
from pathlib import Path

from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.redraft_engine_v1_service import install_projection_snapshot

REPO_ROOT = Path(__file__).resolve().parents[1]
_BUNDLED_SNAPSHOT_CSV = (
    REPO_ROOT
    / "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
    / "GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv"
)


def _install_fresh_test_snapshot(tmp_path: Path) -> None:
    """The repo's own bundled seed receipt
    (docs/hq/model/.../NWR_DATA_GOVERNANCE.json) has a real, already-expired
    `valid_until` (2026-08-29) -- a genuine, separately-flagged finding from
    this QA pass (see NWR_OWNER_MOCK_QA_V1), not something this test should
    depend on. Installs the identical, real, already-governed 608-player
    CSV under a freshly-dated receipt bound to the same file, purely for
    this hermetic test fixture -- never touches the committed receipt."""
    receipt_path = tmp_path / "fresh_test_receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "authority": "NWR_DATA_GOVERNANCE",
                "approval_status": "APPROVED_FOR_REDRAFT_V1",
                "season": 2026,
                "source_sha256": (
                    "e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25"
                ),
                "source_id": "NWR_REDRAFT_2026_VETERAN_PLUS_ROOKIE_COMBINED_V1",
                "approved_by": "test fixture",
                "approved_at_utc": "2026-09-06T00:00:00+00:00",
                "valid_until": "2099-01-01",
            }
        ),
        encoding="utf-8",
    )
    install_projection_snapshot(tmp_path, 2026, _BUNDLED_SNAPSHOT_CSV, receipt_path)


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


def test_rostering_k_dst_without_practical_mode_raises_a_real_diagnostic_message(
    tmp_path: Path,
) -> None:
    """Before enabling Practical Mode, a profile that rosters K/DST as real
    starters cannot generate a ranking (K/DST are never part of the ranked
    universe by design) -- the error message must now say why, not just
    that it's "unavailable."""
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="L")
    profile_id = created.data["profile"]["profileId"]
    facade.update_redraft_profile(
        profile_id, league_name="L", team_count=12,
        roster=_roster(1, 1), scoring=_scoring(), draft=_draft(),
    )
    facade.activate_redraft_profile(profile_id)
    _install_fresh_test_snapshot(tmp_path)

    try:
        facade.start_redraft_draft_room(
            profile_id=profile_id, owner_slot=1, seed=1, speed="FAST", mode="MOCK"
        )
        raised = False
    except FacadeError as exc:
        raised = True
        assert "K" in exc.message and "DST" in exc.message
        assert exc.message != "The active Redraft ranking is unavailable."
    assert raised, "expected a real REDRAFT_RANKINGS_UNAVAILABLE error"


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
