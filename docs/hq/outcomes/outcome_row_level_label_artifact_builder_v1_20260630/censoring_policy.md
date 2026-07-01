# Censoring Policy

## Required rule

Missing or incomplete labels are not failures, misses, zeros, or low probabilities.

They must be represented as:

- `Not enough information`
- `censored`
- `not_applicable`
- an equivalent explicit non-observed status from an approved source

## Window semantics

Outcome V2 horizon labels must preserve their existing definitions:

| Window | Meaning |
| --- | --- |
| `this_year` | Outcome in anchor season A+1. |
| `next_year` | Outcome in anchor season A+2. |
| `within_5y` | Outcome hit at least once from A+1 through A+5. |

If the complete forward window is not observed, the row must remain censored. A censored row must not be converted to an observed miss.

## Hit status

Allowed row-level hit states for a future artifact:

- `observed_hit`
- `observed_miss`
- `not_applicable`
- `censored`
- `missing_target_data`
- `Not enough information`

`false`, `0`, or `0%` may appear only when an approved row-level source explicitly says an observed row is a miss. They cannot be used for missing, censored, unavailable, or unmatched data.

## Current packet decision

No censoring statuses were generated in this packet because no tracked approved row-level Outcome label source was available.
