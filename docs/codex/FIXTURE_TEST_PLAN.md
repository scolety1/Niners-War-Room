# Fixture Test Plan

## Fixture Data
Use small checked-in fixture rows for pick labels, one QB/RB/WR/TE score input each, Niners top-five roster rows, keeper/drop rows, and trade package examples.

## Expected Outputs
Expected outputs must include exact pick values, hand-calculated private scores, keeper/drop/confidence scores, official top-five order, forced-release candidates, and trade labels.

## Formula Tests
Formula tests must cover pick values, position private scores, first-down adjustments, confidence, keeper score, drop score, keeper pressure, top-five release, shield eligibility, and trade scoring.

## Import Tests
Import tests must cover duplicate players, duplicate picks, missing official rank warning, rank 400 warning, invalid pick labels, missing identity, unknown team warning, and roster count warning.

## Edge Cases
Cover ties in official rank, missing rank, rank 400 placeholders, unknown position, duplicated owners/picks, missing market values, and future picks with unknown slot/certainty.
