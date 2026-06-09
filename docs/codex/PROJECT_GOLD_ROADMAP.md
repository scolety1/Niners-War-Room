# Project Gold Roadmap

Project Gold is the plan to turn Niners War Room into a decision-grade LVE fantasy football model and draft tool. The goal is not to make the UI prettier first. The goal is to make the rankings trustworthy, inspectable, and hard to fool.

The app should not become decision-ready just because it produces numbers. It becomes decision-ready only when the data, identity joins, formulas, source coverage, receipts, sanity fixtures, and independent audit loop all agree that the model is safe enough to use for roster and draft decisions.

## Gold Standard

Project Gold succeeds when:

- Rankings are driven by real football statistics, role, projections, age, injury context, and LVE scoring fit.
- Market data is isolated to liquidity, trade value, and buy/sell edge.
- Every important score has a receipt showing raw value, normalized value, weight, contribution, source, and warning.
- Young players, incoming rookies, established veterans, free agents, and released veterans are evaluated in separate lifecycle lanes.
- Age/dropoff logic is explicit, sourced, and visible in receipts.
- Missing data creates review status or confidence drag, not fake certainty.
- Final decision-ready status requires internal tests and an independent external audit packet.

## Mandatory Audit Loop

This is now the default model-safety workflow.

1. Export the active model audit packet:
   - full rankings
   - visible War Board rankings
   - Niners roster board
   - normalized feature rows
   - contribution receipts
   - source coverage
   - outliers
   - named-player audit rows
2. Run an external/pro-agent audit without anchoring it to specific player complaints.
3. Bring the audit report back into the repo.
4. Classify each issue:
   - data bug
   - identity bug
   - normalization bug
   - formula bug
   - source coverage issue
   - calibration issue
   - UI/label issue
5. Patch only supported issues.
6. Add regression tests for every fixed bug.
7. Regenerate outputs and rerun the audit loop.
8. Only then run the final decision gate.

## Phase 1: Model Rescue Freeze

Lock current rankings as audit-only until Project Gold gates pass.

Deliverables:

- Review-only status stays active.
- Current model outputs remain available for inspection.
- A repeatable model audit packet export exists.
- The app never labels rankings decision-ready while blockers remain.

Success criteria:

- Audit packet can be regenerated from current outputs.
- No decision-ready label appears without final gate approval.

## Phase 2: Data Truth Contract

Define what every input means and whether it is real evidence.

Deliverables:

- Feature data dictionary.
- Input status taxonomy:
  - imported real data
  - derived from real data
  - neutral imputation
  - manual review
  - disabled
- Hard rule: neutral defaults cannot masquerade as real evidence.

Success criteria:

- Every scored feature row carries source status and warning status.
- Hidden `50` defaults are visible in receipts.

## Phase 3: Identity Cleanup

Make player identity joins trustworthy.

Deliverables:

- Sleeper/nflverse/GSIS/PFR identity bridge.
- Duplicate player detector.
- Retired/stale/free-agent active-status audit.
- Team and position mismatch checks.

Success criteria:

- No duplicate player rows in active rankings.
- No retired/stale players enter normal roster rankings.
- Ambiguous identities become review rows.

## Phase 4: Core Free Data Import

Use the best free/public data before paying for anything.

Deliverables:

- nflverse/nflreadr import adapters for:
  - weekly player stats
  - player IDs
  - player bio and age
  - passing/rushing/receiving
  - targets and air yards where available
  - first downs or first-down derivation
  - injuries where available
  - snap/participation proxies where available

Success criteria:

- Core production, age/bio, identity, and baseline injury inputs are imported locally.
- Missing free-data fields are explicitly listed.

## Phase 5: Paid Data Trial

Evaluate paid/exportable data only for gaps that create edge.

Best first candidates:

- Fantasy Points Data Suite for routes, route share, snap share, target share, advanced receiving/rushing, YPRR, and exportable fantasy data.
- SportsDataIO or FantasyData for API-style projections, injuries, depth charts, player stats, and fantasy feeds.
- FantasyPros export/API for consensus projections/rankings as a market/projection sanity layer only.
- PFF+ only if the exact premium stats needed are exportable and usable locally.

Deliverables:

- Paid source trial checklist.
- Sample export for 20-30 players.
- Field coverage comparison.
- ID mapping proof.
- Terms/licensing review.

Success criteria:

- No paid source is adopted until exportability, fields, mapping, and local use are verified.

## Phase 6: Projection Layer

Replace local baseline projections with an independent projection layer.

Deliverables:

- Projection import CSV/API contract.
- LVE rescoring formula for projections.
- Projection confidence rules.
- Clear separation between historical production and forward projection.

Success criteria:

- Projection value is no longer mostly neutral baseline `50`.
- Missing independent projection remains visible and lowers confidence.

## Phase 7: Role And Usage Layer

Add the data that separates real opportunity from box-score noise.

Deliverables:

- Snap share.
- Route share.
- Routes run.
- Target share.
- Targets per route run.
- RB weighted opportunities.
- Red-zone and goal-line role.
- Starter/depth chart status.

Success criteria:

- WR/TE values no longer rely on catch totals or box-score production alone.
- RB role scores distinguish between stable workhorse role, fragile spike role, and committee noise.

## Phase 8: Age Dropoff Bridge

Make age/dropoff a first-class auditable model layer.

Deliverables:

- Raw age source.
- Position age bucket.
- Age curve score.
- Age cliff warning.
- Injury interaction.
- Role interaction.
- Receipt rows for every age contribution.

Position principles:

