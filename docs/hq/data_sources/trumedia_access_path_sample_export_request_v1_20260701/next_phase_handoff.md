# Next Phase Handoff

Current status: `WAITING_ON_TRUMEDIA_CONTACT`

This lane created a public-research and sample-export request packet only. It did not access TruMedia systems or fetch data.

## Trigger For Next Lane

Create a new source-admission branch only after one of these events:

- TruMedia confirms a demo/trial path.
- TruMedia provides a rights-cleared sample export.
- TruMedia provides a schema/data dictionary and written use terms.
- TruMedia declines access and NWR needs to record the final blocker.

## Next Lane Scope

Allowed:

- Read TruMedia's written response.
- Inspect a rights-cleared sample export if storage/use terms permit.
- Build compact source-admission receipts.
- Build schema, coverage, identity, and zero/missing reports.
- Update source-governance artifacts only.

Disallowed:

- App wiring.
- Model training or tuning.
- Formula changes.
- Rankings, recommendations, hidden sort, or source-truth changes.
- Raw vendor data commits unless the license explicitly allows it.
- Credential use unless TruMedia grants access and the API key handling policy is followed.

## First Validation Tasks If Sample Is Received

1. Confirm written rights cover local inspection and derived receipts.
2. Save raw sample outside git unless license explicitly allows repository storage.
3. Record export timestamp, license note, and schema version.
4. Generate a schema manifest with field types and nullability.
5. Generate coverage matrices by season, week, position, grain, and field family.
6. Validate identity joins for GSIS and PFF IDs.
7. Validate route denominator, target, receiving yard, air yard, YAC, snap, red-zone, coverage, matchup, and separation semantics.
8. Produce a source-admission verdict without production promotion.

## Handoff Verdict

Contact TruMedia. Ask for a rights-cleared sample export and written answers to `rights_questions_for_trumedia.md` before any technical integration work.

