# Trading Lab Research Intake Template

Date: 2026-06-18

## Purpose

Use this template for a new research question before it becomes a watchlist,
risk, strategy, or paper journal note. Intake is paper-only, research-only, and
not investment advice.

## Required Fields

- `intake_id`
- `date`
- `research_question`
- `asset_or_topic_scope`
- `source_names`
- `source_review_status`
- `paper_only_intent`
- `expected_learning_goal`
- `risk_categories_to_review`
- `prohibited_content_check`
- `next_review_date`
- `status`
- `notes`

## Valid Fake Examples

| field | example |
| --- | --- |
| intake_id | `RI-EXMPL-001` |
| date | 2026-06-18 |
| research_question | How should public filing notes be reviewed before a paper watchlist entry? |
| asset_or_topic_scope | Fictional symbol `EXMPL` and public filing process |
| source_names | SEC EDGAR public filing page |
| source_review_status | `PASS_PUBLIC_RESEARCH_ONLY` |
| paper_only_intent | Paper-only learning note |
| expected_learning_goal | Practice source attribution and invalidation notes |
| risk_categories_to_review | Thesis risk, source quality, advice-language drift |
| prohibited_content_check | No orders, no credentials, no private account data |
| next_review_date | 2026-07-18 |
| status | `SOURCE_REVIEW` |
| notes | No execution path. |

## Invalid Examples

| invalid_content | rejection_reason |
| --- | --- |
| Buy or sell `EXMPL` now | Investment advice and real-money instruction. |
| Place an order after review | Broker order instruction. |
| Use my brokerage balance | Private account data dependency. |
| Add broker API token | Credentials/secrets and broker integration. |
| Auto-execute if a threshold is crossed | Automated execution. |

## Acceptance Criteria

- Intake is research-only and paper-only.
- Source names are public or marked HOLD.
- Prohibited content check is explicit.
- Next review date is present.
- No private account data, credentials, execution path, or advice language.
