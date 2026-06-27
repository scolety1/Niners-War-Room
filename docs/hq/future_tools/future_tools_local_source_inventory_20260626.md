# Future Tools Local Source Inventory - 2026-06-26

This inventory is intentionally conservative. It records what NWR can reference for Future Tools R&D without making those sources active model inputs or decision-page wiring.

## Approved Or Safe For Display/Review

- Sleeper league/draft/runtime context: useful for league, roster, draft, and trade-event display once local state or official API pulls are explicitly in scope. It is not a valuation engine.
- Live Draft V2 runtime state and event log: manual/local draft evidence only. It can support audit and checklist scaffolds but is not official source truth.
- Dynasty Rankings / Frozen baseline checkpoint: existing display/rank context only. Future Tools cannot mutate ranks, tiers, Dynasty Rank, or Final Board Rank.
- DynastyProcess market baseline: display-only market sanity. It cannot drive hidden sort, trade value, model value, or recommendations.
- Evidence registry and review pages: safe for status labels and gate state.

## Review-Only Or Blocked

- CFBD review artifacts and identity matching: review-only. `model_use_allowed=false`, `training_allowed=false`, and human approval gates remain required.
- NFL usage evidence: review-only/model-candidate pending manual gate. It is not an active feature source.
- Unified player universe: review-only with app/model wiring blocked unless a later gate explicitly opens it.
- Historical/proxy drop evidence: sensitivity/review only, not training truth.
- Outcome artifacts: display context only where already approved; missing outcome remains `Not enough information`.

## Manual, Privacy-Gated, Or Forbidden For This Lane

- Gmail/league-history emails: privacy-gated review evidence only. No raw email bodies or automation in this lane.
- RotoWire/FantasyPros/vendor exports: blocked/manual unless a separate source policy and licensed path is approved. No scraping.
- Raw CFBD/nflverse caches, `C:\NWR_SHARED_DATA`, `C:\NWR_LOCAL_SECRETS`, and `local_exports`: must not be tracked.

## External Source Notes

- Sleeper documents a free read-only HTTP API for public user, league, roster, draft, pick, and traded-pick data: https://docs.sleeper.com/
- nflreadpy is the Python nflverse loader path for public NFL data and caching: https://github.com/nflverse/nflreadpy
- nflreadr documents play-by-play availability from nflverse data and snap counts from PFR: https://rdrr.io/cran/nflreadr/man/load_pbp.html and https://rdrr.io/cran/nflreadr/man/load_snap_counts.html
- CollegeFootballData provides API/export access for college football data and requires an API key: https://collegefootballdata.com/
- DynastyProcess data is useful for market context only and remains display-only in NWR: https://github.com/dynastyprocess/data

## Safe R&D Conclusion

The only safe near-term Future Tools work is roadmap/spec/status UI plus framework-only checklists or inventory shells. Any active start/sit, waiver, in-season ranking, trade target, rookie class, class-strength, or playoff planning output requires a separate model/data/source-truth gate.
