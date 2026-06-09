# Phase 5 Review of Niners Dynasty War Room

## Executive Verdict

The overall direction is sound. A local-first, deterministic, table-first model is a good fit for a one-league dynasty tool because it keeps the system auditable, reproducible, and portable. A CSV-first approach is also appropriate, but only if you make table relations, field types, and provenance explicit rather than implicit in application code. The entity["organization","W3C","web standards body"] tabular-metadata recommendation and the Table Schema specification both exist for exactly this problem: giving tabular data enough structure to validate, relate, and display reliably. For override history and provenance, the entity["organization","U.S. Food and Drug Administration","US regulator"] guidance on computerized records is not domain-specific to fantasy football, but it is highly relevant as a model for “who changed what, when, and why,” and for preserving prior values instead of overwriting them. citeturn2view5turn2view6turn13view0

Where the current plan starts to wobble is not at the league logic level, but at the modeling architecture level. The design currently tries to answer at least five different questions with one continuous score: prospect quality, LVE scoring fit, rookie-year usage, long-term dynasty value, and market/trade insulation. The research base on the entity["organization","NFL","American football league"] draft is a warning sign here. Across offensive-skill studies, the traits that move players up draft boards are not always the same traits that predict later productivity, and in several position-specific papers researchers explicitly conclude that teams overvalue some traits and undervalue others. That means a model like yours gets stronger when it separates “what the player is,” “what the league rewards,” and “what the market will still pay for later,” instead of letting those concepts bleed into one another. citeturn12view0turn7view0turn10view2turn5view3

My verdict is therefore:

| Question | Verdict |
|---|---|
| Is the directionally correct? | Yes |
| Is it overcomplicated for V1? | Yes, mildly to materially |
| Is the CSV/schema approach appropriate? | Yes, if registry-driven and relation-explicit |
| Is the veteran-opportunity-cost layer necessary? | Yes, absolutely for this league |
| Is QB/TE suppression justified? | Yes, but it should be explicit and defeasible |
| Biggest pre-implementation problem | Double-counting and source reliability |

The veteran-opportunity layer is not optional in LVE. Because the rookie draft happens after roster declaration, and because each manager must release at least one top-five official player, your real draft pool is not “rookies only.” It is “rookies plus whatever productive veterans and free agents the forced-release system creates.” That means rookie scoring by itself is insufficient. But the veteran layer should be an external comparison layer, not a trait inside the rookie’s talent formula. Treating it as a peer benchmark instead of a feature is the cleanest way to preserve explainability.

The QB and TE suppression logic is also justified for LVE, but for league-structure reasons rather than because “QBs are bad” or “TEs never hit.” In a 10-team, 1QB league with no Superflex, start-one QB scarcity is modest; in a no-TE-premium league with one forced TE starter and flexible WR/RB/TE flex slots, elite TE seasons matter, but generic TE prospects should not be priced like scarce structural necessities. By contrast, three WR starters plus two flex spots increase weekly RB/WR demand, and no-PPR with 0.4 first downs rewards chain-moving and touchdown-linked usage more than raw catch volume. Those are the right strategic premises. The mistake would be turning them into hard-coded dogma instead of explicit gates and overlays.

## Major Risks

The biggest methodological risk is not “using the wrong football inputs.” It is using too many overlapping inputs, then letting those same concepts reappear in multiple score components. That is exactly the kind of architecture that feels detailed while quietly becoming unstable and hard to audit. The evidence-backed part of this concern is straightforward: draft studies repeatedly show that selection signals and later productivity signals overlap only partially, and combine work shows that the useful athletic signals are narrower and more position-specific than many models assume. citeturn12view0turn7view0turn2view0turn10view2

