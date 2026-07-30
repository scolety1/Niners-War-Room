# CFBD College Evidence Admission V1

## Result

Admission identifier: `NWR_CFBD_COLLEGE_EVIDENCE_ADMISSION_V1`.
Foundation identifier: `NWR_NEW_EVIDENCE_FOUNDATION_V1`.
Immutable snapshot: `20260730T171639Z-370ce01696c3`.
Aggregate SHA-256: `370ce01696c305f64792e45e1f8671cfb788b8419b257040206a6f14e5c2770a`.

The admitted families are CFBD draft identity, player season statistics, player
usage, and player PPA. Raw provider bytes remain external and uncommitted.
Recruiting is not admitted because this snapshot does not provide an exact
recruit-to-NFL authority without a prohibited name join.

## Identity and evidence

The only exact bridge is the unique NFL draft `year + round + overall` shared by
CFBD and the admitted nflverse rookie foundation. CFBD `collegeAthleteId` then
joins statistics, usage, and PPA. Names and positions are diagnostics only.
Undrafted players and missing provider IDs remain explicitly unresolved.

Terminal college seasons must be strictly earlier than the NFL draft year.
Current retrieval corrections are acknowledged through
`ADMITTED_WITH_RETROSPECTIVE_REVISION_LIMIT`.
