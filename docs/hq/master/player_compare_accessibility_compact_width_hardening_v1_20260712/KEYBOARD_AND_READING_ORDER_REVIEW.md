# Keyboard and Reading-Order Review

## Result

PASS for native-control structure, visible focus, deterministic DOM order, and absence of custom keyboard traps/shortcuts.

## Control order

The rendered DOM and page source agree on this order:

1. Player A selector.
2. Player B selector.
3. Optional extra players.
4. Selected-player context.
5. Primary Visible Context Summary and its native dataframe tools.
6. Advanced visible-context disclosure.
7. Per-player evidence detail disclosures.
8. Secondary detail tabs and their native controls.

No source code adds `keydown`, `keypress`, custom shortcut, hover-only action, focus-loop, or programmatic focus-restoration behavior.

## Native control evidence

- Player A and Player B expose unique `combobox` roles and names.
- Optional players expose the existing Streamlit multi-combobox.
- Evidence details render as native `details` with focusable `summary` children.
- Secondary details retain native tab roles and existing tab names/order.
- Dataframe toolbar actions retain Show/hide columns, Download as CSV, Search, and Fullscreen names.

## Focus evidence

At 375 × 812 the Player A combobox measured 295 × 44 CSS pixels while focused. Computed focus outline was `rgb(0, 95, 204) solid 3px`. A focused evidence summary exposed the same 3px outline. The focus indication is supplemental; A/B and state meaning remain text.

## Disclosure evidence and limitation

The real Player Compare trust disclosure was uniquely located, expanded, visibly focused, and rendered its complete canonical table without a page overflow. The in-app browser backend did not produce a reliable state change from synthesized Enter/Tab key events, so this packet does not claim automation-backed focus restoration or a key-event trace. Keyboard-operability acceptance rests on native `details/summary` DOM, unique names, visible focus, unchanged Streamlit interaction, focused source tests, and absence of interception code.

## Reading-order result

The browser snapshot exposed: level-one Player Compare; level-two Choose players; level-two Selected-player context; level-two Visible Context Summary; level-two Evidence caveats and trust context; level-three How to use this comparison; level-two Secondary comparison details. The relative-order checks passed at all four viewports.
