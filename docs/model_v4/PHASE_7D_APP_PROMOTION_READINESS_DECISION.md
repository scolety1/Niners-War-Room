# Phase 7D App Promotion Readiness Decision

Created: 2026-05-16

This checkpoint decides whether Model v4 can move from review-only preview into
app-promotion planning. It does not promote v4 into My Team, War Board,
Rankings, Draft Board, or any decision-ready gate.

## Inputs Reviewed

- `docs/model_v4/PHASE_7_EXTERNAL_AUDIT_TRIAGE.md`
- `docs/model_v4/PHASE_7B_FOCUSED_REPAIR_PASS.md`
- `docs/model_v4/PHASE_7C_POST_REPAIR_VALIDATION.md`
- `local_exports/model_v4/review_only_latest/v4_preview_outputs.csv`
- `docs/model_v4/PHASE_7C_SANITY_FIXTURE_RESULTS.csv`
- `docs/model_v4/PHASE_7C_NAMED_PLAYER_REVIEW.csv`
- `docs/model_v4/PHASE_7C_MOVEMENT_AUDIT.csv`

## Decision

Verdict: ready for app-promotion planning, not ready for active app promotion.

Model v4 has cleared the specific Phase 7 repair questions:

- incoming-rookie confidence bug is fixed
- incoming-rookie prior policy is documented
- QB suppression is now acceptable for a 10-team, 1QB review-only model
- all current sanity fixtures pass
- no unexpected movement rows were created
- active app rankings remain unchanged

The remaining issues are source limitations and promotion-process work, not a
reason for another broad formula rebuild.

## Confirmations

| Requirement | Status | Evidence |
| --- | --- | --- |
| Incoming-rookie confidence bug fixed | confirmed | Incoming rookies with no evidence are `weak`, not `strong`, and carry `incoming_rookie_missing_evidence_confidence_cap`. |
| Incoming-rookie prior policy visible | confirmed | Config and Phase 7B notes state that incoming rookies require sourced prospect/rookie-board evidence or stay weak/review. |
| QB suppression acceptable | confirmed for planning | Josh Allen, Lamar Jackson, Jalen Hurts, and other QBs moved below core RB/WR assets; QB fixtures pass. |
| No new unsupported rankings appeared | confirmed for current fixture set | 31/31 sanity fixtures ready; movement audit has 0 unexpected movement rows. |
| Source limitations visible | confirmed | Named review keeps Luther Burden, Kaleb Johnson, and Keenan Allen as weak/blocked review rows. Route data remains unavailable/proxy-only. |
| Active app rankings unchanged | confirmed | V4 remains in review-only preview outputs; no My Team/War Board promotion occurred. |
| Readiness gates unchanged | confirmed | No roster, draft, final-money, or decision-ready status was unlocked. |

## Remaining Issues

| Issue | Classification | Blocks App-Promotion Planning? | Blocks Active Promotion? | Decision |
| --- | --- | ---: | ---: | --- |
| Caleb Williams missing from current v4 preview | data/source control gap | no | yes for QB-control completeness | Add to truth set or document as non-required before active promotion. |
| Luther Burden weak/blocked | source limitation | no | yes for trusted rookie/young-player decisions | Keep review-only until sourced rookie/prospect evidence exists. |
| Kaleb Johnson weak/blocked | source limitation | no | yes for trusted rookie/young-player decisions | Keep review-only until sourced rookie/prospect/NFL evidence exists. |
| Keenan Allen weak | source limitation/confidence warning | no | maybe, depending on use case | Keep warning visible; do not turn weak confidence into a trusted decision. |
| Route metrics unavailable | accepted source limitation | no | no if clearly shown | Keep route metrics quarantined; use snap/target proxies only with warnings. |
| V4 not wired to decision surfaces | UI/process blocker | yes, as work to do | yes | Phase 8 should build shadow app surfaces before any active promotion. |

## Why This Is Not Another Repair Pass

The Phase 7 external audit found two real issues: incoming-rookie false
confidence and QB inflation. Both were fixed and validated. The remaining
warnings are the model being honest about missing or unavailable evidence.

Another formula pass would be premature unless a new audit finds a specific
receipt-backed issue. The next risk is not formula math; it is accidentally
showing v4 as trusted before the app can explain its source limitations.

## Phase 8 App-Promotion Planning Tasks

Phase 8 should promote visibility, not trust. The app should show v4 in shadow
mode first, then dry-run decision surfaces, then decide whether active promotion
is safe.

### Phase 8A: Promotion Contract And Guardrails

Goal: define exactly what it means to move v4 from preview into app surfaces.

Tasks:

1. Create a v4 app-promotion contract.
2. Define allowed states:
   - review-only shadow
   - roster-decision shadow
   - active roster-decision candidate
   - active model
3. Confirm v4 cannot unlock roster/draft/final readiness by display alone.
4. Require every v4 app surface to show review-only status, confidence, and source limitations.
5. Add tests proving My Team and War Board cannot silently swap to v4 active rankings.

### Phase 8B: Missing Control Cleanup

Goal: close the Caleb Williams validation gap and any missing named controls.

Tasks:

1. Add Caleb Williams to the v4 truth-set/player universe if available from current sources.
2. Regenerate v4 preview.
3. Re-run QB validation, sanity fixtures, named review, and movement audit.
4. If Caleb cannot be mapped, document the identity/source reason.
5. Do not change formulas.

### Phase 8C: V4 Shadow War Board

Goal: show v4 rankings beside the current app output without replacing it.

Tasks:

1. Add a War Board v4 shadow section or toggle labeled `Model v4 Review Preview`.
2. Show v4 Dynasty Asset Value, confidence, source warnings, and unavailable sections.
3. Keep active War Board rankings unchanged.
4. Add selected-player v4 receipts.
5. Add tests proving v4 shadow values do not overwrite active rankings.

### Phase 8D: V4 Shadow My Team

Goal: inspect Niners roster decisions with v4 while preserving current app state.

Tasks:

1. Add a My Team v4 shadow view.
2. Show Niners roster players with v4 value, confidence, top receipt drivers, and source warnings.
3. Keep top-five rule context separate from v4 Dynasty Asset Value.
4. Keep weak/blocked source-limited rows visibly review-only.
5. Add tests proving no roster-ready gate unlock occurs.

### Phase 8E: V4 Shadow Receipts And Warnings

Goal: make v4 understandable before any active promotion.

Tasks:

1. Add compact v4 receipt previews on shadow rows.
2. Show production, first-down fit, usage, snap/proxy role, projection, age/dropoff, young prior, and confidence.
3. Highlight route unavailable, estimated first-down projections, missing rookie prior, and weak confidence.
4. Keep raw receipts behind Advanced.
5. Add tests proving receipt totals reconcile.

### Phase 8F: App Promotion Dry Run

Goal: decide whether v4 can become the roster-decision candidate model.

Tasks:

1. Compare active app outputs and v4 shadow outputs for My Team and War Board.
2. Classify differences:
   - expected v4 repair
   - data/source limitation
   - formula concern
   - UI labeling concern
   - acceptable model disagreement
3. Produce an app-promotion dry-run report.
4. If no blockers remain, recommend active roster-decision candidate promotion.
5. Do not mark Roster Decisions Ready yet.

## Final Phase 7D Verdict

Move to Phase 8 app-promotion planning.

Do not run another broad repair pass now. Do not promote v4 into My Team or War
Board yet. Do not unlock any readiness gate. The right next step is a controlled
shadow integration so the app can display v4 honestly before it is trusted for
pre-declaration decisions.
