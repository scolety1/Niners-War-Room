# Protected and Frozen Path Proof

Baseline: `e949c5647001f84dba29195c589e27d923722ea1`.

## Exact blob comparisons

- Decision Trust Strip component: `7319308a4342396a6dcf26514b86697310adec96` baseline/current.
- Decision Trust Strip service: `8672811336a9614f3e3c9dcdedfdf1c642f3a9ef` baseline/current.
- Player Compare decision service: `d5e3a6da6bfbd63d3574f2225fd91ce19db0241b` baseline/current.
- Player comparison service: `c65ff9dbc3ebacdfcba6589912d246a176ec6fab` baseline/current.
- Navigation: `603b3b0aef55806577ec6256beae592d894f43d3` baseline/current.
- Trading Lab page: `8d242439a21c08069015c1e7340be9883c85c8a7` baseline/current.

## Diff scans

- Frozen/prospective-2026/data path scan: no changed path.
- Trading Lab scan: no changed path.
- Ranking/formula scan: no changed path.
- Source registry/admission scan: no changed path.
- Plugin scan: no changed path.
- Rookie registry/queue scan: no changed path.
- Draft page/service scan: no changed path.
- Data Health and roster scan: no changed path.
- Production data scan: no changed path.

## Allowed paths only

The lane diff contains only `app/pages/22_player_compare_v1.py`, `app/components/player_compare_accessibility.py`, `tests/test_player_compare_accessibility_compact.py`, `tests/fixtures/player_compare_accessibility_fixture.py`, and `docs/hq/master/player_compare_accessibility_compact_width_hardening_v1_20260712/`.

No generated data pack, SQLite file, shared-data path, frozen artifact, or protected production system was written.
