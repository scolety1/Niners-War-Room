# League and Lineup Context Review

## Result

YELLOW_READY_WITH_BOUNDED_CAVEAT

The repository contains a canonical human-readable rules lock, but the runtime configuration is not complete enough for truthful starter or flex coverage.

## Canonical settings

Authority: docs/model_v4/LEAGUE_RULES_LOCK.md.

| Setting | Canonical value or status | Initial-scope relevance |
| --- | --- | --- |
| League size | 10 teams | Required for league context; not required for raw roster counts |
| Quarterback format | 1 QB | Required for starter coverage |
| Scoring | Non-PPR; exact first-down and yardage rules; no TE premium | Disclose; not required for raw counts |
| Starting slots | 1 QB, 2 RB, 3 WR, 1 TE, 2 WR/RB/TE flex, 1 K | Required for starter/flex coverage |
| Bench | 14 | Required for full lineup allocation; not required for raw counts |
| Regular-season IR | 2 | Required for IR capacity indicators |
| Preseason IR | 0 | Required when snapshot phase is preseason |
| Taxi | No canonical rule located | Not enough information |
| Dynasty/keeper behavior | Dynasty/keeper hybrid with declaration and offline mixed draft | Required context |
| Position eligibility | Flex is WR/RB/TE | Required for flex coverage |
| Kicker | Included in roster mechanics; excluded from model value by default | Count descriptively; no value signal |
| Defense | Not applicable from 2024 | Source entries require explicit exclusion/mismatch behavior |
| Draft picks | Tradeable for next three annual drafts | Tracker inclusion remains a product question |

## Machine-readable gaps

src/config/league_rules.yaml includes team count, roster limits, IR count, declaration limit, kicker inclusion, draft rules, and general platform status. It does not encode:

- the full starting slot list;
- flex count and eligibility;
- bench count;
- phase-specific IR rules;
- non-PPR/no-TE-premium scoring shape;
- defense exclusion;
- taxi policy;
- product treatment of draft picks.

src/services/future_tools_rd_service.py contains a hard-coded STARTER_FORMAT for QB/RB/WR/TE. It omits two flex slots and the kicker, and it is not tied to the canonical rules lock. It must not be reused as hydration authority.

## Required future configuration input

Before starter/flex/bench coverage is enabled, a separately approved implementation lane must add or extend a typed league configuration carrying:

- config schema version;
- league authority document and revision;
- effective season and phase;
- starter slots and eligibility;
- bench, taxi, and IR capacities;
- kicker and DST treatment;
- scoring-format labels needed for disclosure;
- missing-setting behavior.

This is a migration of existing repository authority, not a new remembered rule. Any setting not present in authority remains configurable and NOT_ENOUGH_INFORMATION.

## Permitted initial behavior

Without the typed migration, only exact roster counts, positions, and missing/unresolved counts may be calculated. Starter, flex, bench, IR-capacity, replacement, and lineup-gap indicators are prohibited.
