# Lagged Usage Candidate Summary

Verdict: `YELLOW_LAGGED_USAGE_CANDIDATE_GATE_READY_REVIEW_ONLY`

This packet defines practical season N to season N+1 review-only feature candidates so NFLVerse work can proceed without waiting for full same-week fantasy scoring parity. It is a policy/spec packet only.

## Candidate counts by bucket

| Bucket | Count |
| --- | ---: |
| `RECOMMENDED_REVIEW_DATASET_BUILDER` | `20` |
| `PENDING_SOURCE_ADMISSION_OR_DEFINITION_REVIEW` | `4` |
| `EXCLUDED_OPTIONAL_QUARANTINED_OR_NO_SAFE_SOURCE` | `5` |

## Recommended dataset-builder features

- `targets`
- `carries / rush attempts`
- `receptions`
- `touches`
- `opportunities`
- `rushing yards`
- `receiving yards`
- `receiving yards after catch (YAC)`
- `passing attempts`
- `passing completions`
- `passing yards`
- `passing TD`
- `passing INT`
- `rushing first downs`
- `receiving first downs`
- `passing first downs`
- `offensive snaps`
- `snap share`
- `receiving air yards`
- `passing air yards`

## Pending red-zone/source-admit fields

- `red-zone targets`
- `red-zone carries`
- `red-zone pass attempts`
- `red-zone aggregate opportunities (rz_att unresolved)`

## Excluded optional fields

- `air yards share`
- `true routes run`
- `TPRR`
- `YPRR`
- `direct return touchdown subtype`

All recommended fields are approved only for a future review-only dataset builder. Model use, training, source truth, rank logic, hidden sort, probability output, and app behavior remain false.
