# NFLVerse Player Context Rebuild Readiness Summary

Verdict: `YELLOW_WAITING_FOR_BINDING_ARTIFACT`

## Base

- Base branch: `origin/work/hq-parallel-control`
- Required minimum HQ HEAD: `bb7146271c71c39a1d7f1d82fd40c65b4ce9d4d5`
- Actual base HQ HEAD: `bb7146271c71c39a1d7f1d82fd40c65b4ce9d4d5`

## Readiness Decision

The rebuild is not ready to run.

The approved overlay exists and contains 43 review-only identity approvals, but every approved row still has `nwr_player_id=Not enough information` and `join_key_status=NEEDS_NWR_PLAYER_ID_BINDING`. The binding packet required to convert those approvals into safe app-joinable rows is not present in the current HQ base.

Until that binding packet is merged and explicitly permits the rebuild, all 54 current `NEED_IDENTITY_REVIEW` rows in the compact player-context artifact remain gated.

## Current Facts

- Player context artifact rows: 294
- Current `SAFE_NOW_DISPLAY_ONLY` rows: 240
- Current `NEED_IDENTITY_REVIEW` rows: 54
- Approved overlay rows waiting for NWR player ID binding: 43
- Non-approved identity rows: 11
- Binding artifact exists in current HQ base: false

## Rows That May Move After Binding

Only the 43 rows in `identity_approved_overlay_v1.csv` may move from `NEED_IDENTITY_REVIEW` to `SAFE_NOW_DISPLAY_ONLY`, and only after each row receives a unique, validated `bound_nwr_player_id` in the required binding artifact.

Eligible names:

- Jeremiyah Love
- Makai Lemon
- Carnell Tate
- KC Concepcion
- Jadarian Price
- Denzel Boston
- Germie Bernard
- Chris Bell
- Zachariah Branch
- Antonio Williams
- Jonah Coleman
- Skyler Bell
- Brenen Thompson
- Elijah Sarratt
- Emmett Johnson
- Kaytron Allen
- Adam Randall
- Josh Cameron
- Nicholas Singleton
- Barion Brown
- Demond Claiborne
- Lewis Bond
- J'Mari Taylor
- Kentrel Bullock
- Kejon Owens
- Robert Henry Jr.
- Seth McGowan
- Dominic Richardson
- Hank Beatty
- Emmanuel Henderson
- Roman Hemby
- Chase Roberts
- Jordan Hudson
- Kevin Coleman
- Donaven Mcculley
- Caullin Lacy
- Deion Burks
- Trebor Pena
- Jordyn Tyson
- Eli Stowers
- Kaelon Black
- Sam Roush
- Jamal Haynes

## Rows That Must Remain Blocked

The 11 non-approved rows must remain `NEED_IDENTITY_REVIEW` / unavailable until a later human-review and binding lane explicitly approves them:

- Eric McAlister
- Sieh Bangura
- Chris Brazzell
- Jacob De Jesus
- Omar Cooper
- Devin Voisin
- O'Mega Blake
- Barika Kpeenu
- Braylon James
- Jamarion Miller
- Chip Trayanum

## Expected Player Context Counts After A Fully Valid Binding

- Artifact rows: 294, unchanged
- `SAFE_NOW_DISPLAY_ONLY`: 283, if all 43 approved rows bind cleanly
- `NEED_IDENTITY_REVIEW`: 11, the non-approved rows only
- `review_required=false`: 283
- `review_required=true`: 11

Partial binding is allowed only if the binding packet says partial apply is permitted. Otherwise a partial binding must keep the rebuild blocked.

## Flags That Must Remain False

These flags must remain `false` in the rebuilt player-context artifact, the binding artifact, denominator artifacts, schedule artifacts, schema manifests, and app consumption contracts:

- `model_use_allowed`
- `training_allowed`
- `source_truth_allowed`
- `rank_logic_allowed`
- `hidden_sort_allowed`
- `trade_value_allowed`
- `pick_value_allowed`

Every row must remain `display_only=true`. Identity approval remains review/display-only and does not promote an identity into model, rank, source-truth, trade, or pick logic.

## Denominator And Schedule Impact

The player-context rebuild should update only the compact player-context artifact and its directly related schema/build/guardrail docs unless a later apply lane explicitly permits dependent artifact rebuilds.

Availability denominator artifacts must not update automatically in this lane. If a separate denominator refresh runs after binding, it may move the bound rows' two season-anchor records out of `NEED_IDENTITY_APPROVAL`, but exact `SAFE_NOW_DISPLAY_ONLY` versus `NEED_SOURCE_FIELDS` counts depend on source-field support. `games_missed_while_rostered` must remain `Not enough information`.

Schedule context artifacts do not need a separate policy update. The existing schedule gate already allows factual schedule display for rows passing the central player-context identity/status filters. After a valid player-context rebuild, newly safe rows may expose schedule fields only if the rebuilt row passes the same filters and the schedule fields are not `Not enough information`. Gated rows with populated schedule context must remain 0.

## Final Rebuild Gate

Current decision: wait for the binding artifact.

Recommended next lane: NFLVerse Approved Identity NWR Binding V1, producing the required merged binding artifact and explicit rebuild permission.