| Risk area | Severity | Why it matters | Concrete fix |
|---|---|---|---|
| Double-counting across score components | High | Draft capital, age trajectory, and production can easily reappear in `main_prospect_score`, `long_term_dynasty_score`, and `trade_insulation_score`, making the system look nuanced while mostly repeating the same signal | Make each component answer one question only; enforce a registry rule that a raw feature can be “core-weighted” in only one parent component |
| Draft capital used as both talent and market value | High | Research consistently shows draft order carries real information, but also that teams misprice some traits; if you let draft capital dominate both prospect score and trade insulation, you are rewarding the same market signal twice citeturn12view0turn7view0turn10view2 | Keep draft capital as a core input in `main_prospect_score`; in `trade_insulation_score`, use only the *residual* market persistence logic, or sharply cap capital’s contribution there |
| Veteran opportunity treated as a player feature | High | A rookie’s talent should not rise or fall because a released veteran exists; that is a board-management question, not a prospect-truth question | Compute rookie score first, then compare it against veteran benchmarks on the same 0–100 decision scale |
| Missing-data defaults flatten the board | High | A universal default of 50 for missing core fields can make incomplete prospects look artificially average, especially for Day 3 players | Keep neutral imputation for arithmetic stability, but increase confidence penalties, add visible incompleteness flags, and optionally cap final score when too many core fields are missing |
| Route-derived and first-down-derived prospect metrics may be hard to source locally | High | If routes run, target-per-route, route participation, or first-down profiles are inconsistent across imported datasets, your most “advanced” features become garbage-in-garbage-out | Only promote route-derived metrics to core when the local data source is stable and consistent across the class; otherwise make them secondary or confidence modifiers |
| Landing spot leakage into talent score | High | Post-draft team context is real, but if it enters the prospect core, the model stops being a prospect model and starts becoming a season projection model | Keep landing spot, depth chart, and offensive environment strictly in `rookie_opportunity_score` or a post-draft overlay |
| Manual overrides without provenance | High | Unlogged overrides are the fastest way to destroy trust in a deterministic system | Require immutable note rows with author, timestamp, field changed, old value, new value, reason, and source reference; never overwrite raw values in place citeturn13view0turn2view5 |
| Static QB/TE gates that ignore exceptional profiles | Medium | A hard “never before pick X” rule can miss legitimate outlier prospects | Keep gates, but define explicit exceptional override criteria tied to core metrics and veteran opportunity |
| Huge audit table becoming unreadable | Medium | Auditability fails if users cannot find the rows that actually drove the score | Sort by component and weighted contribution, add filters, and pin explanatory columns; do not dump every raw field by default |
| Too many committed CSV artifacts | Medium | If generated score files are committed, they drift from formulas and create diff noise | Commit inputs, registry, and benchmarks; generate feature scores and model outputs at runtime or during test fixtures only |
| User-editable weights and registry logic | Medium | If the same UI that displays outputs can casually edit scoring logic, reproducibility disappears | Treat registry weights and logic columns as versioned configuration, not ordinary user edits |
| Return-game scoring overfitting | Low to Medium | LVE awards return yards and return TDs, but many offensive prospects lose return work once their offensive role grows | Keep return value as a tiny rookie-only upside flag or tiebreaker, not a core score driver |

The model’s strategic premises for LVE are mostly right. The danger is that your implementation might accidentally turn them into correlated score inflation. That is the key thing to protect against before you write any UI.

## Formula Review

The strongest evidence-backed improvement from the research set is at quarterback. In the college-QB literature, older work found that pre-draft college and combine data were weak predictors of later NFL success and argued that much of the variance is simply hard to observe in advance. More recent econometric work on college quarterbacks found that passing ability matters most for making an NFL roster, but rushing ability matters more for differentiating which drafted quarterbacks actually succeed, and that scouts appear to undervalue rushing relative to later NFL outcomes. In other words: draft capital and passing competence matter for entry, but rushing is the clearest place where a fantasy model can outperform a generic scouting consensus. citeturn10view2turn11view0

### Quarterback

Your QB formula is strongest when it suppresses generic pocket passers in 1QB, heavily values rushing profile, and treats sack avoidance as a real signal rather than a cosmetic one. That is the right orientation for LVE.

