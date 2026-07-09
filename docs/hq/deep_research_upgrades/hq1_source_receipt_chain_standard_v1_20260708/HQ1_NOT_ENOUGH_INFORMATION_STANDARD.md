# HQ1 Not Enough Information Standard

NWR should say `NOT_ENOUGH_INFORMATION` when evidence is missing instead of guessing.

## Use This Standard When

- Source origin is unclear.
- Source URL/path or acquisition method is missing.
- Acquisition timestamp is missing for a mutable source.
- Licensing or use rights are unclear.
- Row grain cannot be proven.
- Schema or field meaning is unclear.
- Player identity keys are missing or name-only.
- Join collisions or unmatched rows are unresolved.
- Historical coverage is unknown.
- Missingness behavior is unknown.
- Source timing cannot prove decision-date safety.
- Rebuild steps are missing.
- Raw file hashes or source receipts are missing.
- A value appears in a public display but no reproducible feed exists.
- A field is likely equivalent to an upstream input but the upstream receipt is absent.

## What To Do Instead Of Guessing

- Label the item `NOT_ENOUGH_INFORMATION`.
- Preserve the evidence that exists.
- State the missing evidence.
- State the unsafe use.
- State what would unblock the item.
- Park the metric/source until a future lane can resolve the blocker.

## Required Language

Use direct language:

`NWR does not have enough information to classify this source or field for review-only, display-only, model-use, source-truth, or production use. It must not be used as an approved input until a future lane supplies the missing receipt evidence.`

## Examples

- Public route leaderboard with no documented export, IDs, license, or historical file receipts.
- Current board value file with no upstream component receipt chain.
- Injury status field without point-in-time publication receipts.
- Player stat table where row grain changes across seasons.
- Name-only player match with same-name collision risk.

## Final Rule

Not enough information is not failure. It is a guardrail that prevents false confidence.
