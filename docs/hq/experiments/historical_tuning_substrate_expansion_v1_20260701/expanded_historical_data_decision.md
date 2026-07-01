# Expanded Historical Data Decision

## Decision

Preserve and validate the existing 2018-2024 feature seasons with 2019-2025 target seasons. Do not admit older feature rows in V1.

## Why Older Expansion Did Not Land

The existing safe Backtest V1 builder was attempted for 2012-2025 season inputs. It failed before producing rows because `nflreadpy` was unavailable in the approved local-only nflverse runtime. Since this lane cannot silently switch to an unapproved runtime or source path, older feature-side expansion is deferred.

## Target-Only Expansion

Outcome V2 historical target labels exist as review-only target-side evidence, including the local 2000 probe and tracked compact labels. They are not sufficient alone because this substrate requires aligned safe season N features and season N+1 targets.
