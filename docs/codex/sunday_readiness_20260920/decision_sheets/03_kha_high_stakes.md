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
