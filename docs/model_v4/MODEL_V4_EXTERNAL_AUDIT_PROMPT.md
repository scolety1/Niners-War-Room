# Model v4 External Audit Prompt

You are an independent senior fantasy-football model auditor and data-quality
investigator.

Project context:

This is a local-first deterministic dynasty fantasy football model for a
10-team, 1QB, no-PPR league with:

- passing yards: 1 point per 30 yards
- passing TD: 3
- interception: -1
- rushing yards: 1 point per 10 yards
- rushing TD: 4
- receiving yards: 1 point per 10 yards
- receiving TD: 4
- reception: 0
- rushing/receiving first down: 0.4
- fumble lost: -1
- 3 WR, 2 RB, 1 TE, 2 flex
- no TE premium
- deep benches
- 23 keepers
- roster-declaration forced-release rule based on each roster's league-rank top five

Important constraint:

Model v4 is currently review-only. It has not replaced the active app rankings,
My Team, War Board, draft board, or readiness gates. Your job is to audit
whether Model v4 is good enough to promote later, not to assume it is already
decision-ready.

Files included in the packet:

- Phase 4 checkpoint
- Phase 3 checkpoint
- Phase 4 WR evidence audit
- v4 preview rankings
- v4 normalized component rows
- v4 receipt rows
- v4 source coverage rows
- v4 warning rows
- Phase 3 sanity fixture dry run
- Phase 3 named-player review
- formula config
- formula lane architecture
- position formula proposal
- feature/source contract
- receipt requirement contract
- truth-set player universe and coverage audit
- league rules and offseason ranking locks

Audit goals:

1. Determine whether the Model v4 review-only rankings make football sense for
   this specific league format.
2. Determine whether WR values, especially the elite WR tier, are low because of:
   - missing evidence
   - route data unavailable
   - first-down projection gap
   - source coverage gaps
   - normalization issue
   - lifecycle issue
   - true formula imbalance
   - acceptable model disagreement
3. Audit cross-position balance:
   - elite RBs versus elite WRs
   - aging RBs versus younger cornerstone RBs
   - 1QB quarterback suppression
   - no-premium TE suppression
   - young-player bridge values versus established veterans
4. Audit confidence labels:
   - do confidence labels match source quality?
   - are weak/proxy/missing-source players clearly marked?
   - are not-applicable sections correctly excluded from failure counts?
5. Audit source integrity:
   - does the model correctly separate real evidence, derived evidence, proxy evidence, context-only evidence, missing evidence, and unavailable data?
   - are route metrics honestly quarantined?
   - are market and league-rank inputs kept out of private Dynasty Asset Value?
6. Audit receipts:
   - can surprising scores be explained from component contributions?
   - are raw fields, source statuses, warnings, and unavailable reasons visible enough?
   - do receipts reconcile to preview component scores?
7. Audit readiness:
   - what blocks roster-decision use?
   - what blocks draft readiness?
   - what blocks final money-decision readiness?

Required output:

1. Executive verdict:
   - promote to app planning
   - patch data/source issues first
   - patch formula/normalization issues first
   - run another audit after specific fixes
2. Confirmed strengths.
3. Confirmed bugs.
4. Likely bugs needing local verification.
5. Data/source gaps that should block promotion.
6. Data/source gaps that are acceptable if clearly labeled.
7. Formula or normalization concerns, with evidence.
8. Player/tier findings by group:
   - elite RBs
   - elite WRs
   - young bridge players
   - QBs
   - TEs
   - aging veterans
9. Exact patch list before promotion.
10. Exact patch list that can wait.
11. Any finding you believe is a false positive or acceptable model disagreement.

Rules:

- Do not tune rankings to match opinions.
- Do not assume consensus rankings are automatically correct.
- Use receipts and source coverage to explain every major concern.
- Do not recommend using unavailable/restricted route data as if it exists.
- Do not recommend market data inside private Dynasty Asset Value.
- Do not recommend league rank inside Dynasty Asset Value.
- If a ranking looks surprising but the receipts support it, say so.
- If the receipts are insufficient to justify a ranking, identify the missing evidence.
- Be blunt. The goal is to decide whether this model can be trusted later.
