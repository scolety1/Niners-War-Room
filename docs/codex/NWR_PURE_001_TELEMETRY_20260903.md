# NWR PURE 001 — decision receipt schema and readiness (sections 16/24)

Design/schema pass, not wired into the live app this wave. Saturday's
actual owner-facing decisions should keep using the currently admitted
NWR decision authority (rankings/Suggestions as they exist today, now
respecting position-max legality per this wave's fix) — **not** any
SHADOW value from `shadow_numeric_authorities_service.py`, which is
explicitly not decision authority yet.

## Freeze manifest (required before Saturday, if NWR PURE 001 runs)

```json
{
  "app_sha": "<git rev-parse HEAD of the adopted candidate>",
  "model_sha": "<hash of generate_rankings' governing inputs -- projection_sha256 already exists on RankingResult, reuse it>",
  "player_universe_sha": "<sha256 of projections/<season>/current.csv, already computed at install time per current.manifest.json>",
  "league_config": "<LeagueProfile as JSON, verbatim>",
  "market_snapshot": "<AdpSnapshot.source + source_date + sample_size at freeze time>",
  "algorithm_version": "<MODEL_FAMILY / REDRAFT_AUTHORITY_LABEL constants already in redraft_engine_v1_service.py>"
}
```

Every field on the right already exists somewhere in this codebase
(`RankingResult.projection_sha256`, `current.manifest.json`'s
`source_sha256`, `LeagueProfile`, `AdpSnapshot`, and the existing
`REDRAFT_AUTHORITY_LABEL`/`MODEL_FAMILY` constants) — this is an
assembly task, not new provenance plumbing.

## Decision receipt (one per owner pick, immutable)

```python
@dataclass(frozen=True)
class DecisionReceipt:
    timestamp_utc: str
    pick_number: int
    available_universe_size: int          # len(_available_ranked(...))
    roster_before: list[str]               # player_ids
    nwr_recommendation: str                # playerId of the actual admitted-authority pick
    alternatives: list[str]                # the other Suggestions cards' playerIds, for context
    player_score: float | None             # replacement_adjusted_value of the recommended player
    team_score_shadow: float | None         # SHADOW, logged, never shown as decision advice
    championship_equity_shadow: float | None  # SHADOW, logged only
    pick_score_shadow: float | None          # SHADOW, logged only
    market_context: dict                    # ADP source/date/expected_pick for the recommended player
    owner_action: str                       # the actual player_id the owner selected
    udk_comparator: dict | None              # logged silently, never surfaced to the owner during NWR PURE
    fantasypros_comparator: dict | None      # logged silently, never surfaced
    build_versions: dict                    # the freeze manifest above, repeated per-receipt for self-containment
```

**Immutability**: append-only, same pattern as `state["picks"]` and this
wave's new `state["corrections"]`-adjacent `last_correction` log — no
retrospective rewriting, matching the rest of this session's evidence-
preservation practice.

**SHADOW fields are logged, never surfaced as advice**: `team_score_shadow`
/ `championship_equity_shadow` / `pick_score_shadow` populate from
`evaluate_pick_candidates()` run silently in the background against the
Suggestions candidate set at the moment of each real pick — this is
exactly the kind of "postmortem comparison data" NWR PURE 001 needs, and
it's available today because this wave shipped the SHADOW module. The
owner-facing NWR PURE view must not render these fields; only the
existing admitted rankings/Suggestions surface (with this wave's
position-max fix applied) should appear.

## What is genuinely ready

- Decision-authority Suggestions surface: ready (position-max legality
  fixed this wave).
- Rapid capture for entering real picks fast: ready, tested against all
  23 historical SEARCH_FAILURE fixtures.
- Surgical correction if an entry mistake happens live: ready, tested.
- K/DST and previously-missing skill players representable: ready (13/14
  and 5/5 respectively — see the reconciliation ledger).
- SHADOW metrics to log silently for postmortem: ready
  (`evaluate_pick_candidates`), but not yet wired into an automatic
  per-pick logging hook in `desktop_facade.py` — that wiring, plus a
  `DecisionReceipt` writer using the schema above, is the remaining
  integration work before a real NWR PURE 001 run.
- Freeze-manifest assembly: not yet automated into one function/command;
  every input exists, assembling them into the JSON shape above is
  unstarted.

## Verdict

Readiness for Saturday's *operational* draft flow (rapid capture,
correction, K/DST/missing-player coverage) is real and tested. Readiness
for a full **NWR PURE 001 experiment with decision-receipt logging** is
not — the schema and every underlying data source are ready, but the
integration wiring (auto-log a `DecisionReceipt` on every real pick,
assemble the freeze manifest once at draft start) has not been built.
Do not run NWR PURE 001 as a formal logged experiment until that wiring
exists; running the draft itself with this wave's operational fixes is
independently safe regardless.
