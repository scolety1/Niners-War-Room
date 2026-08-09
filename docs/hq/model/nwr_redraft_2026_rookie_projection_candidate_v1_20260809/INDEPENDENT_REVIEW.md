# Independent review verdict

`GREEN_CORRECTED_REVIEW_CANDIDATE_OWNER_SHA_APPROVAL_REQUIRED`

The exact original candidate commit `08b6bdd13d3ca487e5e00404ecbcba5c193cccea`
is `STOP_REPLACE`: the independent review found two Medium integrity/coherence
defects. Both are corrected on the isolated review branch. No High or Medium
issue remains in the corrected candidate described below.

This review did not install, govern, canonicalize, or otherwise authorize the
rookie layer. Real-draft readiness remains blocked on exact-SHA owner approval
and the normal governed installation/adoption checks.

## Corrected exact candidates

- Rookie rows: 78
- Rookie SHA-256: `c62a47ffa3ed8746675225225be473da0dbe7f1313842c769dafbcd6709499bc`
- Approved veteran rows: 530
- Approved veteran input SHA-256: `6ee6dbff41e238fb925c8d8d4b5e5079f48de71b132888e5c75fea34e9831c63`
- Combined rows: 608
- Combined SHA-256: `218eb5068b30e4441ae6426967f7ea5ce2a47ed3c81686663d5bd155bc45e31f`
- Governance status: `OWNER_EXACT_SHA_APPROVAL_REQUIRED`
- Installed: no

## Findings and corrections

### IR-01 — Medium — committed manifest did not match committed bytes

The original `MANIFEST.csv` was created from CRLF JSON/Markdown bytes before
the packet-wide LF Git policy normalized those files. Eight manifest hashes did
not match the exact committed files. The candidate and combined CSV hashes were
not affected.

Correction: all builder-authored text and JSON now use explicit LF newlines.
The regenerated manifest has 0 byte-count or SHA mismatches, and an executable
test verifies every manifest row against the committed file.

### IR-02 — Medium — central score fell outside its projection bounds

The original component-wise sixth-round QB median produced 47.5 passing yards
and 1.0 interception for Cade Klubnik: -0.1 half-PPR points, while the stored
lower bound was 0.0. The original nonnegative-component gate did not detect
that the interval excluded its own central score.

Correction: the component median preserves its turnover mix but scales median
turnovers only when necessary to keep the deterministic central half-PPR score
nonnegative. A new promotion gate requires every central score to be finite,
nonnegative, and inside its low/high bounds. The corrected minimum score is
0.0 and there are 0 bound violations.

## Independent evidence checks

### Leakage and survival handling

- Historical draft classes: 2012-2025.
- Walk-forward test classes: 2016-2025.
- Walk-forward prediction rows: 796.
- Target/future-class training violations: 0.
- Exact historical identity coverage: 1,105 / 1,111 = 99.46%.
- Historical exact-ID rows with a REG outcome: 896.
- Historical exact-ID rows without a REG outcome: 209; all 209 are retained
  with every modeled outcome component set to zero.
- Draft-pick source career outcomes are excluded at load time.
- Dynasty ranks, Unified Preview values, market ranks, proprietary projections,
  narratives, and post-2025 NFL outcomes are not model inputs.

The corrected position-level walk-forward results are:

| Position | Rows | Model MAE | Baseline MAE | Improvement | Spearman |
|---|---:|---:|---:|---:|---:|
| QB | 119 | 41.6324 | 65.7144 | 24.0820 | 0.5534 |
| RB | 215 | 42.5874 | 53.8427 | 11.2553 | 0.5457 |
| TE | 141 | 25.8482 | 31.6851 | 5.8369 | 0.5115 |
| WR | 321 | 33.1495 | 44.3524 | 11.2029 | 0.5812 |

The selected model beats the position-median baseline in every one of the ten
combined test seasons. At the position-season level, each position wins 9 of
10 test seasons. The mean combined season lift is 12.1861 points.

### Source, license, identity, and current role gates

- Draft, player-registry, and 14 seasonal-stat assets all match their immutable
  completion-manifest hashes (16 assets checked, 0 mismatches).
- All three snapshot manifests are complete, immutable, and
  `ADMITTED_PRIMARY_SOURCE`.
- All three license receipts are `CC-BY-4.0` and
  `TERMS_ACCEPTED_FOR_RESEARCH_WITH_ATTRIBUTION`.
- Retrieval timestamp is `2026-07-30T07:24:07Z`, ten calendar days before the
  packet date and inside the existing 30-day boundary.
- Current drafted skill-player rows: 80.
- Exact PFR-ID bridges: 73; unique exact normalized-name+position bridges: 7;
  duplicate current IDs: 0.
- Eligible projections: 78 (77 ACT, 1 RES).
- Blocked: Max Bredeson (draft TE/current RB) and Riley Nowakowski (draft
  TE/current FB). No position conflict is coerced.
- No structured 2026 depth chart exists in the admitted local evidence; none is
  invented. Draft capital is the only current workload proxy.

### Components, combined board, and presets

- Rookie positions: QB 10, RB 12, WR 36, TE 20.
- All granular components are finite and nonnegative.
- Games are within 0-17; availability equals games / 17.
- Completions do not exceed attempts; receptions do not exceed targets; first
  downs and touchdowns do not exceed their associated opportunities.
- Every corrected central half-PPR score is nonnegative and inside its bounds.
- The combined prefix exactly equals all 530 approved veteran rows across all
  17,490 cells; no approved veteran value changes.
- Combined positions: QB 84, RB 140, WR 243, TE 141; K/DST rows: 0; duplicate
  player IDs: 0.
- All four built-in presets are READY and rank all 608 rows.
- All five profile checks pass: Superflex QB rise, TE-premium TE rise, 3WR
  scarcity, 12-team QB depth, and extra-FLEX scarcity.

### Preservation and execution

- Candidate diff changes no dynasty, Unified Preview, Trading Lab, scheduler,
  profile, or installed-projection path.
- Trading Lab remains documented and implemented as manual-only.
- Scheduled task `NWR DynastyProcess Market Baseline Refresh` is Disabled.
- Canonical installed Redraft projection remains the approved 530-veteran file
  at SHA-256 `6ee6dbff41e238fb925c8d8d4b5e5079f48de71b132888e5c75fea34e9831c63`.
- Canonical saved Redraft profiles: 0; active profile receipt: absent.
- Focused tests: 47 passed.
- Ruff review scope: passed.
- Independent corrected rebuild reproduces the exact rookie and combined SHAs.

## Remaining Low limitations

- The model is intentionally coarse: players at the same position and draft
  round receive the same central line; exact pick within a round and team depth
  are not modeled.
- All rookie ranking rows correctly remain LOW confidence.
- One eligible player has current registry status RES; the model uses the
  explicitly allowed ACT/RES gate and makes no narrative availability claim.
- Uncertainty is a position-level walk-forward absolute-error p80, not a
  player-specific calibrated distribution.

These limitations are conspicuous, deterministic, and do not invalidate the
corrected review-only layer. They should remain visible during owner review and
draft-day use.
