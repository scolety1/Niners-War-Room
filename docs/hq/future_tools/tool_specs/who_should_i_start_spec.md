# Who Should I Start? Spec - R&D Only

Purpose: future weekly lineup help after weekly projection, injury/status, scoring, and lineup-rule gates exist.

Safe output now: roadmap/status only.

Blocked output: start/sit recommendation, confidence, projection gap, injury-adjusted caveat.

Required data: roster, lineup rules, weekly projections, current injury/status, opponent/schedule, scoring settings, and lock status.

Proposed mechanics: compare source-approved projected points after availability and lineup constraints. This is not implemented.

Current NWR coverage: dynasty ranks and review-only NFL usage exist, but no approved weekly projection/start-sit model exists.

Build decision: `BLOCKED_NEEDS_MODEL_GATE`.

Safety notes: missing projection, injury, or status data must remain `Not enough information`.

Next step: create a separate weekly projection and start/sit model approval gate.

Sources: Sleeper API docs https://docs.sleeper.com/ and nflreadpy https://github.com/nflverse/nflreadpy.
