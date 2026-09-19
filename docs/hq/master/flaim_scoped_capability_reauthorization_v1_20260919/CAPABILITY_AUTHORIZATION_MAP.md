# Capability Authorization Map

`packet_id: flaim_scoped_capability_reauthorization_v1_20260919`

This is the operative table for this authorization. Every capability NWR
could plausibly source from a Flaim-mediated ESPN league is listed here, with
its exact July finding, its status under this authorization, and its binding
constraint. **A future worker implementing ESPN/Flaim data consumption in
NWR must check this table before adding a new use of Flaim-sourced data — a
capability not listed here is not authorized.**

| Capability | July finding it maps to | Status under this authorization | Binding constraint |
|---|---|---|---|
| Verified league identity (`league_id`, `league_name`, `season`, `team_count`, provider) | July "League connection" row: observed-connection-only, no prohibited use named against identity itself | **ALLOWED** | Must carry a retrieval timestamp (see Freshness row below); is not automatically treated as more authoritative than the profile's existing manually-entered identity fields until the owner has confirmed a real cross-check at least once |
| Owner/team roster-slot mapping (which roster/team belongs to the owner) | July "Ownership" row: identifier-consumable, "not independently verified against same-time native truth" | **ALLOWED**, carrying July's own caveat forward | Must state, wherever displayed, that ownership was not independently verified against same-time native ESPN truth — the exact caveat July itself required |
| Roster membership snapshot (players on a roster, with provider player IDs) | July "Rosters" row: internally coherent; permitted manual use = "Read-only roster membership snapshot" | **ALLOWED** | Must be presented as a **point observation at retrieval time**, never as guaranteed-current without a timestamp — this is July's own prohibited-use boundary ("current authoritative roster truth when freshness is absent"), complied with by always attaching `retrieved_at_utc` |
| Lineup/roster-slot eligibility (starter/bench/reserve, FLEX rules) | July "Settings" row: FLEX eligibility among the 5 `PARTIAL` / 2 `NOT_EXPOSED` results | **ALLOWED once individually verified against that specific league's real data** | Must carry a per-field completeness flag (`COMPLETE` / `PARTIAL` / `UNKNOWN`); if FLEX/eligibility rules are `PARTIAL` or `NOT_EXPOSED` for a given real league, that must be surfaced to the owner, never silently assumed exact |
| Scoring settings | July "Settings" row: 23 `EXACT`, 5 `PARTIAL`, 2 `NOT_EXPOSED`; required caveat "Retain field-level fidelity labels" | **ALLOWED**, same completeness-flag discipline this codebase already uses for Sleeper (`scoring_reconciliation` / `unsupported_scoring` in the existing Sleeper import receipt) | `hasScoringSettings` must be `COMPLETE` only when every scoring field maps with known confidence; otherwise `PARTIAL` or `UNKNOWN`, and the specific unmapped fields must be disclosed the same way the Sleeper receipt already discloses `unsupported_scoring` |
| Current standings | July "Standings" row: "materially misrepresented"; prohibited use: "Rank or playoff status" | **CONSTRAINED** — display-only if surfaced at all, never authoritative for any computed decision | Must never feed any ranking/decision/sort/filter logic; if shown to the owner at all, must carry an explicit "not verified against native ESPN standings — provenance: Flaim" caveat next to it, every time |
| Transaction direction / waiver claims / add-drop reconstruction | July "Transactions" + "Trades" rows: both "materially unsafe" / "unsafe"; prohibited uses: add/drop direction, transaction completeness, exact trade sides | **CONSTRAINED / NOT ENABLED** | Not built, not designed for build, in this pass or any pass without a separate, explicit reentry decision. This is doubly blocked: by July's own finding, and independently by this project's standing "no provider writes, no transaction-direction inference" rule, which is unrelated to and unaffected by this authorization |
| Available-player / free-agent pool | July "Free agents" row: "capped, alphabetic, noisy, incomplete"; prohibited use: "complete actionable free-agent pool" | **CONSTRAINED** | Must carry an explicit `hasAvailablePlayerPool` flag of `BOUNDED` (never `COMPLETE`) whenever Flaim-sourced, plus a human-readable statement of the actual bound observed (e.g., "first N alphabetically, not exhaustive — do not treat absence from this list as unavailability"); never used as if exhaustive anywhere in the product |
| Freshness / source-as-of | July "Freshness and provenance" row: "most records lacked adequate source-as-of or version fields" | **CONSTRAINED** | Every Flaim-sourced fact must show **retrieval time** (`retrieved_at_utc` — when NWR/Flaim actually fetched it) **distinct from** any provider-published as-of time (`provider_as_of_utc`, which may legitimately be `null`/unknown); when the provider as-of is unknown, the UI/data must say so explicitly rather than implying the data is currently live |
| Flaim's own analysis / rankings / trade opinions / a "disagreement panel" | Governed entirely by `EXTERNAL_SIGNAL_GOVERNANCE_BOUNDARY.md`, not addressed by the owner's authorization at all | **EXPLICITLY UNCHANGED — still `BLOCKED`, still 0% production influence** | This authorization concerns only raw factual data conduits (identity, roster, lineup, settings). It does not touch, expand, or reinterpret the July packet's separate, still fully-binding rule that plugin *output/judgment* (as opposed to raw provider facts relayed through the plugin) can never influence NWR's formulas, rankings, recommendations, sorting, filters, confidence, or source admission |

