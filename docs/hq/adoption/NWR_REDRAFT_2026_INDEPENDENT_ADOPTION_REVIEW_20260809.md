# NWR Redraft 2026 independent HQ adoption review

## Adoption scope

- Fresh branch: `work/nwr-redraft-2026-independent-adoption-20260809`
- Fresh worktree: `C:\NWR\Niners-War-Room-redraft-2026-independent-adoption-20260809`
- Canonical HQ base: commit `5ad753afb71311bcbdfcf875213605b656485985`, tree
  `926d08a4c2543948f6613cf166fda83566663c20`
- Adopted source commits, in order: `c396afbff5b4664247e4042500890aad8e68af90`,
  `d392db5d6f1cb92fb9d2e3c3fa5ea150e3e3edf8`, and
  `99ad2f222ca861d70a77348ffe4052ec181586b1`
- Review date: 2026-08-09

## Governance and data result

- The NWR Owner record approves scope `REDRAFT_2026_VETERAN_PROJECTIONS` and exact
  candidate SHA-256 `94306d2934f6eb3ee6d1f4c2ee41428c84f8479fbea68c736ebd16c3c7780837`.
- Independent deterministic finalization reproduced the governed snapshot byte-for-byte at
  SHA-256 `6ee6dbff41e238fb925c8d8d4b5e5079f48de71b132888e5c75fea34e9831c63`.
- Finalization changed only `source_status` and `evidence_status`: 1,060 cells across 530
  rows, with zero other changed cells.
- The separately supplied `NWR_DATA_GOVERNANCE` receipt binds the governed CSV SHA,
  approval scope, source identity, validity window, and permitted/prohibited uses. A
  disposable install retained the receipt and produced a manifest whose source and receipt
  hashes validated on reload.
- Snapshot checks: `source_as_of=2026-08-08`; 530 veterans; QB 74, RB 128, WR 207, TE 121;
  zero rookies, K, or DST; exact-ID joins only; freshness valid through 2026-09-07.
- All four built-in league profiles generated 530 ranked rows. The 10-team 1QB Standard,
  12-team 1QB Half-PPR, 12-team PPR, and 12-team Superflex PPR generations were ready.
  Settings sanity passed 5/5.

## Independent correction

The source commits did not force LF bytes for the governed admission packet. On a fresh
Windows checkout with `core.autocrlf=true`, checkout conversion changed the approved and
governed CSV byte hashes even though the Git blobs were correct. The adoption branch adds a
packet-scoped `.gitattributes` rule (`text eol=lf`). A fresh materialization now preserves the
exact candidate, governed snapshot, and owner-record hashes. Admission logic was not weakened.

The earlier medium durable-validation concern remained materially applicable on a fresh
checkout: the committed receipt predated the final source fingerprint and raw worktree bytes
made matching line-ending-dependent. The adoption correction canonicalizes CRLF to LF for the
fingerprint, rebinds the receipt to the corrected source, and adds a Windows/LF equivalence
test. The build script fingerprints itself and the implementation/tests, and receipt validation
requires the exact unique 9-route by 3-viewport matrix.

## Test and browser evidence

- Focused pytest set: 73 passed. Coverage included engine service, page integration,
  navigation, projection model, deterministic owner finalization, admitted-snapshot
  validation, Draft Cockpit, and Player Compare.
- Warmed browser matrix: all 27 route/viewport cells passed at 375x812, 768x1024, and
  1440x1000 for `/redraft`, `/player-compare`, `/draft-cockpit`, `/rankings`,
  `/unified-universe-review`, `/rookie-board`, `/trading-lab`, `/personal-board`, and
  `/settings-data-health`. Every route had one semantic `h1`, no root overflow, no traceback,
  and no persistent dialog.
- A single cold-start Streamlit direct-route fallback was observed and retained in the
  console evidence. The warmed source-matched matrix passed without recurrence.
- Player Compare showed `REDRAFT V1 - REVIEW`, the active 12-team PPR profile, exact-ID
  current-player rows, and Carson Beck as a blocked rookie with `Not enough information`.
- Draft Cockpit showed a separate redraft expander for the active profile, including top
  remaining redraft rank, tier, and replacement gap, explicitly descriptive and without
  automatic best-pick authority.

## Mutation and preservation checks

A controlled second open-only cycle across Redraft, Player Compare, Draft Cockpit, and
Settings / Data Health produced identical before/after fingerprints:

- Disposable redraft store: 5 files,
  `a3c141530dbc14062de5d075fb95bf1d1eccea97c2dbe726b389c6c3feaaace8`
- Live draft runtime: 204 files,
  `6b55879f3687ccc6209f15c87e09c024d9531b77b667e96a5e325bf834276bae`
- Personal workspace root remained absent; no page-open record was created.

No browser action assigned a pick, saved personal state, changed a profile, or installed a
projection. Canonical HQ, stable, operational, dynasty artifacts, scheduler state, and shared
user state were not promoted or mutated by this adoption review.

## Independent verdict

No remaining High or Medium adoption defect was found. The owner-approved, governed veteran
projection admission and Redraft Engine V1 are recommended for adoption into canonical HQ,
subject to the normal independent merge/cherry-pick workflow. Do not promote directly to
stable from this branch.
