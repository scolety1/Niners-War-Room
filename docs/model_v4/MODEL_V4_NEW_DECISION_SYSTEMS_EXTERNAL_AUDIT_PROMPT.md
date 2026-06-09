# Model v4 External Audit: New Decision Systems And Overall Integrity

You are auditing Model v4, a local-first dynasty fantasy football decision model.

League context:
- 10-team dynasty
- 1QB
- non-PPR
- rushing/receiving first-down scoring
- no TE premium
- User team: Niners
- June 15 roster deadline

Important philosophy:
Do not judge the model by whether it matches consensus rankings. Weird rankings are allowed and may be useful. The audit should decide whether unusual outputs are supported by admitted football evidence, properly labeled as model edge, or caused by missing/source-shaped data.

Hard constraints to verify:
- All outputs remain review-only.
- No final cut/keep/trade/draft recommendations are generated.
- Active rankings, My Team, War Board, readiness gates, and app promotion are not mutated.
- Market, ADP, rankings, projections, mock drafts, big boards, and consensus ranks do not drive private football value.
- Missing data remains missing and is not converted to zero, average, or positive evidence.
- Historical outcomes and similarity comps are context only and do not feed back into ranking formulas.
- Draft-pick trade provenance is context only.

Systems in this packet:
1. Phase 11A formula contract
2. Rookie formula balance repair
3. Startup Slot Simulator
4. Roster Cut Opportunity-Cost Engine
5. Rookie Pick Decision Lab
6. Historical Similarity Engine
7. Player Rank Explainer
8. Source-Risk Heatmap
9. Model Edge Queue
10. Current rookie board and prospect value rows

Audit questions:
1. Overall system integrity:
   - Are the new systems still review-only?
   - Is there any sign of app promotion, active ranking mutation, My Team mutation, War Board mutation, or final recommendation leakage?
   - Do allowed_use / blocked_use fields clearly prevent misuse?

2. Market leakage:
   - Is there any evidence that ADP, market ranks, consensus ranks, projections, mock drafts, or big boards are being used as private football value?
   - Are any market-like fields present only as display/context, if present at all?

3. Decision usefulness:
   - Do the new systems help a human decide, or do they just create more tables?
   - Is Startup Slot useful for comparing rookies, roster players, picks, and potential drops by internal model value?
   - Is Roster Opportunity Cost useful for understanding what is lost by cutting a player without saying who to cut?
   - Is Rookie Pick Decision Lab useful for 1.03, 1.04, 2.04, 2.08, and 5.04?
   - Are missing-baseline cases, especially 5.04 if present, quarantined clearly?

4. Rookie model trust:
   - Are first-round rookies protected enough by factual NFL draft capital without simply copying consensus?
   - Can production / college team share still overpower draft capital in a harmful way?
   - Are day-three or low-capital outliers labeled as edge cases requiring manual review?
   - Are Skyler Bell-type profiles understandable as model edge versus source issue?
   - Are Carnell Tate-type profiles treated fairly when draft capital is strong but college production/share is weaker?

5. Positional discipline:
   - Are QBs appropriately discounted for 10-team 1QB?
   - Are TEs appropriately capped for no TE premium?
   - Are high TE outputs labeled with no-premium caution rather than presented as automatic draft edges?

6. Historical comps and outcome context:
   - Are historical similarity comps useful and honest?
   - Are missing historical outcomes treated as unknown rather than misses?
   - Are immature 2025 outcomes labeled clearly?
   - Are comps and outcome context prevented from feeding back into private value?

7. Explainability:
   - Does Player Rank Explainer make rankings understandable in plain English?
   - Do weird rankings get a clear label such as legitimate_model_edge, source_shape_warning, format_discipline_case, or manual review required?
   - Are source-risk labels clear enough for a human user?

8. UI / workflow:
   - Based on the outputs, what should the app surface first for human review?
   - Are there too many tabs/systems?
   - What should be consolidated, renamed, or made more prominent?

9. Blockers before final human decision review:
   - Identify critical, high, medium, and low issues.
   - Say whether the system is ready for human review tonight.
   - Say whether any formula repair is needed before using the Draft Room / June 15 Review.
   - Say whether any UI/workflow repair is needed before the user reviews decisions.

Required audit output:
- Overall verdict: ready / ready with cautions / needs repair / blocked
- Critical blockers
- High-priority issues
- Medium/low issues
- Market-leakage verdict
- Review-only safety verdict
- Rookie model verdict
- Decision-system usefulness verdict
- UI/workflow recommendations
- Specific notes on:
  - Jeremiyah Love
  - Carnell Tate
  - Jordyn Tyson
  - Makai Lemon
  - Skyler Bell
  - Kenyon Sadiq
  - Fernando Mendoza
  - Niners roster opportunity-cost outputs
  - 1.03 / 1.04 / 2.04 / 2.08 / 5.04 pick decision rows

Do not recommend tuning the model merely to match consensus. Recommend repair only when there is evidence of source-shape error, leakage, missingness mishandling, bad format discipline, or unusable workflow.
