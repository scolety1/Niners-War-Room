# Visual and Accessibility Review

The representative Streamlit AppTest fixture covers valid/current, stale, missing, gated, unavailable, identity exception, source exception, and not enough information. It verifies compact text summaries and expandable details.

Result:

- Seven representative entity disclosures rendered without exception; the eighth not-enough-information state is covered by service/schema tests and fixture matrix.
- Status labels remain understandable without color.
- Symbols supplement text and never replace it.
- `st.expander` provides the existing keyboard disclosure behavior and logical document focus order.
- No custom focus management or CSS was added; no focus trap exists.
- Compact captions add one collapsed line per entity and do not change ranking-table rows.
- Expanded details remain inside responsive Streamlit containers and do not overlay neighboring content.
- All surfaces use the same field labels and state vocabulary.

Minor caveat: large four-player comparisons or multi-asset packages create multiple compact lines by design. This is bounded by existing selection limits and is not a decision or data issue.

Result: `PASS_WITH_MINOR_DENSITY_CAVEAT`.
