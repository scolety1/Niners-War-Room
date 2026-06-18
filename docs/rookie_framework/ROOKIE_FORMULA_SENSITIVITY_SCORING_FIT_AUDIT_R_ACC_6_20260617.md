# Rookie Formula Sensitivity Scoring-Fit Audit R-ACC-6

Date: 2026-06-17

Status: Read-only, pre-registered audit. No formula run. No replacement ranking.

## Frozen State

- Formula: `cfbd_enriched_baseline_v1_1`
- Board order: frozen
- Private/model scores changed: no
- Production/app artifacts changed: no
- Probabilities, bands, hidden sort keys, promoted artifacts created: no

## What The Current Formula Appears To Reward

Based on local docs and exports, the current formula rewards:

- Source-safe CFBD production.
- Draft capital and position context.
- Production share context.
- Role/archetype context where available.
- Evidence confidence and warning visibility.
- Manual warning overlays such as draft-capital trap guard.

The current board also keeps ADP/market out of private value. ADP/market may appear as display-only draft-room price context.

## League Fit

League context:

- 10-team dynasty/keeper hybrid.
- 1QB.
- Non-PPR.
- No superflex.
- No TE premium.
- Rush/rec first downs matter.
- Passing TDs are de-emphasized.
- Mixed rookie + dropped-veteran draft later, but this audit is rookie-only.

Fit implications:

- RBs need early-down, goal-line, short-yardage, receiving first-down, and pass-pro trust context.
- WRs need target quality, route participation, target earning, first-down conversion, and TD path context.
- Empty PPR volume should not create confidence.
- QB scarcity should not affect this rookie review group.
- TE premium does not apply.

## Current Concern Diagnosis

Data/evidence gaps:

- Primary issue. Depth Chart / Role remains missing for most early-pick candidates.

Player-specific context gaps:

- Material. Carnell Tate, Jadarian Price, and Antonio Williams need player-specific risk review before premium use.

Role/depth-chart gaps:

- Most important current blocker for 1.04 confidence.

Formula-weight concerns:

- Not proven in this sprint. The current issues look more like missing role/context evidence than a confirmed formula-weight failure.

Display/readability concerns:

- Improved by R-ACC-2 through R-ACC-5. Remaining readability work is packaging, not scoring.

## Pre-Registered Later Sensitivity Questions

These are questions for a future gated sprint only:

1. Would source-safe early NFL role evidence explain premium-pick risk better than changing CFBD production weights?
2. Would first-down/goal-line/target-quality context improve manual confidence without changing base rank?
3. Should draft-capital trap guard remain a manual warning instead of a rank changer?
4. Are older early-pick profiles better handled as manual notes until historical validation is explicitly approved?
5. Do low-source-confidence premium names need stronger manual hold language rather than formula edits?

No question above was run as a formula test in R-ACC-6.

## Prohibited Changes

R-ACC-6 does not allow:

- Formula change.
- Board reorder.
- Private/model score edits.
- Production/app integration.
- Outcome/veteran/model_v4 production edits.
- Probabilities.
- New bands.
- Hidden sort keys.
- Promoted artifacts.
- ADP/market as private value.

## Recommendation

Recommendation: no formula change now.

The next safe step is a manual draft kit packaging/readability pass using the existing frozen board and R-ACC reports. A later read-only shadow sensitivity sprint could be proposed only after Tim supplies role/depth-chart evidence and explicitly approves a new gate.

If later sensitivity work is approved, it should be labeled plan-only until run, avoid replacement rankings, and report whether evidence gaps explain the issue before any formula-weight proposal.

## Do Not Use For Production/App

This audit is local/manual-use only. Do not wire it into app views, production rankings, Outcome files, veteran/model_v4 production files, probability systems, bands, hidden sort keys, or promoted artifacts.

## Next Best Codex Prompt

Proceed to R-ACC-7: manual draft kit v2 packaging and readability pass. Preserve formula, board order, and manual-use status.
