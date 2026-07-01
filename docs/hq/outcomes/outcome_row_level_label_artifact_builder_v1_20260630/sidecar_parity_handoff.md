# Sidecar Parity Handoff

## Current parity status

NFLVerse Label Parity Validator V1 remains partial.

The weekly first-down sidecar is row-level and source-safe for review, but the Outcome label side is not row-level in tracked git artifacts. Therefore, full parity cannot compute:

- matched player-season label rows;
- unmatched label rows;
- unmatched sidecar rows by label window;
- scoring parity at label-row grain; or
- censoring parity at label-row grain.

## Handoff to next gate

The next parity-enabling lane should create one of these, with explicit approval:

1. A tracked compact row-level Outcome label artifact derived from the existing Outcome V2 label factory outputs; or
2. A tracked compact row-level Outcome label artifact recomputed from approved factual player-season inputs.

## Minimum handoff schema

Use `outcome_row_level_label_schema.csv` as the required contract.

## Safety requirements for the next lane

- Do not read raw/shared files from app pages.
- Do not track raw cache files.
- Do not promote labels to model input.
- Do not treat censored windows as misses.
- Do not use missing data as zero or `0%`.
- Do not change Outcome V2 probabilities.
- Do not wire Rankings or app behavior.
