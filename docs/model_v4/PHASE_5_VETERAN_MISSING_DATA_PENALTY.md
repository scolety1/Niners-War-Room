# Phase 5H Veteran Missing-Data Penalty Repair

This audit verifies that missing evidence for established veterans is labeled as unavailable or insufficient evidence instead of being treated as proof of zero production. It remains review-only.

## Summary

- review_status: review_only
- audited_rows: 50
- projection_gap_rows: 32
- possible_import_or_identity_gap_rows: 0
- evidence_adjusted_rows: 32
- insufficient_evidence_rows: 0
- active_rankings_promoted: False
- score_changes_are_review_only: True

## Repair Notes

- Established-veteran missing value components are excluded from the value denominator when enough other evidence exists.
- Missing projections remain visible and keep confidence in review/weak territory.
- Not-applicable young-player prior rows no longer show as missing evidence.
- No fake production, projection, injury, route, or market values were created.

## Audited Rows

| player | position | dynasty_asset_value | value_basis | confidence_label | missing_sections | not_applicable_sections | root_cause | action_taken |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lamar Jackson | QB | 57.318 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Jakobi Meyers | WR | 42.829 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| David Montgomery | RB | 52.152 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Brandon Aiyuk | WR | 28.721 | evidence_adjusted_missing_not_zero | weak | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Jake Ferguson | TE | 29.44 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Wan'Dale Robinson | WR | 37.604 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Jerry Jeudy | WR | 45.807 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Romeo Doubs | WR | 34.606 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| T.J. Hockenson | TE | 30.262 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Daniel Jones | QB | 38.086 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Devin Singletary | RB | 26.753 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Christian McCaffrey | RB | 32.781 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Kyren Williams | RB | 70.583 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Breece Hall | RB | 60.695 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Saquon Barkley | RB | 78.234 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Jonathan Taylor | RB | 71.912 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Josh Jacobs | RB | 72.006 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| James Cook | RB | 63.649 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Kenneth Walker III | RB | 52.543 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Derrick Henry | RB | 73.223 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Ja'Marr Chase | WR | 67.083 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Justin Jefferson | WR | 56.63 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Amon-Ra St. Brown | WR | 57.928 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| CeeDee Lamb | WR | 50.511 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Tee Higgins | WR | 47.274 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Nico Collins | WR | 49.186 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Garrett Wilson | WR | 55.909 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Drake London | WR | 60.09 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| George Pickens | WR | 44.751 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Chris Olave | WR | 30.378 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Jaylen Waddle | WR | 41.195 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Keenan Allen | WR | 40.925 | evidence_adjusted_missing_not_zero | weak | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Davante Adams | WR | 50.456 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Tyreek Hill | WR | 46.576 | evidence_adjusted_missing_not_zero | weak | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Mike Evans | WR | 48.135 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Stefon Diggs | WR | 31.869 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Cooper Kupp | WR | 37.188 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Terry McLaurin | WR | 54.432 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Josh Allen | QB | 59.34 | complete_applicable_evidence_weighted_sum | usable |  | young_player_prior | not_applicable_data_no_longer_counted_as_missing | Not-applicable young-player prior is displayed separately from missing data. |
| Jalen Hurts | QB | 73.815 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Patrick Mahomes | QB | 57.51 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Joe Burrow | QB | 63.952 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Brock Purdy | QB | 57.944 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Trey McBride | TE | 63.682 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| George Kittle | TE | 57.454 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Mark Andrews | TE | 47.096 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Travis Kelce | TE | 49.119 | evidence_adjusted_missing_not_zero | review | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Darrell Henderson | RB | 24.97 | evidence_adjusted_missing_not_zero | weak | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Hollywood Brown | WR | 18.911 | evidence_adjusted_missing_not_zero | weak | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
| Amari Cooper | WR | 31.34 | evidence_adjusted_missing_not_zero | weak | projection | young_player_prior | truth_set_projection_coverage_gap | Missing projection excluded from established-veteran value denominator; confidence remains review/weak. |
