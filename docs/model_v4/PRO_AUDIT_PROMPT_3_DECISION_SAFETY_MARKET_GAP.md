# Pro Audit 3: Decision Safety, Leakage, And Market-Gap Layer

You are auditing Model v4 for decision safety, market leakage, and the new market-gap feature.

Goal:
Verify that the system is safe to use for human decision review, especially after adding normalized league-rank and dynasty startup ADP scores.

New feature:
- League rank is normalized to 0-100 where league rank 1 = 100.
- Dynasty startup ADP is normalized to 0-100 where ADP 1.0 / 1.01 = 100.
- If our model is high while league rank and ADP scores are low, that can create a review-only trade-for candidate.
- If our model is low while league rank and ADP scores are high, that can create a review-only trade-away or do-not-overpay signal.
- These market/reference scores must never become private football value.

Audit focus:
1. Market-gap safety:
   - normalization formula correctness
   - rank 1 and ADP 1.0 map to 100
   - worst available rank/ADP maps near 0
   - missing ADP remains missing
   - ADP/league rank do not drive private football value
2. Leakage checks:
   - no ADP/rank/projection/consensus/mock/big-board leakage into private value
   - market gap is context/review-only
   - market gap cannot silently affect model score, keep priority, or VORP
3. Decision safety:
   - trade-for/trade-away labels are framed as review-only, not recommendations
   - top-five release decision is separated from ordinary roster pressure
   - June 15 decision board does not mutate My Team, War Board, active rankings, or readiness gates
4. Output clarity:
   - “trade_for_candidate_review” and similar labels are understandable enough
   - warnings are visible where data is missing
   - market-gap rows with missing ADP are not overtrusted
5. App/data architecture:
   - market gap belongs in Trade Lab and Player Board context, not formula core
   - Settings/Data Health separation is safe
   - hidden legacy pages do not create accidental conflicting workflows

Please answer with:
1. Overall safety verdict
2. Critical blockers
3. High/medium/low issues
4. Whether normalized league rank and ADP are implemented safely
5. Whether market-gap labels are too strong, too weak, or clear enough
6. Whether any final-decision language leaks into review-only pages
7. Whether the app is ready for human decision use after these changes
8. Specific recommendations to harden safety and clarity

Constraints:
- Do not recommend using market data as private football value.
- Do not recommend automatic final trade/cut/draft decisions.
- Missing data must remain missing.
- Review-only labels must stay visible.
