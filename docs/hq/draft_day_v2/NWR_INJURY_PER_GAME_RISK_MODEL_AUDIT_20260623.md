# NWR Injury + Per-Game Risk Model Audit - 2026-06-23

## Final Verdict

YELLOW.

The audit is complete and safe, but NWR does **not** currently have enough approved current injury / games-missed / recovery-history coverage to create a player-facing injury score or to automate model/rank changes. The right next step is a display-first data contract and Player Compare presentation improvement, not a new injury model.

This report and CSV do not mutate the frozen board, Dynasty Rank, `latest_candidate`, `latest_approved`, pinned snapshot, model logic, or app behavior.

## Current Data Available

| Source | Path / Artifact | Classification | What It Can Support | What It Cannot Support Yet |
|---|---|---|---|---|
| Frozen final board | `docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.csv` | verified internal / frozen export | final board rank, asset type, age in later app overlay, risk notes, manual review flags | direct current injury status, games missed, per-game vs total split |
| Expanded draftable app pool | service `load_expanded_draftable_player_pool()` | current app/runtime display layer | age display, source group, candidate/on-clock warnings, PDF/free-agent overlay | approved medical/injury conclusions |
| Full dynasty source | `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` | verified internal / candidate-review-only | NWR dynasty rank/score, warning flags, data-needed notes, age gaps, source limitations | current injury report, medical recovery status, verified games missed |
| Outcome display | `C:\NWR\Niners-War-Room-outcome\app\generated\outcome_probability\numeric_outcome_display_v1.csv` and app prop `outcome_player_context.csv` | approved display-only | current position-aware Outcome probabilities where matched | injury causality or recovery risk |
| Injury durability service | `src/services/lve_injury_durability_service.py` | implemented internal derivation service | availability rate, report weeks, out weeks, limited/DNP weeks, recurrence, lower-body flags if nflverse injury/stats/snap rows exist | current draft-day coverage unless populated with real source rows |
| nflverse stats upgrade templates | `templates/real_data_inputs/nflverse_stats_upgrade/` | schema/template only | intended schema for weekly stats, snaps, participation, injuries | no broad current player coverage; template rows are not live data |
| Public-source injury input template | `templates/real_data_inputs/public_sources/player_injury_inputs.csv` | schema/template only | proposed injury source fields including games-missed proxy and report status | no current filled source for the audited players |
| API-SPORTS injury fallback | `docs/hq/parallel_lanes/NWR_API_SPORTS_INJURY_DISPLAY_CONTEXT_V0.md` and script `scripts/api_sports_injury_display_context_v0.py` | YELLOW display-only candidate; no current rows | possible future live injury/practice display context if API access works | no approved 2026 data; initial probe was blocked by plan/season access |
| Older model audits/sample veteran features | `docs/model_audits/`, `sample_data/veteran_model_v1/` | manual/candidate/diagnostic | shows prior injury-durability concepts and some example feature values | not current approved source truth; should not drive app/model automatically |

## Biggest Missing Data

- Current injury/practice status for the draftable pool.
- Verified games played / games missed by season for current board players.
- A clean split between season total production and per-game production for all relevant players.
- Recovery context from major injuries.
- Chronic/recurrent injury history with source lineage.
- Current availability/participation risk that is not merely an old warning flag.
- Player-specific injury confidence, distinct from general model confidence.

Missing injury data must not be displayed as clean health. The display phrase should be:

`Not enough information`

## Taxonomy

1. **Per-game performance signal**: How productive a player was when active. This should protect players from being punished for injury-shortened season totals.
2. **Annual total signal**: Full-season usefulness, including availability. This still matters for fantasy outcomes, but it should not be confused with talent.
3. **Injury-shortened season context**: Explicit flag that a low annual total may be volume/missed-time driven.
4. **Current injury/status risk**: Current report/practice/status information. Must be sourced and timestamped.
5. **Recovery risk from major injury**: Return-from-major-injury uncertainty. Requires sourced injury type/date/context.
6. **Chronic injury history risk**: Recurrent same-area or repeated missed-time risk. Requires multi-event source evidence.
7. **Availability/participation risk**: Games active, snaps/routes, participation, weekly availability.
8. **Not enough information**: Default when data is missing. This is not a clean-health label.

## Proposed Safe Display Fields

- `per_game_signal_available`
- `annual_total_signal_available`
- `games_missed_signal`
- `injury_shortened_year_flag`
- `current_injury_status_available`
- `current_injury_status`
- `recovery_risk_band`
- `chronic_injury_risk_band`
- `injury_data_confidence`
- `model_treatment_summary`
- `human_review_warning`

Rules:

- `Not enough information` means unknown, not healthy.
- Same player can have strong per-game signal and high availability risk.
- Injury/recovery bands should be display-only until source coverage and validation improve.
- Do not collapse this into a single hidden score.

