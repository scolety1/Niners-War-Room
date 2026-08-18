# Test results

- Python compilation passed for the service, desktop facade, and desktop API server.
- Focused isolated service checks passed for markdown and plain-text parsing, shared snapshot loading, auto platform selection, manual override, disabled-to-FFC behavior, CPU source labels, Draft Room source, and decision-row ADP.
- Desktop TypeScript typecheck passed.
- Focused Vitest suite passed: 16 assertions across the Redraft acceptance surface and authenticated API-client routes, including the per-league platform-selection route.
- Normal Redraft 1.0.3 NSIS packaging and installation passed; installed sidecar matches the final built sidecar receipt and owner state is unchanged.

The bundled Python runtime does not include `pytest`, so the focused service checks were executed directly in isolated temporary state rather than installing a new dependency.

## Parse coverage repair V2

- Plain-text four-column extraction and selected/fallback provider checks passed in isolated temporary state.
- Desktop TypeScript typecheck passed.
- Focused Redraft/API Vitest suite passed: 18 assertions.
- Redraft 1.0.4 NSIS package/install passed with an unchanged owner-state manifest.
