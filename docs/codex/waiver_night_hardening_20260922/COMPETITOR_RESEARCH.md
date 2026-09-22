# Waiver-Night Hardening V1 — Competitor Research (Worker 1, Phase 1)

Date: 2026-09-22
Method: WebSearch + WebFetch against public/official product & help-center pages only (no scraping of gated app UI, no third-party review blogs treated as authoritative — official docs preferred and cited). All claims below are **LIVE OBSERVATION (via WebSearch/WebFetch of public documentation)**, not INSPECTED CODE — treat vendor self-description as directional product framing, not verified behavior.

Goal: extract FUNCTIONAL product requirements (not UI/visual design) from leading in-season fantasy tools, then compare against NWR's actual current capability (from Phase 0 code reading, see `LEDGER.md` for the Phase-0-sourced comparison table). This file is the raw competitor findings; the honest gap/no-gap judgment against NWR lives in `LEDGER.md` so it can cite the Phase-0 code evidence directly.

---

## 1. FantasyPros — My Playbook / Waiver Assistant / Waiver Planner

Source: fantasypros.com and support.fantasypros.com (Waiver Planner support article was 403-blocked to fetch directly; findings below are from search-result summaries of that and adjacent pages).

- **Waiver Planner**: reviews the user's team + league in one pass and produces a *complete waiver strategy* per league — not just a ranked list. Output includes: specific pickup **targets**, a **priority order** across those targets, a **suggested FAAB bid** per target, and a **one-click submit** path that sends the claims directly to the league host (ESPN/Yahoo/Sleeper/CBS etc., since My Playbook supports league import/sync from those hosts).
- **Waiver Assistant** (separate, more analytical tool inside My Playbook): for each available free agent, shows a full **add/drop scenario analysis** — i.e., it doesn't just rank free agents in isolation, it evaluates the *net roster impact* of a specific add+drop pair against the user's actual roster.
- **Multi-league**: leagues are imported/synced once; recommendations, lineups, and (for paid tiers) direct-submit are then available across all synced leagues from one screen — explicitly framed as saving the "switch app, re-check settings" tax of running several leagues.
- **Start/Sit Assistant**: recommendations come from *expert consensus rankings* blended with matchup analysis; user can pick which individual experts to weight, or use FantasyPros' default panel. Submits directly to host. Manual override ("Edit Lineup") always available alongside the assisted recommendation.
- **Freshness/notifications**: once a league is synced, breaking news affecting a rostered player triggers push notifications — freshness is surfaced as *event-driven alerts*, not just a "last updated" timestamp.

