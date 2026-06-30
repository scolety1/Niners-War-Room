# Safe Overlay Update Plan

This lane does not update active Outcome, Rankings, or player-context app artifacts.

A later lane could safely use this packet only after explicit human review. Safe follow-up actions could include:

- show review-only identity caveats for rows accepted by a human reviewer;
- keep ambiguous rows as `Not enough information`;
- block rows with incomplete team/timeline evidence;
- expose identity join health in Data Review surfaces;
- preserve `review_only=true`, `model_use_allowed=false`, `training_allowed=false`, and `source_truth_allowed=false`;
- avoid rank logic, hidden sort, model inputs, source-truth promotion, trade value, and pick value.

Rows in this packet must not be treated as safe player context solely because they have a recommendation. `approved_by_human=false` means they remain pending.
