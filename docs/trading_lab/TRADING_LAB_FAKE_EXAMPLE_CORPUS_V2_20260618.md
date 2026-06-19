# Trading Lab Fake Example Corpus V2

Date: 2026-06-18

## Purpose

This corpus provides fake inline examples for docs and regression tests. It is
not a data file, market dataset, recommendation set, or generated output.

| artifact | example | expected_outcome | explanation |
| --- | --- | --- | --- |
| source inventory | SEC EDGAR public filing review for `EXMPL` | ACCEPT | Public/manual source with attribution and research-only use |
| source inventory | Broker credential vault for `PAPER` | REJECT | Credential source category is prohibited |
| research intake | Research whether `SIM` depends on one public source | ACCEPT | Paper-only research question |
| research intake | Use broker token before reviewing `SIM` | REJECT | Broker token wording is prohibited |
| manual lifecycle | `IDEA` to `SOURCE_REVIEW` with manual review note | ACCEPT | Valid manual transition |
| manual lifecycle | `draft` to `executed` | REJECT | Unsupported execution state |
| watchlist note | `REVIEW` thesis with public sources and risk notes | ACCEPT | Paper-only and source-backed |
| watchlist note | Buy `REVIEW` now | REJECT | Advice/execution language is prohibited |
| strategy note | Hypothesis for `FAKE` with evidence and invalidation | ACCEPT | Research-only strategy note |
| strategy note | Auto-execute `FAKE` order | REJECT | Automated execution is prohibited |
| risk journal | Risk category for concentration of evidence | ACCEPT | Risk framing only |
| risk journal | Private account balance risk | REJECT | Private account data is prohibited |
| paper journal | Hypothetical paper entry for `PAPER` | ACCEPT | Simulation note only, no real order |
| paper journal | Real-money order history for `PAPER` | REJECT | Real-money execution data is prohibited |
| manual review packet | Complete fake packet with source/risk/closeout sections | ACCEPT | All required sections present |
| manual review packet | Packet missing source review | HOLD | Missing manual review sections require completion |
| blocked-work gate | Draft docs-only source review checklist | ACCEPT | Research-only maintenance |
| blocked-work gate | Future data ingestion proposal | HOLD | Requires explicit future approval |
| blocked-work gate | Broker/API order routing | REJECT | Broker/API execution path is prohibited |

## Boundary

All examples are fictional and educational. They are not investment advice and
must not be used for execution, data ingestion, or production decisions.
