# Health Inference Blocker Report

Verdict: `HEALTH_INFERENCE_BLOCKED`

## Approval Status

No audited field is approved for health inference.

Approval counts:

- `can_represent_absence_safely=true`: `0`
- `can_use_for_experiment_now=true`: `0`
- `can_use_for_model_now=true`: `0`
- `can_use_for_training_now=true`: `0`
- `can_use_for_source_truth_now=true`: `0`

## Blocked Inferences

This packet does not approve:

- injury-risk score
- durability score
- medical projection
- ACL or comeback projection
- recovery estimate
- healthy-by-missing-data logic
- low-risk-by-missing-data logic
- active or inactive by missing roster logic
- missed game by missing snap/stat logic
- zero usage by missing snap/stat logic

## Why Health Inference Is Blocked

The tracked artifacts are display and review evidence. They do not provide a
clinical or availability outcome source. They also do not prove point-in-time
source visibility for historical prediction anchors.

Specific risks:

- Missing injury reports could be misread as healthy.
- Missing snap rows could be misread as zero snaps, inactivity, or missed games.
- Missing stat rows could be misread as zero production or inactivity.
- Current roster status could leak future roster survival.
- Last active context could leak future career survival.
- Practice status could leak health or role if used outside display review.
- Per-game denominators could create label leakage without replay proof.

## Required Future Evidence Before Reconsideration

A future lane must provide point-in-time source snapshots, prediction anchors,
source extraction timestamps, row-level censoring, identity-safe joins, leakage
diagnostics, label interaction audits, and explicit HQ approval. This packet does
not grant that approval.
