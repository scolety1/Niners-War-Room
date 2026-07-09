# True YPRR TPRR Blocked Reason V1

## Final Blocked Status

True YPRR and true TPRR remain blocked because NWR does not have an admitted, legal, reproducible, identity-safe `routes_run` denominator source.

## Formula Understanding Is Not The Blocker

The formulas are straightforward:

- `YPRR = receiving_yards / routes_run`
- `TPRR = targets / routes_run`

The blocker is not metric definition. The blocker is source admission.

## Missing Admission Requirements

No candidate currently satisfies all of the following:

- actual player-level `routes_run`
- public, licensed, or otherwise permission-safe use
- stable API, export, static file, or supported delivery path
- historical coverage suitable for NWR review
- WR, TE, and RB coverage or documented omissions
- stable player identity fields beyond name-only joins
- team, season, position, and grain documentation
- field dictionary
- missingness and eligibility documentation
- provenance, checksum, schema version, or source update timestamp
- allowed internal storage
- allowed derived YPRR and TPRR computation
- redistribution, display, and model-use restrictions documented

## Why Leads Remain Blocked

SumerSports and ESPN are meaningful route-denominator leads, but neither clears permission/export/API gates. Sumer remains blocked by lack of supported admitted export/API, unresolved terms, and identity crosswalk risk. ESPN remains blocked by undocumented client-object status and Disney terms/permission risk, even though prior probes indicated strong identity fields.

PlayerProfiler and commercial providers remain contractable or proprietary leads only. nflverse participation, snaps, pass attempts, and primary-receiver route labels are not full player-level route denominators.

## Production Rule

Do not calculate or display production YPRR or TPRR from these leads. Do not use route-like payload fields, screenshots, client objects, public display rows, paywalled feeds, or proxies as route source truth.

True YPRR and TPRR may become derivable only after a separate source-admission lane admits a real `routes_run` feed.
