# Compact-Width Layout Contract

## Scope

The contract is activated only when the DOM contains `#nwr-player-compare-page`. No global app-shell file is changed.

## Width behavior

- Above 900 CSS pixels: retain the existing desktop layout—two selector columns, four summary metrics, two context columns, wrapped native tabs, and native dataframe containment.
- At or below 900 CSS pixels: every Streamlit `stColumn` on Player Compare becomes a deterministic 100%-width row in source order.
- Page-level width must equal client width. The main Streamlit scroll surface must also have equal scroll and client width.
- Dense tables remain Streamlit dataframes. Their outer containers must stay within the page while existing internal grid scroll handles dense columns.
- No comparison information, tab, disclosure, or table column may be removed solely for a narrower screenshot.

## Control behavior

- Player A selector precedes Player B selector; optional players follow.
- Player A and Player B selected-context text follows controls and precedes comparison evidence.
- Selector comboboxes/buttons, help control, dataframe toolbar buttons, tab controls, and disclosure summaries receive a compact minimum target of 44 CSS pixels.
- Focus-visible outlines use 3px solid `#005fcc` with 2px offset.
- Metric values, tab text, and disclosure text use normal white-space and non-ellipsis wrapping.

## Evidence order

1. Page heading and purpose.
2. Choose players.
3. Selected-player context.
4. Visible Context Summary.
5. Evidence caveats and trust context.
6. How-to-use guidance and secondary details.

## Measured acceptance

320, 375, and 768px: selectors stacked; zero document/main horizontal overflow; zero detected text clipping; all visible tables contained; compact target groups met 44px thresholds.

1440px: selectors remain two-column; zero overflow/clipping; existing desktop data presentation remains complete.
