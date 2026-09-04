# DecisionBundle UI wiring — deferred this wave (section 21)

## What was checked before deciding

Surveyed `src/desktop_api/server.py`'s existing route-registration
pattern (regex route constants + handler dispatch) to scope the real
size of "wire the real DecisionBundle endpoint into Draft Room V2."

## Why it is deferred, per the directive's own explicit permission

Live-drafting DecisionBundle wiring needs a DIFFERENT construction path
than everything built this wave: this wave's `decision_bundle_service`/
`historical_decision_state_service` consume a `RankingResult` built by
the NEW historical bridge from point-in-time historical rows. A live
Draft Room pick needs a `RankingResult` built from the CURRENT governed
projection snapshot instead — a real, separate integration this wave
did not build, requiring at minimum:

1. A new `desktop_facade.py` method assembling the live
   `RankingResult`/`AdpSnapshot`/`comparable_leagues` state
   `decision_bundle_service.build_decision_bundle` needs from the
   ALREADY-BOOTSTRAPPED redraft state (not a small change — the current
   facade never constructs a `comparable_leagues` Monte Carlo
   population for a live pick today).
2. A new HTTP route in `server.py` (following the existing
   `_REDRAFT_*` regex-route pattern).
3. A new `@nwr/api-client` method.
4. Real Draft Room V2 UI changes to call it and render Pick Score / Team
   Score / Championship Equity / Cost of Waiting instead of the
   existing `RESEARCH_NOT_CONNECTED` placeholder — never a static/mock
   value, per the directive's own instruction.

This is a genuine multi-layer backend-HTTP-surface-plus-frontend
project, not a light wiring task — exactly the case the directive says
to defer ("If live DecisionBundle wiring becomes a broad frontend
project: defer UI and prioritize calibration backend"). The backend
side this wave prioritized instead (bridge, decision state, tournament,
calibration toolkit, gates, one-command entrypoint) is the larger,
harder, and more foundational half of this work; the live-drafting
facade method above is the concrete next step whenever UI wiring is
prioritized.

## What is NOT deferred

Draft Room V2's existing `RESEARCH_NOT_CONNECTED` labeling (prior wave)
is untouched and remains accurate — the UI still visibly, honestly
states that SHADOW/RESEARCH numbers are not wired to a live route,
rather than silently going stale or wrong.