What looks questionable is a QB formula that separately scores passing efficiency, adjusted yards per attempt, raw accuracy, big-time throw rate, turnover-worthy play rate, pressure-to-sack rate, and film grade all at core weight. For a deterministic local-first app, that is too many partially overlapping passing-quality proxies. The research base does not support the idea that ever more quarterback submetrics automatically produce a stronger rookie-draft model; if anything, the literature warns that a lot of pre-draft QB information is weakly predictive, while rushing adds actionable separation. citeturn10view2turn11view0

What I would simplify: reduce QB core to five things—draft capital, rushing profile, passing efficiency composite, sack avoidance composite, and age trajectory. Make film grade secondary. Make landing spot strictly post-draft. Make the “elite QB exception” explicit instead of letting a bunch of passing micro-metrics sneak a low-scarcity QB up the board.

What I would add: a clear exceptional-gate test. Something like “QB gate can only be beaten if draft capital is premium *and* either rushing is elite or the player clears a very high passing-plus-sack-avoidance threshold.” That preserves the 1QB structural push-down without making it arbitrary.

The current LVE weighting idea is reasonable only if a good pocket QB still usually loses to comparably strong RB/WR profiles in the same decision band.

### Running Back

Your RB formula is structurally in the best place. LVE does not justify a blanket push-down at RB, and the league scoring makes real touches, first downs, goal-line work, and touchdown access matter more than pure reception volume. That is exactly the right lens for a no-PPR, first-down-scoring format.

Where I would push back is excessive decomposition. If the model separately weights carries, targets, receptions, route participation, receiving yards, receiving market share, first-down profile, missed tackles forced, yards after contact, explosive rate, success rate, short-yardage role, and goal-line role, the RB architecture becomes too crowded. Those are not all separate truths. Several of them are manifestations of workload earning or role quality.

The cleaner approach is to merge the underlying ideas into a smaller set of canonical RB features: workload earning, receiving impact, rush efficiency, goal-line/short-yardage power, athletic burst, age trajectory, and draft capital. In LVE, receiving impact should stay in the model, but it should not be weighted like a full-PPR league. A receiving back who catches five dump-offs for low leverage is less valuable here than a back who earns high-share touches, converts first downs, and gets touchdown work.

What I would add is an earlier veteran benchmark check at RB than at WR. Forced-release leagues often produce usable veteran RBs, and because LVE is not PPR-driven, the rookie satellite back archetype becomes easier for released veterans to beat in pure startability.

The current broad RB direction is good. The main implementation risk is feature crowding, not philosophy.

### Wide Receiver

The WR side is the best fit for your league context. LVE starts three WRs and two flexes, so the model should be structurally comfortable ranking strong WR prospects aggressively. The evidence base also supports anchoring WR evaluation in college production and efficiency rather than in shallow size-and-athleticism heuristics. In the WR research you surfaced, speed and college production were consistently relevant, while several other combine-style measurements were much less important. The broader draft literature also supports the idea that draft-day determinants and later productivity determinants overlap only partially, which is another reason to prefer target earning and efficient production over a bloated athletic checklist. citeturn5view3turn12view0turn2view0

What looks questionable is giving separate core weights to `efficiency_dominance`, `target_earning`, `chain_moving`, `role_robustness`, `receiving_market_share`, `yards_per_team_pass_attempt`, `target_share`, `dominator`, and `touchdown_share`. That is too many ways of rewarding the same receiver for being productive and central to his offense.

What I would simplify: choose one production/efficiency bucket and one earning bucket. For example, let `efficiency_dominance` absorb YPRR plus a production-market-share element, and let `target_earning` absorb target share and route-level earning where your data source is trustworthy. Then keep `age_trajectory`, `draft_capital`, and a smaller `role_robustness` or `film_quality` overlay. If first-down conversion data exists, `chain_moving` can stay, but it should not quietly duplicate the same slot/possession archetype already rewarded by target earning.

What I would add is a tiny rookie-only return-value upside overlay because LVE does score return yards and return TDs. But that should be small, probably a tiebreaker or upside flag, because return roles are unstable once offensive roles consolidate.

The WR weights are conceptually the most reasonable for LVE. If any position deserves the highest adjusted board presence here, it is usually WR, not QB or TE.

### Tight End

