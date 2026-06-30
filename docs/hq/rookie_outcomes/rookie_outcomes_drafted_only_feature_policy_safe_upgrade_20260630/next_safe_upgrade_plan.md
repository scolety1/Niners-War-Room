# Next Safe Upgrade Plan

## A. Implemented / Safe Now

- Drafted-only admission contract.
- Synthetic draft-capital quarantine policy.
- Gate E feature manifest.
- Label-source partition policy.
- Historical replay leakage guardrail documentation.
- Gate F/G blocker policies.
- Focused guardrail tests.

## B. Waiting For nflverse Refresh Health Green

- Dataset-level refresh receipts for draft_picks, combine, player_stats, rosters, weekly_rosters, ff_playerids, depth_charts, snap_counts, and injuries.
- Depth-chart row counts, teams, positions, IDs, and parseable depth order.
- nflverse player_stats sidecar label comparison.

Classification: `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN`.

## C. Needs Model Gate

- Any Gate E refresh or model tuning.
- Any use of combine, depth, roster, snap, injury, age, or broader replay features as model inputs.
- Any promotion of label targets to training truth.

## D. Blocked

- UDFA/non-drafted modeling.
- CFBD model input or training truth.
- Gate G / Rankings wiring.
- Vendor/Gmail/RotoWire/FantasyPros/FootballDB/private/raw source ingestion.

## E. Recommended Next Branch

`work/lane-nflverse-refresh-health-20260630` should complete first if the next work needs refreshed public datasets. Otherwise, the next safe Rookie Outcomes lane should be a review-only feature-gate approval packet for the six Gate E features and any proposed additions.
