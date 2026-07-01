# Recommended Next Lanes

1. `NFL Usage Historical Experiment Gate V1`
   - Start from the NFL usage historical panel/backtest artifacts, not full scoring parity.
   - Prove as-of windows, leakage controls, and target separation before any experiment.

2. `NFLVerse Lagged Usage Candidate Gate V1`
   - Consider lagged targets, carries, receptions, snaps, and opportunity fields only after as-of proof.
   - Missing values must remain Not enough information.

3. `NFLVerse PBP/Participation Route Metric Feasibility V1`
   - Direct `routes_run`, `TPRR`, and `YPRR` were not confirmed as direct safe tracked fields.
   - Determine whether participation/PBP/FTN can derive them safely without licensed or leakage issues.

4. `NFLVerse Return TD Subtype Source Gate V1`
   - Direct return touchdown subtype remains unavailable in admitted fields.
   - Do not use `special_teams_tds` as a substitute.

5. `NFLVerse Point-In-Time Snapshot Collection Gate V1`
   - Current display safety does not imply historical replay safety.
   - Build extraction/as-of manifests before any model/training proposal.

6. `Rookie Draft/Combine Feature Gate V1`
   - Draft and combine fields look like high-confidence context, but current-player and rookie timelines need separate pre-draft/as-of gates.
