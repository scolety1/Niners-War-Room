# RB/WR Cross-Position Balance Audit

Date: 2026-05-12

Active pack: `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`

Audit artifact: `local_exports/rb_wr_cross_position_receipt_audit.csv`

## Scope

This pass audits whether the stats-first model is overcorrecting toward running backs or wide receivers. It compares elite RBs, fragile role-driven RBs, elite WRs, young WRs, and stable veteran WRs using receipts instead of vibes.

No broad formula weights were changed.

## Current Active Balance

After the active stats-first sync and this pass, the top RB/WR board is not RB-only and not WR-only. The first ten RB/WR rows are:

1. Justin Jefferson
2. CeeDee Lamb
3. Bijan Robinson
4. Ja'Marr Chase
5. Amon-Ra St. Brown
6. Malik Nabers
7. A.J. Brown
8. Brian Thomas
9. Puka Nacua
10. Jahmyr Gibbs

That shape is directionally consistent with LVE: elite WRs matter because of 3 WR plus 2 flex, while elite young RBs still belong near the very top because no-PPR plus first-down scoring rewards real rushing/receiving work.

## Supported Bug Patch

The audit found one supported normalization bug: RB `first_down_td_fit_capped` was capped by age and injury, but not by actual role/workload access. A back with weak role security and weak workload could still carry a 100 first-down/TD fit into win-now scoring.

Patch made:

- `_rb_capped_first_down_td_fit` now caps first-down/TD fit by the minimum of:
  - age/injury dynasty window
  - role security/workload access

This prevents a low-access RB from becoming too valuable from one overloaded first-down/TD feature.

## Regression Fixtures Added

Two cross-position guardrails were added:

- An elite WR anchor must beat a good but fragile role-driven RB when the RB's receipt shows age/injury fragility.
- RB first-down/TD fit cannot overload value by itself when role security and workload earning are weak.

Existing fixtures already cover:

- Elite WR and elite RB both belong in the LVE top tier.
- A mid/stable WR beats a fragile role-driven RB.
- Kyren-style role spike does not rank ahead of Bijan/Gibbs/Jeanty-style dynasty RB anchors.
- JSN-style WR production/target earning should beat Tee Higgins-style profile when the current-season evidence supports it.

## Source-Coverage Limitation

The active board remains review-only. All audited RB/WR rows still show review-level coverage for production and role/usage. The active public import is still missing the freshest completed-season production/role layer needed for final trust.

This means current ordering is useful as an audit surface, but not final decision truth.

## Audit Read

The model is no longer obviously skewed toward WRs or RBs after the sync and RB cap patch. The board now favors:

- elite WR anchors with strong target/route/production receipts
- elite young RBs with strong dynasty windows
- role-heavy RBs only when age/injury/dynasty hold receipts support the value

Remaining odd ranks should be audited through source freshness and role/usage coverage before changing model weights.
