# Label Truth Guardrail Report

## Required posture

This packet admits compact row-level label-source rows for review/parity validation only.

| Flag | Status |
| --- | --- |
| `review_use_allowed` | `true` only for compact rows derived from validated row-level sources. |
| `label_truth_allowed` | `false` everywhere. |
| `model_use_allowed` | `false` everywhere. |
| `training_allowed` | `false` everywhere. |
| `source_truth_allowed` | `false` everywhere. |

## What this packet does not approve

- No label-truth promotion.
- No model input approval.
- No training approval.
- No source-truth approval.
- No app wiring.
- No current-player probabilities.
- No Ranking, Outcome Lens, Player Compare, Live Draft, or Mock Draft behavior.

Labels remain evaluation targets and parity-validation substrate, not input features.