## Player Audit Table

Detailed CSV:

`docs/hq/draft_day_v2/injury_per_game_risk_audit_20260623.csv`

Key findings:

| Player | Current Evidence Summary | Risk Display Finding |
|---|---|---|
| Jameson Williams | Expanded pool, full dynasty, Outcome, risk notes present; no current injury/games-missed source. | Show per-game/availability distinction; current injury status is `Not enough information`. |
| Brian Thomas Jr | Matched via current app/dynasty alias context; no current injury/games-missed source. | Identity/history caveats should remain visible; do not infer health. |
| Zay Flowers | Strong dynasty/context presence; no current injury/games-missed source. | Should not be penalized by missing injury data; show unknown health context. |
| Chris Olave | Dynasty/outcome context present; first-down/role evidence caveats; no injury source. | If season totals look low, Player Compare should ask whether availability explains it. |
| Drake Maye | QB outcome context exists; 1QB guardrails present; no injury source. | Injury not supported as a differentiator. Keep 1QB context separate from health. |
| Tyreek Hill | PDF free agent overlay, age/status warning; no approved current injury source. | Loud human review: age/current-status risk, but do not fabricate injury conclusion. |
| Keenan Allen | Frozen/dynasty rows include no-team/current-status context and age cliffs. | Human review required; current injury status still `Not enough information`. |
| Darren Waller | No-team/current-status context plus TE age cliff/retirement-health warning language. | Human review required; do not treat as normal healthy veteran. |
| Rashee Rice | Expanded pool/outcome/dynasty context; no current injury source. | Current injury/availability unknown; keep legal/status/role caveats separate if present elsewhere. |
| Jaylen Warren | Dynasty age-window and role/data caveats; no current injury source. | Availability unknown; age/RB role risk should be visible but not medicalized. |
| Jeremiyah Love | Rookie board context and role manual question; no current injury source. | Rookie health/recovery history unavailable; do not mark clean. |
| Makai Lemon | Rookie role/depth manual question; no current injury source. | Same: unknown health, role evidence is the main risk. |
| Carnell Tate | Rookie source/rank support question; no current injury source. | Do not add injury risk beyond missing information. |
| KC Concepcion | Missing age in app source, role/depth manual question, no current injury source. | Data gap should be visible; no health conclusion. |
| Jadarian Price | Rookie role/depth manual question; no current injury source. | Unknown health; do not downgrade as injured or upgrade as clean. |

## Player Compare Recommendation

Player Compare should show injury/per-game risk as a compact decision block:

- **Per-game talent**: available / not enough information.
- **Season-total context**: available / not enough information.
- **Availability context**: games missed / injury-shortened year / not enough information.
- **Current status**: current injury/practice/team status if sourced, otherwise `Not enough information`.
- **Recovery/chronic risk**: only if sourced; otherwise `Not enough information`.
- **Interpretation**: one sentence explaining whether low totals are likely performance or availability driven.

Keep detailed source rows behind an expander. Do not show a fabricated medical conclusion, and do not bury the decision summary under raw injury tables.

## Model / Ranking Recommendations

Do:

- Separate per-game scoring strength from full-season availability.
- Use games played/missed and active/snap weeks only when sourced.
- Treat current injury/status as display-only until source coverage is approved.
- Use injury data as a confidence/risk modifier, not a dominant value driver.
- Flag “season total may understate player because injured” when per-game signal is good and games missed is sourced.
- Flag “annual usefulness risk” when per-game is good but missed-time recurrence is sourced.

Do not:

- Penalize missing injury data as if the player is injured.
- Treat missing injury data as clean health.
- Use API-SPORTS or other current injury sources in model/rank logic before approval.
- Infer chronic/recovery risk from age alone.
- Convert old diagnostic/manual injury scores into current app values.
- Create a single hidden injury sort or private value.

## What Should Not Be Automated Yet

- Player-facing injury score.
- Chronic injury band.
- Recovery risk band.
- Current status risk band.
- Any model/rank adjustment from live injury status.

These should wait until a source lane produces verified player-level rows with dates, source status, coverage, and tests.

## Next Implementation Lane Prompt

Use this later if Master approves:

> Implement Injury / Per-Game Display V2 for Player Compare only. Use the approved field contract from `NWR_INJURY_PER_GAME_RISK_MODEL_AUDIT_20260623.md`. Do not create a score. Add a compact display block that distinguishes per-game production, season-total context, availability/games-missed context, current injury status, recovery/chronic risk, and missing data. All missing values must say `Not enough information`. Do not change ranks, models, source truth, frozen board, latest files, or pinned snapshot. Use display-only labels and add focused tests.

## Validation

- CSV load validation: passed.
- `git diff --check`: pending at report write, required before commit.
- Frozen board row count must remain `66`.
- Pinned snapshot hash must remain `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`.
- No app/model/source-truth files changed by this audit.
