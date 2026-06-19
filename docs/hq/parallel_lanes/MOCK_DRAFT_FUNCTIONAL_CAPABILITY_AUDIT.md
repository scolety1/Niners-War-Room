# Mock Draft Functional Capability Audit

Date: 2026-06-19

Repo: `C:\NWR\Niners-War-Room-mock-draft`

Branch: `work/mock-draft-simulator`

HEAD audited: `50cc612731cabf748ebf156a8fb467dcdc7dcd67`

Starting status: clean.

## Bottom Line

Mock Draft has a real, tested service-layer draft-state engine and a
fixture-only/review-only opponent timing scenario builder. It does not yet have
a complete real draft-day operator application, and it is not ready for actual
draft use.

Verdict:

- Fixture-only practice/review: YELLOW/GREEN. Core state transitions and
  review-only scenario behavior work with fake fixtures, but there is no fluid
  operator UI.
- Real-input validation: GREEN infrastructure / YELLOW inputs. Contracts,
  manifest checks, preflight scripts, and candidate validation exist.
- Real draft use: YELLOW/HOLD. Final real inputs and a local-only manifest are
  incomplete, and no real-use operator workflow has been validated end to end.

No real simulations were run for this audit. No real data was copied. No real
manifest was created. ADP/market separation remains preserved.

## What Is Actually Implemented

- `src/services/draft_state_service.py` implements an immutable draft board
  state with picks, available players, drafted players, current pick,
  my-pick tracking, history, search/filter helpers, best remaining rows,
  undo/reset, correction/edit behavior, guardrail status, grid rows, and
  export-row builders.
- `src/services/mock_draft_simulator_service.py` implements a review-only
  opponent pick scenario that can use behavior-only market timing rows while
  preserving NWR quality/value fields.
- Contract services exist for input readiness, manifest validation, available
  pool, pick order, rosters/keepers, team needs, market separation, schema
  diagnostics, header aliases, redaction, blank templates, and closeout status.
- Read-only scripts exist for state smoke, input readiness, real-input
  preflight, and closeout status.
- Tests cover service-layer fixture behavior, validation invariants, no-real
  data guardrails, and ADP/market separation.

## Docs / Contracts Only

- Operator quick-start, draft-day safety runbook, Master handoff, user
  checklist, manual mapping packet, and blank input template packet are docs.
- These documents make restart and handoff easier, but they are not an
  interactive operator experience.
- The local-only manifest bootstrap is dry-run only. It intentionally does not
  create the real manifest.

## Fixture-Tested

- Draft state creation, current pick, my-pick summary, drafted player removal,
  history, undo, reset, correction/edit, duplicate validation, search, position
  grouping, grid rows, export rows, and review-only option rows.
- Fixture manifest validation and schema separation.
- Fixture-only opponent timing scenario with market fields ignored as private
  value.
- Real-input preflight missing-manifest path, which correctly reports YELLOW.

## Missing Or Not End-To-End

- Final local-only real manifest.
- Final frozen rookie input confirmation/mapping.
- Final dropped/available veteran pool.
- Final pick order and NWR/my picks.
- Final roster/keeper state.
- Team needs/opponent tendency source.
- NWR private value source for the mixed rookie/veteran pool.
- Real ADP/market behavior source.
- A draft-day operator UI, CLI command loop, or persistent manual entry screen.
- End-to-end live operator workflow for mixed rookie plus dropped-veteran draft.
- Safe real-time save/load/persistence policy for manual picks during an actual
  draft.

## Functional Surface Audit

| Surface | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Streamlit/app UI | RED | No Mock Draft app wiring found in this lane. | Intentionally not wired. |
| CLI | YELLOW | Read-only scripts exist; no interactive draft command loop. | Useful for preflight, not live operation. |
| Script-based operator flow | YELLOW | Smoke/readiness/preflight/closeout scripts. | Reporting only; not a live draft room. |
| Service-only layer | GREEN | `draft_state_service.py` and contract services. | Strongest implemented surface. |
| Test-only simulator | GREEN | `test_draft_state_service.py`, `test_mock_draft_simulator_service.py`. | Fake fixtures only. |
| State manager | GREEN | `DraftBoardState` plus transition functions. | Immutable service-layer state. |
| Draft pick recorder | GREEN | `mark_player_drafted`, replacement/correction helpers. | Tested with fixtures. |
| Available pool manager | GREEN | selected player removal, remaining pool helpers. | Real pool still missing. |
| Current pick tracking | GREEN | recomputed from drafted picks. | Tested. |
| Undo/edit capability | GREEN | `undo_pick`, `replace_drafted_player_at_pick`, `reset_mock`. | Service layer only. |
| My-pick alerts | YELLOW | `next_my_pick`, `draft_progress_summary`, `is_my_turn`. | No live notification UI. |
| Team/opponent model | YELLOW | Market timing scenario, team-needs contract. | Not a full opponent model. |
| Export/report capability | YELLOW | Export rows and local-review artifact writers exist. | Some writers target `local_exports`; not used in this audit. |
| Real draft manifest ingestion | YELLOW | Manifest validator/preflight. | Missing real manifest and final sources. |
| Fixture-only demo flow | YELLOW/GREEN | Fixture state flow passed in audit. | Service-level, not polished operator demo. |

## Capability Matrix

