# NWR Current Role + Elite Youth Correction Gauntlet V1 — Preregistration

Date frozen: 2026-08-13

## Scope and authority

- Champion Dynasty authority: Finished V1, SHA-256 `263cc8aa050c4670bf5ed22701d7b04801e143480c5630b98e00dd08d2968ce4`.
- Champion Redraft authority: `NWR_REDRAFT_2026_STATUS_FILTERED_PRIOR_SEASON_PERSISTENCE_V1`, governed 2026 snapshot dated 2026-08-08.
- Market/ADP, analyst ranks, and named-player outcomes are excluded from challenger fitting and selection.
- Bowers, Jeanty, and Sutton are held out diagnostic cases. They are read only after challenger disposition.

## Frozen hypotheses and bounded families

| Hypothesis | Challenger | Frozen feature definition | Required historical labels |
| --- | --- | --- | --- |
| H1: injury-shortened elite-young suppression | C1 availability/ability decomposition | completed-season production rate, games, pre-target-season point-in-time injury availability, age, position, prior elite-production flag | next-season dynasty-value proxy and availability outcome |
| H2: short-history elite-youth suppression | C2 youth bridge | draft capital, age, completed rookie/second-year production, completed rookie role, first downs, position; all facts frozen before the target season | subsequent-season ordering/value outcome |
| H3: persistence after role change | R1 role-competition adjustment | prior team opportunity, player share, incoming/outgoing completed-season volume, team/QB continuity, position, pre-target-season transaction/roster status | next-season player stat line and fantasy points |
| H3 (only after R1 passes) | R2 role + efficiency | R1 plus YPRR/TPRR/route participation/first-downs per route only if every feature has legal historical parity | same R1 labels |
| Elite-TE guard | C3 TE refinement | C1/C2 evidence plus position-specific historical TE labels and an ordinary-TE control cohort | forward TE value and 1QB replacement impact |

No C4 combination is evaluated unless both of its component challengers independently pass.

## Leakage rules

1. Each target season uses only features known before that season; no retroactive roster, depth, injury, market, or outcome label is allowed.
2. Training seasons must be strictly earlier than the evaluated target season; the final temporal holdout is never used to choose a threshold.
3. Player IDs must join exactly. Missingness stays missing; it is never zero, healthy, or role-stable by default.
4. A current-news fact may support a current sensitivity display only. It is not a historical model feature until it has point-in-time historical parity.

## Frozen metrics and promotion gates

### Dynasty C1/C2/C3

All must pass:

- Exact Finished V1 historical replay is available and byte-reproducible.
- On the final temporal holdout, the challenger improves the selected ordering metric by at least 0.010 Spearman **and** improves target-cohort mean absolute rank error by at least 2% relative to Champion.
- H1/H2 target cohort improves by at least 5%; non-target veterans may not worsen by more than 1%; ordinary TE controls may not worsen by more than 1%.
- No position worsens by more than 2%, and 1QB Top-24 accuracy may not decline by more than one player.
- Source authority, exact identity, point-in-time safety, and receipt-level interpretability all pass.

### Redraft R1/R2

All must pass:

- Exact Champion replay exists for each target season.
- Final temporal holdout overall MAE improves by at least 2%, role-change-cohort MAE improves by at least 5%, and role-stable MAE does not worsen by more than 1%.
- Top-24 and Top-60 membership accuracy each decline by no more than one player; at least one improves or the challenger is rejected.
- Each event group is mutually exclusive using a pre-target-season event ledger: `HIGH_COMPETITION_ADDED`, `COMPETITION_REMOVED`, `ROLE_STABLE`, `PLAYER_CHANGED_TEAM`, `QB_CONTEXT_CHANGED`, `RETURN_FROM_INJURY`.
- No analyst consensus/ADP, non-recreatable route/separation data, or current-only roster/depth/injury data may enter the model.

## Selection rule

If required evidence is missing, the family is `BLOCKED_NO_SELECTION`, not a failed performance result. No player-specific adjustment, threshold change, or post-hoc feature selection is permitted. A passed challenger would be documented as `READY_FOR_OWNER_MODEL_APPROVAL`; this packet cannot promote it to production.
