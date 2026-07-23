# Validation results

Status: `CANONICAL_BUILD_SELF_VALIDATION_PASS`.

The authoritative builder validates all governed tracked-input hashes, exact
player-ID joins, historical feature metadata, the exactness lattice, the
924-row frozen comparator, the 240-row current board, and preserved metric and
challenger conclusions before the packet manifest is sealed.

- Fixed history anchor: `0929ce6ec058a698efeee10fe5770f56047bab21`.
- Exact rows: `0 / 5,518`.
- Exact seasons: `NONE`.
- Proxy-to-exact differential: `NOT TESTABLE`.
- Current board: 240 rows / `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`.
- Frozen comparator: 924 rows / `b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179`.
- Production ranking change: `NONE`.
- Frozen 2026 change: `NONE`.
- Challenger disposition: `NO_ACCURACY_CHALLENGER_ADMITTED`.

The independent mutation, clean-checkout, Hermetic, LocalData, security
regression, Data Health, and preservation gates are recorded in the separately
committed assertion/regeneration revision packet. This file is generated
atomically; no post-build correction is permitted.
