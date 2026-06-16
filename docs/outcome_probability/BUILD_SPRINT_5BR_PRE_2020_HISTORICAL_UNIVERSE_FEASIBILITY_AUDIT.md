# Sprint 5BR: Pre-2020 Historical Universe Feasibility Audit

Outcome lane: veteran outcome probability column path only

Verdict: `PRE_2020_EXPANSION_FEASIBLE_FOR_INVENTORY_ONLY_RELEASE_BLOCKED`

Sprint type: `DOCS_ONLY_INVENTORY_RESEARCH`

## 1. Scope

Sprint 5BR audits whether the veteran Outcome historical universe can safely expand before 2020. This is an inventory and feasibility checkpoint only. It does not build new training rows, model outputs, probability tables, band tables, app-readable status tables, app wiring, rankings/sorting changes, hidden sort keys, rookie framework work, or promoted artifacts.

Evidence reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BQ_OUTCOME_INTERNAL_STATUS_POLICY_LARGER_UNIVERSE_FEASIBILITY.md`
- `docs/outcome_probability/BUILD_SPRINT_5BP_OUTCOME_COLUMN_RELEASE_PATH_DECISION_MATRIX.md`
- `docs/outcome_probability/BUILD_SPRINT_5BI_INTERNAL_HOLDOUT_CALIBRATION_PACKAGE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BJ_5BI_HOLDOUT_CALIBRATION_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5BK_CALIBRATION_INSTABILITY_ROOT_CAUSE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BL_CALIBRATION_BIN_SENSITIVITY_ABSTENTION_POLICY.md`
- `docs/outcome_probability/BUILD_SPRINT_5BM_THRESHOLD_GROUPING_POOLED_CALIBRATION_RESEARCH.md`
- `local_exports/outcome_probability/sprint_5v_season_expansion_calibration_readiness/`
- `local_exports/outcome_probability/sprint_5w_older_player_stats_source_registration/`
- `local_exports/outcome_probability/sprint_5x_2020_2022_historical_rebuild/`

Local exports were used as read-only evidence only and must not be committed.

## 2. Executive Feasibility Decision

Pre-2020 expansion appears feasible enough for a formal inventory sprint, but not approved for modeling.

Key findings:

- Local `player_stats.csv` coverage is reported from 1999 through 2024.
- The already-registered 2019-2024 slice supports completed prior-season factual reconstruction for target preseasons 2020-2025.
- The raw source header includes player ID, position, team, weekly season fields, rushing first downs, receiving first downs, NWR scoring components, and quarantined convenience fields.
- First expansion before 2020 should target target seasons 2018-2019, using source seasons 2017-2018 as completed prior-season feature inputs and target seasons 2018-2019 as outcome labels.
- Target seasons before 2018 may be plausible later, but they carry more era drift, identity drift, and scoring comparability risk.

Release implication: no exact percentages, coarse bands, app wiring, rankings/sorting, hidden sort keys, or promoted artifacts are eligible from this feasibility audit.

## 3. Potentially Usable Pre-2020 Seasons

Potential source coverage:

| Season family | Feasibility read | Current approval |
| --- | --- | --- |
| Source seasons 1999-2018 | Potentially available in local `player_stats.csv` according to 5V source coverage. | Not registered for Outcome expansion. |
| Target seasons 2000-2019 | Potentially reconstructable if prior source season and same-year labels pass audit. | Not approved. |
| Target seasons 2018-2019 | Best first pre-2020 expansion target because they are closest to the approved 2020-2024 universe. | Recommended for next inventory sprint. |
| Target seasons before 2018 | Possible later extension if 2018-2019 passes. | Defer until closer-era audit passes. |

The first safe expansion range should be narrow. Jumping directly from 2020-2024 to the full 2000-2019 history would mix too many unquantified risks into one sprint.

## 4. Source And Local File Availability

Read-only local evidence identifies these candidate sources:

| Source/local file family | Evidence | Feasibility result |
| --- | --- | --- |
| `local_exports/truth_set_lab/v3/downloads/player_stats.csv` | 5V reports 1999-2024 raw weekly player stats coverage. | Primary candidate for pre-2020 inventory. |
| 5W older player stats registration | Registers 2019-2024 as completed prior-season factual sources. | Policy pattern to extend backward, not proof for pre-2019. |
| DynastyProcess player IDs | 5V reports broad stable identity/DOB metadata candidate coverage. | Candidate identity bridge; needs season-specific join audit. |
| Truth-set v3 production/usage/snap-share reports | 5V reports 2022-2024 only and current-source-date enrichment. | Not sufficient for pre-2020 feature reconstruction. |
| Play-by-play and snap counts | 5V reports 2022-2024 only for the audited packet. | Not a pre-2020 unlock in current evidence. |

The next sprint should inventory the raw source season-by-season for 2017-2019 first, then decide whether 2016 and earlier deserve the same treatment.

## 5. NWR Scoring Label Reconstructability

NWR labels appear likely reconstructable for QB/RB/WR/TE if the same allowlisted component policy from 5W can be extended backward.

Available component families in the registered 5W policy:

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
- fumbles lost derived from rushing, receiving, and sack fumble lost fields
- games played or active games from regular-season weekly rows

The raw source also contains `fantasy_points` and `fantasy_points_ppr`, but those must remain quarantined and excluded. NWR scoring labels should be rebuilt from allowlisted raw components, not copied from fantasy total columns.

## 6. First-Down Availability

Current finding: promising but not fully approved pre-2020.

Evidence:

- The raw `player_stats.csv` header includes `rushing_first_downs` and `receiving_first_downs`.
- 5W confirms rushing and receiving first downs are present and registered for source seasons 2019-2024.
- Pre-2019 first-down completeness was not proven in this sprint.

Feasibility decision:

| Component | Pre-2020 status | Required next audit |
| --- | --- | --- |
| Rushing first downs | likely available by schema, but unverified for pre-2019 | season-by-season non-null and aggregation audit |
| Receiving first downs | likely available by schema, but unverified for pre-2019 | season-by-season non-null and aggregation audit |
| Passing first downs | present in raw header but not part of the 5W allowed NWR feature list | keep out unless separately approved |
| First-down reconstruction from play-by-play | not supported for pre-2020 by current local evidence | do not rely on it for first expansion |

If pre-2019 rushing or receiving first downs are missing or inconsistent, first expansion should either block or run a separate first-down reconstruction feasibility sprint before modeling.

## 7. Player ID, Team, And Position Mapping

Player IDs:

- The raw source has a `player_id` column.
- 5W reports 100% player ID coverage for the audited 2019-2024 source seasons.
- 5V identifies DynastyProcess identity metadata as a stable identity/DOB candidate with broad season coverage.
- Pre-2019 ID coverage and crosswalk quality remain unproven until audited.

Team and position:

- The raw source has `position`, `position_group`, `recent_team`, `season`, `week`, `season_type`, and `opponent_team`.
- 5W reports 100% position coverage for 2019-2024.
- Pre-2019 team and position trustworthiness remains unproven.

Required next audit checks:

1. Player ID coverage by source season.
2. Duplicate player-week keys.
3. Position missingness and position changes across a season.
4. Team abbreviation consistency and relocation/renaming behavior.
5. Player-name collision review for missing or ambiguous IDs.
6. Join coverage against the identity/DOB source.

## 8. Legal Preseason Feature Feasibility

Legal preseason features appear feasible if the completed prior-season policy is extended backward.

Allowed pattern:

- Source season `S` can support target preseason `S+1`.
- Use only completed prior-season facts available before the target prediction cutoff.
- Same-season final stats for target season `S+1` can be labels only, never preseason features.
- Derived availability date and prediction cutoff policy should mirror the 5W completed prior-season registration unless HQ revises it.

Likely consistent feature families:

| Feature family | Feasibility | Notes |
| --- | --- | --- |
| Age/experience | feasible if identity/DOB and season math pass | Needs identity join audit. |
| Prior completed-season NWR PPG | feasible from allowlisted scoring components | Must not use fantasy total shortcuts. |
| Prior completed-season NWR finish rank | feasible from reconstructed NWR scoring | Must be computed only from source season `S`. |
| Games/active games | feasible from weekly regular-season rows | Must aggregate before season-level use. |
| Receptions | likely consistent | Present in source schema. |
| Rushing/receiving yards | likely consistent | Present in source schema. |
| Passing yards/TDs/interceptions | likely consistent | Useful for QB and possible cross-position support. |
| Rushing/receiving first downs | promising but must be audited for pre-2019 completeness | Do not assume without season-by-season check. |
| Fumbles lost | feasible if component columns are present and consistently populated | Must derive from source-safe fumble lost columns. |

Risky or forbidden features:

- ADP
- public rankings
- projections
- consensus
- market values
- trade values/calculators
- RotoWire rankings/projections/outlooks/values
- prior fantasy draft history
- legacy `private_score`
- same-season final stats as preseason features
- label supplement sources as prediction features
- `fantasy_points` and `fantasy_points_ppr` shortcuts
- EPA, WOPR, target-share, air-yards-share, and similar analytic context columns unless separately approved

## 9. Recommended First Expansion Range

Recommended first expansion feasibility target:

`target seasons 2018-2019`

Required source seasons:

`2017-2018 completed prior-season player_stats`

Reason:

- Closest pre-2020 seasons to the current approved 2020-2024 universe.
- Smaller era/scoring/usage drift than deeper history.
- Adds two target seasons if feasible, which may materially improve rare threshold support without taking on the full 2000-2019 risk at once.
- Exercises the backward-registration process before committing to a larger rebuild.

Fallback if 2017 source coverage is weak:

`target season 2019 only`, using 2018 completed prior-season features.

Do not expand directly to 1999-2019 in one step.

## 10. Safest Validation/Test Strategy

If pre-2020 data becomes usable, the safest first modeling split is:

| Split | Seasons | Rationale |
| --- | --- | --- |
| Train | 2018-2022 if 2018-2019 pass; otherwise 2019-2022 or current 2020-2022 | Adds older examples only to training first. |
| Validation | 2023 | Preserve existing post-training holdout. |
| Test | 2024 | Preserve newest complete independent holdout. |

Do not move 2023/2024 into training for the first pre-2020 expansion run. Keeping the existing validation/test split makes the expanded training universe comparable to 5BI and avoids hiding era drift behind a changed evaluation setup.

Future alternate split research may test rolling-origin validation, but only after the first expanded training audit passes.

## 11. Blockers Before Any Larger-Universe Model Run

Blockers that must be resolved before modeling:

1. Register pre-2019 source seasons explicitly under the completed prior-season fact policy.
2. Verify rushing and receiving first-down completeness for source seasons 2017-2018.
3. Verify QB/RB/WR/TE NWR label reconstruction for target seasons 2018-2019.
4. Confirm player ID coverage and identity/DOB join coverage.
5. Confirm team and position mappings are stable enough for aggregation and labels.
6. Confirm no same-season target stats leak into preseason features.
7. Re-run forbidden source/feature scans.
8. Quarantine fantasy total columns, EPA columns, target-share/WOPR-style analytic context, and all rank/projection/market/private-score contexts.
9. Audit missingness and blocked rows before training.
10. Keep rookies out of veteran heads.
11. Keep kickers not applicable.
12. Emit only local-only internal audit artifacts if HQ authorizes a later rebuild.

## 12. Release And Display Stance

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

App-readable probability, band, or status tables remain blocked.

Rankings/sorting usage remains blocked.

Hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy may remain safe unchanged, per 5BP/5BQ. Sprint 5BR does not touch app code or create new app-readable status output.

## 13. Recommended Next Safe Sprint

Recommended next safe sprint:

`Sprint 5BS - Pre-2020 Source Registration Inventory for 2017-2018 Player Stats`

Scope:

- Docs/local-only inventory only.
- Audit `player_stats.csv` source seasons 2017 and 2018 for target seasons 2018 and 2019.
- Check first-down completeness, player IDs, team/position mapping, duplicate player-week keys, component coverage, forbidden fields, and derived availability policy.
- Do not build model outputs.
- Do not create app-readable artifacts.
- Do not change rankings/sorting, app wiring, rookie framework, or promoted artifacts.

## 14. Final Gate Label

Final gate label:

`PRE_2020_HISTORICAL_UNIVERSE_FEASIBILITY_TARGET_2018_2019_RELEASE_BLOCKED`

Meaning:

- Pre-2020 expansion is plausible but not approved for modeling.
- Target seasons 2018-2019 are the safest first feasibility range.
- First-down, identity, team, position, source registration, and leakage checks must pass first.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting and hidden sort keys remain blocked.
- Promoted artifacts remain blocked.
