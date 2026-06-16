# Sprint 5BT: Formal 2017-2018 Completed Prior-Season Registration Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_SOURCE_REGISTRATION_ONLY_MODELING_NOT_APPROVED`

Sprint type: `DOCS_FIRST_REGISTRATION_AUDIT_NO_MODELING`

## 1. Scope

Sprint 5BT formally audits whether 2017 and 2018 `player_stats.csv` source seasons can be registered as completed prior-season factual sources for future 2018 and 2019 veteran Outcome historical expansion. This sprint does not build training rows, train models, generate outcome probabilities, create app-readable probability/band/status outputs, wire app display, alter rankings/sorting, create hidden sort keys, score rookies through veteran heads, or create promoted artifacts.

Read-only evidence:

- `docs/outcome_probability/BUILD_SPRINT_5BR_PRE_2020_HISTORICAL_UNIVERSE_FEASIBILITY_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5BS_PRE_2020_SOURCE_REGISTRATION_INVENTORY_2017_2018.md`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`

No local exports were created. No files under `data/` or `local_exports/` were edited.

## 2. Registration Decision

| Source season | Future target season | Registration verdict | Modeling approval |
| ---: | ---: | --- | --- |
| 2017 | 2018 | GREEN for completed prior-season source registration | not approved |
| 2018 | 2019 | GREEN for completed prior-season source registration | not approved |

Registration meaning:

- Source season `S` may support target preseason `S+1`.
- 2017 source stats may support future 2018 target-season preseason features.
- 2018 source stats may support future 2019 target-season preseason features.
- Same-season target stats remain labels only and must never become preseason features.

This is a source-registration decision only. A later sprint must explicitly approve any rebuild, training expansion, calibration rerun, or modeling package.

## 3. Source Coverage

Source path:

`local_exports/truth_set_lab/v3/downloads/player_stats.csv`

| Source season | Rows | Regular-season rows | Postseason rows | Weeks covered |
| ---: | ---: | ---: | ---: | --- |
| 2017 | 5,319 | 5,107 | 212 | 1-21 |
| 2018 | 5,281 | 5,070 | 211 | 1-21 |

Registration policy should use regular-season completed prior-season facts for preseason feature construction. Postseason rows exist and should remain excluded unless a later source-policy sprint explicitly approves postseason handling.

## 4. Allowed Prior-Season Source Fields

Allowed for completed prior-season feature construction, subject to aggregation and legality checks:

| Field family | Source fields |
| --- | --- |
| Games or active games | `week`, `season_type`, player-week presence |
| Passing volume/production | `completions`, `attempts`, `passing_yards`, `passing_tds`, `interceptions` |
| Rushing volume/production | `carries`, `rushing_yards`, `rushing_tds`, `rushing_first_downs` |
| Receiving volume/production | `receptions`, `receiving_yards`, `receiving_tds`, `receiving_first_downs` |
| Fumbles lost | `rushing_fumbles_lost`, `receiving_fumbles_lost`, `sack_fumbles_lost` |
| Identity/context for joins | `player_id`, `player_name`, `player_display_name`, `recent_team`, `position`, `position_group`, `season`, `week`, `season_type` |

Derived fields allowed only from source-safe components:

- prior completed-season NWR PPG
- prior completed-season NWR finish rank
- games played or active games
- age and experience only if identity/DOB joins pass in a later rebuild sprint

## 5. Forbidden And Quarantined Fields

The source contains fields that must remain excluded from prediction features and label shortcuts:

| Field family | Fields/status |
| --- | --- |
| Fantasy total shortcuts | `fantasy_points`, `fantasy_points_ppr` |
| EPA fields | `passing_epa`, `rushing_epa`, `receiving_epa` |
| Advanced/analytic context | `dakota`, `wopr`, `racr`, `pacr`, `target_share`, `air_yards_share` |
| Public market/rank/projection context | ADP, public rankings, projections, consensus, market values, trade values/calculators |
| RotoWire context | rankings, projections, outlooks, values |
| Draft-history context | prior fantasy draft history |
| Legacy private context | legacy `private_score` |
| Leakage fields | same-season target final stats as preseason features |
| Label supplements as features | any label supplement source used as a prediction feature |

These fields either are present and quarantined by allowlist, or remain forbidden even if introduced by future source joins.

## 6. First-Down Registration Result

Rushing and receiving first downs are available and safe as completed prior-season source features.

| Source season | `rushing_first_downs` non-missing rows | `receiving_first_downs` non-missing rows | Result |
| ---: | ---: | ---: | --- |
| 2017 | 5,319 | 5,319 | pass |
| 2018 | 5,281 | 5,281 | pass |

Passing first downs are present in the source header but are not approved by this registration audit as a veteran Outcome feature. Return yards and return TD fields are not present in the source header.

## 7. Identity, Team, Position, And Key Uniqueness

Identity and context coverage:

| Source season | Missing player IDs | Missing player names | Missing display names | Missing teams | Missing positions | Missing position groups |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2017 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2018 | 0 | 0 | 0 | 0 | 0 | 0 |

Duplicate key definition:

`player_id + season + week + season_type`

| Source season | Duplicate key extra rows | Result |
| ---: | ---: | --- |
| 2017 | 0 | pass |
| 2018 | 0 | pass |

Identity/team/position verdict: pass for source registration. A future rebuild still needs a join audit against the stable identity/DOB source and a team mapping QA pass before modeling.

## 8. Label And Leakage Policy

Future 2018 and 2019 target-season labels may use same-season final stats only as labels.

Required legal mapping:

| Future target season | Legal preseason feature source | Legal label source |
| ---: | ---: | --- |
| 2018 | completed 2017 source facts | final 2018 source-safe NWR outcome labels |
| 2019 | completed 2018 source facts | final 2019 source-safe NWR outcome labels |

Forbidden leakage examples:

- using 2018 final stats as 2018 preseason features
- using 2019 final stats as 2019 preseason features
- copying `fantasy_points` or `fantasy_points_ppr` as labels or features
- using EPA, WOPR, target-share, projection, ranking, ADP, market, trade-value, RotoWire, or private-score fields as prediction features

Leakage-risk result: controlled if and only if the later rebuild enforces source season `S` strictly before target season `S+1`.

## 9. Missingness, Drift, And Source Concerns

Remaining concerns:

| Concern | Status | Required handling |
| --- | --- | --- |
| Missingness | core identity and allowed component fields pass for source registration | re-audit after any aggregation/rebuild |
| Era drift | 2017-2018 are close to 2020-2024 but still earlier seasons | compare expanded model calibration against unchanged 2023/2024 holdouts |
| Scoring drift | NWR scoring must be reconstructed from source-safe components | verify label formula and tie handling |
| Source drift | 2017-2018 are newly registered relative to 5W's 2019-2024 registration | keep separate provenance and audit metadata |
| Team/position drift | raw fields are present, but team semantics can drift | run mapping QA before modeling |
| Return scoring | return yards/TD support is not complete from this source | do not include unless separately approved |
| Postseason rows | present | exclude from preseason feature source unless separately approved |

## 10. Future Modeling Gate

Future 2018-2019 target expansion is not approved for modeling now.

Before any model run, a later sprint must:

1. Build a local-only 2018-2019 historical feature/label rebuild package.
2. Enforce completed prior-season feature legality.
3. Rebuild 2018/2019 labels from source-safe NWR components.
4. Re-run forbidden-field and leakage scans.
5. Run identity/DOB, team, position, duplicate-key, and blocked-row audits.
6. Keep rookies out of veteran heads.
7. Preserve the existing 2023 validation and 2024 test holdout plan unless HQ approves a split change.
8. Keep outputs internal-only and not app-readable.
9. Pass adversarial audit before any calibration comparison.

## 11. Release And Display Stance

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

App-readable probability, band, or status tables remain blocked.

Rankings/sorting usage remains blocked.

Hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe unchanged. Sprint 5BT does not touch app code.

## 12. Recommended Next Safe Sprint

Recommended next safe sprint:

`Sprint 5BU - Local-Only 2018-2019 Historical Feature and Label Rebuild Plan`

Scope:

- Plan the local-only rebuild contract for future target seasons 2018 and 2019.
- Define exact feature and label schemas before generating rows.
- Define artifact quarantine, split discipline, leakage checks, and population policy.
- Do not train models.
- Do not create app-readable outputs.
- Do not release probabilities or bands.

## 13. Final Gate Label

Final gate label:

`FORMAL_2017_2018_COMPLETED_PRIOR_SEASON_REGISTRATION_GREEN_MODELING_BLOCKED`

Meaning:

- 2017 source registration is GREEN for completed prior-season future use.
- 2018 source registration is GREEN for completed prior-season future use.
- 2018/2019 target expansion is not approved for modeling yet.
- Same-season target stats may be labels only.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting and hidden sort keys remain blocked.
- Promoted artifacts remain blocked.
