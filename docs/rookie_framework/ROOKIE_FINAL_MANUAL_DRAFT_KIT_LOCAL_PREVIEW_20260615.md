# Rookie Final Manual Draft Kit Local Preview

Date: 2026-06-16

Lane: Rookie framework only

## Executive Verdict

- Preview type created: HTML
- Streamlit available: no (`No module named streamlit`)
- Draft-kit source: frozen local/manual-use kit
- Main ranking formula changed: no
- Board order changed: no

This pass creates a standalone local browser preview for Tim to inspect the frozen Rookie Final Manual Draft Kit before draft day. The preview is local-only and reads the frozen kit exports from `local_exports/rookie_framework/final_manual_draft_kit_20260615/`.

No production app navigation, production ranking, private score, outcome column, hidden sort key, Outcome file, veteran file, probability, band, promoted artifact, tuning, rescoring, reorder, or v2 board was created.

## Files Created

- `scripts/rookie_framework/preview_rookie_final_manual_draft_kit.py`
- `tests/test_rookie_final_manual_draft_kit_preview.py`
- `docs/rookie_framework/ROOKIE_FINAL_MANUAL_DRAFT_KIT_LOCAL_PREVIEW_20260615.md`

## Local-Only Preview Export

Created:

- `local_exports/rookie_framework/final_manual_draft_kit_20260615/preview/index.html`

The HTML preview includes:

- Final board
- Draft-day quick sheet
- Tier cards
- Manual decision checklist
- Warning-priority sheet
- Filters for position, tier, warning severity, and draft action
- Banner: `Manual-use rookie draft kit only. Not production rankings.`

## How To Open

Open this local file in a browser:

`C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies\local_exports\rookie_framework\final_manual_draft_kit_20260615\preview\index.html`

Rebuild command:

```powershell
python scripts\rookie_framework\preview_rookie_final_manual_draft_kit.py --build-html
```

Streamlit command if Streamlit is installed later:

```powershell
streamlit run scripts\rookie_framework\preview_rookie_final_manual_draft_kit.py
```

In this run, Streamlit was unavailable, so the HTML preview is the usable preview artifact.

## Source Kit Inputs

- `local_exports/rookie_framework/final_manual_draft_kit_20260615/rookie_2026_final_manual_draft_board_frozen_20260615.csv`
- `local_exports/rookie_framework/final_manual_draft_kit_20260615/rookie_2026_draft_day_quick_sheet_20260615.csv`
- `local_exports/rookie_framework/final_manual_draft_kit_20260615/rookie_2026_tier_cards_20260615.csv`
- `local_exports/rookie_framework/final_manual_draft_kit_20260615/rookie_2026_manual_decisions_checklist_20260615.csv`
- `local_exports/rookie_framework/final_manual_draft_kit_20260615/rookie_2026_warning_priority_sheet_20260615.csv`

## Preview Safety

- Local preview only: PASS
- No production app wiring: PASS
- No production ranking change: PASS
- No private score change: PASS
- No outcome column change: PASS
- No hidden sort key: PASS
- No Outcome/veteran file touched: PASS
- No probabilities, bands, promoted artifacts: PASS
- No tuning, rescoring, reorder, or v2 board: PASS
- `data/` not committed: PASS
- `local_exports/` not committed: PASS

## Validation Commands

- `git status --short`
- `git branch --show-current`
- `git rev-parse HEAD`
- `python -c "import streamlit"`
- `python -m py_compile scripts\rookie_framework\preview_rookie_final_manual_draft_kit.py tests\test_rookie_final_manual_draft_kit_preview.py`
- `python tests\test_rookie_final_manual_draft_kit_preview.py`
- `python scripts\rookie_framework\preview_rookie_final_manual_draft_kit.py --build-html`
- `python -m pytest tests\test_rookie_final_manual_draft_kit_preview.py -q`
- HTML existence/banner/filter checks
- `git diff --check`

Result: direct preview harness, static HTML build, HTML existence/banner/filter checks, and `git diff --check` passed. `pytest` was unavailable in the active Python environment (`No module named pytest`), so the direct harness result was used.

## Final Recommendation

Use the static HTML preview for local draft-kit review. It is the right artifact for Tim to inspect the frozen kit without changing model logic or touching production app surfaces.
