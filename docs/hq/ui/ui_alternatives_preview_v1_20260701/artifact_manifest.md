# NWR UI Alternatives Preview V1 Artifact Manifest

Branch: `work/ui-alternatives-preview-v1-20260701`

Base branch: `origin/work/hq-parallel-control`

Base HEAD: `a85e35a02bf5800be8ef42af6428d5ec0b0f298f`

Purpose: create a review-only UI preview lane named `UI Alternatives Preview` so Tim can compare possible UI upgrades side-by-side without changing production rankings, model behavior, source truth, runtime data, or default rank logic.

## App Files

- `app/pages/45_ui_alternatives_preview_v1.py`
- `app/components/ui_alternatives_preview.py`
- `app/navigation.py`

## Test Files

- `tests/test_ui_alternatives_preview_page.py`
- `tests/test_navigation_compression.py`

## Required Artifacts

- `artifact_manifest.md`
- `ui_alternatives_preview_summary.md`
- `current_ui_preservation_notes.md`
- `alternative_a_compact_review_cards.md`
- `alternative_b_evidence_first_layout.md`
- `alternative_c_lab_console_layout.md`
- `side_by_side_comparison.md`
- `screenshots_or_route_smoke_report.md`
- `guardrail_report.md`
- `merge_safety_report.md`
- `next_phase_handoff.md`

## Guardrail Status

GREEN. This lane adds only a static review UI route, navigation entry, tests, and documentation. It does not change production formulas, model training, model tuning, ranking logic, hidden sort, recommendations, source truth, runtime data sources, or default app page behavior.

## Validation Snapshot

- Focused tests: `22 passed`.
- Ruff focused check: PASS.
- Page/import compile: PASS.
- HTTP route smoke: PASS for `/ui-alternatives-preview`, `/rankings`, `/player-compare`, `/trading-lab`, `/development-lab`, `/settings-data-health`, and `/draft-cockpit`.
- Streamlit AppTest render smoke: PASS with zero exceptions for preview and representative default pages.
- `git diff --check`: PASS.
- `git diff --cached --check`: PASS.
- Protected app/model/rank/source-truth scan: PASS.
- Forbidden raw/shared/cache/local/secrets path scan: PASS.
