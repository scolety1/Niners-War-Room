# Drafted-Only Feature Gate Summary

Verdict: `YELLOW_ROOKIE_DRAFTED_ONLY_FEATURE_GATE_EVIDENCE_READY_NO_GATE_G`

The primary policy input, `docs/hq/outcomes/outcome_rookie_nflverse_feature_policy_gate_v1_20260630/`, is `YELLOW_MODEL_POLICY_GATE_READY_NO_ACTIVATION`. This rookie lane narrows that posture to drafted-only Rookie Outcomes evidence.

## Current NFLVerse Display Facts

- Player context rows: `294`
- Safe display rows: `281`
- Gated identity rows: `13`
- Rows requiring review: `13`
- Schema fields with `model_use_allowed=false`: `51`
- Outcome/Rookie policy matrix rows with `allowed_for_model_now=false`: `21`

## Drafted-Only Classification

Drafted-only review may proceed only when positive `draft_picks` evidence exists. Draft year, round, overall pick, and drafted team are review context after admission, not independent admission sources. Missing draft capital does not confirm UDFA, and fake round 8 is blocked.

## Approval Boundary

No feature family is approved for model use, training use, source truth, active rookie probabilities, Gate G, Rankings wiring, or app behavior changes.
