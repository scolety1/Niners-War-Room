# Stribling Acceptance

Expected and verified governed payload:

- Stable asset: `blocked-rookie:dezhaun-stribling`
- Live governed ID: `00-0041035`
- Current team/position: `SF WR`
- NFL capital: Round 2, pick 33
- Draft eligible/selectable: YES / YES
- Model score eligible: NO
- Frozen rank/score: null / null

Contract/UI regression surfaces: global search (exact, partial, apostrophe-free),
Asset Explorer, Rookie Board, Player Detail, Compare, Trade Lab, Scenario Playground,
and Draft Cockpit. Compare must show no admitted lean. Trade must return
`INSUFFICIENT_EVIDENCE`, LOW confidence, and no preferred side.
