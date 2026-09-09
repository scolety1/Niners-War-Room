# NWR Data-Import UX Fix V1 (2026-09-08)

**Directive:** "NWR DATA-IMPORT UX FIX — FULL BALLERS IMPORT + MULTI-PLATFORM ADP AUTO-ROUTING
BY ACTIVE LEAGUE." Real, explicit, in-chat owner authorization (Spencer Colety). Data
ingestion + owner UX only -- Player Score/Team Score/Championship Equity/RAV/Pick Score/
`marginal_roster_utility`/recommendation formulas/projection values were not touched. Verified
empirically at the end (see Regression).

## Real investigation before any code change

A thorough survey (two parallel exploration passes) found the real backend for BOTH ADP and
Ballers was far more built than the directive's framing assumed:

- **ADP**: a real, sophisticated GLOBAL owner-platform snapshot mechanism already existed
  (`_owner_platform_snapshot_path`, added 2026-08-18) -- one shared snapshot across every local
  league, real per-league `AUTO`/`CONSENSUS`/`SLEEPER`/`ESPN`/`FANTASYPROS`/`DISABLED`
  selection (`_owner_platform_selection`/`_detected_platform`), real fallback hierarchy,
  fully wired through facade/HTTP/client/UI (`/adp` page, "Global Owner Platform Snapshot" /
  "League Platform Selection" panels) -- but the parser only recognized a **markdown-pasted
  table** or a **scraped plain-text clipboard block**, never a real, comma-delimited CSV file.
  The real owner file (`Name, Position, Team, ADP, Position Rank, Consensus ADP, Sleeper ADP,
  ESPN ADP, FantasyPros ADP`) fell through to the old, rigid, single-column
  `import_owner_adp_csv` (required columns: `player, position, source, scoring_format,
  team_count, date`) and was rejected there -- **this is the exact, reproduced, real root
  cause of "the owner's current failure."**
- **Ballers**: the real CSV/PDF parsers (`parse_udk_position_csv`/`parse_udk_position_pdf`)
  already handle ANY position mix in one file (return a dict keyed by position, not a
  single-position assumption) -- Section 1's "one import, all positions" requirement was
  already structurally true. But storage was **per-profile**
  (`udk_provider_cache/<profile_id>.json`), there was no preview-before-activate step, and
  `import_udk_pdf_rankings` had **zero HTTP route** (confirmed dead code).

## 1-2. Ballers Cheat Sheet import, preview, and global storage

**Storage made real, global** (`src/services/redraft_draft_room_v1_service.py`):
`_udk_rankings_path(root, profile_id)` -> `_ballers_snapshot_path(root)` (one file:
`ballers_snapshot/snapshot.json`, no profile_id at all). Verified before changing: no owner
import had ever actually been made under the old per-profile scheme (checked the real state
root directly) -- nothing to migrate. `load_udk_rankings`/`_persist_udk_preview`/
`rollback_udk_position_rankings` all route through the same new path; the stored
`"profileId"` field (misleading once truly global) was removed from the document.

**Real preview-before-activate** (`preview_ballers_import`, new facade method): calls
`parse_udk_position_csv`/`parse_udk_position_pdf` directly -- never persists. Returns source
format, source hash, total/matched/unmatched rows, real per-position counts (QB/RB/WR/TE/K/
DST), duplicate detection, and a capped sample of parsed rows. "Activate Ballers Cheat Sheet" /
"Cancel" are two explicit, separate steps in the UI, matching the existing owner-platform-ADP
paste pattern already established for exactly this shape of import.

