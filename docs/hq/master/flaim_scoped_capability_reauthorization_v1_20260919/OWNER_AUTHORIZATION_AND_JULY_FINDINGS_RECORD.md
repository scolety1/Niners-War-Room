# Owner Authorization and July Findings Record

`packet_id: flaim_scoped_capability_reauthorization_v1_20260919`

This packet does **not** replace, edit, delete, or supersede
`docs/hq/master/fantasy_plugin_research_canonicalization_closeout_v1_20260711/`
(the "July packet"). That packet is preserved exactly as written, unedited, in
this pass. This is a new, additional, narrowly-scoped decision record that
sits alongside it and is cross-referenced from it (in this direction only —
see the note at the end of this file on why the July files themselves were
not touched).

## 1. Why this packet exists

The July packet closed with a deliberate, still-standing verdict: Flaim's
production adapter path is `BLOCKED`, manual human consultation is
`PERMITTED_WITH_CAVEATS_AND_TERMS`, and reentry requires one of eight named
triggers (`PROVIDER_CHANGE_REENTRY_GATE.md`). On 2026-09-19, during this
Flaim-integration cycle, the owner gave this session (via the dispatching
brief for this worker) an explicit, dated, scoped authorization to revise
that blanket restriction — not by rerunning or discrediting the July audit,
but by narrowing what it blocks. This packet records that authorization
precisely, preserves the July findings it is responding to, and defines
exactly what is now allowed, what remains blocked, and why.

## 2. The owner's authorization — verbatim, as relayed to this worker

> "I authorize revising the July project-owned blanket adapter restriction to
> allow a private, personal, read-only integration whose capabilities are
> individually validated... The July audit identified legitimate concerns
> involving standings, transaction direction, incomplete available-player
> lists, and freshness. Those concerns should constrain the affected
> capabilities. They should not automatically prevent verified league
> identity, roster, or lineup information from being useful."

**Date of authorization:** 2026-09-19 (Flaim integration cycle, Worker 1).
**Authorized by:** the project owner, relayed through the coordinating
session's dispatch brief to this worker — this worker did not itself
interact with the owner directly; it is recording what it was told,
verbatim, as the governance record demands.

**Scope of the authorization, as stated by the owner and preserved exactly:**

- **Private, personal, read-only use.** Not a production feature for other
  users. Not a write path of any kind.
- **Capabilities individually validated, not blanket-approved or
  blanket-blocked.** Each capability is judged on its own merits against the
  July findings (section 3 below), not lumped in with the capabilities July
  found genuinely unsafe.
- **Does not override provider terms, authentication requirements, or actual
  permission controls.** Nothing in this authorization grants NWR, Flaim, or
  this session any access, credential, or right it does not otherwise
  legitimately have. It is a statement of the *owner's own* policy toward
  *their own* codebase's treatment of *their own* private league data, not a
  claim about ESPN's, Sleeper's, or Flaim's terms of service.

## 3. The July findings this authorization is responding to — preserved accurately, not paraphrased from memory

Read directly from the July packet this pass (not reconstructed from
summary), quoting/restating its own words:

- **Overall verdict:**
  `YELLOW_PLUGIN_RESEARCH_USEFUL_WITH_SCORING_AND_GOVERNANCE_CAVEATS`
  (`SANITIZED_EXECUTIVE_VERDICT.md`).
- **Flaim classification:** `USEFUL_MANUALLY_NOT_READY_FOR_ADAPTER`. "One
  2026 Sleeper league connected successfully." Settings review: 23 `EXACT`,
  5 `PARTIAL`, 2 `NOT_EXPOSED`. "Core scoring and starting-slot values were
  mostly explicit, while FLEX eligibility, full keeper/dynasty semantics,
  full playoff structure, and current phase-specific roster limits were
  incomplete or absent." Ten roster calls were "internally coherent," with
  "stable provider player identifiers," and "ownership was
  identifier-consumable," but explicitly "not independently verified against
  same-time native truth."
- **The four concerns the owner's authorization explicitly names, quoted
  from `PLUGIN_CAPABILITY_SUMMARY.csv`:**
  - **Standings:** "Standings were materially misrepresented" — canonical
    reliability `Unsafe`; prohibited authoritative use: "Rank or playoff
    status."
  - **Transaction direction:** "Add/drop normalization was materially
    unsafe" (Transactions row) and "Exact trade-side reconstruction was
    unsafe" (Trades row) — canonical reliability `Unsafe` for both;
    prohibited authoritative use: "Add/drop direction or transaction
    completeness" and "Exact trade sides."
  - **Incomplete available-player lists:** "Free-agent retrieval was capped,
    alphabetic, noisy, incomplete, and unsuitable as a complete pool"
    (`SANITIZED_EXECUTIVE_VERDICT.md`); `PLUGIN_CAPABILITY_SUMMARY.csv`:
    "Results were capped alphabetic noisy and incomplete" — canonical
    reliability `Not complete`; prohibited authoritative use: "Complete
    actionable free-agent pool."
  - **Freshness:** "Most records lacked adequate provider as-of or version
    fields" — canonical reliability `Insufficient`; required caveat: "State
    when source-as-of and version are unavailable."
