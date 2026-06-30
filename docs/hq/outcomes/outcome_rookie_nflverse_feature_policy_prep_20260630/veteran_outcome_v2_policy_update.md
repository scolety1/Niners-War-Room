# Veteran Outcome V2 Policy Update After NFLVerse Context Rebuild

## Executive Position

Outcome V2 probabilities do not change.

The rebuilt NFLVerse player context artifact improves review/display context
coverage, but it does not approve new Outcome probability columns, model input
promotion, training use, source-truth promotion, hidden sort, trade value, pick
value, or rank changes.

## Rebuilt Context

The tracked player context artifact now has:

- total rows: `294`
- safe display rows: `281`
- remaining gated rows: `13`
- newly bound review-only rows: `41`

The newly bound rows are identity bindings only. Non-identity context can still
be `Not enough information`.

## Display / Review Context

For safe rows, Veteran Outcome review may reference:

- roster and weekly roster status;
- injury report and practice status as caveats;
- schedule next game/opponent/bye context as display-only schedule context;
- depth chart role as current review/watchlist context;
- snap recency and last active season/week as factual activity context;
- draft capital and non-financial contract context;
- identity bridge health.

These fields cannot change current probabilities.

## Future Candidate Features

Future model or calibration work must go through explicit gates for:

- player_stats sidecar label parity;
- historical replay;
- as-of leakage;
- missingness handling;
- identity coverage;
- feature source policy;
- validation/calibration.

Until those gates pass, all NFLVerse context remains review/display-only.

## Blocked Uses

- New active probabilities.
- Rankings or app behavior changes from this packet.
- RB blocked fields activation.
- Injury risk, medical projection, or recovery projection.
- Depth chart as pre-draft feature without leakage gates.
- Future NFL production as pre-draft evidence.
- Missing data as zero, false, healthy, clean, no-role, or no-usage.
