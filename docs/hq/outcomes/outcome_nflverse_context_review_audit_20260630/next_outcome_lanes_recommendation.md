# Next Outcome Lanes Recommendation

## Safe Now

- Use tracked NFLVerse player context as review/display context for safe rows.
- Keep Outcome V2 probabilities unchanged.
- Keep Rookie Outcome Gate G closed.
- Keep missing data as `Not enough information`.
- Use positive `draft_picks` evidence for drafted-only review admission.

## Safe After Data Hygiene Hardening

- Accept or reject the 43 safe identity resolution proposals in the NFLVerse
  identity review packet.
- Rebuild the player-context artifact only after Data Hygiene/HQ approval.
- Add a current/future schedule context lane if schedule data becomes available.
- Harden age/source and identity coverage reporting.

## Safe Only After Model Gate

- Any NFLVerse feature family as model input.
- Any Rookie Outcome model training.
- Any active Rookie Outcome probabilities.
- Any new current-player Outcome probability artifact.
- Any use of injury/availability/depth/snap/player_stats fields as predictive
  model inputs.

Required gates:

- source-policy gate
- identity gate
- as-of/leakage gate
- missingness policy gate
- validation/calibration gate
- explicit user approval

## Blocked

- `ff_rankings`
- market/ADP/DynastyProcess as model input
- CFBD production as model input without explicit approval
- UDFA modeling from draft absence or roster/stat appearances
- injury risk, medical risk, comeback probability, or recovery projection
- schedule/opponent/bye display from the current artifact
- hidden sort/rank/trade/pick-value behavior

## Recommended Next Lane

1. `NFLVerse Player Context Data Hygiene Identity Hardening`
2. `Outcome Feature Candidate Policy Gate`
3. `Veteran Outcome Review-Context Display Cleanup`
4. `Rookie Drafted-Only Label/Feature Feasibility Review`

Do not start model training until an explicit model gate is requested and
approved.
