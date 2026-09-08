# NWR Make-It-Back Calibration — Confidence-Interval + Second-Draft Follow-Up (V1)

**Date:** 2026-09-08 (overnight V4 continuation)
**Scope:** Directive V4 section 20 — follow up the earlier Make-It-Back 0.500-vs-0.595 gap (403 board, "8-15 intervening picks" bucket, n=42) with confidence-interval and more-draft analysis.

## 1. The original finding (prior session, UPDATE 8)

Empirical Make-It-Back calibration against the real, completed 403 draft board found: for turns with 8-15 intervening opponent picks, mean predicted MIB = 0.500 vs. real observed survival = 0.595 (gap −0.095, n=42) — flagged as "worth noting, not alarming given the sample size," explicitly not recalibrated pending a larger sample.

## 2. Confidence-interval analysis (this session)

Real observed survivors: 25/42 = 0.595. Wilson 95% CI: **[0.445, 0.730]**. The model's predicted 0.500 falls comfortably inside this interval. **The −0.095 gap is not statistically distinguishable from sampling noise at this sample size** — a rigorous, quantitative confirmation of the prior session's own qualitative caution, not a new finding overturning it.

## 3. More-draft analysis (this session, new)

The real, second, independently-sourced Fantasy Gamers league board (`mode: LIVE_READ_ONLY`, a genuine external Sleeper sync, not a mock — 91 of 150 real picks completed as of this session) was used as a second, real ground-truth source. Only picks that have actually happened (≤90; pick 91 is mid-round, not a completed owner-turn boundary) were used — never treating "not yet drafted" beyond that point as a real survival signal.

This real second draft populated the **two buckets the 403 board had zero real observations for** (structurally impossible for an 8-team, slot-8 owner to ever produce a 1-7 or 16+ intervening-pick gap — every one of their turns is either 0 or ~14 intervening picks):

| Bucket | n (403) | n (FG) | n (combined) | Real observed rate | Predicted MIB | 95% Wilson CI | Predicted inside CI? |
|---|---:|---:|---:|---:|---:|---|---|
| 0 (back-to-back) | 45 | 0 | 45 | 1.000 | 1.000 | [0.921, 1.000] | **Yes** |
| 1-7 (partial round) | 0 | 20 | 20 | 0.950 | 0.977 | [0.764, 0.991] | **Yes** |
| 8-15 (~1 round) | 42 | 0 | 42 | 0.595 | 0.500 | [0.445, 0.730] | **Yes** |
| 16+ (2+ rounds) | 0 | 20 | 20 | 0.400 | 0.457 | [0.219, 0.613] | **Yes** |

**Every bucket's predicted Make-It-Back value falls inside its real, empirically-observed 95% confidence interval, across two independent real drafts.** The FG-board buckets even skew in the *opposite* direction from the original 403 finding (model slightly over-predicts survival there, +0.027/+0.057, vs. under-predicting in the 403 bucket, −0.095) — consistent with symmetric sampling noise around a genuinely well-calibrated model, not a systematic directional bias in either direction.

## 4. Disposition

**No recalibration warranted or applied.** Make-It-Back's existing calibration is now validated against real outcomes from two independent real drafts at every intervening-pick bucket that has any real data, with no bucket showing a statistically significant deviation. This closes the follow-up the prior session correctly deferred — the honest answer, now backed by real statistics rather than a qualitative hedge, is that the model is well-calibrated at current real sample sizes.

A genuinely larger sample (more completed real drafts) would still narrow these intervals further and is worth revisiting once more real draft data exists — but there is no evidence-backed reason to touch the Make-It-Back formula tonight.

## 5. Verification

Read-only throughout except a reversible, expected `activate_redraft_profile` call (needed to read the Fantasy Gamers profile's own context, restored to 403 — the owner's real primary league — immediately after). Both real boards' pick counts/`updated_at_utc` verified byte-identical before and after this entire investigation.
