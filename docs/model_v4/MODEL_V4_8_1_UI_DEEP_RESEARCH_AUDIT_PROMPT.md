# Model v4.8.1 UI Deep Research Audit Prompt

You are auditing a local-first dynasty fantasy football decision app for human usability.

League/context:
- 10-team dynasty
- 1QB
- non-PPR
- rushing/receiving first-down scoring
- no TE premium
- User team: Niners
- June 15 roster deadline

Important constraints:
- The app is review-only.
- It must not create final cut/keep/trade/draft recommendations.
- It must not mutate My Team, War Board, active rankings, readiness gates, or app promotion.
- Market/ADP/rankings/projections may appear only as display/context, not as private model value.
- The user is a human manager trying to answer concrete questions quickly, not a developer trying to inspect raw tables.

Audit goal:
Decide whether the current frontend is good enough for human review tonight, and identify the highest-leverage UI fixes before final decision review.

Files included:
- Frontend repair prompt history
- Navigation definition
- Main user-facing Streamlit page files
- Shared UI/detail components
- Screenshots of Review Workflow, Decision Board, Draft Room, Player Board, Trade Review, Trade Context Drill-Down, and Settings

Please review for:
1. Navigation clarity:
   - Does the reduced navigation make sense?
   - Are the page names understandable?
   - Is it obvious where to start?
   - Is it obvious when to use Decision Board vs Draft Room vs Player Board vs Trade Review?

2. Page usefulness:
   - Review Workflow: does it help, or is it clutter?
   - Decision Board: does it surface the top-five drop rule, cut pressure, and replacement context before raw tables?
   - Draft Room: can a user understand rookie clusters, pick zones, manual-only baselines, and candidate risk?
   - Player Board: can a user inspect model scores, age/context, market display context, and warnings without drowning?
   - Trade Review: does it feel like context/drilldown rather than an offer generator?
   - Settings: does it explain data health/data packs without implying destructive actions?

3. Human language:
   - Identify labels that are still too technical.
   - Identify rows/columns that need plainer names.
   - Identify warnings that need more direct human wording.
   - Note whether "review-only" is clear without becoming noise.

4. Layout and density:
   - Are the screenshots readable at normal desktop size?
   - Are cards/tables/buttons clipping or overflowing?
   - Are raw/technical tables hidden behind Advanced sections where appropriate?
   - Are there too many metrics or columns on first screen?

5. Decision workflow:
   - Could a user answer, "Who are my top drop candidates?"
   - Could a user answer, "What am I giving up if I cut this player?"
   - Could a user answer, "What should I compare at 1.03/1.04/2.04/2.08/5.04?"
   - Could a user answer, "Why is this player ranked here?"
   - Could a user answer, "Is this weird ranking a model edge or a source problem?"

6. Missing frontend features:
   - What should be added before final human review?
   - What should be removed or hidden?
   - Where should age, team, position, source risk, and warning badges appear?
   - What one or two "killer views" would make the app much easier to use?

Output format:
- Overall verdict: ready / usable with minor fixes / needs repair before human review
- Critical blockers
- High-priority UI fixes
- Medium/low-priority UI fixes
- Page-by-page notes
- Suggested ideal review workflow for the user
- Any labels to rename
- Any sections to hide, merge, or promote
- Final recommendation: what to patch next

Be blunt. If a page is confusing, say so. Do not evaluate the formulas unless the UI presentation makes the data misleading.
