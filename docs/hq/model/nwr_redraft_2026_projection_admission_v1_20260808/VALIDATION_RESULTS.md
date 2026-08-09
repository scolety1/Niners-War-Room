# Validation results

- Owner-approved candidate SHA-256:
  `94306d2934f6eb3ee6d1f4c2ee41428c84f8479fbea68c736ebd16c3c7780837`
- Governed projection SHA-256:
  `6ee6dbff41e238fb925c8d8d4b5e5079f48de71b132888e5c75fea34e9831c63`
- Deterministic finalization: 530 rows, 1,060 authorized status-cell changes, 0 other changes
- Exact identities: 910; unresolved: 0
- Admitted veterans: 530; separately blocked rows: 380
- Depth: QB 74, RB 128, WR 207, TE 121; K/DST 0
- Four built-in profile rankings: 530 admitted rows each
- Settings checks: 5/5 pass
- Ranking sanity: no top-100 duplicate IDs, zero projections, rookies, or K/DST leakage
- Rookie handling: no workload invention; Player Compare returns `NOT_ENOUGH_INFORMATION` for a
  rookie absent from the governed snapshot
- Browser: three responsive viewports plus profile CRUD, all Redraft tabs, Player Compare Redraft
  context, Draft Cockpit Redraft context, and five dynasty regression routes passed
- Browser diagnostics: zero console warnings/errors, zero root overflow, no traceback or Page Not
  Found; no draft pick was assigned and disposable profile state was removed
- Focused owner-finalization tests: 3 passed
- Admitted-validator callable test: 1 passed
- Prior Redraft model/engine/page focused tests: 24 passed
- Repository-wide suite: the prior bounded run produced no final result after timing out at 304
  seconds; the focused admission and product gates are the authoritative bounded verification here
- Scheduler: `NWR DynastyProcess Market Baseline Refresh` remains disabled
- Independent fresh-HQ adoption: required next; HQ/stable not yet changed by this packet commit
