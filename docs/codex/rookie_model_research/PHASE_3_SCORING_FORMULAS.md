# Deterministic Rookie Scoring Formulas for the LVE Dynasty League

These formulas are built around one central principle: forecast fantasy usefulness in the entity["organization","NFL","american football league"] from pre-draft evidence in entity["organization","NCAA","college sports association"] football, then re-rank that talent through your exact league rules instead of through generic dynasty assumptions. The strongest research-backed points are that draft position is a very important signal but not a pure causal measure of talent, athletic testing usually predicts where players get drafted better than how they actually perform, younger entry tends to matter, quarterback rushing materially improves translation, several wide receiver college efficiency measures add signal beyond raw box-score totals, and tight end drafting is especially prone to mismatches between what teams pay for and what later becomes fantasy value. citeturn18view0turn42search1turn6view5turn24view2turn27view0turn35view1

For LVE specifically, the model should push value away from generic Superflex and TE-premium assumptions. A 1QB format with 3-point passing TDs reduces quarterback scarcity and lowers the value of pocket-passing-only profiles. No PPR reduces the value of empty target volume. A 0.4 rushing/receiving first-down bonus pushes the model toward chain-moving touches, on-field trust, and goal-line/short-yardage roles. Three starting WRs plus two flexes materially increase weekly WR/RB demand, so WR and RB should occupy more of the early board than they would in a shallow-start league. Deep benches and 23 keepers make it easier to hold long-arc WRs and TEs, but the forced-release rule means every rookie pick must be priced against the actual released-veteran pool, not against rookies in isolation. The formulas below therefore use evidence-backed talent cores, but cap landing spot as an overlay and explicitly subtract veteran opportunity cost at the end. citeturn35view2turn13search6turn13search20

## Research basis and design rules

The cleanest way to think about draft capital is as an information bundle. It captures scouting consensus, athletic testing, interviews, medicals, scheme fit, expected opportunity, and organizational willingness to force volume toward the player. That makes it the best single input in a rookie model, but it is still a proxy, not a cause. Academic work on tight ends and wide receivers shows that the variables driving draft order are not always the same variables driving NFL productivity, and work on combine outcomes shows testing often does more to separate “drafted versus not drafted” than to explain future performance once players are in the league. citeturn24view1turn24view2turn27view0turn18view0

That is why these formulas use a layered structure. The **Main Prospect Score** is the evidence-backed talent core. The **League-Fit Adjustment** translates that talent into your scoring and lineup rules. The **Rookie-Year Opportunity Adjustment** is capped because situation matters for immediate fantasy production but is fragile. The **Long-Term Dynasty Adjustment** rewards age, role stability, and profile features that survive coordinator changes. The **Trade Insulation Formula** intentionally leans back toward draft capital, because market value in dynasty is often more stable than raw fantasy scoring. Final LVE value is then reduced or enhanced by the released-veteran benchmark actually available in your room. That separation keeps landing spot from contaminating the core talent score while still making it actionable on draft day. citeturn40view0turn24view0turn27view0turn30view0turn32view1

Evidence is strongest for quarterback rushing, quarterback draft capital, early entry/age effects, wide receiver college production and efficiency, and first-round tight end insulation. Evidence is more mixed for many RB-specific microstats, for college first-down data because public historical samples are smaller and more recent, and for some film-adjacent charting inputs like contested targets. Those weaker or newer inputs should still be used, but with smaller weights, as modifiers, or only as tiebreakers. citeturn6view1turn42search1turn37view0turn11view4turn35view1turn35view2

## Shared normalization and helper functions

Use normalized 0-100 fixture inputs for every atomic metric. Do raw-to-score transformation offline once, save the score in CSV or JSON, and never let runtime code depend on live APIs.

