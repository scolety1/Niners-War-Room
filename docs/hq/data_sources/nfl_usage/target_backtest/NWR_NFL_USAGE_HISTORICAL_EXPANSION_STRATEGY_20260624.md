# NFL Usage Historical Expansion Strategy V0

Previous limitation: the first target/backtest run used historical panels built for feature seasons 2022 and 2023, which produced only target seasons 2023 and 2024.

Safe older source families: `player_stats`, `pbp`, and `snap_counts` can be pulled farther back through nflreadpy and cached outside git.

Core factual fields: targets, carries, receptions, touches, opportunities, rushing/receiving yards, air yards, YAC, rushing/receiving first downs, and red-zone/inside-10/inside-5 derived counts.

Snap fields: offense snaps and offense percent are retained with a YELLOW identity-join caveat because snap counts join through normalized name/team/position/week.

Advanced fields: NGS, participation/personnel/formation, route proxies, FTN/PFR fields, and true route/TPRR/YPRR gaps are not forced into older-season diagnostics.

Expanded feature seasons attempted: 2018;2019;2020;2021;2022;2023.
Expanded target seasons attempted: 2019;2020;2021;2022;2023;2024.

Minimum threshold: at least four leakage-safe feature seasons are required before any field may become a model-candidate pending manual review. No field becomes active model input here.

Fallback: if older coverage is incomplete, reports must mark `BACKTEST_STILL_LIMITED_HISTORICAL_WINDOW` or field-level caveats rather than faking improvement.

Boundaries: no CFBD, no market/ADP/projection/rank targets, no app wiring, no model input, and no raw payloads tracked.
