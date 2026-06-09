# Truth Set Lab v1 Preview Ranking Audit

Date: 2026-05-14

This audit compares the active stats-first preview against the Truth Set Lab dry run. It does not change active rankings, formulas, gates, roster decisions, or app outputs.

## Files Reviewed

- Dry-run preview: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\truth_set_model_dry_run_preview.csv`
- Truth-set rank comparison: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\truth_set_preview_rank_comparison.csv`
- Rejected fields: `C:\Dev\niners-war-room\local_exports\truth_set_lab\v1\reports\truth_set_model_dry_run_rejected_fields.csv`
- Active preview rankings: `C:\Dev\niners-war-room\local_exports\active_veteran_model_public_sources\stats_first_veteran_model_preview_outputs.csv`

## Executive Read

The new safe truth-set fields improve the audit picture but do not radically change the model. That is both good and bad.

Good: the dry run did not expose a catastrophic join or scoring explosion. All 40 truth-set players were evaluated, 37 used recomputed no-PPR LVE projection points, 17 used eligible young bridge prior, and zero players crossed the large-change threshold.

Bad: because movement is modest, the truth-set data does not by itself fix the deeper trust concerns. The remaining problems are mostly source coverage, stale/weak role inputs, formula balance, and a few suspicious source rows.

## Overall Movement

Largest model-value movements:

| player | pos | active | preview | delta | main cause |
|---|---:|---:|---:|---:|---|
| Josh Allen | QB | 57.32 | 61.74 | +4.42 | projection recompute |
| Bijan Robinson | RB | 75.14 | 78.93 | +3.79 | projection recompute plus bridge context |
| Jahmyr Gibbs | RB | 70.75 | 74.35 | +3.60 | projection recompute |
| Jayden Higgins | WR | 49.75 | 46.46 | -3.29 | projection recompute plus bridge context |
| Christian McCaffrey | RB | 61.14 | 64.42 | +3.28 | projection recompute |
| Chase Brown | RB | 54.38 | 57.59 | +3.21 | projection recompute plus bridge context |
| Kaleb Johnson | RB | 53.16 | 50.12 | -3.04 | projection recompute plus bridge context |
| De'Von Achane | RB | 66.14 | 69.01 | +2.87 | projection recompute plus bridge context |
| Luther Burden | WR | 49.48 | 46.90 | -2.58 | projection recompute plus bridge context |
| Oronde Gadsden II | TE | 26.26 | 24.10 | -2.16 | projection recompute plus bridge context |

Interpretation: the new fields mostly nudge the model. They do not create an immediate "trust unlock."

## Named Group Audit

### Niners Roster Players

The dry run is most useful for the young and bubble players:

- Brian Thomas Jr. remains a strong roster asset in both active and preview values.
- De'Von Achane rises from 66.14 to 69.01, which supports him as a meaningful hold/bubble-up asset rather than a cut-side player.
- Chase Brown rises from 54.38 to 57.59, mostly from projection recompute, but still does not jump into a core tier.
- Kaleb Johnson drops from 53.16 to 50.12. This is important: the safe truth-set data does not support the earlier worry that Kaleb should be treated as an especially strong fantasy asset right now.
- Luther Burden drops from 49.48 to 46.90. The model is still skeptical once raw projected LVE scoring replaces broad rookie enthusiasm.
- Jayden Higgins drops from 49.75 to 46.46. Same pattern: projection evidence is not yet strong enough to boost him.
- Lamar Jackson rises modestly from 54.68 to 56.49, but QB structural suppression still holds.
- Tight ends remain low, which is directionally correct for no TE premium, though the TE formula still needs route/target validation before final trust.

Recommendation: this dry run supports using the Niners roster page as an audit surface, not as final authority. It adds useful evidence that Kaleb/Luther/Jayden should not be blindly boosted by rookie/draft capital alone.

### Elite WRs

Elite WRs remain stable at the top. Jefferson, Lamb, Chase, Nabers, Amon-Ra, Puka, and BTJ stay in the same broad tier.

Jaxon Smith-Njigba remains suspicious. His projection data is very strong, and he moves from 62.32 to 64.36, but he still trails Tee Higgins at 67.81 in preview value. That may be possible, but the receipt burden is high. If JSN's real 2025 production/target-earning edge is not appearing clearly, this is likely a stale production, role/usage, or formula-weight issue.

Recommendation: make JSN vs Tee a priority receipt audit after the truth-set import. The truth-set projection strengthens the case that JSN should at least be challenged against Tee.

### Elite RBs

