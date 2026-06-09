# QB/TE Context Balance v1 Deep Audit - 2026-06-09

This is a proposal-only audit. It does not implement or promote `qb_te_context_balance_v1`.

## 1. Executive Summary
- Variant audited: `qb_te_context_balance_v1`.
- Recommendation status: `revise_combined_candidate_before_patch`.
- The combined candidate improves the obvious baseline shape problem: QB/TE no longer dominate the top 10/top 25 in a 10-team 1QB, no-TE-premium league.
- The candidate should be revised before a production patch because the TE compression may be too blunt: all TEs leave the top 25, Trey McBride lands at #42, and Brock Bowers lands at #67.
- RB/WR scores do not change; rank gains are collateral displacement from QB/TE compression.
- No active output changed, and Decision Board remains blocked.

## 2. What The Candidate Changes In Shadow
- Compresses QB scores toward the private QB median to test 1QB spread discipline.
- Applies a no-premium TE ceiling shaped by private RB/WR distribution context, then compresses TE spread toward the private TE median.
- Re-ranks the full shadow board under the experiment folder only.

## 3. What It Does Not Change
- Does not change active Rankings or baseline CSVs.
- Does not change production formula files.
- Does not change RB/WR scores.
- Does not use market rank, league rank, public ranks, ADP, startup, projections, consensus, RotoWire rankings/projections, trade calculators, or legacy active-pack scores as score inputs.
- Does not create roster actions or final recommendations.

## 4. Why Baseline Was Suspicious
- Baseline top 25 had 4 QBs and 3 TEs, including Trey McBride #1 overall, Josh Allen #5, Drake Maye #8, and Trevor Lawrence #9.
- Baseline diagnosis ties QB pressure to VORP normalization plus rushing/passing component strength.
- Baseline diagnosis ties TE pressure to strong TE VORP, route/target, first-down, efficiency, and red-zone components before full no-premium cross-position context.

## 5. Why Combined Variant May Be Better
- Shadow top 25 by position: {'WR': 13, 'RB': 10, 'QB': 2}.
- Josh Allen and Drake Maye remain relevant at #18 and #23, but QBs no longer occupy the top 10.
- TEs no longer outrank elite RB/WR assets by default in a no-premium format.
- RB/WR scores are unchanged, which keeps the experiment narrow.

## 6. Possible Overcorrection Concerns
- Moving every TE out of the top 25 may be too aggressive even in no-TE-premium.
- Trey McBride #42 may be plausible for review, but it is a large move from #1 and needs component-level scrutiny.
- Brock Bowers #67 may be too low relative to the model's own component evidence and dynasty profile.
- The candidate is a broad compression transform, not yet a nuanced elite-exception rule.

