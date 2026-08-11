# Validation

- Start authority: canonical HQ `4f431ccf46e91720095c93aa2ae65bbd1af539f7`, tree
  `02df67aa31542dd5fe8e92864f06c1d09505a97c`.
- Python compile and Ruff: pass for changed application, service, and test files.
- Focused owner/navigation tests: 24 passed.
- Broader owner, trade, outcome, personal workspace, rankings, player-detail, and Redraft regression
  set: 182 passed.
- Streamlit AppTest: 11 owner pages, zero exceptions.
- Browser desktop route audit: 12 known owner routes, one H1 each after settled load, no traceback, no
  document-level overflow. All Dynasty Assets required its normal longer governed-data settle time.
- Browser mobile route audit: six highest-risk surfaces at 390x844, no traceback or overflow.
- Browser visual correction: metric contrast defect found, fixed, and rechecked through computed style.

The unrestricted repository-wide run exceeded the five-minute command bound without emitting an
Owner Mode failure. In the uncommitted implementation worktree, a bounded `pytest -q -x` run passed
44 tests and then correctly reached a guard requiring no `app/` changes.

The same `pytest -q -x` command was rerun from a clean detached post-commit review worktree. It passed
148 tests, including the clean-tree guard, and then stopped at the known local fixture boundary:
`local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` is intentionally
not present in an isolated Git worktree. A second fresh-worktree AppTest run executed all 11 owner
pages with zero exceptions and left the review worktree clean.
