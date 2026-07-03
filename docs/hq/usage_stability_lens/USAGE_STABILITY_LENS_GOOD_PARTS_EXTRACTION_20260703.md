# Usage/Stability Lens Good Parts Extraction

This document preserves the reusable parts of the held Usage/Stability Lens work without promoting the candidate.

## What Survived

- NFLVerse usage/opportunity data pipeline.
- Safe review-only evidence handling.
- Null-fencing and `Not enough information` semantics.
- Warmer/colder movement labels that respect inverted rank numbers.
- Static human-review packet generation pattern.
- Cornerstone warning flags.
- Injury/timeline discount watchlist concept.
- Role-up context watchlist concept.
- Candidate guardrail/testing infrastructure.
- No-promotion validation checks.

## What Did Not Survive

- Ranking replacement.
- Main formula promotion.
- Hidden ranking variant.
- App/rank/source-truth wiring.
- Broad tuning loop.
- Market-mirroring behavior.

## How This Can Help Later

The useful parts can support future review-only work as:

- side context for human review;
- candidate diagnostics;
- model QA and failure-mode discovery;
- a source of safe factual usage evidence after separate approval gates;
- a way to identify players needing human review.

The surviving pieces are evidence and workflow patterns, not production logic.

## Non-Promotion Statement

Nothing in this extraction approves rank behavior changes, model input use, source truth, app wiring, hidden sort, recommendations, trade value, pick value, or draft advice.
