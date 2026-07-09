# SumerSports Routes Run Hardening Probe V2B

## Scope

Public pages inspected:

- WR: https://sumersports.com/players/wide-receiver/
- TE: https://sumersports.com/players/tight-end/
- RB: https://sumersports.com/players/running-back/
- Terms: https://sumersports.com/terms-of-service/

This probe was schema-only. No raw player table was copied into the repository.

## Visible Surface

WR and TE public stats pages visibly expose:

- `Routes Run`
- `Targets/Route Run`
- `YPRR`

RB public stats pages do not visibly expose route columns in the table surface. The visible RB surface emphasizes rushing and receiving usage such as rushes, yards, YPC, YAC, target share, and touchdowns.

## Payload Fields Observed

Public page payload probes found these route-denominator-like fields:

- `sumerPlayerId`
- `receivingPassRoutesRun`
- `receivingTargetsPerRouteRun`
- `receivingYardsPerRouteRun`

Observed schema counts by position/season query:

| Position | Seasons with route payload rows observed | Seasons probed without route payload rows |
| --- | --- | --- |
| WR | 2022, 2023, 2024, 2025 | 2017, 2018, 2019, 2020, 2021 |
| TE | 2022, 2023, 2024, 2025 | 2017, 2018, 2019, 2020, 2021 |
| RB | 2022, 2023, 2024, 2025 | 2017, 2018, 2019, 2020, 2021 |

Important RB note: `receivingPassRoutesRun`, `receivingTargetsPerRouteRun`, and `receivingYardsPerRouteRun` were observed in the RB page payload for 2022-2025 even though the RB page does not visibly display route columns. This makes Sumer a possible full pass-catcher coverage lead, but only as a lead.

## Readiness Gates

| Gate | WR | TE | RB | Status |
| --- | --- | --- | --- | --- |
| Actual player-level routes_run-like field | yes | yes | yes in payload | lead only |
| Visible route count field | yes | yes | no | partial |
| Historical seasons | 2022-2025 observed | 2022-2025 observed | 2022-2025 observed | partial |
| Stable player ID | `sumerPlayerId` observed | `sumerPlayerId` observed | `sumerPlayerId` observed | needs NWR crosswalk |
| Documented public API/export | no | no | no | blocked |
| Permission-safe automated retrieval | no | no | no | blocked |
| Missingness measurable | not yet | not yet | not yet | blocked |
| Approved NWR identity join | no | no | no | blocked |

## Terms and Licensing Risk

SumerSports terms state that Sumer owns its content except where expressly authorized and restrict automated access, retrieval, scraping, copying, indexing, and related reuse. The lane found no public license, bulk export, or documented API permission allowing NWR to reproduce this dataset.

## Classification

`YELLOW_ROUTE_DENOMINATOR_LEAD`

Sumer is the strongest provider-family lead for 2022-2025 WR/TE/RB route denominator recovery, but it is not a green candidate because access, licensing, export/API, identity, and missingness gates remain unresolved.

## Required Hardening Before Admission

1. Written permission or documented public data license for route fields.
2. Stable supported retrieval path, preferably documented API or export.
3. Sumer field dictionary for `receivingPassRoutesRun`, TPRR, and YPRR fields.
4. Season and position coverage table, including whether 2022 is the first available season.
5. NWR-safe identity crosswalk from `sumerPlayerId` to canonical player IDs.
6. Missingness audit by season, position, team, and player.
7. Confirmation that RB payload route fields are supported data, not incidental or deprecated client state.
