# Kick Return Export Validation - 2026-05-17

This report validates manually collected kick-return CSV exports before Model v4 uses them.

## Model Context

The locked LVE rules include return scoring: return yards are worth 1 point per 30 yards and return TDs are worth 4 points. Current code does not yet include return scoring in `src/config/lve_scoring.py`, so this data should remain staged until the scoring contract and recompute services are patched and tested.

Kick-return evidence should be a small direct scoring component and role/context signal. It should not become a large dynasty talent signal.

## Summary

| Season | Clean Rows | KR Yards | KR TD | LVE Points If Used | Status | Warnings |
|---:|---:|---:|---:|---:|---|---|
| 2024 | 100 | 22514 | 7 | 778.47 | usable_after_cleanup | none |
| 2025 | 125 | 48392 | 6 | 1637.07 | usable_after_header_inference | shifted_header_expected_player_header_inferred |

## Findings

- Raw exports were preserved under `local_exports/model_v4/raw_user_exports/rotowire_manual/<season>/returns/`.
- `Kick Return - 2024.csv` has a valid header and no duplicate/conflicting rows.
- `Kick Return - 2025.csv` has a shifted header: the `Player` header is missing and the final header cell is `0`. The expected header can be inferred safely during intake.
- No exact duplicate rows, conflicting duplicate player rows, malformed rows, or numeric issues were found in either file.
- Team/position columns are absent, so identity joins must use normalized player names and should flag ambiguous names.

## 2024 Kick Returns

- Exact header: `True`
- Shifted header: `False`
- Exact duplicate rows removed: `0`
- Duplicate player rows with different stats: `0`
- Numeric issues: `0`

Top rows by kick-return yards after cleanup:

| Player | Returns | Yards | Avg | TD | Fumbles |
|---|---:|---:|---:|---:|---:|
| KaVontae Turpin | 27 | 904 | 33.5 | 1 | 0 |
| Raheem Blackshear | 31 | 791 | 25.5 | 0 | 1 |
| Austin Ekeler | 19 | 594 | 31.3 | 0 | 1 |
| Eric Gray | 21 | 554 | 26.4 | 0 | 2 |
| Deebo Samuel Sr. | 17 | 533 | 31.4 | 0 | 2 |
| Keisean Nixon | 18 | 528 | 29.3 | 0 | 0 |
| Derius Davis | 19 | 524 | 27.6 | 0 | 1 |
| Xavier Gipson | 17 | 489 | 28.8 | 0 | 0 |
| DeAndre Carter | 15 | 479 | 31.9 | 0 | 0 |
| DeeJay Dallas | 15 | 459 | 30.6 | 1 | 1 |
| Laviska Shenault Jr. | 16 | 459 | 28.7 | 1 | 2 |
| Kenneth Gainwell | 18 | 456 | 25.3 | 0 | 0 |

## 2025 Kick Returns

- Exact header: `False`
- Shifted header: `True`
- Exact duplicate rows removed: `0`
- Duplicate player rows with different stats: `0`
- Numeric issues: `0`

Top rows by kick-return yards after cleanup:

| Player | Returns | Yards | Avg | TD | Fumbles |
|---|---:|---:|---:|---:|---:|
| KaVontae Turpin | 69 | 1814 | 26.3 | 0 | 0 |
| Chimere Dike | 62 | 1588 | 25.6 | 0 | 1 |
| Myles Price | 57 | 1479 | 26 | 0 | 2 |
| Charlie Jones | 42 | 1084 | 25.8 | 1 | 0 |
| Devin Duvernay | 40 | 1069 | 26.7 | 0 | 0 |
| Malik Washington | 36 | 965 | 26.8 | 0 | 0 |
| Ray Davis | 31 | 943 | 30.4 | 1 | 0 |
| Skyy Moore | 33 | 907 | 27.5 | 0 | 0 |
| Jacob Saylors | 33 | 897 | 27.2 | 0 | 0 |
| Dylan Laube | 33 | 855 | 25.9 | 0 | 1 |
| Isaiah Williams | 28 | 837 | 29.9 | 0 | 1 |
| Greg Dortch | 31 | 811 | 26.2 | 0 | 1 |
