# Presentation and Trust Contract

## Vocabulary

The future tracker must use the existing Decision Trust Strip states:

- Valid / current;
- Stale;
- Missing;
- Gated;
- Unavailable;
- Identity exception;
- Source exception;
- Not enough information.

Refresh and retention presentation must reuse:

- Refresh succeeded;
- Partial success;
- Stale retained data;
- Source skipped;
- Source unavailable;
- Source gated;
- Refresh failed;
- Not enough information;
- CURRENT_RETAINED_DATA;
- STALE_RETAINED_DATA;
- NO_USABLE_RETAINED_DATA.

No competing positive state or synonym may be invented.

## Required disclosure

Every hydrated roster presentation must disclose:

- admitted source label;
- source-as-of time;
- hydration attempt time;
- freshness state and threshold authority;
- latest successful and last-known-good relationship;
- retained-data state;
- total source assets;
- resolved, unresolved, duplicate, unsupported, and excluded counts;
- exact identity join method;
- missing fields and partial coverage;
- league configuration authority/version;
- whether each output is descriptive, review-only, or advisory.

## Display rules

- Missing roster data cannot display as healthy or complete.
- Stale data cannot display as current.
- A valid receipt does not imply every source row is healthy.
- A failed latest attempt does not erase a prior valid snapshot.
- Last-known-good is historical retained evidence, not a new success.
- One unresolved player must be visible in the summary and details.
- Partial coverage may show resolved descriptive rows only with the denominator and caveat visible.
- Duplicate identity, corrupt schema, and integrity failure prohibit aggregate calculations.
- Rankings may remain available when the roster is unavailable, but no roster weakness may be inferred.
- Roster facts may remain available when rankings are unavailable, but rank/value distribution must show Unavailable.
- Descriptive facts cannot be phrased as trade, waiver, add/drop, start/sit, or draft advice.

## Surface boundary

The current manual page remains PRESENTATION_ONLY until a separately approved integration lane. Manual rows and hydrated rows must not be merged silently. If both are ever shown, they require separate source labels and no automatic overwrite.

## Accessibility

Status meaning must be text, not color alone. Summary and detail views must expose the same state, unresolved count, as-of time, and caveat. Keyboard order and compact-width behavior require focused tests in the integration lane.
