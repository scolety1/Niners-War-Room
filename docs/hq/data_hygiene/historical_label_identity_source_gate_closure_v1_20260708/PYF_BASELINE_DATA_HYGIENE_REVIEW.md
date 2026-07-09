# PYF Baseline Data Hygiene Review

## Decision

PYF is safe as the mandatory review-only anchor comparator for future component signal tests.

PYF is not a production formula, source-truth field, ranking change, or model-use promotion.

## Evidence

The partial historical replay benchmark used `prior_nwr_points` and `prior_nwr_ppg` as safe prior-year baselines across:

- Seasons: `2013-2025`
- Rows: `5,518`
- Positions: QB, RB, WR, TE
- QB rows: `754`
- RB rows: `1,429`
- WR rows: `2,124`
- TE rows: `1,211`

## Baseline Results

| Position | PYF Spearman | Best Non-PYF Signal | Best Non-PYF Spearman | Non-PYF Beat PYF? |
| --- | ---: | --- | ---: | --- |
| QB | `0.712` | `prior_passing_yards` | `0.683` | No |
| RB | `0.633` | `prior_rushing_yards` | `0.628` | No |
| WR | `0.691` | `prior_receiving_yards` | `0.683` | No |
| TE | `0.701` | `prior_receiving_yards` | `0.691` | No |

## Required Use

Any future Formula Gauntlet candidate must compare to PYF:

- overall
- by position
- on sparse-history slices
- on low-games slices
- on prior-production decline false positives

## Blocked Uses

PYF cannot be used to:

- claim production accuracy
- activate a formula
- replace rankings
- become a hidden sort
- promote source truth
- skip sparse-history checks
- justify a candidate that fails position-level tests
