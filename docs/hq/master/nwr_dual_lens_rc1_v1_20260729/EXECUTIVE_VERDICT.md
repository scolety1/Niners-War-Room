# Executive verdict

`YELLOW_NWR_DUAL_LENS_RESEARCH_REVISED_FORMULAS_NOT_ADMITTED`

The bounded research identified **W3_SHORT_HORIZON_CALIBRATED_BLEND** as the strongest Win Now
research candidate and **D1_DISCOUNTED_MULTI_HORIZON_VOR** as the strongest Dynasty
research candidate. Win Now: Spearman 0.693439, rank MAE 69.591628, nDCG 0.961443, coverage 100.00%, severe errors 55.
Dynasty: Spearman 0.720216, rank MAE 40.072258, nDCG 0.970708, coverage 59.18%, severe errors 15.

Neither lane is admitted. The controlling 5,518-row mart explicitly says
`training_allowed=False` and `production_approved=False`, and it contains zero
true-rookie rows. Those are mandatory authority/coverage failures that metrics
cannot override. The app therefore received no dual-lens implementation.
Finished V1 and Outcome V3 remain canonical and byte-identical.

This is not a V2-2 continuation. No provider was called, no security scan was
run, no opaque DynastyProcess CSV was opened, and no historical receipt
recovery lane was started.
