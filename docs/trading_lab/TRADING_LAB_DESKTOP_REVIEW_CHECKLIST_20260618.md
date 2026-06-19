# Trading Lab Desktop Review Checklist - 2026-06-18

Use this checklist for manual desktop review of the fake-data Trade Lab page before any real NWR integration is proposed.

## Page Smoke

- Page loads from the isolated Streamlit page: `app/pages/11_trade_lab.py`.
- Page title is `Trade Lab`.
- Subtitle says: `Find realistic fantasy trades where market says fair, but NWR says we win.`
- Fake-data and not-wired notices are visible.
- No old Wall Street product language is visible as active page purpose.

## Desktop Layout

- Left control panel is visible.
- Center review board is visible.
- Right roster context panel is visible.
- The page feels usable on desktop without a routed app shell change.

## Interaction Review

- Mode selector is usable.
- Trade For Player and Trade Away Player modes are present.
- Best trade card is visible.
- Ranked packages are visible.
- Negotiation ladder is visible.
- Bad trade warnings are visible.
- Roster aftermath and context placeholders are visible.
- Training Mode scenarios are visible.

## Guardrail Review

- All data is fake and in-memory.
- No real roster values are claimed.
- No real Outcome, Rookie, Mock Draft, or Drop Decision integration is claimed.
- No automated trade submission, automatic decisioning, generated outputs, or deployment behavior exists.
- No broker, stock-market, crypto, equity, credential, secret, key, token, or execution feature is present.
