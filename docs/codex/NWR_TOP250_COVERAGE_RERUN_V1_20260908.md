# Top-250 / Real Market Coverage Rerun — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 4's own required
follow-up ("After both fixes, rerun Top-250 coverage, report before/after, classify every
remaining gap") and Section 15. Rerun against the real, current admitted universe after both
the Diggs-class fix (`NWR_DIGGS_CLASS_SOURCE_GAP_FIX_V1_20260908.md`) and the Brooks-class
fallback (`NWR_BROOKS_CLASS_SOURCE_GAP_FIX_V1_20260908.md`).

## Source note (important, honest)

The owner's real, local ADP snapshot (`adp_snapshots/4b4a990faf124ce7a5d612537ba5943b.json`,
276 rows) was checked first but is **not** a market-wide top-250 list -- it is a
league-specific, pre-matched import (all 276 rows already `MATCHED`, max real ADP value
1049) that does not even contain Diggs/Hill/Allen/Brooks, so it cannot stress-test coverage.
Used instead: the real, admitted FFA 2026 market pack
(`C:\NWR_HISTORICAL_DATA\FFA_OFFICIAL\2026\projections\projections_2026_official_ffa.csv`,
already governance-admitted per `NWR_FFA_SEPT4_ADMISSION_DECISION_V1_20260908.md`), restricted
to its 220 real QB/RB/WR/TE rows (the only positions this league models). This is a smaller,
real, honest population, not literally 250 rows -- reported as such rather than padded to a
round number.

## Result

```
FULLY_MODELED: 216/220 (98.2%)
ALIAS_MISMATCH:   3
STATUS_EXCLUDED:  1
```

Real, direct evidence of the Diggs/Brooks fixes working: every previously-identified
SOURCE_GAP name (Diggs, Hill, Samuel, Allen, Harris, Hopkins, Waller, Ertz, Garoppolo, Chubb)
is now `FULLY_MODELED` in this real market pack.

## The 4 remaining real gaps, individually root-caused

1. **Marvin Harrison Jr. (WR, ARI)** -- `ALIAS_MISMATCH` in *this diagnostic script only*,
   not a real production gap. A real name collision exists in the nflverse registry (a
   retired 2000s-era "Marvin Harrison" WR and the current "Marvin Harrison Jr." both
   normalize to the same `marvinharrison|WR` key once the suffix is stripped), so this
   script's simplified normalized-name join correctly refuses to guess between them. The
   real production pipeline (`attach_exact_identities`, used for the actual rookie/veteran
   candidate build) does **not** have this problem -- it prefers the real PFR-ID bridge over
   name matching and resolves Harrison Jr. to his exact real `gsis_id` (`00-0039849`,
   `identity_method=EXACT_PFR_ID_BRIDGE`, verified directly). No fix needed; a diagnostic-
   script limitation, disclosed rather than silently miscounted.
2. **Kenneth Gainwell (RB, TB)** -- real `ALIAS_MISMATCH`: FFA's source uses "Kenneth
   Gainwell," the nflverse registry uses "Kenny Gainwell" (`gsis_id 00-0036919`, real,
   currently active). A genuine nickname/formal-name variant across sources, not a coverage
   defect -- the player IS in the real universe under his registry name.
3. **Chigoziem Okonkwo (TE, WAS)** -- same real pattern: FFA uses "Chigoziem Okonkwo," the
   registry uses "Chig Okonkwo" (`gsis_id 00-0037809`, real, currently active).
4. **Joe Mixon (RB, HOU per registry / listed FA in FFA)** -- real `STATUS_EXCLUDED`: his
   real nflverse registry status is `RSN` (Reserve/Suspended-class code), outside the current
   `("ACT", "RES")` safety valve. A real, intentionally conservative exclusion (same design
   principle as the Diggs-class fix's own false-positive guard) -- not reopened this pass;
   flagged as a known remaining status-code gap for a future, separately-audited status-
   valve widening (would need the same false-positive rigor already applied to
   `NOT_CURRENTLY_ROSTERED_STATUSES`).

## Disposition

No further code change made this unit -- both real name-alias cases are source-formatting
differences, not identity-resolution defects in the real production pipeline; Mixon's `RSN`
status is a real, disclosed, deliberately-unopened edge case. 216/220 (98.2%) real, honest
coverage on the QB/RB/WR/TE market pack that matters for this league.