- **What July's own findings do *not* flag as unsafe** — this is the basis
  for the owner's "should not automatically prevent... identity, roster, or
  lineup" clause, verified directly against the July capability table rather
  than assumed:
  - **League connection / identity:** July's own permitted manual use for
    this row is "Explicit read-only settings consultation," with no
    prohibited-use entry naming identity itself as unsafe. The only caveat
    is "Connection does not validate every returned semantic" — a
    reason to individually validate other capabilities, not a reason to
    block identity.
  - **Rosters:** July's own permitted manual use is explicitly "Read-only
    roster membership snapshot." The prohibited use is narrower than "never
    use roster data" — it is "Current authoritative roster truth when
    freshness is absent," i.e., don't claim it's live-current without a
    timestamp. This authorization's roster capability (section 4 below)
    complies with that exact caveat by requiring a retrieval timestamp.
  - **Settings (which lineup/FLEX eligibility falls under):** July found
    this *mixed*, not uniformly unsafe (23 EXACT / 5 PARTIAL / 2
    NOT_EXPOSED) — its own required caveat is "Retain field-level fidelity
    labels," not "never use." This authorization complies by requiring an
    explicit per-field completeness flag (section 4).
- **What remains completely untouched by this authorization:** the July
  packet's `EXTERNAL_SIGNAL_GOVERNANCE_BOUNDARY.md` — "NWR's base score
  remains controlling and separately reproducible. Plugin output has `0%`
  production influence and must not affect formulas, rankings,
  recommendations, sorting, filters, confidence, source admission, or
  persisted product state" — governs Flaim's/FantasyBot's own *computed
  judgments* (rankings, trade opinions, a disagreement panel). This
  authorization is about **raw factual data conduits only** (an ESPN league's
  own identity/roster/lineup/settings facts, fetched via Flaim because no
  direct ESPN client exists), never about admitting Flaim's own analysis as
  a signal. That boundary is completely unchanged by this packet — see
  `CAPABILITY_AUTHORIZATION_MAP.md` section "Explicitly unchanged."

## 4. What this authorization is and is not, precisely

- It is **not** a rerun or invalidation of the July audit. July's findings
  are accepted as accurate and are the direct basis for what remains
  constrained (section 3, and the constrained rows in
  `CAPABILITY_AUTHORIZATION_MAP.md`).
- It is **not** a blanket "Flaim is now approved" decision. It authorizes
  specific capabilities, each mapped to a specific July finding, for a
  specific narrow use (private, personal, read-only, by the owner, for the
  owner's own real leagues).
- It **does** satisfy, honestly, one of the eight reentry triggers already
  named in the July packet's own `PROVIDER_CHANGE_REENTRY_GATE.md`: "Written
  persistent-use, display, and retention permission." The owner's dated
  authorization above is exactly that — a written grant, from the rights
  holder for their own private league data, for persistent storage/use of a
  narrow subset of that data inside their own private NWR install. See
  `CAPABILITY_AUTHORIZATION_MAP.md` for the explicit trigger mapping and what
  the gate's own text says that trigger does and does not permit (it "permits
  a narrow test; it does not authorize production integration" — this
  authorization is scoped to match that limit, not exceed it).
- It does **not** grant this session, or any future session, Flaim account
  access, ESPN credentials, or any bypass of Flaim's or ESPN's own
  authentication. Actually fetching real data still requires the owner's own
  completed OAuth login to Flaim's MCP endpoint (pending as of this packet's
  creation — see `docs/codex/flaim_integration_20260919/LEDGER.md`).

## 5. Why the July packet's own files were not edited

The task instruction for this pass was explicit: "do not delete or silently
edit the July one — preserve its history." Beyond that instruction, editing
`PROVIDER_CHANGE_REENTRY_GATE.md` or any other July file to insert a
cross-reference would itself be a silent edit to a closed, dated governance
record — exactly the kind of drift `SOURCE_USE_RIGHTS_AND_PRIVACY_BOUNDARY.md`
guards against ("Nothing in this packet admits either plugin as a production
source or changes NWR source governance" — the July packet's own governance
result stands exactly as recorded). This new packet is the cross-reference,
pointing *into* July; nothing points *out of* July into this packet. A future
worker or the owner may choose to add a one-line pointer to the July `README`
equivalent (it has none — the packet has no top-level index file other than
`MANIFEST.json`, which is itself hash-verified and would need regeneration to
edit safely) — deliberately left for a separate, explicit decision rather than
done implicitly here.
