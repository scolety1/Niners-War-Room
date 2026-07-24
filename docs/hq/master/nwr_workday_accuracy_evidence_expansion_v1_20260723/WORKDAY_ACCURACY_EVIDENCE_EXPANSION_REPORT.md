# NWR Workday Accuracy Evidence Expansion V1

## Verdict

`YELLOW_NWR_RECEIPT_RECOVERY_EXHAUSTED_WITH_ACTIONABLE_HUMAN_LEADS`

The exhaustive local recovery found no admissible historical checkpoint, final-score,
or exact-rank receipts for `model_v4_wr_qb_v2_old_pocket_qb_guardrail`. Exact replay remains `0 / 5,518`.
The recovered exact definition of `HQ2_THREE_YEAR_STABILITY_LOW_GAMES_GUARD_V1`
is a meaningful definition/provenance gain, and its 4,764-row review-only V3 output
regenerates deterministically, but it does not expand exact Model v4 evidence.

## Evidence frontier

- Historical panel: 5,518 rows / 1,552 players /
  2013-2025.
- OOF candidate panel: 4,731 rows / 1,390 players / 2015-2025.
- Exact primary rows: 0.
- Exact deterministic-regeneration rows: 0.
- Exact seasons/positions: none.
- Proxy-to-exact: `PROXY_TO_EXACT_NOT_TESTABLE`.
- Final challenger disposition: `NO_ACCURACY_CHALLENGER_ADMITTED`.
- Production ranking change: `NONE`.
- Frozen 2026 change: `NONE`.

## Recovery result

Canonical Git history, all local NWR worktrees/clones, direct NWR roots, NWR shared
research/backtest roots, Documents NWR packets, and 40 unique ZIP archives were
searched. Current-only receipts, partial/review-only panels, and near-equivalent
reconstructions were rejected for exact historical use.

## Governed definition gain

The HQ2 definition was recovered from clean tracked Git bytes at commit
`5556520fb5b0591ea2740855ab43400279603809`, tree `160b7174a6f6b4ce5e0e26cdf2fd00c0b52d2940`. Formula, parameters, missingness,
identity, tie behavior, input exclusions, output schema, and deterministic generation
are proven. The candidate still fails admission because exact Model v4 overlap is zero
and low-games misses regress by 12 versus the prior-year baseline.

## Safe closeout

No production, ranking, frozen comparator, source admission, Data Health, launcher,
or persistence behavior was changed. The human/external recovery package is the next
authorized evidence action; no formula search follows this report.
