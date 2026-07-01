# Next Dataset Builder Prompt

Build `Core Usage Review Dataset V1`, a review-only Season N to Season N+1 lagged usage candidate dataset from the approved candidate matrix.

Requirements:

1. Use only rows where `recommended_for_next_dataset_builder=true`.
2. Include core build-ready families: targets, carries, receptions, rushing/receiving yards, air yards, YAC, first downs, offensive snaps, snap share, touches, and opportunities.
3. Emit `feature_season`, `target_season`, `source_as_of`, `player_id`, `position`, and source artifact fields.
4. Preserve source component fields for derived features such as touches and opportunities.
5. Do not use labels as features.
6. Do not use market, ADP, DynastyProcess, projections, analyst ranks, vendor opinions, rank values, or hidden sort fields.
7. Missing values must remain `Not enough information` unless an observed row or approved zero-eligibility denominator proves zero.
8. Do not build routes, TPRR, or YPRR unless a rights-cleared upload is already available and separately admitted.
9. Keep red-zone out of Core V1 unless a source-admit/coverage-audit lane approves `rec_rz_tgt`, `rush_rz_att`, or `pass_rz_att` semantics.
10. Set all model/training/source-truth/rank/app/probability approval flags to false.
11. Stop if point-in-time, identity, or source schema requirements are missing.

Do not train or tune a model in the dataset builder lane.
