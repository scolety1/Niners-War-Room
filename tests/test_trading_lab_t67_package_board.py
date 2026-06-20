from src.trading_lab.trade_comparison import (
    PACKAGE_BOARD_LABELS,
    comparison_rows_for_mode,
    package_board_summary_lines,
)


def test_package_comparison_rows_expose_required_labels() -> None:
    for expected in (
        "Rank",
        "Give",
        "Get",
        "NWR edge",
        "Market realism",
        "Primary warning",
        "Selected package explanation",
    ):
        assert expected in PACKAGE_BOARD_LABELS


def test_package_board_can_show_several_fixture_packages() -> None:
    rows = comparison_rows_for_mode("Trade For Player")

    assert len(rows) >= 2


def test_ranking_remains_deterministic() -> None:
    assert comparison_rows_for_mode("Trade For Player") == comparison_rows_for_mode(
        "Trade For Player"
    )


def test_warnings_appear_in_row_summary() -> None:
    lines = package_board_summary_lines("Trade For Player")

    assert any("Primary warning" in line for line in lines)


def test_no_real_integration_claims() -> None:
    text = " ".join(package_board_summary_lines("Trade For Player")).lower()

    for blocked in ("real integration wired", "real data loaded", "public source wired"):
        assert blocked not in text
