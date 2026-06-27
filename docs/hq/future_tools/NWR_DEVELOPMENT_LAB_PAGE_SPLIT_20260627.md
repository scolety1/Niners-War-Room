# NWR Development Lab Page Split - 2026-06-27

## Verdict

GREEN feature lane: the Safe V0 Future Tools were split into a Development Lab section with separate manual/display-only pages. No model, ranking, source-truth, or decision-page gates were opened.

## Final navigation structure

Draft:
- Live Draft
- Mock Drafts
- Draft Analyzer

Research:
- Dynasty Rankings
- Player Compare
- Trading Lab

Development Lab:
- Lab Home
- Roster Weakness Tracker
- Future Pick Planning
- Keeper Deadline Prep
- Drop Deadline Prep
- Trade Deadline Prep
- Future Tools

Admin:
- Refresh Data
- Evidence Review
- Settings / Data Health

## Page split

- `/development-lab`: control board for Safe V0 lab tools, blocked/gated tools, and guardrails.
- `/roster-weakness-tracker`: manual roster structure counts and coverage notes only.
- `/future-pick-planning`: planning ledger from manual notes and existing live draft runtime trade events only.
- `/keeper-deadline-prep`: manual keeper deadline checklist.
- `/drop-deadline-prep`: manual drop deadline checklist.
- `/trade-deadline-prep`: manual trade deadline checklist with links to Trading Lab and Player Compare.
- `/future-tools`: roadmap-only ideas page for blocked/gated tools.

## Guardrails preserved

- Development Lab tools are Safe V0, display-only, and manual workflow.
- Future Tools is roadmap-only and does not render active Safe V0 controls.
- No start/sit, waiver, in-season ranking, trade-target, playoff, rookie-class, pick-valuation, or trade-valuation logic was added.
- DynastyProcess, ADP, market, CFBD, NFL usage, Gmail, vendor, proxy, and Outcome evidence remain outside model input.
- Frozen board, tiers, Dynasty Rank, Final Board Rank, pinned snapshot, latest candidate, latest approved, and production model/rank logic were not changed.

## Validation

Focused tests:
- `tests/test_navigation_compression.py`
- `tests/test_future_tools_page.py`
- `tests/test_future_tools_rd_service.py`

Additional validation:
- Ruff on touched Python files passed.
- Python compile on touched Python files passed.
- `git diff --check` passed.
- Browser route smoke passed for `/development-lab`, `/roster-weakness-tracker`, `/future-pick-planning`, `/keeper-deadline-prep`, `/drop-deadline-prep`, `/trade-deadline-prep`, `/future-tools`, `/live-draft-room`, `/mock-draft`, `/draft-analyzer`, `/rankings`, and `/settings-data-health`.

## Remaining caveats

- Safe V0 lab tools are not persisted; manual notes can be downloaded but are not stored.
- Future Pick Planning reads live draft runtime trade events as manual/local context only, not official source truth.
- Blocked/gated roadmap tools remain inactive until a future explicit data/model/source approval gate is opened.
- Streamlit still treats the default Live Draft page as the app fallback. The Live Draft route rendered correctly in smoke, but the DOM can include Streamlit's generic fallback text; no Python traceback was observed.
