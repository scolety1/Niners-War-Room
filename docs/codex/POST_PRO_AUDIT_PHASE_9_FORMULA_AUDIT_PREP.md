# Post-Pro Audit Phase 9: Formula Audit Prep

Generated: 2026-05-15

## Status

Review-only formula preparation. No scoring formulas, active rankings, model gates, or decision-ready labels were changed.

Truth Set Lab v2 does **not** justify immediate formula tuning. The v2 audit found:

- Major v1-to-v2 movement rows: 0
- Suspicious rows: 88
- Production import status: `rejected`
- Role/usage import status: `rejected`
- Projection import status: `safe_after_derivation_with_rejections`

Suspicious-row causes:

| issue | rows | interpretation |
|---|---:|---|
| production_rejected | 40 | Core historical production evidence is still not safe enough for formula conclusions. |
| role_usage_rejected | 37 | Route/workload/usage evidence is still not safe enough for formula conclusions. |
| low_confidence_or_blocking_warning | 5 | Some young/control players still need direct review before trusting rank surfaces. |
| projection_team_mismatch | 3 | Projection rows need team/source-date validation before scoring. |
| missing_projection | 3 | Projection gaps remain visible and should not become fake certainty. |

## Formula Prep Rule

The only formula work supported right now is fixture design and hypothesis documentation. A future formula change should not be applied until:

1. Corrected production import passes strict validation, or a reliable paid/free production source replaces it.
2. Corrected role/usage import passes strict numeric validation, or a paid route/usage source passes a sample trial.
3. The affected player group has receipt rows proving the formula problem is not a data, identity, lifecycle, or normalization issue.
4. A regression fixture exists before the formula change is applied.

## Proposed Formula-Change Backlog

### 1. RB Age / Dropoff / Workload Fragility

Reason:

RB rankings are extremely sensitive to workload and short-term projection opportunity. In an LVE dynasty context, RB value should reward young elite workload assets while preventing older or fragile workload spikes from behaving like stable long-term dynasty anchors.

Evidence status:

- Not yet fixture-backed enough for a formula change.
- Truth Set v2 still rejects production and role/usage, so carry share, target share, weighted opportunity, red-zone role, and workload fragility remain weak inputs.
- Current elite/control RB audit rows include Bijan Robinson RB1, Jahmyr Gibbs RB2, De'Von Achane RB4, Kyren Williams RB7, Christian McCaffrey RB10, Chase Brown RB25, Ashton Jeanty RB26.

Affected players to audit:

- Bijan Robinson
- Jahmyr Gibbs
- De'Von Achane
- Kyren Williams
- Christian McCaffrey
- Chase Brown
- Ashton Jeanty
- David Montgomery
- James Cook
- Derrick Henry

Expected direction if supported later:

- Preserve high scores for young elite backs with strong production plus receiving/first-down roles.
- Reduce dynasty_hold_value for older RBs, fragile RBs, and workload-only profiles.
- Separate win-now RB value from dynasty hold value more clearly.
- Require stronger confidence when a top RB ranking is driven by projected opportunity rather than real production/role evidence.

Regression fixture:

- Young elite RB with strong production and receiving role remains above older workload RB.
- Older RB with strong projected workload but age/injury fragility cannot pass young elite RBs on dynasty_hold_value alone.
- Explosive but injury-fragile RB can score well in win_now_value while carrying lower confidence or hold value.
- Young incoming/bridge RB with draft capital but little NFL evidence stays review-needed until production/role exists.

Risk:

- Over-penalizing productive older RBs could erase useful one-year title-window value.
- Under-penalizing age and workload could recreate the prior “role-only RB rocket ship” problem.
- Needs clean role/usage and injury evidence before tuning.

### 2. WR Target Earning / Production Stability

Reason:

WR values should be driven by target earning, role stability, production stability, age window, and first-down/TD fit. If target/route evidence is missing or rejected, WR formula changes may accidentally reward stale production or punish players for source gaps.

Evidence status:

- Not yet fixture-backed enough for a broad formula change.
- Truth Set v2 still rejects role/usage data, which is central for WR target earning and route role.
- Current elite/control WR audit rows include Justin Jefferson WR1, CeeDee Lamb WR2, Ja'Marr Chase WR3, Amon-Ra St. Brown WR4, Malik Nabers WR5, Puka Nacua WR6, Brian Thomas Jr. WR8, Tee Higgins WR23, Jaxon Smith-Njigba WR35.

Affected players to audit:

- Justin Jefferson
- CeeDee Lamb
- Ja'Marr Chase
- Amon-Ra St. Brown
- Puka Nacua
- Malik Nabers
- Brian Thomas Jr.
- Jaxon Smith-Njigba
- Tee Higgins
- Luther Burden
- Jayden Higgins
- Xavier Worthy

Expected direction if supported later:

- Strengthen target-earning and stable route role as core WR signals.
- Make recent elite production easier to inspect and harder to bury behind stale or proxy features.
- Preserve upside for young bridge WRs while requiring clear confidence labels when NFL evidence is limited.
- Avoid boosting WRs from market or subjective prospect notes.

Regression fixture:

- Elite WR with strong target earning and production stability remains a top overall asset.
- WR with strong projection but missing route/usage data is review-labeled rather than treated as fully certain.
- Young WR with strong draft/prospect prior but weak NFL evidence stays below young WR with real NFL production unless clearly marked as upside/review.
- JSN/Tee-style comparison must show exactly whether the gap comes from source window, target earning, projection, or formula behavior.

Risk:

- Without clean target/route data, formula changes can overreact to projections.
- Increasing WR stability weights too early could suppress legitimate younger breakout profiles.

