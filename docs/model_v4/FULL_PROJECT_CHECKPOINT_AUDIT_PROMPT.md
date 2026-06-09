# Model v4 Full-Project Checkpoint Audit Prompt

Audit Model v4 as a full-project checkpoint.

Context:
This is a local-first dynasty fantasy football decision model for a 10-team, 1QB, non-PPR league with first-down scoring. The user's team is the Niners. The key deadline is June 15.

The project has completed:
- RotoWire/NFL data spine
- first-down and return scoring canonicalization
- rookie/prospect data spine
- identity/source/leakage repairs
- Deep Research requirements lock
- formula contract
- replacement/VORP core
- current value modules
- lifecycle/archetype and confidence layers
- prospect, pick, and dynasty asset review outputs
- Sprint 14A-F decision-board layers
- Sprint 15 cross-model calibration
- Sprint 1 decision-board validation checkpoint

Please audit whether the whole project is on track.

Focus on:
1. Whether the model is still aligned to 10-team, 1QB, non-PPR, first-down scoring.
2. Whether review-only outputs remain safely separated from active app rankings, My Team, War Board, and readiness gates.
3. Whether market/ADP/rankings/projections/mock drafts remain excluded from private football value.
4. Whether first-down and return data are handled honestly.
5. Whether rookie/prospect identity and source risks are still controlled.
6. Whether QB and TE values are properly disciplined for 1QB and no TE premium.
7. Whether veteran/aging and rushing-age risks are visible enough.
8. Whether Sprint 14F and Sprint 1 are ready for human final decision review.
9. Whether any blocker remains before morning human decision work.
10. Whether the next step should be decision review, more source repair, formula repair, UI work, or more research.

Please return:
- Overall verdict
- Critical blockers, if any
- High/medium/low issues
- What looks strong
- What should be checked manually in the morning
- Whether the project is ready to use as a review tool for roster, trade, pick, and rookie draft decisions
