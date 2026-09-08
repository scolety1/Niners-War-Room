# Validation results

- Candidate deterministic regeneration: True
- Candidate SHA-256: `cad28b9090181daeaa7aadb6b0804967e299c6c547378142436b1fb889f49578`
- Exact identities: 650; unresolved: 0
- Candidate rows: 491; blocked: 159
- Depth: {'QB': 69, 'RB': 118, 'TE': 118, 'WR': 186}
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
