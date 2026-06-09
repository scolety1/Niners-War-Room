# Model v4.8.1 Data Usage Deep Research Audit Prompt

You are auditing a dynasty fantasy football decision model and app for data correctness, evidence separation, and review-only safety.

League/context:
- 10-team dynasty
- 1QB
- non-PPR
- rushing/receiving first-down scoring
- no TE premium
- User team: Niners
- June 15 roster deadline

Important constraints:
- Outputs are review-only.
- No final cut/keep/trade/draft recommendations.
- No active rankings, My Team, War Board, readiness gate, or app promotion mutation.
- Market/ADP/ranking/projection/mock/big-board data must not drive private football value.
- Missing evidence must remain missing, not become zero, average, or positive evidence.
- Draft-pick trade provenance is context-only.
- Historical outcomes and similarity/bucket outputs are display-only calibration context and must not feed back into ranking formulas.

Audit goal:
Determine whether the current app and review outputs are using the right data in the right way, and whether the UI/display layers faithfully communicate source risk, market context, confidence, and review-only status.

Files included:
- Phase 11A formula contract and allowed/blocked field registries
- Loader guard report
- Warning dictionary
- Source risk heatmap outputs
- Current player value and dynasty asset value review rows
- Prospect/rookie value rows and components
- Rookie draft board
- Startup slot simulator rows and outcome buckets
- Rookie pick decision lab rows
- Roster opportunity cost rows
- June 15 decision board rows
- Model edge queue rows

Please review for:
1. Evidence separation:
   - Are private model values traceable to allowed evidence surfaces?
   - Are market/ADP/rank/projection fields excluded from private football value?
   - Are market fields clearly display-only where present?
   - Are historical outcomes/similarity/buckets display-only rather than formula inputs?

2. Missing-data correctness:
   - Does missing evidence remain missing?
   - Are confidence caps/source-risk labels applied when data is partial, source-limited, stale, or quarantined?
   - Are low-evidence players prevented from appearing falsely certain?
   - Are manual-only pick baselines, especially 2026 5.04, handled honestly?

3. League-format correctness:
   - Does 10-team 1QB discipline show up in QB values and warnings?
   - Does no-TE-premium discipline show up in TE values and warnings?
   - Are first-down and return-scoring contexts used appropriately?
   - Are RB/WR/QB/TE values explainable for this format?

4. Decision-layer correctness:
   - Does the Decision Board remain review-only?
   - Does roster opportunity cost avoid final cut/keep calls?
   - Does pick decision lab avoid final draft recommendations?
   - Does trade context avoid final trade recommendations or offer generation?
   - Are allowed_use and blocked_use fields doing their job?

5. Rookie model/data usage:
   - Is draft capital admitted as a strong anchor without simply tuning to consensus?
   - Can production/team-share still overpower draft capital in ways that look like source-shape errors?
   - Are day-three outliers labeled as model edges or manual scout rows?
   - Are TE/QB rookie values disciplined for no TE premium / 1QB?
   - Are outcome buckets honest about small sample sizes?

6. Display fidelity:
   - Do displayed columns make it clear what is model value vs market context vs source risk?
   - Are warning labels sufficient for a human to understand risk?
   - Is there any column name that could mislead a user into thinking the model made a final recommendation?

Output format:
- Overall verdict: data usage safe / mostly safe with repairs / unsafe before review
- Critical blockers
- High-priority repairs
- Medium/low-priority repairs
- Evidence leakage findings, if any
- Missing-data handling findings
- Position/league-format findings
- Rookie/data-specific findings
- UI display/data-label findings
- Final recommendation: safe for human review or needs repair first

Be brutally honest. Do not recommend tuning the model to consensus rankings. Weird rankings are acceptable if the evidence path is clean and warnings make the uncertainty visible.