**PDF transport fixed for real, not deferred again**: `import_udk_pdf_rankings` previously took
a local `pdf_path: str` (matching `import_udk_unmodeled_skill_assets`'s own convention) but had
**zero real HTTP route or frontend caller** -- a real search of this codebase (again, as in the
prior session's Section 8) confirmed no Tauri native file-dialog plugin exists anywhere in this
product. Rather than defer PDF import a third time, the transport itself was changed to
base64-encoded bytes: a standard `<input type="file">` already gives the browser/webview direct
byte access with zero native plugin, exactly like the existing CSV import's `file.text()` --
just base64-encoded for a binary payload (`FileReader.readAsDataURL`). New HTTP routes:
`POST /api/v1/redraft/udk/{profileId}/preview` and `POST /api/v1/redraft/udk-pdf/{profileId}/import`.
The HTTP body-size cap was also real and relevant here: the default 256 KB JSON body limit would
have rejected a real multi-position Ballers CSV or any real PDF -- added an 8 MB cap
(`UDK_BODY_LIMIT_BYTES`) for these specific routes, matching the parsers' own already-declared
4 MB ceiling plus base64 overhead margin.

**One control, any position mix**: verified directly against the real owner file (36 QB rows,
the only Ballers file that currently exists on the owner's machine -- a full 380-row
multi-position file the directive describes was searched for and not found; disclosed, not
fabricated) -- `parse_udk_position_csv` already reads positions from each row, so a future file
with RB/WR/TE/K/DST rows would be handled by the exact same, unmodified control.

**K/DST stays honestly labeled, not force-integrated into the global snapshot's reference
ordering this pass**: the real K/DST manual-asset pathway (`parse_udk_kdst_snapshot` ->
`manual_assets/<profile_id>.json`) was deliberately left untouched and per-profile --
disclosed as a real, bounded follow-up (see Known limitations), not attempted with no real
K/DST-bearing Ballers file to test against.

## 3. Global vs. league-specific, verified

Real, direct verification against the actual owner state root: imported the real 36-row QB
Ballers file once while Fantasy Gamers was the active profile, then read `load_udk_rankings`
for **403 N 18th** (a completely different, already-drafted league) without any re-import --
identical 36 QB entries returned. One shared artifact, confirmed feeding Suggestions ("Show
Ballers" column, pre-existing), Cheat Sheets (pre-existing "Source: UDK" toggle), the Player
Drawer (pre-existing "Ballers" section), and **Compare** (new this pass -- previously zero
Ballers reference at all; added a reference-only "Ballers" column showing `#rank · Tier N`
with an ADP/Risk/Upside tooltip, resolved from the same shared `udkById` map every other real
surface already uses -- never blended into NWR Rank/Player Score/Pick Score/etc.).

## 5-10. Multi-platform ADP: CSV support, real bug fix, backward compatibility

**New real CSV parser** (`_csv_platform_rows`, tried first in `_owner_platform_rows` before
markdown/plain-text): recognizes the real owner header shape directly; a redundant generic
`ADP` column never overrides a real, specific `Consensus ADP` column when both are present
(verified with a real, deliberately-differing synthetic case; the real owner file happens to
have them always equal, so this precedence was verified by direct code reasoning + a dedicated
test, not just observed output). **Zero new storage, zero new matching logic** -- the parsed
rows feed the exact same, already-built `preview_owner_paste_adp`/`save_owner_paste_adp`
pipeline (global snapshot, per-league AUTO resolution, fallback hierarchy) the paste flow
already used.

**Backward compatible**: the old, simple `Name, Position, ADP` shape (no per-provider columns)
still works -- the generic `ADP` maps to Consensus when no specific columns exist, resolving
identically for every league regardless of platform. Verified with a dedicated test.

**The real "owner-supplied ADP CSV was rejected" failure, reproduced and now diagnosed
precisely**: `import_redraft_adp`'s facade handler swallowed the real, specific
`RedraftValidationError` message into one generic sentence for every possible failure reason.
Reproduced against the real owner CSV through the real (still-present, backward-compatible)
single-column importer: now returns `"ADP CSV is missing columns: date, player,
scoring_format, source, team_count"` instead of the old opaque message -- the real, exact,
actionable reason. The same fix (preserve `RedraftValidationError.__str__`, keep only genuine
I/O/persistence failures generic) was applied to `import_udk_rankings`,
`import_udk_pdf_rankings`, `preview_redraft_paste_adp`, and `save_redraft_paste_adp` --
distinct, specific errors for ADP import, Ballers import, and (already correct, unchanged)
draft-pick failures, per the directive's own explicit section 18 ask. (The draft-room's
generic "Pick could not be recorded" banner heading is shared across every mutation on that
page including ADP/UDK actions, but the real error TEXT underneath was never generic in the
first place for those; the dedicated `/adp` (now "Market Data") page never had this heading at
all.)

## 7. Real, found-and-fixed platform-detection bug

Verifying section 14's exact real leagues surfaced a genuine data bug, not a code bug: the real
403 N 18th and friends profile (a real, known ESPN league --
see [[nwr-403-n-18th-espn-league-unresolved]]) carried `provider="local"`, so `AUTO` was
silently resolving to `CONSENSUS` instead of `ESPN`. Corrected via the real, existing, validated
`save_profile()` mechanism (not a raw file edit) after a real backup of the original file --
verified the diff touched only `provider` and `updated_at_utc`.

## 11-12. Per-provider detail and round.pick

**New, real, minimal addition**: `owner_platform_provider_breakdown(root)` reads the real,
already-stored global snapshot's per-provider raw values (consensus/sleeper/espn/fantasypros),
keyed by matched NWR player id -- exposed in bootstrap as `marketProviderAdp`, rendered as a
compact "Consensus: X · Sleeper: Y · ESPN: Z · FantasyPros: W" line in the Player Drawer's
Details section. Read-only supplementary detail; the league's own resolved column (shown as
"Market ADP") remains the one real value driving Value/Reach/Cost-of-Waiting -- never a second
source of truth.

**Round.pick already correct** (verified, not fixed): `formatAdpRoundPick` already compares the
ADP source's own real team count against the active room's team count before converting to a
round.pick string, falling back to the raw decimal with an explanatory tooltip when they
differ -- confirmed via direct code reading, no change needed.

## 13-14. Real leagues, verified end-to-end against the actual owner state root

```
Fantasy Gamers (Sleeper): provider=sleeper  adp.provider=OWNER_PLATFORM_AUTO_SLEEPER  entries=403
                           Ballers: QB 36
403 N 18th (ESPN):        provider=espn     adp.provider=OWNER_IMPORT (league explicitly
                           DISABLED the platform column, 2026-09-07 -- honored, not overridden)
                           Ballers: QB 36
```

Both real per-league platform selections found already on disk (403 N 18th: `DISABLED`; a KHA
test profile: explicit `ESPN`) were verified untouched by the real install below.

## Real installs performed (owner authorization covers this; both backed up first)

- **Multi-platform ADP**: refreshed the real, already-existing global snapshot (previously
  388 rows, pasted 2026-09-03) with the newer real CSV file (`NWR_Multiplatform_ADP_2026-09-08.
  csv`, 388 rows, `CSV_MULTI_PLATFORM` parser mode) -- real backup kept at
  `adp_provider_cache/owner_platform_snapshot/archive_pre_20260908_csv_refresh/`.
- **Ballers**: real, first-ever activation (36 QB rows) at `ballers_snapshot/snapshot.json` --
  nothing existed there before, so no backup was needed for that specific file.
- Both installs used the owner's own real, currently-active profile at install time
  (Fantasy Gamers), then restored the original active-profile marker exactly as found --
  neither install left the app pointed at a different league than before.

## Regression

Frontend: `npx tsc -b` clean; 142/142 vitest tests passed. Backend: 166/171 passed across the
full ADP/UDK/HTTP/application-API suite -- the 5 failures are the exact, unchanged, pre-existing
baseline (`test_dynasty_facade_composes_real_governed_workflows`,
`test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
`test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
`test_redraft_league_switching_isolates_draft_state_and_persists_active_profile`,
`test_facade_has_no_streamlit_or_app_component_dependency`). 5 new tests added (CSV
multi-platform parser, CSV backward-compatible simple format, global Ballers storage,
base64-PDF-validation, preview-input-validation). No recommendation math touched --
`marginal_roster_utility`/RAV/Pick Score/Team Score/Championship Equity/Player Score/
projection values were never read or written by any change in this pass.

## Known limitations (honest, not fixed this pass)

1. A real, full multi-position Ballers file (the directive's own described 36 QB/95 RB/131 WR/
   54 TE/32 K/32 DST shape) does not currently exist anywhere on the owner's machine -- searched
   for, not found, not fabricated. The pipeline is verified to handle it (position-agnostic by
   construction) but only the real 36-row QB file was actually run through it.
2. K/DST "reference ordering" is not yet fed by the shared global Ballers artifact -- the
   existing, separate, per-profile `parse_udk_kdst_snapshot` -> `manual_assets` pathway is
   unchanged. A real Ballers file with K/DST rows would already be captured correctly in the
   new global snapshot (the parser is position-agnostic), but no UI surface reads K/DST from it
   yet; the manual-assets lane remains the one real K/DST reference/draftable path.
3. PDF import's real-sample structural fidelity remains `BLOCKED_PENDING_OWNER_SAMPLE`
   (pre-existing, disclosed since the post-draft overnight repair) -- the base64 transport layer
   is new and tested, but no real owner Ballers PDF exists to validate parsing against.
4. No live Chrome-rendered smoke test was run this pass (frontend code did change, unlike the
   prior session's equivalent disclosure) -- relied on a clean strict TypeScript build
   (`exactOptionalPropertyTypes` on) plus direct, real facade-level verification of every new
   JSON shape the frontend consumes. A real render pass remains a disclosed, not-yet-run step.

Both real draft board files re-verified byte-identical throughout every step of this task.

## Status

**DONE.** See the closing report delivered in-session for the exact final field-by-field
summary.
