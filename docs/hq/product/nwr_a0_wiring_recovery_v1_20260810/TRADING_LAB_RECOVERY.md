# Trading Lab Recovery

The existing builder and descriptive review logic were preserved. A governed-registry adapter now supplies current players, Rookie Review assets, blocked prospects, 2026 picks, and future picks to the same two-sided state machine.

Acceptance package:

- NWR gives: Puka Nacua (Finished V1 veteran)
- NWR gets: Jeremiyah Love (Rookie Review) and 2027 1st (Context-Only)
- status: context ready for manual review
- saved into isolated acceptance state
- page reloaded and scenario reopened with all three governed IDs
- Markdown/JSON trade brief controls rendered with source-separated evidence

Authority remains `MANUAL_DESCRIPTIVE_ONLY`. No winner, fairness score, package total, grade, accept, or reject logic was added.