The TE suppression logic is justified, and the research supports being selective. The tight-end literature you cited found that measures most predictive of draft order are not the same as measures most predictive of career success, and specifically concluded that size measures like BMI, weight, and height are overemphasized by the NFL draft market. That is exactly the kind of finding that should keep athletic-size features in check. citeturn7view0

What looks questionable is a TE formula that keeps `athletic_size`, BMI, height thresholds, hand size, speed score, burst, and broad jump all live as weighted core inputs. In a no-TE-premium league, that is too much optimism for a position that already has less structural scarcity in your format.

What I would simplify: draft capital, receiving efficiency, route role, production volume, and age trajectory should do most of the work. `athletic_size` is useful as a gate-helper, not as a free source of extra points. A Day 3 TE should remain heavily suppressed unless the receiving profile is extremely unusual and the post-draft path to routes is unusually clean.

What I would add is an explicit exceptional TE gate, not just a soft score bump. If a TE is going to break the positional suppression in LVE, the model should be able to say exactly why: premium draft capital, strong evidence of real receiving ability, probable route role, and favorable veteran comparison.

What I would remove from core weighting: standalone BMI, hand size, and broad-body proxies. The research cuts against making those central. citeturn7view0

## Feature Review

The feature registry needs pruning more than expansion. The evidence-backed reason is simple: both the WR and TE studies support the idea that some physical and combine traits influence draft position more than actual future performance, while the combine study for RBs and WRs shows that useful athletic signals exist but are relatively narrow and position-specific. That argues for a smaller canonical feature set with raw metrics feeding composites, not a sprawling list where every raw stat gets independent weight. citeturn5view3turn7view0turn2view0

### Duplicate and overlapping features that should be merged

| Overlap cluster | Current pattern | Recommended merge |
|---|---|---|
| Age-related features | age, breakout_age, early_declare | `age_trajectory` |
| WR production share features | dominator, market_share, receiving_yards_market_share, touchdown_share, yards_per_team_pass_attempt | `efficiency_dominance` or `production_dominance` |
| WR earning features | target_share, targets_per_route_run, route participation | `target_earning` |
| RB usage volume features | carries, targets, receptions, route participation, touch share | `workload_earning` plus `receiving_impact` |
| RB efficiency family | missed_tackles_forced, yards_after_contact, explosive_play_rate, success_rate | `rush_efficiency` |
| QB negative-play family | pressure_to_sack_rate, sack_avoidance, sack EPA style measures | `sack_avoidance` |
| Athletic testing family | forty, burst, agility, speed_score, RAS | `athleticism` with position-specific subrules |
| TE role features | routes, target rate, slot rate, receiving usage | `route_role` |

### Features that should be display-only or sharply downgraded

Conference label, raw team pace, college pass rate environment, hand size, catch radius, raw games played, bowl pedigree, and broad “competition level” buckets should not be core weighted unless you have hard evidence that the local source is stable and the effect is incremental after the main features. They are useful context rows in the audit table, but not the center of the formula. The WR study you referenced is particularly helpful here because it points away from some of the body-measure clutter and toward speed plus real production. citeturn5view3

### Features that should move from core to secondary

Film grades, composite athletic scores, injury/durability, return-game value, and offensive-environment adjustments should generally move down a tier. They are not useless. They are either hard to source consistently, highly context-dependent, or too easy to double-count via other features.

### Features that should move from secondary into confidence or risk handling

Injury history, missing combine data, small-school competition context, and uncertain route-denominator metrics belong more naturally in confidence/risk than in raw score contribution. If a strong prospect lacks stable route data, the right response is usually “same central score, lower confidence,” not “pretend the missing value is fully average and move on.”

### Missing features that matter

The most important “missing” concept is not an additional football stat. It is source reliability. The registry needs a notion of whether a feature is consistently available across the class and whether it is allowed to affect the score when the underlying denominator is unstable. In practice, that means something like `data_quality_tier`, `requires_routes`, `post_draft_only`, and `manual_entry_allowed`.

