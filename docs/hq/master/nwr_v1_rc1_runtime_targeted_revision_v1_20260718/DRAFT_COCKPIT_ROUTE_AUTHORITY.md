# Draft Cockpit route authority

Classification: `SUPPORTED_HIDDEN_ROUTE`.

Evidence:

- `ALL_NAVIGATION_PAGES` registered `draft-cockpit-root` and marked it hidden.
- `pages/44_draft_cockpit_root.py` delegates to canonical owner `pages/21_live_draft_room_v1.py`.
- The canonical owner renders semantic H1 `Draft Cockpit`.
- Existing navigation tests required the route to remain registered and hidden.
- The rejected review classified the route as supported with a caveat rather than deprecated.

The authority is unambiguous. Deprecation or removal would contradict the production inventory and owning tests.

Negative controls now prove that a wrong target, missing route, registered named route marked as default, or unrelated heading cannot satisfy the contract. The named-default control is the direct static proxy for the observed Streamlit Page Not Found failure.
