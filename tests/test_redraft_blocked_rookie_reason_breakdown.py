"""NWR full-cycle Worker 1 (data-issues-badge audit, 2026-09-16).

Real bug found while investigating the desktop "3 data issues" header
badge's "7 rookies remain blocked" item: every caller of the bundled
BLOCKED_2026_ROOKIES.csv block reasons asserted a single blanket phrase --
"position conflicts with the current factual registry" -- for all 7 real
blocked rows. Reading the actual CSV
(docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/
BLOCKED_2026_ROOKIES.csv) shows only 2 of the 7 rows are true draft-
position/current-position conflicts (Max Bredeson, Riley Nowakowski); 4
rows are blocked because the current factual roster status is not a
currently-rostered status (Joe Royer, Emmanuel Henderson Jr., Lewis Bond,
Anthony Smith); and 1 row (Jam Miller) is blocked because its exact current
identity is unresolved. This is a real, fixable text/classification-
accuracy bug (not a data-availability problem, and it does not touch the
governed valuation model, roster legality core rules, or the blocked-row
CSV data itself) -- `DesktopBackendFacade._blocked_seed_reason_breakdown`
now groups the already-parsed per-row `reason` field instead of
re-asserting the wrong blanket phrase everywhere it is surfaced (the
header-badge notice, the redraft_bootstrap warning, and the Data Health
readiness message).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.application.desktop_facade import (
    REDRAFT_SEED_BLOCKED_RELATIVE,
    DesktopBackendFacade,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_blocked_seed_reason_breakdown_groups_distinct_real_reasons() -> None:
    rows = [
        {"player": "Max Bredeson", "reason": "draft position conflicts with current factual registry position"},
        {"player": "Riley Nowakowski", "reason": "draft position conflicts with current factual registry position"},
        {"player": "Joe Royer", "reason": "current factual roster status is not a currently-rostered status"},
        {"player": "Emmanuel Henderson Jr.", "reason": "current factual roster status is not a currently-rostered status"},
        {"player": "Lewis Bond", "reason": "current factual roster status is not a currently-rostered status"},
        {"player": "Anthony Smith", "reason": "current factual roster status is not a currently-rostered status"},
        {"player": "Jam Miller", "reason": "exact current GSIS identity unresolved"},
    ]

    breakdown = DesktopBackendFacade._blocked_seed_reason_breakdown(rows)

    # The old code path would have summarized this entire set as one
    # blanket "position conflict" reason. The fix must surface all three
    # real, distinct reasons with their real counts.
    assert "2 rows -- draft position conflicts with current factual registry position" in breakdown
    assert "4 rows -- current factual roster status is not a currently-rostered status" in breakdown
    assert "1 row -- exact current GSIS identity unresolved" in breakdown


def test_blocked_seed_reason_breakdown_handles_missing_reason() -> None:
    breakdown = DesktopBackendFacade._blocked_seed_reason_breakdown(
        [{"player": "No Reason Player", "reason": ""}]
    )
    assert breakdown == "1 row -- reason not recorded"


def test_blocked_seed_reason_breakdown_empty_rows_is_empty_string() -> None:
    assert DesktopBackendFacade._blocked_seed_reason_breakdown([]) == ""


def test_real_bundled_blocked_rookies_csv_is_not_uniformly_position_conflict() -> None:
    """Guards against the real underlying mislabeling regressing: confirms
    the actual bundled CSV this whole feature reads from still contains a
    genuine mix of block reasons, not a uniform "position conflict" set --
    i.e. that fixing the message text was actually correcting a real
    inaccuracy and not inventing one."""
    path = REPO_ROOT / REDRAFT_SEED_BLOCKED_RELATIVE
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    blocked = frame.loc[frame["projection_status"].eq("BLOCKED")]
    reasons = set(blocked["block_reason"])
    assert len(reasons) > 1, (
        "Expected the real bundled blocked-rookie CSV to contain more than "
        "one distinct block_reason; if this now fails because the CSV was "
        "regenerated with a single uniform reason, the blanket wording this "
        "test guards against may be accurate again and this test can be "
        "revisited."
    )

    rows = [{"reason": reason} for reason in blocked["block_reason"]]
    breakdown = DesktopBackendFacade._blocked_seed_reason_breakdown(rows)
    # Every distinct real reason must appear in the breakdown -- nothing
    # collapsed back into one blanket phrase.
    for reason in reasons:
        assert reason in breakdown
