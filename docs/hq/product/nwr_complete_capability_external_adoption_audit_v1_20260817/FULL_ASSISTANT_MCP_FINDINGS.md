# Full Assistant / MCP Findings

`gtonic/nfl_mcp` at `ae5553d...` is the strongest broad assistant repository inspected: current, MIT, approximately 70 tools and roughly 68 test files. Its catalog spans draft boards/mocks, start-sit/full lineups, streamers, waiver/FAAB, injuries, schedules/weather, opponent analysis, transactions and playoff planning.

## Use

Use it as a workflow-discovery checklist, provider-isolation example, and evidence that tool contracts/evals deserve first-class tests. It exposed missing NWR owner workflows recorded in `MISSING_CAPABILITIES_DISCOVERED_FROM_EXTERNAL_ASSISTANTS.md`.

## Do not use

Do not turn NWR into a generic MCP-first assistant or adopt bundled claims/heuristics as canonical truth. NWR's deterministic owner UI, local state and separate analytical authorities remain the product. Any future assistant is a read-only explanatory/query surface over the same application services, with a bounded evidence packet, allowlisted entities and deterministic fallback.

No assistant may mutate Sleeper, owner state, ranks or draft availability without the same validated application command used by the UI.
