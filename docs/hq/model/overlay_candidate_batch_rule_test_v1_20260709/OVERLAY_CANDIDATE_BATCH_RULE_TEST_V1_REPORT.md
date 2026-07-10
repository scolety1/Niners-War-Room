# Overlay Candidate Batch Rule Test V1

## Verdict

`YELLOW_SPARSE_HISTORY_OVERLAY_REMAINS_PRIMARY`

## Scope

This was a bounded review-only overlay batch rule test. It froze exactly five selected overlay families before scoring and enforced a non-stacking primary-overlay policy. It did not run a broad Formula Gauntlet, tune formulas, dynamically tune thresholds, add overlay families after seeing results, run ranking simulation, change production rankings, change app/runtime/model behavior, promote sources, push/merge, mutate canonical `local_exports`, approve production/model-use, create hidden sort/recommendation logic, use current-only ADP historically, use SportsDataIO, use paid/API/free-trial/API-key sources, use same-season/future leakage, use PFF Elusive Rating, use `nwr_elusive_proxy_review_only`, use ungated CFBD/prospect production, or infer UDFA truth.

## Test Summary

- Overlay families tested: `5`
- References tested: `5`
- Result rows: `30`
- Eligibility ledger rows: `2526`
- Windows tested: full-history `2013-2025`, broad-window `2014-2025`, partial-window `2022-2025`
- Primary-overlay priority policy: discovery packet order, no stacking

## Best Results

- Best net miss-reduction overlay: `PRIMARY_POLICY_NONSTACKING_DISCOVERY_PRIORITY` on `PYF_BASELINE` / `full_history_2013_2025`, net miss reduction `8`
- Best false-negative reduction overlay: `PRIMARY_POLICY_NONSTACKING_DISCOVERY_PRIORITY` on `PYF_BASELINE` / `full_history_2013_2025`, false-negative reduction `4`
- Best false-positive reduction overlay: `PRIMARY_POLICY_NONSTACKING_DISCOVERY_PRIORITY` on `PYF_BASELINE` / `full_history_2013_2025`, false-positive reduction `4`

Any overlay beat `REFINE_005_A_EARLY_ROLE_015` on net miss reduction: `no`.

Any overlay beat `REFINE_005_A_EARLY_ROLE_015` on false-negative reduction: `no`.

Sparse-history overlay remains primary: `yes`.

## Decision

Recommended next lane: `Sparse-History Overlay Candidate Remains Primary / Stop V1`.

Review-only ranking simulation remains blocked. Production/model-use and rankings integration remain blocked.
