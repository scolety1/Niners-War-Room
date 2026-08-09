# NWR Redraft 2026 rookie governed adoption review

## Verdict

`GREEN_NWR_REDRAFT_2026_ROOKIE_GOVERNED_ADOPTION_READY`

No High or Medium defect remains. The exact governed rookie/combined candidate is
ready for a normal non-force canonical push and stable fast-forward, provided the
adopting lane rechecks that canonical and remote HQ have not moved and that the
installed projection SHA remains unchanged immediately before adoption.

This review did not push, merge, fast-forward, or mutate canonical Git state. All
review writes were confined to the isolated review worktree and disposable local
review state.

## Reviewed Git identity

- Candidate commit: `08e4155815d85a04b9a81550929b42126c906875`
- Candidate tree: `b7ea038ba9d07fb6b260a99e476752b1d5580d5b`
- Canonical base: `8b98d45657bcddc4562543f3f629425d10f321bb`
- Canonical base tree: `b9e9a880c915e0a840ce3c6d31c83c857fdf5ab1`
- Review worktree: `C:\NWR\Niners-War-Room-redraft-2026-rookie-governed-adoption-review-20260809`
- Review branch: `codex/nwr-redraft-2026-rookie-governed-adoption-review-20260809`

At the final pre-verdict drift check, local stable and
`origin/work/hq-parallel-control` both remained at the canonical base above, and
the stable worktree was clean.

## Exact approval and finalization bindings

The committed owner approval records the exact owner message timestamp
`2026-08-09T01:52:00-06:00`, scope
`REDRAFT_2026_ROOKIE_PROJECTIONS`, and `source_as_of` `2026-07-30`.

| Artifact | Independently observed SHA-256 |
|---|---|
| Approved rookie candidate | `c62a47ffa3ed8746675225225be473da0dbe7f1313842c769dafbcd6709499bc` |
| Approved combined review candidate | `218eb5068b30e4441ae6426967f7ea5ce2a47ed3c81686663d5bd155bc45e31f` |
| Approved immutable veteran input | `6ee6dbff41e238fb925c8d8d4b5e5079f48de71b132888e5c75fea34e9831c63` |
| Governed rookie output | `e1636eb729441aed91187cf8170c05279090213ef0c2426269a63d95ec59c4d7` |
| Governed combined output | `e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25` |

The finalizer was rerun from the admitted public source snapshots into a fresh
temporary packet. It reproduced all four rookie/review/governed hashes above.
The exact-hash stop tests also passed for modified rookie and modified combined
review bytes.

Finalization changed exactly 156 cells: `source_status` and `evidence_status`
for each of 78 owner-approved rookie rows. Every transition was respectively
`GOVERNANCE_PENDING` to `GOVERNED` or `MODEL_VALIDATED_REVIEW_ONLY` to
`ADMITTED_CURRENT_SEASON`. No other cell changed.

## Veteran, row, and position invariants

- Approved veterans: 530 rows, 33 columns, 17,490 cells.
- Governed rookies: 78 rows: QB 10, RB 12, WR 36, TE 20.
- Governed combined snapshot: 608 rows.
- Blocked outside the admitted snapshot: 2 rows, Max Bredeson and Riley
  Nowakowski, both position conflicts.
- K/DST rows: 0.
- Duplicate admitted player IDs: 0.
- The governed combined file begins with the complete approved veteran CSV as
  its exact byte prefix.
- All 17,490 veteran cells are identical to the approved veteran input.
- The installed canonical projection independently hashes to the exact governed
  combined SHA `e483caae...1c25`.
- Its install manifest binds that SHA, 608 admitted rows, 0 blocked rows, the
  governance receipt hash, and validity through `2026-08-29`.

## Source, license, leakage, and model gates

- Packet source rows: 17, comprising the immutable veteran input plus 16 public
  nflverse assets.
- All 16 asset hashes match the local immutable snapshots.
- Draft, player-registry, and seasonal-stat completion manifests match their
  recorded hashes and are `complete=true`, `immutable=true`, and
  `ADMITTED_PRIMARY_SOURCE`.
