# NWR Next-Draft Final Blocker Closure — Running Ledger

**Started:** 2026-09-08, HEAD `d00f51dd` (end of the prior "class-time autonomous hardening"
run, all 20 sections of that directive complete). This is a distinct, follow-up directive:
close remaining next-draft readiness gaps only. Do NOT retune marginal_roster_utility, reopen
age/rookie studies, rebuild K/DST models, change Pick Score formulas, redo FFA research, or
redesign the Draft Room. No push/merge/deploy.

## Section 1 — Projection snapshot freshness/bootstrap bug (DONE)

Full evidence: `docs/codex/NWR_NEXT_DRAFT_FRESHNESS_BLOCKER_V1_20260908.md`. Real root cause:
the row-level freshness gate (30-day window) is real, correctly-designed governance, not a
bug -- the real owner's live install has organically aged past it (verified directly,
read-only: all 608 real rows blocked; the one real draft-day authorization self-expired at
2026-09-08T10:00:00Z, exactly as designed). Fixed the diagnostic (not the gate): a new
`_draft_day_authorization_status()` plus an upgraded top-level error message make the real
cause and real required action explicit, traced end-to-end through to the real
`redraft_bootstrap()` owner-facing status. 7 new tests (dynamically-dated, all directive-named
scenarios). No governance semantics changed. Real owner data read-only (isolated copy for the
facade trace); verified untouched via final hash check.

## Section 2 — Full owner runtime acceptance after freshness fix

(next)
