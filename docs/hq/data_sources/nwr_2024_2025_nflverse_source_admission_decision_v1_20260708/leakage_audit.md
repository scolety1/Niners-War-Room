# Leakage Audit

Review-only candidate status does not equal production feature safety.

Allowed for later review-only consideration:

- Completed season/week factual usage rows.
- Weekly roster season-week context, if anchored to the same historical season/week and not used as current status.
- Snap/opportunity context with missingness preserved.

Blocked or caveated:

- Current roster/status/injury/depth/schedule context as historical model features.
- PFR/ESPN identity-unsafe sources.
- Routes, TPRR, YPRR, and further source/research work unless a future experiment-readiness gate requests a concrete missing artifact.

No leakage gate is opened for production use. `model_use_approved=false` everywhere.