## 7. QB-Specific Review
| Player | Base Rank | Shadow Rank | Base Score | Shadow Score | Rank Delta | Score Delta | Trust | Warning Summary | Audit Read | Human Review Question |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| Josh Allen | 5 | 18 | 80.3133 | 50.9815 | 13 | -29.3318 | Capped Score | qb_rushing_age_caution_active|missing_or_review_route_target_snap_evidence | Fixes top-end 1QB pressure, but must not bury elite QB evidence. | Does this QB placement fit 10-team 1QB football judgment? |
| Drake Maye | 8 | 23 | 77.0377 | 49.1799 | 15 | -27.8578 | Scored + Warnings | partial_first_down_confidence_cap | Fixes top-end 1QB pressure, but must not bury elite QB evidence. | Does this QB placement fit 10-team 1QB football judgment? |
| Trevor Lawrence | 9 | 28 | 73.5624 | 47.2685 | 19 | -26.2939 | Scored |  | Fixes top-end 1QB pressure, but must not bury elite QB evidence. | Does this QB placement fit 10-team 1QB football judgment? | Should this row stay flagged before rankings trust? |
| Matthew Stafford | 19 | 45 | 55.0484 | 37.0858 | 26 | -17.9626 | Scored + Warnings | first_down_missing_confidence_cap | Fixes top-end 1QB pressure, but must not bury elite QB evidence. | Should this row stay flagged before rankings trust? | Does this QB placement fit 10-team 1QB football judgment? |
| Jalen Hurts | 42 | 69 | 41.1499 | 29.4416 | 27 | -11.7083 | Capped Score | one_qb_small_vorp_gap_cap|missing_or_review_route_target_snap_evidence | Fixes top-end 1QB pressure, but must not bury elite QB evidence. | Does this QB placement fit 10-team 1QB football judgment? |
| Patrick Mahomes | 69 | 90 | 31.7813 | 24.2889 | 21 | -7.4924 | Scored + Warnings | 3 warnings: partial_first_down_confidence_cap, one_qb_small_vorp_gap_cap | Fixes top-end 1QB pressure, but must not bury elite QB evidence. | Does this QB placement fit 10-team 1QB football judgment? |
| Lamar Jackson | 150 | 150 | 15.2515 | 15.1975 | 0 | -0.054 | Scored + Warnings | one_qb_replacement_level_qb_cap|qb_rushing_age_caution_active | No material movement. | Should this row stay flagged before rankings trust? | Does this QB placement fit 10-team 1QB football judgment? | Is this low NWR placement source-driven or formula-driven? |
| Joe Burrow | 219 | 200 | 7.4662 | 10.9156 | -19 | 3.4494 | Capped Score | one_qb_replacement_level_qb_cap|missing_or_review_route_target_snap_evidence | Rises by compression side effect; check for low-QB anomaly. | Is this low NWR placement source-driven or formula-driven? | Does this QB placement fit 10-team 1QB football judgment? |
| Jayden Daniels | 208 | 191 | 8.9902 | 11.7538 | -17 | 2.7636 | Scored + Warnings | one_qb_replacement_level_qb_cap | Rises by compression side effect; check for low-QB anomaly. | Is this low NWR placement source-driven or formula-driven? | Does this QB placement fit 10-team 1QB football judgment? |
| Kyler Murray | 225 | 208 | 6.1955 | 10.2167 | -17 | 4.0212 | Capped Score | one_qb_replacement_level_qb_cap|rotowire_current_team_status_warning | Rises by compression side effect; check for low-QB anomaly. | Does this QB placement fit 10-team 1QB football judgment? |
| Daniel Jones | 189 | 180 | 11.1635 | 12.9491 | -9 | 1.7856 | Capped Score | one_qb_replacement_level_qb_cap|rotowire_current_team_status_warning | Rises by compression side effect; check for low-QB anomaly. | Should this row stay flagged before rankings trust? | Does this QB placement fit 10-team 1QB football judgment? |

## 8. TE-Specific Review
| Player | Base Rank | Shadow Rank | Base Score | Shadow Score | Rank Delta | Score Delta | Trust | Warning Summary | Audit Read | Human Review Question |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| Trey McBride | 1 | 42 | 87.4776 | 37.3106 | 41 | -50.167 | Capped Score | 4 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | Large no-premium compression; overcorrection risk. | Does this TE placement fit no-premium scoring? |
| Kyle Pitts | 18 | 43 | 55.2691 | 37.3106 | 25 | -17.9585 | Capped Score | 4 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | Moderate no-premium compression; human review needed. | Does this TE placement fit no-premium scoring? | Should this row stay flagged before rankings trust? |
| Travis Kelce | 25 | 44 | 50.9057 | 37.3106 | 19 | -13.5951 | Capped Score | 5 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | Moderate no-premium compression; human review needed. | Should this row stay flagged before rankings trust? | Does this TE placement fit no-premium scoring? |
| Brock Bowers | 59 | 67 | 34.9344 | 29.7961 | 8 | -5.1383 | Capped Score | 6 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | Moderate no-premium compression; human review needed. | Does this TE placement fit no-premium scoring? |
| Sam LaPorta | 149 | 151 | 15.4274 | 15.1659 | 2 | -0.2615 | Capped Score | 5 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | Moderate no-premium compression; human review needed. | Does this TE placement fit no-premium scoring? |
| Mark Andrews | 162 | 161 | 14.0569 | 14.138 | -1 | 0.0811 | Capped Score | 6 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | No material TE compression. | Does this TE placement fit no-premium scoring? |
| T.J. Hockenson | 164 | 164 | 13.7788 | 13.9294 | 0 | 0.1506 | Capped Score | 6 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | No material TE compression. | Should this row stay flagged before rankings trust? | Does this TE placement fit no-premium scoring? |
| Jake Ferguson | 77 | 89 | 27.6842 | 24.3585 | 12 | -3.3257 | Capped Score | 6 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | Moderate no-premium compression; human review needed. | Does this TE placement fit no-premium scoring? |
| Brenton Strange | 170 | 167 | 13.4585 | 13.6892 | -3 | 0.2307 | Capped Score | 5 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | No material TE compression. | Should this row stay flagged before rankings trust? | Does this TE placement fit no-premium scoring? |
| George Kittle | 88 | 103 | 25.4179 | 22.6588 | 15 | -2.7591 | Capped Score | 6 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | Moderate no-premium compression; human review needed. | Does this TE placement fit no-premium scoring? |
| Tucker Kraft | 156 | 157 | 14.7059 | 14.6248 | 1 | -0.0811 | Capped Score | 6 warnings: licensed_route_metrics_not_available, not_used_in_stats_first_value | Moderate no-premium compression; human review needed. | Is this low NWR placement source-driven or formula-driven? | Does this TE placement fit no-premium scoring? |

