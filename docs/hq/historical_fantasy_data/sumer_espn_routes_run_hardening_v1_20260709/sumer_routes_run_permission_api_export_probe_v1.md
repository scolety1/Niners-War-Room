# Sumer Routes Run Permission/API/Export Probe V1

## Public Surfaces Checked

- WR stats page: https://sumersports.com/players/wide-receiver/
- TE stats page: https://sumersports.com/players/tight-end/
- RB stats page: https://sumersports.com/players/running-back/
- Terms of Service: https://sumersports.com/terms-of-service/
- End User License Agreement: https://sumersports.com/end-user-license-agreement/

This probe used only public, non-authenticated pages. It recorded field names, status codes, and row/field counts. It did not copy raw player rows into the repository.

## Visible Route Fields

WR and TE pages visibly expose:

- `Routes Run`
- `Targets/Route Run`
- `YPRR`

The RB page does not visibly expose those route columns. Its visible table includes rushing and receiving usage fields such as rushes, rushing yards, receptions, receiving yards, receiving touchdowns, YAC, and target share.

## Payload Field Probe

Public page payload probes observed the following fields for 2022-2025 WR, TE, and RB pages:

- `sumerPlayerId`
- `receivingPassRoutesRun`
- `receivingTargetsPerRouteRun`
- `receivingYardsPerRouteRun`

The 2017-2021 public page probes returned page shells but no observed route payload rows for WR, TE, or RB.

## Coverage Summary

| Position | Visible route columns | Payload route fields observed | Seasons with route payload rows | Seasons without route payload rows |
| --- | --- | --- | --- | --- |
| WR | yes | yes | 2022-2025 | 2017-2021 |
| TE | yes | yes | 2022-2025 | 2017-2021 |
| RB | no | yes | 2022-2025 | 2017-2021 |

## API/Export Findings

No public documented SumerSports route data API was found. No public bulk CSV, parquet, database dump, or download link was found. The only reproducible public path found in this lane is the rendered page/page payload surface.

The page surface is stable enough to remain a lead, but not stable or licensed enough to be a candidate. RB route fields are especially sensitive because they appear in the payload but not the visible table.

## Permission and Terms Findings

Sumer's Terms of Service state that Sumer owns the Sumer Platform content and does not grant rights except as expressly authorized. The terms restrict selling, licensing, copying, publishing, modifying, reproducing, distributing, creating derivative works from, publicly displaying, using, or exploiting Sumer Content except as authorized.

The same terms restrict robots, spiders, automated retrieval, copying, scraping, indexing, reverse engineering, mining, and excessive automated access unless expressly permitted. The EULA has similar restrictions on data made available through Sumer software.

## Identity Fields

`sumerPlayerId` is a plausible provider identity field. It is not yet NWR-safe because:

- No official Sumer player ID dictionary was found.
- No public Sumer-to-GSIS/ESPN/NWR crosswalk was found.
- Name/team/season fallback joins are not approved.

## Classification

`YELLOW_ROUTE_DENOMINATOR_LEAD`

Sumer has actual route-denominator-like fields and WR/TE visible route columns. It does not satisfy the GREEN gate because permission-safe use, documented API/export, historical depth, RB support confirmation, and identity crosswalk remain unresolved.

## What Would Unblock Sumer

1. Written permission or public license allowing NWR to use route fields.
2. Documented route stats API, export, or static data product.
3. Provider field dictionary for `receivingPassRoutesRun`, `receivingTargetsPerRouteRun`, and `receivingYardsPerRouteRun`.
4. Confirmation that RB payload route fields are supported and intentionally provided.
5. Season coverage documentation, especially whether route data begins in 2022.
6. Player identity crosswalk from `sumerPlayerId` to an admitted NWR identifier.
7. Missingness/coverage audit by season, team, and position.
