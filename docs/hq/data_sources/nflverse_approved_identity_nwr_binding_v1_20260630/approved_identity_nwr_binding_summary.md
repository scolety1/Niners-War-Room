# Approved Identity to NWR Binding Summary

Verdict: `YELLOW_PARTIAL_BINDING_PACKET_READY`

The packet binds 41 of 43 human-approved NFLVerse identity overlay rows to review-only NWR player IDs. 2 rows remain gated because the binding evidence is not strong enough for this lane.

## Counts

| Metric | Count |
| --- | ---: |
| Approved overlay rows reviewed | 43 |
| Bound review-only rows | 41 |
| Needs more information | 2 |
| Ambiguous blocked | 0 |
| Non-approved rows left unbound | 11 |
| Safe existing display rows checked for NWR/Sleeper ID equivalence | 240 / 240 |

## Binding Status

Rows marked `BOUND_REVIEW_ONLY` may be consumed by a later Data Hygiene rebuild lane as review/display-only identity bindings. They are not app activation and do not expose any player context by themselves.

Rows marked `NEEDS_MORE_INFO` must remain unbound until a later identity review resolves the NWR/Sleeper binding evidence.

## Non-Approved Rows

The 11 non-approved rows from the overlay packet were not bound. Their recommendations are:

| Recommendation | Count |
| --- | ---: |
| `RECOMMEND_HUMAN_REVIEW` | 4 |
| `RECOMMEND_KEEP_BLOCKED` | 7 |


## Current Gating

- No player context artifact was rebuilt.
- No app pages were changed.
- No model, training, source-truth, rank, hidden-sort, trade-value, or pick-value flags were enabled.
- `ff_rankings` was not used.
- DynastyProcess IDs were not used as binding evidence.