| Capability | Status | Audit finding |
| --- | --- | --- |
| 1. Load rookie input | YELLOW | Contract and candidate validation exist; final confirmed real source/mapping incomplete. |
| 2. Load dropped/available veterans | YELLOW/RED | Contract exists; final canonical veteran pool is missing. |
| 3. Load pick order | YELLOW | Contract exists; archived candidates exist; final/current source not confirmed. |
| 4. Load my picks | YELLOW | Pick ownership contract exists; final mapping/source not confirmed. |
| 5. Load rosters/keepers | YELLOW | Contract exists; candidate archive partial; final keeper state not confirmed. |
| 6. Load NWR private values | YELLOW | Contract exists; mixed rookie/veteran private value source incomplete. |
| 7. Load ADP/market separately | YELLOW | Separation contract exists; real market behavior source missing. |
| 8. Build available player pool | YELLOW/GREEN | Service can build from rows; real mixed pool not finalized. |
| 9. Prevent kept/rostered players from available | GREEN for contract | Roster contract detects kept/available overlap in fixtures. |
| 10. Track current pick | GREEN | Implemented and tested. |
| 11. Mark player drafted | GREEN | Implemented and tested. |
| 12. Detect duplicate picks/assets | GREEN | Implemented and tested. |
| 13. Maintain draft pick history | GREEN | Implemented and tested. |
| 14. Undo or correct a pick | GREEN | Implemented and tested. |
| 15. Identify my upcoming picks | GREEN/YELLOW | Service summary exists; no live alert UI. |
| 16. Show best available by NWR private value | YELLOW | `best_options_at_pick` uses input order/draft rank/value fields; no real validated private value source. |
| 17. Show likely opponent behavior using ADP/market separately | YELLOW | Review-only market timing scenario exists; not live real workflow. |
| 18. Filter by position/team/status | YELLOW/GREEN | Search and position helpers exist; no full operator UI filters. |
| 19. Flag missing data | GREEN | Readiness/preflight contracts flag missing inputs. |
| 20. Support fixture-only practice mode | YELLOW/GREEN | Service/test fixtures support practice flows; not a polished mode. |
| 21. Support real draft-use mode after manifest validation | YELLOW | Validation path exists; real mode not end-to-end proven. |
| 22. Provide human operator screen/CLI/report | YELLOW/RED | Reports/scripts exist; no fluid screen or command loop. |
| 23. Produce a draft-day quick view | YELLOW | Grid/export rows and docs exist; no live quick-view surface. |
| 24. Avoid production rankings/app wiring | GREEN | No app wiring introduced; guardrails preserved. |
| 25. Preserve ADP/market separation | GREEN | Contracts/tests and simulator firewall preserve separation. |

## Practice / Mock Simulator

There is a usable service-layer practice/review engine for fake fixtures:

- create draft state;
- mark a player drafted;
- advance current pick;
- preserve draft history;
- undo/reset/correct picks;
- run a review-only opponent timing scenario with fake market context.

However, this is not a polished practice app. It requires Python/test/service
use rather than a friendly operator interface.

## Real Draft-Use Workflow

Real draft-use is not ready. The repo has readiness contracts, manifest
validation, preflight scripts, candidate validation, and redaction rules, but
the final local-only real inputs are still missing or only archive candidates.
The workflow remains validation-only until those inputs are supplied and
confirmed.

## Operator Experience

The current operator experience is not fluid for draft day. It is mostly:

- docs;
- readiness scripts;
- service-layer state functions;
- tests/fixtures;
- report row builders.

There is no dedicated UI, no interactive CLI, no persistence loop for live
manual pick entry, and no validated one-command draft-day screen. A knowledgeable
developer can exercise the service layer, but a human draft operator would need
additional workflow polish before using it under time pressure.

## Real Draft Safety

Current real draft use is not safe to start. Safe actions are:

- read-only real input validation;
- local-only manifest review if explicitly approved;
- fixture-only practice/review;
- additional operator workflow development using fake data.

Unsafe actions remain:

- treating archive/candidate paths as final inputs;
- running real simulations;
- importing ADP as NWR value;
- committing real data or local manifests;
- wiring app/production ranking behavior.

## Required Work Before Draft-Ready

1. Confirm final local-only manifest path and roles.
2. Confirm frozen rookie input and header aliases.
3. Confirm final dropped/available veteran pool.
4. Confirm pick order and NWR/my picks.
5. Confirm rosters/keepers and exclude unavailable kept players.
6. Confirm NWR private value source for rookies and veterans.
7. Confirm ADP/market behavior source separately.
8. Build or approve an operator workflow: UI, CLI loop, or manual screen.
9. Validate real inputs read-only, then run a fixture-like dry operator rehearsal.
10. Define persistence/recovery for manual picks during an actual draft.

## Recommendation

- Ready for fixture-only practice? Yes, at service/test level; not as a polished
  app.
- Ready for real-input validation? Yes.
- Ready for real draft use? No.
- Needs additional runway? Yes. The next runway should be operator workflow
  design/prototype with fake fixtures only, or real-input validation once Master
  supplies confirmed local paths.

## Fixture Operator Workflow Update

The fixture-only operator workflow now has a command-driven practice path for
status, available assets, manual mark drafted, undo, history, upcoming NWR picks,
and validation. This improves practice readiness, but it still does not create a
real draft-use mode, production UI, automated opponent algorithm, or simulation
approval.
