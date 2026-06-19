# Trading Lab Lifecycle Validation Expectations

Date: 2026-06-18

| example | expected_result | reason |
| --- | --- | --- |
| IDEA to SOURCE_REVIEW with manual review note | ACCEPT | Valid manual state transition |
| IDEA to PAPER_JOURNAL_OPEN | REJECT | Skips required manual steps |
| RISK_REVIEW to PAPER_JOURNAL_OPEN with place-order language | REJECT | Execution language |
| SOURCE_REVIEW to WATCHLIST_NOTE with broker/API key language | REJECT | Broker/credential language |
| WATCHLIST_NOTE to RISK_REVIEW with auto-execute language | REJECT | Automated execution |
| SOURCE_REVIEW to WATCHLIST_NOTE with account balance language | REJECT | Private account data |

Lifecycle validation is not an execution state machine. It only governs manual
paper/research note status.
