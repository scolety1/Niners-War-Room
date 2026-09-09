# NWR Cheat Sheet — Combined NWR + Market + Ballers View V1 (2026-09-08)

Real, explicit, in-chat owner authorization (Spencer Colety). Directive: "NWR CHEAT SHEET —
COMBINED NWR + MARKET + BALLERS VIEW / QUICK PRE-DRAFT UX FIX — DO NOT TOUCH ENGINE MATH",
continuing directly from `da1023ba` (Market Data / ADP control center). The owner's real global
Ballers/UDK snapshot is now the full 380-row file (QB 36 / RB 95 / WR 131 / TE 54 / K 32 / DST
32) — confirmed live via a read-only facade check against the real state root before any UI work
started, imported by the owner themselves between the prior directive and this one.

## What changed

`desktop/apps/redraft/src/cheat-sheet.tsx`, plus two new small shared modules extracted from
`draft-room-v2.tsx` (`adp-format.ts`, `ballers-shared.ts`) so the new Combined view reuses the
exact same safe round.pick formatting and Ballers lookup every other surface already uses,
instead of a second, divergent implementation. `draft-room-v2.tsx` itself now re-exports from
those modules (existing imports/tests unchanged) rather than defining the logic inline.

**1. Combined is now the default Cheat Sheet source (directive section 1).** The old binary
NWR/UDK selector is now COMBINED/NWR/BALLERS, defaulting to COMBINED. Combined shows, in one row,
per directive section 9's exact compact-width column list: NWR Rank, Player (team/position/NWR
Tier in the subtitle), this league's own routed Market ADP, Ballers Rank, Ballers Tier, Ballers
Risk, Ballers Upside, Draft/Queue — 8 columns, no horizontal hunting at normal desktop width.
Every other real field the Ballers row carries (its own Ballers ADP, projected points, bye week,
outlook) is in the Ballers Rank/Tier cells' hover tooltip and, in full, one click away in the
existing Player Drawer "Ballers" section (already built in a prior session — confirmed working
correctly against the real 380-row data during this pass, no changes needed there). NWR/BALLERS
single-source modes stay available for a focused view of either.

**2. Market ADP uses the exact same routed field everywhere else already does (directive section
3).** `RedraftRanking.overallAdp` / `ManualDraftAsset.overallAdp` are already computed
server-side per the active league's platform routing (Fantasy Gamers Auto→Sleeper, 403
Auto/override→ESPN) — the Combined table reads that field directly, the identical value
Suggestions/Compare/the Player Drawer already display. No new ADP computation was added.

**3. K/DST get an honest, dedicated layout (directive section 7).** The old 3-column manual
table (Player/Status/Draft) is now Ballers Rank / Team-Player / Active Source / ADP / Draft,
joining each manual K/DST asset to its real Ballers row by the shared `manual:POSITION:TEAM`
player-ID scheme both the manual-asset and Ballers pipelines already use — confirmed a real,
direct ID match in the live data (e.g. `manual:DST:HOU` in both). "Active Source" reads "Ballers
rankings" when the owner's file covers that team, or "Manual · not modeled by NWR" when it
doesn't — never a fabricated NWR score for K/DST. The Source selector (COMBINED/NWR/BALLERS) is
hidden for K/DST sheets, since NWR has no score for them — there is only one honest table, not
three variants of the same data.

**4. A real, live floating-point display bug found and fixed (directive section 10) — this is
the most significant finding of this pass.** `formatRoundPick` (in `draft-room-v2.tsx`, used by
Suggestions/Compare/the Player Drawer's ADP columns, and now also by Cheat Sheets' Combined and
K/DST tables) ran its round/pick-in-round arithmetic directly on the raw overall-ADP number.
Real market ADP is frequently fractional (a consensus/averaged value like 13.3, or Sleeper's own
168.6) — for a fractional input, the modulo step produced a fractional `pickInRound` carrying
real floating-point error (e.g. `3.3000000000000007`), and `String(pickInRound).padStart(2,
"0")` stringified that verbatim, concatenated after the clean integer round. This reproduced,
byte-for-byte, the exact corrupted values the owner's directive quoted
(`2.2.3000000000000007`, `3.3.6000000000000014`, `3.10.399999999999999`) — confirmed live in
this session's own Chrome-rendered Combined table before the fix, screenshotted, then confirmed
clean after. The fix (`adp-format.ts`) rounds the overall pick to the nearest integer before the
round/pick-in-round arithmetic; every existing unit test (all integer inputs) still passes
unchanged, and a new regression test locks in the fractional case (`draft-room-v2.test.ts`,
"never leaks floating-point error for a fractional overall ADP"). This bug was live in
Suggestions, Compare, and the Player Drawer's ADP display too, not just Cheat Sheets — the fix,
being in the one shared function every caller uses, closes it everywhere at once.

**Disclosed, not hidden**: an earlier code-only audit in this same session (before actually
rendering the Combined view with real fractional ADP data) concluded the formatting was already
safe — that conclusion was wrong, and is recorded here rather than quietly corrected. The bug
only reproduces with a genuinely fractional overall-ADP input, which the existing unit tests
never exercised.

