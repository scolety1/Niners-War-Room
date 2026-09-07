"""NWR LAST PRE-DRAFT BLOCKER CLOSURE (section 2): a real release blocker
found while building the exact 16-round 8-team acceptance mock at
tonight's real roster shape (1K/1DST) -- the ONLY real, live K/DST source
ever wired anywhere (`start_practical_redraft_mock`) is hard-gated to the
owner's one Fantasy Gamers Sleeper league, so a manually-configured league
(e.g. tonight's real ESPN league) had NO real path to a current K/DST pool
at all. `parse_udk_kdst_snapshot()` (all 32 real NFL teams' current K/DST,
an owner-authorized UDK CSV export) already existed but was never
reachable from any facade method, HTTP route, or GUI control -- this
proves the new `import_udk_kdst_snapshot` facade method (wired to a real
HTTP route and a real GUI upload control) actually closes that gap."""

from pathlib import Path

from src.application.desktop_facade import DesktopBackendFacade, FacadeError

REPO_ROOT = Path(__file__).resolve().parents[1]

_SNAPSHOT_CSV = """player_name_raw,position,team_name_raw,team_raw
Andre Szmyt,K,Buffalo Bills,BUF
Cameron Dicker,K,Los Angeles Chargers,LAC
Buffalo Bills,DST,Buffalo Bills,BUF
Los Angeles Chargers,DST,Los Angeles Chargers,LAC
"""


def test_import_udk_kdst_snapshot_populates_real_manual_assets(tmp_path: Path) -> None:
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="L")
    profile_id = created.data["profile"]["profileId"]

    result = facade.import_udk_kdst_snapshot(profile_id=profile_id, csv_text=_SNAPSHOT_CSV)
    assets = result.data["manualAssets"]

    kickers = [row for row in assets if row["position"] == "K"]
    defenses = [row for row in assets if row["position"] == "DST"]
    assert {row["player_name"] for row in kickers} == {"Andre Szmyt", "Cameron Dicker"}
    assert {row["team"] for row in defenses} == {"BUF", "LAC"}
    # Never assigns an NWR score/authority claim to K/DST -- the real,
    # unmodified authority label the parser itself uses.
    assert all(row["authority"] == "EXTERNAL_UDK_UNMODELED_BY_NWR" for row in assets)
    assert result.data["addedCount"] == 4


def test_import_udk_kdst_snapshot_is_additive_and_never_overwrites(tmp_path: Path) -> None:
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="L")
    profile_id = created.data["profile"]["profileId"]

    first = facade.import_udk_kdst_snapshot(profile_id=profile_id, csv_text=_SNAPSHOT_CSV)
    assert first.data["addedCount"] == 4
    # Re-importing the exact same snapshot adds nothing new (idempotent,
    # keyed by player_id) -- never duplicates or overwrites.
    second = facade.import_udk_kdst_snapshot(profile_id=profile_id, csv_text=_SNAPSHOT_CSV)
    assert second.data["addedCount"] == 0
    assert len(second.data["manualAssets"]) == 4


def test_import_udk_kdst_snapshot_rejects_a_csv_missing_required_columns(
    tmp_path: Path,
) -> None:
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="L")
    profile_id = created.data["profile"]["profileId"]

    try:
        facade.import_udk_kdst_snapshot(profile_id=profile_id, csv_text="not_a_real_column\nvalue\n")
        raised = False
    except FacadeError as exc:
        raised = True
        assert exc.code == "UDK_KDST_SNAPSHOT_INVALID"
    assert raised, "expected a real UDK_KDST_SNAPSHOT_INVALID error"
