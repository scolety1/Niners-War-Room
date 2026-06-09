# Truth Set Lab v1 Intake 03: Projections

## Files

- Clean preview: `local_exports/truth_set_lab/v1/source_clean/projections.csv`
- Intake summary: `local_exports/truth_set_lab/v1/reports/projection_intake_summary.json`
- Intake flags: `local_exports/truth_set_lab/v1/reports/projection_intake_flags.csv`
- Points audit: `local_exports/truth_set_lab/v1/reports/projection_points_audit.csv`

## Intake Result

Status: `ready_for_review_not_model_use`

The pasted projection table covers all 40 truth-set players and has no extra players or malformed rows. It is useful as a preview source for projected stat columns, but it is not safe to promote directly into model scoring yet.

## Coverage

- Truth-set rows expected: 40
- Rows present: 40
- Missing truth-set players: 0
- Extra players: 0
- Populated projection evidence rows: 38
- Players without usable offensive projections: 3
  - Luke McCaffrey
  - Brandon Aiyuk
  - Keenan Allen

## Critical Findings

The supplied `projected_lve_points_if_calculable` column should not be used as LVE scoring. For 36 players, the supplied points differ materially from a no-PPR LVE recomputation using the stat columns. The gaps strongly suggest the supplied column includes non-LVE assumptions such as reception scoring.

Largest examples from the audit:

| player | supplied_points | recomputed_no_fd_lve | gap |
|---|---:|---:|---:|
| Puka Nacua | 357 | 213.6 | 143.4 |
| Amon-Ra St. Brown | 324 | 184.3 | 139.7 |
| Ja'Marr Chase | 336 | 196.7 | 139.3 |
| Jaxon Smith-Njigba | 326 | 195.4 | 130.6 |
| Justin Jefferson | 293 | 166.6 | 126.4 |
| CeeDee Lamb | 295 | 175.5 | 119.5 |
| Brock Bowers | 240 | 129.1 | 110.9 |
| Christian McCaffrey | 352 | 244.4 | 107.6 |

## First-Down Gap

No row provides projected rushing first downs or projected receiving first downs. Because LVE awards 0.4 points for rushing/receiving first downs, true projected LVE points must either:

1. Use a separate first-down projection source, or
2. Estimate first downs from historical first-down rates with an explicit `estimated_first_down_projection` status.

Until that is built, recomputed projection scores should be labeled `recomputed_lve_no_first_down_projection`.

## Source Quality Notes

Most rows cite ESPN Mike Clay's 2026 NFL Projection Guide as a public PDF source, but the source field is a site/PDF label instead of a direct retrievable URL. Treat these rows as manual preview evidence until the exact source file is archived or directly referenced.

Rows for Brandon Aiyuk and Keenan Allen explicitly state no 2026 projection is available. Those players should keep a projection gap warning rather than receiving a neutral projection as if it were evidence.

## Safe Usage

Safe:

- Use the stat columns as preview projection inputs.
- Recompute LVE projection points from the stat columns.
- Keep first-down projection missing warnings visible.
- Use missing projection status for players without offensive projections.

Unsafe:

- Do not use `projected_lve_points_if_calculable` as a model score.
- Do not treat the pasted points as official LVE points.
- Do not increase confidence from manually pasted PDF rows until source provenance is tightened.
- Do not hide missing first-down projection fields.

## Recommended Next Step

Create a derived projection import layer that reads the projected stat columns, recomputes no-PPR LVE points, adds explicit first-down projection status, and leaves all results in preview mode until source provenance and first-down estimation are reviewed.
