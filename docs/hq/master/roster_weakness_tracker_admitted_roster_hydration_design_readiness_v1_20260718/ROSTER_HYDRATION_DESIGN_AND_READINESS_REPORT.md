# Roster Hydration Design and Readiness Report

Date: 2026-07-18
Lane: design, evidence, and readiness only
Verdict: BLOCKED_ROSTER_HYDRATION_STABLE_IDENTITY_NOT_AVAILABLE

## Executive conclusion

The repository has an explicitly admitted roster source. The source registry classifies Sleeper players, rosters, and drafts/traded picks as ADMITTED_FACT, permits roster joins and league-state use, and does not classify them as display-only. The repository also has a visible Roster Weakness Tracker route and a canonical league-rules document.

Hydration implementation is not ready. A clean checkout has no current roster snapshot or LocalData pack; the tracked synthetic player fixture has no populated Sleeper IDs; the current roster schema does not carry roster snapshot identity, starter/bench, taxi, IR, resolution, retention, or integrity fields; and existing identity code contains name-based fallback paths that this design prohibits. The repository therefore cannot prove a stable exact join for every supported roster asset.

No provider was called, no private or LocalData content was read or copied, and no application, data, source, ranking, formula, refresh, or trust behavior was changed.

## Verified control point

- Canonical remote branch: work/hq-parallel-control
- Verified commit: adc058512b389657830e86ad1abd4b85bebd7eea
- Verified tree: 00f6e7035fd81ad9341dd5605eb251ae375b785a
- Expected commit/tree comparison: exact match
- Intervening commits: zero
- Stop-scope conflicts: none
- Isolated branch: work/roster-hydration-readiness-design-v1-20260718
- Isolated worktree: C:\NWR\Niners-War-Room-roster-hydration-readiness-design-v1-20260718

## Current product meaning

Repository authority permits a descriptive checklist and display-only roster structure:

- roster composition and positional counts;
- simple position coverage;
- age buckets when age is supplied;
- dynasty-rank buckets when rank is supplied;
- visible missing information and manual notes.

Repository authority does not authorize:

- a weakness score;
- add/drop, start/sit, waiver, trade, or draft advice;
- a hidden sort or target ranking;
- replacement-level gaps;
- automated contender/rebuilder classification;
- a recommendation derived from rank, value, market, injury, or schedule context.

The existing page is PRESENTATION_ONLY. It accepts manual rows, persists local lab notes outside the repository, and renders descriptive summaries. Its starter thresholds are hard-coded and omit flex and kicker requirements, so they are not a truthful hydration contract.

## Authority findings

### Admitted source

GREEN for source admission, bounded to local factual league state.

The controlling evidence is config/source_registry.csv:

- sleeper/players: ADMITTED_FACT; identity, player IDs, roster joins;
- sleeper/rosters: ADMITTED_FACT; league rosters, roster state, ownership;
- sleeper/drafts_and_traded_picks: ADMITTED_FACT; pick ownership, league settings, draft state.

The old scheduled-puller and normalizer artifacts remain SOURCE_GATED as raw or candidate snapshots. A source class being admitted does not promote any particular raw snapshot, candidate package, or missing LocalData folder.

### Identity

BLOCKED.

The data contract names player_id as the canonical NWR player key and dim_players.csv provides sleeper_id as a possible exact source crosswalk. That shape is usable only when both identifiers are nonblank, unique, and complete for the roster snapshot.

The tracked synthetic fixture proves internal uniqueness for 24 rows but contains zero nonblank sleeper_id values. The current clean checkout therefore cannot test the source-to-canonical join. Existing identity-audit code may fall back to normalized names or name/position/team; those paths are explicitly forbidden for hydration.

No stable, fully evidenced NWR identity is available for all possible K, DST, inactive/retired, unresolved, or draft-pick assets. Draft picks have source-native season/round/original-roster coordinates but the tracker specification does not yet declare whether they are part of hydrated V1, and the canonical data-pack schema has no stable asset identifier.

### Roster fields

BLOCKED for production hydration; contract designed for re-entry.

The current fact_rosters.csv shape supports snapshot date, season, league/team/player context, position, roster status, rank, and source. It omits:

- a unique roster snapshot ID and schema version;
- a source namespace and source asset ID distinct from NWR identity;
- team ownership truth as a typed indicator;
- starter/bench, flex eligibility, taxi, and IR states;
- source-as-of versus hydration timestamps;
- validation and identity-resolution states;
- retained-data and last-known-good references;
- integrity metadata.

