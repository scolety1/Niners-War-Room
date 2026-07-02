# Watchlist Policy

Watchlist rows are review labels only.

Required watchlist categories:

- `EXPLAINABLE_NOT_BLOCKING`: case remains visible but does not block the next static review artifact.
- `WATCHLIST_NOT_BLOCKING`: case remains visible and should be checked by Tim before any later shadow implementation.
- `BLOCKER`: case would stop further review if it shows a production-promotion or leakage risk.

Pollard/Lamb policy:

- `T.Pollard`: `EXPLAINABLE_NOT_BLOCKING`
- `C.Lamb`: `WATCHLIST_NOT_BLOCKING`

No watchlist label is a recommendation, rank, hidden sort, or production decision.
