# RotoWire Golden Suspicious Ranking Audit

Date: 2026-05-17

Status: review-only, external-audit input

## Purpose

This file lists the current Golden Build rankings or model behaviors that
should get special attention before app promotion planning. These are not
automatic bugs and should not trigger blind tuning. They are audit targets.

## Highest-Priority Audit Targets

1. **Lamar Jackson sell-high / trade-review logic**

   Lamar is QB4 and overall 49 in the current candidate layer. His
   replacement/VORP receipt is negative versus the 10-team 1QB QB replacement
   baseline, while his dynasty premium depends heavily on rushing separation.
   That makes him a named control for QB rushing age-cliff logic and
   sell-high/trade-review language.

2. **Malik Nabers elite-WR review**

   Malik Nabers remains WR19 and outside the current high-WR sanity threshold.
   This may be caused by incomplete young-player/prospect prior evidence rather
   than a pure formula bug. The auditor should inspect receipts before
   recommending any formula patch.

3. **Brian Thomas Jr. and Luther Burden roster-rule sensitivity**

   BTJ and Luther are both important Niners top-five roster-rule names. Their
   private football value must not be affected by league rank, but their
   outputs must be audited before any forced-release logic is allowed to speak.

4. **First-down estimation**

   The model is first-down-aware, but current 2025 rushing/receiving first
   downs are estimated from 2022-2024 direct nflverse first-down history because
   the local RotoWire exports do not expose direct 2025 first-down fields.
   These estimates are labeled `estimated_from_history` and remain review-only.

5. **Incoming rookie/prospect gap**

   Incoming rookies remain weak/review unless they have sourced NFL evidence.
   This is safer than inventing prospect value, but Draft Ready cannot pass
   until rookie/prospect evidence is integrated.

## Guardrails

- Do not tune rankings to public consensus.
- Do not treat first-down estimates as direct data.
- Do not let projections, ADP, rankings, market, or league rank affect private
  football value.
- Do not promote to app decisions until suspicious rankings are explained by
  receipts or repaired.

See `ROTOWIRE_GOLDEN_SUSPICIOUS_RANKING_AUDIT.csv` for the issue table.
