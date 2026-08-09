# Validation results

- Candidate deterministic regeneration: True
- Candidate SHA-256: `94306d2934f6eb3ee6d1f4c2ee41428c84f8479fbea68c736ebd16c3c7780837`
- Exact identities: 910; unresolved: 0
- Candidate rows: 530; blocked: 380
- Depth: {'QB': 74, 'RB': 128, 'TE': 121, 'WR': 207}
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
