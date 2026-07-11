# Design Consistency Review

## Result

`PASS_WITH_LEGACY_AUTHORITY_FIELD_NORMALIZED_FAIL_CLOSED`

The 22-file source design is internally consistent on its substantive governance conclusions. The only machine-interpretation defect requiring correction is the mixed legacy `canonical_now` field. The source remains unchanged; the sibling normalized CSV resolves interpretation without asserting new evidence authority.

## Preserved consistencies

- The executive verdict, schema contract, rights/privacy boundary, lifecycle contract, identity contract, migration plan, no-recreate index, and immediate-lane contract all keep player-value consolidation blocked.
- The exact nine source/use purposes and six decision values agree across the schema and rights boundary.
- Missingness, availability, identity, source admission, use permission, locality, duplication, lifecycle, and censoring remain separate dimensions.
- Missing draft evidence cannot imply UDFA; current review status cannot prove confirmed UDFA.
- Name-only identity is not an approved controlling join.
- CFBD downstream source truth, model, training, and production use remains blocked.
- Local-only and off-HQ artifacts remain review/audit references, not canonical player-value sources.
- Conflicting historical scoring and target systems remain separate and require explicit review.
- No-recreate and additive migration language remains non-destructive.

## Legacy-field defect and correction

The 23 source rows contain ten distinct `canonical_now` strings that mix Boolean-looking, scope-qualified, policy-qualified, decision-receipt, local-review, and consumer labels. Treating the field as Boolean would erase scope and could promote blocked evidence.

The correction:

- retains all 23 original strings verbatim;
- labels every one `NON_MACHINE_INTERPRETABLE_LEGACY_SCOPE_FIELD`;
- supplies closed metadata, scope, locality, use, and admission-effect columns;
- fixes `player_value_authority=false` and `production_authority=false` for all rows;
- provides no admitting `source_admission_effect` value;
- requires fail-closed rejection rather than fallback to prose.

## No contradiction introduced

The normalization narrows interpretation only. It does not change the source design verdict, select evidence, alter an existing source/use decision, change a lifecycle/evidence state, resolve a duplicate/conflict, or authorize migration.
