# Current Canonical State

Canonicalization was re-performed after fetching and pruning origin on 2026-07-31 for Phase 1A.

- Live branch: work/hq-parallel-control
- Live HQ before Phase 1A: 79b62c3993cf1d00c6dc068199826abb6d9954e3
- Live tree before Phase 1A: 8c74b2c5cc497f1d1e827620e264f2b7d47e2cfd
- Advances since the previously expected HQ: exactly the two Golden Lane documentation commits 8c74b2c and 79b62c3
- Stable checkout before this packet: clean at the exact live HQ and tree
- Operational checkout: clean on work/nfl-usage-target-backtest-v0 at dc5ff68c172f7a5a49755934d122ee1f99d87670; not updated

## Unified-board result consumed by Phase 0

The completed review exists on implementation commit c422d86b4b9c2b97c88b2a571e349f3c059904ae and independently adopted commit 682b904666532bca7ee505858cc5bf54271e8fdd. Its verdict is BLOCKED_NWR_ROOKIE_OR_VETERAN_COMMON_SCALE: rookie survival/bust calibration and veteran Y3 discrimination failed their gates. It produced no unified player ranking and no product integration.

Golden Lane disposition: PHASE_0_GREEN_COMMON_SCALE_REJECTED_EXISTING_AUTHORITIES_RETAINED. A null common-scale result is compatible with completion. The failed result is closed as evidence; no calibration rerun is authorized by this packet.

## Preserved authority

- Finished V1: 240 current players; SHA-256 263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4.
- Outcome V3: 17,280 rows; stable authoritative SHA-256 e3b44047d36bd62d9573295db64d96f214922a20f0083cf49105f104970b3d20.
- Model V4 2026 Rookie Review: 73 scored and 7 blocked; governed digest cd5ff629dcf159950e3f23dc75bbb713c225dd4c7e7bffe2a5496e209a231f70.
- Frozen comparator SHA-256: b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179.
- Opaque artifacts: 5/5 hash matches.
- Persistent state: 14 files, 542801 bytes, digest 88d1a981d514e6519e328efa639e80e51c4ae0379f046e3e3ee55acef1f82987.
- Recovery state: 7 files, 172878 bytes, digest 1fbd0b5097b240ed43a21be111926480ed4a97f558f033b8fea68e5c42604835.

The fresh Golden Lane worktree exposes the known checkout-only Outcome V3 line-ending hash a8b468c13a68c8c2feecaf55440982615099019cde8c1963e48068eed01a87cb. Stable retains the exact authoritative bytes. Phase 1B, not Phase 0, owns resolution under a Data Hygiene contract.

The NWR DynastyProcess Market Baseline Refresh scheduled task is disabled. No provider-refresh, rookie-builder, or ranking-builder process was running. Launcher state was not changed.

## Phase 1B starting state

Phase 1B began after the bounded-autopilot controller was independently adopted
and canonicalized at `99eff4f3a91b9428ed5958c72dbf281cf6c4de05`. Its starting
tree was `a74c3eb5616a5f2b083496b139c7c5b9f3b17629`; remote divergence was
0 ahead / 0 behind and stable was clean at the same HQ. Operational remained
clean on `work/nfl-usage-target-backtest-v0` and was not updated.

The exact 14 Phase 1A source hashes remain immutable. Phase 1B added only
fail-closed hygiene contracts, validator/tests, and a scoped LF checkout rule
that restores the already governed Outcome V3 blob bytes in fresh worktrees.

## Phase 2 contract result

Phase 2 began from canonical HQ `12e8871e14ec2d520fd0a3cf3b4664174e1b29ab`
and tree `7e28ba7d145089c523be2a2a89db6d292c07ab11`, with zero remote
divergence and a clean stable checkout. It admitted no new data or model output.

The lane froze the exact scoring and eligible population, separate Win Now,
two-year, and three-year target contracts, review-only positional replacement
references, lifecycle strata, horizon-aware chronological folds, deterministic
ties, support thresholds, and fail-closed missingness. Its 94-row synthetic
persistence fixture produced four deterministic review-only baseline rows with
SHA-256 `c71bff8b924bd1e02f0c65fabe51d368c595d1effa0702c7ddf7ce833dcd0979`
in two disposable roots. Production and user state were not touched.

## Phase 3 gauntlet result

Phase 3 began from canonical HQ `e92e5d17d83cfd4af23591e6632dbe6229310f14`
and tree `4543f190e07e001567aaa969e1c848bb9c9a6c81`. It evaluated five
preregistered review-only feature families on the exact 5,518-row Formula Data
Mart across 39 applicable position and separate target-horizon cells. No family
cleared every chronological, support, bootstrap, Holm, replacement-precision,
productive-veteran, and low-games gate. The result is the accepted truthful null
`NULL_NO_FAMILY_PASSED`; no model or ranking authority changed.
