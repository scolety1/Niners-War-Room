# NWR Model/Data Candidate Sanity Review - 2026-06-22

Verdict: YELLOW

This lane performed a candidate-only model/data sanity review for tomorrow's draft. It did not integrate anything into the app and did not mutate frozen, approved, latest, pinned, model, value, ranking, or Streamlit workflow files.

## Scope And Guardrails

Worktree:

`C:\NWR\Niners-War-Room-model-data-candidate-sanity`

Branch:

`codex/model-data-candidate-sanity-20260622`

Starting commit:

`cc49fa6a30197b4b39e260031fc59c16ed51b36d`

This report and the companion CSVs are review-only. They are not `latest_candidate`, not `latest_approved`, not a ranking change, not a frozen-board mutation, not private value, not Mock Draft logic, and not final draft advice.

## Inputs Reviewed

| Source | Path | Notes |
|---|---|---|
| Frozen Final Draft Board V1 | `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_FROZEN.csv` | 66-row draft-day source of truth |
| Manual review flags | `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_MANUAL_REVIEW_FLAGS.csv` | 36 manual-review rows |
| Top tiers | `C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622\FINAL_DRAFT_BOARD_V1_TOP_TIERS.csv` | Top 30 board rows |
| Full Dynasty source | `C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv` | 240-row current-player dynasty source |
| Outcome props | `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\outcome_columns\outcome_player_context.csv` | Partial outcome context |
| Trading props | `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\trading_lab\trade_helper_context.csv` | Display-only trade helper context |
| Decision props | `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\decision_board\decision_flags_context.csv` | Display-only decision flags |
| Mock availability props | `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\mock_draft\availability_context.csv` | Display-only availability context |
| Rookie overlay | `C:\NWR_SHARED_DATA\draft_day_app_props\20260622\rookie_hq\rookie_overlay_context.csv` | 54 rookie/prospect rows |

## Sanity Summary

| Check | Result |
|---|---:|
| Frozen board rows | 66 |
| Frozen rank contiguous 1-66 | PASS |
| Duplicate frozen player/position rows | 0 |
| Outcome-supported rows | 12 |
| Outcome gap rows | 54 |
| Manual-review rows | 36 |
| Top-tier rows reviewed | 30 |
| Team label rows with `needs_data` or `UNKNOWN` | 10 |
| Depth/role rows with `needs_data` caveat | 43 |
| Full Dynasty source rows | 240 |
| Frozen board overlap with Full Dynasty by name/position | 12 |

## Biggest Model/Data Risks For Tomorrow

1. Outcome support remains only 12 of 66 board rows. The remaining 54 should say exactly `Not enough information`.
2. The frozen board has no `player_id`; most app props also rely on rank/name/position joins. This is acceptable for tomorrow but brittle.
3. Ten rows have team labels of `needs_data` or `UNKNOWN`.
4. Forty-three rows have depth/role `needs_data` caveats, mostly target-earning or rush/goal-line role questions.
5. Thirty-six rows are manual-review flagged; 15 are priority P1 draft-room reviews.
6. The full Dynasty source only overlaps 12 of 66 frozen-board players, so it should not be treated as a full replacement for the frozen board.
7. Keenan Allen and Darren Waller remain team/status review cases. Internal sources say no current team; web checks were mixed or uncertain.
8. Some high-board rookie ranks are supported by model posture but still require human confirmation of NFL role/depth/draft context.
9. Market/ranking context in the dynasty source must stay display-only and must not become a rank driver.
10. The app should make uncertainty louder, not quieter, especially for top-board players with `needs_data` role context.

## Highest-Confidence Candidate Fixes

These are not applied to live artifacts. They are candidate-only notes for Master/human review.

| Player | Current Label | Candidate Action | Confidence | Evidence |
|---|---|---|---|---|
| Jamarion Miller | `needs_data` | Candidate team label repair to `NE` / Patriots | HIGH | NFL.com draft video and Tyler ISD release report Patriots selected Jam/Jamarion Miller at pick 245 |
| Jacob De Jesus | `needs_data` | Possible `KC` review only | MEDIUM | ESPN lists him as Kansas City Chiefs WR/Active; should be confirmed against an official Chiefs roster/source before live use |
| Keenan Allen | `UNKNOWN` | No repair | MEDIUM | Internal source says no current team; external references are mixed/UFA-oriented |
| Darren Waller | `UNKNOWN` | No repair | MEDIUM | Internal source says no current team; external references show 2025 Dolphins context and 2026 uncertainty |

Official/reputable checks used:

