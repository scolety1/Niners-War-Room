# Validation results

- Candidate deterministic regeneration: True
- Candidate SHA-256: `15001fc47cc0d039a3ffdd8211f16aae44ca5bb1136fa9e9919ef6ab4309d1c9`
- Exact identities: 973; unresolved: 0
- Candidate rows: 576; blocked: 397
- Depth: {'QB': 76, 'RB': 141, 'TE': 132, 'WR': 227}
- Review-only preset rankings: all four built-ins READY
- Settings checks: 5/5 PASS
- Ranking sanity: zero top-100 duplicates, zero top-100 projection-zero rows, no rookies or
  K/DST leakage; 1QB top 25 contains 8 QBs and Superflex top 25 contains 11, retained as an explicit
  owner-review observation rather than manually reordering players
- Governance: owner approval required; installer was not called
- Browser/independent adoption/HQ: skipped because admission is not complete
- Focused tests: 24 passed
- Repository-wide suite: no result; bounded run timed out after 304 seconds after the pre-existing
  environment's missing `openpyxl` dependency was supplied locally
