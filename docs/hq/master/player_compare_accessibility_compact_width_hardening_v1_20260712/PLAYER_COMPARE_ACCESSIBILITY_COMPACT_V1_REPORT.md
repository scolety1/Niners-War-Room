# Player Compare Accessibility and Compact-Width Hardening V1 Report

## Control state

- Controlling remote branch: `work/hq-parallel-control`
- Expected HQ: `e949c5647001f84dba29195c589e27d923722ea1`
- Fetched live HQ: `e949c5647001f84dba29195c589e27d923722ea1`
- Remote advance: none
- Worktree: `C:\NWR\Niners-War-Room-player-compare-accessibility-compact-v1-20260712`
- Branch: `work/player-compare-accessibility-compact-v1-20260712`
- Push: prohibited and not performed

## Outcome

`GREEN_PLAYER_COMPARE_ACCESSIBILITY_COMPACT_V1_READY_FOR_HQ_REVIEW`

The implementation reuses the existing Player Compare selection/data path, visible-context summary services, Streamlit dataframes/tabs/expanders, and independent per-player Decision Trust Strips. It adds a page-local semantic and responsive frame, explicit selector labels, visible Player A/B selected context, compact target sizing, focus-visible styling, and a corrected information order.

No comparison calculation, identity join, player population, selection default, duplicate exclusion, displayed field, rank, score, formula, recommendation, source state, missingness state, refresh behavior, or trust fact changed.

## Presentation changes

1. Added a semantic level-one `Player Compare` heading while retaining the existing visual header.
2. Added level-two regions: Choose players, Selected-player context, Visible Context Summary, Evidence caveats and trust context, and Secondary comparison details.
3. Renamed visible/native selector labels to `Player A selector` and `Player B selector` without changing keys, values, options, indices, or callbacks.
4. Added text-only selected-slot summaries using the already selected labels; no identity lookup or fallback is performed.
5. Repositioned the unchanged trust-strip render after primary evidence, as permitted by the compact-layout contract.
6. Moved the existing how-to-use copy after trust context and before secondary tabs.
7. Added page-scoped CSS at 900px and below to stack Streamlit columns, provide 44px targets, wrap metric/tab/disclosure text, expose focus, and constrain dataframe containers.
8. Kept desktop two-column selectors and four-metric summary behavior above 900px.

## Real viewport results

| Viewport | Document scroll/client | Main scroll/client | Overflow | Selectors | Clipped text | Dataframes |
| --- | --- | --- | --- | --- | --- | --- |
| 320 × 700 | 320 / 320 | 310 / 310 | none | stacked; 286px wide each | 0 | 6 visible; all contained; internal scroll present |
| 375 × 812 | 375 / 375 | 365 / 365 | none | stacked; 341px wide each | 0 | 6 visible; all contained; internal scroll present |
| 768 × 1024 | 768 / 768 | 758 / 758 | none | stacked; 726px wide each | 0 | 6 visible; all contained; internal scroll present |
| 1440 × 1000 | 1440 / 1440 | 1430 / 1430 | none | two columns; 627px wide each | 0 | 6 visible; all contained; internal scroll present |

The widest measured internal dataframe content was 2,562 CSS pixels. It remained inside a 286px, 341px, 726px, or 1,270px outer dataframe container depending on viewport.

## Accessibility result

- Accessible selector names: pass.
- Player A/B distinction without color: pass; slot, state, and selected label are text.
- Semantic heading structure: pass; one level-one heading followed by ordered level-two regions.
- DOM reading order: pass; selection → selected context → primary evidence → trust/caveats → secondary details.
- Native keyboard controls: pass by component and DOM contract; selectors are comboboxes, disclosures are `details/summary`, tabs retain tab roles.
- Visible focus: pass; browser measured a 3px `rgb(0, 95, 204)` focus-visible outline on the Player A combobox and disclosure summary.
- Focus trap/custom shortcut/hover dependency: none added or found in scoped source.
- Compact touch targets: selectors, disclosure summaries, dataframe tools, and tabs measured at least 44px high and 44px wide where both dimensions apply.
- Text wrapping/clipping: no clipped paragraph, label, tab, button, or summary text detected at any required viewport.
- Stat-table context: existing adjacent headings/captions retained; native dataframe toolbar names remained visible to the accessibility snapshot.
- Programmatic focus restoration: not claimed.

## Semantic equivalence

The canonical snapshot covers the selected labels/order, ID fields, 84 compare columns and records, visible-context summary, decision rows, and both independent trust strips. Baseline and post hashes match exactly at `97b15a7ebdbe3f079c4743c398a3a9bd1061e0467482f4431f5a4d098fdcb9f3`.

The current default fixture rows have blank `player_id` values in existing source data. This lane does not infer, create, or fall back to a player identity; it merely repeats the already selected display labels in presentation-only context.

## Testing and evidence

- 22 focused accessibility/compact tests passed.
- 94 existing Player Compare, comparison-service, Decision Trust Strip, injury/availability, navigation, compile/import, and guardrail regressions passed.
- Real-route smoke passed at all four required viewports.
- Nine JPEG artifacts cover four real viewports, real expanded trust evidence, and clearly synthetic partial, missing/gated, long-label, and large-table states.
- Python compilation and scoped Ruff validation passed.
- Documentation JSON/CSV/image/manifest and protected-path validations are recorded in `VALIDATION_RESULTS.md`.

## Known caveats

- Production selection behavior remains unchanged and requires two players when at least two are available. Partial/empty selection representation is tested synthetically only.
- A fresh direct-route session can display Streamlit's pre-existing `Page not found` notice while the registered Player Compare content is present; navigation registration and route files are unchanged.
- Existing Streamlit `use_container_width` deprecation warnings remain. Repairing shared dataframe calls is outside this lane.
- The browser backend did not provide a reliable synthesized Enter/Tab state transition for native controls, so the keyboard proof uses native DOM roles/elements, unique accessible names, visible focus, source review, and focused tests. No focus-restoration claim is made.

## Rollback readiness

One local commit is the rollback unit. Reverting it removes the page import/order/label changes, the page-only helper, focused tests/fixtures, and this packet without touching HQ, shared trust semantics, data, or frozen artifacts.
