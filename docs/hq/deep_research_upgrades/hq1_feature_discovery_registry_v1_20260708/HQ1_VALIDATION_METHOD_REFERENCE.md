# HQ1 Validation Method Reference

Date: 2026-07-08

## Purpose

This reference preserves the future validation and feature-tournament rules from the HQ1 research corpus. It is a methodology artifact only. No feature tournament was run in this lane.

## Required Frozen Registries

Future scoring lanes must freeze these registries before any candidate is scored:

- Candidate metric registry.
- Source registry and source gate snapshot.
- Baseline registry.
- Target registry.
- Split registry.
- Missingness policy.
- Coverage-bias policy.
- Minimum sample rules.
- Evaluation metric definitions.

The freeze must happen before results are viewed. Candidate definitions should not be rewritten after observing scores.

## Split Rules

Use walk-forward season splits. The primary target structure should be N-to-N+1: prior-season information predicts the next season or next draft decision horizon.

Do not use random splits. Random splits can leak player-career era, year-specific scoring environment, team context, and future information into training/evaluation.

Use leave-one-season-out checks as a stability diagnostic. A candidate should not be treated as robust if its signal depends on one unusual season, one scoring environment, or one position subgroup.

## Baseline Rules

Use position-specific baselines. QB, RB, WR, TE, and cross-position dynasty/meta signals have different usage shapes, replacement levels, aging curves, and missingness patterns.

Future baselines may include prior-year finish, position-only baselines, age/position baselines, opportunity baselines, and market/display-only sanity baselines when explicitly allowed. Baselines must be frozen before testing.

## Target Rules

Freeze target definitions before scoring. NWR should define whether a test targets rank error, startable precision, fantasy finish bands, first-down scoring fit, multi-year value, role persistence, or dynasty/meta outcomes.

No candidate should be declared useful without reporting which target family it helps and which target family it does not help.

## Coverage And Missingness Controls

Every future tournament should report:

- Player and position coverage.
- Season coverage.
- Missing input rate.
- Zero versus missing policy.
- Identity join coverage.
- Source-specific missingness.
- Position and role coverage bias.
- Impact of excluding missing rows.
- Missingness indicators used in candidate panels.

Absence of a row is not evidence of zero usage unless the source contract proves explicit zero semantics.

## Outlier Checks

Future tournaments should run outlier checks before interpreting scores. Examples include tiny-sample efficiency spikes, injured-season distortions, team environment shocks, rookie partial seasons, role changes, and unusual touchdown variance.

Outlier checks should preserve evidence. They should not be used to quietly tune around bad results.

## Production Boundary

New metrics must not be tested by dropping them into the current production formula. Production model files, rankings files, UI/app files, runtime services, default sort, hidden sort, recommendation logic, verdict logic, and boost logic are protected.

GREEN means review-only signal. It does not mean production promotion, source promotion, model approval, or UI integration.

Any future source admission, model promotion, or production integration requires a separate explicitly approved lane.
