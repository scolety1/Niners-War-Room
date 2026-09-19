# Sunday Decision Sheet — 2026 KHA High Stakes League

## Verdict: BLOCKED for lineup and pickup advice

Re-confirmed live this session (Worker 6 closure pass), against the
final-HEAD Redraft app (`1149b89d`): activating the real KHA profile
(`fb1c49402c7644a99120197d41344bbb`) and opening Start/Sit shows, verbatim,
in-app: **"Sleeper league required — Weekly in-season tools (Start/Sit,
Waivers, Trade, streamers) require an active Sleeper-imported league.
Choose or import one."** This is an honest, existing, self-reported
refusal — not a silent failure and not an attempt to serve advice from
stale draft data.

## Exact reason

- **No ESPN Fantasy API integration exists anywhere in this codebase.**
  Reconfirmed by source inspection across this entire cycle (Workers 1, 3,
  4): zero matches for any ESPN API client pattern in `src/`.
- KHA is a real ESPN league (16 teams, PPR, 1QB). The only current data
  this app holds for it anywhere is a real, complete **157-pick historical
  draft board** — draft data, not a current roster. No post-draft
  transaction, waiver, or trade history from ESPN exists in this codebase
  for this league. Historical picks are not a current roster.
- League status badge correctly shows **IN SEASON** (this cycle's own D2
  draft-completion-evidence fix, live-reconfirmed this session) — the app
  correctly knows the season has started, it simply has no live roster
  source to act on.

## Exact input checklist (documentation only — nothing built or attempted)

If the owner wants this closed, one of the following is required:

1. **Real current roster read.** Either (a) the owner manually re-enters
   the current real KHA roster through this app's existing
   `provider: "local"` profile mechanism (already proven safe for local
   test profiles — reuses existing, tested code, zero new integration),
   refreshed by hand whenever it goes stale, or (b) a genuine, new,
   read-only ESPN Fantasy API integration (see item 4).
2. **Real scoring config re-confirmation.** KHA's profile has
   `practical_mode: True` (K/DST already handled by manual entry, an
   existing, unrelated, already-working mechanism) — the rest of the
   scoring settings should be reconfirmed from a live ESPN read or
   re-entered by hand if pursuing a manual-roster path.
3. **Real transaction/waiver state.** No ESPN-sourced transaction, waiver,
   or trade data exists anywhere in this codebase for this league. Any
   FAAB/waiver tooling needs a real, current transaction log, obtainable
   only from a live ESPN API or fully manual owner tracking.
4. **Smallest validated path if a real ESPN integration is pursued (not
   started, listed only):** a genuine, new, read-only ESPN Fantasy API
   client (GET requests only), built the same disciplined way this
   codebase's Sleeper client was — a single, narrow HTTP wrapper plus a
   dedicated import service. ESPN's private-league fantasy API requires
   the owner's own authenticated session cookies (`SWID` and `espn_s2`)
   — these must come from the owner explicitly; this project does not
   scrape, request passwords, or extract browser cookies under any
   circumstance (hard boundary, respected throughout this entire cycle).

## What this sheet cannot do

No lineup, pickup, K/DST, or FAAB advice is provided for KHA. Providing
any of the above from the stale 157-pick draft board would be presenting
historical data as current, which this app correctly refuses to do.

## Addendum — Worker 3 (connection/update pass, 2026-09-19 ~5:00 PM Mountain): live-re-verified, verdict UNCHANGED

Independently re-confirmed this pass via real Chrome MCP browser
interaction against the live app (not just cited from the prior cycle):
activated the real KHA profile and checked, live, in this order — Weekly
Home, Start/Sit (`/lineup`), Improve Team (`/waivers`, Targets tab), and
the K/DST Streamer (`/waivers?tab=streamers`).

- Weekly Home, Start/Sit, and Improve Team all show the same honest,
  static "Sleeper league required" empty state as before — INSPECTED CODE
  confirms this is gated by `data.activeProfile?.provider === "sleeper"`
  across every weekly surface (`in-season.tsx`, `improve-team.tsx`), not a
  silent failure.
- **The K/DST Streamer tab behaves slightly differently and was verified
  precisely, not assumed:** its "External consensus authority" panel
  renders unconditionally (it does not show a static blocked message on
  load, unlike the other tabs), because K/DST ECR reads from FantasyPros
  external consensus rather than the roster. Setting an NFL week and
  clicking "Refresh K/DST ECR" DOES send a real request
  (`POST /api/v1/redraft/kdst/streamer`) — which the backend correctly and
  honestly rejects with a real HTTP 409: **"Command center unavailable —
  The active profile has no valid Sleeper import receipt. Re-import it
  before opening the K/DST Streamer."** This is an honest, backend-
  enforced block, not stale data presented as current, and not a silent
  failure once a request is actually sent.
- **One real, minor, precisely-reproduced UX gap found (not fixed this
  pass):** on first load, before the NFL week field has been manually
  edited, clicking "Refresh K/DST ECR" is a genuine silent no-op — no
  network request, no error, no visible feedback — because the frontend's
  own `streamerWeek` state stays `null` for a non-Sleeper profile (there
  is no live provider week source to resolve it from) even though the
  input visibly displays a fallback "1". Only after the owner types a
  week number does the button actually fire, at which point the backend's
  honest 409 above is what the owner sees. This does not change the
  BLOCKED verdict (the K/DST Streamer still cannot serve real current
  guidance for KHA either way) — it only means the very first click can
  look like nothing happened, rather than immediately showing the honest
  block. Not fixed this pass: no component-test harness (React Testing
  Library or equivalent) exists anywhere in this codebase to safely verify
  a change to this logic per the "test it" requirement, and the
  underlying verdict is unaffected regardless. Flagged as a follow-up for
  a future worker with the appropriate test infrastructure investment.

**Verdict: UNCHANGED. BLOCKED for lineup, pickup, and K/DST advice.**
No sub-capability newly supports KHA this pass.
