# NWR Sleeper Status Context V1 - 20260623

## Verdict
GREEN_RUNTIME_PULL

Sleeper provides status flags, not full injury/news analysis. These fields are warning and diagnostic context only; they are not model inputs and do not change NWR rank/value.

## Warning Counts
`{'clean': 114, 'injury/status review': 16, 'missing status metadata': 8, 'team/status mismatch': 5}`

## Sample Warning Rows
| player | pos | nfl_team | warning_classification | source_note |
| --- | --- | --- | --- | --- |
| Makai Lemon | WR | PHI | injury/status review | Sleeper provides status flags, not full injury/news analysis. |
| Chris Bell | WR | MIA | injury/status review | Sleeper provides status flags, not full injury/news analysis. |
| Eric McAlister | WR | FA | injury/status review | Sleeper provides status flags, not full injury/news analysis. |
| Sieh Bangura | RB | NEEDS_DATA | missing status metadata | No Sleeper metadata match; do not infer clean health. |
| Jacob De Jesus | WR | NEEDS_DATA | team/status mismatch | Sleeper provides status flags, not full injury/news analysis. |
| Chris Olave | WR | NO | injury/status review | Sleeper provides status flags, not full injury/news analysis. |
| Devin Voisin | WR | NEEDS_DATA | missing status metadata | No Sleeper metadata match; do not infer clean health. |
| Barika Kpeenu | RB | NEEDS_DATA | missing status metadata | No Sleeper metadata match; do not infer clean health. |

## Required Missing-Data Behavior
Missing injury/status/age metadata means `Not enough information`. It does not mean clean health.
