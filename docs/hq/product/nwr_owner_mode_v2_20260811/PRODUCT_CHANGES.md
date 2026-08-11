# Owner Mode V2 product changes

## Shared decision system

- Added a common owner hero, decision cards, owner metric contrast, market readout, and reusable
  Floor / Expected / Ceiling component.
- Floor / Expected / Ceiling uses research downside probability, frozen research neighborhood, and
  research ceiling probability. Numeric signals are rendered as percentages; no generic score range
  was invented.
- Added a deterministic five-band NWR-versus-market translation. Rank gaps remain display-only.

## Main surfaces

- Home is action-first: evaluate, compare, analyze a trade, inspect market gaps, search an asset, or
  resume saved work.
- Rankings is a compact canonical board with owner filters and direct paths into Detail, Why, and
  Compare.
- Market Analysis is a dedicated disagreement worklist with explicit buy/aligned/caution bands.
- Why NWR Ranks Them gives a summary plus three-to-five concise admitted reasons before receipts.
- Player Compare is organized around short-, medium-, and long-term leans, a decision matrix, ranges,
  market gaps, risk, and applicable outcomes.
- Player Detail centralizes identity, rank, range, outcomes, market, reasons, and personal context.
- Rookie Review now leads with rookie tiers, draft ranges, and plain-language explanations; raw model
  fields remain in Advanced details.
- All Dynasty Assets exposes source rank, research coverage/readiness, missing evidence, personal
  flags, and blocked states with raw sources and scores below an expander.

## Decisions and separation

- Analyze Trade retains current roster/pick negotiation, exact governed assets, and advisory outcomes,
  with a new football-first entry statement.
- Scenario Playground replaces owner-visible JSON with named football scenarios and a saved
  composition check tied to the selected team window.
- Decision Tracker states its prospective-learning purpose before dashboards and receipts.
- `/redraft` is now a launcher for the separate Redraft app. The dedicated Redraft application still
  runs through `app/main_redraft.py` and `scripts/start_redraft_app.ps1` on port 8512.
- The old dense Rankings and Compare views are preserved at `/rankings-data` and `/compare-data`.