The required future fields and fail-closed behavior are in ROSTER_FIELD_CONTRACT.csv.

### League and lineup context

YELLOW with a bounded migration caveat.

docs/model_v4/LEAGUE_RULES_LOCK.md is explicit canonical repository authority for a 10-team dynasty/keeper hybrid, 1 QB, 2 RB, 3 WR, 1 TE, 2 WR/RB/TE flex, 1 K, 14 bench, two regular-season IR slots, no PPR, no TE premium, and no DST beginning in 2024. It also governs roster limits and the declaration workflow.

The runtime YAML does not encode the full lineup, flex eligibility, bench, scoring, or DST treatment, and the tracker service hard-codes only QB/RB/WR/TE thresholds. No implementation may use that partial constant as league truth. A future typed configuration must migrate the canonical document with provenance and tests before starter/flex coverage is enabled.

### Snapshot and freshness

YELLOW for design reuse; no roster receipt exists.

The current refresh-receipt service correctly separates latest attempt, latest successful receipt, retained data, stale retained data, last-known-good, source unavailable, source gated, partial success, and not enough information. Roster hydration should use a bounded result row in the existing receipt family if the closed field set can identify the roster dataset without private identifiers. Otherwise, a separately approved roster receipt family must reuse the same lifecycle semantics.

No failed attempt may replace a validated current or stale retained snapshot. Last-known-good matching requires the same admitted source, approved opaque league reference, roster/team identity, and compatible schema version.

### Privacy and LocalData

YELLOW for the designed boundary; BLOCKED for current availability.

Private league, roster, account, user, transaction, and waiver data belongs only under an approved ignored local root. Tokens, credentials, cookies, headers, provider payloads, private messages, and arbitrary source metadata are prohibited from snapshots and receipts. The tracked LocalData manifest requires allowedRoot local_exports, noCopy true, noCheckIn true, and arbitraryDiskFallback false.

The approved LocalData pack is absent in this clean worktree. That absence is not a failure of source admission, but it blocks production identity completeness, current roster verification, and end-to-end hydration tests.

### Weakness calculation

Only descriptive facts are authorized:

- admitted roster asset counts;
- exact position counts;
- unresolved-identity and missing-field counts;
- exact slot/status counts when governed fields are available;
- descriptive age distribution when age authority and coverage are disclosed;
- read-only canonical rank/value distribution with its existing trust status.

Starter, flex, age/lifecycle, availability, concentration, replacement-gap, rank/value-gap, and draft-capital weakness indicators remain blocked or review-only as recorded in WEAKNESS_CALCULATION_AUTHORITY_MATRIX.csv.

## Supported and unresolved assets

Conditionally support in the first future source adapter only:

- NFL player assets, including rookies, veterans, inactive/retired players, and kickers, when the Sleeper source ID maps exactly and uniquely to one NWR player_id;
- taxi and IR status attached to those exact player identities, only when captured explicitly by an admitted snapshot.

Unresolved and not silently omitted:

- DST assets, because no complete canonical NWR mapping is proved and canonical league authority says DST is no longer applicable;
- draft picks, because product inclusion and stable canonical asset identity are not settled for the tracker;
- any roster entry missing, duplicating, or conflicting on an exact admitted identifier;
- any opaque provider object that is not a declared supported asset type.

## Readiness decision

Mandatory BLOCKED gates:

- stable identity;
- roster field completeness;
- LocalData availability;
- clean-worktree reproducibility.

Mandatory YELLOW gates:

- product scope for draft assets;
- machine-readable league/lineup configuration;
- roster-specific freshness receipt;
- private-data lifecycle;
- descriptive calculation boundaries;
- end-to-end testability.

GREEN gates:

- source admission;
- presentation/trust vocabulary reuse;
- rollback design;
- protected-path compatibility.

No average or score is used.

## Implementation authorization

No roster hydration implementation is authorized.

After all re-entry evidence is accepted, the first implementation lane may be a typed, read-only roster snapshot and exact-identity validation contract using synthetic fixtures only. It must not call a provider, hydrate production data, wire the page, compute weakness, change rankings, or write outside an approved ignored test root.

See FIRST_IMPLEMENTATION_SLICE_CONTRACT.md and REENTRY_EVIDENCE_REQUIREMENTS.md.
