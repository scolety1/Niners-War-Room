# Drafted-Only Admission Gate Contract

Drafted-only Rookie Outcomes work is admitted only by positive `draft_picks` evidence. A player must have a real draft year, real NFL draft round, and real pick/overall pick from an approved draft-pick source to enter drafted-only review coverage.

Other datasets may enrich identity and status after the drafted row exists. `ff_playerids`, roster data, weekly rosters, depth charts, player stats, snap counts, injuries, Sleeper/NWR IDs, or CFBD candidate rows cannot admit a drafted row by themselves.

Draft absence cannot imply UDFA. Absence from draft-pick rows can be documented as `not_found_in_draft_picks_needs_review`, but it cannot create `confirmed_udfa`, clean draft capital, a model feature, or training truth.

Real NFL draft rounds only are admitted in the modern drafted path. Synthetic round 8, missing round, pseudo-capital, unknown status, or review-only UDFA status must stay outside drafted-only model buckets.

All outputs remain:

- `review_only=true`
- `model_use_allowed=false`
- `training_allowed=false`

Missing draft fields remain `Not enough information`; they are never zero, false, healthy, low-risk, undrafted, or a miss.
