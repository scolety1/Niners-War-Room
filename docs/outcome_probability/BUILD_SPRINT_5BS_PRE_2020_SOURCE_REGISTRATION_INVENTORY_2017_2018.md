# Sprint 5BS: Pre-2020 Source Registration Inventory for 2017-2018 Player Stats

Outcome lane: veteran outcome probability column path only

Verdict: `YELLOW_FOR_FUTURE_MODELING_FEASIBILITY_GREEN_FOR_INVENTORY`

Sprint type: `DOCS_ONLY_SOURCE_REGISTRATION_INVENTORY`

## 1. Scope

Sprint 5BS inventories source seasons 2017 and 2018 from local `player_stats.csv` as the first controlled step toward pre-2020 veteran Outcome historical expansion. This sprint does not register a release source, build training rows, train models, release probabilities, wire app display, alter rankings/sorting, create hidden sort keys, score rookies through veteran heads, or create promoted artifacts.

Primary future target mapping:

| Source season | Intended future target season | Intended use |
| --- | ---: | --- |
| 2017 | 2018 | completed prior-season preseason features |
| 2018 | 2019 | completed prior-season preseason features |

Read-only evidence:

- `docs/outcome_probability/BUILD_SPRINT_5BR_PRE_2020_HISTORICAL_UNIVERSE_FEASIBILITY_AUDIT.md`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `local_exports/outcome_probability/sprint_5w_older_player_stats_source_registration/README_SPRINT_5W.md`
- `local_exports/outcome_probability/sprint_5w_older_player_stats_source_registration/completed_prior_season_registration.csv`

No local exports were created. No files under `data/` or `local_exports/` were edited.

## 2. Source File

Local source path:

`local_exports/truth_set_lab/v3/downloads/player_stats.csv`

File status: present.

Header includes:

- identity fields: `player_id`, `player_name`, `player_display_name`
- roster/context fields: `position`, `position_group`, `recent_team`, `season`, `week`, `season_type`, `opponent_team`
- offensive components: passing/rushing/receiving yards, TDs, interceptions, receptions, rushing and receiving first downs, fumble-lost components
- special teams TDs: `special_teams_tds`
- forbidden or quarantined convenience fields: `fantasy_points`, `fantasy_points_ppr`, EPA fields, `dakota`, `wopr`, `racr`, `pacr`, `target_share`, `air_yards_share`

Header does not include:

- `return_yards`
- `return_tds`

Return-yard/return-TD support is therefore not approved from this source inventory.

## 3. 2017-2018 Coverage Summary

| Source season | Rows | Regular-season rows | Postseason rows | Weeks covered | QB/RB/WR/TE rows | Unique player IDs | QB/RB/WR/TE unique IDs |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 2017 | 5,319 | 5,107 | 212 | 1-21 | 5,125 | 587 | 530 |
| 2018 | 5,281 | 5,070 | 211 | 1-21 | 5,112 | 614 | 552 |

Position coverage in the audited rows is broad, with QB/RB/WR/TE carrying nearly all modeled offensive rows. Non-modeled positions also appear and should remain excluded from veteran Outcome head training unless a later sprint explicitly authorizes them.

## 4. Identity, Team, And Position Findings

| Source season | Missing player IDs | Missing player names | Missing display names | Missing teams | Missing positions | Missing position groups |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2017 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2018 | 0 | 0 | 0 | 0 | 0 | 0 |

Inventory result: player IDs, player names, display names, teams, positions, and position groups are present for 2017 and 2018.

Future modeling still requires an identity join audit against the stable identity/DOB metadata source and a player/team mapping QA pass. Presence in the raw source is necessary but not sufficient for registration.

## 5. Duplicate Player-Week Key Audit

Duplicate key definition:

`player_id + season + week + season_type`

| Source season | Duplicate player-week extra rows | Result |
| --- | ---: | --- |
| 2017 | 0 | pass |
| 2018 | 0 | pass |

Inventory result: no duplicate player-week keys were detected for 2017 or 2018 using the audited key.

