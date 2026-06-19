# Trading Lab Docs Index

Date: 2026-06-18

## Purpose

This index maps the Trading Lab paper/research-only documentation set. Trading
Lab is not an investment-advice, broker/API, execution, deployment, data
ingestion, or fantasy-football lane.

## Reading Order

1. Charter and source policy
2. Safe research foundation
3. Source inventory and watchlist templates
4. Paper, risk, and strategy journal templates
5. Validation expectation docs
6. Schema contracts and validation inventory
7. Backtesting design guardrails and future gates
8. Operator workflow and manual review packets
9. Closeout docs

## Charter And Foundation

- `TRADING_LAB_CHARTER_20260618.md`: lane purpose, non-purpose, scope, hard
  prohibitions, and relationship to Niners War Room fantasy lanes.
- `TRADING_LAB_SOURCE_AND_DATA_POLICY_20260618.md`: allowed and prohibited
  source categories, no-secrets policy, no-credentials policy, and untracked
  local file rules.
- `TRADING_LAB_SAFE_RESEARCH_FOUNDATION_20260618.md`: current validation-only
  module purpose and safe future-agent rules.

## Source Inventory

- `TRADING_LAB_SOURCE_INVENTORY_TEMPLATE_20260618.md`: required source review
  fields and fake/public-only examples.
- `TRADING_LAB_SOURCE_INVENTORY_VALIDATION_EXAMPLES_20260618.md`: T3 examples
  showing ACCEPT, REJECT, and HOLD FOR MANUAL REVIEW outcomes.
- `TRADING_LAB_RESEARCH_INTAKE_SCHEMA_CONTRACT_20260618.md`: T5 intake
  fields, statuses, invalid fields, and paper-only constraints.

## Watchlist Notes

- `TRADING_LAB_WATCHLIST_NOTE_TEMPLATE_20260618.md`: paper-only watchlist-note
  fields and invalid prohibited examples.
- `TRADING_LAB_WATCHLIST_EXAMPLES_20260618.md`: fictional safe watchlist
  examples and invalid examples.
- `TRADING_LAB_WATCHLIST_NOTE_SCHEMA_V2_20260618.md`: T5 watchlist schema v2
  fields, statuses, and rejection cases.

## Paper Journal

- `TRADING_LAB_PAPER_JOURNAL_TEMPLATE_20260618.md`: paper/simulation-only
  journal entry fields and examples.
- `TRADING_LAB_PAPER_JOURNAL_VALIDATION_EXPECTATIONS_20260618.md`: T3
  validation expectations for valid and invalid paper journal entries.
- `TRADING_LAB_PAPER_JOURNAL_SCHEMA_V2_20260618.md`: T5 paper journal schema
  v2 action statuses, review statuses, and execution wording.

## Risk Journal

- `TRADING_LAB_RISK_JOURNAL_TEMPLATE_20260618.md`: research-only risk journal
  fields and fake examples.
- `TRADING_LAB_RISK_JOURNAL_VALIDATION_EXPECTATIONS_20260618.md`: T3
  expectations for safe risk notes and prohibited drift.
- `TRADING_LAB_RISK_JOURNAL_SCHEMA_V2_20260618.md`: T5 risk categories,
  severity/probability scales, and invalid examples.

## Strategy Notes

- `TRADING_LAB_STRATEGY_NOTE_TEMPLATE_20260618.md`: research-only strategy note
  fields and fake examples.
- `TRADING_LAB_STRATEGY_NOTE_VALIDATION_EXPECTATIONS_20260618.md`: T3
  expectations for safe strategy-note content and prohibited content.
- `TRADING_LAB_STRATEGY_NOTE_SCHEMA_V2_20260618.md`: T5 strategy schema v2
  validation expectations for hypotheses, assumptions, evidence, risks, and
  invalidation notes.

## Backtesting Design

- `TRADING_LAB_BACKTESTING_DESIGN_GUARDRAILS_20260618.md`: design guardrails
  before any future backtesting code exists.
- `TRADING_LAB_BACKTESTING_READINESS_CHECKLIST_20260618.md`: T3 checklist for
  what must exist before any future implementation is separately approved.
- `TRADING_LAB_BLOCKED_WORK_GATE_CHECKLIST_20260618.md`: T5 gate before future
  data ingestion or backtesting can even be proposed.
- `TRADING_LAB_FUTURE_PHASE_DECISION_GATE_20260618.md`: T6 future-phase gate
  for proposal preconditions, required approval, and closeout expectations.

