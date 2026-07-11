# Compact-Width Layout Contract

Target viewport: 390×844; desktop reference: 1440×1000.

1. Current pick, current drafting team, and draft status are expressed in text before dense tables.
2. Filter/sort controls retain their original values and callbacks inside the native `Filter and sort players` disclosure.
3. Player and pick selectors, selected context, assign, undo, and edit/remove disclosure precede the dense player table in DOM/render order.
4. Existing global Streamlit breakpoint behavior stacks columns to 100% width below 760px.
5. Primary buttons use container width and may wrap text; they must not clip or create page overflow.
6. Draft board and player dataframes remain width-contained and may scroll internally.
7. Reset/runtime controls and secondary rails remain below the primary workflow and separated from assignment.
8. No columns, filters, sort modes, data, or desktop behavior are removed.

Measured browser results: document `scrollWidth == clientWidth` at 390 and 1440 on both routes. At 390, the visible assignment button measured 356px from x=12 to right=368. Dataframe containers stayed within the content width while their internal scroll widths exceeded client widths by a small amount, confirming contained internal scrolling.
