from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.services.refresh_receipt_store_service import write_refresh_receipt

FIXTURE = Path("tests/fixtures/durable_refresh_receipt_fixture.py")


def _payload(run_id: str, *, status: str = "GREEN") -> dict[str, object]:
    failed = status == "RED"
    return {
        "run_id": run_id,
        "started_at_utc": "2026-07-13T12:00:00+00:00",
        "finished_at_utc": "2026-07-13T12:01:00+00:00",
        "loader_mode": "QUICK_REFRESH",
        "overall_status": status,
        "results": [
            {
                "source_id": "fixture_source",
                "source_name": "Fixture source",
                "dataset_id": "",
                "source_family": "",
                "action_type": "FAILED" if failed else "REFRESHED",
                "status": status,
                "refreshed": not failed,
                "execution_status": "failed" if failed else "success",
                "freshness_status": "STALE" if failed else "CURRENT",
            }
        ],
    }


def test_receipt_survives_rerun_navigation_equivalent_and_fresh_app_load(
    tmp_path: Path, monkeypatch
) -> None:
    latest = write_refresh_receipt(
        _payload("20260713_121001"),
        status_root=tmp_path,
        created_at_utc="2026-07-13T12:02:00+00:00",
    ).latest_path
    monkeypatch.setenv("NWR_REFRESH_RECEIPT_TEST_PATH", str(latest))

    at = AppTest.from_file(str(FIXTURE)).run(timeout=20)
    assert not at.exception
    receipt_id = str(at.dataframe[0].value.iloc[0]["receipt_id"])
    assert receipt_id.startswith("rr_")
    assert "Latest refresh attempt" in str(at.dataframe[0].value.iloc[0]["receipt_role"])
    assert "CURRENT_RETAINED_DATA" in at.dataframe[-1].value.to_string()

    rerun = at.run(timeout=20)
    assert not rerun.exception
    assert str(rerun.dataframe[0].value.iloc[0]["receipt_id"]) == receipt_id

    fresh_app = AppTest.from_file(str(FIXTURE)).run(timeout=20)
    assert not fresh_app.exception
    assert str(fresh_app.dataframe[0].value.iloc[0]["receipt_id"]) == receipt_id


def test_corrupt_latest_shows_failure_and_validated_prior_separately(
    tmp_path: Path, monkeypatch
) -> None:
    write_refresh_receipt(_payload("20260713_121002"), status_root=tmp_path)
    latest = write_refresh_receipt(
        _payload("20260713_121003", status="RED"),
        status_root=tmp_path,
    ).latest_path
    latest.write_text("{bad", encoding="utf-8")
    monkeypatch.setenv("NWR_REFRESH_RECEIPT_TEST_PATH", str(latest))

    at = AppTest.from_file(str(FIXTURE)).run(timeout=20)

    assert not at.exception
    assert any("corrupt" in item.value.lower() for item in at.error)
    assert any("validated prior receipt" in item.value.lower() for item in at.warning)
    text = "\n".join(frame.value.to_string() for frame in at.dataframe)
    assert "Validated prior receipt (not latest)" in text
    assert "CURRENT_RETAINED_DATA" in text
