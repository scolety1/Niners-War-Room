# As-Of And Leakage Guardrail Report V3

## Checks

- Feature season N to target season N+1 lag: PASS.
- Target outcomes remain target-only: PASS.
- Current-only roster/status/injury/depth/schedule context as historical features: ABSENT.
- Market, ADP, vendor, projection, and live ranking fields as source truth: ABSENT.
- Forbidden route/proxy families and ambiguous red-zone attempt fields: ABSENT from canonical columns and blocked in the fence report.
- No formula search or optimization: PASS.

V3 starts from the V2 N-to-N+1 substrate and only appends review-only audit metadata. It does not use target-season context as feature data.
