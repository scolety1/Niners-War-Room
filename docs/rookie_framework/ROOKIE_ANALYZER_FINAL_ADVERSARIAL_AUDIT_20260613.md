# Rookie Analyzer Final Adversarial Audit - 2026-06-13

## Executive Verdict

Verdict: GREEN.

The rookie analyzer artifacts remain rookie-only, local/export-only, warning-visible, and non-production. No blocker was found.

## Source Contamination Audit

GREEN.

The analyzer and draft-day simulation builders read only local rookie framework exports. They do not read `data/`, production ranking files, private-score files, app/Streamlit files, outcome files, veteran outcome-head files, probabilities, or bands.

Strict mode rejects prohibited private-value input columns, including ADP, public rankings, projections, consensus, market values, trade values, draft-kit ranks, league rank, legacy `private_score`, probabilities, and bands.

Generated local order fields such as `candidate_rank` and `analyzer_rank` are treated as internal export context only, not as public ranking inputs or production values.

## `rankable_with_warning` Semantics

GREEN.

Current analyzer counts:

- `ready`: `0`
- `rankable_with_warning`: `42`
- `manual_review_required`: `7`
- `blocked`: `43`
- `unavailable`: `119`

`rankable_with_warning` rows remain review-orderable only with visible warnings. They are not treated as clean ready rows and are not approved for production implementation.

Every analyzer row keeps:

- `app_ready=no`
- `production_score_created=no`
- `probabilities_created=no`

## 1.03 Handling

GREEN.

Analyzer rows with `pick_zone=1.03`: `0`.

Draft-day simulation creates exactly one `1.03` context row:

- `player=NO_PLAYER_CLEARED`
- `simulation_action=trade_down_or_manual_review`
- `fit_signal=trade_down_or_manual_review_only_no_player_cleared`

No player is forced into `1.03`.

## 1.04 Warning Visibility

GREEN.

The premium analyzer context remains warning-visible:

- `1.04` analyzer rows: `10`
- `rankable_with_warning`: `7`
- `manual_review_required`: `2`
- `unavailable`: `1`
- clean `ready`: `0`

Premium warning rows preserve `warnings`, `blockers`, `remaining_gaps`, `draft_only_if`, `do_not_draft_if`, and emergency-stop context.

## Round 2 / 5.04 Sanity

GREEN.

Round 2 context:

- analyzer Round 2 rows: `9`
- simulation rows at `2.04`: `10`
- simulation rows at `2.08`: `12`

Round 2 remains manual review and warning-visible. It does not create production values.

5.04 context:

- analyzer `5.04` rows: `144`
- simulation rows at `5.04`: `45`

The analyzer keeps late profiles as asymmetric darts, role-path reviews, manual holds, unavailable rows, or blocked rows. Generic low-evidence rows are not promoted to clean ready.

## Manual Flags Visibility

GREEN.

Manual flags remain visible in:

- analyzer `warnings`;
- analyzer `blockers`;
- analyzer `remaining_gaps`;
- `draft_only_if`;
- `do_not_draft_if`;
- `emergency_stop_signal`;
- simulation rows;
- pick-card summaries.

The Stage 5 plan explicitly recommends prioritization before any warning reduction. It does not remove warnings.

## Implementation Safety

GREEN.

Confirmed:

- no production ranking files changed;
- no private-score files changed;
- no formula files changed;
- no Streamlit/app files changed;
- no probabilities created;
- no bands created;
- no outcome files changed;
- no veteran outcome-head files changed;
- no app-readable artifact created;
- no production score created;
- `data/` remains untracked and uncommitted;
- `local_exports/` remains uncommitted.

The analyzer queue touched only rookie framework docs, rookie framework scripts, and tests.

## Local Export Audit

Analyzer local export:

- rows: `211`
- `app_ready`: only `no`
- `production_score_created`: only `no`
- `probabilities_created`: only `no`

Draft-day simulation local export:

- rows: `77`
- pick cards: `5`
- `simulation_only`: only `yes`
- `app_ready`: only `no`
- `production_score_created`: only `no`
- `probabilities_created`: only `no`

Generated local exports are not committed.

## Stage 9 Gate

Stage 9 is GREEN.

Stage 10 may proceed to final checkpoint if validation remains GREEN.
