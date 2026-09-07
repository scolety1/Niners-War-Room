from src.services.current_kdst_eligibility_service import (
    classify_status,
    filter_current_kdst_assets,
)


def _k(name: str, player_id: str = "manual:K:1", team: str = "XXX") -> dict[str, str]:
    return {"player_id": player_id, "player_name": name, "position": "K", "team": team}


def _dst(team: str) -> dict[str, str]:
    return {"player_id": f"manual:DST:{team}", "player_name": f"{team} D/ST", "position": "DST", "team": team}


def test_classify_status_maps_real_nflverse_codes_correctly() -> None:
    assert classify_status("ACT") == "ACTIVE_ELIGIBLE"
    assert classify_status("RES") == "TEMPORARILY_LIMITED_BUT_ELIGIBLE"
    assert classify_status("PUP") == "TEMPORARILY_LIMITED_BUT_ELIGIBLE"
    assert classify_status("CUT") == "NOT_WITH_TEAM"
    assert classify_status("RET") == "RETIRED_INACTIVE"
    assert classify_status("NWT") == "NOT_WITH_TEAM"
    assert classify_status(None) == "UNKNOWN"
    assert classify_status("") == "UNKNOWN"
    assert classify_status("SOME_UNRECOGNIZED_CODE") == "UNKNOWN"


def test_classify_status_never_infers_season_out_from_a_bare_status() -> None:
    """A bare RES/PUP status alone must never become SEASON_OUT -- that
    label is reserved for an individually-sourced, verified override."""
    assert classify_status("RES") != "SEASON_OUT"
    assert classify_status("PUP") != "SEASON_OUT"
    assert classify_status("RES", verified_season_out=True) == "SEASON_OUT"


def test_filter_current_kdst_assets_excludes_a_real_cut_kicker() -> None:
    """RELEASE-BLOCKER ADDENDUM: a K whose cross-referenced nflverse status
    is unambiguously non-current is excluded from the pool -- by STATUS,
    never by name (this fixture uses a generic name/id, not any specific
    real player)."""
    assets = [_k("Test Kicker One", "manual:K:1"), _k("Test Kicker Two", "manual:K:2"), _dst("SEA")]
    status_by_name = {("testkickerone", "K"): "CUT", ("testkickertwo", "K"): "ACT"}
    filtered, counts = filter_current_kdst_assets(assets, status_by_name)
    names = {a["player_name"] for a in filtered}
    assert "Test Kicker One" not in names
    assert "Test Kicker Two" in names
    assert counts["excluded_not_current"] == 1
    assert counts["kept"] == 2  # kicker two + the DST


def test_filter_current_kdst_assets_never_excludes_for_an_injury_adjacent_status() -> None:
    assets = [_k("Test Kicker PUP", "manual:K:3")]
    status_by_name = {("testkickerpup", "K"): "PUP"}
    filtered, counts = filter_current_kdst_assets(assets, status_by_name)
    assert len(filtered) == 1
    assert counts["excluded_not_current"] == 0


def test_filter_current_kdst_assets_never_silently_excludes_an_unmatched_kicker() -> None:
    """No nflverse match at all (a genuinely new/unmapped player) is kept,
    not silently dropped -- unknown != excluded."""
    assets = [_k("Totally New Kicker", "manual:K:4")]
    filtered, counts = filter_current_kdst_assets(assets, {})
    assert len(filtered) == 1
    assert counts["unknown"] == 1
    assert counts["excluded_not_current"] == 0


def test_filter_current_kdst_assets_leaves_dst_entries_untouched() -> None:
    assets = [_dst("SEA"), _dst("DAL")]
    filtered, counts = filter_current_kdst_assets(assets, {})
    assert len(filtered) == 2
    assert counts["kept"] == 2
