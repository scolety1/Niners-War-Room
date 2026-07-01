# Return Touchdown Policy Report

Special teams touchdowns do not matter for this model/parity path.

Direct `return_touchdowns` remains unavailable. `special_teams_tds` is not used as a return touchdown substitute and does not block this zero-eligibility parity rerun. Any return/special ambiguity is documented as excluded/ignored, not converted into a model feature.

Confirmed policy fields in this packet:

- `return_touchdown_used=false`
- `special_teams_tds_used=false`
- no direct return touchdown feature is created
- no special-teams touchdown substitute is created
