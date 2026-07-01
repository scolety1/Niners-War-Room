# Next Gate Recommendations

## Immediate Next Gate

Run the `NFLVerse Label Parity Validator V1` lane using:

- `player_stats_sidecar_artifact.csv`;
- existing Outcome V2 label/source docs;
- existing Rookie Outcome label/source docs where applicable.

## Validator Requirements

The validator should compute:

- matched players;
- unmatched existing labels;
- unmatched NFLVerse sidecar rows;
- identity match rate;
- scoring parity;
- first-down scoring parity;
- censoring parity;
- mismatch categories;
- field-level promote/keep-blocked review decisions.

## Still Blocked

- label truth promotion;
- model input use;
- training use;
- source-truth use;
- active current-player probabilities;
- active rookie probabilities;
- Rankings or app wiring;
- missing stats as zero;
- raw/shared/cache/local export tracking.