## 6. Component Availability

All rows in both audited seasons have non-missing values for the core allowlisted offensive components below.

| Component | 2017 non-missing rows | 2018 non-missing rows | Inventory result |
| --- | ---: | ---: | --- |
| Passing yards | 5,319 | 5,281 | present |
| Passing TDs | 5,319 | 5,281 | present |
| Interceptions | 5,319 | 5,281 | present |
| Carries | 5,319 | 5,281 | present |
| Rushing yards | 5,319 | 5,281 | present |
| Rushing TDs | 5,319 | 5,281 | present |
| Rushing first downs | 5,319 | 5,281 | present |
| Receptions | 5,319 | 5,281 | present |
| Receiving yards | 5,319 | 5,281 | present |
| Receiving TDs | 5,319 | 5,281 | present |
| Receiving first downs | 5,319 | 5,281 | present |
| Rushing fumbles lost | 5,319 | 5,281 | present |
| Receiving fumbles lost | 5,319 | 5,281 | present |
| Sack fumbles lost | 5,319 | 5,281 | present |
| Special teams TDs | 5,319 | 5,281 | present, not automatically approved |

First-down result: rushing and receiving first downs are present for all audited 2017 and 2018 rows.

Return result: return yards and return TD fields are absent. `special_teams_tds` is present, but it should not be treated as a complete return-scoring source without a separate scoring policy review.

## 7. NWR Scoring Label Reconstructability

NWR scoring labels likely can be reconstructed for QB/RB/WR/TE from 2017 and 2018 player stats if the 5W allowlist is extended backward and the same legal policy is applied.

Supported by this inventory:

- passing yards
- passing TDs
- interceptions
- rushing yards
- rushing TDs
- rushing first downs
- receptions
- receiving yards
- receiving TDs
- receiving first downs
- fumble-lost components

Not approved by this inventory:

- fantasy total shortcuts
- EPA-derived or target-share-derived features
- return yards
- complete return TD treatment
- same-season target stats as preseason features

Future label reconstruction should rebuild NWR scoring from source-safe components rather than copying `fantasy_points` or `fantasy_points_ppr`.

## 8. Legal Preseason Feature Feasibility

Legal preseason feature construction is feasible in principle under the completed prior-season rule:

`source season S -> target preseason S+1`

Allowed future examples:

| Future target season | Completed prior source season | Feasibility |
| ---: | ---: | --- |
| 2018 | 2017 | likely feasible after formal registration |
| 2019 | 2018 | likely feasible after formal registration |

Required guardrails:

- Use only source-season facts strictly before the target season.
- Never use target-season final stats as preseason features.
- Aggregate weekly rows before season-level feature use.
- Preserve missing optional values rather than filling from future data.
- Keep rookies out of veteran heads unless a separate rookie path is approved.
- Use source-safe component allowlists rather than convenience totals.

## 9. Forbidden And Leakage Risk Findings

Forbidden or high-risk fields are present in the source and must remain quarantined:

| Field family | Present? | Handling |
| --- | --- | --- |
| `fantasy_points`, `fantasy_points_ppr` | yes | exclude; do not use as features or label shortcuts |
| EPA fields | yes | exclude unless separately approved |
| `dakota`, `wopr`, `racr`, `pacr` | yes | exclude unless separately approved |
| `target_share`, `air_yards_share` | yes | exclude unless separately approved |
| ADP/public rankings/projections/consensus/market/trade values | not detected in source header | remain forbidden |
| RotoWire rankings/projections/outlooks/values | not detected in source header | remain forbidden |
| prior fantasy draft history | not detected in source header | remain forbidden |
| legacy `private_score` | not detected in source header | remain forbidden |

Same-season leakage risk:

- The file contains season-level facts by source season. That is legal only when source season `S` is used for target preseason `S+1`.
- Using 2018 stats as 2018 preseason features or 2019 stats as 2019 preseason features would be leakage and remains forbidden.

## 10. 2010-2019 Apparent Coverage Note

