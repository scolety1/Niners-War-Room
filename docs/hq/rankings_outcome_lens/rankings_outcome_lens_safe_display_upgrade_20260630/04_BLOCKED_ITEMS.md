# Blocked Items

The following are blocked for this lane:

- Missing data as `0%`, `false`, clean health, no injury, no usage, or no role.
- Fake Outcome columns or unvalidated probability heads.
- Hidden sort by Outcome, market, injury, depth, snap, rookie, or nflverse context.
- Market, ADP, or DynastyProcess as model/rank input or private value.
- DynastyProcess/ADP as trade value or pick value.
- Rookie Gate G wiring without explicit GREEN approval.
- Injury risk score, medical risk, recovery projection, comeback probability, healthy-now label, or injury discount.
- Trade/pick valuation logic.
- FootballDB scraping.
- Vendor/Gmail/FantasyPros/RotoWire/private data.
- Raw/cache/shared/local/secrets tracked in Git.
- `latest_candidate` or `latest_approved` writes.
- Live Draft Room or Mock Draft behavior changes.
