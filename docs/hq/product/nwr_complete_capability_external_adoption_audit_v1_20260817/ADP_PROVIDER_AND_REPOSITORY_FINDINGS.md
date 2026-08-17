# ADP Provider and Repository Findings

## Conclusion

NWR has no production Redraft ADP. The cleanest first implementation is a provider-neutral snapshot contract with owner-imported CSV. Optional APIs can be added only after owner, license/terms, format, freshness and outage approval.

| Source | What it can provide | Decision | Boundary |
|---|---|---|---|
| Sleeper official API | league settings, rosters, drafts, picks, transactions, players | Keep | Read-only; no documented ADP endpoint |
| Historical Sleeper league drafts | league-specific pick observations | Add later | Sparse/sample-biased; season and identity receipts required |
| Owner CSV | current ADP/expected pick from an owner-authorized source | Add first | Hash, schema, scoring/platform and timestamp required |
| FantasyPros API | keyed projections/rankings/consensus depending entitlement | Optional/defer | Separate terms and API key; never mandatory |
| MFL/other public exports | possible ADP context | Research gap | Do not ship until official contract/terms and 2026 coverage are verified |
| `VTNoble/adp-vs-projection` | 2022 rank-gap demonstration | Reject | stale, unlicensed, no supported provider guarantee |
| `ball-and-chain-gfl/adp-board-2026` and similar repos | potentially current snapshots | Defer | repository data is not automatically licensed/current/provider-grade |

ADP must never be inferred from the current Dynasty Market value. A Redraft snapshot must carry expected pick, uncertainty/sample count when available, source format, season, scoring, platform, team count, freshness, coverage and stable identity.
