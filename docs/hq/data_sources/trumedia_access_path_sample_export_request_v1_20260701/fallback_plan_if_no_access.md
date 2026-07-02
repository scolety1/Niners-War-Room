# Fallback Plan If No Access

If TruMedia declines access, does not respond, or cannot license NWR's intended use, NWR should treat the requested field families as unresolved licensed gaps.

## Immediate Fallback

- Keep routes, TPRR, YPRR, route type, tracking-derived separation, defender matchup, and coverage fields `BLOCKED_LICENSED_GAP`.
- Do not create route proxies from snaps, participation, or targets.
- Do not infer separation or coverage from public play-by-play.
- Do not promote any replacement field to source truth.

## Review-Only Existing Sources

- Existing NWR nflverse/Sleeper source-admission artifacts may continue to support review-only usage and red-zone context where already documented.
- PBP-derived red-zone counts may remain review-only validation/fallback artifacts only when built by an approved source-governance lane.
- Existing source-contract and missingness policies continue to block zero-fill and route proxies.

## Alternate Acquisition Paths

If TruMedia is unavailable, a future acquisition lane can separately evaluate other legitimate vendors or public datasets under the same rules:

- Written rights first.
- Sample export before integration.
- Field-level source and license matrix.
- Explicit zero/missing semantics.
- No app/model/rank/source-truth behavior changes.

## Stop Conditions

- Any request for credential reuse.
- Any login-wall scraping requirement.
- Any unclear right to store sample data locally.
- Any vendor restriction against private derived artifacts.
- Any inability to distinguish missing from true zero for routes, targets, snaps, or red-zone opportunities.

