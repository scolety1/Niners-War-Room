# NWR System Audit PFR RB Broken Tackle Addendum V1

## Verdict

`GREEN_SYSTEM_AUDIT_PFR_RB_BROKEN_TACKLE_ADDENDUM_READY`

## Clear Answer

This addendum preserves a narrow PFR RB broken-tackle review-only hypothesis without changing the Full System Audit conclusion. PFR advanced stats are public/reproducible nflverse PFR advanced stat parquet releases, not proprietary PFF data, but PFR is still not production-approved in NWR.

Only one PFR item should carry forward:

`PFR_RB_BROKEN_TACKLE_CONTEXT_REVIEW_ONLY`

Allowed RB-only review variants:

- `pfr_rush_brk_tkl__raw`
- `pfr_rush_brk_tkl__per_game`

Diagnostic only:

- `pfr_rush_brk_tkl__per_attempt`

Blocked:

- PFF Elusive Rating
- `nwr_elusive_proxy_review_only`
- PFF-style elusive/proxy naming
- broad PFR production use
- PFR QB passing as production input
- broad WR/TE PFR feature sets unless separately reopened by Master HQ

## Source Clarification

The PFR advanced stats referenced here came from nflverse public PFR advanced stat parquet releases:

- `advstats_season_pass`
- `advstats_season_rush`
- `advstats_season_rec`

The prior source provenance packet hardened the public PFR/nflverse source endpoint and recorded a PFR rushing source SHA. This addendum does not add raw parquet files or caches to git.

## Evidence Preserved

The prior PFR RB readiness/design chain found weak positive full-control lift:

| Variant | Full-Control Lift | Status | Interpretation |
| --- | ---: | --- | --- |
| `pfr_rush_brk_tkl__raw` | `+0.001531` | review-only primary | Tiny signal. Worth preserving as context, not as a winner. |
| `pfr_rush_brk_tkl__per_game` | `+0.000651` | review-only primary | Tiny signal. Worth preserving as context, not as a winner. |
| `pfr_rush_brk_tkl__per_attempt` | not preserved as primary | diagnostic only | Parked unless separately approved. |

## Formula Gauntlet Readiness Impact

This addendum does not change Formula Gauntlet readiness.

Current readiness remains:

`CLEARED_FOR_REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`

Still blocked:

- 100-candidate Formula Gauntlet
- champion refinement
- rankings integration
- production model use
- source-truth promotion

The addendum only adds a clearer inventory/status note so future Formula Gauntlet or Data Hygiene lanes do not reinvent or misclassify the PFR RB broken-tackle evidence.

## Production Status

No production use is approved by this packet.

PFR remains review-only unless a later Master HQ source-admission lane explicitly approves otherwise. PFF Elusive Rating and `nwr_elusive_proxy_review_only` remain blocked and must not be calculated, displayed, or used as substitutes for this narrow PFR RB context hypothesis.

## Recommended Next Lane

Keep this as evidence-ingestion context. The next practical lane remains Data Hygiene receipt locator/ledger work, not Formula Gauntlet execution. If Master HQ later approves a bounded component-signal contract, this addendum can feed an RB-only broken-tackle context slice that must compare against PYF and control for rushing volume/prior production.