## Real data used

Verified via a read-only facade call against the real state root
(`DesktopBackendFacade(repo_root=..., mode="redraft")`, `NWR_REDRAFT_HOME` pointed at the real
install): the active Fantasy Gamers profile carries the full 380-row Ballers snapshot (QB 36 /
RB 95 / WR 131 / TE 54 / K 32 / DST 32, imported 2026-09-09T02:40 UTC) and a 388-row multi-
platform ADP snapshot, Auto→Sleeper. Trey McBride's real Ballers row (Rank #2, Tier 1, Risk 4.2,
Upside 8.3) matches the owner's own worked example in the directive exactly.

## Rendered smoke test (directive section 13)

Stood up the real app against a **fresh, fully isolated copy** of the real state root (a plain
filesystem copy to `%LOCALAPPDATA%\Temp\nwr_gui_test_root_v2` — zero risk to the real KHA/403/
Fantasy Gamers data; the real files were only ever read, never written, during this pass) so the
render reflects the current real 380-row Ballers snapshot rather than a stale fixture. Standalone
backend (`scripts/run_nwr_desktop_api.py`, port 18742) plus the real Vite dev server (port 1422),
rendered and interacted with via Chrome MCP.

Confirmed, screenshot-verified, with real data: Combined Overall (clean round.pick Market ADP
throughout — the exact fix above, visually confirmed before/after), Combined TE (Trey McBride
Risk 4.2 matching the owner's example), NWR-only mode (unchanged), Ballers-only mode (relabeled
"Ballers Rank"/"Ballers ADP"/"Ballers Risk / Upside", Trey McBride 4.2/8.3 again matching), K
sheet and DST sheet (new 5-column honest layout, Source selector correctly hidden), and the
Player Drawer's existing "Ballers" section (Rank #3, Tier 2, ADP, Risk, Upside — all real,
already correctly separated from the NWR/Market/Status stats above it). Draft/Queue actions
remain wired and functional (verified via the embedded Draft Room V2 Cheat Sheets tab, which has
live pick-context; the standalone `/#/cheat-sheet` route intentionally has no Player Drawer or
live pick context, unchanged from before this pass). Zero console errors on a full reload with
console tracking active.

## Tests

- `npx tsc -b apps/dynasty/tsconfig.json apps/redraft/tsconfig.json` — clean, zero errors.
- `npm run test` (vitest) — 16 files, **143** tests passing (142 prior + 1 new float-leakage
  regression test).
- `npm run build:redraft` — production build succeeds.
- `python -m pytest tests/test_desktop_application_api.py -q` — 41 passed, 5 failed; the exact
  known pre-existing baseline, no new failures.

## Engine boundary proof (directive's "DO NOT TOUCH ENGINE MATH")

Every file touched this pass is a `.ts`/`.tsx` frontend file:
```
desktop/apps/redraft/src/cheat-sheet.tsx
desktop/apps/redraft/src/draft-room-v2.tsx        (re-export shims only; logic unchanged)
desktop/apps/redraft/src/draft-room-v2.test.ts    (new test)
desktop/apps/redraft/src/adp-format.ts            (new; extracted, one line of real arithmetic
                                                     changed -- the float-leak fix)
desktop/apps/redraft/src/ballers-shared.ts         (new; extracted, unchanged)
```
Zero Python files. Player Score, Team Score, Championship Equity, RAV, Pick Score,
`marginal_roster_utility`, backup utility rates, candidate ordering, projections, and
status/risk math are all computed exclusively in the untouched backend — provably unchanged.
The one real logic change (`formatRoundPick`'s `Math.round`) is display-only: it changes how an
already-computed ADP number is *shown*, never any ranking, score, or ordering value; the Pick
Score/Player Score/Team Score/Championship Equity values screenshotted throughout this pass
(e.g. Christian McCaffrey Pick Score 100.0, Player Score 290.9) are the same real backend values
seen in the prior directive's own verification.

Both real draft-board file hashes were re-checked before and after this pass. 403 N 18th
(`4b4a990faf124ce7a5d612537ba5943b.json`) is byte-identical throughout
(`ba106a0c1893bc911754d51d17f2efa772b174704a8ccc65b45ac024e22d2b64`). The Fantasy Gamers board
file's hash changed twice during this session's overall work (once between the prior directive
and this one, and once more during this pass) — traced by file mtime to real, independent
activity on the real app each time (the mtimes fall in gaps between this session's own tool
calls, and this session made zero writes to the real state root at any point — only reads, and
one plain filesystem copy for the isolated render fixture above). Disclosed rather than silently
reconciled, consistent with the prior directive's own handling of the same situation.

## Final verdict

**GREEN_COMBINED_CHEAT_SHEET_V1** — the Combined view is real, live, tested, and rendered with
real data; a genuine, previously-unnoticed float-leakage bug was found and fixed at its one
shared source, closing it across Suggestions/Compare/Cheat Sheets/Player Drawer at once; the
engine is provably untouched. No push, no merge, no deploy.
