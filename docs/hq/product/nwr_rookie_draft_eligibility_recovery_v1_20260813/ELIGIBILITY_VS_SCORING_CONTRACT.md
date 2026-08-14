# Eligibility vs Scoring Contract

These states are independent:

1. `asset_exists`: governed official football/draft asset exists.
2. `draft_eligible`: owner may draft the asset using an exact player identity or a
   unique governed official-draft asset identity.
3. `model_score_eligible`: frozen Rookie Review admitted a score and rank.
4. `authority_status`: `SCORED_REVIEW_ONLY`, `UNSCORED_MANUAL_REVIEW`,
   `BLOCKED_IDENTITY`, or another declared authority.
5. `selectable`: workflow action gate; never derived from missing score alone.

Missing score/rank remains null/UNKNOWN. It is never zero, imputed, or converted to
a veteran value. Stable registry IDs remain unchanged so saved owner context survives.
