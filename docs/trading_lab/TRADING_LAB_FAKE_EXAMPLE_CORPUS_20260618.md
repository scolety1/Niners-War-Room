# Trading Lab Fake Example Corpus

Date: 2026-06-18

This corpus provides inline fake examples for docs and tests. It is not a data
file and does not approve data ingestion or generated outputs.

| artifact_type | example | expected_result | reason |
| --- | --- | --- | --- |
| research_intake | `RI-EXMPL` asks a paper-only public-source question | ACCEPT | Safe manual research language |
| manual_lifecycle | `LC-PAPER` moves IDEA to SOURCE_REVIEW | ACCEPT | Manual lifecycle state only |
| watchlist_note | `REVIEW` paper hypothesis with public source | ACCEPT | Paper-only and citeable |
| strategy_note | `SN-SIM` public evidence hypothesis | ACCEPT | Research-only |
| risk_journal | `RJ-FAKE` source-quality risk | ACCEPT | Descriptive risk |
| paper_journal | `PJ-PAPER` no-action observation | ACCEPT | Paper-only |
| manual_review_packet | `MRP-EXMPL` packet marked HOLD for terms review | HOLD | Manual source terms uncertainty |
| blocked_work_gate | Source manifest proposal with no code | HOLD | Needs explicit approval |
| watchlist_note | Buy `EXMPL` now | REJECT | Advice |
| paper_journal | Use broker token | REJECT | Credential/broker language |
| strategy_note | Auto-execute threshold | REJECT | Automated execution |
| blocked_work_gate | Start data ingestion | HOLD | Future phase proposal required |

Only fictional symbols are used: `EXMPL`, `PAPER`, `SIM`, `REVIEW`, and `FAKE`.
