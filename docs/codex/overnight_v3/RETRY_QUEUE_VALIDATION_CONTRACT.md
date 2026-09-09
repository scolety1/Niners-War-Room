# NWR Overnight V3 Retry-Queue Validation — Preregistered Contract

Written before viewing full walk-forward, blind-draft, or rendered-acceptance results (Phase 4's
Test 18 fixture replay and Phase 5's automated legality/completeness draft below were mechanical,
deterministic regression checks against already-fixed, already-committed code — not something to
tune against — but this contract is filed here, before Phases 3/7/8/9/10's results, per the
mission's own instruction, and this ordering is disclosed honestly rather than hidden).

## Reference vs candidate

- **Reference (accepted pre-overnight engine)**: commit `a72500a6` — the real `draft-upgrade-hq`
  lineage HEAD that produced the Test 18 evidence, confirmed via `git merge-base` against this
  branch.
- **Candidate**: commit `e652caeb` (branch `overnight/nwr-full-advance-v3-20260909`), plus any
  additional commits added on this same branch during this validation pass.
- **Primary regression target**: Test 18 (10-team, ESPN, full PPR, slot 5, roster
  1QB/2RB/2WR/1TE/1FLEX/1K/1DST/7BN) — specifically the Round-14 illegal-WR-recommendation defect.

## Explicit non-tuning commitment

We will NOT tune candidate behavior against Test 18 screenshots or outcomes after seeing results.
Any fix made in response to a failure found during this validation pass must be a genuine root-cause
fix applicable beyond the single observed case (matching the existing pattern already used in Lane 1:
`evaluate_draft_pick_legality` is a general league-config-driven service, not a Test-18-specific
patch).

## Burned holdouts (unchanged)

2016, 2024, and 2025 remain burned historical holdouts. No claim in this validation may be
described as a "pristine holdout" result. Only already-admissible development/historical evidence
(pre-holdout seasons, or already-disclosed re-uses of burned seasons for non-holdout diagnostic
purposes) is used, and every use is labeled honestly as such.

## Required gates (stated before running anything new)

- **A. Zero illegal primary recommendations** — the canonical `evaluate_draft_pick_legality` must be
  the sole hard-maxima authority on every live recommendation surface, and no Suggestions/Search/
  Compare/Cheat-Sheet/Player-Drawer/Draft-Board/CPU-simulation/pick-recording path may present an
  illegal player as "Pick Now."
- **B. No material historical outcome regression** — the legality/roster-construction changes must
  not make historically-realized roster outcomes worse versus the reference commit, on whatever
  historical evidence this worktree can actually reach (disclosed honestly if data access is
  blocked).
- **C. Blind full drafts complete legally** — a full 16-round, 10-team draft finishes with zero
  illegal picks recorded and zero position-cap violations for every team, not just the owner.
- **D. Position-hoarding pathology improves or does not regress** — the specific WR-hoarding-past-
  useful-depth pattern from the real Test 18 draft must not recur under the fixed legality service,
  and no new analogous hoarding pathology at another position may be introduced by this branch's
  changes.
- **E. Latency remains acceptable** — DecisionBundle / Suggestions latency on the candidate must not
  regress materially versus the reference commit's own documented baseline.
- **F. League switching does not leak state** — switching between league profiles must not leak
  roster, drafted-state, scoring, ADP-provider, team-identity, waiver-pool, matchup, queue, or
  draft-slot state across league boundaries.

## Known, disclosed environment constraint set before running Phase 3

This worktree (`C:\NWR\overnight-full-advance-v3`) has no governed 2026 projection snapshot
installed (`local_exports/projections/2026/current.csv` is absent — a real, pre-existing environment
gap documented in this session's own memory, not fabricated or newly discovered here). This bounds
what Phase 3 (historical walk-forward) and Phase 5 (new blind draft) can honestly claim in this
worktree: any automated blind draft run here must use a clearly-labeled synthetic ranked pool (never
presented as real player data), and any historical walk-forward claim is limited to whatever
historical/backtest evidence and harnesses already exist and are runnable in this worktree without
installing new data. This constraint is recorded here, before results, specifically so a later
"data happened to be missing so I only tested the easy part" excuse cannot be retrofitted.
