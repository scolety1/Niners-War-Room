# Model v4.7 UI External Audit Prompt

Please audit the attached Model v4.7 local app UI from the perspective of a dynasty fantasy football manager trying to complete final human review.

## Context

Model v4 is a review-only dynasty fantasy football decision system for a 10-team, 1QB, non-PPR, first-down scoring league with no TE premium. The model formulas and safety rules have already passed external audit. This audit is about the app experience, information architecture, labels, page usefulness, and whether a human can understand what to do next.

The user is confused by the current Command Center. In particular, the home page appears to mix active decision navigation, old sprint/audit artifacts, data health, and review-only packet information. Please be blunt about whether the page helps or hurts.

## Audit Goals

1. Evaluate whether the current sidebar/page structure is understandable.
2. Evaluate whether the Command Center is useful as a home page.
3. Identify which pages should be primary, secondary, or hidden.
4. Identify confusing labels, old sprint language, technical artifacts, or builder-facing concepts that should be removed from default user flows.
5. Recommend the simplest review workflow for the user.
6. Recommend concrete UI changes that improve decision quality without creating final recommendations.

## Pages / Screens To Inspect

- Command Center
- Decision Board
- Player Board
- Draft Room
- Trade Lab
- Model Tuning
- Settings

Screenshots for Command Center, Draft Room, and Decision Board are included. Source files for the app navigation and core pages/components are included.

## Key Questions

1. Should Command Center remain the default page? If yes, what should it contain? If no, what should replace it?
2. Which pages are actually needed for final human decision review?
3. Which pages should be hidden under Settings, Advanced, Audit, or Builder Tools?
4. Does the sidebar naming match the user's mental model?
5. Does the current UI explain the difference between model output, human review, and final decision?
6. Is the user being asked to look at too many tabs/tables?
7. What is the minimum viable user workflow for:
   - top-five drop decision
   - rookie pick review
   - player/rank sanity check
   - trade/context review
8. What should be removed, collapsed, renamed, or moved?
9. Does any UI language accidentally imply final recommendations?
10. Are review-only, no-market-leakage, and no-app-promotion constraints still visible enough?

## Constraints

- Do not recommend formula changes unless the UI creates formula misunderstanding.
- Do not ask to add final cut/keep/trade/draft recommendations.
- Do not use market/ADP/projection/ranking as private value.
- Keep the app local-first and review-only.
- Prefer fewer pages and clearer workflows over adding more tabs.

## Required Output

Please return:

- overall UI verdict: usable / usable with repairs / confusing and needs redesign
- critical UX blockers
- high-priority UI repairs
- medium/low UI improvements
- recommended sidebar structure
- recommended Command Center replacement or rewrite
- recommended default review workflow
- specific labels/tables/tabs to rename, hide, or remove
- whether the app is ready for the user to review decisions tonight
