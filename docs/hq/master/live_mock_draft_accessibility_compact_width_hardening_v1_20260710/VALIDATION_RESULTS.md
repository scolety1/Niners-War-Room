# Validation Results

## Commands and totals

1. `git fetch --all --prune` — PASS; remote HQ resolved to `73cadea025ec582a976ec68d1ef5232e032167e2`; no advance.
2. Python `-m py_compile` for the three implementation files and focused test — PASS.
3. Focused pytest command covering accessibility, compact layout, workflow, runtime state, mock room, and mock storage — **70 passed**.
4. Expanded pytest command covering Live/Mock pages, cockpit, assignment/undo/remove, runtime/persistence, draft services, UX, navigation, ranking consumers, and route contracts — **235 passed**.
5. `python -m ruff check` on changed Python files — PASS.
6. In-app browser `/draft-cockpit` and `/mock-draft` at 1440×1000 and 390×844 — PASS.
7. Browser page-overflow read: Live 1440 `1440=1440`; Live 390 `390=390`; Mock 1440 `1440=1440`; Mock 390 `390=390` — PASS.
8. Compact primary assign width: 356px at x=12 with right edge 368 in a 390px viewport — PASS.
9. Native disclosure inspection and expanded-detail capture — PASS; automated key dispatch limitation recorded in keyboard review.
10. `git diff --check` and staged equivalent — PASS at final validation.
11. Documentation CSV parse, JSON duplicate-key parse, required-file manifest, relative-link and evidence existence checks — PASS at final validation.
12. Protected/frozen/ranking/formula/recommendation/source/draft-logic/persistence/Decision Trust Strip/Refresh Recovery path scans — zero prohibited changes.

## Route smoke

Both direct routes rendered their expected headings, shared primary labels, current-pick text, selected-player text, draft board, player table, and secondary context. The Streamlit direct Live route displayed a transient framework `Page not found` fallback dialog after server restart; dismissing it left the correctly registered Draft Cockpit route. Navigation registration tests passed, and Mock opened directly without that transient.

## Final command recording

Exact final commands and commit hash are recorded in the final lane response and repository commit metadata. No test was skipped, weakened, xfailed, or rewritten solely to mask a failure.
