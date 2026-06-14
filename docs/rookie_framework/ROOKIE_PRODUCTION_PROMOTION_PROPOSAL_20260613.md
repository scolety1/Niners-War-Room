# Rookie Production Promotion Proposal - 2026-06-13

## Status

Proposal-only. Do not implement production promotion from this document.

The current candidate audit is GREEN for planning, but live production ranking replacement is not approved. The production-candidate export currently has `0` ready rows, so the safest proposal is to keep rookies candidate-only until HQ explicitly approves a later implementation.

## 1. What Would Be Promoted

If HQ later approves implementation, the promoted item would be a rookie-only production-candidate ordering layer derived from:

- `rookie_production_candidate_v03.csv`
- `rookie_production_candidate_premium_v03.csv`
- `rookie_production_candidate_round2_v03.csv`
- `rookie_production_candidate_5_04_v03.csv`
- `rookie_production_candidate_manual_warnings_v03.csv`
- `rookie_production_candidate_source_safety_audit_v03.csv`

The promoted concept would remain an ordered rookie candidate layer with visible warnings, not a probability model and not a veteran outcome-head input.

## 2. What Would Not Be Promoted

Do not promote:

- rookie probabilities;
- rookie probability bands;
- app-readable outcome columns;
- veteran outcome-head inputs;
- legacy `private_score`;
- public rankings, ADP, projections, consensus, market values, or trade values;
- source-limited warnings as hard private value;
- scouting prose as numeric grades;
- `1.03` as filled when unsupported.

## 3. Files Likely To Be Touched In A Future Implementation

A future approved implementation would need a separate file contract. Likely touched areas could include:

- a new rookie production-candidate adapter or export script under `scripts/rookie_framework/`;
- tests under `tests/`;
- tracked rookie framework documentation under `docs/rookie_framework/`;
- a clearly quarantined local or model artifact path defined by HQ.

Active production ranking files, app files, formulas, private-score files, outcome-column files, and veteran outcome-head files must remain untouched unless HQ explicitly names them in the implementation prompt.

## 4. Files That Must Not Be Touched

Unless separately and explicitly approved, do not touch:

- Streamlit/app files;
- production ranking files;
- private-score files;
- formula files;
- probability or band files;
- Outcome Columns HQ files;
- veteran outcome-head files;
- `data/`;
- committed `local_exports/`;
- any active model artifact that the app reads.

## 5. Feature Flag Or Config Gating Plan

If HQ later approves app-facing work, it must be gated behind an explicit rookie-only feature flag or config setting.

Required behavior:

- default flag state: off;
- no app read unless flag is explicitly enabled;
- app must show warning fields beside candidate order;
- app must not show probabilities, bands, or outcome labels;
- app must preserve `1.03` empty state as `no_player_cleared`, `hold`, or `trade_down_review`;
- rollback must be one-flag disable plus artifact removal.

No feature flag work is approved in this stage.

## 6. Rollback Plan

Before implementation:

1. Confirm clean git status except allowed files.
2. Rebuild review, shadow, and candidate exports.
3. Record candidate row counts and status counts.
4. Confirm `data/` and `local_exports/` are not staged.

If implementation fails before commit:

1. Stop immediately.
2. Do not stage production files.
3. Remove or quarantine generated local artifacts.
4. Write a blocker checkpoint.

If implementation is committed and then rejected:

1. Revert only the approved implementation commit.
2. Rebuild review, shadow, and candidate exports.
3. Re-run strict builds and direct harnesses.
4. Confirm app files, production rankings, private scores, probabilities, bands, outcome files, and veteran files are back to the approved state.

## 7. Test Plan

Future implementation must run:

- strict review-board build;
- strict shadow-ranking build;
- strict production-candidate build;
- direct Step 2, Step 3, and production-candidate test harnesses;
- pytest if available;
- row-count assertions for full, premium, Round 2, and `5.04` outputs;
- marker assertions for candidate-only/app-read/probability flags;
- source-safety assertions for prohibited inputs;
- import checks to prevent Streamlit/app/outcome/veteran dependencies in rookie builders.

## 8. Source-Safety Assertions

Implementation must prove:

- no ADP/ranking/projection/consensus/market/trade/draft-kit value entered private value;
- `use_now` evidence has provenance;
- `use_as_soft_flag` remains bounded and cannot open zones by itself;
- `manual_review_only` remains warning-only;
- `unavailable` fields are not inferred;
- `excluded` fields are never positive evidence;
- `conflict_review` blocks affected movement until resolved;
- scouting prose is not converted into numeric grades;
- injury notes remain manual unless a future policy changes that.

## 9. App Display Plan If Later Approved

If HQ later approves app display:

- show candidate order as candidate-only, not final ranking;
- show `production_ready_status`, `promotion_blockers`, `manual_warnings`, and `source_safety_notes`;
- show `1.03` as empty if unsupported;
- show `app_read_allowed=no` until the future flag explicitly changes it;
- do not show probabilities, bands, projected outcomes, or veteran outcome labels.

No app display work is approved in this stage.

## 10. No Probabilities Or Bands Unless Separately Approved

No probabilities or probability bands are part of this proposal.

Any future probability/band work would require a separate HQ-approved model contract, source hierarchy, tests, calibration plan, and app-display approval.

## 11. No Veteran Outcome Heads

Rookies must not be forced through veteran outcome heads.

Any future rookie outcome work must be a separate approved project and cannot inherit veteran threshold probability services by default.

## 12. Human Approval Checklist

Before implementation, HQ must answer:

- Is production-candidate order allowed to move beyond local exports?
- Should `1.03` remain empty in production-facing context?
- Are any `1.04` candidates cleared, or should all warnings remain visible?
- Are current `0` ready rows acceptable, or should implementation wait?
- Which files may be touched?
- Is app display approved?
- Is any feature flag approved?
- What is the rollback owner and command sequence?
- Are probabilities, bands, outcome columns, and veteran outcome heads still prohibited?

Default answer: pause until HQ explicitly approves implementation.

## 13. Exact Next Prompt For Later Production-Promotion Implementation

Use this only after HQ approval:

```text
You are working in C:/Users/smcol/Documents/Vacation/Niners-War-Room-rookies on branch work/rookie-framework-path.

Implement the HQ-approved rookie production-candidate promotion exactly as approved.

Allowed files/actions:
[HQ MUST LIST EXACT FILES AND ACTIONS HERE]

Do not create rookie probabilities or bands.
Do not use veteran outcome heads.
Do not modify app/Streamlit files unless HQ explicitly listed them above.
Do not modify production ranking/private-score/formula files unless HQ explicitly listed them above.
Do not use ADP/rankings/projections/consensus/market/trade/draft-kit/private_score as private value.
Do not commit data/.
Do not commit local_exports/.
Do not push.

Before edits, verify repo path, branch, git status, latest commits, and the Stage A-E approval docs.
Run strict review, shadow, and production-candidate builds.
Run direct test harnesses and pytest if available.
Stop immediately if any stop condition appears.
```

## Recommendation

Proceed to Stage E final approval checkpoint summary.

Stage E should summarize that the queue reached a proposal-ready state, not a production-implemented state.