A second missing concept is roster-path evidence for late-round skill players. In a league that scores return yards and has deep benches, “can plausibly make the game-day roster through special teams or return work” is a legitimate upside flag for Day 3 WRs and RBs, and a weaker version of that logic matters for TE route paths as well.

### Features that may be impossible or impractical to source reliably

Targets per route run, route participation, first-down profile, pressure-to-sack rate, big-time throw rate, turnover-worthy play rate, and some film-derived role grades are all potentially excellent features in theory. They are also exactly the kind of fields that become implementation traps in a local-first app if they depend on licensed datasets, inconsistent providers, or manual backfills that are not reproducible. If you do not yet have a stable local source for those metrics, they should not be core in V1.

## CSV Schema Review

Your CSV-first plan is appropriate, but the schemas need more relational structure and stricter provenance controls. The entity["organization","W3C","web standards body"] recommendation on tabular metadata and the Table Schema spec both emphasize that tabular data becomes much more reliable when types, constraints, and relationships are explicit. The FDA guidance adds an important design rule for overrides and audit notes: changes should preserve prior information and record who changed what, when, and why. Those ideas map cleanly to a deterministic fantasy model. citeturn2view5turn2view6turn13view0

| CSV file | Keep? | Commit to repo? | Main problems | Recommended changes |
|---|---|---|---|---|
| `rookie_prospect_inputs.csv` | Yes | Yes | Usually lacks stable IDs, source provenance, and data-status fields | Add `player_id`, `class_year`, `position`, `source_snapshot_id`, `source_name`, `source_date`, `entered_by`, `entered_at`, `data_completeness_status` |
| `rookie_feature_registry.csv` | Yes | Yes | Risk of using mutable text labels as keys | Add stable `feature_id`; keep `feature_name` display-friendly; include `parent_component`, `is_core`, `is_generated`, `post_draft_only`, `requires_source_type`, `editable=false` columns |
| `rookie_feature_scores.csv` | Yes | **No** as a committed artifact | This is derived data and will drift | Generate at runtime or in tests only; if persisted, require `player_id`, `feature_id`, `model_version`, `normalized_score`, `weighted_contribution`, `missing_flag` |
| `rookie_model_outputs.csv` | Yes | **No** as a committed artifact | Also derived; prone to stale diffs | Generate only; include `model_version`, `final_decision_score`, `confidence_score`, `gate_applied`, `gate_reason`, `recommended_pick_min`, `recommended_pick_max`, `recommended_range_label` |
| `veteran_opportunity_benchmarks.csv` | Yes | Yes | Needs explicit benchmark semantics | Add `benchmark_id`, `position`, `benchmark_type`, `source_date`, `score_scale`, `benchmark_min`, `benchmark_max`, `position_cap`, `notes` |
| `rookie_audit_notes.csv` | Yes, with limits | Yes | Too vague unless provenance is strict | Add `note_id`, `player_id`, `field_name`, `old_value`, `new_value`, `reason`, `source_key`, `author`, `created_at`, `is_override`, `override_scope` |

### Unnecessary or risky columns

A comma-joined `citation_links` cell inside several core CSVs is usually the wrong shape. It is human-readable, but it is brittle. Better options are a semicolon-delimited `source_keys` column or a separate provenance table later. Likewise, storing “friendly” range text like `late_round_three_to_mid_round_four` without numeric pick bounds makes testing harder than necessary.

### Missing columns that should be added before coding

You are missing a stable identity layer. At minimum, `player_id`, `feature_id`, `model_version`, and `source_snapshot_id` should exist. Without them, rename operations and historical comparisons become painful.

You are also missing generated/output state markers. I would add `gate_applied`, `gate_reason`, `exceptional_profile_flag`, `veteran_delta`, and `data_completeness_status`. Those fields materially improve explainability.

### Validation gaps

Weight sums should be testable by position and by component. Feature IDs must be unique. Output scores must be clamped to 0–100. Generated files must not become editable source-of-truth artifacts. Post-draft-only features must be null or ignored in pre-draft mode. Rejected/display-only features must never contribute numerically.

### Fields that should not be user-editable

