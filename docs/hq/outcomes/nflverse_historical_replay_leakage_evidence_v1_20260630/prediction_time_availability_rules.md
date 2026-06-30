# Prediction-Time Availability Rules

Verdict: `YELLOW_AVAILABILITY_RULES_DEFINED_NO_REPLAY_RUN`

These rules define what must be true before an NFLVerse-derived field can be tested in a future historical replay. They do not approve model experiments.

## Global Rule

A field is available at prediction time only if the lane can prove the exact value was public, factual, identity-safe, and frozen before the prediction anchor.

The proof must include:

- prediction anchor;
- source snapshot timestamp;
- field as-of timestamp;
- player identity gate;
- eligible player universe;
- feature window;
- missingness rule;
- leakage audit.

## Pre-Draft Rookie Anchor

Allowed future candidates are limited to evidence known before the draft-day prediction anchor. Combine data may be a candidate only if the event and data publication occurred before the anchor. Draft capital, NFL roster status, depth charts, NFL injuries, NFL snaps, NFL player_stats, and NFL activity are not pre-draft features.

Missing draft capital before the draft is not UDFA evidence.

## Post-Draft Rookie Anchor

Draft capital may become a post-draft-only candidate if the draft has completed before the anchor and the drafted-only admission gate passes. Landing spot, depth chart, roster status, snaps, injuries, and player_stats still need their own point-in-time gates.

UDFA status remains blocked unless a separate explicit UDFA source policy and human review gate approves it.

## In-Season Weekly Anchor

Weekly roster, injury, practice, schedule, depth chart, snap, and availability fields require season/week snapshots frozen before the prediction. Closed-week snap or stat values may only be considered after a documented lag policy and cannot include the target game or future weeks.

## Veteran Current-Season Anchor

Completed prior-season stats or context may be display candidates only after source-policy and as-of gates. Current roster, injury, depth, schedule, snap, and activity context cannot be used as model features unless the lane proves prediction-time availability and avoids outcome-horizon leakage.

## Missingness Rule

Missing values stay `Not enough information`.

Missing is never:

- zero;
- false;
- healthy;
- clean;
- no-risk;
- no-role;
- no-usage;
- inactive;
- confirmed UDFA;
- missed game;
- favorable schedule.
