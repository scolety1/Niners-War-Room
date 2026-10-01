# NWR — Path to Finished

Branch: `upgrade/nwr-prospective-outcomes-v1-20260914`
As of commit: `768b0b42` (pre-final-push)
Built from: `docs/codex/dogfood_rebuild_20260929/MASTER_REQUIREMENT_LEDGER.md` (79 dispositioned requirement rows, zero placeholder statuses), `LEDGER.md`, and `FULL_SUITE_FAILURE_INVENTORY.md`, all independently reconciled by the coordinating session this cycle.

This document answers one question directly: **what actually remains before NWR can reasonably be considered ready for trusted daily use**, for the two real, live leagues this product actually serves — Fantasy Gamers (Redraft) and Las Vegas Enginerds (Dynasty). It is deliberately aggressive about shrinking scope: nothing below is listed as blocking unless it genuinely blocks reliable weekly fantasy management.

---

## MUST FIX BEFORE TRUSTED DAILY USE

**Nothing.** Every core weekly-management workflow for both real, active leagues is live-verified working today: Home/command-center, Start/Sit, Waiver Wire (ordered claims for Fantasy Gamers, FAAB for Las Vegas Enginerds), Rankings (current-value-aware for both apps), Trade Finder/Analyze Trade/Generate Counters, and Data Health. Every real, reproducible defect found across this entire closure pass — the K/DST Trade Finder composition gap, three of the four long-standing backend test failures, the test-suite canonical-doc-corruption hazard, Dynasty Compare's missing injury disclosure — was fixed and independently re-verified this cycle, not merely logged. The one remaining backend test failure (`test_dynasty_facade_composes_real_governed_workflows`) is a single hardcoded number drifting against a live, machine-shared market-data cache — not a product defect, and does not affect any real user-facing behavior.

## OWNER / AUTHENTICATION GATES

Three items require the owner's own action, not more engineering:

1. **ESPN/Flaim authentication (KHA, 403 N 18th)** — the owner must complete a real OAuth authorization in their own browser; no Claude session can do this headlessly. The downstream import pipeline is built, tested, and ready — this is purely the one remaining gate. See Master Ledger §5 for the exact action/success-signal/what-happens-next.
2. **The governed Redraft snapshot's approval window** (`valid_until: 2026-10-08`) expires in 8 days as of this writing. The owner should re-approve or refresh it before then, or Redraft's Rankings/Data Health will correctly start flagging it as expired rather than merely "Yellow Stale."
3. **A dedicated reliability gauntlet** (cold start, backend/frontend restart races, concurrent-write corruption) has never been built or run for this product (confirmed by a zero-match grep across the entire test suite — Master Ledger §7.27). This does not block today's supervised, owner-present use (the app has been restarted dozens of times this cycle alone with correct recovery every time), but unattended crash-recovery is not a verified property. The owner should decide whether this is worth a dedicated future engineering pass before relying on the product completely unsupervised.

## VALUABLE BUT NOT REQUIRED

Real, scoped, low-risk options that exist but were deliberately not built automatically, per the owner's own standing instruction not to fabricate functionality to fill a gap:

1. **Official Rank** (expert-consensus rank for skill positions, distinct from Market ADP) — `fantasypros_kdst_consensus_service.py` already proves the exact safe pattern (external consensus, never NWR authority) for K/DST; extending it to skill positions reuses the same credential and architecture. Owner decision (Master Ledger §4.1).
2. **My Rank** (a persisted owner-override preference layer) — does not exist anywhere in either app today. A real but currently-unrequested feature (§4.2).
3. **The orphaned Personal Board fields** (`sell_high`/`buy_low`/`my_rank`/`my_tier`/`conviction`) — already validated by the backend schema, completely unreachable today because the HTTP whitelist, response serializer, and frontend UI all independently exclude them. The cheapest real path: wire the existing fields through, no new backend concept needed (§7.9).
4. **Redraft Compare's status-override disclosure gap** — architecturally distinct and larger than the fix just shipped for Dynasty Compare (the override is baked into Redraft's numeric fields with no separate label, unlike Dynasty's clean `assetStatusNotices` precedent). Real, but Compare is a secondary research surface — every primary decision surface (Rankings, Home, Waivers, Trade Lab) already discloses status correctly for both apps (§7.13).
5. **A real Dynasty win-win/target-player trade search engine** (as opposed to the existing single-counterparty counter generator) — named, consistently disclosed as not-yet-built since Worker 7 (§1.6/§1.7/§7.5).
6. **A session-to-session "what changed" layer** and **a real external-platform transaction-history surface** — both confirmed genuinely absent, neither fabricated nor partially faked (§7.21/§7.22).
7. **A freshly-built native installer** for this exact worktree — the packaging mechanism is proven (a real MSI/NSIS installer has been built successfully on this same branch lineage, privacy-scanned clean), just not currently built in this worktree (last attempt here hit host-RAM limits, not a code defect) (§7.25).

## POSTPONED / DO NOT BUILD

Explicitly not pursued, with reasoning, so nobody mistakes silence for an oversight:

1. **Dynasty Trade Package Search / full Trade Finder parity with Redraft** — a real, named capability gap, but building a second full search engine is new feature work, not required for the product to function; Dynasty's `Analyze Trade` + `Generate counters` already cover the core "should I make this trade" workflow.
2. **Rookie draft-pick-asset ownership crosswalk** — a stable, disclosed limitation (picks honestly show "ownership unresolved" rather than a guess); real work, not currently blocking.
3. **`draft_prep_data_foundation_service.py`** — confirmed, by repo-wide grep, to have zero call sites from the live Tauri desktop app. Its real test-suite-corruption hazard was fixed this cycle because running tests must never corrupt tracked history regardless of whether the feature itself is current-product — but no further investment in this legacy V1-era tool is warranted.
4. **`trade_roster_negotiation_service.py`'s buy-low heuristic** — confirmed dead code, superseded by `trade_decision_assistant_service.py`. Not resurrected.

---

## Bottom line

For the two real leagues this product actually manages week to week, NWR is ready for trusted daily use today. What remains is either a real owner action (Flaim auth, the snapshot approval renewal) or a deliberate, disclosed, non-blocking product decision — never a silent gap.
