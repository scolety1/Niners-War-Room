# Data Hygiene Use-Gate Checklist

This checklist classifies allowed and blocked uses. Data Hygiene may assign these statuses as evidence recommendations. Master HQ approval is required for production promotion.

| Status | Meaning | Allowed Uses | Blocked Uses | Evidence To Upgrade | Master HQ Approval Required |
|---|---|---|---|---|---|
| `PRODUCTION_MODEL_USE` | Source/field is approved for production model use. Data Hygiene cannot grant this alone. | Only after Master HQ approval. | Any Data Hygiene-only promotion. | Full receipt chain, identity audit, leakage audit, historical validation, reproducibility, promotion decision. | yes |
| `REVIEW_ONLY` | Evidence may support human review or future gated work. | Review packets, planning, audits. | Production model, source truth, rankings, app behavior. | Stronger receipts, coverage, identity, leakage, rebuild, validation. | yes to upgrade |
| `DISPLAY_ONLY` | Evidence may be displayed as caveated context. | Human-facing context if app lane approves. | Formula/model/rank/source-truth use. | Source admission, identity safety, leakage proof, missingness policy. | yes to upgrade |
| `BLOCKED` | Source/field cannot be used for the intended purpose. | Document blocker. | Analysis, model, ranking, app behavior, source truth. | Explicit missing evidence or policy change. | yes |
| `IDENTITY_UNSAFE` | Joins/IDs are ambiguous, name-only, collision-prone, or incomplete. | Manual review queue. | Approved joins, model inputs, source truth. | Durable IDs or audited crosswalk with collision handling. | yes |
| `LEAKAGE_UNSAFE` | Field/source may include current/future/post-outcome information. | Blocker report. | Historical replay, backtests, model features. | Point-in-time receipts and decision-date proof. | yes |
| `NOT_ENOUGH_INFORMATION` | Evidence is insufficient to classify safely. | Preserve as unresolved evidence gap. | Guessing, promotion, model use, source truth. | Missing receipt/source/schema/join/leakage/coverage proof. | yes to upgrade |
| `MISSING_SOURCE` | Claimed source is not present or not accessible. | Source search/handoff request. | Any analytical or production use. | Locate source, record path/URL, acquisition method, hash, schema. | yes to upgrade |
| `MISSING_RECEIPT` | Source may exist but receipt chain is absent. | Receipt-building lane. | Promotion, model use, source truth. | HQ1 receipt fields completed. | yes to upgrade |
| `REBUILD_BLOCKED` | Artifact cannot be reproduced from known inputs/scripts/hashes. | Blocker report, rebuild plan. | Canonical promotion or model use. | Rebuild command, inputs, scripts, hashes, validation. | yes to upgrade |
| `JOIN_BLOCKED` | Source exists but cannot be safely joined. | Join audit and review queue. | Joined features, source truth, production use. | Safe keys, collision audit, unmatched handling, no name-only approval. | yes |

## Default Rule

If evidence is incomplete, use the strictest accurate status. Do not upgrade by implication.
