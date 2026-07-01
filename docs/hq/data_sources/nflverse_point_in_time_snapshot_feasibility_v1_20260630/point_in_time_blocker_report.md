# Point-In-Time Blocker Report

## Blocking Decision

No audited NFLVerse feature family is approved for replay or experiment now.

## Blocking Reasons

- Historical snapshots are not tracked for any audited feature family.
- As-of evidence is missing or partial; only availability denominator fields include a source-as-of style string, and that does not prove historical replay safety.
- Current display artifacts may contain current roster, role, schedule, injury, or last-active information that can leak post-anchor events.
- Missing data semantics remain unresolved for replay in several families.
- `games_missed_while_rostered` remains blocked and cannot be inferred from missing snap/stat/roster/injury rows.
- Identity bridge health is prerequisite gating evidence, not a feature.

## Approval Counts

- `safe_for_replay_now=true`: 0
- `safe_for_experiment_now=true`: 0
- `allowed_for_model_now=true`: 0
- `allowed_for_training_now=true`: 0
- `allowed_for_source_truth_now=true`: 0
