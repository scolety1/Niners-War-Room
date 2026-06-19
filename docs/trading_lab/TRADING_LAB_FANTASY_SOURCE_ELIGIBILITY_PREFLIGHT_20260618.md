# Trading Lab Fantasy Source Eligibility Preflight - 2026-06-18

This preflight lists possible future source categories. It does not approve integration.

| Source category | Possible future use | Value type | Contamination risk | Manual review | Approval required | Storage/output rule | Current status |
|---|---|---|---|---|---|---|---|
| NWR private value outputs | Core NWR edge and value delta | Private NWR value | High if overwritten by public value | Required | Yes | Read-only; no generated exports | NOT WIRED |
| Outcome V1 display values | Context display for player/outcome view | Private/display context | Medium if treated as trade truth | Required | Yes | Read-only; no generated exports | NOT WIRED |
| Rookie board values | Rookie pick/player context | Private NWR value | High if merged without provenance | Required | Yes | Read-only; no generated exports | NOT WIRED |
| Drop Decision roster pressure | Roster pressure and cut-risk context | Private roster context | Medium if auto-applied | Required | Yes | Read-only; no generated exports | NOT WIRED |
| Mock Draft pick/player context | Draft plan and pick tier context | Private planning context | Medium | Required | Yes | Read-only; no generated exports | NOT WIRED |
| Manually entered opponent roster context | Opponent fit and negotiation realism | Manual context | Medium due to stale/manual input | Required | Yes | In-memory until persistence approved | NOT WIRED |
| Public fantasy rankings | Display-only market comparison | Public market display | High if used inside private NWR score | Required | Yes | Attribution required; no scraping without approval | NOT WIRED |
| Public dynasty trade calculators | Market fairness comparison | Public market display | High if treated as NWR truth | Required | Yes | Attribution required; no scraping without approval | NOT WIRED |
| Public ADP | Market sentiment and pick context | Public market display | Medium | Required | Yes | Attribution required; no scraping without approval | NOT WIRED |
| Public dynasty market value | Market realism labels | Public market display | High if used inside private NWR score | Required | Yes | Attribution required; no scraping without approval | NOT WIRED |

## Prohibited Unless Explicitly Approved Later

- Scraping.
- Paid/private data.
- Using public fantasy value inside private NWR score.
- Automated trade submission.
- Generated exports.
- Hidden credential, secret, token, or key handling.

## Current Verdict

GREEN for source eligibility documentation. HOLD for every integration.
