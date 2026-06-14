# Rookie Production Candidate Status Semantics Patch - 2026-06-13

## Purpose

This patch adds `rankable_with_warning` to the rookie production-candidate export semantics.

It remains candidate/export-only. It does not implement production promotion, replace production rankings, change private scores, modify formulas, wire app/Streamlit output, create probabilities, create bands, create outcome columns, or use veteran outcome heads.

## Why `ready` Remains Strict

`ready` continues to mean a clean candidate row:

- no material manual warnings;
- no remaining gaps;
- no quarantined prohibited source terms;
- no low source confidence;
- no hard caps;
- no source conflicts;
- no app-read or probability implications.

This prevents warning-heavy players from being misread as production-clean.

## Why `rankable_with_warning` Is Needed

The prior candidate export had `0` `ready` rows because nearly every useful rookie row still had at least one warning, gap, soft flag, source caveat, or manual-review note.

That was safe, but too coarse. A production-candidate order may need to rank players while still showing warnings beside the row. `rankable_with_warning` creates that middle state:

- the row may be ordered in a candidate export;
- warning context must remain visible;
- the row is not production-clean;
- the row does not approve app display or production promotion.

## Status Semantics

- `ready`: clean enough for production-candidate use with no material warnings.
- `rankable_with_warning`: can be ordered in a production-candidate export while displaying warnings/manual-review context.
- `manual_review_required`: needs a human decision before production ranking movement.
- `blocked`: has a true blocker such as a hard cap, source conflict, or capped status.
- `unavailable`: lacks source-safe evidence or needs data/roster-declaration context.

## Warnings That Must Remain Visible

Rows with `rankable_with_warning` or `manual_review_required` must preserve:

- manual-review flags;
- soft flags;
- remaining gaps;
- low source confidence;
- quarantined prohibited source terms;
- injury/manual-review notes;
- source-safety notes;
- `why_ranked_here`;
- `why_not_higher`;
- `why_not_lower`.

Warnings must not disappear to make a row look clean.

## What This Does Not Approve

This patch does not approve:

- production ranking replacement;
- app or Streamlit wiring;
- private-score changes;
- formula changes;
- rookie probabilities;
- rookie probability bands;
- outcome-column files;
- veteran outcome heads;
- `data/` commits;
- `local_exports/` commits.

## Source-Safety Preservation

- Secondary charting remains soft-flag context.
- Scouting prose remains manual-review context.
- Market, rank, projection, ADP, consensus, trade, and draft-kit terms remain quarantined or excluded.
- `1.03` remains empty when unsupported.
- `1.04` warnings remain visible and are not auto-cleared.

## Next Gate

The next safe task is an audit of the new status semantics and regenerated candidate exports.

Do not implement production promotion from this patch.
