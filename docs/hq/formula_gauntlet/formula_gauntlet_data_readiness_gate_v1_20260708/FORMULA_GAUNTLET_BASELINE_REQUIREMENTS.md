# Formula Gauntlet Baseline Requirements

## Decision

PYF must remain the required champion baseline for any future Formula Gauntlet work.

PYF means prior-year finish or prior-year NWR fantasy points/rank, depending on the exact benchmark contract. In the accepted partial replay benchmark, `prior_nwr_points` was the strongest available PYF-style baseline and the best non-PYF component signal did not beat it in any position.

## Minimum Baseline Ladder

Every future candidate must be compared against:

1. PYF / prior-year NWR points.
2. Prior-year NWR PPG.
3. Position-specific PYF baseline.
4. Startable precision baseline for the NWR league format.
5. Sparse-history / low-games baseline.
6. Prior-production-decline false-positive baseline.
7. Current-formula-family proxy only when the evidence says the comparison is safe and comparable.

## Required Passing Standard

A candidate cannot advance beyond review-only evidence unless it:

- Beats PYF overall.
- Beats PYF by position for the relevant position scope.
- Does not increase sparse-history harm.
- Does not increase prior-production-decline false positives.
- Passes leakage checks.
- Uses only source-gated, decision-date-safe inputs.
- Has source receipts and reproducibility evidence.

## Current Evidence

| Position | Best Non-PYF Signal | Spearman | PYF Baseline | Beat PYF? |
| --- | --- | ---: | ---: | --- |
| QB | `prior_passing_yards` | `0.683` | `0.712` | No |
| RB | `prior_rushing_yards` | `0.628` | `0.633` | No |
| WR | `prior_receiving_yards` | `0.683` | `0.691` | No |
| TE | `prior_receiving_yards` | `0.691` | `0.701` | No |

## Guardrail

Candidates that fail PYF may still be stored as review-only evidence, but they must not be treated as formula improvements and must not be promoted.
