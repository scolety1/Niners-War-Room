# Make-It-Back Method

Probability is emitted only when the imported owner snapshot supplies `std_dev` or both `min_pick` and `max_pick`.

The implementation derives a bounded normal-distribution spread from that owner evidence and estimates survival beyond the next owner selection. The output is explicitly labeled `HEURISTIC_NORMAL_FROM_OWNER_ADP_RANGE`; it is not presented as calibrated historical truth.

Expected-pick-only rows show `HEURISTIC — LOW CONFIDENCE` without a numeric probability. Missing ADP or a missing next owner pick shows `MAKE-IT-BACK: UNAVAILABLE`. No external simulator code was copied.
