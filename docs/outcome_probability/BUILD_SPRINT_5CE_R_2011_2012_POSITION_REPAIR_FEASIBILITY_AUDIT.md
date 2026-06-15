# Sprint 5CE-R: 2011-2012 Position Repair Feasibility Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_FOR_DETERMINISTIC_REPAIR_FEASIBILITY_REBUILD_STILL_BLOCKED`

Sprint type: `FEASIBILITY_AUDIT_ONLY_NO_REBUILD_NO_MODELING`

## 1. Scope

Sprint 5CE-R audits whether the 2011-2012 blank `position` / `position_group` blocker from Sprint 5CE can be repaired using only source-safe local identity evidence. This sprint does not patch source rows, generate feature/label rebuild rows, train models, generate probabilities, create coarse bands, create app-readable probability/band/status outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, score rookies through veteran heads, or create promoted artifacts.

Read-only evidence:

- `docs/outcome_probability/BUILD_SPRINT_5CE_2011_2012_SOURCE_REGISTRATION_AUDIT.md`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/draft_pool_downloads/dynastyprocess_db_playerids.csv`
- `local_exports/truth_set_lab/v3_2/promoted_review_models/truth_set_v3_2_promoted_review_20260515T212700Z/sleeper_nflverse_identity_bridge.csv`
- `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/draft_pool_downloads/sleeper_players_nfl.csv`
- `config/source_registry.csv`
- `config/api_source_permissions.csv`

No internet lookup was performed. No manual position guesses were used.

## 2. Local-Only Inventory Export

Created local-only inventory package:

`local_exports/outcome_probability/sprint_5ce_r_2011_2012_position_repair_feasibility/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5ce_r.json` | run metadata, source files checked, repairability decision | no |
| `affected_blank_position_offensive_rows.csv` | every affected 2011-2012 offensive row | no |
| `position_repair_source_evidence.csv` | local source-safe position evidence by player | no |
| `position_repair_feasibility_by_player.csv` | repairability decision by player ID | no |
| `README_SPRINT_5CE_R.md` | local package summary | no |

All outputs are internal-only and not app-readable.

## 3. Affected Rows

The audit found 23 affected rows with blank `position` or `position_group` and offensive activity.

Affected row counts:

| Season | Player ID | Player | Team | Rows | Offensive evidence |
| ---: | --- | --- | --- | ---: | --- |
| 2011 | `00-0027567` | Steve Maneri | KC | 2 | receiving/target activity |
| 2011 | `00-0028543` | Jeff Maehl | HOU | 1 | target activity |
| 2012 | `00-0027567` | Steve Maneri | KC | 5 | receiving/target activity |
| 2012 | `00-0029675` | Trent Richardson | CLE | 15 | rushing/receiving activity |
| Total |  |  |  | 23 |  |

Affected player IDs:

- `00-0027567` - Steve Maneri
- `00-0028543` - Jeff Maehl
- `00-0029675` - Trent Richardson

## 4. Local Sources Found

Source-safe local evidence found:

| Source | Local path | Role | Use in repair decision |
| --- | --- | --- | --- |
| DynastyProcess player IDs | `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/draft_pool_downloads/dynastyprocess_db_playerids.csv` | GSIS-keyed identity crosswalk | primary source-safe position evidence |
| Sleeper-to-nflverse identity bridge | `local_exports/truth_set_lab/v3_2/promoted_review_models/truth_set_v3_2_promoted_review_20260515T212700Z/sleeper_nflverse_identity_bridge.csv` | local matched identity bridge | corroborating source-safe position evidence |
| Sleeper players export | `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233/draft_pool_downloads/sleeper_players_nfl.csv` | local player identity export | name/position corroboration only |

`config/source_registry.csv` admits `sleeper,players` as identity evidence and `dynastyprocess,player_ids` as an identity crosswalk while keeping values/ECR market context forbidden. 5CE-R used only identity/position fields, not values, rankings, projections, market data, RotoWire rankings/projections/outlooks/values, or manual guesses.

## 5. Repair Feasibility By Player

| Player ID | Player | Affected rows | Source-safe position found | Evidence sources | Repair grain | Repairable? |
| --- | --- | ---: | --- | --- | --- | --- |
| `00-0027567` | Steve Maneri | 7 | TE | DynastyProcess player IDs; local identity bridge; Sleeper players export | all affected 2011-2012 rows by `player_id` | yes |
| `00-0028543` | Jeff Maehl | 1 | WR | DynastyProcess player IDs; local identity bridge; Sleeper players export | all affected 2011 rows by `player_id` | yes |
| `00-0029675` | Trent Richardson | 15 | RB | DynastyProcess player IDs; local identity bridge; Sleeper players export | all affected 2012 rows by `player_id` | yes |

The repair can be deterministic by `player_id` for all affected 2011-2012 blank offensive rows. Row-specific repair is not required because each affected player has exactly one source-safe position across the local identity evidence.

Manual guessing is not required.

Forbidden sources are not required.

## 6. Repair Policy

Recommended repair policy for a later patch sprint:

1. Apply a tiny deterministic allowlist keyed by `player_id`:
   - `00-0027567` -> `TE`
   - `00-0028543` -> `WR`
   - `00-0029675` -> `RB`
2. Limit repair scope to 2011-2012 rows where `position` or `position_group` is blank.
3. Require offensive activity before repair is applied.
4. Use repaired positions only for source registration, row eligibility, and the normal legal `position` field already present in prior rebuilds.
5. Do not use the repair as a new model signal beyond ordinary source-safe position identity.
6. Emit a local-only repair audit showing before/after counts and source evidence.
7. Re-run 5CE source-registration checks after repair.

No source file is patched in 5CE-R.

## 7. GREEN Feasibility Implication

2011 can become GREEN after repair: yes, if a later deterministic local position repair patch is applied and re-audited.

2012 can become GREEN after repair: yes, if a later deterministic local position repair patch is applied and re-audited.

Current status: 2011-2012 remain blocked until that repair patch exists and passes audit.

## 8. Release Stance

5CE-R does not approve the 2012-2013 rebuild.

5CE-R does not approve modeling.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but this sprint creates no app-readable status table.

## 9. Recommended Next Safe Sprint

Recommended next safe sprint: Sprint 5CE-R2 - deterministic local 2011-2012 position repair patch and source-registration re-audit.

5CE-R2 should not rebuild 2012-2013 rows unless the repair patch passes and explicitly upgrades 2011-2012 source registration to GREEN. The 2012-2013 rebuild requires separate HQ approval after the repair re-audit.

## 10. Checks

Checks run:

- local CSV inventory completed with no downloads and no package installation
- `git diff --check` passed

Ruff was not required because no tracked Python file changed in 5CE-R. Pytest was not required because no tracked code or test file changed in 5CE-R.
