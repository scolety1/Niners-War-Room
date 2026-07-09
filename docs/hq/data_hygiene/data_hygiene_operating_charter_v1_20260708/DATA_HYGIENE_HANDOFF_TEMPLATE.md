# Data Hygiene To Master HQ Handoff Template

Use this template whenever Data Hygiene evidence needs Master HQ review.

## Verdict

`GREEN_REVIEW_READY` / `YELLOW_REVIEW_READY_WITH_CAVEATS` / `RED_BLOCKED`

## Artifact Path

`docs/hq/...`

## Source/Data Reviewed

- source family:
- provider:
- artifact/path/URL:
- acquisition method:
- receipt IDs:

## What Exists

- raw artifact exists:
- tracked review artifact exists:
- rows:
- columns:
- schema:
- seasons/weeks/dates:
- hashes:

## What Is Missing

- missing source:
- missing receipt:
- missing join key:
- missing hash:
- missing rebuild step:
- missing as-of proof:

## Source Status

`PRODUCTION_MODEL_USE` / `REVIEW_ONLY` / `DISPLAY_ONLY` / `BLOCKED` / `IDENTITY_UNSAFE` / `LEAKAGE_UNSAFE` / `NOT_ENOUGH_INFORMATION` / `MISSING_SOURCE` / `MISSING_RECEIPT` / `REBUILD_BLOCKED` / `JOIN_BLOCKED`

## Receipt Status

- source receipt:
- component receipt:
- rebuild receipt:
- validation receipt:

## Join Safety

- identity keys:
- join keys:
- join method:
- matched rows:
- unmatched rows:
- duplicate/collision rows:
- name-only joins present:

## Leakage Status

- decision date/as-of:
- current-only fields:
- future-known fields:
- post-outcome fields:
- replay eligibility:

## Reproducibility Status

- rebuild command/script:
- required local files:
- local_exports dependency:
- hash reproducibility:
- blocker:

## Coverage/Missingness

- row count:
- season coverage:
- week/date coverage:
- position coverage:
- field coverage:
- missingness policy:
- sparse-history flags:

## Blockers

- blocker:
- evidence needed:
- owner:

## Allowed Uses

- review-only:
- display-only:
- data readiness:

## Blocked Uses

- production model use:
- source truth:
- ranking logic:
- app behavior:
- hidden sort/recommendations:

## Recommendation

Data Hygiene recommendation:

## Master HQ Decision Required

yes/no:

Reason:
