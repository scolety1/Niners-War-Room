# App Consumption After Rebuild Plan

Verdict: `YELLOW_WAITING_FOR_BINDING_ARTIFACT`

## App Change Decision

No app page changes are needed for this readiness lane.

After a valid future player-context rebuild, app lanes that already read the central player-context artifact or shared service layer should pick up newly safe rows through the existing filters:

- join by `nwr_player_id`;
- require `identity_join_status=SAFE_NOW_DISPLAY_ONLY`;
- require `review_required=false`;
- require schema-safe field status;
- require display-only guardrail flags.

## Lanes Expected To Need No App Wiring

These lanes already consume the central tracked artifact or service layer and should need no page wiring solely because 43 additional rows become safe:

- Rankings / Data Review context panels
- Player Compare NFLVerse context surfaces
- Development Lab manual context surfaces
- Draft Room / Mock Draft / Draft Analyzer read-only context expanders
- Trading Lab manual context and missing-evidence context
- Injury / Availability denominator context for already approved denominator fields, subject to a separate denominator refresh if counts need to move

The app should continue to show existing unavailable or identity-review copy for rows that remain blocked.

## Schedule Context After Rebuild

Schedule context should continue through the existing schedule display gate. Newly bound rows may show factual schedule fields only when:

- the rebuilt central row is safe;
- `review_required=false`;
- requested schedule fields are not `Not enough information`;
- schema and guardrail flags pass.

No app lane should recompute schedule joins from raw data.

## Denominator Context After Rebuild

Availability denominator artifacts should not update automatically as part of this readiness packet. If a later denominator-refresh lane runs after binding, app pages should keep reading the tracked denominator artifact and continue requiring:

- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`;
- `review_required=false`;
- `denominator_status=SAFE_NOW_DISPLAY_ONLY`;
- display-only flags;
- missing values treated as unavailable, not zero or healthy.

## Still Blocked

The following remain blocked after this readiness packet and after any future display-only rebuild unless separately approved:

- the 11 non-approved identity rows;
- any approved row without a valid NWR player ID binding;
- model input;
- model training;
- source truth;
- rank logic;
- hidden sort;
- recommendations;
- trade value;
- pick value;
- start/sit;
- schedule strength;
- opponent difficulty;
- injury risk;
- durability score;
- medical or comeback projection;
- rookie/veteran outcome probability changes;
- Gate G activation;
- raw/shared/local/vendor/Gmail/cache/runtime/secret reads by app pages.
