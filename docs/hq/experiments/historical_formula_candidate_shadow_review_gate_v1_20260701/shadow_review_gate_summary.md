# Historical Formula Candidate Shadow Review Gate V1

Verdict: `GREEN_SHADOW_REVIEW_GATE_GO_REVIEW_ONLY`

Decision: `GO_SHADOW_REVIEW_PACKET_REVIEW_ONLY`

Selected candidate: `wr_boundary_breakout_sensitivity_guard`

This gate reviews merged historical candidate evidence and Tim's human review notes. It does not approve production promotion, create app pages, start live preview, change rankings, or wire candidate output into NWR.

## Gate Evidence

- Holdout MAE delta: `-1.196383`
- Holdout Spearman delta: `0.001089`
- Holdout startable precision delta: `0.0`
- Cutline misses: original `8`, rb/wr safe `5`, selected `2`
- Elite-QB severe regressions: original `14`, selected `1`
- Remaining cutline players: `T.Pollard, C.Lamb`
- Holdout MAE improved across `4/4` positions and `2/2` seasons.

Conclusion: the selected redesign may advance to a review-only side-by-side shadow comparison packet. Production promotion remains blocked.