```ts
type Pos = 'QB' | 'RB' | 'WR' | 'TE';
type Score = number; // 0..100

interface LeagueContext {
  teams: 10;
  startQB: 1;
  startRB: 2;
  startWR: 3;
  startTE: 1;
  flex: 2;
  ppr: 0;
  tePremium: 0;
  passTd: 3;
  rushRecTd: 4;
  rushRecFirstDown: 0.4;
  keepers: 23;
}

interface VeteranValue {
  playerId: string;
  position: Pos;
  lveVeteranScore: Score;   // from separate veteran model or manual ranking
  flexEligible: boolean;    // RB/WR/TE = true
}

interface PositionScoreResult {
  mainProspect: Score;
  leagueFit: Score;
  rookieOpportunity: Score;
  longTermDynasty: Score;
  tradeInsulation: Score;
  veteranOpportunityAdj: number; // signed adjustment
  missingPenalty: number;
  confidence: Score;
  finalDecision: Score;
  riskFlags: string[];
  upsideFlags: string[];
  floorFlags: string[];
  recommendedRange: string;
  doNotDraftBeforePick: number | null;
}

const FINAL_WEIGHTS = {
  mainProspect: 52,
  leagueFit: 10,
  rookieOpportunity: 14,
  longTermDynasty: 14,
  tradeInsulation: 10,
}; // sums to 100

function clamp(x: number, min = 0, max = 100): number {
  return Math.max(min, Math.min(max, x));
}

function wa(parts: Array<[number, number]>): Score {
  const weightSum = parts.reduce((s, [, w]) => s + w, 0);
  const value = parts.reduce((s, [v, w]) => s + (v * w), 0) / weightSum;
  return clamp(value);
}
```

Use linear or piecewise normalization depending on the metric. For stable metrics such as age at draft, YPRR, draft-pick buckets, target share, or pressure-to-sack rate, fixed thresholds are better than season-relative z-scores because they are deterministic and easier to test. For noisier or newer metrics like first-downs per route run, missed tackles forced, or charting-based role data, use percentile bands built from your local historical study set and version them in fixtures. The goal is not elegance; the goal is repeatability. citeturn35view2turn37view0turn39view0

Use a common final structure across all four positions:

```ts
function combineFinal(
  mainProspect: Score,
  leagueFit: Score,
  rookieOpportunity: Score,
  longTermDynasty: Score,
  tradeInsulation: Score,
  veteranOpportunityAdj: number,
  missingPenalty: number
): Score {
  const preVeteran = wa([
    [mainProspect, 52],
    [leagueFit, 10],
    [rookieOpportunity, 14],
    [longTermDynasty, 14],
    [tradeInsulation, 10],
  ]);
  return clamp(preVeteran + veteranOpportunityAdj - missingPenalty);
}
```

The missing-data framework should be neutral-first, then punitive. Impute a missing feature to **50**, but apply a penalty based on feature class so that incomplete profiles never tie with fully observed profiles.

```ts
type FeatureClass = 'core' | 'secondary' | 'modifier' | 'tiebreaker';

const MISSING_MULTIPLIER: Record<FeatureClass, number> = {
  core: 0.40,
  secondary: 0.25,
  modifier: 0.12,
  tiebreaker: 0.05,
};

function missingPenalty(
  weightedMissingFeatures: Array<{ featureWeight: number; featureClass: FeatureClass }>,
  cap: number
): number {
  const raw = weightedMissingFeatures.reduce(
    (sum, f) => sum + f.featureWeight * MISSING_MULTIPLIER[f.featureClass],
    0
  );
  return clamp(raw, 0, cap);
}
```

Confidence should reward completeness and agreement across the important signals, while penalizing profiles where draft capital says one thing and production says another.

```ts
function confidenceScore(
  dataCompleteness: Score,   // weighted non-missing coverage
  evidenceCoverage: Score,   // High=100, Medium=70, Low=40, Speculative=20; weighted
  signalAgreement: Score,    // 100 - scaled stdev among major sub-scores
  sampleQuality: Score       // combine verified data, official measurements, reliable charting
): Score {
  return clamp(
    0.55 * dataCompleteness +
    0.25 * evidenceCoverage +
    0.10 * signalAgreement +
    0.10 * sampleQuality
  );
}
```

