from dataclasses import replace

from src.trading_lab.trade_comparison import comparison_rows_for_mode
from src.trading_lab.trade_lab_ui import packages_for_mode
from src.trading_lab.trade_layout import (
    compact_negotiation_note,
    compact_package_row,
    format_asset_name,
    format_warning_stack,
    no_package_layout_message,
    provider_status_panel_labels,
)


def test_long_fake_names_are_accepted_and_formatted() -> None:
    name = "Very Long Fixture Player Name With Extra Context And Review Notes"

    formatted = format_asset_name(name, max_length=30)

    assert formatted.endswith("...")
    assert len(formatted) == 30


def test_no_package_fallback_is_present() -> None:
    assert "No fixture-backed packages available" in no_package_layout_message("Trade For Player")


def test_many_warnings_are_handled() -> None:
    warnings = tuple(f"warning {index}" for index in range(8))
    formatted = format_warning_stack(warnings, limit=3)

    assert len(formatted) == 4
    assert formatted[-1] == "+5 more warnings for manual review"


def test_package_comparison_can_handle_several_rows() -> None:
    rows = comparison_rows_for_mode("Trade For Player")

    assert len(rows) >= 2
    assert rows[0].rank == 1


def test_compact_package_row_handles_long_values() -> None:
    package = packages_for_mode("Trade For Player")[0]
    long_package = replace(
        package,
        give=("Very Long Fixture Player Name With Extra Context",),
        warnings=tuple(f"warning {index}" for index in range(5)),
    )
    row = compact_package_row(long_package, rank=1)

    assert row.give.endswith("...")
    assert "more warnings" in row.primary_warning


def test_long_negotiation_notes_are_compacted() -> None:
    note = "This is a very long fixture negotiation note that should be shortened for display."

    assert compact_negotiation_note(note, max_length=35).endswith("...")


def test_no_layout_helper_assumes_real_data() -> None:
    labels = provider_status_panel_labels(("missing-placeholder", "fixture-only"))
    text = " ".join(labels).lower()

    assert "Provider status: missing-placeholder" in labels
    assert "real data" not in text
