# NWR Live Player Intelligence Admission Contract V1 (PREREGISTERED)

Branch `upgrade/nwr-live-player-intelligence-v1-20260913`, worktree
`C:\NWR\live-player-intelligence-v1`, Start HEAD `4d46f107`. Written and
committed **before** any candidate source is measured in this work cycle
(Work Unit 0, ahead of Work Unit 1). These are the fixed admission gates a
live-player-availability source (or a specific field of one) must clear
before it is promoted out of shadow-only status into the real
`PlayerAvailabilityStatus` production authority
(`src/services/player_availability_status_service.py`) or any consumer of
it. They are written down now, precisely, so results measured afterward
cannot quietly reshape the bar. Nothing in this document is edited after
source measurement begins in Work Unit 1 or later; if a gate later proves
wrong or under/over-specified, that is recorded as a NEW dated finding in
a later doc, never a silent edit here.

This document does not itself admit, promote, or wire anything. It is the
yardstick a later, separate promotion pass measures candidates against.
Today's `PlayerAvailabilityStatus` authority (manual, individually-sourced
overrides only) and today's shadow ingestion
(`src/services/live_player_intelligence_shadow_v1_service.py`) are
untouched by this document.

---

## GATE 1 — Provenance

100% of surfaced production values carry: `source` (which admitted
provider produced the value), `source timestamp` (the provider's own
as-of/updated timestamp for that value, where the provider makes one
available), `fetched_at` (when NWR itself retrieved the value), and a
`freshness` figure derivable from the two timestamps above. A field with
no available source timestamp must say so explicitly (e.g. a null/absent
source-timestamp marker) rather than substituting `fetched_at` or any
other value in its place. Unknown stays unknown: a field NWR cannot
currently populate from any admitted source must render as absent/unknown,
never defaulted to a guessed, healthy, or otherwise assumed value. This
gate is evaluated per FIELD, not only per row — a row can be admitted for
one field and unknown for another.

## GATE 2 — Identity

Every production-admitted row resolves to exactly one canonical NWR
`player_id`, or is quarantined (excluded from production surfacing,
logged for review) rather than guessed. Acceptable resolution methods are
limited to those already proven elsewhere in this codebase at admission
time (e.g. direct id-scheme match such as `gsis_id`, or the existing
`_identity` name+position+team normalizer used by
`waiver_engine_service.resolve_roster_canonical_ids` and
`fantasypros_kdst_consensus_service.py`) — no new fuzzy-matching heuristic
may be invented solely to inflate a coverage number. Zero guessed joins:
an ambiguous or low-confidence match is quarantined, not admitted at
reduced confidence.

## GATE 3 — Official factual agreement

Zero contradictory hard OUT/active-state values may reach production —
i.e. NWR must never surface a value that flatly contradicts the official
NFL/team-published state for the same player at the same point in time
(one source saying OUT while the authoritative official record says
ACTIVE for the same game/week is a hard failure, not a rounding error).
Beyond that hard floor, normalized designation/practice records (e.g.
Out/Doubtful/Questionable, Full/Limited/DNP practice participation) must
achieve ≥99% exact agreement against official NFL reports on the held-out
test sample built by the official-NFL-truth-benchmark work (a separate,
later work unit). This gate cannot be evaluated until that benchmark
exists; it is preregistered here so the benchmark worker builds to a
known target rather than an after-the-fact one.

## GATE 4 — Coverage

≥95% of fantasy-relevant offensive players who actually appear on an
official injury report during the evaluation window are mapped/covered by
the admitted source(s) (i.e. NWR successfully resolves and surfaces a
status for them) during that same window. This is a coverage-of-the-
official-report-population gate, not a coverage-of-the-full-roster-pool
gate — a source is not penalized for having nothing to say about a
healthy player who was never on any injury report to begin with.

## GATE 5 — Freshness

Two independently evaluated freshness floors, because these are two
different real use cases with different tolerances — a source may clear
one and fail the other, and admission is field-specific, not all-or-
nothing:
- **Ordinary practice/designation context**: P95 latency ≤2 hours behind
  the official publication of that designation/practice-status change.
- **Game-day inactive authority** (the actual in/out-of-lineup
  determination on game day): P95 latency ≤10 minutes behind the
  authoritative inactive-list release.
A source failing the 10-minute game-day bar may still be admitted for the
2-hour ordinary-context use case, and vice versa is not possible (nothing
clears the tighter bar without also clearing the looser one) — but each
use case is gated on its own merits, not blended into one number.

## GATE 6 — Precedence

Verified manual overrides (`current_player_status_overrides_service.py`)
must never be silently overwritten by lower-precedence automated data, on
any field, under any freshness or agreement condition. This is
unconditional and does not get weaker as an automated source's measured
quality improves — a human-verified, individually-cited override always
wins on the field it sets.

## GATE 7 — Cross-league correctness

One player status event must correctly identify every real league
containing that player and no unrelated league, and must correctly
distinguish, per league: owner-starter, owner-bench, opponent-roster,
free-agent, and not-relevant-to-this-league. A status event leaking into
an unrelated league, or mis-classifying an owner's own roster slot,
is a hard failure of this gate regardless of the underlying data's factual
accuracy.

## GATE 8 — Performance

Warm cached status resolution adds ≤100ms at the median and ≤250ms at P95
to an owner-facing status-dependent read, measured against the same kind
of real, instrumented timing this repo already uses elsewhere (e.g. the
release-gate smoke script's per-surface timing). This is an ADDED-latency
budget on top of whatever that surface already costs today, not an
absolute ceiling on the surface's total time.

## GATE 9 — Rights

Production admission requires documented rights compatible with NWR's
actual usage pattern: local caching, redistribution to the owner's own
app UI, and (should it ever apply) commercial use, given NWR is a
personal desktop app today. If caching, redistribution, or commercial-use
rights are unresolved, undocumented, or require a sales conversation the
owner has not had, the source stays SHADOW regardless of measured
technical quality on Gates 1-5 and 7-8. A source can be "the best
technical fit" and still fail this gate outright; the two are evaluated
independently and Gate 9 is a hard blocker, not a weighted factor.

## GATE 10 — Recommendation regression

Existing decision/test suites stay green after any promotion. Recommend-
ations may change ONLY where a newly-admitted factual availability change
legitimately changes eligibility or context for that specific player (the
same effect `current_player_status_overrides_service.py`'s zero-value
kinds already produce today) — never as a side effect of an unrelated
scoring, ranking, or weighting change introduced alongside a promotion.

---

## Scope note for this specific work cycle (Worker 1, Work Unit 1)

This work cycle's Work Unit 1 only CHARACTERIZES candidate sources
(coverage, timestamp granularity, identity scheme, rights, historical
access, freshness, missingness, revision behavior) and stores raw research
artifacts outside production code. It does not measure Gates 3 or 4
against a real official-NFL benchmark (that benchmark does not exist yet
— it is the next work unit's job to build), does not measure Gate 5's
precise P95 latency against a live monitored window, does not measure
Gate 8 (no code is wired into any live read path), and does not perform
any promotion. Where this cycle's findings bear on a gate, they are
reported as directional evidence only, explicitly labeled as such, never
as a gate PASS.
