# Trading Lab Desktop Human Review Script - 2026-06-18

## Open The Page

Open the isolated Streamlit page: `app/pages/11_trade_lab.py`.

## Modes To Click

- Trade For Player.
- Trade Away Player.
- Upgrade Position.
- Consolidate Depth.
- Pick Conversion.
- Drop-Pressure Trade.
- Opponent-Fit Trade.
- Training Mode.

## Sections That Should Appear

- Header with fixture-only and not-wired labels.
- Build the trade.
- Review board.
- Best trade.
- Ranked packages.
- Negotiation ladder.
- Bad trade warnings.
- Roster aftermath.
- Training Mode.
- Placeholder integration boundaries.
- Review queue placeholder.

## Best Trade Card Checks

- NWR Gain is visible.
- Market Fairness is visible.
- Opponent Fit is visible.
- Roster Impact is visible.
- Keeper/Drop Impact is visible.
- Risk and Verdict are visible.
- Explanation summary is review-only.

## Package Comparison Checks

- Rank, give, get, NWR gain, public market fairness, opponent fit, roster impact, keeper/drop impact, risk, verdict, and primary warning can be reviewed from helper output.

## Negotiation Ladder Checks

- Opening offer, fair offer, max offer, walk-away line, do-not-include assets, counteroffer ideas, reject branch, and ask-for-more branch are present.

## Trade-Away Board Checks

- Best NWR return.
- Most realistic return.
- Best win-now return.
- Best long-term return.
- Pick-heavy return.
- Player-heavy return.
- Do-not-accept-below line.

## Trade-For Board Checks

- Cheapest plausible opener.
- Fair offer.
- Aggressive offer.
- Max offer.
- Player-only offer.
- Pick-heavy offer.
- Do-not-include assets.
- Sweetener suggestions.

## Roster Aftermath Checks

- Keeper impact.
- Drop pressure impact.
- Positional depth impact.
- Rookie/mock placeholder context.
- Real roster integration not wired label.

## Warning Engine Checks

- Negative NWR edge warnings.
- Unrealistic market gap warnings.
- Keeper damage warnings.
- Drop pressure warnings.
- Low opponent fit warnings.
- Untouchable asset warnings.

## Training Mode Checks

- At least three fake scenarios.
- Four choices per scenario.
- Scoring dimensions for NWR value, market realism, opponent fit, roster impact, and negotiation quality.
- Training-only / fake scenario disclaimer.

## Fixture-Only / Not-Wired Labels

- Fixture demo value.
- Real NWR integration not wired.
- Public fantasy market source not wired.
- Manual review required.
- Review queue not wired.

## What Would Be A Bug

- Any claim that real NWR data is wired.
- Any claim that public fantasy sources are wired.
- Any save/export/generated output behavior.
- Any automated fantasy trade submission.
- Any stock-market, broker, crypto, equity, or real-money framing.
- Any broken mode or empty screen without a clear placeholder.

## Intentionally Placeholder

- Real NWR values.
- Public fantasy market values.
- Roster context.
- Rookie/mock draft context.
- Saved review queue.
- Generated exports.
