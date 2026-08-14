# FantasyPros provider boundary

- Authority label: `EXTERNAL CONSENSUS — FANTASYPROS`
- Scope: `K`, `DST` only; QB/RB/WR/TE are rejected.
- Transport: official public API endpoint, GET only, `x-api-key` header.
- Credential: local `NWR_FANTASYPROS_API_KEY`; no key is committed, displayed, or persisted in a profile.
- Prohibited: HTML scraping, key discovery, terms bypass, NWR K/DST prediction, and cross-scale math with Redraft Champion values.

The new client parses ECR/tier/name/position/team defensively. A malformed response fails closed and never creates a synthetic rank.
