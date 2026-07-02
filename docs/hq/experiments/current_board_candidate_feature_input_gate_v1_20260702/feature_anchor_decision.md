# Feature Anchor Decision

Feature anchor used: `2025`

Prediction anchor: `2026_current_board_shadow_review`

Rationale:

- Current HQ context is July 2026.
- The latest completed NFL season available in Core Usage Review Dataset V1 is 2025.
- 2025 factual usage can be used as lagged review-only feature context for a 2026 current-board shadow packet only when stable identity joins pass.

Limitations:

- This gate does not use current injuries, depth, schedule, role, availability, rankings, ADP, projections, vendor context, or target outcomes.
- The feature anchor is not a production model anchor.
