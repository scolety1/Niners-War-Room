# Phase 2A — Sleeper substrate

Read-only pipeline: league ID → settings/scoring/slots → users/managers → rosters/starters/bench/IR/taxi → transactions → traded picks/draft state → rostered index → unrostered pool → freshness receipt.

Contracts: LeagueStateSnapshot, LeagueRosterSnapshot, TeamRosterSnapshot, ManagerSnapshot, RosteredPlayerIndex, AvailablePlayerPool, TransactionLedger, TradedPickLedger, LeagueFreshnessReceipt, SourceFailureState. Cache immutable timestamped snapshots; refresh explicitly; stale data remains visible with no recommendation escalation. No Sleeper writes or raw owner data outside the local state boundary.
