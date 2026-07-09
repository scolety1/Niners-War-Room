# Formula Gauntlet Revival Lane Charter

## Purpose

Prepare a safe review-only lane where future Formula Gauntlet research can happen after data readiness improves.

Future Formula Gauntlet work may:

- Generate and test unique formula candidates.
- Compare formula candidates against strong baselines.
- Compare candidates against prior-year finish and current-formula-family proxy baselines.
- Perform failure autopsy before any future promotion discussion.
- Preserve source-trace-first and receipt-first rules.
- Keep every candidate review-only unless separately approved.

## Scope For This Setup Lane

Allowed:

- Create documentation.
- Define future guardrails.
- Define future evidence structure.
- Define future data readiness prerequisites.
- Define candidate metric backlog categories without approving them.

Not allowed:

- Run candidate generation.
- Run challenger tournaments.
- Run broad formula search.
- Tune weights.
- Upgrade formulas.
- Change rankings.
- Promote metrics.
- Promote sources.
- Create active formulas.
- Write production artifacts.

## Operating Principles

1. Every future Formula Gauntlet run must begin from a declared HQ base commit.
2. Every future candidate must have a source trace, feature receipt map, and decision-date safety statement.
3. Every future candidate must be compared against a baseline ladder, not judged by isolated metrics.
4. Every future candidate must include failure review before any promotion conversation.
5. Every future candidate must remain review-only until a separate human-approved production lane exists.

## Future Candidate Eligibility

A future candidate is eligible for review only if:

- All input fields have source status documented.
- Source-gate status allows review use.
- Player identity joins are stable and audited.
- Missingness policy is explicit.
- Train, validation, and holdout splits are leakage-safe.
- Output artifacts are written only to review paths.
- Candidate outputs cannot affect app behavior, rankings, hidden sort, recommendations, trades, or draft logic.

## Non-Promotion Statement

This lane creates no active formula. It makes no production claim. It does not alter `nwr_dynasty_score`, `checkpoint_review_score`, current board output, rankings defaults, or any app/runtime behavior.
