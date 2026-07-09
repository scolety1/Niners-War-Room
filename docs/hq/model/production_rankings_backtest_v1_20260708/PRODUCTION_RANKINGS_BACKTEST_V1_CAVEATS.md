# Production Rankings Backtest V1 Caveats

## Exact Replay Blocker

Exact historical replay is blocked because the current `nwr_dynasty_score` artifact is produced from current Model v4 evidence/checkpoint layers, not from committed season-by-season historical formula inputs. The current app validates a pinned full-board CSV hash and displays the result; it does not recompute historical rankings on demand.

## Proxy Boundary

The benchmark proxy reuses current formula families and weights where local V3 lagged factual columns overlap. Missing current-only components are penalized and disclosed. This is not a promoted model and not a production approval.

## Coverage Caveats

- Current board rows read: `240`.
- Current scored rows read: `232`.
- V3 substrate rows tested: `5518`.
- Feature seasons: `2012-2024`.
- Target seasons: `2013-2025`.
- Rookie/veteran split is not safely available from the V3 substrate. Current-board `is_rookie` is current-only and was not used historically.
- Injury-affected miss slices are review-only only. No injury field was admitted as a historical proxy input in this benchmark.
- K is excluded because the current value chain and the scoring contract mark kicker as not meaningfully modeled.

## Leakage Guardrails

- No target-season outcome was used to score proxy ranks.
- No 2026-only roster, status, injury, depth chart, ADP, market, or projection field was used as historical input.
- Display-only Outcome V1/V2 fields were not used as model inputs.
- DynastyProcess/market fields were not used as model inputs.

## Season/Position Coverage Snapshot

| Target Season | Position | Rows | Optional Null-Fenced Rows | Median Proxy Component Weight | Missing Component Rows | Actual Startable Rows In Coverage |
| --- | --- | --- | --- | --- | --- | --- |
| 2013 | QB | 52 | 52 | 0.950 | 52 | 10 |
| 2013 | RB | 105 | 105 | 1.000 | 41 | 30 |
| 2013 | TE | 86 | 86 | 0.950 | 86 | 12 |
| 2013 | WR | 153 | 153 | 1.000 | 1 | 40 |
| 2014 | QB | 57 | 9 | 0.950 | 57 | 10 |
| 2014 | RB | 100 | 51 | 1.000 | 37 | 30 |
| 2014 | TE | 86 | 9 | 0.950 | 86 | 12 |
| 2014 | WR | 148 | 21 | 1.000 | 0 | 40 |
| 2015 | QB | 60 | 13 | 0.950 | 60 | 10 |
| 2015 | RB | 108 | 55 | 1.000 | 45 | 30 |
| 2015 | TE | 93 | 14 | 0.950 | 93 | 12 |
| 2015 | WR | 150 | 25 | 1.000 | 1 | 40 |
| 2016 | QB | 53 | 8 | 0.950 | 53 | 10 |
| 2016 | RB | 116 | 50 | 1.000 | 38 | 30 |
| 2016 | TE | 85 | 18 | 0.950 | 85 | 12 |
| 2016 | WR | 148 | 17 | 1.000 | 0 | 40 |
| 2017 | QB | 57 | 9 | 0.950 | 57 | 10 |
| 2017 | RB | 108 | 43 | 1.000 | 33 | 30 |
| 2017 | TE | 92 | 12 | 0.950 | 92 | 12 |
| 2017 | WR | 152 | 13 | 1.000 | 2 | 40 |
