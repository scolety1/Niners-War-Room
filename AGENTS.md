# AGENTS.md - Niners Dynasty: War Room

You are building a private local-first fantasy football decision engine.

Primary build target:
V1 Drop Deadline Command Center.

Core constraints:
- Do not build a generic fantasy football app.
- Do not require live API calls at app runtime.
- Use local CSV and SQLite snapshots.
- Treat APIs only as optional data collection mechanisms.
- Keep formulas deterministic and testable.
- Keep UI simple, table-first, and low-text.
- Hide long explanations behind side panels.
- Separate Official Rank, Market Rank, War Room Rank, and My Rank.
- Do not hardcode player data except in sample fixtures.
- Do not scrape websites.
- Do not delete files outside the repository.
- Do not modify generated data packs unless explicitly asked.
- Do not overwrite old data packs. Create new dated snapshots.
- Do not implement complex ML in V1.
- Prioritize correctness over polish.

V1 must support:
- CSV import
- import review
- SQLite storage
- Niners roster page
- official top-5 release logic
- keeper/drop score
- pick value curve
- basic trade board
- league keeper pressure board

Testing requirements:
- Add tests for every model formula.
- Add tests for roster/ranking validation.
- Add tests for pick value calculations.
- Add tests for forced top-5 release rules.
- Add tests for import errors.

Current preferred stack:
- Python
- Streamlit
- SQLite
- pandas
- pydantic
- pytest
- ruff

Never assume unknown league rules. If a rule is unclear, represent it as configurable.
