# Next Phase Handoff

Recommended next checkpoint: `Core Usage Review Dataset V1 Review and Experiment Gate Prep`.

Use only the tracked packet artifacts, not raw `C:\NWR_SHARED_DATA`, from app pages or downstream review lanes.

Before any experiment:

1. Aggregate player-week rows into season N lagged summaries.
2. Prove the prediction anchor for target season N+1.
3. Preserve nulls and explicit-zero semantics.
4. Re-check identity and snap-count join caveats.
5. Keep the red-zone sidecar review-only and validate typed fields against PBP-derived `yardline_100 <= 20` counts.
6. Keep `rz_att`, routes, TPRR, and YPRR blocked.
7. Run a separate experiment-readiness gate before any modeling.

This packet is ready for review/batch merge if the validation checks pass.
