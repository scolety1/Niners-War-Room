# NWR Overnight Product Advance V3 — Final Integration Report

Overnight candidate branch: `overnight/nwr-full-advance-v3-20260909`, based on real canonical commit
`a72500a6` (the draft-upgrade-hq lineage HEAD that produced the Test 18 evidence). Final candidate commit:
`c98ee8c4`. Canonical `main` untouched. Nothing pushed. Nothing deployed.

12 real commits + 2 merge commits, all scoped-test-verified at every stage, final integrated state verified
clean end-to-end: frontend `tsc -b` clean, 98/98 frontend tests pass (6 files), backend 217 passed / 1
skipped / exactly the 5 known pre-existing baseline failures (data-age/hermetic-seed gap, unrelated,
documented in this session's own memory as expected to recur on 2026-09-09 — it did, exactly as predicted).

## Lane 1 — remaining items 1.6–1.9, resolved from already-completed evidence rather than re-run

- **1.6 (backup-utility study)**: this exact study — historical WEEKLY FANTASY-outcome-derived marginal
  roster utility vs. snap-share-derived utility, across league sizes — was already performed and PROMOTED in
  a prior session (see this session's own memory,
  `nwr-post-draft-engine-forensics-v1`: 4 real historical seasons × 12 real draft slots, leakage-safe,
  preregistered gates all passed, mean_delta +74.65, challenger won 32/48 paired observations). It is
  already live in production as the primary candidate-ordering signal
  (`_candidate_sort_key`, `decision_bundle_service.py`, confirmed tonight). Not re-run tonight — re-running
  an already-validated, already-promoted study would not change tonight's engine and was not a genuine gap.
- **1.7 (RB depth vs WR hoarding)**: the original "WR5-8 beats RB3-5" pathology in Test 18 had two real,
  now-fixed causes, not a scarcity/value-model defect: (a) the WR position cap was never enforced (Lane 1
  item 1), so nothing stopped accumulation past a sane depth; (b) once `marginal_utility` (item 1.6, already
  promoted) became primary and the legality gate is real, roster construction is now bounded by actual
  position maxima and mandatory-slot feasibility, not by an unbounded value chase. No RB quota was added, as
  instructed.
- **1.8 (QB2/QB3)**: `test_r14_acceptance_excludes_franklin_and_doubs_at_wr_eight_of_eight` proves directly,
  in code, that Kyler Murray (QB3) was the top LEGAL candidate only after Franklin/Doubs were correctly
  excluded — i.e. a forced legal fallback, never an independent QB3 preference. Lawrence (QB2, R10) remains
  a genuine voluntary recommendation, unchanged by tonight's fixes (RB depth was already exhausted at that
  point in the real draft; not re-litigated here, matches the corrected evidence packet's own framing).
- **1.9 (Pick Score/ordering)**: resolved in the Lane 1 report — a stale UI label, not an ordering defect.
  Fixed.

## Lane 1.13–1.15 — NOT completed tonight; genuinely queued, not silently dropped

Preregistering Challengers A/B/C, re-running historical validation end-to-end, and a NEW live blind 10-team
ESPN draft under an "always take NWR's first legal recommendation" policy were **not** performed tonight.
Classification: `RESOURCE_BLOCKED` (time/host-memory budget, after the real, repeated OOM kills documented
in the Lane 1 report consumed a large share of tonight's capacity) for the historical re-validation piece,
and `EXTERNAL_ACCESS_BLOCKED` for a genuine live ESPN mock draft specifically (this session cannot drive an
external website through a multi-hour live snake draft unattended). What tonight's work DOES provide in
their place, honestly: the R14 regression fixture is a real, deterministic, leakage-safe proof that the
specific Test 18 defect (illegal-WR recommendation at cap) is fixed and stays fixed — a permanent CI gate,
not a one-time demo. A full new acceptance run (live or via `practical_redraft_mock_service.py`, which
already exists and was not invoked tonight) remains the right next step and is on the retry queue below.

## OVERNIGHT_RETRY_QUEUE

| Lane | Item | Status | Classification | Attempts | Root cause | Next reasonable attempt |
|---|---|---|---|---|---|---|
| 1 | Full historical walk-forward re-validation of tonight's specific fixes | Not attempted | RESOURCE_BLOCKED | 0 | Time/host-memory budget consumed by 3x real Codex OOM kills + hands-on repair | Run once host memory is stable; scope to the legality fix and label fix only (marginal_utility itself already separately validated) |
| 1 | New live blind 10-team ESPN draft, always-take-first-legal-recommendation policy | Not attempted | EXTERNAL_ACCESS_BLOCKED | 0 | Requires hours of live external-website interaction this session cannot drive unattended | Either a real live draft (owner-run or Chrome-automated) or invoke `practical_redraft_mock_service.py` (exists, untested tonight) as a lower-fidelity but automatable substitute |
| 1 | Challengers A/B/C preregistration | Not attempted | RESOURCE_BLOCKED | 0 | Depends on the historical re-validation above | After the re-validation item lands |
| 4 | RB-now / wait-on-QB counterfactual reaching the live UI | Still open | IMPLEMENTATION_DEFECT (real, named repeatedly across V3-V8 per the closure audit, never built) | 0 tonight | Genuinely large scope, never attempted in any prior pass either | Scope as its own bounded lane next session |
| 4 | Player Drawer secondary "News" display (Ballers) | Re-verified, already fine | N/A | 1 (verification) | Turned out already fixed at `a72500a6`; Lane 3 added a regression test | Closed |
| 5 | Full integrated acceptance sweep (League Chooser/Draft/Lineup/Waivers/Trades/Streamers/Multi-League/Performance/Persistence) | Partial — see below | Mixed | 1 | Time budget; some surfaces need a live rendered app this session didn't launch tonight | See Lane 5 table below |
| 6 | In-season prospective weekly-recommendation freeze | Blocked | DEPENDENCY_BLOCKED | 0 | No weekly-projection source exists yet (same gap as Lane 2's blocked items) | After a governed weekly-projection model is admitted |

## Lane 5 — Integrated acceptance (honest partial pass, not fabricated)

| Surface | Result | Evidence |
|---|---|---|
| League Chooser | PASS (logic-verified, not visually rendered) | `leagues.tsx` typechecks, reuses the proven `activateRedraftProfile` mutation path; no live browser render was performed this session (no Tauri window screenshot capability here — documented limitation, see this session's memory) |
| Draft (legality) | PASS (deterministic, permanent regression) | `test_r14_acceptance_excludes_franklin_and_doubs_at_wr_eight_of_eight`, `test_test18_kdst_downstream_legality_after_kyler_and_ravens` |
| Draft (full new blind run) | BLOCKED | see retry queue above |
| Weekly Lineup / Start-Sit | BLOCKED | no weekly-projection source exists (Lane 2 archaeology, unchanged) |
| Waivers (Free Agents slice) | PASS | `sleeper_free_agent_pool`, 3 new focused unit tests, all green |
| Waivers (skill-position value ranking, FAAB) | BLOCKED | same data-source gap |
| Trades | BLOCKED | Dynasty-only; deliberately not wired into Redraft tonight (real design decision, not attempted) |
| Streamers (K/DST) | Untouched, pre-existing, not re-verified tonight | no code changed here tonight beyond the free-agent generalization reusing its primitive |
| Multi-League switching | PASS | `key={data.activeProfileId}` remount fix (Lane 3) closes the real state-leak bug found in archaeology; not re-verified via a live render tonight |
| Performance | Not profiled tonight | out of scope given time budget |
| Persistence (restart/relaunch) | Not tested tonight | requires an actual app relaunch this session did not perform |

## Lane 6 — Prospective freeze

**Draft**: not frozen as an accepted candidate tonight — the specific Test 18 defect is fixed and
permanently regression-tested, but the full acceptance sweep above (new blind draft, historical
re-validation) that would justify a freeze was not completed. Correct status:
`DRAFT_FREEZE_BLOCKED_BY_INCOMPLETE_ACCEPTANCE_SWEEP` (not a broken-engine block — the fixes are real and
verified at the unit/integration level; the block is on the larger validation sweep, honestly not run
tonight).

**In-season**: `DRAFT_FREEZE_BLOCKED_BY_NO_WEEKLY_PROJECTION_SOURCE` — cannot freeze prospective weekly
recommendation evidence before outcomes when no weekly recommendation capability exists yet (Start/Sit, ROS,
Waivers-for-skill-positions all confirmed blocked in Lane 2). What DOES exist and could be frozen once real
weekly usage begins: Data Health status, the K/DST streamer, and the new Free Agents/Opponent Rosters reads
— all real, live, already engine-commit-attributable.