**Functional takeaways to weigh against NWR**: (a) FAAB bid suggestion bundled directly with a ranked, prioritized *plan* rather than a flat list; (b) explicit add/drop scenario pairing rather than ranking adds and drops separately; (c) true multi-league one-screen view with per-league custom scoring already resolved; (d) direct one-click submission to the host (NWR is explicitly read/recommend-only per this cycle's hard boundary — no writes — so this is a deliberate non-goal, not a gap).

---

## 2. Draft Sharks — Free Agent Finder / Who to Start

Source: draftsharks.com/kb/waiver-wire-assistant, draftsharks.com/who-should-i-start (fetched directly).

### Free Agent Finder
- **Ranking is multi-metric and user-selectable**, not a single blended score: sortable by "current week projection," "ceiling projection for the week," "Rest of Season projection," or "Consensus ROS projection." The user picks the lens (this week vs. ROS vs. upside) rather than the tool picking one for them.
- **Bye-week / strength-of-schedule (SOS) look-ahead is a first-class sort dimension**: "positional SOS for either of the next two matchups" and "SOS for rest of season" are both explicit, separately sortable fields — this is proactive roster planning, not just reactive current-week advice.
- **Cross-league identity resolution**: a single player search shows that player's *availability status in every synced league at once* — useful the instant injury news breaks, to immediately know which of several leagues still has that handcuff/replacement sitting on waivers.
- **Explicit timeframe framing per candidate**: the tool literally asks "best option for rest of season? A one-week fill-in? A DST for next week?" — i.e. weekly-need vs. ROS-need vs. streamer-need are treated as three distinct product framings a user picks between, not folded into one number.
- Roster-needs-aware: knows which players are already on the user's roster and which are on other rosters in the same league, to avoid suggesting unavailable players.

### Who to Start
- **Floor / median / ceiling are all first-class, always shown together** — floor = "downside risk without assuming an injury," ceiling = "everything breaks right." These are described as always part of the formula, with a **strategy slider ("Safety" ↔ "Ceiling")** that re-weights which end of the distribution drives the final start/sit call, rather than the user having to interpret three separate numbers themselves.
- **Matchup context is concrete and player-relevant**: opponent's positional rank against the player's position, plus an "Adjusted Points Allowed" figure that's specific to that matchup (not a generic team ranking), plus a season trend graph for the player, plus recent injury/news blurbs feeding the same view.

**Functional takeaways**: (a) explicit floor/median/ceiling *with a user-adjustable risk slider*, not just three static numbers; (b) SOS/bye-week look-ahead as an explicit sortable dimension on both the weekly and ROS lens; (c) explicit three-way timeframe split (this-week / ROS / streamer) as separate product framings.

---

## 3. RotoWire — My Leagues

Source: rotowire.com/myleagues, rotowire.com/football/ search summaries.

- Waiver tool lets the user **pick a waiver strategy** (roughly: safe/floor vs. upside/ceiling orientation) and then tags pickups as "safest," "most upside," and "most selected" (i.e., a popularity/consensus-add-rate signal), letting the same underlying free-agent pool be read three different ways depending on user risk posture.
- Distinguishes **just-this-week value vs. full-season value** explicitly as a toggle ("for just the week or an entire season").
- Lineup optimizer offers a **binary choice between "safest" and "highest upside" suggested lineups** rather than one blended recommendation — conceptually the same floor/ceiling framing as Draft Sharks, presented as two alternate complete lineups instead of a single slider.
- **News feed integrated directly into the My Leagues context**: injury updates, depth-chart changes, and fantasy-relevant headlines are shown *in the same screen* as the waiver/lineup tools, not as a separate news section the user has to cross-reference manually.

**Functional takeaways**: (a) "most selected" as a distinct, explicit popularity/consensus signal alongside projection-based ranking; (b) two full alternate lineups (safe vs. upside) as an actionable output format, not just a stat.

---

## 4. Footballguys — Waiver / League Dominator

Source: footballguys.com, footballguys.com/waiver-wire, footballguys.com/dominator search summaries.

- **League sync drives personalized, settings-aware advice across start/sit, waivers, and trades from one sync action** — described as "weekly in-season advice based on your roster and the players actually available to you," i.e. the free-agent pool shown is always filtered to true availability in that specific league, not a generic top-N list.
- Once synced, "your players and free agents will be highlighted" directly in rankings pages — ownership status is a first-class visual/data attribute layered onto the same ranking table the tool already shows everyone, rather than a separate "my team" view.
- **FAAB bid-percentage framing**: waiver-wire "gems" are shown with "the percentage of a blind-bid budget used" for that type of pickup in leagues that run FAAB — i.e. bid guidance is given as a *percent of budget*, not just a raw dollar number, which generalizes across leagues with very different total FAAB budgets.
- Supports Redraft, Dynasty, Best Ball, IDP, Superflex, DFS all under the same "sync and get settings-aware advice" umbrella.

**Functional takeaways**: (a) ownership/ADP-style highlighting layered directly onto full rankings rather than a separate silo; (b) FAAB guidance normalized as % of remaining budget, not just absolute dollars.

---

## 5. Sleeper — native in-season UX

Source: sleeper.com, support.sleeper.com, sleeper.com/blog (search summaries; third-party review note flagged as such, not vendor-authoritative).

- Natively supports **three waiver systems** (rolling, reverse-standings, FAAB) and does not force one — the league commissioner configures which the league runs, and Sleeper's own tools adapt to whichever is active. This matches NWR's own project-memory precedent of "never assume unknown league rules, represent as configurable" (AGENTS.md) — Sleeper's own product explicitly treats waiver *type* as a per-league config, not a global assumption.
- Commissioners can edit FAAB budgets live from the mobile app mid-season.
- **Known UX gap** (third-party/review-sourced, not vendor doc — flagged as lower-confidence): Sleeper is reported to have thin built-in player outlooks/recaps and a waiver order that's reportedly hard to find in-app, which is why third-party trend-watching tools (e.g. add-rate spike detectors polling Sleeper's own API) exist as an ecosystem workaround. This is a *gap in Sleeper itself*, not something for NWR to imitate — but it does validate that "add-rate/trending" signals are a real, wanted product surface that Sleeper's own native UI under-serves.

