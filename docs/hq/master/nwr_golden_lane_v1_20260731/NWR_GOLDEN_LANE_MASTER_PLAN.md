# NWR Golden Lane Master Plan V1

The Golden Lane is the permanent sequential control path for completing Niners War Room. It advances one major phase at a time, preserves existing authority until a later gate explicitly supersedes it, and treats a truthful null-model decision as a valid closeout. Dispatch runs in `BOUNDED_CONTINUOUS_AUTOPILOT`: a completed phase may automatically start the next authorized phase when every automatic-advance gate passes.

## Operating rules

1. Begin from the live work/hq-parallel-control commit and tree after fetching the remote.
2. Execute only the phase named by NEXT_AUTHORIZED_LANE.md and verified by the prompt identity/hash in GOLDEN_LANE_AUTOPILOT_STATE.json.
3. Do not repeat an entry in CLOSED_WORK_REGISTRY.csv without genuinely new external authority.
4. Keep football value, availability, evidence confidence, and market retention distinct.
5. Fail closed on invalid source, identity, temporal, preservation, security, or product gates.
6. Every phase closeout updates this packet and replaces NEXT_AUTHORIZED_LANE_PROMPT.md with exactly one next work order.
7. Never force-push. Update stable only after independent review and an authorized green canonical push.
8. Use a fresh implementation worktree and a fresh independent review/adoption worktree for every phase; never combine major phases.
9. Continue automatically only under GOLDEN_LANE_AUTOPILOT_POLICY.md. Stop on any active hard-stop condition.

## Ordered gates

Phase 0 closes the unified-board mission. Phases 1A and 1B establish source authority and baseline hygiene. Phase 2 freezes targets and baselines. Phase 3 tests admitted open role, availability, and lifecycle families. Phase 4 closes or admits formula research. Phase 5 is optional and requires a proven data gap plus owner approval. Phase 6 separately governs market retention. Phase 7 completes or formally closes product surfaces. Phase 8 performs Golden Release acceptance.

The mechanically calculated completion percentage is passed phase gates divided by ten total gates: Phase 0, Phase 1A, Phase 1B, and Phases 2 through 8.

Phases 5 and 6 are never dispatched automatically. Phase 4 may close a null result or record a decision automatically, but production formula authority requires an owner hard stop. Phase 7 and Phase 8 use the additional preconditions in the autopilot policy.