The veteran/free-agent opportunity-cost layer is mandatory in LVE because the draft follows roster declarations and released players can be materially more useful than middle-class rookies. For each rookie, compare the pre-veteran score to the relevant released-veteran benchmark.

```ts
function veteranOpportunityAdjustment(
  pos: Pos,
  preVeteranScore: Score,
  samePosBenchmark: Score,
  flexBenchmark: Score
): number {
  const benchmark =
    pos === 'QB' ? samePosBenchmark :
    pos === 'TE' ? (0.55 * samePosBenchmark + 0.45 * flexBenchmark) :
                   (0.70 * samePosBenchmark + 0.30 * flexBenchmark);

  const diff = preVeteranScore - benchmark;

  if (pos === 'QB') return clamp(diff * 0.35, -18, 6);
  if (pos === 'RB') return clamp(diff * 0.25, -12, 8);
  if (pos === 'WR') return clamp(diff * 0.22, -10, 8);
  return clamp(diff * 0.30, -16, 5); // TE
}
```

For LVE, compute benchmarks from the actual post-declaration pool. A good default is: QB = top-3 available QBs; RB = top-6 available RBs; WR = top-8 available WRs; TE = top-3 available TEs; flex benchmark = top-10 available RB/WR/TE values. That sizing matches the fact that QBs and TEs are one-starter positions while WR/RB are pushed by 3 WR plus 2 flex. This benchmarking step is a league-specific design choice, but it is exactly the kind of context the released-veteran rule forces you to encode. 

## Quarterbacks

The evidence base for quarterbacks is clear enough to support a hard structural rule: in 1QB, quarterback is the least urgent early-round rookie position unless the prospect combines high draft capital with functional rushing and acceptable sack avoidance. Research on college quarterbacks found that both passing and rushing ability correlate with selection, but rushing ability stands out as especially important when projecting NFL performance, while age of entry also matters. Analyst work on fantasy translation reaches a similar conclusion: early-entry quarterbacks and first-round quarterbacks meaningfully outperform low-capital peers, and draft capital does most of the heavy lifting at the position. citeturn6view5turn6view1turn42search1turn32view1

That means the LVE QB formula should not try to be clever with low-capital pocket passers. It should instead reward the structural fantasy traits your scoring cares about: rushing, scramble survivability, and enough passing competence to stay on the field. In your format, passing touchdowns are worth only 3 points and passing first downs are not scored, so pure pocket efficiency is less fantasy-leveraged than in many generic dynasty models. 

```ts
interface QBNormalizedInputs {
  draftCapital: Score;
  rushingProfile: Score;      // rush yards, rush TD rate, scramble rate, designed run share
  passingEfficiency: Score;   // AY/A or EPA, accuracy, BTT-TWP style composite
  sackAvoidance: Score;       // inverse pressure-to-sack, inverse sack rate
  filmGrade: Score;           // NFL.com/PFF/manual scout composite
  ageTrajectory: Score;       // younger entry, early declare, age at draft
  goalLineRush: Score;
  explosivePass: Score;
  rookieStartPath: Score;
  passProtectionEnv: Score;
  coachingDevEnv: Score;
  weaponsEnv: Score;
  teamPassVolume: Score;
  durability: Score;
  overallPick: number;
}

function scoreQB(input: QBNormalizedInputs, vets: VeteranValue[], ctx: LeagueContext): PositionScoreResult {
  let mainProspect = wa([
    [input.draftCapital, 32],
    [input.rushingProfile, 22],
    [input.passingEfficiency, 18],
    [input.sackAvoidance, 14],
    [input.filmGrade, 8],
    [input.ageTrajectory, 6],
  ]); // 100

  const exceptionalQB =
    input.rushingProfile >= 85 &&
    input.passingEfficiency >= 80 &&
    input.sackAvoidance >= 70;

  // hard suppression for low-capital QBs in 1QB
  if (input.overallPick > 100) {
    mainProspect = clamp(mainProspect * (exceptionalQB ? 0.85 : 0.68));
  }

  const leagueFit = clamp(
    15 +
    0.50 * input.rushingProfile +
    0.20 * input.goalLineRush +
    0.15 * input.sackAvoidance +
    0.15 * input.explosivePass
  );

  const rookieOpportunity = wa([
    [input.rookieStartPath, 35],
    [input.passProtectionEnv, 20],
    [input.coachingDevEnv, 20],
    [input.weaponsEnv, 15],
    [input.teamPassVolume, 10],
  ]);

  const longTermDynasty = wa([
    [input.ageTrajectory, 30],
    [input.passingEfficiency, 25],
    [input.sackAvoidance, 20],
    [input.rushingProfile, 15],
    [input.durability, 10],
  ]);

  let tradeInsulation = clamp(wa([
    [input.draftCapital, 70],
    [input.filmGrade, 15],
    [input.rookieStartPath, 15],
  ]) - 10);

  if (input.overallPick > 100) {
    tradeInsulation = clamp(tradeInsulation * (exceptionalQB ? 0.70 : 0.45));
  }

  // veteranOpportunityAdj, missingPenalty, confidence, flags omitted here for brevity
  // finalDecision = combineFinal(...)
}
```

