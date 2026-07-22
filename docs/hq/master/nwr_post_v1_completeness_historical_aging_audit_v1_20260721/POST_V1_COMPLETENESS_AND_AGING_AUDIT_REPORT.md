# Post-V1 completeness and historical aging audit

Verdict: YELLOW_NWR_POST_V1_AUDIT_COMPLETE_WITH_HISTORICAL_MODEL_CAVEATS

The installed desktop path, all 60 registered routes, core workflows, canonical
rankings, persistent-state boundaries, and tracked historical substrate were
audited. One bounded defect was repaired: the bare root URL previously opened
the state-writing Draft Cockpit. It now opens a read-only Start Here page that
identifies the canonical board, read-only tools, manual decision aids, live
local draft state, Data Health, and the review workflow.

The website repair is green. The historical conclusion is intentionally yellow:
tracked evidence supports an older-player overranking concern in the production
proxy, but exact historical Model v4 replay is not cleared. None of three fixed
age candidates passed all coverage, repeated-position, materiality, and
walk-forward gates. No formula, rank, source, identity, recommendation, or
current-board value changed.

## Controlling state

- Starting HQ: 532215c1b1a8896d5a838b827535c13dd655199d
- Starting tree: bca7ca6ecc1111ead8289a77650f481516d283fd
- Audit branch: work/nwr-post-v1-completeness-aging-audit-v1-20260721
- Website commit: c0b3a136d3fdbb247cd702cbc7b7300676bda859
- Push: not performed, by contract
- Stable checkout: unchanged at starting HQ and clean

## Product audit

All 18 visible routes, 41 hidden or compatibility routes, and the root route
were rendered. No route produced Page Not Found, an exception, or document-root
overflow. Visible routes were checked at 320x700, 375x812, 768x1024, and
1440x1000. Hidden routes were checked at desktop width and by the complete route
suite. The repaired root was rechecked at all four viewports with exactly one
H1 and all six primary links accessible.

No release-critical route remains incomplete. Development, legacy, debug, and
historical surfaces retain explicit manual, review-only, compatibility, or
parked language and are classified honestly.

## Canonical runtime and rankings

The real Desktop shortcut starts PowerShell in the stable checkout with app-mode
browser behavior, port 8520, the persistent LocalAppData root, and verified
launcher ownership. Launcher status app_commit is an accepted RC1 compatibility
floor constant rather than current Git HEAD; actual stable HEAD and tree were
read independently from Git.

The exact production loader resolved 240 rows from the accepted stable export,
SHA-256 263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4.
The ordered top five remained Puka Nacua, Jaxon Smith-Njigba, Bijan Robinson,
Jonathan Taylor, and Jahmyr Gibbs. The candidate UI rendered Full dynasty rows:
240 at desktop and 320px. Streamlit dataframe cells are canvas-rendered, so
ordered names were verified through the exact loader rather than DOM text.

## Historical conclusion

The production proxy covers 2013-2025, while the comparable out-of-fold panel
covers target seasons 2015-2025. Identity joins are exact. Age comes only from
the tracked review-only lifecycle sidecar. Current ADP, market ranks, provider
calls, future-season values, and current-board ranks were excluded.

Older cohorts have positive residuals, strongest for WR 30+, RB 28+, and TE 31+.
Productive-veteran false negatives remain real, so the evidence does not
authorize a direct age penalty. The strongest tested candidate improved macro
Spearman only 0.000894, lost three age rows, regressed TE aggregate performance,
and failed repeated-position stability. Result:
NO_HISTORICAL_AGE_ADJUSTMENT_CHALLENGER_ADMITTED.

## Integrity

Hermetic passed 13 bootstrap controls, 20 security-control regressions, and
2,736 Python tests with exit 0. LocalData returned
BLOCKED_MISSING_LOCAL_TEST_PACK, native exit 4. The five user-owned primary CSV
hashes stayed exact. Persistent product data, recovery quarantine, ranking
exports, formulas, identities, protected or frozen artifacts, and security
automation were not modified.
