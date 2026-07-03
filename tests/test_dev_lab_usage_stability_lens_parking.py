from pathlib import Path

from src.services.development_lab_review_upgrade_service import (
    USAGE_STABILITY_STATIC_PACKET_PATH,
    artifact_manifest_rows,
    guardrail_ledger_rows,
    usage_stability_lens_good_parts_rows,
    usage_stability_lens_parking_rows,
)


def test_usage_stability_lens_is_parked_as_review_only_hold() -> None:
    rows = usage_stability_lens_parking_rows()
    by_item = {row["Item"]: row for row in rows}

    assert by_item["Lens interpretation"]["Value"] == "REVIEW_ONLY_USAGE_STABILITY_LENS"
    assert by_item["Lens interpretation"]["Status"] == "HOLD"
    assert "Not a ranking system" in by_item["Lens interpretation"]["Review-only note"]
    assert by_item["Production promotion"]["Value"] == "Not approved"
    assert by_item["Main-formula readiness"]["Value"] == "Not approved"
    assert by_item["App/live preview"]["Status"] == "MANUAL_PATH_ONLY"


def test_usage_stability_lens_static_packet_path_is_optional_metadata_only() -> None:
    rows = usage_stability_lens_parking_rows()
    packet = {row["Item"]: row for row in rows}["Static label-fixed packet"]

    assert packet["Value"] == USAGE_STABILITY_STATIC_PACKET_PATH
    assert packet["Status"] == "OPTIONAL_OUTSIDE_REPO_PACKET"
    assert "manual path only" in packet["Review-only note"]
    assert "cannot break the app" in packet["Review-only note"]


def test_usage_stability_lens_display_counts_and_null_fence_are_preserved() -> None:
    rows = usage_stability_lens_parking_rows()
    by_item = {row["Item"]: row for row in rows}

    assert by_item["Warmer rows"]["Value"] == "115"
    assert by_item["Colder rows"]["Value"] == "127"
    assert by_item["Null-fenced rows"]["Value"] == "125"
    assert by_item["Null-fenced rows"]["Status"] == "Not enough information"
    assert by_item["CeeDee Lamb example"]["Value"] == "LENS_COLDER_THAN_BASELINE"
    assert "WR11 to WR18" in by_item["CeeDee Lamb example"]["Review-only note"]


def test_usage_stability_lens_good_parts_are_extracted_without_promotion() -> None:
    rows = usage_stability_lens_good_parts_rows()
    extracted = {row["Extracted part"] for row in rows}

    assert "NFLVerse usage/opportunity data pipeline" in extracted
    assert "Null-fencing / Not enough information semantics" in extracted
    assert "Warmer/colder movement labels" in extracted
    assert "Static human-review packet generation pattern" in extracted
    assert "No-promotion validation checks" in extracted
    assert all("PRODUCTION" not in row["Parking status"] for row in rows)


def test_development_lab_page_wires_parking_section_only() -> None:
    page = Path("app/pages/35_development_lab_v1.py").read_text(encoding="utf-8")
    component = Path("app/components/development_lab.py").read_text(encoding="utf-8")

    assert "Usage/Stability Lens Parking" in page
    assert "render_usage_stability_lens_parking_panel" in page
    assert "Review-only usage/stability lens" in component
    assert "main board" in component
    assert "open it, score it, regenerate it" in component


def test_no_ranking_or_model_surfaces_wire_the_usage_stability_lens() -> None:
    protected_paths = [
        Path("app/pages/05_rankings.py"),
        Path("app/pages/23_trading_lab_v1.py"),
        Path("app/pages/07_model_lab.py"),
    ]
    protected_text = "\n".join(path.read_text(encoding="utf-8") for path in protected_paths)

    assert "usage_stability_lens" not in protected_text
    assert "Usage/Stability Lens" not in protected_text
    assert "LENS_COLDER_THAN_BASELINE" not in protected_text


def test_no_hidden_sort_recommendation_or_source_truth_language_introduced() -> None:
    paths = [
        Path("app/components/development_lab.py"),
        Path("app/pages/35_development_lab_v1.py"),
        Path("src/services/development_lab_review_upgrade_service.py"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)

    forbidden_phrases = [
        "use as ranking",
        "ranking command",
        "recommendation logic",
        "hidden sort is active",
        "source truth is promoted",
        "model training is enabled",
        "production promotion is approved",
        "main-formula readiness is approved",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text


def test_docs_capture_future_gate_requirements_and_no_silent_promotion() -> None:
    docs = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("docs/hq/usage_stability_lens").glob("USAGE_STABILITY_LENS_*.md")
    )

    assert "GREEN_DEV_LAB_USAGE_STABILITY_LENS_PARKED_REVIEW_ONLY" in docs
    assert "Separate approval for any model input use" in docs
    assert "Separate approval for any rankings impact" in docs
    assert "No Silent Promotion" in docs
    assert "Nothing in this extraction approves rank behavior changes" in docs


def test_artifact_manifest_includes_usage_stability_hardening_packet() -> None:
    rows = artifact_manifest_rows()
    artifacts = {row["Artifact"]: row for row in rows}

    assert "Usage/Stability Lens Targeted Hardening V1" in artifacts
    assert artifacts["Usage/Stability Lens Targeted Hardening V1"]["Tracked"] == "yes"


def test_guardrail_ledger_includes_usage_stability_parking() -> None:
    rows = guardrail_ledger_rows()
    by_guardrail = {row["Guardrail"]: row for row in rows}

    assert "Usage/stability lens parking" in by_guardrail
    evidence = by_guardrail["Usage/stability lens parking"]["Evidence"]
    assert "Candidate status remains HOLD" in evidence
    assert "manual static-packet path" in evidence