The risk flags for QB should be aggressive. Flag a quarterback if he is Day 3, if his sack-avoidance score is below 40, if he is an older non-early entrant without rushing help, or if he needs immediate starts but does not have a clear rookie path. Upside flags should require some version of Round 1 or early Round 2 capital plus either elite rushing or unusually strong passing-efficiency and sack-avoidance numbers. Floor flags should require both real draft capital and a playable passing floor; athletic chaos without staying power is not a floor in 1QB. citeturn6view1turn32view1turn39view0

For LVE draft management, the practical QB rules should be harsh. A QB with a **Final LVE Decision Score** of 92 or higher can enter the Round 1 conversation, but still should not be taken before pick 11 unless his veteran adjustment is non-negative and there is no RB or WR within 6 points of him. Scores of 84-91 fit best in the late first or early second. Scores of 76-83 belong in the second or third. Scores below 76 are usually patience stashes or post-draft additions. The simple do-not-draft-before rule is: **do not draft a QB ahead of any same-tier RB/WR when the gap is 6 points or less**, and **do not draft any pick-101+ QB before Round 4 unless he clears the exceptional-QB gate**. 

## Running backs

Running back is where LVE’s scoring shifts the formula the most. The position still cares a great deal about draft capital and opportunity, but your scoring format makes “useful touches” much more important than raw catch totals. Public analyst research on RB outcomes is less standardized and less open than the WR/QB evidence base, but the stable findings are still useful: early-declare backs outperform non-early backs, draft capital is the strongest single predictor of early fantasy value, receiving skill matters, competition-adjusted college production matters, and some combine traits are overvalued by the market relative to more football-shaped traits like agility or multidimensional usage. citeturn30view0turn43view0turn39view0turn29search6

In LVE, the RB formula should therefore elevate chain-moving ability, short-yardage utility, and touch-earning evidence. Receiving still matters, but not as “catch volume.” It matters as proof that the player can stay on the field, convert first downs, survive game-script changes, and preserve long-term value if he is not a pure grinder.