`default_weight`, `min_weight`, `max_weight`, `expected_direction`, `evidence_strength`, `is_core_feature`, `is_post_draft_feature`, `is_rejected_or_display_only`, `normalized_score`, `weighted_contribution`, `confidence_score`, `final_decision_score`, and all gate outputs should be formula- or registry-driven, not casually editable.

### Fields that should be generated rather than committed

`rookie_feature_scores.csv` and `rookie_model_outputs.csv` should be generated. If you commit them, you will create a permanent maintenance problem where a schema tweak or weight change forces massive unrelated diffs.

## Minimum Deterministic Test Plan

Before UI work, you need a proper engine test suite, not just a set of sample players. This is exactly the kind of project where `pytest` is a good fit because it is built for small, readable tests and scales cleanly to parametrized cases and fixture-driven validation. citeturn2view4

| Test group | Minimum assertions |
|---|---|
| Helper math | `clamp()` boundaries, weighted-average behavior, zero-weight protection, rounding behavior |
| Missing-data logic | Neutral imputation works, confidence drops correctly, caps trigger when too many core fields are missing |
| Registry integrity | Feature IDs unique, no display-only feature has nonzero live weight, weights stay within min/max |
| Position formulas | One golden fixture each for QB, RB, WR, TE returns expected subscore bands |
| QB gate | Non-elite 1QB pocket QB is suppressed; exceptional QB can beat gate only when explicit criteria are met |
| TE gate | Day 3 TE remains suppressed; elite-capital and elite-receiving-profile TE can beat gate only when both sides of gate pass |
| Veteran adjustment | Position caps enforced; rookie score is compared against benchmark without mutating prospect subscore internals |
| Landing spot isolation | Changing landing spot cannot alter `main_prospect_score` |
| Display-only isolation | Editing a display-only feature changes the audit table but not any score |
| Recommended range logic | Numeric min/max and label stay consistent |
| Do-not-draft-before logic | Output reflects position gate and exception logic deterministically |
| Audit contribution math | Sum of weighted feature contributions equals component score within tolerance |
| Manual override provenance | Any override produces a note row, preserves old value, records author and timestamp |
| Regression snapshots | Fixed fixture class continues to return the same scores across refactors unless model version changes |

The minimum fixture set you already described is good and should be preserved. I would require at least these golden cases before UI: elite rushing QB, good pocket QB suppressed in 1QB, premium three-down RB, satellite RB downgraded in no-PPR, elite WR, older volume WR with weak earning, elite exception TE, suppressed Day 3 TE, rookie losing to veteran cost, and rookie beating veteran cost.

## Simplified V1 and Implementation Order

The current plan is larger than it needs to be for a trustworthy first release. A smaller V1 can preserve nearly all of the important LVE behavior while cutting the risk surface materially.

### Simplified V1 recommendation

Commit only the source-of-truth tables. Generate everything else. That means:

| V1 data layer | Status |
|---|---|
| `rookie_prospect_inputs.csv` | Commit |
| `rookie_feature_registry.csv` | Commit |
| `veteran_opportunity_benchmarks.csv` | Commit |
| `rookie_audit_notes.csv` | Commit only if you are truly using manual notes/overrides in V1 |
| `rookie_feature_scores.csv` | Generate |
| `rookie_model_outputs.csv` | Generate |

For V1, I would keep the output model shape but reduce raw feature count.

| Position | Minimum V1 core features |
|---|---|
| QB | `draft_capital`, `rushing_profile`, `passing_efficiency`, `sack_avoidance`, `age_trajectory` |
| RB | `draft_capital`, `workload_earning`, `rush_efficiency`, `receiving_impact`, `goal_line_power`, `age_trajectory` |
| WR | `draft_capital`, `target_earning`, `efficiency_dominance`, `age_trajectory`, `chain_moving` |
| TE | `draft_capital`, `receiving_efficiency`, `route_role`, `production_volume`, `athletic_size`, `age_trajectory` |

For V1, I would also simplify two outputs:

First, let `trade_insulation_score` be mostly a controlled function of draft capital and age trajectory instead of a second full feature stack.

Second, let `league_fit_score` be a compact position-and-scoring overlay rather than another place where the same workload and production stats are rescored.

