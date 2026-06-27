# Roster Weakness Tracker Spec - Framework Only

Purpose: descriptive roster health/checklist surface that flags missing information before any recommendation.

Safe output now: checklist/status framework.

Blocked output: add/drop/start/trade recommendation or weakness score.

Required data: roster state, positions, ages, injuries/current status, draft assets, and scoring.

Proposed mechanics: count roster slots by position and label missing age/status as `Not enough information`.

Current NWR coverage: roster/runtime and ranking context exist, but current health/status and lineup-depth evidence are incomplete.

Build decision: `SAFE_NOW_FRAMEWORK_ONLY`.

Safety notes: descriptive counts are allowed; recommendations and risk defaults are not.

Next step: build only after human approval of source fields and desired UI.

Sources: Sleeper API docs https://docs.sleeper.com/.
