# Golden Lane Autopilot Resume Prompt

Resume `BOUNDED_CONTINUOUS_AUTOPILOT` from the canonical
`work/hq-parallel-control` branch. Fetch/prune once, verify the live HQ/tree,
read the complete Golden Lane packet, and run
`scripts/validate_golden_lane_autopilot.py` before dispatch.

If `dispatch_status` is `READY` and all automatic-advance gates pass, execute the
single prompt identified by `next_phase` and `next_prompt_sha256` without asking
for a routine phase handoff. If state is `HARD_STOP`, request only the recorded
owner decision. Preserve prior canonical phases and never force-push, update the
operational checkout, or change the scheduled refresh task.
