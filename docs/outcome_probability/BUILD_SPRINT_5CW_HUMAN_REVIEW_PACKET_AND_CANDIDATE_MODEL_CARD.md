# Sprint 5CW: Human Review Packet And Candidate Model Card

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_HUMAN_REVIEW_PACKET_AND_MODEL_CARD`

Sprint type: `REVIEW_PACKET_NO_PRODUCTION_NO_DISPLAY`

## 1. Scope

Sprint 5CW prepares the human review packet and candidate model card for the Phase 5 local-only candidate modeling results. This sprint did not run additional modeling, run current-player inference, create production model artifacts, create serialized model files, create app-readable outputs, create exact display percentages, create coarse bands, wire app display, alter rankings/sorting, create hidden sort keys, create promoted artifacts, touch rookie files, edit or commit `data/`, stage or commit `local_exports/`, push, or deploy.

No script or local-only export was required.

## 2. Candidate Model Card

### Intended Use

The candidate model is an internal research artifact for historical local-only evaluation of veteran outcome threshold heads. Its intended use is to support human review and decide whether a later Phase 6 production-candidate proposal may be drafted.

### Non-Use Cases

The candidate model must not be used for:

- current-player probabilities
- current-board inference
- app display
- exact display percentages
- coarse display bands
- rankings/sorting
- hidden sort keys
- promoted artifacts
- rookie evaluation
- production model deployment

### Historical Data Coverage

The evaluation uses 2010-2019 historical target seasons from the local-only historical feature/label package chain. Features are completed prior-season source-safe inputs only. The 5CK-R Taysom Hill 2018 QB to 2019 TE accepted exclusion remains excluded.

### Approved Candidate Heads

Accepted conservative candidate heads:

- `qb_t12`
- `rb_t12`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Caution heads:

- `qb_t18`
- `qb_t24`
- `rb_t24`
- `te_t18`
- `te_t24`

Deferred heads:

- `rb_t36`
- `rb_t48`
- `wr_t48`

Blocked heads:

- `qb_t6`
- `rb_t6`
- `wr_t6`
- `te_t3`
- `te_t6`

### Feature And Source Restrictions

Allowed features are prior completed-season source-safe features only:

- prior games and availability counts
- prior passing/rushing/receiving yards
- prior rushing/receiving first downs
- prior receptions
- prior NWR finish rank
- prior NWR PPG

Forbidden inputs remain excluded:

- fantasy totals
- EPA
- WOPR/RACR/PACR/Dakota
- target-share or air-yard-share fields
- ADP
- projections
- public rankings
- market/trade values
- RotoWire values/outlooks/projections
- prior fantasy draft history
- legacy `private_score`
- target-year outcomes as features
- same-season final stats as preseason features

### Calibration And Sanity Results

5CV found a GREEN audit result for human review. All evaluated heads improved Brier and log loss versus base-rate baseline, but caution heads remain caution because of calibration thinness or weaker aggregate profile.

No head is calibrated enough for exact display percentages or coarse bands.

### Known Limitations

- Historical window is 2010-2019 only.
- Single-season holdout folds can create thin calibration bins.
- Some thresholds have display-semantics risk even when aggregate metrics look useful.
- Return scoring remains limited by unavailable granular return stats.
- Multi-position cases require explicit policy before production consideration.
- The candidate model is not production-ready.

### Output Quarantine Requirements

All model evidence must remain under sprint-specific `local_exports/outcome_probability/` directories. `local_exports/` must not be staged or committed. No app-readable output path may be written.

## 3. Human Review Checklist

Before any Phase 6 proposal, a reviewer must confirm:

1. accepted candidate heads remain limited to the conservative set
2. caution heads are not promoted without stronger calibration evidence
3. deferred and blocked heads remain excluded
4. rolling historical folds remain time-aware
5. no random split or target leakage is introduced
6. feature allowlist remains source-safe
7. forbidden feature scans are clean
8. no current-player inference has occurred
9. no row-level prediction export is app-readable
10. no serialized model artifact exists
11. no production model artifact exists
12. no app wiring or app-readable output exists
13. no ranking/sorting or hidden sort key exists
14. exact display percentages remain blocked
15. coarse display bands remain blocked
16. rollback and quarantine plan is documented

## 4. Review Questions By Head Tier

Accepted heads:

- Are `qb_t12`, `rb_t12`, `wr_t12`, `wr_t24`, `wr_t36`, and `te_t12` sufficiently stable for a Phase 6 production-candidate proposal?
- Should any accepted head require abstention rules before production-candidate evaluation?
- Are the threshold semantics understandable without implying ranking or certainty?

Caution heads:

- Do `qb_t18`, `qb_t24`, `rb_t24`, `te_t18`, and `te_t24` need another calibration audit before any production-candidate proposal?
- Should any caution head be excluded from Phase 6 entirely?

Deferred and blocked heads:

- Should broad RB/WR thresholds stay deferred until a separate semantics audit?
- Should sparse top-end thresholds remain blocked until more historical support exists?

## 5. Remaining Approvals Required

Before any production proposal, HQ must separately approve:

- exact production-candidate head list
- production-candidate training/evaluation plan
- artifact quarantine and rollback plan
- calibration and abstention gates
- model-card update after production-candidate evaluation
- app-display contract, if display is ever considered

5CW does not approve production execution.

## 6. Remaining Blockers

The following remain blocked:

- current-player probabilities
- exact display percentages
- coarse display bands
- app-readable outputs
- production model artifacts
- app wiring
- rankings/sorting
- hidden sort keys
- promoted artifacts
- rookie files
- `data/` commits
- `local_exports/` commits
- push/deploy

## 7. Verdict

5CW verdict: GREEN.

The human review packet and candidate model card are complete, conservative, and do not approve production execution.

5CX is approved to run next as a Phase 5 production-proposal readiness verdict.

## 8. Checks

Checks run:

- 5CU/5CV docs and local evidence reviewed
- `git diff --check` passed

No Python files changed in 5CW, so `python -m py_compile`, Ruff, and pytest are not required.