```ts
interface RBNormalizedInputs {
  draftCapital: Score;
  workloadEarning: Score;     // touch share, scrimmage share, snap-touch rate
  rushEfficiency: Score;      // MTF/att, YAC/att, explosive rate, success rate
  receivingImpact: Score;     // YPRR, TPRR, routes, receiving market share
  ageTrajectory: Score;       // age, early declare, exp-adjusted production
  goalLinePower: Score;       // short-yardage role, goal-line profile, BMI/weight
  athleticism: Score;         // speed score, burst, agility
  firstDownRunner: Score;     // first downs per carry/touch or proxy
  returnValue: Score;
  depthChartEarlyDown: Score;
  depthChartPassDown: Score;
  depthChartGoalLine: Score;
  runBlockEnv: Score;
  teamRunRateEnv: Score;
  durability: Score;
  overallPick: number;
}

function scoreRB(input: RBNormalizedInputs, vets: VeteranValue[], ctx: LeagueContext): PositionScoreResult {
  let mainProspect = wa([
    [input.draftCapital, 26],
    [input.workloadEarning, 18],
    [input.rushEfficiency, 16],
    [input.receivingImpact, 16],
    [input.ageTrajectory, 10],
    [input.goalLinePower, 8],
    [input.athleticism, 6],
  ]); // 100

  const leagueFit = wa([
    [input.goalLinePower, 30],
    [input.firstDownRunner, 25],
    [input.workloadEarning, 20],
    [input.receivingImpact, 15],
    [input.returnValue, 10],
  ]);

  const rookieOpportunity = wa([
    [input.depthChartEarlyDown, 30],
    [input.depthChartPassDown, 20],
    [input.depthChartGoalLine, 20],
    [input.runBlockEnv, 15],
    [input.teamRunRateEnv, 15],
  ]);

  const longTermDynasty = wa([
    [input.ageTrajectory, 30],
    [input.receivingImpact, 25],
    [input.draftCapital, 20],
    [input.durability, 15],
    [input.athleticism, 10],
  ]);

  const tradeInsulation = wa([
    [input.draftCapital, 55],
    [rookieOpportunity, 25],
    [input.receivingImpact, 10],
    [input.athleticism, 10],
  ]);
}
```

The key LVE nuance is that **firstDownRunner** and **goalLinePower** are not “cute” features; they are scoring translators. A no-PPR league already discounts empty targets. Your first-down bonus then gives extra weight to backs who convert carries and short targets into new sets of downs. That means a back who earns 14 meaningful touches with short-yardage and goal-line equity can outscore a more target-heavy but less trusted satellite back even when the latter looks more exciting in generic dynasty discourse.

RB risk flags should fire on late capital plus weak receiving, on poor size/BMI without receiving-ace traits, on old non-early entrants, and on profiles that need immediate volume but have poor rookie opportunity. Upside flags should trigger when a back has real draft capital and at least one of two fantasy-winning paths: elite receiving impact or elite goal-line/chain-moving power. Floor flags should require enough capital, enough touch-earning evidence, and enough role trust to avoid disappearing the moment pass protection or short-yardage work matters. citeturn30view0turn43view0

The LVE RB draft bands should be the most aggressive of any position. Scores of 90 or higher are valid top-8 overall picks. Scores of 82-89 are strong first-round values. Scores of 74-81 fit the late first or early second. Scores of 66-73 belong in the second or third. Scores below 58 are usually Round 4-5 or veteran-compare-only bets. The do-not-draft-before rule is: **do not draft an RB with rookieOpportunity below 55 ahead of a released veteran RB/WR benchmark that beats him by 8 or more**, unless his longTermDynasty score is 80 or higher and his confidence is above 70. That rule protects you from taking committee projections over immediately startable veteran value.

## Wide receivers

Wide receiver is where the best open evidence exists for a deterministic prospect model. Older work found college statistics more predictive than combine data for wide receivers, with total college touchdowns, final-year share, and BMI carrying more signal than the 40 or school label once actual NFL performance was the target. Newer analyst work finds that yards per route run, production quality grades, and some role-robustness variables such as contested efficiency and reduced behind-the-line usage carry more predictive value than many traditional box-score stats, while early-declare plus draft-capital buckets remain the strongest fantasy-success cohorts. First-downs per route and similar chain-moving stats also look meaningfully predictive in modern receiving studies and are already being used in current rookie models. citeturn27view0turn37view0turn11view4turn32view0turn35view2turn36search3

