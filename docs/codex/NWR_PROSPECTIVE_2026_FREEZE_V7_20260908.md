# NWR Prospective 2026 Freeze V7 (2026-09-08, rookie/insufficient-history closure)

**Verdict: `NEXT_DRAFT_READY_VETERAN_AND_ROOKIE_LIVE`**

**HEAD:** `b2555f095cd1e4e2b6b9b08754dba5cf2b1fdce9`

Does NOT overwrite V1-V6 (`NWR_PROSPECTIVE_2026_FREEZE_20260907.md` d815c633,
`..._V2_20260908.md` 5ec89064, `..._V3_20260908.md` c318a10c, `..._V4_20260908.md` 26c455d9,
`..._V5_20260908.md` eaef1a47, `..._V6_20260908.md` a1505742). Covers the real work of the "NWR
NEXT-DRAFT ROOKIE / INSUFFICIENT-HISTORY CLOSURE" directive, starting from V6's own HEAD.

## What changed since V6

1. **Rookie component re-governed, fresh** (`b2555f09`): the prior 78-row rookie admission's own
   receipt was independently expired (`source_as_of=2026-07-30`, 40+ days old, blocked
   regardless of the veteran admission's state). Built fresh through the existing rookie
   pipeline, all 9 real promotion gates PASS -- 73 real rows.
2. **Rookie status-universe filter fixed systemically** -- the same real
   `CURRENTLY_ROSTERED_STATUSES` widening now applied to the true-rookie pipeline too (single
   shared constant with the veteran fix). PLAYER UNIVERSE ELIGIBILITY vs. FANTASY
   AVAILABILITY/RISK made explicit: the real, exact non-ACT/RES status is preserved in
   `provenance`, never expressed as a fabricated numeric discount (traced and honored this
   codebase's own prior, completed, disqualifying research on `availability_probability`).
3. **Empirically verified zero generic rookie boost** -- all 73 overlapping players' real
   projection values are byte-identical old vs. new; only eligibility changed.
4. **Brooks-class determined, with real evidence, NOT safe as a live recommendation input**
   (a real, already-existing 168-case historical spot-check shows it loses to a naive zero
   baseline) -- stays `VISIBLE_REVIEW_ONLY`. Made searchable/draftable/queueable/comparable via
   the existing manual-asset lane instead (33 real candidates added to the real Fantasy Gamers
   profile).
5. **Veteran admission (491 rows, `a1505742`) preserved byte-for-byte, verified** -- not
   reopened, not re-derived, not touched.
6. **Real, official `install_projection_snapshot()` mechanism used for the install** for the
   first time (in place of the prior pass's manual manifest/approval construction).

## What did NOT change

Team Score, Championship Equity, Pick Score, `marginal_roster_utility`'s own formulas; the
veteran admission (491 rows, byte-identical); the Diggs-class fix; DecisionBundle latency (not
re-optimized, confirmed unchanged); FFA admission decision; the historical burned-holdout rule;
K/DST's manual/unmodeled status.

## Updated frozen component versions (delta from V6)

| Component | V6 status | V7 status |
|---|---|---|
| Rookie admission | Expired (2026-07-30 receipt) | **Fresh, governed** (73 rows, `source_as_of=2026-09-08`) |
| Rookie status filter | `ACT`/`RES` only | **`ACT`/`RES`/`EXE`/`RSR`/`PUP`** (same shared constant as veterans; `DEV` stays excluded) |
| Rookie status disclosure | N/A | Real, exact status preserved in `provenance` for non-ACT/RES admitted rows (1 real case: Jordyn Tyson, RSR) |
| Brooks-class fallback | Staged, review-only, no consumption path | **Determined NOT recommendation-safe (real evidence)**; searchable/draftable/queueable via manual assets |
| Combined admitted universe | 491 (veteran only) | **564** (491 veteran + 73 rookie) |
| ESPN Top-250 | 241/250 | **241/250** (unchanged -- rookie work doesn't move this window) |
| Install mechanism | Manual manifest/approval construction | **Real `install_projection_snapshot()`** |

Every other V6 component/limitation entry stands unchanged.

## Real coverage/count summary

- Admitted universe: 564 real players (491 veteran + 73 rookie).
- Real ESPN Top-250 coverage: 241/250 (96.4%) FULLY_MODELED_FOR_RECOMMENDATION.
- Real Brooks-class searchable/draftable pool: 33 real players (manual assets, Fantasy Gamers).
- Multi-league regression: 5/5 (8/10/12/16-team 1QB + 12-team Superflex) legally complete;
  rookie representation 7-25 per league depending on depth; zero blocked-player-drafted
  violations (structurally guaranteed).
- DecisionBundle latency: ~4.1s (one real confirmatory reading; unchanged/not re-optimized).

## Known limitations carried forward (honest, not fixed this directive)

1. A live, UI-surfaced, scoring-neutral status/risk flag for the EXE/RSR/PUP distinction (both
   veteran and rookie) remains a real, disclosed follow-up -- requires either a new status/risk
   override `kind` or new UI wiring, not invented unilaterally.
2. Joe Royer's real `RSN` status remains outside the owner-approved widening (not force-included).
3. Jam Miller's real identity-resolution gap (fresh-registry PFR-ID linkage) is a real,
   pre-existing rookie-pipeline limitation, unrelated to this fix, not chased down this pass.
4. Zero true 2026 rookies (beyond the pre-existing De'Zhaun Stribling overlap) fall inside the
   real ESPN top-250 window -- whether the rookie draft-evidence pipeline's own coverage/matching
   is complete for genuinely elite rookie prospects was not investigated this pass (a real,
   disclosed, out-of-scope model-research question).
5. K/DST direct model remains research-only, correctly not promoted (unchanged).
6. Travis Hunter remains a genuine SOURCE_GAP (unchanged).

## Prospective evaluation protocol (unchanged from V1-V6, restated)

1. 2016/2024/2025 remain permanently excluded from this engine's evaluation.
2. When 2026 season results become available, compare against this frozen state honestly.
3. Do not retune Team Score/Championship Equity/Pick Score/`marginal_roster_utility`/
   `CURRENTLY_ROSTERED_STATUSES` based on this freeze or any single 2026 outcome.
4. If 2026 real outcomes suggest any component underperforms, that is real, new prospective
   evidence to be evaluated on its own terms, not silently reverted.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SVeKhFHk5pYE5iRihLvFxy
