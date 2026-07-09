# Model v4 Formula Gauntlet Clearance Decision

## Decision

Maximum clearance remains:

`CLEARED_FOR_REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`

## Answers

- Review-only component signal tests remain the maximum clearance: yes.
- Partial replay support is improved as audit evidence only: yes, but no broader partial replay run is cleared.
- Position-scoped Formula Gauntlet remains blocked: yes.
- Full Formula Gauntlet remains blocked: yes.
- 100-candidate Formula Gauntlet remains blocked: yes.
- Champion refinement remains blocked: yes.
- Rankings integration remains blocked: yes.

## Why

The freeze preserved useful evidence and schemas, but the locator still found `0` exact/likely historical equivalents for the missing Model v4 receipt chain. The most important frozen artifacts are current-only or partial/proxy summaries. They can help write a safer component-test contract, but they cannot support tournament execution or formula promotion.

## Required Before Any Tournament

- Master HQ execution contract.
- PYF baseline comparator.
- Data Hygiene leakage/as-of checks.
- Position-level coverage and missingness rules.
- No blocked route/YPRR/TPRR, return scoring, or unadmitted source use.
- Explicit statement that outputs are review-only and cannot change rankings.