That fits your league almost perfectly. LVE starts 3 WR and 2 flex, which pushes weekly WR demand up. At the same time, no PPR means you should not blindly pay for catch counts. The winning WR archetype in this league is the player who earns routes, earns targets, moves chains, and can still bring touchdowns or explosive plays. So the formula should emphasize dominance, target earning, age trajectory, and first-down translation more than raw receptions.

```ts
interface WRNormalizedInputs {
  draftCapital: Score;
  efficiencyDominance: Score;     // YPRR, YPTPA, receiving yards market share
  ageTrajectory: Score;           // age at draft, breakout age, early declare
  chainMoving: Score;             // 1D/RR or proxy, TD share, drive-sustaining profile
  targetEarning: Score;           // target share, TPRR
  filmQuality: Score;             // production quality / route skill / PFF-like grade
  roleRobustness: Score;          // contested catch, low behind-LOS reliance, alignment
  athleticism: Score;             // speed, agility, burst
  returnValue: Score;
  projectedRouteShare: Score;
  depthChartVacancy: Score;
  qbEnv: Score;
  teamPassRateEnv: Score;
  alignmentFit: Score;
  durability: Score;
  overallPick: number;
}

function scoreWR(input: WRNormalizedInputs, vets: VeteranValue[], ctx: LeagueContext): PositionScoreResult {
  let mainProspect = wa([
    [input.draftCapital, 26],
    [input.efficiencyDominance, 20],
    [input.ageTrajectory, 16],
    [input.chainMoving, 12],
    [input.targetEarning, 10],
    [input.filmQuality, 8],
    [input.roleRobustness, 4],
    [input.athleticism, 4],
  ]); // 100

  const exceptionalWR =
    input.efficiencyDominance >= 85 &&
    input.ageTrajectory >= 80 &&
    input.targetEarning >= 75;

  if (input.overallPick > 150 && !exceptionalWR) {
    mainProspect = clamp(mainProspect * 0.90);
  }

  const leagueFit = wa([
    [input.chainMoving, 30],
    [input.projectedRouteShare, 25],
    [input.efficiencyDominance, 20],
    [input.filmQuality, 15],
    [input.returnValue, 10],
  ]);

  const rookieOpportunity = wa([
    [input.projectedRouteShare, 35],
    [input.depthChartVacancy, 25],
    [input.qbEnv, 15],
    [input.teamPassRateEnv, 15],
    [input.alignmentFit, 10],
  ]);

  const longTermDynasty = wa([
    [input.ageTrajectory, 35],
    [input.targetEarning, 25],
    [input.efficiencyDominance, 20],
    [input.draftCapital, 10],
    [input.roleRobustness, 10],
  ]);

  const tradeInsulation = wa([
    [input.draftCapital, 55],
    [input.ageTrajectory, 20],
    [input.targetEarning, 15],
    [input.filmQuality, 10],
  ]);
}
```

The biggest anti-trap rule for WR is straightforward: **do not overweight pure receptions or manufactured-touch usage in a no-PPR league**. The newer WR evidence is useful here because it separates broad dominance from gimmick volume. If a prospect’s production is heavily built on behind-the-line targets, low-depth manufactured touches, or single-role usage, that should show up as a drag inside **roleRobustness**, not as a bonus through raw catch totals. Conversely, chain-moving and target-earning metrics deserve real weight because your scoring explicitly rewards meaningful receiving work. citeturn37view0turn35view2

WR risk flags should fire for older prospects without early breakout, for gadget-heavy profiles with weak rate production, for athletic-only prospects with poor target earning, and for low-capital players who need a perfect landing spot to clear route thresholds. Upside flags should require some combination of strong draft capital, strong age trajectory, and strong efficiency dominance. Floor flags should require target earning, route share, and enough draft capital that the player will keep getting chances. citeturn27view0turn37view0

Because of your lineup structure, WR should remain very live throughout the first two rounds of the combined board. Scores of 90 or higher are valid top-8 overall picks. Scores of 82-89 are solid first-round values. Scores of 74-81 should cluster in the late first and second. Scores of 66-73 are ideal Round 3 values. The do-not-draft-before rule is softer here than at QB or TE: **only delay a WR when veteranOpportunityAdj is -6 or worse and rookieOpportunity is below 55**. Otherwise, the combination of lineup demand and deep-bench dynasty value justifies more patience at WR than at most other positions.

