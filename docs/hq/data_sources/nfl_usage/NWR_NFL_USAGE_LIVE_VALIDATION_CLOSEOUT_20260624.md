# NFL Usage Live Validation Closeout

## Verdict

GREEN. Live source smoke, field inventory, schema fingerprints, review artifacts, validation, and field-level quarantine reports are complete and safe.

## Sources GREEN

- player_stats
- snap_counts
- pbp
- nextgen_stats passing/receiving/rushing
- participation
- ftn_charting
- pfr_advstats pass/rush/rec
- rosters
- players
- ff_playerids

## Inventory-Only / Proxy-Only Sources

- NGS fields remain inventory/review-only.
- FTN charting remains inventory/review-only with attribution.
- PFR advanced stats remain inventory/review-only with attribution.
- Participation route-like fields remain proxy-only.

## Quarantined Fields

The live schema contains 14 field-level quarantines. These are blocked or non-evidence fields such as fantasy point fields and score-state fields. Quarantine status means they are not accepted evidence and cannot be used for model input, app wiring, rankings, or source truth.

## Licensed-Data Gaps

- true routes run
- true TPRR
- true YPRR

## Guardrails

- Raw data tracked: no
- App/model flags: no
- latest_candidate/latest_approved: untouched
- Frozen board: unchanged
- Pinned snapshot: unchanged
