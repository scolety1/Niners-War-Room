# Trading Lab T23 Desktop Review Polish Plan

Date: 2026-06-18

## Starting HEAD

`13b4d45ea8200a249788d081f23bd8d172dd1d86`

## Goal

Make the existing desktop Trade Lab page easier to scan and review using fake
in-memory fantasy trade packages only.

## Planned UI Polish

- Clearer section headers.
- Stronger visual priority for the best trade card.
- Clearer fake-data and integrations-not-wired notice.
- Better grouping for left controls.
- Better ranking language for trade packages.
- Clearer score labels: NWR Gain, Market Fairness, Opponent Fit, Roster Impact,
  Keeper/Drop Impact, Risk, and Verdict.

## Guardrails

No real data, APIs, generated outputs, deployment, automated trade submission,
or Wall Street product framing.

## Validation Plan

Run focused Trading Lab pytest and Ruff against `src/trading_lab`,
`tests/test_trading_lab_*.py`, and `app/pages/11_trade_lab.py`.