Bijan jumps to the top of the truth-set preview group, moving from truth-set rank 8 to rank 2. That is a good sign. Gibbs also improves. Achane and Chase Brown move up modestly. Kaleb Johnson moves down.

This is healthier than earlier versions of the model. It no longer says fringe/uncertain RB profiles should jump elite players based on vague role or bridge assumptions.

Concern: Kyren remains high relative to some younger or more insulated assets. The dry run only moves him +1.50, so his rank is not caused by the new truth-set data. If he still feels too high, the cause is in the base formula or active public-data inputs, not this new import.

Recommendation: audit RB formula receipts for Kyren, CMC, Achane, Chase Brown, Bijan, Gibbs, and Jeanty. Focus on whether role/projection is overpowering dynasty hold and age/injury.

### Young Bridge WRs

Young bridge prior is behaving conservatively. It does not blindly boost young players. BTJ remains high because his current model value was already high. Luther, Jayden, Kaleb, and Oronde move down, not up.

This is a strong sign that the bridge layer is not the main source of wonky rankings right now.

Recommendation: keep the bridge prior preview-only until the missing young rows and source-quality flags are reviewed, but do not rebuild it from scratch.

### Young Bridge RBs

Bijan, Gibbs, Achane, and Chase Brown improve from the projection recompute. Kaleb drops. Jeanty is basically unchanged because the missing young-prior report row prevents a meaningful bridge adjustment.

Recommendation: Jeanty needs a real young/prospect prior row before the model can compare him fairly to established RBs.

### QB/TE Controls

QB suppression is working directionally. Josh Allen and Lamar rise from better projections but remain below the elite RB/WR assets. Daniel Jones remains low. That is correct for 10-team 1QB.

TE suppression is also directionally working. Brock Bowers rises but remains below elite WR/RB. Hockenson, Ferguson, Strange, and Gadsden remain low. That is directionally correct for no TE premium.

Recommendation: no immediate QB/TE formula rewrite from this dry run. TE route/target data remains the bigger missing input.

## Suspicious Items

### Source Data Problems

Some projection rows disagree with active team context:

| player | projection team | active team | concern |
|---|---|---|---|
| David Montgomery | HOU | DET | possible bad projection source row or future-team assumption |
| Romeo Doubs | NE | GB | possible bad projection source row or future-team assumption |
| Wan'Dale Robinson | TEN | NYG | possible bad projection source row or future-team assumption |

LAR vs LA for Puka/Kyren is just abbreviation style, not a model concern.

Recommended patch: add a team-mismatch flag to truth-set preview intake. Do not use team-mismatched rows as model-safe until reviewed.

### Missing Source Data

Brandon Aiyuk and Keenan Allen have no projection rows. They stay unchanged in the dry run. Keenan remaining high despite missing projection is a model-audit concern. That does not prove he is wrong, but it means his value is coming from active base inputs rather than new truth-set evidence.

Recommended patch: add "missing projection but high active value" to the outlier worklist.

### Rejected Production Data

Production remains rejected across the board. That means this dry run still lacks the biggest missing truth input: clean historical production. Until the production report is re-exported in a strict schema, projection recompute is doing more work than it should.

Recommended patch: request/rebuild production data as a strict CSV with stable columns, then rerun the dry run.

### Formula Balance Concerns

The dry run suggests the biggest remaining model trust problems are not caused by the new truth-set fields. They are likely in:

- stale production sources
- missing route/participation evidence
- how projection value is weighted against actual recent production
- RB age/injury/dynasty hold balance
- WR target-earning and route-role visibility
- high-value players with missing projection/context rows

## Recommended Patches

1. Add a Truth Set source-quality gate for projection team mismatches.
2. Add outlier flags for high active model value with missing projection evidence.
3. Re-export the production data in a strict schema; do not use the current production CSV.
4. Run a focused JSN vs Tee receipt audit using active production, projection recompute, target earning, and route role.
5. Run a focused RB receipt audit for Kyren, CMC, Achane, Chase Brown, Bijan, Gibbs, and Jeanty.
6. Add missing young/prospect prior rows for Jahmyr Gibbs, Ashton Jeanty, and Brock Bowers or keep those rows explicitly review-only.
7. Keep active rankings unchanged until the clean production data and route/participation gaps are resolved.

## Bottom Line

The Truth Set Lab improves auditability and catches some source issues, but it does not fully fix model trust. The encouraging part is that safe projection and bridge fields do not create absurd swings. The discouraging part is that the model's remaining weirdness is probably in older base inputs, role/usage gaps, formula balance, and rejected/missing production evidence.

Do not promote these dry-run values. Use them to drive the next patch list.
