from __future__ import annotations

from pathlib import Path

DOC_ROOT = Path("docs/hq/parallel_lanes")
FIXTURE_ROOT = Path("tests/fixtures/mock_draft_inputs")


def test_no_local_exports_csv_data_is_committed_in_mock_draft_fixtures() -> None:
    paths = list(FIXTURE_ROOT.rglob("*.csv"))

    assert paths
    assert all("local_exports" not in path.as_posix() for path in paths)


def test_no_real_manifest_under_local_exports_is_committed() -> None:
    assert not Path("local_exports/mock_draft/manual_input_manifest.local.json").exists()


def test_fixture_files_use_obvious_fake_names() -> None:
    fixture_text = "\n".join(
        path.read_text(encoding="utf-8") for path in FIXTURE_ROOT.rglob("*.csv")
    )

    assert "Fixture" in fixture_text


def test_docs_do_not_include_full_real_dataset_rows() -> None:
    docs_text = "\n".join(
        path.read_text(encoding="utf-8") for path in DOC_ROOT.glob("MOCK_DRAFT*.md")
    )

    assert "Real Player" not in docs_text
    assert "SENSITIVE" not in docs_text


def test_committed_manifest_example_uses_fake_paths_only() -> None:
    manifest = DOC_ROOT / "MOCK_DRAFT_INPUT_MANIFEST_EXAMPLE.json"
    text = manifest.read_text(encoding="utf-8")

    assert "C:/example/local-only/" in text
    assert "local_exports/mock_draft/manual_input_manifest.local.json" not in text
