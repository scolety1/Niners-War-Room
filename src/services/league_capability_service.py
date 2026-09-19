"""League data-capability model (Flaim-integration cycle, 2026-09-19).

Replaces provider-specific assumptions (e.g. ``profile.provider ==
"sleeper"``) with capability checks that reflect what a league profile's
underlying data snapshot GENUINELY has, regardless of which provider it
came from. This is the pure, testable core of that replacement -- it is
not yet wired into any live guard (`desktop_facade.py`'s existing
Sleeper-receipt 409s, or the frontend's ``isSleeper``/``provider ===
"sleeper"`` checks) by this pass. See
``docs/codex/flaim_integration_20260919/LEDGER.md`` for exactly what was
and was not wired, and why.

Nothing in this module calls Flaim, ESPN, or Sleeper, and nothing in it
performs any I/O. It is a pure dispatcher: given whatever real receipt or
snapshot data a profile actually has (a Sleeper import receipt today, an
ESPN/Flaim snapshot once one exists -- see
``espn_flaim_snapshot_service.py``), it computes an honest
``LeagueCapabilities`` record. It never fabricates a capability that
isn't backed by real data in the receipt/snapshot passed in, and it never
assumes a capability is present or absent just because a provider string
says "sleeper" or "espn".

Authorization for what NWR is allowed to DO once a capability is True/
non-NONE is a separate, already-recorded policy decision -- see
``docs/hq/master/flaim_scoped_capability_reauthorization_v1_20260919/
CAPABILITY_AUTHORIZATION_MAP.md``. This module only computes what IS
true about a given snapshot; it does not itself enforce usage policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Mapping, Sequence

if TYPE_CHECKING:
    from src.services.espn_flaim_snapshot_service import EspnFlaimSnapshot

ScoringCompleteness = Literal["COMPLETE", "PARTIAL", "UNKNOWN"]
PlayerPoolCoverage = Literal["COMPLETE", "BOUNDED", "NONE"]
StandingsAvailability = Literal["DISCLOSED_NON_AUTHORITATIVE", "NONE"]
# Transaction direction (add/drop, trade-side reconstruction) is
# constrained both by the July 2026 Flaim audit's own findings (standings/
# transaction-direction/trade-side reconstruction were each found
# "materially unsafe") and by this project's separate, standing "no
# provider writes" rule. Nothing in this module ever computes anything
# other than NOT_ENABLED for this field; it exists as an explicit,
# documented constraint rather than being silently omitted.
TransactionCapability = Literal["NOT_ENABLED"]


@dataclass(frozen=True)
class LeagueCapabilities:
    """What a specific league profile snapshot genuinely has data for.

    Every field here must be backed by an actual field's presence in the
    receipt/snapshot passed to the function that produced this record --
    never inferred from ``profile.provider`` alone. See
    ``docs/hq/master/flaim_scoped_capability_reauthorization_v1_20260919/
    CAPABILITY_AUTHORIZATION_MAP.md`` for what each field is authorized to
    be used for once True/non-NONE/non-UNKNOWN.
    """

    has_verified_identity: bool
    has_roster_data: bool
    has_lineup_eligibility: bool
    has_scoring_settings: ScoringCompleteness
    has_available_player_pool: PlayerPoolCoverage
    has_standings: StandingsAvailability
    transaction_direction: TransactionCapability
    # When this snapshot/receipt was actually fetched -- distinct from any
    # provider-published as-of time. Required to be honest: None means
    # "we don't know", never fabricated as "now".
    retrieved_at_utc: str | None
    # The provider's own published as-of time, if the source exposed one.
    # The July 2026 audit's own finding was that most Flaim records lacked
    # this field -- so it is explicitly optional and must never be
    # fabricated from retrieved_at_utc.
    provider_as_of_utc: str | None
    # Human-readable notes explaining any non-COMPLETE/non-NONE flag above
    # (e.g. "FLEX eligibility not exposed by provider", "free-agent pool
    # capped at 200, alphabetic, not exhaustive"). Always populated
    # alongside any constrained flag.
    disclosures: tuple[str, ...] = ()


NO_CAPABILITIES = LeagueCapabilities(
    has_verified_identity=False,
    has_roster_data=False,
    has_lineup_eligibility=False,
    has_scoring_settings="UNKNOWN",
    has_available_player_pool="NONE",
    has_standings="NONE",
    transaction_direction="NOT_ENABLED",
    retrieved_at_utc=None,
    provider_as_of_utc=None,
    disclosures=(),
)


def capabilities_from_sleeper_receipt(receipt: Mapping[str, object]) -> LeagueCapabilities:
    """Compute capabilities from an existing Sleeper import receipt.

    Mirrors the real receipt shape this codebase already writes for every
    Sleeper-imported profile (see
    ``local_exports/redraft_v1/sleeper_imports/<profile_id>.json``):
    top-level ``league``, ``owner``, ``roster_snapshot``,
    ``roster_positions``, ``scoring_reconciliation``,
    ``unsupported_scoring``.

    Note: a live Sleeper league's *available player pool* is fetched
    live, per-request, by the weekly tools (``desktop_facade.py``'s
    direct Sleeper calls) rather than persisted in this receipt file --
    so this function correctly reports ``NONE`` for
    ``has_available_player_pool`` even though live Sleeper leagues can, in
    practice, see available players through a separate live-fetch path
    this function does not model. A future caller that already knows a
    live fetch succeeded should not treat this function's NONE as "no
    players are available" -- only as "this receipt file specifically
    doesn't carry that data".
    """

    league = receipt.get("league")
    league = league if isinstance(league, Mapping) else None
    roster_snapshot = receipt.get("roster_snapshot")
    roster_snapshot = roster_snapshot if isinstance(roster_snapshot, Mapping) else None
    roster_positions = receipt.get("roster_positions")

    has_identity = bool(league and league.get("league_id") and league.get("name"))

    roster_players = roster_snapshot.get("players") if roster_snapshot else None
    has_roster = bool(isinstance(roster_players, Sequence) and len(roster_players) > 0)

    has_lineup = has_roster and bool(
        isinstance(roster_positions, Sequence) and len(roster_positions) > 0
    )

    unsupported = receipt.get("unsupported_scoring")
    disclosures: tuple[str, ...] = ()
    if isinstance(unsupported, Sequence) and len(unsupported) > 0:
        scoring: ScoringCompleteness = "PARTIAL"
        disclosures = (
            f"{len(unsupported)} scoring setting(s) not mapped to an NWR "
            "equivalent (unsupported_scoring).",
        )
    elif receipt.get("scoring_reconciliation") is not None:
        scoring = "COMPLETE"
    else:
        scoring = "UNKNOWN"

    retrieved_at = roster_snapshot.get("synced_at_utc") if roster_snapshot else None

    return LeagueCapabilities(
        has_verified_identity=has_identity,
        has_roster_data=has_roster,
        has_lineup_eligibility=has_lineup,
        has_scoring_settings=scoring,
        has_available_player_pool="NONE",
        has_standings="NONE",
        transaction_direction="NOT_ENABLED",
        retrieved_at_utc=str(retrieved_at) if retrieved_at else None,
        provider_as_of_utc=None,
        disclosures=disclosures,
    )


def capabilities_from_espn_flaim_snapshot(snapshot: "EspnFlaimSnapshot") -> LeagueCapabilities:
    """Compute capabilities from a real, parsed ESPN/Flaim snapshot.

    See ``espn_flaim_snapshot_service.py`` for the snapshot schema and
    loader. Standings are always reported ``NONE`` here because the
    snapshot schema itself deliberately does not carry a standings field
    at all -- the July 2026 audit found Flaim's standings "materially
    misrepresented", so this capability model does not merely constrain
    display of standings, it does not model them as present yet.
    """

    disclosures: list[str] = []
    if snapshot.scoring_completeness != "COMPLETE":
        disclosures.append(
            f"Scoring settings completeness: {snapshot.scoring_completeness} "
            f"({len(snapshot.scoring_settings)} field(s) captured)."
        )
    if (
        snapshot.available_player_pool_coverage != "NONE"
        and snapshot.available_player_pool_bound_description
    ):
        disclosures.append(snapshot.available_player_pool_bound_description)

    has_roster = len(snapshot.roster) > 0
    has_lineup = has_roster and len({p.slot for p in snapshot.roster}) > 0

    return LeagueCapabilities(
        has_verified_identity=bool(snapshot.provider_league_id and snapshot.league_name),
        has_roster_data=has_roster,
        has_lineup_eligibility=has_lineup,
        has_scoring_settings=snapshot.scoring_completeness,
        has_available_player_pool=snapshot.available_player_pool_coverage,
        has_standings="NONE",
        transaction_direction="NOT_ENABLED",
        retrieved_at_utc=snapshot.retrieved_at_utc,
        provider_as_of_utc=snapshot.provider_as_of_utc,
        disclosures=tuple(disclosures),
    )


def capabilities_for_profile(
    *,
    sleeper_receipt: Mapping[str, object] | None = None,
    espn_snapshot: "EspnFlaimSnapshot | None" = None,
) -> LeagueCapabilities:
    """The provider-agnostic entry point future call sites should use.

    Replaces patterns like ``profile.provider == "sleeper"`` with a real
    check of what data is actually present. Pass whichever real receipt/
    snapshot the profile actually has on disk. If a profile somehow has
    both (not expected in practice today), the Sleeper receipt is treated
    as authoritative for the fields it covers, since it reflects a live,
    already-working connection rather than a manually-authorized
    Flaim-mediated one.

    Returns ``NO_CAPABILITIES`` (everything False/NONE/UNKNOWN, never a
    guess) when neither is available -- the correct, honest answer for a
    profile with no provider-import receipt of any kind.
    """

    if sleeper_receipt is not None:
        return capabilities_from_sleeper_receipt(sleeper_receipt)
    if espn_snapshot is not None:
        return capabilities_from_espn_flaim_snapshot(espn_snapshot)
    return NO_CAPABILITIES
