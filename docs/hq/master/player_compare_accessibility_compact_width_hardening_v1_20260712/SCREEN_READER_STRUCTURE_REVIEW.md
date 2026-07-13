# Screen-Reader Structure Review

## Result

PASS with native Streamlit dataframe semantics retained.

## Heading tree

- H1: Player Compare.
- H2: Choose players.
- H2: Selected-player context.
- H2: Visible Context Summary.
- H2: Evidence caveats and trust context.
- H3: How to use this comparison.
- H2: Secondary comparison details.

The existing visual title remains generic presentation, while one visually hidden semantic H1 provides the programmatic page heading. The hidden heading stays in DOM order and is not hidden with `display:none` or `visibility:hidden`.

## Names and states

- Combobox names are `Player A selector`, `Player B selector`, and `Optional extra players`.
- Selected context reads `Player A — selected` and `Player B — selected`, followed by their existing display labels.
- Partial synthetic context reads `not selected` and `No player selected` rather than using color or an empty placeholder.
- Trust disclosures are named `Evidence details — <selected player>`.
- Missing, stale, gated, unavailable, identity exception, source exception, and not-enough-information states remain canonical text in trust tables.

## Tables and disclosures

Existing visible headings/captions remain adjacent to every primary/detail dataframe group. Native dataframe toolbar controls expose their names in the accessibility snapshot. Wide data remains in the same dataframe and is not truncated or replaced. Trust tables are inside named native disclosures with an explicit keyboard/status caption.

## Reading order

Selection controls precede selected summaries. Primary evidence precedes trust and caveats. Trust and how-to-use context precede the secondary detail tabs. This sequence passed DOM index checks at every required viewport.

## Non-color result

A/B identity, selection state, missingness, freshness, gating, warnings, identity exceptions, source exceptions, and unavailable states all include text. Existing markers/colors are redundant cues only.
