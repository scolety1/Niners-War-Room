import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/LEGACY_VS_CURRENT_SENTINEL_EXPANSION_20260605.md"
ACTIVE_PACK = ROOT / "local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/model_outputs.csv"
CURRENT_ROWS = (
    ROOT
    / "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv"
)


def _active_pack_rows() -> dict[str, dict[str, str]]:
    with ACTIVE_PACK.open(newline="", encoding="utf-8-sig") as handle:
        return {row["player_name"]: row for row in csv.DictReader(handle)}


def _current_rows() -> dict[str, dict[str, str]]:
    with CURRENT_ROWS.open(newline="", encoding="utf-8-sig") as handle:
        return {row["player_name"]: row for row in csv.DictReader(handle)}


def test_legacy_sentinel_report_discloses_comparison_only_sources():
    text = REPORT.read_text(encoding="utf-8")

    assert "lve_sleeper_20260505_pdf_ranks/model_outputs.csv" in text
    assert "private_score" in text
    assert "veteran_lve_stats_first_v1_0_0" in text
    assert "legacy_active_pack" in text
    assert "current_player_value_review_rows.csv" in text
    assert "checkpoint_review_score" in text
    assert "comparison-only" in text
    assert "not a primary value" in text
    assert "not a ranking value" in text
    assert "not a recommendation signal" in text


def test_legacy_sentinel_report_has_twenty_five_sentinel_rows():
    text = REPORT.read_text(encoding="utf-8")
    sentinel_lines = [
        line
        for line in text.splitlines()
        if line.startswith("| S") and "Legacy Active-Pack Score" not in line
    ]

    assert len(sentinel_lines) == 25
    assert any("| S24 | Keenan Allen |" in line for line in sentinel_lines)
    assert any("| S25 | Darius Slayton |" in line for line in sentinel_lines)


def test_legacy_sentinel_report_matches_known_handoff_values():
    text = REPORT.read_text(encoding="utf-8")
    active_rows = _active_pack_rows()
    current_rows = _current_rows()

    assert float(active_rows["Keenan Allen"]["private_score"]) == 82.4
    assert float(current_rows["Keenan Allen"]["checkpoint_review_score"]) == 41.6097
    assert "| S24 | Keenan Allen | WR | 78 | 82.40 | 30 | 41.6097 |" in text

    assert float(active_rows["Darius Slayton"]["private_score"]) == 78.88
    assert "Darius Slayton" not in current_rows
    assert "| S25 | Darius Slayton | WR | 88 | 78.88 | missing | blank | n/a |" in text
    assert "manual_required_no_model_v4_current_player" in text


def test_legacy_sentinel_report_preserves_no_formula_and_no_routing_change_guardrails():
    text = REPORT.read_text(encoding="utf-8")

    assert "does not change source routing" in text
    assert "Do not change source-routing behavior" in text
    assert "Do not tune 1QB caps" in text
    assert "Do not import market, ADP, rankings, projections, consensus, startup" in text
    assert "Do not convert these rows into trade, cut, keep, draft" in text