What to postpone: raw route-denominator features when source stability is uncertain; broad athletic submetrics; rich film grades; handwritten historical note integration into scoring; any override system that cannot produce proper provenance.

### Safest implementation order

| Step | Goal | Done condition |
|---|---|---|
| Step one | Add schemas, enums, and docs only | CSV docs and validation contracts exist; no scoring yet |
| Step two | Add registry loader and deterministic helpers | Clamp, normalization, missing-data, and weighted-average tests pass |
| Step three | Add position formulas and gates | QB/RB/WR/TE formulas produce deterministic outputs from fixtures |
| Step four | Add veteran comparison layer | Veteran benchmark comparison works with caps and does not mutate prospect cores |
| Step five | Add sample rookie fixtures and regression tests | Golden fixtures pass and model version is explicit |
| Step six | Add compact rookie board | Board displays generated outputs only |
| Step seven | Add huge audit table | Per-feature contributions reconcile to component scores |
| Step eight | Add overrides and provenance notes | Manual changes are logged immutably and never overwrite raw source fields |

This order avoids dependency churn, avoids committing generated artifacts, and gets the scoring engine trustworthy before any presentation layer becomes expensive to change.

## Final Recommended Spec Changes

Before coding, I would change Phase 4 in the following exact ways.

1. Reclassify `veteran_opportunity_adjustment` from a “score component” to an external comparison overlay that operates after the rookie’s internal scores are complete.

2. Make `rookie_feature_scores.csv` and `rookie_model_outputs.csv` generated-only artifacts. Do not commit them.

3. Add stable identifiers everywhere: `player_id`, `feature_id`, `model_version`, `source_snapshot_id`.

4. Reduce each position to five to six canonical core features. Feed composites from raw data, but do not weight every raw data point independently.

5. Prevent a raw feature from being core-weighted in more than one parent component. This single rule will eliminate most silent double-counting.

6. Make `landing_spot`, `depth_chart_opportunity`, and similar context variables post-draft only, and forbid them from touching `main_prospect_score`.

7. Separate `confidence_score` from `final_decision_score`; confidence may cap or warn on the final output, but it should not silently blur the meaning of the underlying player score.

8. Replace text-only recommendation outputs with numeric and label forms: `recommended_pick_min`, `recommended_pick_max`, `recommended_range_label`.

9. Add `gate_applied`, `gate_reason`, and `exceptional_profile_flag` to generated outputs so the board can explain why a QB or TE is being held down or allowed through.

10. Make unsupported or unstable metrics—especially route-derived, first-down-derived, and proprietary scouting fields—secondary until you confirm a reliable local source.

11. If overrides are in V1, require immutable provenance rows with old value, new value, author, timestamp, reason, and source key. If not, postpone overrides entirely.

12. Keep the compact rookie board in V1; keep the huge audit table in V1 as well, but launch it only after contribution reconciliation tests are green.

These changes make the model smaller, more testable, and more trustworthy without meaningfully weakening the league-specific logic that makes the project valuable.

## Open Questions

Only a handful of questions actually block implementation or materially change the model.

- What local source will provide route-derived metrics such as routes run, targets per route, route participation, and first-down profiles, and do you have the right to store and reuse that data locally?

- Is the veteran-opportunity layer comparing rookies against actual released players in the current draft pool, or against static position benchmark bands? This changes both schema and formula shape.

- What exact criteria define an “exceptional” QB or TE that can beat the structural gate? Without this, `do_not_draft_before_pick` logic remains subjective.

- Are film grades and scouting grades truly part of V1, and if so, who enters them and on what fixed 0–100 rubric?

- Do you want manual overrides in V1, or only provenance notes? If the answer is “overrides,” then a proper immutable override ledger is required before scoring code ships.

- Are pre-draft and post-draft runs separate model modes, or one pipeline with nullable post-draft fields? This determines whether landing spot and opportunity fields live in one input CSV or a separate post-draft layer.

Those are the questions I would answer before writing the core engine. Everything else can be deferred until after the deterministic model and regression tests are stable.