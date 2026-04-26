# Engineering Plan

## Milestones

1. Bootstrap repo and SQLite schema.
2. Implement CSV schema validation and data pack loading.
3. Implement pick value, player score, confidence, and keeper/drop engines.
4. Build Streamlit Import Review, Team, and War Board pages.
5. Build Trade Central, League Intel, and Draft Room V1.

## Task Slices

- Keep each Fleet task scoped to one subsystem.
- Add tests before or alongside formulas.
- Prefer small deterministic services over UI-first work.
- Do not change dependencies unless explicitly approved.

## Test Strategy

- `scripts/init_db.py` must create all local SQLite tables and indexes.
- `pytest` must cover formulas, validation, and roster rules.
- `ruff check .` must pass.
- `scripts/codex-static-check.ps1` is the Fleet acceptance command.

## Acceptance Criteria

- A sample 2026 data pack can be loaded.
- Imports are validated before acceptance.
- Niners top five is calculated from official rank.
- Pick values use the local 1,000-point scale.
- Keeper/drop and trade recommendations are deterministic.
- Streamlit pages load locally without live APIs.

## Rollback Plan

Revert the most recent git commit or Fleet task branch. Generated SQLite data under `data_packs/` is not committed and can be recreated from sample CSVs.
