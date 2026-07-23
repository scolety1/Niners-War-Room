# Original blocker closure

Before hardening, all eight required negative controls survived the production
research pipeline. After hardening, the same controls fail closed:

1. future production is rejected at temporal validation;
2. future games are rejected at temporal validation;
3. current-only ADP is rejected for historical rows;
4. current-board rank is rejected as a historical input;
5. label-only promotion cannot satisfy derived exactness;
6. frozen score mutation fails the governed comparator contract;
7. name-preserving player-ID substitution fails exact identity authority; and
8. reversed input order canonicalizes to the same governed bytes, so the
   nondeterministic implementation mutation is detected.

The harness calls the real builder boundaries:
`validate_temporal_records`, `derive_full_row_exactness`,
`validate_exactness_proofs`, `validate_identity_frame`,
`exact_player_id_join`, `validate_frozen_comparator`, `canonicalize_frame`, and
`add_ranks`. It does not rely on source substring assertions or a duplicate
test evaluator.

Result: original blockers `8/8 SURVIVED` before and `8/8 DETECTED` after.
Expanded result: `33/33 DETECTED`.
