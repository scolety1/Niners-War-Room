# Reading Order Review

Result: PASS at 320x700, 375x812, 768x1024, and 1440x1000.

The DOM and heading order is:

1. Page heading and purpose: Player Compare.
2. Player-selection controls: Choose players; Player A, Player B, optional extra players.
3. Selected-player context: explicit Player A/B selected text.
4. Primary comparison evidence: Visible Context Summary.
5. Caveats and trust context: two independent per-player trust disclosures and How to use this comparison.
6. Secondary details: existing tabs, tables, and disclosures.

Compact visual stacking follows this same DOM order. The source uses normal Streamlit call order and responsive column stacking; it does not use CSS order, row-reverse, column-reverse, absolute-position reordering, or another visual-only reorder. Desktop preserves two columns for Player A and Player B while retaining A-before-B DOM order.
