# Historical Replay Requirements

Verdict: `YELLOW_REPLAY_REQUIREMENTS_DEFINED_NO_REPLAY_RUN`

This packet defines requirements only. It does not run a replay, train a model, tune a model, score current players, or create probabilities.

## Required Replay Contract

Any future Outcome/Rookie lane that proposes NFLVerse-backed model or training use must define:

- prediction anchor;
- feature as-of date;
- season and week window;
- eligible player universe;
- exact source artifact and snapshot;
- row-level identity gate;
- missingness policy;
- label target and censoring policy;
- leakage audit;
- validation/calibration acceptance guard;
- explicit user approval for model, training, and source-truth promotion.

## Feature Families Requiring Replay

At minimum, replay is required before any model/training consideration for:

- roster status;
- weekly roster status;
- injury report status;
- practice status;
- schedule next game / opponent / bye;
- depth chart role;
- snap recency / sample;
- last active season / week;
- draft capital;
- combine;
- availability denominator fields.

## As-Of Rules

Current NFLVerse fields cannot be backfilled into a pre-draft or historical decision as if they were known at the anchor. Future NFL production, snap counts, activity weeks, roster movement, depth chart placement, injury status, and schedule state must prove source availability at the prediction time.

For rookie work, depth chart, roster appearance, player_stats appearance, snap appearance, and injury context are not pre-draft feature evidence unless a future replay proves the source existed before the selected rookie prediction anchor.

## Leakage Blocks

The replay must block:

- future NFL production as pre-draft evidence;
- current role as historical role;
- post-anchor roster movement;
- post-anchor injury or practice status;
- post-anchor snap counts;
- future schedule or opponent context;
- future games or career length;
- labels joined back into features;
- draft absence treated as UDFA proof.

## Acceptance Criteria

A replay lane can only recommend a later model gate if it produces:

- reproducible source manifest;
- feature-window matrix;
- leakage diagnostics;
- missingness diagnostics;
- identity pass/fail counts;
- label coverage and censoring counts;
- holdout validation/calibration results;
- explicit list of still-blocked fields;
- confirmation that model/training/source-truth approvals remain false until a separate approval lane.