**Functional takeaway**: waiver-type-as-config (rolling/reverse-standings/FAAB) is validated as standard practice; a "trending adds" signal is a real wanted surface that even Sleeper's own ecosystem has to patch with third-party tools.

---

## 6. ESPN — native league/waiver behavior

Source: espn.com/fantasy rules pages, support.espn.com (fetched via search summaries).

- Waiver period is **time-boxed and processes overnight** (Standard league waiver run window given as 3-5am ET) — free agency (post-waiver-period, unclaimed players) is instant/first-come-first-serve and explicitly does **not** affect waiver priority order, which is a distinct rule from the waiver-claim period itself.
- UI distinguishes **"Add" (free agent, executes immediately) vs. "Claim" (on waivers, executes at the next processing run)** with different button colors/labels — i.e. ESPN's own UI treats "can I get this player right now" vs. "I'm entering a queued claim" as two visibly different states, not one generic "add player" action.
- Same-day add+release of a player keeps them a free agent (anti-churn rule) — a specific edge-case ESPN's own rules page calls out explicitly.
- This is directly relevant to the new September 22 evidence about ESPN/Flaim transaction data: ESPN's own rules confirm **waiver-clear timestamps and acquisition-type (waiver vs. free-agent) are meaningful, well-defined concepts in ESPN's own rules model**, which is consistent with (but does not itself verify) the new evidence's claim that Flaim's `get_transactions` can expose exactly this distinction. This is corroborating context for a later formal re-audit, not proof the Flaim data is accurate.

**Functional takeaway**: the on-waivers vs. free-agent distinction, and the specific "waiver clears overnight, free agency is instant" rule, is exactly the kind of provider-specific rule NWR would need to model correctly if/when ESPN capabilities are trusted — this is a genuine complexity ESPN adds that Sleeper (rolling/reverse-standings/FAAB, no overnight-clear distinction) does not have in the same form.

---

## Cross-cutting functional themes observed across all 6 products

1. **Floor / median / ceiling, not just a point estimate** — Draft Sharks and RotoWire both build this in as a first-class, user-adjustable dimension (slider or safe/upside toggle), not an afterthought.
2. **Explicit weekly-vs-ROS-vs-streamer framing as separate user-selectable lenses**, not one blended number (Draft Sharks most explicit about this three-way split).
3. **Drop-replacement shown as a paired scenario** (add X + drop Y together), not add-ranking and drop-ranking done independently (FantasyPros Waiver Assistant explicit about this).
4. **FAAB guidance normalized as % of remaining budget** in at least one competitor (Footballguys), not just a raw dollar amount.
5. **Bye-week / strength-of-schedule look-ahead as an explicit, separately sortable dimension**, not just baked silently into a single projection number (Draft Sharks).
6. **Ownership/availability status layered directly onto the same ranking table** rather than a separate silo (Footballguys); cross-league availability lookup for one player (Draft Sharks).
7. **News/injury feed integrated into the same screen as the decision tool**, not a separate tab (RotoWire).
8. **Waiver-type-as-per-league-config** (rolling/reverse-standings/FAAB) is standard industry practice (Sleeper native).
9. **"Trending"/consensus-add-rate as a distinct signal** from pure projection-based ranking (RotoWire "most selected"; Sleeper ecosystem's third-party trend tools).
10. **Provider-specific waiver mechanics differ materially** (ESPN's overnight-clear + on-waivers-vs-free-agent state machine vs. Sleeper's simpler model) — any provider-neutral NWR layer needs to represent this as a real state machine, not assume Sleeper's simpler model generalizes.
11. **Multi-league one-screen views with per-league settings already resolved** are table stakes at the premium tier across FantasyPros/RotoWire/Footballguys.
12. All six products keep the **actual roster-add/drop transaction execution** as a host-side action (either the competitor's own one-click submit that calls the host API, or ESPN/Sleeper's own native UI) — none of them independently invent a parallel transaction ledger; they all treat "submit to host" as the terminal step.

See `LEDGER.md` in this same directory for the honest, code-evidence-backed comparison of each of these 12 themes against NWR's actual current implementation (Phase 0 findings) — several of these are already implemented well in NWR, and this file intentionally does not pre-judge that; the comparison lives in the ledger where it can cite exact files/tests.
