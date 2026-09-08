# NWR Rookie / Insufficient-History Coverage Closure V1 (2026-09-08)

**Directive:** "NWR NEXT-DRAFT ROOKIE / INSUFFICIENT-HISTORY CLOSURE" -- continue from `a1505742`,
preserving the fresh veteran admission (not reopened, not touched, not re-derived). Real,
explicit, in-chat owner authorization (Spencer Colety).

## 1. Freshen/govern the 78-row rookie component

**Before installation (per the directive's own required report):**
- Artifact path: `docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/GOVERNED_ROOKIE_PROJECTION_SNAPSHOT.csv`
- Exact hash: `e1636eb729441aed91187cf8170c05279090213ef0c2426269a63d95ec59c4d7`
- `source_as_of`: `2026-07-30` (40+ days stale, independently blocked by the row-level freshness
  gate regardless of the veteran admission's own state)
- Row count: 78 (all `rookie=True`)
- Positions: WR 36, TE 20, RB 12, QB 10
- ESPN market coverage: 1/78 overlap with the real ESPN top-250 (`De'Zhaun Stribling`) -- true
  2026 rookies with real, early, top-250-relevant draft capital are rare in this admitted set;
  not investigated further this pass (a real identity/draft-evidence-coverage question, out of
  this directive's explicit scope)
- Ballers/UDK coverage: N/A -- no owner UDK/Ballers import currently staged for either real
  profile
- Previous governance state: `APPROVED_FOR_REDRAFT_V1`, renewed once already (2026-09-06,
  "Spencer Colety, explicit in-session authorization") for a narrow practice-draft window that
  has since expired again

**Real, fresh admission built through the existing rookie pipeline** (`build_current_rookie_candidate`,
`redraft_2026_rookie_projection_model_service.py`) -- no source dates changed, no fabricated
receipt, no projection values altered. Reused the same fresh players registry already pulled for
the veteran admission (`2026-09-08T21:54:00Z`), the same permanent/immutable 2012-2026 draft-picks
and rookie-outcome-history snapshots (unchanged -- historical facts, not time-sensitive). All 9
real promotion gates passed (`historical_exact_identity_coverage_gte_98pct`,
`walk_forward_training_precedes_target`, `selected_model_beats_position_median_overall`,
`selected_model_beats_position_median_each_position`, `current_identity_and_role_gate`,
`projection_numeric_nonnegative`, `projection_score_and_bounds_coherent`,
`rookie_layer_not_governed_or_installed`, `k_dst_blocked`).

Real result: **73 rows** (down from 78 -- verified, individually explained below, not a defect).

## 2. Rookie status-universe filter fixed systemically

Applied the exact same real distinction as the veteran fix: `CURRENTLY_ROSTERED_STATUSES`
(`ACT`, `RES`, `EXE`, `RSR`, `PUP`) imported from `redraft_2026_projection_model_service.py` --
single source of truth, no duplicated/divergent definition. `DEV` (practice squad) and every
other non-currently-rostered code stay excluded, unchanged.

**PLAYER UNIVERSE ELIGIBILITY vs. FANTASY AVAILABILITY/RISK, honored precisely**: admitted
players whose real status is not `ACT`/`RES` are NOT treated as equally available -- but the
directive's own standard ("no already-validated calibration exists") ruled out expressing this
as a numeric discount. Traced the codebase's own prior, already-completed research on exactly
this question (`score_projection_availability_adjusted`'s docstring,
`redraft_engine_v1_service.py`): `availability_probability` is already known to be a mechanical
restatement of `games/17` with **no event-specific signal**, and a prior session's own tested,
disclosed, NOT-adopted experiment found that using it as a second discount **double-counts** an
existing discount and was explicitly rejected. Given that, the real, exact status is preserved,
undiscarded, in each affected row's own `provenance` text (e.g. `"...; current NFL roster status:
RSR"`) -- honest and visible, never silently dropped, never expressed as a fabricated number.
**1 real row affected this pass**: Jordyn Tyson (WR, `RSR`).

A live, UI-surfaced, scoring-neutral status/risk flag for this signal (distinct from the
provenance text) is a real, disclosed follow-up requiring either a new status/risk-override
`kind` beyond the current three (`SEASON_OUT`/`NOT_WITH_TEAM`/`TEAM_CORRECTION` -- none fit
"still rostered, real reduced-but-nonzero availability") or new UI wiring to show the raw
registry status -- not invented unilaterally this pass.

**Audit of the 5 rookies dropped from the prior 78-row set** (all individually verified against
the fresh registry): Anthony Smith, Emmanuel Henderson Jr., Lewis Bond -- real `DEV` (practice
squad) transitions since 2026-07-30, correctly excluded. Joe Royer -- real `RSN` status, NOT in
the owner-approved `{ACT,RES,EXE,RSR,PUP}` widening (a different, unreviewed code; left excluded,
consistent with the already-approved narrow scope, not force-included). Jam Miller -- a real,
pre-existing (not this-fix-caused) identity-resolution gap: "exact current GSIS identity
unresolved" against the fresh registry's own PFR-ID linkage; unrelated to status filtering.

**Real, empirical proof of "no generic rookie boost" (Section 3)**: compared all 73 real,
projection-value columns (rushing/receiving/passing yards, receptions, `projection_low/high`,
etc.) for every player present in both the old and new admitted sets -- **zero value mismatches**.
Confirms the entire real change this pass is eligibility-only; the model's own projection math
was never touched, and no calibration, boost, or correction of any kind was applied.

## 3. Real governance chain and install

Built a real, rookie-scoped finalize step (`GOVERNANCE_PENDING`->`GOVERNED`,
`MODEL_VALIDATED_REVIEW_ONLY`->`ADMITTED_CURRENT_SEASON`) -- the existing
`finalize_redraft_2026_owner_approval.py` explicitly rejects `rookie=True` rows (its own real
scope is `REDRAFT_2026_VETERAN_PROJECTIONS` only), so this mirrors its exact real transform for
the real, separate `REDRAFT_2026_ROOKIE_PROJECTIONS` scope rather than being misapplied.

Combined the 73 fresh, governed rookie rows with the **491 veteran rows carried forward
byte-for-byte identical from `a1505742`'s own committed `GOVERNED_PROJECTION_SNAPSHOT.csv`**
(verified: zero cell mismatches across every veteran row) -- the veteran admission was not
reopened, not re-derived, not touched.

**Installed via the real, official, existing mechanism this time**: `install_projection_snapshot()`
(`redraft_engine_v1_service.py`) -- the canonical install function this project already has,
used here in place of the manual manifest/approval construction the prior veteran-only admission
used. Real backup of the pre-install files kept at
`projections/2026/archive_2026_09_08_rookie_admission_pre_install/`.

## 4. Brooks-class live path -- determined NOT safe, with real evidence

Traced the codebase's own prior, real, already-completed research
(`docs/codex/NWR_BROOKS_CLASS_SOURCE_GAP_FIX_V1_20260908.md`): a real, honest, 168-case historical
spot-check already found the insufficient-history fallback's cohort-median point estimate
**loses to a naive "predict zero" baseline** (mean MAE 16.79 vs. 9.80; wins only 28/168, 16.7% of
cases). This is real, disqualifying, already-existing evidence against participating in
Recommendations with any confidence contract. **Disposition: stays `VISIBLE_REVIEW_ONLY`** --
no point estimate invented to force a coverage-count improvement.

**Made it searchable/draftable/queueable/comparable anyway**, via the real, already-existing,
already-wired mechanism this project built for exactly this shape of gap
(`udk_unmodeled_skill_asset_service.py`'s manual-asset lane -- the same real mechanism K/DST
already uses, carrying an honest "not modeled by NWR" badge in the UI already). Added 33 real
Brooks-class candidates (from the already-staged, already-verified
`BROOKS_CLASS_FALLBACK_REVIEW_ONLY/` set, itself already confirmed consistent with the final,
post-widening veteran admission -- zero overlap with the ranked universe) to the real Fantasy
Gamers profile's `manual_assets.json` via the existing `merge_manual_assets`/
`write_manual_assets_file` functions, with a distinct, honest authority label naming the real
168-case spot-check result. Real backup kept
(`manual_assets/4c5f04762921420595e4d8c7cda76582.pre_brooks_class_backup_20260908.json`); all 75
pre-existing K/DST entries verified preserved untouched.

## 5. ESPN Top-250 rerun

Rerun against the newly-installed real data (564 rows: 491 veteran + 73 rookie), same corrected
methodology (full 294-row `match_report`, nickname/suffix corrections applied):
**241/250 (96.4%) FULLY_MODELED_FOR_RECOMMENDATION** -- unchanged from the prior fresh-admission
report's own number. Honestly disclosed: none of the 73 newly-admitted rookies, and none of the
33 Brooks-class manual-asset additions, happen to fall inside this specific top-250 window this
pass -- the rookie work is real and correct, but does not move this particular metric. Remaining
gaps unchanged: Jonathon Brooks/Deebo Samuel/Tank Dell/MarShawn Lloyd/Deshaun Watson/Jordan
James/Erick All Jr. (genuine SOURCE_GAP or insufficient-history), Kenneth Gainwell/Cameron Ward
(diagnostic-script-only nickname misses, real players confirmed admitted under their nickname
form), Jaydon Blue/Jawhar Jordan (real, correct `DEV` exclusions), Travis Hunter (genuine
SOURCE_GAP, absent from the registry entirely).

## 6. Multi-league regression

Real mock drafts against the newly-installed 564-row admitted universe (not a synthetic fixture):

```
Case                 Legal complete   Rookies drafted (leaguewide)   Owner roster (skill)
8-team 1QB             128/128          7/73                          RB6 WR5 TE2 QB1
10-team 1QB            160/160          7/73                          WR6 QB2 RB4 TE2
12-team 1QB            192/192          7/73                          WR7 QB2 RB3 TE2
16-team 1QB (19 rds)   304/304          25/73                         RB5 WR8 TE2 QB2
12-team Superflex      216/216          10/73                         RB5 WR6 QB3 TE2
```

All 5 legally complete. Rookie representation scales sensibly with league depth (7 in
16-round leagues, 25 in the deeper 19-round 16-team league, 10 in the 18-round Superflex league)
-- rookies appear more as the board goes deeper, never as blanket inflation (a small, plausible
minority of total picks in every case: 25/304 ≈ 8% at the deepest). K/DST unchanged in every
case (1 K + 1 DST per owner roster). **Structural guarantee, asserted and verified**: no blocked
player (rookie or otherwise) was ever drafted in any case -- `run_complete_mock` only ever
selects from the real, already-admitted ranking pool, so an "unavailable rookie recommended"
scenario is impossible by construction, not merely untested.

**DecisionBundle latency**: one real, confirmatory reading against the real Fantasy Gamers
profile (isolated copy) -- 4.09s wall / 3.08s reported internal latency. Within the previously
established ~5.8-6.95s FAST-preset range; not re-measured broadly or re-optimized (latency
optimization explicitly out of this directive's scope).

## Real regression suite

`tests/test_redraft_2026_projection_model_service.py` (8/8), `tests/test_redraft_2026_rookie_projection_model_service.py`
(13/14 -- the 1 failure is the same pre-existing, unrelated repo inconsistency confirmed via `git
status`/`git log` in the prior fresh-admission task, untouched by this directive's own changes),
`tests/test_projection_freshness_diagnostic_v1_20260908.py` (7/7), `tests/test_desktop_http_api.py`
(40/40). `tests/test_desktop_application_api.py`: unchanged 5/46 pre-existing baseline failures,
41 passed -- no new regression. A new, dedicated test added for the rookie-pipeline status
widening (`test_currently_rostered_statuses_admit_exe_but_exclude_dev_and_preserve_status`).

Both real draft board files re-verified byte-identical throughout every step of this task.

## Status

**DONE.** See the closing report delivered in-session for the exact final field-by-field summary.