Read-only source inventory found apparent local coverage for each season from 2010 through 2019.

| Season | Rows | Regular-season rows | Weeks covered | QB/RB/WR/TE rows | Unique player IDs | Notes |
| ---: | ---: | ---: | --- | ---: | ---: | --- |
| 2010 | 5,204 | 4,988 | 1-21 | 4,891 | 580 | future inventory only |
| 2011 | 5,301 | 5,091 | 1-21 | 5,003 | 586 | future inventory only; minor missing position rows |
| 2012 | 5,354 | 5,150 | 1-21 | 5,005 | 603 | future inventory only; minor missing position rows |
| 2013 | 5,231 | 5,022 | 1-21 | 4,919 | 591 | future inventory only; minor missing position rows |
| 2014 | 5,350 | 5,129 | 1-21 | 5,107 | 589 | future inventory only; minor missing position rows |
| 2015 | 5,318 | 5,101 | 1-21 | 5,109 | 594 | future inventory only |
| 2016 | 5,274 | 5,062 | 1-21 | 5,086 | 593 | future inventory only |
| 2017 | 5,319 | 5,107 | 1-21 | 5,125 | 587 | primary 5BS target |
| 2018 | 5,281 | 5,070 | 1-21 | 5,112 | 614 | primary 5BS target |
| 2019 | 5,261 | 5,046 | 1-21 | 5,079 | 617 | already covered by 5W registration pattern |

This note does not approve 2010-2016 modeling. Those seasons remain future inventory only unless directly audited in a later sprint.

## 11. Source Registration Verdict

Verdict: `YELLOW`

Reason:

- 2017 and 2018 player stats are present.
- Identity, team, position, first-down, yards, TD, interception, and fumble-lost components look complete for the audited rows.
- Duplicate player-week keys were not found.
- Legal preseason features likely can be built under the completed prior-season policy.
- However, pre-2019 seasons are not formally registered by the existing 5W registration packet.
- Forbidden/convenience columns are present and require strict allowlist quarantine.
- Return yards and complete return TD support are absent.
- Same-season leakage must be explicitly blocked in any future rebuild.

This is green for continuing source-registration work, yellow for future modeling feasibility, and red for any immediate release/display.

## 12. Required Gates Before Modeling

Before any larger-universe model run:

1. Formally register 2017 and 2018 under the completed prior-season fact policy.
2. Re-run component allowlist and forbidden-field scans.
3. Validate identity/DOB joins.
4. Validate team and position mappings.
5. Rebuild target-season labels from source-safe NWR components.
6. Prove no target-season final stats are used as preseason features.
7. Audit blocked rows and missing required features.
8. Keep all generated artifacts local-only and not app-readable.
9. Run an adversarial audit before any training expansion is trusted.

## 13. Release And Display Stance

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

App-readable probability, band, or status tables remain blocked.

Rankings/sorting usage remains blocked.

Hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe unchanged. Sprint 5BS does not touch app code.

## 14. Recommended Next Safe Sprint

Recommended next safe sprint:

`Sprint 5BT - Formal 2017-2018 Completed Prior-Season Registration Audit`

Scope:

- Register 2017 and 2018 player stats using the 5W completed prior-season source policy.
- Emit only docs or HQ-approved local-only audit outputs.
- Confirm derived availability dates and target preseason cutoffs.
- Re-run forbidden-field, component, duplicate-key, identity, team, position, first-down, and leakage audits.
- Do not train models or create app-readable outputs.

## 15. Final Gate Label

Final gate label:

`PRE_2020_2017_2018_SOURCE_INVENTORY_YELLOW_MODELING_FEASIBILITY_RELEASE_BLOCKED`

Meaning:

- 2017 and 2018 source rows are present and promising.
- First downs and core NWR scoring components are present.
- Player ID, team, and position fields are present.
- No duplicate player-week keys were found for 2017 or 2018.
- Formal source registration is still required.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting and hidden sort keys remain blocked.
- Promoted artifacts remain blocked.
