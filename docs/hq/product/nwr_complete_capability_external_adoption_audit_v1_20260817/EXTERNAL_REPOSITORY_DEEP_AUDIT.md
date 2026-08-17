# External Repository Deep Audit

Selection followed the requested high-signal stopping rule. Nine repositories were shallow-cloned to a disposable directory and inspected at exact commits; official provider pages were checked separately. No external code was copied.

## Deep findings

### `zacharykirby/ai-nfl-fantasy-draft` — `233d18e...` — MIT

Strongest board/state architecture: domain-separated board/session/recommendation layers; snake pick ownership; every-team rosters; event-backed autosave; undo/recovery; duplicate prevention; deterministic fallback; tier cliffs, position runs and next-pick survival; broad tests. NWR should adapt the pattern while retaining NWR projections, identities, storage and authority labels. A later lane may review isolated MIT code for `COPY_WITH_ATTRIBUTION`, but this audit authorizes no copying.

### `joewlos/fantasy_football_monte_carlo_draft_simulator` — `2e33e3f...` — MIT

Uses league historical pick/position data to fit logistic opponent-pick behavior, simulates snake drafts and randomizes roster outcomes. Useful for ADP survival and CPU realism concepts. It is a 2024 work in progress, has sparse/no visible tests and needs owner-supplied datasets/configuration. Adapt and simplify; do not adopt wholesale or train before data gates exist.

### `VTNoble/adp-vs-projection` — `f5caf6a...` — no license

Shows the basic projection-rank minus Sleeper-App-ADP concept using 2022 notebooks and snapshots. It does not establish a current supported Sleeper ADP endpoint or usable license. Concept is already obvious; reject code/data/provider.

### `aptmac/fftiers-python` — `57877b5...` — no license

Old Python 3.4 workflow, FantasyPros credential/scraping assumptions and hard-coded KMeans cluster counts. It demonstrates why forced `k` produces presentation tiers rather than governed evidence. Reject.

### `playjukeff/wire-room` — `82eab68...` — no license

The strongest waiver concept: derive actually unrostered players, compute optimal legal lineups, evaluate add/drop pairs by weekly lineup-point improvement, and model claim priority/probability/sequencing. No license and little/no test structure means no code reuse. Rebuild the pattern with NWR contracts and explicit uncertainty.

### `evanng07/FantasyFootballOptimizer` — `89d8dc9...` — no license

The React app largely displays projection rows and contains no credible optimization engine. Reject.

### `mattkjones/4-keeper-sleeper-ff-trade-machine` — `57f23f3...` — MIT

Small Streamlit program that imports Sleeper rosters/picks, calls FantasyCalc values, enumerates packages and applies arbitrary keeper/consolidation adjustments. NWR's trade authority is materially stronger. Adapt only the opponent-roster target/package-search interaction; reject its valuation logic.

### `gtonic/nfl_mcp` — `ae5553d...` — MIT

Current, broad and well-tested (roughly 68 test files) tool catalog across drafts, lineups, streaming, waivers, injuries, schedules, opponents and transactions. It is valuable as a missing-workflow discovery checklist and provider-isolation example. Claims such as projection/trade/FAAB quality require independent validation. Do not replace NWR with an MCP shell or import its combined heuristics as authority.

### `nflverse/nflverse-data` — `9037aa8...` — CC BY 4.0

Current automated data-release repository. NWR already uses nflverse; keep governed, hashed snapshot ingestion and attribution. Individual upstream datasets/packages can carry different terms, so approve sources dataset by dataset.

## Stop rationale

These repositories supplied sufficient evidence for draft state, opponent behavior, tiers, waivers, lineups, trade search, assistant workflow coverage and core data. Remaining named projects were category-triaged; deep inspection would not justify the audit cost absent a specific unresolved architecture question.