- Ohio Athletics: Sieh Bangura received a Tennessee Titans rookie minicamp invitation: https://ohiobobcats.com/news/2026/4/25/football-nfl-draft-sieh-bangura
- South Alabama Athletics: Devin Voisin received a Buccaneers rookie minicamp invitation: https://usajaguars.com/news/2026/4/27/football-bullock-and-voisin-earn-nfl-opportunities.aspx
- Arkansas Athletics: O'Mega Blake roster/production context: https://arkansasrazorbacks.com/roster/omega-blake/
- TCU Athletics: Braylon James roster context: https://gofrogs.com/sports/football/roster/braylon-james/18225
- NFL.com: Jam Miller Patriots draft selection video: https://www.nfl.com/videos/patriots-select-jam-miller-with-no-245-pick-in-2026-draft
- ESPN: Jacob De Jesus profile: https://www.espn.com/nfl/player/_/id/5155179/jacob-de-jesus
- NFL.com: Darren Waller profile: https://www.nfl.com/players/darren-waller/
- Spotrac: Keenan Allen contract/free-agent context: https://www.spotrac.com/nfl/player/_/id/12357/keenan-allen

## Candidate Files Created

Review-only candidate artifacts were created under:

`docs/hq/parallel_lanes/model_data_candidates_20260622/`

Files:

- `candidate_team_label_repairs.csv`
- `candidate_manual_review_priority.csv`
- `candidate_role_caveat_loudness.csv`
- `candidate_player_id_join_issues.csv`
- `candidate_sanity_metrics.csv`

### candidate_team_label_repairs.csv

Contains the 10 rows where the frozen board has `nfl_team` as `needs_data` or `UNKNOWN`. Only one high-confidence candidate repair was found:

- Jamarion Miller: candidate `NE` / Patriots, review-only.

The other nine remain no-repair or review-only because evidence was either a minicamp invitation, college roster/prospect context, or conflicting free-agent/team status.

### candidate_manual_review_priority.csv

Prioritizes 36 manual-review rows:

- P1 draft-room review: 15
- P2 if-on-clock range: 18
- P3 depth only: 3

This should help the app or human workflow make top-board uncertainty visible without changing rank.

### candidate_role_caveat_loudness.csv

Flags top-tier players whose depth/role/trap caveats should be louder in the app. This is especially important for top-30 rookies whose visible score may look confident while role evidence remains incomplete.

### candidate_player_id_join_issues.csv

Confirms the frozen board lacks stable `player_id`, and most frozen rows do not map to the full Dynasty source. This is a future bridge recommendation, not a tonight patch.

## Players To Trust More

These are not final advice; they are lower-friction review postures based on current package evidence:

- Rows with no manual-review flag, no `needs_data` team label, and no critical trap guard.
- Dropped/current veteran rows where internal identity match is explicit and the app labels team/status caveats.
- Top-board rows with clear draft capital/team label and no critical warning, while still respecting manual context.

## Players To Manually Double-Check

Highest-priority examples:

- Antonio Williams: critical trap guard.
- Jonah Coleman: feature-driven rank move needs role/draft/team confirmation.
- Skyler Bell, Brenen Thompson, Elijah Sarratt: target-earning path questions.
- Emmett Johnson, Kaytron Allen, Adam Randall, Nicholas Singleton: early-down/goal-line/first-down role path questions.
- Jamarion Miller: candidate team repair likely `NE`, but live artifacts should not change without approval.
- Keenan Allen and Darren Waller: team/status should remain `UNKNOWN` unless Master approves a source-backed update.

## Lower-Confidence Than Display Suggests

The biggest mismatch is not the final rank order itself; it is the visual confidence of high-scoring rows with unresolved role context. Any row with `needs_data` in `depth_chart_role_display_only` should display a visible caveat.

The app should not let a high `final_board_score_visible` suppress manual-review or role-depth uncertainty.

## Safe Changes Master Could Approve Later

1. Candidate team-label repair for Jamarion Miller to `NE` / Patriots after Master confirms the evidence.
2. Possible Jacob De Jesus team-label review for `KC`, only after official Chiefs confirmation.
3. Add a future player-ID bridge package across frozen board and app props.
4. Increase UI loudness for top-board `needs_data` role caveats.
5. Preserve `Not enough information` for all unsupported Outcome probabilities.
6. Add a Dynasty page note that the 240-row source is not a full 66-row frozen-board replacement.

## Human Decisions Needed

1. Should Master approve the Jamarion Miller `NE` candidate repair for a later artifact?
2. Should Jacob De Jesus be treated as possible `KC` or left as `needs_data` until official confirmation?
3. Should Keenan Allen and Darren Waller remain `UNKNOWN` on draft day, with clear free-agent/status caveats?
4. Should top-board role caveats be displayed as loud badges during the draft?
5. Should the player-ID bridge be deferred until after the draft?

## No-Touch Confirmation

This lane did not touch:

- Streamlit app files
- frozen Final Draft Board V1
- Full Dynasty source
- `latest_candidate`
- `latest_approved`
- pinned snapshot
- Mock Draft simulator logic
- model/value/ranking logic
- `C:\NWR_SHARED_DATA` tracked contents
- raw vendor CSVs
- raw prediction dumps

Final posture: YELLOW, candidate/report only. The frozen board remains structurally coherent, but app/human workflow should treat partial Outcome, team/status gaps, role-depth gaps, and missing player IDs as visible caveats rather than invisible implementation details.
