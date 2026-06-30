# Identity Apply Overlay Readiness

Current readiness: PARTIAL_OVERLAY_READY_FOR_REVIEW_ONLY_APPLY_LANE

- Approved rows available in overlay: 43
- Rows still pending: 4
- Rows kept blocked: 7

The overlay is not an app-ready join by itself because approved rows still need safe binding to current NWR player rows. A future apply/rebuild lane must validate that binding before rebuilding the player context artifact.
