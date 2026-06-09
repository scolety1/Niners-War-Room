# Formula Candidate Proposal Packet

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: summarize candidate football-quality or formula-review areas discovered
by the evidence reports. This packet is proposal-only. This packet does not implement experiments, tune formulas, change model weights, change veteran age curves, change rookie weights, change pick baselines, change VORP, change replacement formulas, change market-gap thresholds, change confidence cap magnitudes, or change startup-slot conversion.

Do not patch formulas from this packet. Do not use this packet as a final
ranking, roster recommendation, trade recommendation, cut recommendation, keep
recommendation, draft recommendation, buy recommendation, sell recommendation,
defer recommendation, target recommendation, or start/sit recommendation.

## Required Preconditions

These conditions should be satisfied before any candidate below becomes a real
formula experiment:

1. Data/source gaps from `DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md` are fixed
   or explicitly accepted as residual risk.
2. Legacy active-pack sentinels remain comparison-only: Keenan Allen legacy
   `82.4` and Darius Slayton legacy `78.88` cannot become primary Player Board
   values.
3. Blank primary-score rows remain fail-closed/manual-only until source gaps are
   repaired: Jeremiyah Love, Carnell Tate, Jordyn Tyson, Fernando Mendoza, and
   Kenyon Sadiq.
4. Market, ADP, rankings, projections, consensus, startup, and trade-calculator
   context remain display-only and excluded from private value.
5. Human judgment worksheet review is completed for the named rows before any
   formula proposal is promoted into implementation.

## Candidate Summary

| Candidate ID | Candidate Area | Source Evidence | Impacted Rows | Proposal Status |
|---|---|---|---|---|
| FC01 | No-premium TE ceiling clarity | `TE_NO_PREMIUM_DISCIPLINE_REPORT_20260605.md`, `SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md` | Trey McBride, Brock Bowers, Travis Kelce, George Kittle, Sam LaPorta, Mark Andrews, T.J. Hockenson | Proposal-only, blocked pending human no-premium judgment. |
| FC02 | 1QB spread and cap clarity | `QB_1QB_DISCIPLINE_REPORT_20260605.md`, `TOP_BOTTOM_CURRENT_PLAYER_SANITY_SCAN_20260605.md` | Josh Allen, Jalen Hurts, Patrick Mahomes, Lamar Jackson, Joe Burrow, Jayden Daniels, Brock Purdy, Daniel Jones | Proposal-only, blocked pending 1QB human prior review. |
| FC03 | RB/WR cross-position balance | `RB_WR_CROSS_POSITION_BALANCE_REPORT_20260605.md`, `YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md` | Christian McCaffrey, Jonathan Taylor, Bijan Robinson, Jahmyr Gibbs, CeeDee Lamb, Justin Jefferson, Garrett Wilson, Malik Nabers | Proposal-only, blocked pending source/identity cleanup and human tier review. |
| FC04 | Veteran age/status confidence shape | `VETERAN_AGE_WINDOW_AUDIT_20260605.md`, `INJURY_STATUS_RISK_AUDIT_20260605.md` | Christian McCaffrey, Derrick Henry, Saquon Barkley, Josh Jacobs, Davante Adams, Stefon Diggs, Mike Evans, Tyreek Hill, Cooper Kupp, Amari Cooper, Keenan Allen | Proposal-only, blocked pending team/identity verification. |
| FC05 | Young-player evidence sensitivity | `YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md`, `CURRENT_PLAYER_VALUE_EXTRACTION_REPORT_20260605.md` | Brian Thomas Jr., Marvin Harrison Jr., Malik Nabers, Xavier Worthy, Ladd McConkey, Ashton Jeanty, Luther Burden, Hollywood Brown | Proposal-only, blocked pending source-gap review. |
| FC06 | Rookie source-limited prior handling | `ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md`, `ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md` | Jeremiyah Love, Makai Lemon, Skyler Bell, Jordyn Tyson, Carnell Tate, Antonio Williams, Daniel Sobkowicz | Proposal-only, blocked pending manual scouting and source coverage. |
| FC07 | Pick-neighborhood explanation and comparison shape | `PICK_VALUE_LADDER_AUDIT_20260605.md`, `PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md` | 2026 1.03, 2026 1.04, 2026 2.04, 2026 2.08, 2026 5.04, Josh Jacobs, Chase Brown, Trey McBride | Proposal-only, blocked pending source-disclosure and UI review. |

## FC01: No-Premium TE Ceiling Clarity

Evidence:

- Trey McBride is the highest numeric current-player score overall at `87.4776`
  in the current checkpoint.
- TE report shows one TE in the top 20, five TEs in the top 50, seven TE rows
  with `no_premium_te` warning text, and a median numeric TE score of `28.1813`.
- Lower TE rows such as Sam LaPorta, Mark Andrews, and T.J. Hockenson carry
  explicit no-premium cap or replacement-level cap warnings.

Risk if ignored:

- A no-premium league user may not understand whether Trey McBride is a valid
  difference-making exception or an overly aggressive TE ceiling.

Future experiment idea:

- After human review, compare "elite TE exception" behavior against lower TE
  cap behavior using ordering fixtures and explanation checks. This is not an
  instruction to change TE discipline or VORP.

## FC02: 1QB Spread and Cap Clarity

Evidence:

- Josh Allen, Jalen Hurts, and Patrick Mahomes appear inside the top 20 by
  numeric current score.
- Joe Burrow and Jayden Daniels appear near the bottom score band with explicit
  1QB cap warnings.
- Daniel Jones carries both 1QB cap text and identity/team review warnings.

Risk if ignored:

