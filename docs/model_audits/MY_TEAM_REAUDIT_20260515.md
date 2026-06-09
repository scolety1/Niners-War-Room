# My Team Re-Audit - 2026-05-15

## Verdict

The roster-decision gate was too permissive. It was showing "Roster Decisions Ready"
even though active My Team rows still carried review-level confidence and model/source
warnings. That made labels such as Core Hold and Bubble look cleaner than the evidence
supported.

This checkpoint changes the app behavior:

- Review-confidence or warning-status rows are no longer allowed into clean decision
  buckets such as Core Holds.
- They are routed to Needs Data Review unless they are the explicit required top-five
  release slot.
- The roster gate now reports Roster Decisions Need Review when active roster rows
  are below usable confidence.

## BTJ / Achane Check

| Player | Old UI Bucket | New UI Bucket | Model Call | Model Value | Keep Priority | Cut Risk | Confidence | Main Issue |
|---|---:|---:|---|---:|---:|---:|---|---|
| Brian Thomas | Core Holds | Needs Data Review | keep | 75.81 | 72.49 | 22.97 | review | High rank with review confidence, local baseline projection, missing participation proxy, stale source warning |
| De'Von Achane | Bubble Players | Needs Data Review | bubble | 66.14 | 62.94 | 33.00 | review | Dynasty RB value looks too low versus expectation; injury/model warning and proxy/missing participation inputs remain active |

## What "Bubble" Means

Bubble means the model is not making a clean keep/cut/shop call. It is supposed to mean
"close call, inspect receipts." It should not be treated as "bad player" or "drop."

In this patch, review-confidence rows do not get presented as clean Bubble calls.
They move to Needs Data Review first.

## Why This Matters

BTJ over Achane may still be explainable by the current receipts, but it is not
decision-safe yet. The current data says:

- BTJ gets a strong WR dynasty/target-earning profile and young-player bridge support.
- Achane gets strong recent LVE scoring and age score, but is dragged by injury risk,
  role/workload uncertainty, and the RB formula's durability/role handling.
- Both depend on local baseline projection and missing participation proxy inputs.

That combination should trigger review, not a green-light roster decision.

## Next Audit Focus

1. Re-run the external/pro audit using the updated packet.
2. Specifically ask whether current RB/WR cross-position balance underrates elite
   dynasty RB assets with uncertain workload/injury flags.
3. Audit whether local baseline projection and route/participation proxy rows are
   suppressing or inflating the wrong players.
4. Do not mark roster decisions ready until BTJ/Achane-style contradictions are
   either explained by receipts or fixed with data/normalization/formula changes.
