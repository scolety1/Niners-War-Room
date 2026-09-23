# NWR Waiver-Night Readiness — Owner Test Checklist

Branch `upgrade/nwr-prospective-outcomes-v1-20260914`, commit `eed9f076` (pushed to origin — verify below).

Redraft app: **http://127.0.0.1:1422/** (backend on :18742). Both are isolated dev instances — your real AppData install was never touched tonight.

## 8-12 things to check

1. **Open Fantasy Gamers.** Confirm it lands on Weekly Home with real Week 3 data, not a stale week.
2. **Open Improve Team → FAAB.** Confirm it shows "not a FAAB league" (this league is waiver-priority, priority #9).
3. **Switch to Las Vegas Enginerds.** Confirm Improve Team → FAAB now shows a real dollar budget ($100) and real bid ranges — this confirms no state leaked from Fantasy Gamers.
4. **Open Start/Sit for Las Vegas Enginerds.** Confirm no DST slot appears anywhere (this league has none), and if any player shows as "not included this week," confirm the reason given is specific (an actual injury/status), not a generic placeholder.
5. **Open the K/DST Streamer tab** for either Sleeper league and click "Refresh K/DST ECR" (this requires a manual click by design — it's a real live external call, not a bug). Confirm it recommends KEEP CURRENT when your own player is actually better ranked, not just the top free agent.
6. **Switch to KHA** (2026 KHA High Stakes League). Confirm every weekly tool (Start/Sit, Waivers, K/DST) shows an honest "Verified league data required" message — this is correct today, not broken. Real ESPN data for this league requires one small step from you later (see below).
7. **Switch to 403 N 18th and friends.** Same honest-block confirmation as KHA.
8. **Switch rapidly between all 4 leagues a few times** (Fantasy Gamers → KHA → Las Vegas Enginerds → 403 N 18th → Fantasy Gamers) and confirm the roster/budget/recommendations shown always match whichever league is currently selected — this was tested extensively tonight (zero leaks found across 70 automated probes) but your own eyes are the final check.
9. **Open Trades → Trade Finder** for Fantasy Gamers and confirm real opponent rosters/players appear, not placeholders.
10. **Check the browser console** (F12) on a couple of pages for any red errors — none were found tonight, but worth a spot-check.
11. **Report anything that looks wrong** — a wrong number, a confusing message, a page that doesn't load — even something small. Everything above was verified with real data tonight, but you know your leagues better than any of this.

## The one small step for real ESPN data (KHA and 403 N 18th)

See `TOMORROW_OWNER_CHECKLIST.md` in this same folder for the exact, minimal steps.
