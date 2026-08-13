# Post-fix trade and market results

Replayed through `DesktopBackendFacade` with an explicit disposable workspace on 2026-08-13.

| Scenario | Before | After | Preferred side after | Visible evidence units after |
| --- | --- | --- | --- | --- |
| Puka Nacua for Gabe Davis + 2028 2nd | LEAN_REJECT | REJECT | Current side | 5 to 1 |
| Original Burden/Bell/2027 1st package | COUNTER | COUNTER | Current side | 13 to 4; opposing clear evidence preserves counter |
| Replace Kittle with Puka on incoming side | COUNTER / current side | COUNTER / incoming side | Incoming side | 10 to 9; substantial opposing clear evidence preserves counter |

The premium substitution now changes the preferred side even though the cross-authority recommendation correctly remains `COUNTER`. The lopsided premium-for-depth case crosses the declared decisive threshold.

All owner surfaces used the same composed snapshot. Market receipt: source as of `2026-07-17`, status `Yellow Stale`, message `Market evidence is 27 days old ... display-only context remains available but is not current.`
