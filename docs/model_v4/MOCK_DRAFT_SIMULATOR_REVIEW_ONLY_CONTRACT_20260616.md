# Mock Draft Simulator Review-Only Contract - 2026-06-16

## Scope
- Lane: `work/mock-draft-simulator`.
- Purpose: drop-day mock draft prep using the combined review pool of frozen rookies plus dropped/available veterans and free agents.
- State model: local/session mock state only. The simulator must not mutate data packs, promoted artifacts, app wiring, ranking sort logic, rookie board order, or outcome probability bands.

## Pool
- Rookies come from the frozen/review draft pool already supplied to draft state.
- Dropped veterans and free agents come from available-player rows already supplied to draft state.
- Protected roster players remain blocked upstream and must not be inferred as available.

## Market/ADP Firewall
- ADP, public market rank, expected pick, and similar market context may be used only to model opponent pick timing, opponent behavior, and whether a player is likely to remain available.
- Market context is blocked from NWR private quality/value fields, including `stats_model_value`, `model_value`, `draft_value`, `nwr_draft_value`, `nwr_dynasty_score`, `nwr_quality_score`, `quality_score`, and `war_score`.
- If a market context row includes blocked score/value fields, those fields are ignored and surfaced as warnings.
- Simulator outputs must carry review-only language and preserve `nwr_score_status=unchanged_from_input` for availability rows.

## Output Use
- Safe: scenario rehearsal, likely-availability review at the next Niners pick, opponent-timing stress tests, and saved mock JSON artifacts.
- Blocked: final draft recommendations, private score tuning, rookie rank/order changes, production ranking/sorting changes, outcome-probability updates, or Drop Decision/Outcome HQ promotion.
