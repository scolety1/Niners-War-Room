from __future__ import annotations

import shutil
from pathlib import Path

from scripts.validate_admitted_redraft_2026_combined import validate
from src.services.redraft_engine_v1_service import install_projection_snapshot

PACKET = Path(
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
)
VETERAN = Path(
    "docs/hq/model/nwr_redraft_2026_projection_admission_v1_20260808/"
    "GOVERNED_PROJECTION_SNAPSHOT.csv"
)


def test_combined_governed_snapshot_installs_and_validates(tmp_path: Path) -> None:
    packet = tmp_path / "packet"
    shutil.copytree(PACKET, packet)
    store = tmp_path / "store"
    installed = install_projection_snapshot(
        store,
        2026,
        packet / "GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv",
        packet / "NWR_DATA_GOVERNANCE.json",
    )
    assert len(installed.players) == 608
    receipt = validate(store, packet, VETERAN)
    assert receipt["status"] == "ADMITTED_COMBINED_PRODUCTION_VALIDATED"
    assert receipt["rookie_rows"] == 78
    assert receipt["settings_checks_passed"] == receipt["settings_checks_total"] == 5
    assert receipt["veteran_bytes_preserved_as_installed_prefix"] is True
