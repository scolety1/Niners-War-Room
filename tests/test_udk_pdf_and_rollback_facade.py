"""NWR class-time autonomous hardening, section 7: proves the real facade
wiring this session added actually closes two owner-facing gaps --
`parse_udk_position_pdf`/`save_udk_position_pdf_rankings` existed but were
never reachable from any facade method (CSV was the only real UDK import
path), and no rollback capability existed at all.

A full happy-path PDF-import-through-the-facade test would additionally
need a real, governed 2026 projection snapshot fixture (`_redraft_room_
context` requires one for identity matching) -- attempting to build one
here surfaced a genuine, PRE-EXISTING, unrelated environment issue: the
same bundled fixture CSV/receipt `test_redraft_profile_practical_mode_
toggle.py` already uses for exactly this purpose now fails with
"Projection snapshot has no rankable player rows" even in that untouched
file (a real source_as_of freshness-window drift as the simulated "today"
advances, not something this session's changes caused or should patch).
Not fixed here -- out of scope for this directive section; the PDF
parsing/matching logic itself is already thoroughly covered at the
service level in test_redraft_draft_room_v1_service.py. This file proves
the two things that do NOT depend on that broken fixture: the unreadable-
path rejection (now checked before any ranking work, see the reordering
in desktop_facade.py) and the real rollback facade wiring (the rollback
service function only needs `load_profile`, never a ranking)."""

from pathlib import Path

import pytest

from src.application.desktop_facade import DesktopBackendFacade, FacadeError
from src.services.redraft_draft_room_v1_service import save_udk_position_rankings

REPO_ROOT = Path(__file__).resolve().parents[1]


def _facade_with_profile(tmp_path: Path) -> tuple[DesktopBackendFacade, str]:
    facade = DesktopBackendFacade(repo_root=REPO_ROOT, mode="redraft", redraft_root=tmp_path)
    created = facade.create_redraft_profile(preset_key="12_TEAM_1QB_HALF_PPR", league_name="L")
    profile_id = created.data["profile"]["profileId"]
    facade.activate_redraft_profile(profile_id)
    return facade, profile_id


def test_import_udk_pdf_rankings_rejects_an_unreadable_path_before_touching_ranking(
    tmp_path: Path,
) -> None:
    """Proves the file is validated BEFORE `_redraft_room_context` runs --
    this must reject with the real, specific PDF error, not a ranking/
    profile error, even with no governed snapshot installed at all."""
    facade, profile_id = _facade_with_profile(tmp_path)
    with pytest.raises(FacadeError) as exc_info:
        facade.import_udk_pdf_rankings(profile_id=profile_id, pdf_path=str(tmp_path / "missing.pdf"))
    assert exc_info.value.code == "REDRAFT_UDK_PDF_UNREADABLE"


def test_rollback_udk_position_rankings_closes_the_real_facade_gap(tmp_path: Path) -> None:
    facade, profile_id = _facade_with_profile(tmp_path)

    # Seed two real versions directly at the service level, using a
    # minimal fixture LeagueProfile/RankingResult sharing the real facade-
    # created profile_id (the ranking-dependent write path's own matching
    # logic is already thoroughly tested in
    # test_redraft_draft_room_v1_service.py; this test's job is only to
    # prove the FACADE's rollback method really reads/writes the same
    # on-disk file the CSV/PDF import paths do).
    from src.services.redraft_engine_v1_service import (
        DraftContext,
        LeagueProfile,
        RankingResult,
        RosterSettings,
        ScoringSettings,
    )

    league_profile = LeagueProfile(
        profile_id, "Fixture", 2026, 10, RosterSettings(), ScoringSettings(),
        DraftContext(rounds=16),
    )
    empty_ranking = RankingResult(league_profile, (), (), (), "2026-08-08T00:00:00Z", profile_id)
    header = "Name,Position,Team,Bye Week,Rank,Points,Risk,Upside,ADP,Tier,Outlook,Dynasty,Markers"
    v1 = f'{header}\r\n"QB 0","QB","TST","7","1","300.0","4.0","8.0","2.06","1","Outlook.","locked","Mark Drafted"\r\n'
    v2 = f'{header}\r\n"QB 1","QB","TST","7","1","300.0","4.0","8.0","2.16","1","Outlook.","locked","Mark Drafted"\r\n'
    save_udk_position_rankings(tmp_path, league_profile, empty_ranking, v1, ())
    save_udk_position_rankings(tmp_path, league_profile, empty_ranking, v2, ())

    result = facade.rollback_udk_position_rankings(profile_id=profile_id, position="QB")
    assert result.data["rollback"]["position"] == "QB"
    assert result.data["rollback"]["remainingHistoryCount"] == 0


def test_rollback_udk_position_rankings_rejects_when_no_history(tmp_path: Path) -> None:
    facade, profile_id = _facade_with_profile(tmp_path)
    with pytest.raises(FacadeError) as exc_info:
        facade.rollback_udk_position_rankings(profile_id=profile_id, position="QB")
    assert exc_info.value.code == "REDRAFT_UDK_ROLLBACK_UNAVAILABLE"
