# Rookie Outcome NFLVerse Context Audit

## Current Status

Rookie Outcome remains a separate lane from normal Veteran Outcome V2. The
drafted-only / feature-policy safe-upgrade packet is review-only and keeps all
release gates closed.

Gate G remains blocked.

## What Changed With NFLVerse

NFLVerse refresh-health and player-context artifacts improve review visibility:

- `draft_picks` can support positive drafted-only admission review.
- `combine` can support review-only context after schema/source review.
- rosters, weekly rosters, player_stats, snap counts, depth charts, and
  injuries can support review context when identity and as-of gates are safe.

This is not a Rookie Outcome model approval.

## Drafted-Only Review

Positive `draft_picks` evidence may admit drafted-only review coverage when it
has real draft year, round, and pick/overall pick from an approved draft-pick
source.

Other datasets cannot admit a drafted row by themselves:

- ff_playerids
- rosters / weekly rosters
- depth charts
- player stats
- snap counts
- injuries
- Sleeper/NWR IDs
- CFBD candidate rows

## Gate Answers

- Does this approve rookie model training? No.
- Does this approve active rookie probabilities? No.
- Does this approve Gate G? No.
- Does this approve UDFA modeling? No.
- Does NFLVerse confirm UDFA status? No.

Draft absence, roster appearance, stat appearance, snap appearance, or depth
chart appearance is insufficient to confirm UDFA status.

## Combine Context

Combine data may be useful for review packets, but it is not model/training
approved in this audit. It needs a separate feature-policy/model gate before
any stronger use.

## Depth Chart Context

Depth charts may support a current opportunity watchlist as review-only
context. They cannot be used as historical/pre-draft modeling features without
an as-of leakage gate.

## UDFA Policy

UDFA modeling remains blocked. Review-only UDFA decisions do not become
historical source truth, training truth, model input, Rankings wiring, or Gate
G approval.

Missing draft capital remains:

`Not enough information`

It is never zero, false, low-risk, clean, or confirmed undrafted.

## Recommended Rookie Next Step

Run a Rookie drafted-only label/feature feasibility review after Data Hygiene
hardens identity and draft-pick admissions. Do not build a model or app-facing
rookie probabilities until Gate G is explicitly reopened and approved.