## Public Source Review

- `TRADING_LAB_PUBLIC_SOURCE_REVIEW_CHECKLIST_20260618.md`: source acceptance
  checklist for public research references.

## Operator Workflow And Review Packets

- `TRADING_LAB_OPERATOR_MANUAL_20260618.md`: manual workflow from intake to
  closeout.
- `TRADING_LAB_RESEARCH_INTAKE_TEMPLATE_20260618.md`: research intake template.
- `TRADING_LAB_MANUAL_PAPER_LIFECYCLE_20260618.md`: manual lifecycle states and
  invalid transitions.
- `TRADING_LAB_MANUAL_LIFECYCLE_SCHEMA_CONTRACT_20260618.md`: T5 formal
  lifecycle states and transitions.
- `TRADING_LAB_REVIEW_CADENCE_AND_CLOSEOUT_20260618.md`: review cadence and
  closeout checklist.
- `TRADING_LAB_MANUAL_REVIEW_PACKET_TEMPLATE_20260618.md`: T5 end-to-end
  manual review packet template.
- `TRADING_LAB_MANUAL_REVIEW_PACKET_EXAMPLES_20260618.md`: T6 valid, invalid,
  and HOLD packet examples.

## Validation Inventory And Language

- `TRADING_LAB_VALIDATION_COVERAGE_MATRIX_20260618.md`: artifact-to-guardrail
  coverage matrix.
- `TRADING_LAB_VALIDATOR_INVENTORY_20260618.md`: T6 validator inventory across
  docs, tests, helpers, and gaps.
- `TRADING_LAB_T7_ARTIFACT_VALIDATOR_PLAN_20260618.md`: T7 plan for generic
  manual artifact validators.
- `TRADING_LAB_T7_VALIDATOR_COVERAGE_20260618.md`: T7 ACCEPT/REJECT/HOLD
  coverage summary.
- `TRADING_LAB_T8_SCHEMA_REGISTRY_PLAN_20260618.md`: T8 schema registry plan.
- `TRADING_LAB_SCHEMA_REGISTRY_20260618.md`: centralized docs-only artifact
  schema registry.
- `TRADING_LAB_FAKE_EXAMPLE_CORPUS_20260618.md`: inline fake ACCEPT/HOLD/REJECT
  examples for docs and tests.
- `TRADING_LAB_NO_ADVICE_LANGUAGE_GUIDE_20260618.md`: safe and prohibited
  language rewrites.
- `TRADING_LAB_PROHIBITED_LANGUAGE_TAXONOMY_20260618.md`: T6 taxonomy for
  execution, broker/API, credential, private-account, advice, automation, data,
  and generated-output language.

## Closeouts

- `TRADING_LAB_T1_CLOSEOUT_20260618.md`: T1 docs-only closeout.
- `TRADING_LAB_SAFE_RUNWAY_CLOSEOUT_20260618.md`: safe runway closeout.
- `TRADING_LAB_T3_READINESS_CLOSEOUT_20260618.md`: T3 readiness closeout.
- `TRADING_LAB_T4_OPERATOR_WORKFLOW_CLOSEOUT_20260618.md`: T4 operator workflow
  closeout.
- `TRADING_LAB_T5_SCHEMA_AND_GATES_CLOSEOUT_20260618.md`: T5 schema and gates
  closeout.
- `TRADING_LAB_T6_READINESS_AUDIT_20260618.md`: T6 readiness audit.
- `TRADING_LAB_T6_VALIDATION_READINESS_CLOSEOUT_20260618.md`: T6 validation
  readiness closeout.
- `TRADING_LAB_T7_ARTIFACT_VALIDATOR_CLOSEOUT_20260618.md`: T7 artifact
  validator closeout.
- `TRADING_LAB_T8_SCHEMA_REGISTRY_CLOSEOUT_20260618.md`: T8 schema registry
  closeout.

## Ready

Trading Lab is ready for paper/research-only source review, template-based
watchlist notes, paper journal validation examples, risk journal hygiene,
strategy-note structure, and future readiness review.

## Still Blocked

Still blocked:

- Real-money trading
- Broker orders
- Broker/API integration
- Credentials, secrets, keys, or tokens
- Automated execution
- Production investment advice
- Public deployment
- Data ingestion
- Generated market datasets or generated outputs
- Private brokerage/account data
- Fantasy-football lane behavior changes

## Guardrail Summary

All current Trading Lab work must remain paper-only, research-only, local-first,
non-executing, and not investment advice.
