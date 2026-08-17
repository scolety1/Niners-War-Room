# Implementation Roadmap

No phase begins until the owner approves this packet. Branch names are suggestions; each lane starts from the owner-adopted HQ, never from the audit branch.

## Phase 0 — adopt truth and shared contracts

Features: reconcile the `9cb6eaf...` candidate into HQ through a dedicated adoption review; preserve separate installed state; establish `LeagueWorkspace`, identity, availability, provider/snapshot/freshness and authority-ledger contracts; refresh or visibly stale Dynasty Market; adopt approved Rookie visibility without changing scored authority.

- Dependencies: owner candidate/adoption decision and binary/state receipts.
- Likely lane: `adopt/nwr-desktop-owner-reconciliation-v1` followed by focused shared-contract lanes.
- Effort: 1-2 weeks, medium.
- Model: strong reasoning for reconciliation/review; normal coding model for mechanical implementation. No training.
- Risks: hidden lineage conflict, installed-state migration, authority-label regression.
- Gate: clean ancestry/diff, docs/code separation, all current acceptance suites, binary provenance, owner smoke test of both apps.
- Owner test required before Phase 1: yes.

## Phase 1 — complete Redraft Draft Room

Features: ADP snapshot/import; position-first tiering; immutable pick events and read models; every-team rosters/snake ownership; save/reload/undo; seeded ADP CPU mock; Beat ADP NWR View/Draft Timing; live read-only Sleeper companion; manual K/DST boundary.

- Dependencies: Phase 0 contracts and owner-approved ADP source.
- Likely lanes: `feature/redraft-adp-contract`, `feature/redraft-draft-room-v2`, `feature/redraft-tiering-v2`, `feature/redraft-mock-beat-adp`.
- Effort: 3-5 weeks, high.
- Model: strong reasoning for architecture/calibration; normal coding model for implementation. Historical model fitting only after an explicit data gate.
- Risks: identity mismatch, ADP staleness, misleading probabilities, state corruption, unrealistic CPU behavior.
- Gate: deterministic seeded simulations; event invariants; crash/reload/undo; duplicates impossible; calibration report; offline fallback; complete 15-round owner rehearsal.
- Owner test required before Phase 2: yes.

## Phase 2 — weekly decisions

Features: weekly snapshot provider boundary; legal lineup optimizer; close-call start/sit; active unrostered pool; add/drop marginal value; QB/TE/K/DST streamers; bye/injury replacement; transaction history views. FAAB stays experimental/deferred until calibrated.

- Dependencies: shared provider/identity/availability contracts and approved weekly data sources.
- Likely lanes: `feature/weekly-lineup-v1`, `feature/waiver-wire-v1`, `feature/streamers-v2`.
- Effort: 3-5 weeks, high.
- Model: strong reasoning for evidence/calibration; normal coding model for deterministic optimizer/UI. No new ranking model.
- Risks: provider terms/outage, illegal lineup edge cases, stale injury data, overconfident add/drop deltas.
- Gate: slot property tests; retrospective weeks; stale/missing-provider drills; roster/availability correctness; owner weekly walkthrough.
- Owner test required before Phase 3: yes.

## Phase 3 — Trade Finder and market UX

Features: opponent needs/surplus, target search, package enumeration, counteroffer workflows, before/after roster impact; refreshed Market display. No new calculator.

- Dependencies: shared roster/provider contracts and stable Trade Decision Assistant.
- Likely lane: `feature/dynasty-trade-finder-v1`.
- Effort: 2-3 weeks, medium.
- Model: strong reasoning for search constraints/review; normal coding model for implementation.
- Risks: combinatorial search, one-sided suggestions, stale Market interpreted as truth.
- Gate: same NWR authority outputs as existing analyzer; bounded search; evidence on both teams; owner trade scenarios.
- Owner test required before Phase 4: yes.

## Phase 4 — product reconciliation and publication

Features: final navigation, disconnected planning tools, accessibility/keyboard/responsive polish, source/system pages, backup/restore/migration, packaging and signed receipts, documentation and acceptance matrix.

- Dependencies: accepted Phases 0-3.
- Likely lane: `release/nwr-complete-product-v1`.
- Effort: 1-2 weeks, medium.
- Model: normal coding plus strong final audit/review.
- Risks: cross-app divergence, installer/state regression, technical navigation leaking to Owner mode.
- Gate: fresh-machine installs, existing-state upgrades, offline/stale/network-failure scenarios, complete Dynasty/Redraft owner scripts, clean canonical adoption.
- Owner test required before complete/publication: yes, explicit sign-off.
