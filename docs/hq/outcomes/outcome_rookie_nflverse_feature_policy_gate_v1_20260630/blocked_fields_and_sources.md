# Blocked Fields And Sources

Verdict: `YELLOW_BLOCKLIST_LOCKED_NO_PROMOTION`

This packet preserves all blocked-source and blocked-field guardrails. Nothing listed here is promoted to model input, training input, source truth, rank logic, hidden sort, valuation, recommendation logic, or app behavior.

## Blocked Sources

The following remain blocked for Outcome/Rookie model or training use:

- `ff_rankings`;
- market data;
- ADP;
- DynastyProcess;
- CFBD joins;
- UDFA status without explicit approved source evidence;
- Gmail/private/vendor/local export inputs;
- raw/shared/cache/local export files;
- `latest_candidate`;
- `latest_approved`.

## Blocked Or Non-Eligible Feature Families

- contract context as valuation or player value;
- `games_missed_while_rostered`;
- CFBD joins;
- UDFA status;
- `ff_rankings`;
- market / ADP / DynastyProcess;
- injury context as injury risk or medical projection;
- schedule context as recommendation or matchup strength;
- depth chart context as pre-draft feature without replay;
- player_stats sidecar as label truth without parity.

## Missingness Blocks

Missing values remain `Not enough information`.

They are never:

- zero;
- false;
- healthy;
- clean;
- low risk;
- no-role;
- no-usage;
- confirmed UDFA;
- missed game;
- played game;
- favorable schedule;
- negative outcome.

## Identity Blocks

The 13 remaining identity rows remain gated. Kentrel Bullock and Jamal Haynes remain gated pending NWR/Sleeper binding review. Chip Trayanum remains a future human-confirmation candidate only.

Manual evidence does not become an approved identity join, source truth, model input, rank input, or binding approval without a later explicit approval lane.

## Outcome/Rookie Blocks

- Outcome V2 probabilities do not change.
- Rookie probabilities are not approved.
- Gate G remains blocked.
- UDFA modeling remains blocked.
- CFBD model/training input remains blocked.
- No new Outcome/Rookie label or sidecar source is promoted.
