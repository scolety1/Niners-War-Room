# Source and Receipt Gate

## Decision

`PASS_FOR_REVIEW_ONLY_TEMPORAL_VALIDATION_AND_2026_BASELINE_FREEZE_WITH_CAVEATS`

The historical Formula Mart and age sidecar each contain 5,518 exact, duplicate-free `(target season, position, GSIS player_id)` rows. The Mart's N→N+1 leakage and as-of gates pass. Its production-related stamps remain false; this lane is an expressly authorized review-only evaluation, not source promotion or production training approval.

The age sidecar contains eight rows with missing DOB/draft identity and three rows flagged for duplicate-GSIS DOB conflict. Those 11 age values are deterministically null-fenced: the ridge applies its preregistered training-only imputation and missingness indicator, while exact GAUNTLET_081 marks those candidate rows invalid. No unsafe age value enters a score.

The 2026 completed-feature file contains 342 distinct QB/RB/WR/TE players after exact duplicate collapse: 231 scoreable and 111 null-fenced. Every scoreable row has an exact GSIS identity, and all 231 join to a single nonconflicting DynastyProcess DOB. No normalized-name identity fallback is used.

## Verified controlling hashes

- Formula Mart: `4c63a01cc4d56d0496d56ff13d4dabb4faa0b7a24d8f7510a368ad48d9714151`
- Historical age/lifecycle sidecar: `ea5ec2455c89031b8deb6077847b7c10e4da4a09f604bf1dae0e6250983f883b`
- Accepted Gauntlet runner: `791f22187d98cd58e11be34a474f63688001887affd583fb1fd5d2c392231038`
- Mart builder: `bbaec148c2edd1c57ace89d371357180228e65ba5e1d15ca8e04bb9c9f054e34`
- Canonical severe-miss runner: `eb8066a38bb05cded46719bc532b7c1467215cdd29e0bcb3ad869fecbf2ff75e`
- 2026 completed features: `bdff4e6c0c51b64a3f867c6ed11f72cda088046e1ffd194c32fb55f49357d1e0`
- Raw player-stat receipt: `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba`
- DynastyProcess identity/DOB/draft source: `8b3f5d19e29163363dce579b61574277ea138c7b6f292b899f9ecfe672cd6cc1`
- Exact current-board comparator: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- NWR scoring contract: `03986944a57f0f73c78a8f56413b53749b3e384a10788ff7ab262d21e0b1eab2`

## Caveats and blocked uses

- Formula Mart rows are `review_only`; `training_allowed`, `model_use_allowed`, `source_truth_allowed`, `production_approved`, and rankings integration remain false.
- The exact current-board artifact is `candidate_review_only_not_active_rankings`. It is frozen as the exact app-visible/current-board comparator, not relabeled as human-approved production-active ranks.
- Production/model use, rankings integration, app/runtime changes, and source promotion remain blocked.
