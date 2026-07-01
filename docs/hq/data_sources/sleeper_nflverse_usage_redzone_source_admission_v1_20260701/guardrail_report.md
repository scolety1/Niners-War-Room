# Guardrail Report

## Preserved

- `review_only=true` for all packet rows.
- `model_use_allowed=false` for all packet rows.
- `training_allowed=false` for all packet rows.
- `source_truth_allowed=false` for all packet rows.
- No app pages changed.
- No Rankings, Player Compare, Trading Lab, Development Lab, Draft Room, Outcome, model, rank, tier, source-truth, hidden-sort, probability, recommendation, trade-value, or pick-value behavior changed.
- No latest pointers changed.
- No raw Sleeper responses tracked.
- No `C:\NWR_SHARED_DATA`, `C:\NWR_LOCAL_SECRETS`, `local_exports`, cache, runtime JSON, private/vendor/Gmail, or secret files tracked.
- No full fantasy scoring parity, return touchdown subtype, route/TPRR/YPRR, probability, or production-model approval was created.
- No route proxies were created from participation data.

## Source Handling

Sleeper API responses were sampled live only to produce compact receipt rows. Approved local NFLVerse cache files were inspected read-only for row counts and headers; raw files were not copied into the repo and must not be read by app pages.

## Approval Posture

This is source admission evidence only. It does not approve production model use, training use, label truth, source truth, current-player predictions, app wiring, or ranking behavior.
