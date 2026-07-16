# Focused and Regression Results

## Focused contracts

- Exact original nine nodes: `9 passed in 0.40s`; zero skipped; zero xfailed.
- Complete Player Board checklist plus trust-banner files: `26 passed in 0.55s`.
- Negative-control selection: `16 passed, 10 deselected in 0.20s`.
- Current `/rankings`, `/player-board`, title, Decision Trust Strip, legacy
  banners, Draft Prep gate, and collapsible details all pass their positive
  controls.

## Owning and adjacent regression

The prior 114-test selection was reproduced with the same files. The revision
adds 16 collected negative controls, so the selection now collects 130 tests.

Result: `116 passed, 14 skipped in 2.29s`.

The 14 skips are the unchanged `test_player_board_score_service.py`
missing-local-pack sentinels reported by the source and independent review.
Skip differential: zero. Xfail differential: zero. No focused or mutation
control is skipped or xfailed.

## Accessibility and presentation

The prior selection of `test_live_mock_draft_accessibility_compact.py`,
`test_player_compare_accessibility_compact.py`, and
`test_refresh_recovery_presentation_service.py` reports
`35 passed in 0.33s`.

## Static validation

- Python compileall over `app`, `src`, and `tests`: pass.
- Ruff on all three changed Python files: pass with zero findings.
- Full Ruff differential: accepted source 80 findings; revision 80 findings;
  zero new findings.
- `git diff --check`: pass.
