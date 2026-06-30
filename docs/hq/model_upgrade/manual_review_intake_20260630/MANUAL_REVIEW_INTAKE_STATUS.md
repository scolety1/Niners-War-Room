# Manual Review Intake Status

## 1. Executive Summary

Verdict for this lane: `GREEN_INTAKE_ONLY`.

The repo already contains strong manual-review evidence across review queues, app UX notes, Outcome V2 lanes, CFBD/NFL usage source artifacts, rookie outcome gates, Development Lab notes, Draft Analyzer artifacts, and older Model v4 human-review packets. This package converts those observations into structured issue, candidate, source-gate, blocked-use, and app/UX matrices.

No model changes are implemented. No rankings, tiers, source gates, production outputs, draft-room behavior, or runtime state are changed.

## 2. What Was Inventoried

Tracked artifacts reviewed:

- Morning review queues for Unified Universe blockers, CFBD identity review, NFL usage promotion review, evidence registry status, and route audit.
- App UX notes for Player Compare, Trading Lab, Dynasty Rankings, Outcome Lens, navigation cleanup, and original draft issue status.
- Outcome V2 docs covering current feature/as-of gates, display-only current-player artifacts, Rankings Outcome Lens integration, injury context flags, injury display, and RB intermediate 5Y diagnostics.
- CFBD review artifacts and CFBD identity matching packages.
- NFL usage source contracts, route proxy policy, field promotion gate, blocklist, and promotion decision matrix.
- Rookie outcome feasibility, CFBD approval blocker, Gate E model R&D, Gate F display artifact, UDFA unknown review packet, and Gate G release-audit blockers.
- Development Lab and Future Tools safe/manual scaffold docs.
- Final board app-prop artifacts, manual review cards, and older outcome app-prop status.
- Model v4 human review and refinement artifacts, including human decision prep, rankings review readiness, rookie analyzer notes, user judgment worksheet, and model refinement queue.

Ignored-worktree checks:

- The ignored export folder was not present in this isolated worktree.
- The ignored `data` folder was not present in this isolated worktree.
- No raw local exports, shared-data files, API caches, vendor files, Gmail files, or secrets were added.

## 3. Top Must-Fix App Issues

1. Preserve clear `Not enough information` reasons for Outcome V2 missing-feature rows, rookie/prospect rows, unsupported positions, and blocked fields.
2. Keep Outcome Lens caveats visible: `This Year = 2026 NFL season`, partial first-down scoring, missing games availability context, and display-only status.
3. Keep Player Compare and Trading Lab language manual/display-only, especially injury context and trade planning labels.
4. Keep proxy route labels explicit so route participation proxies are not confused with true routes, true TPRR, or true YPRR.
5. Keep review pages separate from decision pages and ensure P0/P1 queues are easy to scan.

## 4. Top Model Feature Candidates

These are candidates only:

- `last_materially_active_season`
- `missed_prior_season`
- `limited_recent_sample`
- games/availability context
- per-game versus season-total feature split
- partial first-down scoring exactness flags
- source-disclosure and missing-feature indicators
- rookie draft-capital buckets after review-only source approval
- QB 1QB and TE no-premium format diagnostic indicators

## 5. Top Source Gates

1. CFBD identity human approval before any college production use.
2. CFBD source contract and promotion gate before college evidence display/model/rank use.
3. NFL usage promotion/backtest gate before any usage field becomes a model candidate.
4. Licensed source gate for true routes, true TPRR, and true YPRR.
5. Injury context gate before any use beyond review/display caveats.
6. Current feature as-of/freshness gate before future Outcome V2 feature promotion.
7. Rookie draft-capital and historical rookie label gates before rookie outcome display or model R&D promotion.

## 6. Top Blocked Items

- Injury risk score, recovery projection, medical comeback probability, or health inference.
- Trade valuation, pick valuation, generated offers, least-acceptable-price logic, or market-as-model-input.
- DynastyProcess, ADP, rankings, projections, vendor, or analyst fields as model input.
- CFBD model input or training truth without explicit human/source gates.
- True routes, true TPRR, or true YPRR without a licensed/approved source.
- Rookie/prospect probabilities or Rankings rookie columns without later gates.
- Start/sit, waiver, in-season rankings, trade targets, class strength, and playoff planner recommendations.

## 7. What Should Not Change Yet

Do not change Dynasty Rank, tiers, Frozen Final Draft Board V1, `final_board_rank`, pinned snapshots, `latest_candidate`, `latest_approved`, model/rank/source-truth gates, CFBD/NFL model input gates, Live Draft Room, Mock Draft, draft runtime, draft workflow, pick ownership, hosted deployment, or production model logic.

Do not run data refresh. Do not scrape. Do not track raw, shared, local, generated, vendor, Gmail, cache, or secret files.

## 8. Suggested Next Lanes

1. `CFBD Rookie Identity Human Approval Packet V1`: approve, reject, defer, or keep blocked high-confidence, possible, and ambiguous CFBD rows as review-only.
2. `Outcome V2 Missing Feature Context Review`: review Brandon Aiyuk, Joe Mixon, Tank Dell, Jonathon Brooks, and MarShawn Lloyd missing 2025 feature rows and caveat wording.
3. `NFL Usage Display Context Caveat Review`: decide whether red-zone and inside-10/inside-5 fields can become display-only with sample-size caveats.
4. `RB Intermediate 5Y Diagnostic Follow-Up`: keep RB T15/T18/T20 test-only, then investigate sparse missed-prior-season and limited-recent-sample validation slices.
5. `Rookie Gate F Coverage Repair V2`: improve review-only display coverage before any Gate G or Rankings discussion.
6. `App UX Caveat QA`: browser-smoke Outcome Lens, Player Compare, Trading Lab, Future Tools, and review routes for caveat clarity only.
