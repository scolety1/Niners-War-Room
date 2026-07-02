# Public Access Findings

Research date: `2026-07-02`

Method: public web pages only. No TruMedia login, API call, credential lookup, private document, or behind-login scraping was used.

## Public Evidence

| Source | Public finding | NWR interpretation |
|---|---|---|
| [TruMedia home](https://www.trumedianetworks.com/) | TruMedia describes products for teams and media clients, with API availability for media external applications and a public email address. | Access is likely business-to-business. The public route is contact/demo, not self-service API signup. |
| [TruMedia teams page](https://www.trumedianetworks.com/teams) | The teams page says more information, demo, or trial inquiries should be emailed to TruMedia. | NWR should use the public email route and request a rights-cleared evaluation path. |
| [TruMedia football page](https://www.trumedianetworks.com/football) | TruMedia says its football platform merges data, video, and player tracking; metrics and models are available in UI and API; `NFL Core`, `NFL Advanced Analytics`, and `NFL API` are separate product concepts. | NWR's requested routes/tracking/coverage fields are most likely under Advanced Analytics, NFL API, data warehouse, or partner export rather than a public feed. |
| [TruMedia data warehouse page](https://www.trumedianetworks.com/nextgen-data-warehousing) | TruMedia describes a sports data warehouse with Sports SQL, large-field ingestion, and access controls based on each client's third-party licensing rights. | Export rights and available fields likely depend on customer license and third-party rights. NWR must ask about permitted local storage and derived artifacts. |
| [TruMedia Terms of Use](https://www.trumedianetworks.com/terms-of-use) | Terms require a Customer License or written authorization for access, restrict use of TruMedia content files absent license permission, describe evaluation/trial designations, require credential confidentiality, and prohibit data mining or robots against the services. | Do not scrape, automate, or access TruMedia systems without written authorization. If trial access exists, it is only for the purpose TruMedia states. |
| [TruMedia MLB API help docs](https://baseball.help.trumedianetworks.com/baseball/api-documentation-using-r) | Public baseball help docs describe a TruMedia-provided master token, temporary tokens, CSV/JSON output, and multiple row formats. | This is not NFL documentation and must not be treated as NFL access approval. It does show a general TruMedia pattern: tokens are provided by TruMedia and should remain private. |
| [TruMedia MLB Data Pro docs](https://baseball.help.trumedianetworks.com/baseball/data-pro-api-docs) | The public Data Pro page says those APIs are only available to MLB Team Data Pro customers. | Even public help docs can describe customer-only API access. NWR should assume NFL API access requires approval. |
| [SkillCorner American football page](https://skillcorner.com/us/sports/american-football) | SkillCorner describes American football data delivered through API or TruMedia front-end integration, with PFF and GSIS IDs, 10 seasons, tracking, contextual data, separation, and XY tracking. | A partner-export route may exist for PFF/GSIS IDs and tracking fields, but TruMedia/SkillCorner rights must be confirmed in writing. |
| [ESPN 2016 article](https://www.espn.com/nfl/story/_/id/17655038/finding-nfl-next-breakout-players-small-sample-size-all-stars-2016) | Public ESPN text cites TruMedia for receiver routes run and target-per-route style analysis. | Public media usage supports that routes/run and TPRR-like metrics exist in at least some TruMedia-enabled workflows. It does not prove NWR export rights. |
| [CBS Sports DK Metcalf article](https://www.cbssports.com/nfl/news/new-seahawks-coach-mike-macdonald-wants-to-make-dk-metcalf-a-moving-target-for-defenses/) | Public CBS text uses TruMedia/PFF-style alignment and yards-per-route analysis by inside/outside alignment. | Alignment and YPRR-style splits appear available to some media workflows. Exportability still needs confirmation. |
| [TruMedia CBS in-the-news page](https://www.trumedianetworks.com/analytics-news/tag/CBS) | TruMedia republishes media snippets using TruMedia and PFF for coverage and route analysis. | Coverage and route families likely exist in research-platform context, but source ownership and allowed export must be clarified. |
| [The Baltimore Banner Hopkins article](https://www.thebanner.com/sports/ravens-nfl/deandre-hopkins-ravens-offense-lamar-jackson-free-agency-V7EQUB5ZJVDJXGRYVXDXHLWZWM/) | Public article cites TruMedia for target separation and route type distribution. | Separation and route-type fields appear plausible, but NWR should request schema proof and rights before use. |

## Findings

- TruMedia access appears legitimate only through customer approval, demo/trial, or written authorization.
- A public email route exists: `info@trumedianetworks.com`.
- No public NFL self-service API signup was found.
- No public NFL data dictionary with the requested export fields was found.
- Public materials strongly indicate TruMedia combines play-by-play, video, player tracking, tagging, advanced models, and third-party data.
- Public materials do not prove NWR can store, derive from, train on, or privately use TruMedia data without a Customer License.
- Public materials support asking about PFF/GSIS IDs and partner exports; they do not support assuming Sleeper IDs are available.

## Source-Admission Posture

All TruMedia fields remain `BLOCKED_LICENSED_GAP` or `REVIEW_ONLY_PENDING_RIGHTS` until TruMedia provides written rights, a schema dictionary, zero/missing semantics, export grains, and a sample export that NWR is permitted to inspect.