## 9. RB/WR Collateral Review
| Player | Pos | Base Rank | Shadow Rank | Rank Delta | Score Delta | Collateral Read |
|---|---|---:|---:|---:|---:|---|
| Puka Nacua | WR | 2 | 1 | -1 | 0.0 | Score unchanged; rank movement is collateral. |
| Christian McCaffrey | RB | 3 | 2 | -1 | 0.0 | Score unchanged; rank movement is collateral. |
| Jaxon Smith-Njigba | WR | 4 | 3 | -1 | 0.0 | Score unchanged; rank movement is collateral. |
| Jonathan Taylor | RB | 6 | 4 | -2 | 0.0 | Score unchanged; rank movement is collateral. |
| Bijan Robinson | RB | 7 | 5 | -2 | 0.0 | Score unchanged; rank movement is collateral. |
| Jahmyr Gibbs | RB | 10 | 6 | -4 | 0.0 | Score unchanged; rank movement is collateral. |
| Ja'Marr Chase | WR | 11 | 7 | -4 | 0.0 | Score unchanged; rank movement is collateral. |
| Amon-Ra St. Brown | WR | 12 | 8 | -4 | 0.0 | Score unchanged; rank movement is collateral. |
| De'Von Achane | RB | 14 | 10 | -4 | 0.0 | Score unchanged; rank movement is collateral. |
| Chase Brown | RB | 28 | 22 | -6 | 0.0 | Score unchanged; rank movement is collateral. |
| Brian Thomas | WR | 90 | 86 | -4 | 0.0 | Score unchanged; rank movement is collateral. |
| Brandon Aiyuk | WR | 93 | 91 | -2 | 0.0 | Score unchanged; rank movement is collateral. |
| CeeDee Lamb | WR | 29 | 24 | -5 | 0.0 | Score unchanged; rank movement is collateral. |
| Justin Jefferson | WR | 32 | 27 | -5 | 0.0 | Score unchanged; rank movement is collateral. |
| Malik Nabers | WR | 72 | 65 | -7 | 0.0 | Score unchanged; rank movement is collateral. |
| Garrett Wilson | WR | 74 | 71 | -3 | 0.0 | Score unchanged; rank movement is collateral. |

