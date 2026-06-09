# Named Player Audit Roster

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: define a balanced 80-subject audit roster for external audit and human
judgment before formula tuning. This is a review roster only. It does not judge
whether a score is correct and does not change formulas, active rankings, source
data, generated outputs, or UI behavior.

This roster also does not change active rankings, My Team, War Board, readiness
gates, active data packs, or generated model outputs.

Use with:

- `docs/model_v4/REFINEMENT_EVIDENCE_MAP_20260605.md`
- `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
- `local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv`
- `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv`
- `local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv`

## Category Coverage

- Elite young/current WR and RB checks.
- Aging productive veteran checks.
- Injury/status/stale-team warning checks.
- Low-evidence and manual-review checks.
- 1QB QB discipline checks.
- No-premium TE discipline checks.
- Rookie board and watchlist checks.
- Owned pick ladder checks.
- Legacy-leak sentinel checks.

## Audit Roster

| ID | Subject | Type | Pos | Primary Source Surface | Audit Category | Why Included |
|---|---|---|---|---|---|---|
| A01 | Puka Nacua | current_player | WR | Player Board / current value | elite_young_wr | Top-tier WR check; verify high score has clear source and warnings. |
| A02 | Jaxon Smith-Njigba | current_player | WR | Player Board / current value | elite_young_wr | Top-tier young WR and known high-value sanity anchor. |
| A03 | Ja'Marr Chase | current_player | WR | Player Board / current value | elite_wr_anchor | Elite WR should be explainable relative to Puka/JSN. |
| A04 | Amon-Ra St. Brown | current_player | WR | Player Board / current value | elite_wr_anchor | High-end WR with warning coverage to inspect. |
| A05 | CeeDee Lamb | current_player | WR | Player Board / current value | elite_wr_anchor | Elite-name check where score/rank may need human review. |
| A06 | Justin Jefferson | current_player | WR | Player Board / current value | elite_wr_anchor | Elite-name check; useful for suspicious-ranking review. |
| A07 | Nico Collins | current_player | WR | Player Board / current value | high_value_wr | Productive prime WR bridge between elite and mid tiers. |
| A08 | Chris Olave | current_player | WR | Player Board / current value | young_wr_warning | Young WR with warning context; inspect confidence. |
| A09 | Drake London | current_player | WR | Player Board / current value | young_wr_warning | Young WR name-value sanity check. |
| A10 | George Pickens | current_player | WR | Player Board / current value | warning_sentinel | Team/status warning candidate; verify row is not overconfident. |
| A11 | Jaylen Waddle | current_player | WR | Player Board / current value | young_wr_warning | Team/status warning candidate and known dynasty-name check. |
| A12 | Tee Higgins | current_player | WR | Player Board / current value | young_wr_warning | Prime WR value band and warning visibility check. |
| A13 | Brian Thomas Jr. | current_player | WR | Player Board / current value | young_wr_warning | Young WR that may expose conservative evidence handling. |
| A14 | Marvin Harrison Jr. | current_player | WR | Player Board / current value | young_wr_warning | Big-name young WR and missing/source warning check. |
| A15 | Malik Nabers | current_player | WR | Player Board / current value | young_wr_warning | High-profile young WR with possible source-missing tension. |
| A16 | Xavier Worthy | current_player | WR | Player Board / current value | young_wr_warning | Speed/upside profile; inspect evidence and warnings. |
| A17 | Ladd McConkey | current_player | WR | Player Board / current value | young_wr_warning | Young WR warning and confidence check. |
| A18 | Ricky Pearsall | current_player | WR | Player Board / current value | roster_relevance | Niners-relevant young WR; useful for human judgment. |
| A19 | Brandon Aiyuk | current_player | WR | Player Board / current value | roster_relevance | Niners-relevant value and injury/status review. |
| A20 | Quentin Johnston | current_player | WR | Player Board / current value | volatile_profile | Volatile young WR profile; inspect score humility. |
| A21 | Christian McCaffrey | current_player | RB | Player Board / current value | elite_aging_rb | Top score with RB age-cliff warning; major money-decision sentinel. |
| A22 | Jonathan Taylor | current_player | RB | Player Board / current value | elite_prime_rb | Prime RB anchor for RB/WR balance. |
| A23 | Bijan Robinson | current_player | RB | Player Board / current value | elite_young_rb | Elite young RB anchor. |
| A24 | Jahmyr Gibbs | current_player | RB | Player Board / current value | elite_young_rb | Elite young RB anchor and format sanity check. |
| A25 | Derrick Henry | current_player | RB | Player Board / current value | aging_rb | Aging RB with high production; age curve candidate, not formula change. |
| A26 | De'Von Achane | current_player | RB | Player Board / current value | volatile_rb | Explosive RB with fragility/evidence tension. |
| A27 | James Cook | current_player | RB | Player Board / current value | rb_balance | RB tier balance check. |
| A28 | Kyren Williams | current_player | RB | Player Board / current value | rb_warning | Productive RB with warning coverage to inspect. |
| A29 | Saquon Barkley | current_player | RB | Player Board / current value | aging_rb | Productive veteran RB; age and confidence check. |
| A30 | Josh Jacobs | current_player | RB | Player Board / current value | aging_rb | Veteran RB value and partial-evidence warning check. |
| A31 | Breece Hall | current_player | RB | Player Board / current value | young_rb_warning | Young RB anchor that may reveal RB/WR balance issues. |
| A32 | Kenneth Walker III | current_player | RB | Player Board / current value | young_rb_warning | Young RB with team/status warning. |
| A33 | Chase Brown | current_player | RB | Player Board / current value | emerging_rb | Emerging RB confidence and source check. |
| A34 | David Montgomery | current_player | RB | Player Board / current value | veteran_depth_rb | Veteran depth score and warning check. |
| A35 | Ashton Jeanty | current_player | RB | Player Board / current value | rookie_current_bridge | Rookie/current bridge row with historical warning. |
| A36 | Kaleb Johnson | current_player | RB | Player Board / current value | roster_pressure | Niners/Decision Board relevance and low-score review. |
| A37 | Davante Adams | current_player | WR | Player Board / current value | aging_wr | Aging productive WR; age/window sanity check. |
| A38 | Stefon Diggs | current_player | WR | Player Board / current value | aging_wr | Aging WR with team/status warning. |
| A39 | Mike Evans | current_player | WR | Player Board / current value | aging_wr | Productive veteran WR; possible over/under-confidence candidate. |
| A40 | Cooper Kupp | current_player | WR | Player Board / current value | aging_wr | Aging/injury-profile WR sanity check. |
| A41 | Amari Cooper | current_player | WR | Player Board / current value | aging_wr | Veteran WR low-band check. |
| A42 | Tyreek Hill | current_player | WR | Player Board / current value | aging_elite_wr | Elite-name aging WR; suspicious-ranking candidate. |
| A43 | Keenan Allen | current_player | WR | Player Board / current value | legacy_leak_sentinel | Known legacy active-pack sentinel; legacy score must remain comparison-only. |
| A44 | Wan'Dale Robinson | current_player | WR | Player Board / current value | low_band_wr | Lower-band WR with team/status warning. |
| A45 | Romeo Doubs | current_player | WR | Player Board / current value | low_band_wr | Lower-band WR and team/status warning check. |
| A46 | Jerry Jeudy | current_player | WR | Player Board / current value | volatile_profile | Name-value volatility and first-down evidence check. |
| A47 | Garrett Wilson | current_player | WR | Player Board / current value | suspicious_ranking | Big-name WR in lower band; likely human-review candidate. |
| A48 | Tank Dell | current_player | WR | Player Board / current value | injury_status | Injury/status and warning visibility check. |
| A49 | Luther Burden | current_player | WR | Player Board / current value | low_evidence | Missing stats-first component evidence row. |
| A50 | Jayden Higgins | current_player | WR | Player Board / current value | low_evidence | Low-evidence young WR/manual review check. |
| A51 | Jalen Coker | current_player | WR | Player Board / current value | low_evidence | Low-evidence current-player row. |
| A52 | Luke McCaffrey | current_player | WR | Player Board / current value | low_evidence | Low-band row with shifted/header warning style. |
| A53 | Hollywood Brown | current_player | WR | Player Board / current value | injury_status | Missing components and injury/status context check. |
| A54 | Devin Singletary | current_player | RB | Player Board / current value | replacement_rb | Replacement/depth RB boundary check. |
| A55 | Darrell Henderson | current_player | RB | Player Board / current value | replacement_rb | Low-score veteran RB boundary check. |
| A56 | Josh Allen | current_player | QB | Player Board / current value | one_qb_qb | 1QB elite QB discipline anchor. |
| A57 | Jalen Hurts | current_player | QB | Player Board / current value | one_qb_qb | Rushing QB value discipline check. |
| A58 | Patrick Mahomes | current_player | QB | Player Board / current value | one_qb_qb | Pocket/elite-name QB discipline check. |
| A59 | Lamar Jackson | current_player | QB | Player Board / current value | one_qb_qb | Rushing QB with 1QB cap warning. |
| A60 | Joe Burrow | current_player | QB | Player Board / current value | one_qb_qb | Pocket QB cap and low-score sanity check. |
| A61 | Jayden Daniels | current_player | QB | Player Board / current value | one_qb_qb | Young QB replacement-level cap check. |
| A62 | Trey McBride | current_player | TE | Player Board / current value | no_premium_te | TE top score in no-premium format; must be audited closely. |
| A63 | Travis Kelce | current_player | TE | Player Board / current value | aging_te | Aging elite TE/no-premium context. |
| A64 | Brock Bowers | current_player | TE | Player Board / current value | no_premium_te | Young elite TE/no-premium discipline check. |
| A65 | Jake Ferguson | current_player | TE | Player Board / current value | no_premium_te | Mid-band TE no-premium discipline and confidence check. |
| A66 | George Kittle | current_player | TE | Player Board / current value | aging_te | Niners-relevant TE and no-premium context. |
| A67 | Sam LaPorta | current_player | TE | Player Board / current value | no_premium_te | Young TE no-premium cap check. |
| A68 | Mark Andrews | current_player | TE | Player Board / current value | aging_te | Veteran TE band and warning check. |
| A69 | Jeremiyah Love | rookie | RB | Rookie Draft Board | rookie_top_cluster | Top rookie board anchor. |
| A70 | Makai Lemon | rookie | WR | Rookie Draft Board | rookie_top_cluster | Top WR rookie cluster anchor. |
| A71 | Skyler Bell | rookie | WR | Rookie Draft Board | rookie_top_cluster | Top rookie cluster and evidence check. |
| A72 | Jordyn Tyson | rookie | WR | Rookie Draft Board | rookie_top_cluster | Top rookie cluster and pick-window check. |
| A73 | Carnell Tate | rookie | WR | Rookie Draft Board / Player Board bridge | rookie_bridge | Appears in rookie/current bridge context. |
| A74 | Antonio Williams | rookie | WR | Rookie Draft Board | rookie_pick_window | Pick-window candidate across early picks. |
| A75 | Daniel Sobkowicz | rookie | WR | Rookie Draft Board | rookie_low_evidence | Prior focus-row expectation fell out; audit why/how. |
| A76 | 2026 1.03 | pick | PICK | Pick Inventory / Draft Room | pick_ladder | Highest owned pick; audit baseline and nearby assets. |
| A77 | 2026 1.04 | pick | PICK | Pick Inventory / Draft Room | pick_ladder | Adjacent early pick; audit separation from 1.03. |
| A78 | 2026 2.04 | pick | PICK | Pick Inventory / Draft Room | pick_ladder | Mid pick; audit value ladder and candidates. |
| A79 | 2026 2.08 | pick | PICK | Pick Inventory / Draft Room | pick_ladder | Later second; audit neighborhood and candidate windows. |
| A80 | 2026 5.04 | pick | PICK | Pick Inventory / Draft Room | manual_only_pick | Manual-only/missing baseline sentinel. |

## Use Instructions

For each subject, later tasks should record:

- source path and score column,
- displayed model value or pick value,
- warning flags and trust/confidence state,
- whether the row feels too high, too low, or reasonable to the human reviewer,
- whether the concern is likely data/source, formula candidate, UI/explanation,
  or no concern,
- whether any money-action risk exists.

## Non-Goals

- Do not tune formulas from this roster.
- Do not use this roster as rankings.
- Do not add market, ADP, projection, consensus, startup, or trade-calculator
  logic to private value.
- Do not convert review labels into final recommendations.
