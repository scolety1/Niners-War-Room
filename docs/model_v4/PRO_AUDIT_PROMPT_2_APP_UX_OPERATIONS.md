# Pro Audit 2: App UX, Tabs, Pages, And Operating Flow

You are auditing the Model v4 local Streamlit app from a product/decision-workflow perspective.

Goal:
Verify that the app is understandable, decision-focused, and organized around what a fantasy manager actually needs to do before the June 15 deadline. Identify page, tab, naming, filtering, and workflow improvements.

Current desired app structure:
- Command Center
- Decision Board
- Player Board
- Trade Lab
- Draft Room
- Settings

Important context:
- Model v4 is now in application/refinement stage, not pure formula-checking stage.
- The user wants fewer pages and fewer confusing tabs.
- The user wants the Player Board to be the huge understandable table with formula columns and explanations.
- Data Health should live inside Settings.
- Draft Board has been renamed Draft Room.
- Decision Board should make the top-five drop decision obvious.

Audit focus:
1. Sidebar/page structure:
   - Is the visible navigation minimal and intuitive?
   - Are legacy/debug pages hidden appropriately?
   - Are names clear enough for a non-engineer to use?
2. Decision Board:
   - Is the Required Top-Five Release Slot easy to find?
   - Is the distinction between top-five drop and generic roster pressure clear?
   - Are review-only labels clear without being overwhelming?
3. Player Board:
   - Does the big formula table show the right columns?
   - Are column names understandable?
   - Are filters useful and not noisy?
   - Are receipts/warnings accessible without dominating the page?
4. Trade Lab:
   - Are Sell Candidates, Buy Targets, Market Gap, Model vs Market, and Package Builder logically separated?
   - Is normalized league rank / ADP market gap presented clearly?
   - Does the page prevent market context from looking like model truth?
5. Draft Room:
   - Does it feel like a draft-room workflow instead of a raw rankings table?
   - Are pick/roster/draft states understandable?
6. Settings:
   - Is Data Health in the right place?
   - Are source/model-lab controls safely tucked away?
7. Overall operating flow:
   - If a user opens the app at night before decisions, what should they click first?
   - What should be removed, merged, renamed, or made less prominent?

Please answer with:
1. Overall UX verdict
2. Top 10 improvements ranked by impact
3. Any confusing labels or tabs
4. Any places where review-only safety language is too much or too little
5. Recommended final navigation structure
6. Recommended changes to Player Board columns/filters
7. Recommended changes to Decision Board and Trade Lab
8. Whether the app is ready for human final decision review

Constraints:
- Do not recommend adding many new pages.
- Prefer fewer, clearer workflows.
- Do not recommend hiding safety-critical warnings.
- Do not turn review-only outputs into final recommendations.
