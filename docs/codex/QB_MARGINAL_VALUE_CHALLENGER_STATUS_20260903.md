# QB marginal-value CHALLENGER — status (extends the prior audit)

Follows up on `docs/codex/QB_MARGINAL_VALUE_AND_ROOKIE_CALIBRATION_AUDIT_20260903.md`'s
confirmed root cause: `_position_roster_limit` in
`redraft_engine_v1_service.py` derives the QB replacement baseline from
roster *capacity* (`roster_limits.QB=2` → depth `16×2=32`), not from how
many QBs actually *start* (`roster.qb=1`) — inflating QB rank across all
21 QBs the real KHA room drafted (mean implied-round gap −2.21, median
−3.75 rounds). The audit already found the codebase has a shallower,
format-aware baseline in one place
(`model_v4_replacement_vorp_core_service.py`'s
`configured_replacement_rank`, e.g. `12` for a 10-team 1QB league) that
the live `generate_rankings()` path does not use.

## Why a real CHALLENGER (mirroring the rookie one) is not built this pass

The rookie market-blend challenger (section 17) could be built and
backtested with only ordinal `nwr_rank`/`espn_adp` — no raw projection
magnitude was needed. A genuine QB replacement-baseline challenger is a
different shape of problem: `calculate_replacement_levels()` needs each
QB's real *projected points* (`ProjectionPlayer` scored values) to
recompute what a shallower replacement depth would actually produce —
recomputing "what rank would QB #14 get under depth=16 instead of
depth=32" requires the real point differentials, not just draft-order
evidence. That data lives only in the governed 2026 projection snapshot,
which `docs/codex/PLAYER_UNIVERSE_SATURDAY_RENEWAL_PACKET.md` already
concluded must not be reused beyond the single completed 2026-09-02
draft without fresh owner approval. Unlike the KHA shadow replay (which
could substitute a disclosed rank-derived value proxy and still
demonstrate real, meaningful Team Score behavior), a replacement-level
recomputation with a fabricated point-value proxy would not actually
test the real formula defect — it would produce a number that looks
like a validation but isn't one, which is worse than not building it.

## What is ready the moment real data exists

The fix direction is already evidenced in-repo
(`model_v4_replacement_vorp_core_service.py`'s shallower baseline) and
the evaluation methodology is already proven on the rookie challenger:
compute the CHAMPION's real replacement level (unchanged,
`calculate_replacement_levels` as shipped) and a CHALLENGER's (same
function, called with a shallower configured QB depth — e.g. team_count
× 1 instead of × 2, requiring no formula rewrite, only a different
`profile.draft.roster_limits.QB` input), backtest both against the real
21-QB KHA draft-round evidence the same way
`backtest_against_real_outcomes` already does for rookies, then
register the result in `champion_challenger_registry_service.py` before
any promotion decision. Not attempted tonight because it needs the real
projection magnitudes this environment does not currently have lawful
access to.
