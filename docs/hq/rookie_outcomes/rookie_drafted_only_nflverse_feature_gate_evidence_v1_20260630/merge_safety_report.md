# Merge Safety Report

This lane creates docs, one CSV matrix, a non-runtime report builder, and focused tests only.

Confirmed:

- no app files changed;
- no Rankings, Gate F/G, Draft Room, or Player Compare behavior changed;
- no model outputs changed;
- no source-truth behavior changed;
- no pinned snapshots changed;
- no `latest_candidate` or `latest_approved` changed;
- no protected/raw/private paths tracked;
- no secrets tracked;
- no local_exports, raw, or vendor files tracked.

All matrix rows keep `allowed_for_model_now=false`, `allowed_for_training_now=false`, and `allowed_for_source_truth_now=false`.
