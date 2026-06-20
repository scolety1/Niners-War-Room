# Trading Lab UI Review Baseline Inventory - 2026-06-18

## Current Page Route

- `app/pages/11_trade_lab.py`
- Status: isolated routed Streamlit page that calls `render_trade_lab_page()`.

## Current Source Modules

- Contracts, fixtures, scoring, package building, negotiation, roster effects, warnings, explanations, comparison rows, trade-for/trade-away boards, scenario coverage, layout resilience, adapter contracts, disabled adapters, provenance, missing-data states, and review queue placeholder all live under `src/trading_lab/`.

## Current Focused Tests

- Focused Trading Lab tests live under `tests/test_trading_lab_*.py`.
- Current validation suite covers route smoke, fixture contracts, scoring, warnings, UI labels, no-contamination checks, review packet checks, and fallback states.

## Current UI Sections

- Header.
- Desktop layout.
- Left control panel.
- Center results.
- Right context panel.
- Negotiation ladder.
- Bad trade detector.
- Training Mode.
- Placeholder integration boundaries.
- Review queue placeholder.
- Disabled provider states.
- Scenario coverage.

## Current Fake/Fixture Systems

- Fixture value provider.
- Fixture package builder.
- Fixture scoring.
- Fixture negotiation ladder.
- Fixture roster aftermath.
- Fixture warnings.
- Fixture explanations.
- Fixture comparison rows.
- Fixture scenario coverage.

## Current Placeholders

- Real NWR integration.
- Public fantasy market source.
- Roster context.
- Rookie/mock context.
- Saved review queue.
- Generated exports.

## Known Blocked Integrations

- Real Outcome, Rookie, Mock Draft, Drop Decision, Deployment V2, or Master lane wiring.
- Public fantasy source integration.
- Data ingestion.
- Generated outputs.
- Automated trade submission.
- Automatic league transaction execution.

## Review Risks

- Header copy may still be too tool-like for a first human review.
- Mode guidance may need clearer "when to use this" language.
- Best trade card and package board may need stronger Give/Get hierarchy.
- Warning and explanation copy may need less internal jargon.

## Baseline Verdict

GREEN for fixture-only human review baseline. HOLD for real integrations.
