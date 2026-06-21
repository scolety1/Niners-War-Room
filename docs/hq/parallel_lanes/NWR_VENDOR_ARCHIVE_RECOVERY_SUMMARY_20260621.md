# NWR Vendor Archive Recovery Summary - 2026-06-21

Owner: Master/Main HQ

Status: GREEN for local-only archive preservation and header-level audit.
YELLOW for any future use because source/license review is required. This
document does not approve model use, private value, hidden ranking/sort,
recommendations, simulations, final draft decisions, Mock Draft logic,
deployment, `latest_candidate`, or `latest_approved`.

## Local-Only Archive

Archive root:

`C:\NWR_SHARED_DATA\vendor_archive_recovery\rotowire_fantasypros_advanced_20260621`

Corrected organized archive root:

`C:\NWR_SHARED_DATA\vendor_archive_recovery\rotowire_fantasypros_stats_organized_20260621_v2`

Local-only outputs:

- `ARCHIVE_MANIFEST.csv`
- `FILE_INVENTORY.md`
- `YEAR_INFERENCE_REPORT.md`
- `FIELD_COVERAGE_COMPARISON.md`
- `VENDOR_ARCHIVE_RECOVERY_RECOMMENDATION.md`
- `source_copies\`
- Organized archive: `00_manifests\`, `01_originals\`, `02_canonical\`,
  `03_reports\`, `04_quarantine\`, and `05_adjacent_inventory\`

Raw vendor CSVs remain local-only under `C:\NWR_SHARED_DATA` and are not
committed.

## File Counts

Recovered advanced-stat CSV candidates:

| Source | Group | Files |
| --- | --- | ---: |
| FantasyPros | QB advanced | 9 |
| FantasyPros | RB advanced | 10 |
| FantasyPros | WR advanced | 9 |
| FantasyPros | TE advanced | 9 |
| RotoWire | passing advanced | 4 |
| RotoWire | rushing advanced | 5 |
| RotoWire | receiving advanced | 6 |

Total copied source CSVs: 52.

Corrected organized archive source records: 100 core RotoWire/FantasyPros CSVs,
plus 35 adjacent CSV inventory records.

## Year Coverage Summary

No recovered advanced CSV had a dependable explicit season/year column. Year
coverage was inferred from content-recognizable historical leaders, suffix order,
and batch modified-time context, not from filename alone.

High-level inferred coverage:

- FantasyPros QB/WR/TE: likely 2017-2025 coverage.
- FantasyPros RB: likely 2017-2025 coverage plus one partial/unknown low-confidence file.
- RotoWire rushing/receiving: likely 2021-2025 coverage.
- RotoWire passing: likely 2021-2025 coverage across basic, advanced, fantasy,
  and red-zone exports.

Key uncertainties:

- RotoWire 2021 passing is present. RotoWire 2022 passing advanced is present
  from Downloads `rotowire-passing-advanced-stats (1).csv`.
- RotoWire 2022 passing basic, fantasy, and red-zone are present from Downloads
  `rotowire-passing-basic-stats (1).csv`,
  `rotowire-passing-fantasy-stats.csv`, and
  `rotowire-passing-redzone-stats.csv`.
- No expected RotoWire 2021-2025 passing/rushing/receiving file is currently
  missing from the organized archive matrix.
- Two RotoWire receiving files infer to 2025 but differ by hash and row scope:
  one under Duplicates Review and one under Downloads.
- FantasyPros RB base file has only three rows and should not be treated as a
  complete season export.
- FantasyPros filename suffix gaps do not by themselves prove missing seasons.
- Downloads `rotowire-passing-basic-stats.csv` and
  `rotowire-passing-advanced-stats.csv` are exact duplicates of existing
  Duplicates Review 2021 passing exports.

## Field Categories

Mostly already covered or duplicate through current nflverse/Sleeper/PFR/NGS/PBP
planning:

- Basic passing/rushing/receiving volume.
- Games, targets, receptions, carries, yards, touchdowns.
- Air yards, aDOT-style fields, YAC, drops, sacks, broken tackles, yards before
  and after contact.
- Red-zone/goal-line usage, which NWR can derive from PBP/opportunity sources.
- RotoWire IDs as a cross-check against existing ID crosswalk fields.

Potentially useful gaps or challenger fields:

- RotoWire receiving route metrics: exact routes run, targets per route run, and
  yards per route run.
- FantasyPros WR/TE catchable targets, team target share, yards-before-contact,
  and yards-after-contact splits.
- RotoWire rushing inside/outside, stuffed, broken tackle, and after-contact
  fields as RB research challengers.
- FantasyPros QB pocket/pressure context as a definition-gated cross-check.

Still missing or not solved by these files:

- True route participation percentage.
- Direct offensive line grades.
- Current/live 2026 injury and practice fields.
- Explicit missed tackles forced.
- Direct pressure/sack responsibility by blocker.

## Recommendation

Preserve the archive and consider a future local-only candidate package only
after source/license review. The best first research candidate would be a narrow
local-only RotoWire receiving route-metrics package for backtest comparison,
because current NWR coverage identifies exact routes run and direct TPRR as
remaining gaps.

All vendor fields remain display-only or backtest-research-only until a later
Tim/Master/QA-approved source policy explicitly changes that status.
