from src.trading_lab.trade_comparison import (
    COMPARISON_COLUMNS,
    build_package_comparison_rows,
    comparison_rows_for_mode,
)
from src.trading_lab.trade_lab_ui import packages_for_mode


def test_comparison_rows_build_from_candidate_packages() -> None:
    rows = comparison_rows_for_mode("Trade For Player")

    assert rows
    assert rows[0].give
    assert rows[0].get


def test_sorting_is_stable_and_deterministic() -> None:
    first = comparison_rows_for_mode("Trade For Player")
    second = comparison_rows_for_mode("Trade For Player")

    assert first == second
    assert first[0].rank == 1


def test_all_required_columns_exist() -> None:
    assert COMPARISON_COLUMNS == (
        "rank",
        "give",
        "get",
        "NWR gain",
        "public market fairness",
        "opponent fit",
        "roster impact",
        "keeper/drop impact",
        "risk",
        "verdict",
        "primary warning",
    )


def test_best_package_is_first_for_fixture_data() -> None:
    packages = packages_for_mode("Trade For Player")
    rows = build_package_comparison_rows(packages)

    assert rows[0].nwr_gain == max(package.nwr_gain for package in packages)


def test_no_real_integration_required() -> None:
    text = repr(comparison_rows_for_mode("Trade For Player")).lower()

    for blocked in ("http", "fetch", "data/", "local_exports", "real integration is wired"):
        assert blocked not in text
