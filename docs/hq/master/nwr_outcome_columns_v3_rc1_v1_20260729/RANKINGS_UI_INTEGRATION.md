# Rankings UI integration

The existing `Outcome Context` preset gains a compact, long-form Outcome V3
lens. Named controls select one governed position and threshold; the table then
shows 2026, 2027, 2028, Within 3 Years, and Within 5 Years with probability,
calibration status, evidence state, sample support, confidence, and missing
reason. `TWO_OF_NEXT_3Y` is intentionally absent from Rankings.

The main rankings table and its sort pipeline are unchanged. The lens consumes
exact `player_id` joins from `OUTCOME_V3_INTEGRATION_PACK.csv`, is display-only,
and exposes `NWR_OUTCOME_COLUMNS_V3_RC1`.
