# Lane 3 Report — League-First Shell and Disclosed UI Gaps

## Outcome

Completed all requested Lane 3 work on `overnight/lane3-league-shell-20260909`, starting from `a72500a6`. No canonical branch was changed and nothing was pushed.

Incremental commits:

- `cb9a36a1` — `feat(redraft): add league-first chooser flow`
- `75ae6d63` — `fix(redraft): remount league workspace on profile switch`
- `b73f931a` — `feat(redraft): focus active player search with slash`

## Implementation

### 1. League chooser

- Added `/leagues` and a dedicated card-based chooser in `desktop/apps/redraft/src/leagues.tsx:11`.
- Cards come from `data.profiles`, the bootstrap's authoritative persisted/non-archived league list (`leagues.tsx:51-80`). Each card shows the league name, active state, `leagueFormat()` metadata, and `leagueIdentityFormat()` provider identity (`leagues.tsx:67-76`).
- Card activation reuses the existing mutation contract exactly: `client.activateRedraftProfile(profile.profileId)`, replace the full bootstrap through `onUpdate(next)`, then navigate to `/draft-room-v2` (`leagues.tsx:25-41`). A ref-backed in-flight guard prevents overlapping rapid activations.
- Presets were intentionally not rendered as activatable cards. `builtin_presets()` creates `preset:*` templates (`src/services/redraft_engine_v1_service.py:257`), and the existing Profile page uses them only as inputs to `createRedraftProfile`; actual Tester/practice leagues surface through `data.profiles` like every other saved profile.
- Added responsive real-card styling, separate from the cramped `.profile-list` rules, in `desktop/apps/redraft/src/redraft.css:171-199` and `:293`.
- The no-profile state links to existing `/profile` setup instead of inventing another creation flow (`leagues.tsx:82-88`).

### 2. Launch and empty routing

- `/` now chooses `/leagues` when `activeProfileId` is null and `/draft-room-v2` otherwise (`desktop/apps/redraft/src/RedraftApp.tsx:127`).
- `/draft-room-v2` redirects to `/leagues` only when no active profile exists (`RedraftApp.tsx:129-146`), removing the bare Draft Room dead end. With an active profile, direct deep links still render the Draft Room normally.
- The chooser route is registered at `RedraftApp.tsx:128`. Its page intentionally omits the redundant Active League banner (`RedraftApp.tsx:115`).

### 3. One exit-to-chooser target

- The existing Active League banner's league-name text is now the single obvious chooser link (`RedraftApp.tsx:229-231`), with hover and keyboard-focus treatment in `redraft.css:42-44`.
- The existing Switch League dropdown remains the quick in-place switch. No additional sidebar/nav “switch league” action was added.

### 4. League-scoped remount correctness

- `DraftRoomV2Page` is keyed by `data.activeProfileId` at the route boundary (`RedraftApp.tsx:129-146`). A bootstrap replacement that changes leagues therefore remounts the full league-scoped Draft Room state tree, clearing queue, setup, selected roster, drawer, comparison, search, view, and filter state together.
- Reviewed all Draft Room effects. There are no empty-dependency effects that rely on surviving profile switches; profile-dependent intelligence and decision fetches already include `activeProfileId` and use cancellation guards (`desktop/apps/redraft/src/draft-room-v2.tsx:1160-1237`).
- Shared `statusOverrides` and the static `historicalReplay` cache were lifted above the keyed boundary so they survive unchanged (`RedraftApp.tsx:51-59`). The override list still reloads only from its shared backend source (`RedraftApp.tsx:90-106`), and the historical artifact remains lazy-loaded when Replay is opened.
- Sidebar collapse remains owned by `RedraftApp`; global bootstrap snapshots (`profiles`, `presets`, ADP/Ballers/UDK data) remain in the wholesale `RedraftBootstrap`. None are placed below or cleared by the league key.
- Existing profile-keyed fetch state (`externalIntel`, `decisionBundle`, `rawActionValueById`) was not given duplicate reset logic.

### 5a. `/` search shortcut

- Added a window-level slash handler in the Draft Room (`draft-room-v2.tsx:824-835`). It focuses the global quick-pick input on normal tabs and Compare's Add Player input while Compare is active (`draft-room-v2.tsx:807`, `:1648`, `:3368-3415`).
- The guard ignores modified/handled events and does not hijack input, textarea, or contenteditable typing (`draft-room-v2.tsx:88-101`).
- Extended the shared `SearchInput` with an optional input ref, preserving every existing caller (`desktop/packages/ui/src/components.tsx:207`).
- Added shortcut regression coverage at `desktop/apps/redraft/src/draft-room-v2.test.ts:357-388`.

### 5b. Player Drawer Ballers/UDK source

- The starting commit already contained the correct shared-source wiring. Verified that one `buildUdkEntryById(data.udkRankings)` map is built at `draft-room-v2.tsx:1285`, the drawer resolves `drawerUdkEntry` from it at `:1353`, and the Player Drawer renders that `UdkPlayerEntry` in its Ballers section at `:3812-3828`. No stale `drawerEntry.udkPositionRank`/`udkTier` read remains in that display.
- Added a regression test proving the shared helper indexes the current imported UDK entry by player ID (`draft-room-v2.test.ts:332-355`).

### 5c. Metric statuses

- Decision Quality's intentional independent `n/a` / `SKIPPED_TOP_N_ONLY` disclosure lane remains unchanged at `draft-room-v2.tsx:2230-2243`.

## Verification

- `npm.cmd run typecheck` — PASS; both Dynasty and Redraft TypeScript project references completed with zero errors.
- `npm.cmd test -- --reporter=verbose` — PASS; **16/16 test files, 147/147 tests, 0 failures**. There are no final pre-existing failures and no introduced failures.
- `npm.cmd run build:redraft` — PASS; Vite production build completed, 46 modules transformed.
- `git diff --check` — PASS before each commit; no whitespace errors.
- Manual trace — followed chooser card click through API activation, full-bootstrap replacement, navigation, keyed Draft Room remount, and the active/no-active route branches. Traced the slash target selection and the shared UDK map into the Player Drawer. Browser screenshots were not required or available for this lane.

## Failure taxonomy and remaining work

- **IMPLEMENTATION_DEFECT:** none remaining.
- **ENVIRONMENT_DEFECT (resolved):** Windows execution policy blocks the `npm.ps1` shim, and dependencies were initially absent. Installed exactly from `desktop/package-lock.json` with `npm.cmd ci` and used `npm.cmd` for verification. This did not block delivery.
- `npm ci` reported four existing dependency advisories (two moderate, two high). The lockfile was not changed because dependency remediation was outside this reconciliation task.
- Uncompleted requested items: none.