## Tight ends

Tight end needs the harshest structural suppression after quarterback. A deep dynasty bench does make TE patience more tolerable, but your scoring format does not give tight ends any premium, only starts one, and still allows RB/WR/TE in flex. Open research on tight ends shows three important things. First, the variables teams use to draft TEs are not the same as the variables that best predict later NFL production. Second, college receiving production and efficiency matter more than many teams historically priced them. Third, first-round TEs have dramatically better breakout odds than second-round and later TEs, which means capital should dominate the fantasy side even if size and athleticism matter in real football. citeturn24view1turn24view2turn24view4turn35view1

That is exactly why an LVE TE formula should be strict: heavy draft-capital weight, heavy receiving-role scrutiny, and a hard suppression of Day 3 profiles unless the receiving case is genuinely exceptional. The model should not chase every athletic “move TE.” It should reward prospects who project to earn routes, stay on the field, and either command targets or dominate high-value areas.

```ts
interface TENormalizedInputs {
  draftCapital: Score;
  receivingEfficiency: Score;   // YPRR, YPTPA, 1D/RR
  productionVolume: Score;      // market share, TD share, final-year growth
  ageTrajectory: Score;         // younger entry / younger draft age
  routeRole: Score;             // route participation, slot/wide usage, real route volume
  athleticSize: Score;          // size + speed/shuttle + functional frame
  redZoneRole: Score;
  blockingStayOnField: Score;   // enough to stay on the field when needed
  depthChartRoutes: Score;
  twelvePersonnelEnv: Score;
  qbEnv: Score;
  redZonePath: Score;
  durability: Score;
  overallPick: number;
}

function scoreTE(input: TENormalizedInputs, vets: VeteranValue[], ctx: LeagueContext): PositionScoreResult {
  let mainProspect = wa([
    [input.draftCapital, 36],
    [input.receivingEfficiency, 20],
    [input.productionVolume, 14],
    [input.ageTrajectory, 10],
    [input.routeRole, 10],
    [input.athleticSize, 10],
  ]); // 100

  const exceptionalTE =
    input.receivingEfficiency >= 85 &&
    input.routeRole >= 75 &&
    input.athleticSize >= 70 &&
    input.ageTrajectory >= 65;

  if (input.overallPick > 120) {
    mainProspect = clamp(mainProspect * (exceptionalTE ? 0.82 : 0.62));
  }

  const leagueFit = clamp(
    10 +
    0.35 * input.receivingEfficiency +
    0.20 * input.routeRole +
    0.20 * input.redZoneRole +
    0.15 * input.blockingStayOnField +
    0.10 * input.athleticSize
  );

  const rookieOpportunity = wa([
    [input.depthChartRoutes, 30],
    [input.twelvePersonnelEnv, 20],
    [input.qbEnv, 15],
    [input.redZonePath, 20],
    [input.blockingStayOnField, 15],
  ]);

  const longTermDynasty = wa([
    [input.draftCapital, 30],
    [input.ageTrajectory, 20],
    [input.receivingEfficiency, 20],
    [input.routeRole, 20],
    [input.athleticSize, 10],
  ]);

  let tradeInsulation = clamp(wa([
    [input.draftCapital, 70],
    [input.routeRole, 15],
    [input.receivingEfficiency, 15],
  ]) - 8);

  if (input.overallPick > 120) {
    tradeInsulation = clamp(tradeInsulation * (exceptionalTE ? 0.70 : 0.40));
  }
}
```

The LVE TE formula is intentionally severe because the league format is severe on the position. The baseline inside **leagueFit** starts low on purpose. That does not mean the model is anti-TE. It means the model needs a proof burden. A TE has to show capital, receiving skill, route path, and some path to staying on the field. This keeps you from reaching on developmental TE types purely because deep benches make them easier to hold.

