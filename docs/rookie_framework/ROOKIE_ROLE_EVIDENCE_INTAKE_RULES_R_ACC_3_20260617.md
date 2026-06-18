# Rookie Role Evidence Intake Rules R-ACC-3

Date: 2026-06-17

Status: Manual-use role/depth-chart evidence intake rules for Tier 1 plus Antonio Williams.

## Purpose

R-ACC-3 creates a safe way for Tim to fill the remaining early-pick role/depth-chart trust gap without changing the frozen formula, board order, private score, production rankings, app artifacts, Outcome files, veteran files, probabilities, bands, hidden sort keys, or promoted artifacts.

The current formula remains `cfbd_enriched_baseline_v1_1`. Board order remains frozen. This is not production/app approval.

## Review Group

- Jeremiyah Love
- Makai Lemon
- Carnell Tate
- KC Concepcion
- Jadarian Price
- Denzel Boston
- Germie Bernard
- Chris Bell
- Zachariah Branch
- Antonio Williams

## Evidence Needed

For WRs, role evidence should answer:

- Is there a credible early target-earning path?
- Is the player expected to run real routes early, not just gadget or depth snaps?
- What target competition blocks or supports the path?
- Is there separation, route, press, or target-quality context that supports first-down scoring?
- Is the player healthy and available?

For RBs, role evidence should answer:

- Is there a credible early-down role?
- Is there a goal-line or short-yardage path?
- Is there receiving usage that matters for first downs, not empty PPR volume?
- Is pass-protection trust likely to support early snaps?
- What incumbent competition blocks or supports the path?
- Is the player healthy and available?

## Acceptable Sources

Acceptable sources for manual display evidence:

- Official team roster, transaction, injury, or depth-chart page.
- Team-published coach quote or press conference transcript.
- Clearly sourced beat report with date and outlet.
- Team depth-chart blurb when the source is identifiable and dated.
- Injury report, practice participation report, or reliable availability note.
- Tim local notes, if the note includes source/date/context.
- Existing local source-safe Rookie artifacts in this repo.

## Not Acceptable Sources

Do not use these as role facts or private/model inputs:

- ADP.
- Public rankings.
- Projections.
- Trade calculators.
- Market values.
- Unsourced social posts.
- Message-board rumors.
- Guesses from draft capital alone.
- Any source that would require inventing a role/depth-chart fact.

ADP/market may remain display-only for draft-room price and availability pressure. It must not become NWR private value.

## What Can Be Filled Manually

Tim may fill:

- `role_summary_to_enter`
- `role_confidence_low_medium_high`
- `injury_or_availability_note`
- `competition_for_touches_or_targets`
- `projected_path_to_early_usage`
- `first_down_scoring_fit_note`
- `non_ppr_fit_note`
- `Tim_notes`
- `fill_status`

Unknown values should remain blank or `needs_tim_input`.

## Evidence Confidence

Use low, medium, or high:

- High: official/team-confirmed role, clear coach quote, or multiple source-safe reports saying the same thing.
- Medium: one reliable dated source or local note with enough context to guide manual review.
- Low: partial evidence, unclear role, conflicting reports, or evidence that supports only a narrow package.

Low confidence should not clear a player for 1.03 / 1.04 by itself.

## Source-Type Handling

Official team pages:

- Accept for roster, transactions, injury status, and listed depth-chart context.
- Still review whether the listed role translates to fantasy first-down usage.

Team depth-chart blurbs:

- Accept when dated and source-identifiable.
- Mark confidence based on specificity and whether it distinguishes starter, rotation, package, or depth role.

Coach quotes:

- Accept if direct, dated, and tied to usage, health, competition, or role.
- Avoid overreading vague praise.

Beat reports:

- Accept when reporter/outlet/date are captured.
- Prefer reports based on practice participation, reps, personnel usage, or direct team observation.

Injury reports:

- Accept as availability context.
- Do not convert injury context into a model score.

Tim/local notes:

- Accept as manual review evidence if source/date/context are included.
- Keep them manual-use only.

## Preservation Rules

R-ACC-3 evidence may improve display/manual trust only. It cannot:

- Change `cfbd_enriched_baseline_v1_1`.
- Change frozen board order.
- Change private/model score.
- Create probabilities.
- Create new bands.
- Create hidden sort keys.
- Promote artifacts.
- Wire anything into production/app views.

## Returning Filled Evidence

Use:

- `local_exports/rookie_framework/r_acc_3_role_evidence_intake_20260617/rookie_role_depth_chart_evidence_intake_template_20260617.csv`
- `local_exports/rookie_framework/r_acc_3_role_evidence_intake_20260617/rookie_103_104_evidence_trigger_sheet_20260617.csv`

Tim should fill only source-backed fields, leave unknowns blank or `needs_tim_input`, and preserve player/rank/tier fields. A later sprint may ingest the filled file as display/manual evidence only after another guardrail check.

## Manual-Use Warning

This intake is a local/manual-use draft-room aid. It is not production/app approved and must not be treated as a replacement ranking, probability file, score file, or app-ready artifact.

## R-ACC-3 Result

R-ACC-3 creates a safe path to collect the missing role evidence without guessing. If the evidence is not available, the correct action is to leave the field as `needs_tim_input` and keep the player verify-first or hold according to the existing manual review packet.
