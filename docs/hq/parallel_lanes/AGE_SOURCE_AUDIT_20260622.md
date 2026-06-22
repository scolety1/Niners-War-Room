# Age Source Audit - 2026-06-22

Status: GREEN for source audit. YELLOW for prospect-age recovery because local CFBD artifacts do not carry DOB/age, and the prospect ages found locally are derived artifacts rather than primary source truth.

## Verdict

CFBD does not provide a usable local DOB/age source in the inspected NWR artifacts. The local CFBD files expose height, weight, position, team/school, hometown/recruiting/draft metadata, and player stats, but no `age`, `birth_date`, `birthdate`, `dob`, `date_of_birth`, `birthYear`, or `birth_year` fields.

The best trusted app source for current NFL player age is the normalized nflverse roster display context:

```text
C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_roster_display_context\20260621_011500_timing_metadata_v1\player_roster_display_context.csv
```

It has `birth_date`, `live_use_allowed=true`, and Draft Day App V1 already derives display age from it while leaving missing rows as `Not enough information`.

## Coverage Summary

| Source | Field | Frozen 66 | Expanded 143 | Dynasty 240 | Trusted for app? |
| --- | --- | ---: | ---: | ---: | --- |
| CFBD roster/recruiting/draft local CSVs | none | 0 | 0 | 0 | no |
| Sleeper current scheduled ingest | none | 0 | 0 | 0 | no |
| nflverse roster display context | birth_date | 11 | 81 | 224 | yes |
| nflverse weekly roster display context | birth_date | 11 | 81 | 224 | yes |
| Full dynasty board `age` column | age | 0 | 0 | 0 | no |
| PDF page-3 free-agent artifact | age | 0 | 70 | 2 | no |
| Cross-asset frozen-66 artifact | age | 39 | 39 | 12 | no |
| Recommended audit composite | mixed | 39 | 109 | 225 | no |

Full source table: `docs/hq/parallel_lanes/age_source_audit_20260622/age_source_coverage.csv`.

## CFBD Finding

Inspected local CFBD/CollegeFootballData artifacts:

- `data/college_football_data/raw/csv/roster_2025.csv`: 30072 rows; fields include `id`, `firstName`, `lastName`, `team`, `weight`, `height`, `jersey`, `year`, `position`, hometown fields, and `recruitIds`; no DOB/age.
- `data/college_football_data/raw/csv/recruiting_players_2025_highschool.csv`: 2507 rows; fields include recruiting rank, name, school, committed team, position, height, weight, stars, rating, and hometown; no DOB/age.
- `data/college_football_data/raw/csv/draft_picks_2025.csv`: 257 rows; fields include college/NFL IDs, team, year, pick, name, position, height, weight, pre-draft rank/grade, and hometown; no DOB/age.

Conclusion: locally, CFBD is not the age source.

## Sleeper Finding

Current local Sleeper scheduled snapshots contain league/draft/roster/transaction/user JSON, not the Sleeper `/players/nfl` metadata payload. No local Sleeper age or birthdate field was available in the current snapshot.

There is an older script, `scripts/build_model_v4_sleeper_age_supplement.py`, that can derive age from Sleeper `birth_date`, but its expected output file was not present:

```text
C:\NWR\Niners-War-Room\local_exports\model_v4\prospect_age\latest\sleeper_player_age_supplement_20260528.csv
```

That makes Sleeper a possible external recovery path, not a current local artifact.

## nflverse Finding

nflverse roster metadata is the strongest current local source for NFL-player age because it carries source DOB and normalized candidate timing metadata. Coverage is high for the full current-player/dynasty board: 224 of 240.

It does not solve college prospect age: frozen-board prospect coverage remains limited because many frozen-66 rows are not NFL roster players in nflverse.

## Recovered Derived Ages

The remembered broad age coverage appears to come from derived/report artifacts:

- `cross_asset_candidate_player_board.csv` has 39 of 66 frozen rows with an `age` value.
- `free_agent_pdf_page3_draftable_pool.csv` has 70 of 77 PDF page-3 free-agent rows with `age`, which contributes 70 of the expanded 143.
- `emergency_cross_asset_candidate_player_board.csv` has 224 full-dynasty ages, matching nflverse current-player coverage.

These are useful recovery clues, but they are not primary DOB sources. I do not recommend wiring them as app source-truth without a follow-up provenance check.

## Recommendation

Do not switch the app to CFBD for age. CFBD local artifacts do not have the field.

Keep the app on nflverse roster `birth_date` for current NFL players. If age display must improve for rookies/prospects, run a separate approved prospect-DOB source recovery task. Until then, missing prospect ages should remain `Not enough information` rather than using fabricated or weakly sourced ages.

No app/source-truth wiring was changed in this audit.

## Follow-up Rookie API Check

After the local artifact audit, a read-only live/API metadata check was run for the 54 frozen-board rookie rows against:

- Sleeper `/players/nfl`
- local `nflreadpy.load_players()`
- local `nflreadpy.load_ff_playerids()`

Committed-safe derived output: `docs/hq/parallel_lanes/age_source_audit_20260622/rookie_verified_age_display_20260622.csv`.

The live/API check used targeted Sleeper and nflreadpy metadata to verify coverage, then stripped raw birthdates and vendor IDs from the app-facing artifact. The committed CSV contains only player, position, verified display age, verification status, allowed use, and notes.

Coverage:

| Source | Frozen rookie DOB/age coverage |
| --- | ---: |
| Sleeper live player metadata `birth_date` | 43/54 |
| nflreadpy `load_players().birth_date` | 48/54 |
| nflreadpy `load_ff_playerids().birthdate` or `age` | 41/54 |
| Any checked API birthdate | 48/54 |

Result buckets:

- 40 rookies had matching multi-source DOB evidence.
- 5 rookies had a single checked API DOB source only.
- 3 rookies had conflicting DOBs and require manual review: KC Concepcion, Chris Brazzell, and Dominic Richardson.
- 6 rookies had no DOB from the checked APIs: Eric McAlister, Sieh Bangura, Devin Voisin, O'Mega Blake, Barika Kpeenu, and Braylon James.

Recommendation from this follow-up: Sleeper and nflreadpy can materially improve rookie DOB coverage, but only through a dedicated prospect-DOB intake with identity safeguards. Do not wire a naive name match into the app. `Chris Brazzell` demonstrates why: older same-name rows exist, and even selected 2026 rookie rows disagree between Sleeper/nflreadpy sources.

## Validation

- CSV artifact was generated with required columns only.
- CSV load validation passed after write.
- No frozen board source was mutated.
- No `latest_candidate` or `latest_approved` files were changed by this audit.
- No `C:\NWR_SHARED_DATA` files were tracked or committed by this audit.
