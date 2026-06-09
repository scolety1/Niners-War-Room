# Truth Set Lab v3.1 Agent Source Triage

Status: review-only. These reports do not change model scores, formulas, active rankings, or readiness gates.

## Intake

The three agent reports are archived/extracted under:

- `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\agent_reports\NFL Data Sources for Fantasy (1).docx`
- `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\agent_reports\NFL Data Sources for Fantasy (1).txt`
- `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\agent_reports\NFL role_usage data sources.docx`
- `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\agent_reports\NFL role_usage data sources.txt`
- `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\agent_reports\NFL role_usage data sources (1).docx`
- `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\agent_reports\NFL role_usage data sources (1).txt`

Combined triage CSV:

- `C:\Dev\niners-war-room\local_exports\truth_set_lab\v3_1\reports\truth_set_v3_1_agent_source_triage.csv`

## Verdict

The agents mostly confirmed v3/v3.1 rather than overturning it.

- Free/public structured data is enough for production, rushing/receiving first downs, target share, RB carry share, weighted opportunities, red-zone/goal-line usage, short-yardage usage, and snap share.
- Free/public structured data is not enough for true routes run, route participation, TPRR, or YPRR.
- No legal public projection source appears to provide projected rushing/receiving first downs.
- Current injury data remains weak without a structured current source; nflreadr injuries are useful historically through 2024, not as current health truth.
- Manual agent-collected stat tables should remain rejected.

## Implementation Decisions

Already supported by v3:

- Native nflverse production import.
- Real historical rushing/receiving first downs.
- Play-by-play derived usage.
- Snap share import.
- Route-data quarantine.

Supported by v3.1:

- Preview-only first-down projection estimator.
- WR/TE route proxy caution worklist.
- Injury review template for sourced notes only.

Not supported for active scoring yet:

- True route metrics.
- Direct first-down projections.
- Current injury scoring.
- Manually compiled projection/route/injury stat rows.

## Next Best Patch

Do not launch another broad data hunt. The highest-value next patch is a small **v3.2 source-to-model promotion design**:

1. Decide whether v3/v3.1 preview fields are ready to be promoted into the active-model schema.
2. Keep route metrics quarantined and visible.
3. Keep first-down projection estimates preview-only or introduce them with a clear confidence penalty.
4. Keep injury current-status review-only unless a sourced structured feed is available.
5. Run the named-player audit after promotion design, before formula work.

## Agent Guidance

Agents should not manually collect player stats. They may only verify whether a legal/exportable structured source exists and report schema, terms, cost, and mapping fields.
