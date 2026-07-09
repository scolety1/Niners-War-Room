# Routes Run Denominator Recovery V2B Handoff

## Verdict

`YELLOW_ROUTES_RUN_DENOMINATOR_LEADS_ONLY`

The lane found credible route-denominator leads but no source reached `GREEN_ROUTE_DENOMINATOR_CANDIDATE`.

## What Changed From Prior Route Recovery

The most important new finding is that SumerSports RB public pages appear to carry route-denominator-like receiving fields in the page payload for 2022-2025 even though the RB table does not visibly display `Routes Run`. This potentially makes Sumer a WR/TE/RB provider-family lead, but it remains blocked until Sumer grants or documents permissible access and confirms the RB fields are supported.

ESPN Receiver Scores remains the strongest technical lead because its client JSON includes `rtm_routes` with GSIS and ESPN IDs for 2017-2025. It is still not an admitted feed because the object is undocumented and Disney terms block dataset extraction without permission.

PlayerProfiler remains a useful RB public-page lead, but terms and lack of aggregate export keep it out of candidate status.

## Do Not Use Yet

Do not use any of these as production source truth:

- SumerSports route fields.
- ESPN Receiver Scores route fields or `rtm_routes`.
- PlayerProfiler public route metrics.
- NGS route-recognition examples.
- nflverse participation `route` labels as full route denominators.
- Snaps, team pass attempts, target rates, or other proxies as true routes.

No production model, rankings, formula, source-truth, app, runtime, UI, default sort, recommendation, verdict, boost, PFF Elusive Rating, or `nwr_elusive_proxy_review_only` changes were made.

## Recommended Next Lane

Run `Sumer/ESPN routes_run permission, API, export, identity-crosswalk hardening lane`.

Expected outputs:

1. Provider permission or terms memo for SumerSports and ESPN/Disney.
2. Documented API/export/feed path, or written permission for a specific retrieval path.
3. Field dictionaries for `receivingPassRoutesRun` and/or `rtm_routes`.
4. Row-grain specification distinguishing player-season, combined-season, weekly, and game rows.
5. Season/position coverage and missingness tables.
6. Identity crosswalk audit to NWR canonical IDs.
7. Reproducibility script that retrieves only permitted data.
8. Use gate that explicitly keeps routes blocked unless all admission gates pass.

## Boundary Confirmation

HQ2 boundary preserved:

- No prior-year challenger scoring.
- No miss taxonomy output.
- No feature tournament scorecard.
- No direct beat-prior-year claim.
- No multi-year stability candidate work.
- No HQ2 packet path touched.

Production boundary preserved:

- No model/rankings/formula/source-truth/app/runtime/UI file changed.
- No source promoted.
- No proprietary data copied into the repository.
- No push and no merge should occur from this lane unless explicitly requested later.
