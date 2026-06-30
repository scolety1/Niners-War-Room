# Leakage Blocklist

## Blocked Source Patterns

| Source pattern | Examples | Why blocked |
| --- | --- | --- |
| Future NFL production | NFL passing/rushing/receiving stats, fantasy points after prediction date | Direct target leakage. |
| NFL usage after prediction date | games, starts, snaps, routes, carries, targets | Future opportunity/result information. |
| Career summaries | seasons played, final NFL season, career games | Career survival outcome. |
| Value summaries | career AV, weighted AV, draft AV | Future performance summary. |
| Awards | Pro Bowl, All-Pro, Hall of Fame | Future accolade/outcome. |
| Market/projection inputs | ADP, rankings, projections, DynastyProcess value | Market/projection leakage unless separately display-only. |
| Vendor/private/scraped data | Gmail, RotoWire, FantasyPros, FootballDB, vendor files | Explicitly blocked from scraping and model promotion. |
| Outcome V2 labels as features | hit/miss labels, position finish, fantasy points | Labels are evaluation targets only. |
| Ambiguous CFBD joins | fuzzy name match, same-name candidate, school mismatch | Identity risk can attach wrong production. |
| Missing-data coercion | missing becomes 0, false, clean, healthy, low-risk, undrafted, pick 0 | Converts absence of evidence into evidence. |

## Draft Context Split

- Pre-draft models must not use round, overall pick, draft team, landing spot, NFL depth chart, or
  any NFL result after prediction date.
- Post-draft models may use factual draft capital after the draft, but still cannot use future NFL
  production, career outcomes, market/projection data, or labels as inputs.