## 10. My Team Impact
| Player | Pos | Base Rank | Shadow Rank | Rank Delta | Score Delta | Read |
|---|---|---:|---:|---:|---:|---|
| De'Von Achane | RB | 14 | 10 | -4 | 0.0 | direct score unchanged |
| Chase Brown | RB | 28 | 22 | -6 | 0.0 | direct score unchanged |
| Wan'Dale Robinson | WR | 52 | 46 | -6 | 0.0 | direct score unchanged |
| Jakobi Meyers | WR | 75 | 73 | -2 | 0.0 | direct score unchanged |
| Quentin Johnston | WR | 78 | 75 | -3 | 0.0 | direct score unchanged |
| Jerry Jeudy | WR | 80 | 78 | -2 | 0.0 | direct score unchanged |
| Brian Thomas | WR | 90 | 86 | -4 | 0.0 | direct score unchanged |
| Jake Ferguson | TE | 77 | 89 | 12 | -3.3257 | direct QB/TE score changed |
| Brandon Aiyuk | WR | 93 | 91 | -2 | 0.0 | direct score unchanged |
| Luther Burden | WR | 94 | 92 | -2 | 0.0 | direct score unchanged |
| Ricky Pearsall | WR | 95 | 93 | -2 | 0.0 | direct score unchanged |
| Romeo Doubs | WR | 98 | 96 | -2 | 0.0 | direct score unchanged |
| David Montgomery | RB | 103 | 101 | -2 | 0.0 | direct score unchanged |
| Xavier Worthy | WR | 106 | 105 | -1 | 0.0 | direct score unchanged |
| Jalen Coker | WR | 127 | 126 | -1 | 0.0 | direct score unchanged |
| Jayden Higgins | WR | 131 | 130 | -1 | 0.0 | direct score unchanged |
| Oronde Gadsden | TE | 133 | 138 | 5 | -0.7396 | direct QB/TE score changed |
| Lamar Jackson | QB | 150 | 150 | 0 | -0.054 | direct QB/TE score changed |
| Devin Singletary | RB | 158 | 159 | 1 | 0.0 | direct score unchanged |
| T.J. Hockenson | TE | 164 | 164 | 0 | 0.1506 | direct QB/TE score changed |
| Brenton Strange | TE | 170 | 167 | -3 | 0.2307 | direct QB/TE score changed |
| Luke McCaffrey | WR | 175 | 179 | 4 | 0.0 | direct score unchanged |
| Daniel Jones | QB | 189 | 180 | -9 | 1.7856 | direct QB/TE score changed |
| Kaleb Johnson | RB | 232 | 232 | 0 | 0.0 | direct score unchanged |

## 11. Veteran Impact
- Veteran QB/TE rows move mostly because of positional compression, not because age/status confidence was specifically changed.
- Matthew Stafford moves #19 -> #45; Travis Kelce moves #25 -> #44; George Kittle moves #88 -> #103.
- This is a concern: a later patch should separate format compression from veteran age/status confidence rather than letting one broad transform do both jobs.

## 12. Young-Player Impact
- Drake Maye remains high enough for review (#23) after compression.
- Brock Bowers (#67), Sam LaPorta (#151), and young TE rows may be compressed too hard if the future production model still believes elite TE exceptions should exist.
- Young RB/WR anchor scores do not change; they mostly rise by collateral rank movement.

## 13. Source/Trust/Warning Impact
- Source issue rows in the suspicious file: 8.
- The candidate does not clean source warnings or trust labels.
- No non-kicker source quarantine is introduced by the shadow readback.

## 14. Sentinels And Contamination
- Sentinels safe: True.
- Contamination safe: True.
- Keenan Allen and Darius Slayton legacy active-pack scores remain comparison-only.

## 15. Invariants
- Active baseline hash before: `cf32135966d397965e8a60cef2a8e4e243fe9d18cab5d8b439157f45af010dea`.
- Active baseline hash after: `cf32135966d397965e8a60cef2a8e4e243fe9d18cab5d8b439157f45af010dea`.
- Active output changed: False.
- RB/WR score changed: False.
- K rows remain unscored/default-hidden in the baseline.
- Outcome percentages remain blank/in development.
- Decision Board remains blocked.

## 16. Recommendation Status
`revise_combined_candidate_before_patch`

The combined candidate should not be rejected outright; it is the best current lane. But it should be revised before a production patch so TE elite-exception behavior is less blunt and QB compression is tied to production discipline with clearer receipts.

## Overcorrection Audit
1. Moving all TEs out of the top 25 is likely a no-premium correction, but it may be too strong.
2. Trey McBride at #42 is plausible enough for human review, not clean enough for immediate promotion.
3. Brock Bowers at #67 looks like the largest TE overcorrection risk relative to the model's own evidence.
4. Josh Allen at #18 and Drake Maye at #23 keep QB relevant without top-10 domination.
5. The candidate does not bury every elite QB, but it leaves some already-low QB rows low and still needs review.
6. Older QBs/TEs are compressed, but not specifically through age/status logic.
7. Top RB/WR assets dominate the top 25, consistent with this league format.
8. The result looks more like a dynasty board than the baseline, but TE future upside may be underexpressed.
9. The result better respects 1QB/no-TE-premium/2-flex context than the baseline, pending TE revision.

## Readback Sources Consulted
- Manifest excerpt loaded: True.
- Position distribution rows: 5.
- Suspicious rows reviewed: 47.