## Reentry-trigger mapping (formal cross-reference into the July gate, not an edit of it)

`PROVIDER_CHANGE_REENTRY_GATE.md` (July packet, unedited) lists eight
concrete Flaim reentry triggers; at least one must exist before the Flaim
path may reopen at all, "absent [which], do not rerun or recreate the
completed audit." This authorization is triggered by:

> "Written persistent-use, display, and retention permission."

— satisfied by the owner's own dated, written authorization quoted in full in
`OWNER_AUTHORIZATION_AND_JULY_FINDINGS_RECORD.md` section 2, for their own
private league data, for their own private NWR install. This is a
**rights-side** trigger (the owner, who holds the rights to their own league
data, is granting NWR persistent-use permission for that data) — distinct
from and not requiring any of the other seven **provider-side** triggers
(release notes, corrected filtering, explicit trade-side mapping, etc.),
none of which are claimed here and none of which are needed for this
specific trigger to apply.

Per the gate's own text, quoted directly: **"The trigger permits a narrow
test; it does not authorize production integration."** This authorization is
scoped to match exactly that limit:

1. Document the triggering change and its source — done, this packet.
2. Preregister only the corrected/authorized surface and minimum control
   cases — done, the capability table above is the preregistration; nothing
   outside it is authorized.
3. Recheck privacy, retention, display, and downstream-use rights — the
   owner's own authorization is itself that recheck, explicitly scoped to
   private/personal/read-only use; `SOURCE_USE_RIGHTS_AND_PRIVACY_BOUNDARY.md`'s
   finding of "no written permission" for the *original July test subject's*
   data is unaffected (that was a different, now-historical connection) —
   this authorization concerns the owner's own current real leagues, for
   which the owner is the actual rights holder.
4. Test semantic fidelity, completeness, freshness, provenance, and
   stability — explicitly deferred to when a real Flaim connection exists
   (pending OAuth, see `docs/codex/flaim_integration_20260919/LEDGER.md`);
   this packet authorizes the *scope*, it does not itself certify that a real
   ESPN snapshot, once fetched, will actually satisfy each capability's flag
   at `COMPLETE`/`ALLOWED` level — that determination happens per-league,
   per-fetch, via the capability-check architecture built this pass (see
   `docs/codex/flaim_integration_20260919/LEDGER.md` for what was built).
5. Keep production influence at 0% unless a separate numerical-signal and
   source-admission gate passes — unaffected; nothing in this authorization
   creates any numerical-signal admission. Flaim-sourced *facts* (a roster
   list, a scoring setting) are not "plugin output" in the sense
   `EXTERNAL_SIGNAL_GOVERNANCE_BOUNDARY.md` means (Flaim's own computed
   opinions) — they are raw provider data relayed through Flaim because no
   direct ESPN client exists, exactly analogous to how a Sleeper roster
   fetched via `SleeperHttpClient` is raw provider data, not "Sleeper's
   opinion." That distinction is the entire basis on which this
   authorization is coherent with the July packet rather than contradicting
   it, and it is why the "Flaim's own analysis" row above remains untouched.

## What remains for a future worker to actually determine (not settled by this packet)

This packet authorizes *scope*. It does not and cannot determine, in
advance of a real fetch, whether a specific real ESPN league's data (via
Flaim, once OAuth completes) actually satisfies each capability at the level
this table allows. That determination is exactly what the capability-check
architecture built this pass exists to compute, per real snapshot, honestly
— see `src/services/league_capability_service.py` and
`docs/codex/flaim_integration_20260919/LEDGER.md`.
