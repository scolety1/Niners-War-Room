from __future__ import annotations

import csv
from pathlib import Path

from src.services.model_v4_player_identity_crosswalk_service import (
    IDENTITY_CROSSWALK_HEADER,
    IDENTITY_REPORT_HEADER,
    SourceIdentityRecord,
    build_player_identity_crosswalk,
    normalize_identity_name,
    write_player_identity_crosswalk_outputs,
)


def test_player_identity_crosswalk_handles_known_hard_names() -> None:
    result = build_player_identity_crosswalk(
        records=(
            _record("De'Von Achane", "RB", sleeper_id="9226"),
            _record("Brian Thomas Jr.", "WR", sleeper_id="11631"),
            _record("Luther Burden III", "WR", sleeper_id="12519"),
            _record("Jaxon Smith-Njigba", "WR", sleeper_id="9488"),
            _record("Amon-Ra St. Brown", "WR", sleeper_id="7547"),
            _record("Travis Etienne Jr.", "RB", sleeper_id="7543"),
            _record("Patrick Mahomes II", "QB", sleeper_id="4046"),
            _record("Omar Cooper Jr.", "WR", sleeper_id="13276"),
            _record("KC Concepcion", "WR", sleeper_id="13298"),
            _record("Kevin Concepcion", "WR", cfbd_player_id="4870653"),
        )
    )

    by_normalized = {
        row["normalized_player_name"]: row for row in result.crosswalk_rows
    }
    assert "devonachane" in by_normalized
    assert "brianthomas" in by_normalized
    assert "lutherburden" in by_normalized
    assert "jaxonsmithnjigba" in by_normalized
    assert "amonrastbrown" in by_normalized
    assert "travisetienne" in by_normalized
    assert "patrickmahomes" in by_normalized
    assert "omarcooper" in by_normalized
    assert "kevinconcepcion" in by_normalized
    assert "KC Concepcion" in by_normalized["kevinconcepcion"]["source_specific_names"]
    assert "Kevin Concepcion" in by_normalized["kevinconcepcion"]["source_specific_names"]
    assert "explicit_alias_applied" in by_normalized["kevinconcepcion"]["warning_flags"]
    assert result.ambiguous_rows == ()


def test_player_identity_crosswalk_flags_duplicate_names_without_fuzzy_join() -> None:
    result = build_player_identity_crosswalk(
        records=(
            _record("David Long", "CB", nfl_person_id="cb-1"),
            _record("David Long Jr.", "LB", nfl_person_id="lb-1"),
        )
    )

    assert len(result.crosswalk_rows) == 2
    assert len(result.ambiguous_rows) == 2
    assert all(row["join_status"] == "ambiguous" for row in result.ambiguous_rows)
    assert all("duplicate_normalized_name" in row["warning_flags"] for row in result.ambiguous_rows)
    assert result.summary["fuzzy_joining_used"] is False


def test_player_identity_crosswalk_reports_unresolved_missing_ids() -> None:
    result = build_player_identity_crosswalk(
        records=(
            _record("Name Only Player", "WR"),
            _record("No Position Player", "", sleeper_id="id-1"),
        )
    )

    by_name = {row["canonical_player_name"]: row for row in result.unresolved_rows}
    assert "missing_all_stable_ids" in by_name["Name Only Player"]["warning_flags"]
    assert "missing_position" in by_name["No Position Player"]["warning_flags"]


def test_player_identity_crosswalk_writes_expected_outputs(tmp_path: Path) -> None:
    result = build_player_identity_crosswalk(
        records=(_record("Patrick Mahomes II", "QB", sleeper_id="4046"),)
    )

    paths = write_player_identity_crosswalk_outputs(
        tmp_path / "out",
        result,
        doc_path=tmp_path / "phase_10e.md",
    )

    assert _header(paths["crosswalk"]) == IDENTITY_CROSSWALK_HEADER
    assert _header(paths["unresolved"]) == IDENTITY_REPORT_HEADER
    assert _header(paths["ambiguous"]) == IDENTITY_REPORT_HEADER
    assert paths["doc"].exists()
    assert result.summary["formula_scores_changed"] is False
    assert result.summary["active_rankings_changed"] is False


def test_identity_normalization_strips_suffixes_and_preserves_explicit_alias() -> None:
    assert normalize_identity_name("Brian Thomas Jr.") == "brianthomas"
    assert normalize_identity_name("Luther Burden III") == "lutherburden"
    assert normalize_identity_name("De'Von Achane") == "devonachane"
    assert normalize_identity_name("Amon-Ra St. Brown") == "amonrastbrown"
    assert normalize_identity_name("Travis Etienne Jr.") == "travisetienne"
    assert normalize_identity_name("Patrick Mahomes II") == "patrickmahomes"
    assert normalize_identity_name("Omar Cooper Jr.") == "omarcooper"
    assert normalize_identity_name("KC Concepcion") == "kevinconcepcion"
    assert normalize_identity_name("Nick Singleton") == "nicholassingleton"


def _record(
    name: str,
    position: str,
    *,
    sleeper_id: str = "",
    cfbd_player_id: str = "",
    nfl_person_id: str = "",
) -> SourceIdentityRecord:
    return SourceIdentityRecord(
        source_group="test",
        source_name="test.csv",
        source_path="test.csv",
        source_player_name=name,
        position=position,
        sleeper_id=sleeper_id,
        cfbd_player_id=cfbd_player_id,
        nfl_person_id=nfl_person_id,
    )


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
