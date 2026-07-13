# Representative Render Review

All JPEGs are stored under `rendered_evidence/`. Files beginning `real_` use the actual `player-compare` route and existing data. Files beginning `synthetic_` display a prominent `SYNTHETIC TEST FIXTURE` warning and contain no production facts.

| Artifact | Review result |
| --- | --- |
| `real_player_compare_1440x1000_two_players.jpg` | Desktop two-column selectors and two text-labeled selected summaries preserved. |
| `real_player_compare_768x1024_two_players.jpg` | Selectors stack at 768; selected context follows in source order. |
| `real_player_compare_375x812_two_players.jpg` | Player A/B controls, labels, selected values, context, and primary heading remain visible without horizontal overflow. |
| `real_player_compare_320x700_two_players.jpg` | Same compact stack at 320; no control/label clipping. |
| `real_player_compare_375x812_expanded_evidence.jpg` | Real trust disclosure expanded; canonical table contained and internally scrollable. |
| `synthetic_partial_selection_375x812.jpg` | Player A selected and Player B not selected are explicit text states. |
| `synthetic_missing_gated_states_375x812.jpg` | Gated, stale, identity-exception, missing, and source-exception text is visible in the shared trust table. |
| `synthetic_long_label_large_table_320x700.jpg` | Long label is complete and wraps; no abbreviation or identity fallback. |
| `synthetic_large_table_320x700.jpg` | Large native dataframe remains inside a 278px outer container with 320/320 document width. |

## Browser measurements

`VIEWPORT_MEASUREMENTS.json` records exact document/main widths, selector rectangles, stacking, heading order, target sizes, clipping detection, and dataframe containment. It reports zero page/main overflow and zero clipped text at every required viewport.

## Visual caveats

The screenshots are viewport evidence, not information-removal mockups. Streamlit's main section is the vertical scroll surface, so compact captures intentionally scroll to the relevant controls/summary or trust disclosure while leaving all page information present.
