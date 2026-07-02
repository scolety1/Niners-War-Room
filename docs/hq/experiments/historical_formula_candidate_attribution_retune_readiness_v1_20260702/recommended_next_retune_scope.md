# Recommended Next Retune Scope

Decision: `GO_TARGETED_DYNASTY_STABILITY_RETUNE`

Recommended next lane: `Historical Formula Candidate Dynasty Stability Retune V1`.

Scope:
- Start from the current useful usage signal.
- Add or test a bounded review-only `multi_year_production_anchor`.
- Add or test a bounded `career_peak_or_ceiling_anchor`.
- Add or test a conservative `young_wr_te_stability_guard`.
- Keep market/ADP/vendor/projection fields context-only and excluded from source truth.
- Do not run a broad formula search.
- Do not promote or wire anything into NWR.

Reason: the candidate signal is useful, but key WR/TE cornerstone cases still show risk of one-year overreaction and underweighting dynasty stability.