- All three governing license receipts match their hashes, identify
  `CC-BY-4.0`, and record
  `TERMS_ACCEPTED_FOR_RESEARCH_WITH_ATTRIBUTION`.
- Retrieval time is `2026-07-30T07:24:07Z`, within the admitted 30-day boundary.
- Historical draft classes are 2012-2025; strict walk-forward targets are
  2016-2025.
- Independent inspection found 796 walk-forward prediction rows and zero rows
  where `training_max_season >= target season`.
- The selected position-plus-round model beats the position baseline for QB,
  RB, WR, and TE; all promotion gates remain PASS.
- The loader selects only draft-day identity/capital fields from draft picks;
  draft-source career outcomes are not loaded. Dynasty ranks, Unified Preview
  values, proprietary projections, provider/API calls, and post-2025 outcomes
  are absent from the model lane.

## Rankings, sensitivity, tests, and manifest

- All four governed presets rank 608 rows, including all 78 admitted rookies,
  with zero duplicate IDs and zero K/DST rows.
- All five profile sensitivity checks pass.
- Packet manifest: 41 entries for 41 non-manifest files; no missing, extra,
  byte-count-mismatched, or SHA-mismatched entry.
- Focused test command across veteran engine/admission and rookie
  model/finalization/combined validation: **85 passed**.
- Ruff on the seven rookie builder/finalizer/validator/service/test files:
  **All checks passed**.

## Product and browser evidence

The committed browser receipt contains 27 PASS rows: 9 routes across
`375x812`, `768x1024`, and `1440x1000`. Its app source fingerprint
`48364f0daa31de12d8797be3706dcb372b1a629537aa29c74b1a6f4dc9f83c7a`
recomputes exactly from this review checkout.

An additional live smoke used a disposable governed install and profile in the
isolated review worktree:

- `/redraft`: one semantic H1; 608 ranked and 0 blocked.
- Redraft Data Health: `READY_REVIEW_ONLY`, 608 ranked, 0 blocked.
- `/draft-cockpit`: one semantic H1; the Redraft rail resolved the active
  profile and showed top-remaining/tier/replacement context with explicit
  descriptive-only and no-best-pick authority.
- `/trading-lab`: one semantic H1; manual-review/no-trade-model/no-automatic-
  offer language remained visible.
- A known one-time Streamlit direct-route fallback occurred only on cold start;
  warmed direct navigation succeeded. A fresh warmed tab had no console warning
  or error. This matches the durable engine receipt's documented cold-start
  behavior and is not a candidate regression.

The fresh worktree intentionally lacked canonical ignored dynasty board files,
so a second live Player Compare universe smoke could not hydrate its full
dynasty registry there. The exact source-fingerprint-bound canonical 27-cell
receipt and focused Player Compare tests remain the applicable evidence for that
route; no fallback or fabricated players were used in the isolated smoke.

## Preserved authorities and operational state

- The candidate changes no pre-existing app page, dynasty authority, Unified
  Preview authority, Trading Lab implementation, scheduler implementation,
  profile, or installed-projection path.
- The only `src` addition is the separately scoped rookie Redraft model service.
- Trading Lab remains manual-only in implementation and visible language; no
  valuation, offer generation, or automatic recommendation was enabled.
- Scheduled task `NWR DynastyProcess Market Baseline Refresh` is Disabled and
  `Enabled=false`.
- Canonical Redraft saved profiles: 0.
- Canonical active-profile receipt: absent.
- Canonical installed combined projection remained at exact SHA
  `e483caae...1c25` after review.
- Dynasty authority was not changed.

## Adoption recommendation

Adopt only by the normal non-force path. The adopting lane should recheck the
candidate ancestry, exact governed combined and veteran SHAs, clean stable/HQ
state, remote HQ head, zero canonical profiles, absent active profile receipt,
and Disabled scheduler immediately before push/fast-forward. Stop on any drift.
