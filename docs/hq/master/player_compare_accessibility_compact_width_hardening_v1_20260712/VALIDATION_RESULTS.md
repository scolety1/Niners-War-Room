# Validation Results

## Repository control

- `git fetch --all --prune`: pass.
- Live `origin/work/hq-parallel-control`: `e949c5647001f84dba29195c589e27d923722ea1`.
- Expected/live comparison: equal; no intervening commits.
- Isolated branch/worktree: pass.

## Tests

- Focused compact/accessibility suite: 22 passed in 0.59 seconds.
- Existing scoped regression suite: 94 passed in 7.52 seconds.
- Covered Player Compare safe context, NFLVerse context, display-only NGS, decision service, comparison service, Decision Trust Strip surfaces/service/render, injury/availability, navigation, original UX guardrails, drafting-mode route constraints, compile/import guardrails.
- First regression attempt: 83 passed, 2 failed, 9 errored only because pytest/`py_compile` could not write to the read-only worktree/global temp. Identical rerun with approved `--basetemp` and `PYTHONPYCACHEPREFIX` passed 94/94.
- No skip, xfail, weakening, or test deletion.

## Browser and accessibility

- Real route 320 × 700: pass; document 320/320, main 310/310, no overflow, stacked selectors, zero clipping.
- Real route 375 × 812: pass; document 375/375, main 365/365, no overflow, stacked selectors, zero clipping.
- Real route 768 × 1024: pass; document 768/768, main 758/758, no overflow, stacked selectors, zero clipping.
- Real route 1440 × 1000: pass; document 1440/1440, main 1430/1430, no overflow, two-column selectors, zero clipping.
- Visible dataframes: 6 at each viewport; all page-contained; bounded internal scrolling detected; maximum internal width 2,562px.
- Compact target groups: selectors, disclosures, dataframe tools, and tabs had zero under-44 targets in measured groups.
- Accessibility snapshot: one H1; ordered H2 regions; explicit combobox names; text A/B distinction; native disclosure/tab roles.
- Focus: 3px visible outline measured.
- Route smoke: real Player Compare content and controls rendered at all four viewports.

## Semantic and trust protection

- Baseline/post semantic SHA-256: `97b15a7ebdbe3f079c4743c398a3a9bd1061e0467482f4431f5a4d098fdcb9f3` / same.
- Compare records/columns: 2 / 84; exact.
- Trust strips: 2 independent strips; exact field/state sequences.
- Shared trust component/service blobs: unchanged.
- Comparison service blobs: unchanged.

## Static quality

- Python `py_compile` for changed Python files: pass with bytecode redirected to approved temp.
- Ruff for changed Python files: pass with cache disabled.
- `git diff --check`: pass.
- `git diff --cached --check`: pass after staging.

## Packet and scope

- Required documentation files: 16/16 present and non-empty.
- Documentation CSV parse and duplicate-header/key checks: pass.
- JSON parse: pass.
- Image inventory: 9 JPEGs, all non-empty, extension/format-matched, and within packet.
- Manifest path/hash/size validation: pass.
- Protected/frozen domain diff scan: pass; no changed protected path.
- Trading Lab no-change: pass; baseline/current page blob identical.
- Ranking/formula/source-registry/plugin/rookie/draft/data diff scan: pass.

## Existing unrelated baseline observations

- Streamlit emits existing `use_container_width` deprecation warnings on legacy dataframe calls.
- A fresh direct-route startup can show Streamlit's pre-existing route notice before registered Player Compare content settles; navigation files and route semantics are unchanged.
- These observations were documented, not repaired in this lane.