### 3. QB 1QB Suppression

Reason:

LVE is 10-team, 1QB, 3-point passing TD. Most QBs should be suppressed versus scarce RB/WR assets, but true elite rushing/start-security QBs should not disappear if projections are missing or local-baseline-only.

Evidence status:

- Partially fixture-backed from Sprint 2 Phase 12.
- Existing proposal already supports a narrow QB elite exception using real recent production and rushing evidence when independent projections are unavailable.
- Truth Set v2 still does not justify broad QB reweight.

Affected players to audit:

- Josh Allen
- Lamar Jackson
- Jalen Hurts
- Patrick Mahomes
- Daniel Jones
- other replaceable starters

Expected direction if supported later:

- Keep non-elite QBs heavily suppressed.
- Allow elite rushing QBs with strong start security and real production to clear a narrow exception.
- Keep pocket passers dependent on true difference-making production, not name value.

Regression fixture:

- Elite rushing QB with strong real production and start security clears replaceable-QB suppression.
- Replaceable starting QB with neutral projection and modest rushing remains suppressed.
- QB score does not crowd out similarly valuable RB/WR assets in a 1QB build.

Risk:

- Too much QB exception logic can make 1QB rankings look like superflex.
- Too much suppression can make genuine elite QB advantage invisible.

### 4. TE No-Premium Suppression

Reason:

There is no TE premium, so non-elite TEs should be suppressed. Elite TEs should require route participation, target earning, and production/efficiency evidence, especially if projections are missing or local-baseline-only.

Evidence status:

- Partially fixture-backed from Sprint 2 Phase 12.
- Current route/usage rejection means TE route participation is not clean enough for broad tuning.
- Existing proposal supports only a narrow elite exception.

Affected players to audit:

- Brock Bowers
- T.J. Hockenson
- Jake Ferguson
- Brenton Strange
- Oronde Gadsden II
- low-route/blocking TE controls

Expected direction if supported later:

- Keep replacement-level TEs suppressed.
- Let elite route/target/proven-production TEs separate only when evidence is real.
- Prevent TE scarcity from directly inflating private value in no-premium scoring.

Regression fixture:

- Elite TE with strong route role, target earning, and production clears no-premium suppression.
- Low-route or blocker-heavy TE remains suppressed even with touchdown noise.
- TE projection without route/target evidence is review-labeled, not decision-ready.

Risk:

- Over-suppressing TE can hide real elite weekly advantage.
- Under-suppressing TE can recreate generic dynasty TE scarcity where LVE scoring does not support it.

### 5. Young Bridge Prior Decay

Reason:

First-, second-, and third-year NFL players should not be treated as pure veterans or pure rookies. Draft/prospect prior should matter early, decay over time, and yield faster when real NFL production/role evidence exists.

Evidence status:

- Partially supported as a model policy.
- Truth Set v2 filled some young-prior gaps, but production and role/usage are still rejected, so evidence-weight testing is incomplete.
- Young bridge rows in v2 include Brian Thomas Jr., De'Von Achane, Luther Burden, Kaleb Johnson, Jayden Higgins, and other young controls.

Affected players to audit:

- Brian Thomas Jr.
- Luther Burden
- Kaleb Johnson
- Jayden Higgins
- Xavier Worthy
- Ricky Pearsall
- Jalen Coker
- Ashton Jeanty
- Brock Bowers
- Jahmyr Gibbs

Expected direction if supported later:

- Incoming rookies and year-one bridge players retain meaningful draft/prospect prior.
- Year-two players shift materially toward NFL evidence.
- Year-three players retain only a small prior unless NFL evidence is missing.
- Established veterans receive no scored draft-capital prior.
- Strong NFL evidence should reduce reliance on prospect priors faster.

Regression fixture:

- Young player with strong NFL production outranks similar-prior young player with little NFL evidence.
- High draft-capital young player with missing NFL evidence is review-needed, not auto-boosted.
- Established veteran with strong production receives no draft-capital contribution.
- Missing young-prior rows create warnings rather than neutral hidden evidence.

Risk:

- Too much prior keeps failed prospects artificially alive.
- Too little prior makes rookies/early-career players look like empty-stat veterans.
- Requires clean production/usage before deciding decay strength.

## Required Formula-Gate Fixtures Before Any Future Apply

| fixture | purpose | apply blocker if failing |
|---|---|---|
| RB young elite vs older workload | Prevent role-only or age-blind RB inflation. | Yes |
| RB fragile spike vs stable elite WR | Check cross-position dynasty balance. | Yes |
| WR target earner vs projection-only WR | Ensure target/route evidence matters more than unsupported projection. | Yes |
| Young WR NFL evidence vs prospect prior | Verify young bridge decay and evidence weighting. | Yes |
| Elite rushing QB vs replaceable QB | Preserve 1QB suppression with elite exception. | Yes |
| Elite route TE vs low-route TE | Preserve no-premium TE suppression with elite exception. | Yes |
| Established veteran draft prior absent | Prevent draft capital contaminating veteran value. | Yes |
| Missing core production/role data | Keep review-only when formula would otherwise look certain. | Yes |

## Immediate Recommendation

Do not apply formula changes from Truth Set Lab v2.

Next useful work:

1. Get corrected production and numeric role/usage exports to pass validation.
2. Re-run Truth Set Lab v2/v3 preview with those fields.
3. Re-run this formula prep against real production and role/usage evidence.
4. Only then apply fixture-backed formula changes.

If cleaner data cannot be obtained quickly, the safer next step is a paid-data sample trial for route participation, TPRR/YPRR, snap share, red-zone usage, goal-line usage, and injury reliability.
