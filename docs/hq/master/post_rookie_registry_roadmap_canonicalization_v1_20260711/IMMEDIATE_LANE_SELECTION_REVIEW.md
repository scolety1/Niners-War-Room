# Immediate Lane Selection Review

## Decision

Immediate lane: **Trading Lab Saved Manual Scenario Workspace V1**.

The source scorecard recomputes with zero mismatches. Thirteen weights total 100, exactly one immediate lane is selected, and exactly three later lanes are ordered.

| Candidate | Score | Decision |
|---|---:|---|
| Trading Lab Saved Manual Scenario Workspace V1 | 95.0 | Immediate |
| Player Compare Compact-Width and Accessibility Hardening V1 | 90.6 | Next 1 |
| Data Health Guardrail Truth and Refresh Receipt Durability V1 | 84.2 | Next 2 |
| Roster Weakness Tracker Admitted-Roster Hydration Design and Readiness V1 | 79.4 | Next 3, design only |

## Why it remains first

Trading Lab persistence prevents frequent loss of human work, uses already admitted identifiers and manual fields, follows an established local persistence lifecycle, and is fully reversible. It requires no formula, source, plugin, rookie-registry, frozen comparator, external provider, or production valuation change.

Player Compare hardening is valuable but does not prevent data loss. Data Health truth and receipt durability are important operational work but are less directly tied to the primary manual decision workflow. Roster hydration still requires a design-only gate for missing packs, stable identities, and lineup authority.

## Mandatory interpretation

The selected lane is manual, display/workflow oriented, explicit, local-state based, and reversible. It is not a trade calculator, fairness verdict, automated offer generator, recommendation system, ranking adjustment, plugin-output surface, or source of production valuation.

## Baseline treatment

The known trust-banner static baseline remains `2 failed, 3 passed`, identical to clean HQ. Both failures inspect the thin `app/pages/05_rankings.py` wrapper for literal banner text. They are not caused by this roadmap or by the future Trading Lab lane. The implementation lane must reproduce clean-HQ/source/final differentials and may not weaken or rewrite those unrelated tests.