TE risk flags should fire for any pick-121+ TE who does not clear the exceptional gate, for older prospects with mediocre receiving production, and for players who project as rotational blockers rather than route earners. Upside flags should primarily belong to Day 1 or strong Day 2 players with high receiving efficiency and real route-role evidence. Floor flags should require draft capital, playable blocking utility, and a realistic route path. citeturn24view0turn35view1

For draft management, the TE rule should be the strictest on the board: **never draft a TE before pick 16 unless Final LVE is at least 90, veteranOpportunityAdj is better than -3, and the player clears the exceptional-TE gate**. Scores of 82-89 fit the Round 2-3 range. Scores of 74-81 are Round 4 targets. Scores below 66 are usually post-draft or watchlist TEs in this format.

## Cross-position draft board logic

After each position is scored, do not create a “rookie board” and then separately eyeball released veterans. Create one combined acquisition board. Score every rookie with the formulas above. Score every released veteran with your veteran model or manual LVE ranking. Then sort the combined pool by final score and draft the highest score unless your roster-specific build rules say otherwise.

```ts
interface DraftableEntry {
  id: string;
  kind: 'rookie' | 'veteran';
  position: Pos;
  finalLveScore: Score;
  confidence: Score;
}

function combinedDraftBoard(entries: DraftableEntry[]): DraftableEntry[] {
  return [...entries].sort((a, b) => b.finalLveScore - a.finalLveScore);
}
```

Use these overall score bands for the 50-pick LVE draft:

- **90-100**: top-8 overall acquisition candidates
- **84-89**: strong Round 1 values
- **78-83**: late Round 1 to early Round 2
- **72-77**: Round 2
- **66-71**: Round 3
- **60-65**: Round 4
- **54-59**: Round 5 / final-stash territory
- **below 54**: post-draft free-agent pool unless roster-specific need says otherwise

Then apply the position gates:

- **QB**: push down until pick 11 unless elite
- **RB**: no structural push-down; allow true early selections
- **WR**: no structural push-down; this is the safest volume position in your format
- **TE**: push down until pick 16 unless elite

A simple board-level pseudo-code version looks like this:

```ts
function draftSlotAdjustment(pos: Pos, finalScore: Score, confidence: Score, eliteGate: boolean): number {
  if (pos === 'QB' && !(finalScore >= 92 && confidence >= 75 && eliteGate)) return 10;
  if (pos === 'TE' && !(finalScore >= 90 && confidence >= 72 && eliteGate)) return 15;
  return 0;
}
```

The reason this matters is not abstract theory. In a 10-team 1QB format with 3 WR and 2 flex, the marginal difference between QB7 and QB14 is often less important than the difference between an extra usable WR/RB and a bench clogger. At the same time, the forced-release rule can create veteran values that would never exist in a conventional rookie-only board. This is exactly where deterministic models win: they stop you from drafting “pick value” when the room is actually offering player value.

## Open questions and limitations

Two limitations matter enough to encode explicitly. First, running back evidence is directionally useful but less cleanly open and less standardized than the quarterback/wide receiver evidence base. Some useful RB inputs in practice come from analyst models rather than peer-reviewed papers, so those inputs should have medium evidence tags and moderate weights, not dictator weights. citeturn43view0turn30view0turn39view0

Second, college first-down and route-level public data is improving quickly, but historical availability is still less mature than draft capital, age, or standard production. That means first-down-based prospect inputs should absolutely exist in LVE because your scoring rewards them, but they should usually sit as secondary weights or confidence modifiers unless your local dataset is deep enough to validate stronger treatment. citeturn35view2turn13search6turn36search3

The safest implementation posture is therefore: **make draft capital the largest single input, make role/efficiency the largest non-capital input, cap landing spot, punish low-capital QB and TE aggressively, elevate WR/RB demand through the LVE overlay, and always compare a rookie to the actual released-veteran pool before you spend the pick.**