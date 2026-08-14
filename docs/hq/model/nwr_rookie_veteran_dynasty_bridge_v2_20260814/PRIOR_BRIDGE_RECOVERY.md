# Prior bridge recovery

The lane recovered prior work from local-only commits without merging them.

| Commit | Recovered artifact | Classification | Reuse |
|---|---|---|---|
| `dff406ea95bdb9d93438876752089b91b4a5b82a` | Unified rookie/veteran long-term value research | `RESEARCH_ONLY`, `VALIDATION_SPENT`, partly `SUPERSEDED` | Historical 3Y shared-target results and earlier blockers |
| `61b8ffd091de46b7d8cc46d322b8c19e70450298` | Unified training panel/current frame; `MULTI_HORIZON_VECTOR_5Y`; `M5_BOUNDED_QUADRATIC` | `TRAINING_AUTHORIZED`, `VALIDATION_SPENT`, `RESEARCH_ONLY` | Counts, temporal folds, pairwise/position/calibration results |
| `4d137c63b264db1e07f4a46812ea7779cb2d18ae` | Fresh rookie calibration audit | `VALIDATION_SPENT`, `BLOCKED` | Confirms no untouched mature 5Y rookie cohort |
| `451531631b69e0d3efda88718ca0f875a8355348` | Horizon Value Distribution | `BLOCKED`, `RESEARCH_ONLY` | Preserves the failed-closed 0–100 result |
| current base | Finished V1, Outcome V3, Rookie Review V2 candidate, Redraft, Unified Research Preview, Desktop | mixed; see `DATA_AUTHORITY.md` | Product composition only |

The approximately 8,302 veteran states, 5,238 nominal complete-5Y veteran states, 1,041 rookie states, and 720 nominal complete-5Y rookie rows were mechanically found in the prior panel artifacts. This lane does not call those labels outcome-complete: the recovered builder counted calendar slots and converted absent target rows to zero.

The strongest Rookie candidate also exposed a Windows checkout-only hash failure: its generated LF artifacts lacked path-level LF attributes. The bridge branch adds those attributes so the already-committed bytes validate locally; no Rookie artifact content was regenerated or promoted.
