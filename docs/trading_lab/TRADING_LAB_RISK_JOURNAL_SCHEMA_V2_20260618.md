# Trading Lab Risk Journal Schema V2

Date: 2026-06-18

## Purpose

Risk Journal Schema V2 structures research/process risk without becoming real
account guidance, investment advice, broker workflow, or execution policy.

## Required Fields

- `risk_id`
- `date`
- `artifact_type`
- `related_artifact_id`
- `risk_category`
- `risk_description`
- `severity`
- `probability`
- `mitigation_note`
- `invalidation_or_stop_condition`
- `review_date`
- `status`

## Optional Fields

- `operator`
- `related_source_names`
- `lessons_learned`
- `notes`

## Structured Categories

- `THESIS_RISK`
- `DATA_QUALITY_RISK`
- `SURVIVORSHIP_BIAS`
- `LOOK_AHEAD_BIAS`
- `OVERFITTING_RISK`
- `LIQUIDITY_ASSUMPTION_RISK`
- `EMOTIONAL_PROCESS_RISK`
- `EXECUTION_POLICY_RISK`
- `ATTRIBUTION_TERMS_RISK`
- `PRIVATE_DATA_CONTAMINATION_RISK`

## Severity Scale

- `LOW`
- `MEDIUM`
- `HIGH`
- `BLOCKING`

## Probability Scale

- `LOW`
- `MEDIUM`
- `HIGH`
- `UNKNOWN`

## Accepted Statuses

- `OPEN`
- `MITIGATED`
- `HOLD_NEEDS_REVIEW`
- `CLOSED_LESSONS`
- `REJECTED_PROHIBITED`

## Invalid Examples

| invalid_example | reason |
| --- | --- |
| `place a stop-loss order` | Broker/order instruction. |
| `reduce real position based on account balance` | Real-money advice and private account data. |
| `connect broker to monitor risk` | Broker integration. |
| `auto-execute risk rule` | Automated execution. |
| `use private brokerage export` | Private brokerage data. |
