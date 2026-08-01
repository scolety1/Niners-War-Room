from pathlib import Path

from scripts.validate_nwr_phase8_golden_release_v1 import PACKET

ROOT = Path(__file__).resolve().parents[1]


def test_golden_release_evidence_files_exist() -> None:
    required = {
        "README.md",
        "VIEWPORT_ACCEPTANCE.csv",
        "ROUTE_INVENTORY.md",
        "WORKFLOW_ACCEPTANCE.csv",
        "PERSISTENCE_AND_RECOVERY.md",
        "SCREENSHOT_ATLAS.md",
        "DEMO_AND_QUICK_START.md",
        "CAPABILITY_AND_LIMITATIONS.md",
        "ROLLBACK_GUIDE.md",
        "FINAL_MACHINE_STATE.md",
        "VALIDATION_RESULTS.md",
    }
    assert required.issubset({path.name for path in (ROOT / PACKET).iterdir()})


def test_screenshot_atlas_is_complete() -> None:
    screenshots = tuple((ROOT / PACKET / "screenshots").glob("*.png"))
    assert len(screenshots) == 9
    assert all(path.stat().st_size > 10_000 for path in screenshots)
