# Punt Return Export Validation - 2026-05-17

This report validates manually collected punt-return CSV exports before Model v4 uses them.

## Model Context

The locked LVE rules include return scoring: return yards are worth 1 point per 30 yards and return TDs are worth 4 points. Current code does not yet include return scoring in `src/config/lve_scoring.py`, so punt-return data should remain staged until return scoring is patched and tested.

Punt-return evidence should be a small direct scoring component and role/context signal. It should not become a large dynasty talent signal.

## Summary

| Season | Clean Rows | PR Yards | PR TD | LVE Points If Used | Status | Warnings |
|---:|---:|---:|---:|---:|---|---|
| 2024 | 75 | 8600 | 6 | 310.67 | needs_review | repeated_header_lines=1 |
| 2025 | 75 | 8453 | 15 | 341.77 | usable_after_cleanup | none |

## Findings

- Raw exports were preserved under `local_exports/model_v4/raw_user_exports/rotowire_manual/<season>/returns/`.
- Both files have valid headers and no duplicate/conflicting rows.
- No malformed rows or numeric issues were found.
- Team/position columns are absent, so identity joins must use normalized player names and should flag ambiguous names.

## 2024 Punt Returns

- Exact header: `True`
- Exact duplicate rows removed: `0`
- Duplicate player rows with different stats: `0`
- Numeric issues: `0`

Top rows by punt-return yards after cleanup:

| Player | Returns | Yards | Avg | TD | Fair Catches | Fumbles |
|---|---:|---:|---:|---:|---:|---:|
| Kalif Raymond | 30 | 413 | 13.8 | 1 | 9 | 0 |
| Marvin Mims Jr. | 26 | 408 | 15.7 | 0 | 25 | 0 |
| Marcus Jones | 26 | 386 | 14.8 | 0 | 8 | 2 |
| Brandon Codrington | 27 | 313 | 11.6 | 0 | 8 | 1 |
| Jaelon Darden | 32 | 309 | 9.7 | 0 | 12 | 0 |
| Calvin Austin III | 28 | 289 | 10.3 | 1 | 15 | 1 |
| Xavier Gipson | 33 | 266 | 8.1 | 0 | 16 | 4 |
| Jacob Cowing | 28 | 245 | 8.8 | 0 | 11 | 2 |
| Derius Davis | 19 | 235 | 12.4 | 0 | 22 | 2 |
| Ihmir Smith-Marsette | 29 | 228 | 7.9 | 0 | 17 | 1 |
| Jha'Quan Jackson | 28 | 215 | 7.7 | 0 | 7 | 3 |
| Cooper DeJean | 21 | 211 | 10 | 0 | 21 | 2 |

## 2025 Punt Returns

- Exact header: `True`
- Exact duplicate rows removed: `0`
- Duplicate player rows with different stats: `0`
- Numeric issues: `0`

Top rows by punt-return yards after cleanup:

| Player | Returns | Yards | Avg | TD | Fair Catches | Fumbles |
|---|---:|---:|---:|---:|---:|---:|
| Marvin Mims Jr. | 29 | 452 | 15.6 | 1 | 21 | 1 |
| Chimere Dike | 23 | 398 | 17.3 | 2 | 25 | 1 |
| Isaiah Williams | 28 | 396 | 14.1 | 2 | 12 | 0 |
| Marcus Jones | 21 | 363 | 17.3 | 2 | 18 | 2 |
| Parker Washington | 25 | 341 | 13.6 | 2 | 13 | 2 |
| Rashid Shaheed | 23 | 339 | 14.7 | 1 | 27 | 0 |
| Jaylin Noel | 31 | 335 | 10.8 | 0 | 19 | 0 |
| Jaylin Lane | 23 | 314 | 13.6 | 2 | 9 | 2 |
| Myles Price | 30 | 298 | 9.9 | 0 | 12 | 2 |
| Skyy Moore | 25 | 291 | 11.6 | 0 | 7 | 1 |
| Kameron Johnson | 26 | 291 | 11.2 | 0 | 15 | 2 |
| Malik Washington | 20 | 260 | 13 | 1 | 11 | 0 |
