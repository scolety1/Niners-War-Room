# Draft contracts

- `FreshnessStatus`: source, fetchedAt, maxAge, status, fallback, message.
- `EvidenceReceipt`: provider, scope, termsReceipt, hash, coverage, fetchedAt, freshness.
- `LeagueStateSnapshot`: league, scoring, managers, rosters, transactions, picks, receipt.
- `RosterSnapshot` / `AvailablePlayerPool`: identity, eligibility, roster state, source receipt.
- `RedraftRosValue` / `RedraftWeeklyValue`: player, scope, value band, confidence, evidence, warnings.
- `WaiverCandidate`, `DropCandidate`, `AddDropRecommendation`, `StreamerCandidate`, `LineupRecommendation`: legal constraints, marginal effect, confidence and fallback.
- `DynastyInSeasonSignal`, `DynastyValueMovement`, `DynastyStashCandidate`, `TradeWatchCandidate`: existing-authority reference, directional label, sample/role evidence, warning.

All are immutable, receipt-bearing read models; no universal in-season score is defined.
