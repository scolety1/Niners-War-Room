# Next Gate Recommendations

## Immediate Next Gate

Build or expose a review-only row-level Outcome label artifact suitable for parity validation.

Required columns:

- player identity key;
- player name;
- position;
- season;
- label family;
- hit status;
- scoring mode;
- censoring status;
- source artifact;
- model/training/source-truth approvals set to false.

## After Row-Level Labels Exist

Rerun Label Parity Validator V1 to compute:

- matched players;
- matched player-seasons;
- unmatched existing labels;
- unmatched sidecar rows;
- identity match rate;
- scoring parity;
- first-down scoring parity;
- censoring parity;
- mismatch categories;
- parity-ready decisions.

## Still Blocked

- label truth promotion;
- model input use;
- training use;
- source-truth use;
- active current-player probabilities;
- active rookie probabilities;
- app wiring;
- missing values as zero;
- hidden sort by sidecar or labels.