- RB age bites hardest, especially with injury or workload fragility.
- WR age declines slower when target earning and route role remain strong.
- QB age separates rushing decline from passing/start security.
- TE age is later and gentler unless route role disappears.

Success criteria:

- Age is imported in the normalization path, not patched later in a hidden overlay.
- Age/dropoff receipts reconcile to the final score.

## Phase 9: Young NFL Bridge Rebuild

Evaluate first-, second-, and third-year players without pretending they are pure veterans.

Deliverables:

- Lifecycle labels:
  - incoming rookie
  - year-one NFL bridge
  - year-two NFL bridge
  - year-three NFL bridge
  - established veteran
- Draft-capital/prospect prior.
- Evidence decay.
- Confidence drag when NFL evidence is missing.

Success criteria:

- Draft capital helps early but cannot create fake certainty.
- Missing NFL evidence creates review status.
- Year-four-plus players do not score old draft capital.

## Phase 10: Ranking Surface Split

Stop one composite board from pretending to answer every question.

Deliverables:

- Pure Model Value board.
- Keeper Decision board.
- Trade/Liquidity board.
- Forced-Release Pain board.
- Draft Board for available players only.

Success criteria:

- Users can tell whether a player ranks highly because of private model value, keeper context, trade liquidity, or forced-release rules.

## Phase 11: Market Isolation

Keep market data useful without letting it contaminate private value.

Deliverables:

- Market data feeds or imports.
- Market value status:
  - real imported
  - stale
  - missing
  - disabled
- Model vs Market hidden or review-only when market is defaulted.

Success criteria:

- Market does not affect private/model value.
- Missing market no longer creates fake edge.

## Phase 12: Position Formula Rebuild

Rebuild formulas only after data/default issues are fixed.

Deliverables:

- RB formula:
  - role
  - age
  - injury
  - workload fragility
  - first-down/TD fit
- WR formula:
  - target earning
  - route role
  - efficiency
  - age
  - production stability
- QB formula:
  - 1QB replacement suppression
  - elite/rushing exception
  - start security
- TE formula:
  - no-premium suppression
  - route/target earning gate
  - elite exception only

Success criteria:

- Formula changes are backed by receipts and fixtures, not vibes.

## Phase 13: Cross-Position Calibration

Tune positions onto one LVE board.

Deliverables:

- Replacement baselines by position.
- RB/WR/QB/TE sanity bands.
- Position-mix audits for top 25, top 50, and top 100.
- Calibration report.

Success criteria:

- The model can produce surprising rankings, but every surprise must be explainable by receipts.

## Phase 14: Sanity Fixture Suite

Build permanent tests for the cases that should never silently break again.

Fixture families:

- elite WR vs elite RB
- fragile old RB vs stable WR
- young high-capital WR with weak NFL data
- young RB with unclear role
- elite QB exception
- non-elite QB suppression
- elite TE exception
- no-premium TE suppression
- stale player excluded
- missing route/projection does not become confidence
- missing market does not become fake edge

Success criteria:

- A bad model change fails tests before it reaches the app.

## Phase 15: Audit Reports As Workflow

Make the external audit loop a built-in model process.

Deliverables:

- One-command audit packet export.
- Standard external audit prompt.
- Audit import/triage notes.
- Root-cause classification table.
- Patch queue created from audit findings.

Success criteria:

- Every meaningful model run can be independently audited.

## Phase 16: Roster Decision Mode

Make pre-declaration decisions usable before released veterans exist.

Deliverables:

- Core holds.
- Top-five forced-release decision.
- Bubble players.
- Shop/cut candidates.
- Needs Data Review.
- Player receipts for every Niners roster player.

Success criteria:

- Released-veteran pool is not required for pre-declaration roster decisions.
- Top-five release logic focuses on top-five candidates first.

## Phase 17: Draft Mode

Build the final offline draft tool after releases are known.

Deliverables:

- Incoming rookies.
- Released veterans.
- Sleeper free agents.
- Manual adds.
- Protected players excluded.
- Live/mock draft board.
- Best available by pick.
- Rookie/veteran combined board.

Success criteria:

- Draft Board never shows protected roster players as available unless manually added.
- Mock and live draft flows do not mutate source data.

## Phase 18: Final Decision Gate

Only unlock decision-ready when the entire Project Gold chain passes.

Required gates:

- Identity audit passes.
- Source coverage passes or accepted gaps are explicit.
- No hidden defaults in core features.
- Young bridge audit passes.
- Age/dropoff bridge audit passes.
- Sanity fixtures pass.
- Outliers are resolved or accepted with reasons.
- External audit loop passes.
- Roster decision smoke passes.
- Draft pool gates pass for draft-ready status.

Success criteria:

- Final status can be:
  - Review Only
  - Needs Data
  - Calibration Needs Review
  - Roster Decisions Ready
  - Draft Ready
  - Final Money Decisions Ready

No final money-decision label appears unless every required gate passes.

## Near-Term Priority Order

The next implementation work should follow this order:

1. Data truth contract and hidden-default audit.
2. Identity/stale-player cleanup.
3. Ranking surface split.
4. Market-edge disablement until real market imports exist.
5. Age/dropoff bridge.
6. Young NFL bridge rebuild.
7. Participation/routes/projection source plan.
8. Position formula rebuild.
9. Cross-position calibration.
10. External audit loop before final gate.

## Non-Negotiables

- No blind weight tuning.
- No public consensus optimization.
- No market value as private player truth.
- No decision-ready label without receipts, fixtures, and audit.
- No hidden source defaults.
- No stale or duplicate players in normal rankings.
- No UI language that makes review-only scores sound final.
