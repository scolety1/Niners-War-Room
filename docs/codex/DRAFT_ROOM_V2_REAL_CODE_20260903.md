# Draft Room V2 — real isolated candidate (sections 3–6)

Supersedes `docs/codex/DRAFT_ROOM_V2_UI_CONTRACT_20260903.md` (contract
only) with real, working, tested code, per the addendum's explicit
instruction that a contract alone was not enough.

Code: `desktop/apps/redraft/src/draft-room-v2.tsx` (component +
exported pure functions), `draft-room-v2.test.ts` (19 new vitest tests,
40/40 passing across the app). Route: `/draft-room-v2`, added to
`RedraftApp.tsx`'s navigation as "Draft Room V2 (preview)" — a
**distinct route from `/`** (the production Draft Room,
`pages.tsx#DraftRoomPage`, untouched). CSS: appended to `redraft.css`,
namespaced `draft-room-v2-*`/`player-drawer`/`udk-badge-row` so nothing
collides with the production page's styles.

## What's real

Every data field the tabs use already exists in the production
`RedraftBootstrap`/`DraftBoard` payload — **no new backend endpoint was
needed**: `board.beatAdpPool` (NWR rank, market-expected-pick, NWR edge,
timing, make-it-back — the same data the production "Beat ADP pool"
panel already renders) powers Suggestions; `data.rankings` powers
Players; `board.boardCells` powers Board; `board.myRoster` +
`activeProfile.roster` power My Team's strengths/holes; `data.rankings`
+ `manualAssets` + `externalIntelligence` power Compare.

- **Tabs**: Suggestions / Players / Board / My Team / Compare, sidebar
  hideable, matching the target information architecture exactly.
- **Player Drawer**: opens on a plain click anywhere a player row
  appears (Suggestions/Players/Board), showing real NWR rank/Player
  Score/tier, real market ADP/expected round, and real current-alert/
  UDK/FantasyPros fields from `externalIntelligence`.
- **Compare**: Alt+click anywhere adds/removes a player (up to
  `COMPARE_MAX_PLAYERS = 4`, tested), a compare tray appears when not on
  the Compare tab, and the Compare tab itself renders a real table plus
  an **AI Compare Summary** — `generateCompareSummary()`, a real,
  deterministic, template-based function over structured fields only
  (best NWR rank, largest real ADP-vs-rank gap, deepest remaining
  position among the compared players) — no LLM call, no invented
  reasoning, and it says nothing about a field it doesn't have (tested).
- **UDK badges**: `buildUdkBadges()` relocates the exact rendering
  pattern the production Players table already proved (position rank/
  tier/alert chips) onto the new Players tab and is available to
  Suggestions — real UDK data, not fabricated icons.
- **NWR PURE hides external opinions automatically, with no new logic
  needed**: `externalIntelligence` already comes back
  `available: false` / `entries: []` when `nwrPureExperimental` is on
  (this session's earlier section-6 work) — so the drawer/badges here
  simply have nothing to show in that mode, for free.

## What's explicitly NOT connected, and stays visibly labeled

Team Score / Championship Equity / Pick Score / Cost of Waiting are
**not wired to any HTTP route** — `shadow_numeric_authorities_service.py`
remains isolated from every production surface, exactly as it has been
all session. Those columns in Suggestions, and the SHADOW section of the
Player Drawer / My Team tab, render the literal constant
`RESEARCH_NOT_CONNECTED = "Not connected — SHADOW/RESEARCH backend"` —
never a fabricated number, per section 3/10's "research labels must
remain visible; do not make unvalidated values appear production-
authoritative." Wiring a real SHADOW endpoint into this UI is real,
separable follow-on work (its own decision about whether/how to expose
research-only numbers to the owner), not attempted here.

## Verification

`tsc -b` clean, `vitest run apps/redraft` 40/40 (19 new, all pure-
function tests — no React Testing Library in this repo, matching the
established convention of pure-function tests + typecheck/build for JSX
correctness), `vite build` clean (two full rebuilds).

## UDK qualitative flags (section 6) — review queue, not fabricated extraction

Investigated bounded (not "hours," per the directive's own instruction):
the real, already-parsed UDK snapshot CSVs
(`sample_data/kha_real_draft_2026/udk_skill_position_snapshot_with_identity_status.csv`,
`udk_kdst_snapshot_20260902.csv`) carry no My Guy/Value/Bust/Sleeper/
Rookie/Injury Concern/Breakout columns. The raw source PDFs exist on
this machine (`C:\NWR_DRAFT_DAY_TOOLS\2026-09-02\udk\default.pdf` and
`expanded.pdf`) but this environment has no PDF-rendering or icon-
position tooling installed, and no prior PDF-parsing code exists in
this repo to build on — deterministic extraction cannot be proven here.

Per the directive's own fallback instruction, `scripts/build_udk_qualitative_flags_review_queue_v1.py`
produces `sample_data/kha_real_draft_2026/UDK_QUALITATIVE_FLAGS_2026.csv`
(379 real rows, one per real UDK-snapshot player) with every flag column
honestly `NOT_EXTRACTED` and `extraction_confidence =
BLOCKED_NO_DETERMINISTIC_EXTRACTION_TOOLING` — never a fabricated
True/False — plus the real source PDF SHA-256 hashes, so a future pass
with the right tooling (e.g. `pdfplumber`/PyMuPDF installed, or the icon
positions visually confirmed first) has a concrete, ready-shaped starting
point rather than needing to rediscover this investigation from scratch.
No badge/chip for these seven flags is rendered anywhere in Draft Room V2
this pass, matching the "do not fabricate" instruction.
