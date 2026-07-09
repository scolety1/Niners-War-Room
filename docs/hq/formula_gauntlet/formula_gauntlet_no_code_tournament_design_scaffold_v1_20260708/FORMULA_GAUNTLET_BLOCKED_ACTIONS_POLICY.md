# Formula Gauntlet Blocked Actions Policy

## Blocked In This Lane

This lane is a no-code design scaffold. It blocks:

- formula tournaments
- challenger searches
- formula tuning
- weight optimization
- formula hybridization
- winner selection
- source promotion
- production model claims
- production accuracy claims
- ranking changes
- app/runtime changes
- default sort changes
- hidden sort changes
- recommendation, boost, verdict, draft, or trade logic
- use of review-only fields as production inputs
- use of blocked sources as candidate inputs
- use of current/future data in historical inputs

## Blocked Until Separate Source/Data Gates Clear

- Route/YPRR/TPRR tournament execution.
- Exact Model v4 replay tournament execution.
- Rookie/CFBD tournament execution.
- Injury/availability tournament execution.
- Market/ADP tournament execution.
- PFR advanced-stat tournament execution.
- NGS advanced-stat tournament execution beyond approved review-only scope.

## Required Stop Conditions

Stop any future Formula Gauntlet lane if:

- the source gate is ambiguous
- identity joins are name-only
- leakage checks fail
- missingness is treated as zero without proof
- candidate outputs would touch production files
- exact Model v4 replay is claimed without exact receipts
- a formula winner is requested before Master HQ review
- a source-promotion decision is bundled with tournament execution

## Policy Outcome

Until Master HQ explicitly opens an execution lane, Formula Gauntlet is limited to evidence ingestion, process design, source/use gate tracking, and guardrail contracts.