- Users may read high QB rows or low capped QB rows as final 1QB truth without
  understanding the cap context.

Future experiment idea:

- After human 1QB prior review, evaluate whether QB spread explanations and
  ordering fixtures are intuitive. This is not an instruction to change QB caps,
  replacement formulas, or model weights.

## FC03: RB/WR Cross-Position Balance

Evidence:

- RB and WR each place four players in the top 10 numeric current-player
  scores.
- RB places 11 players in the top 25 while WR places 9 players in the top 25.
- RB median score is `59.6777`; WR median score is `32.3993`.
- CeeDee Lamb, Justin Jefferson, Garrett Wilson, Malik Nabers, Brian Thomas Jr.,
  Marvin Harrison Jr., Xavier Worthy, and Ladd McConkey are named WR sanity
  rows below multiple RB-heavy tiers.

Risk if ignored:

- The model may feel RB-heavy or WR-depressed to a human reviewer, even if some
  of the pattern is explained by source warnings, identity warnings, or current
  scoring context.

Future experiment idea:

- After source cleanup and human tier review, compare broad RB/WR ordering
  fixtures rather than exact target scores. This is not an instruction to tune
  RB/WR formulas or change cross-position weights.

## FC04: Veteran Age/Status Confidence Shape

Evidence:

- High-score age-review RB rows include Christian McCaffrey, Jonathan Taylor,
  Derrick Henry, and Saquon Barkley.
- Josh Jacobs carries an RB age-window warning.
- Aging WR rows such as Stefon Diggs, Mike Evans, Cooper Kupp, Amari Cooper,
  Tyreek Hill, and Keenan Allen carry confidence, identity, or team warnings.
- Veteran TE rows also intersect with no-premium TE context.

Risk if ignored:

- Veteran confidence may look certain where source/team/status warnings should
  dominate the user’s interpretation.

Future experiment idea:

- After identity/team verification, isolate veteran age-window behavior from
  source-gap behavior in review fixtures. This is not an instruction to change
  veteran age curves, confidence cap magnitudes, or injury/status penalties.

## FC05: Young-Player Evidence Sensitivity

Evidence:

- High-score young rows include Puka Nacua, Jaxon Smith-Njigba, Bijan Robinson,
  Jahmyr Gibbs, De'Von Achane, Chris Olave, Drake London, Breece Hall, and Chase
  Brown.
- Young WR sanity rows such as Garrett Wilson, Malik Nabers, Brian Thomas Jr.,
  and Marvin Harrison Jr. sit in lower score neighborhoods than many human
  priors may expect.
- Ashton Jeanty, Luther Burden, Hollywood Brown, Kaleb Johnson, and blank-score
  rows expose limited-history, missing stats-first, missing VORP, or
  source-shape warnings.

Risk if ignored:

- The user may misread source-limited young-player rows as hard model
  conviction rather than evidence-sensitive review prompts.

Future experiment idea:

- After source repairs, test whether young-player evidence warnings and broad
  ordering fixtures match human priors. This is not an instruction to change
  young-player priors, rookie weights, or confidence caps.

## FC06: Rookie Source-Limited Prior Handling

Evidence:

- Top-20 rookie rows are all `draftable_review`, but most carry source-limited
  and third-party-combine warnings.
- Top named rookie anchors include Jeremiyah Love, Makai Lemon, Skyler Bell,
  Jordyn Tyson, Carnell Tate, and Antonio Williams.
- Daniel Sobkowicz is the highest explicit `watchlist_data_incomplete` row and
  carries missing prospect/college evidence.
- Watchlist/data-incomplete rows are blocked from final rookie draft use.

Risk if ignored:

- Rookie rows may look more definitive than the source state supports.

Future experiment idea:

- After manual scouting, compare rookie source-limited prior behavior with
  broad tier fixtures and warning coverage. This is not an instruction to
  change rookie weights, pick baselines, or final draft logic.

## FC07: Pick-Neighborhood Explanation and Comparison Shape

Evidence:

- Early firsts show elite current assets in nearby model-value neighborhoods,
  while comparison rows explicitly warn against one-pick trade equivalence.
- `2026 2.08` is very close to Josh Jacobs and Chase Brown by internal score.
- `2026 5.04` has no exact baseline, blank score gaps, and manual-only handling.
- Comparison export lacks explicit `source_path`, `source_column`, and
  `lineage_class` fields.

Risk if ignored:

- Users may mistake internal model-value neighborhoods for market trade prices
  or pick recommendations.

Future experiment idea:

- First improve source disclosure and UI explanation. Only later evaluate
  whether pick-neighborhood comparison shape needs formula review. This is not
  an instruction to change startup-slot conversion, pick conversion, or pick
  baselines.

## Recommended Future Experiment Design

If formula work is explicitly allowed later, each candidate should be handled as
an isolated branch or notebook-style paper trial:

1. Name the candidate and hypothesis.
2. Freeze the input rows and source versions.
3. List affected players/assets before changing anything.
4. Define broad expected behavior, not exact target scores.
5. Run old-vs-experiment comparisons with warning/source readback.
6. Reject the experiment if it improves one headline row while breaking source
   routing, blocked use, or known sentinels.
7. Require human approval before any app-facing promotion.

## Explicit Non-Implementation Guardrails

- Do not implement these candidates in this packet.
- Do not tune formulas from this packet.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not mutate generated outputs, active rankings, My Team, War Board,
  readiness gates, app promotion, active data packs, or user-entered draft
  state.
- Do not add ADP, rankings, projections, consensus, market, startup, or
  trade-calculator logic to private value.
- Do not convert review labels into final trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendations.
