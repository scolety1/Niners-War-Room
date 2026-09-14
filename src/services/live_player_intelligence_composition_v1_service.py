"""Live Player Intelligence field-level source composition/precedence
(Worker 4, Work Unit 6, branch `upgrade/nwr-live-player-intelligence-v1-
20260913`).

Pure, network-free, no production wiring: nothing here is imported by
`src/application/desktop_facade.py`, `src/desktop_api/server.py`,
`player_availability_status_service.py`, or any recommendation/scoring
module -- this is still SHADOW infrastructure per the directive ("This is
still SHADOW infrastructure -- do not wire it into any live recommendation
path yet"). It composes a per-player, per-FIELD status record from multiple
real sources, following the admission contract's Gate 6 precedence and a
real freshness-monotonicity guarantee, but produces a value nothing
downstream currently reads.

--- Precedence (generalized from the directive's four-tier description) ---

The directive states: "manual verified override > admitted automated
factual source > supplementary Sleeper state > unknown." This module
generalizes tier 3 to "supplementary SHADOW source" rather than literally
"Sleeper" only, because Worker 3's real evidence
(`SOURCE_QUALITY_EVALUATION_V1.md`) shows nflverse's injury/practice/depth-
chart fields are ALSO only SHADOW-standing this cycle, not admitted --
there is no principled reason nflverse's shadow signal should outrank
Sleeper's shadow signal at the tier level (both are equally non-
authoritative right now); the REAL differentiation between them is
per-field source preference within that same tier (see
`PREFERRED_SOURCE_BY_FIELD` below, which reuses the same field->source
preferences `live_player_intelligence_shadow_v1_service.precedence_design()`
already documented as a design proposal -- this module is that proposal's
first real implementation, still never wired to any consumer).

  1. `PRECEDENCE_MANUAL_VERIFIED_OVERRIDE` -- always wins, unconditionally,
     on every field it actually sets (Gate 6: "must never be silently
     overwritten by lower-precedence automated data, on any field, under
     any freshness or agreement condition"). Fields the manual override
     wrapper leaves `None` do NOT block a lower-precedence source from
     filling them.
  2. `PRECEDENCE_ADMITTED_AUTOMATED_FACTUAL_SOURCE` -- reserved for a
     source/field pair that has actually cleared full production admission
     (Work Unit 8's decision). As of this cycle, per
     `PRODUCTION_ADMISSION_DECISION_V1.md`, **zero** source/field pairs
     have cleared -- this tier exists architecturally (so a future,
     separate promotion pass has somewhere real to plug an admitted source
     in without redesigning this module) but no builder function in this
     file ever emits an observation at this tier today.
  3. `PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE` -- any SHADOW-standing (not
     REJECTED) automated source: nflverse injury designation/practice
     state/depth-chart context, Sleeper current_team/active_inactive/
     ir_pup_nfi-class fields. Never authoritative; always overridable by a
     manual override at any time.
  4. Unknown (`ComposedField.value is None`) -- no source has ever reported
     a real value for this field. Never defaulted to "healthy" or any other
     guess (Gate 1).

**Sleeper `injury_designation` is explicitly EXCLUDED from this module**,
structurally in two independent places (`observations_from_sleeper_shadow`
never emits one, and `REJECTED_SOURCE_FIELD_PAIRS` defensively drops one
even if a future caller passes it anyway) -- per Worker 3's real REJECT
verdict (28.57% agreement vs the required >=99%, 32.69% coverage vs the
required >=95%, and one real zero-tolerance hard contradiction, Zay
Flowers/BAL). This is not a design choice this module is free to revisit;
it is a fixed, evidence-based exclusion carried forward from
`SOURCE_QUALITY_EVALUATION_V1.md`.

--- Freshness monotonicity (Gate 1 / directive requirement) ---

"Older-arriving data must never silently overwrite newer authoritative
data." Enforced only WITHIN the same precedence tier (a higher-precedence
source always wins regardless of freshness, by design -- see Gate 6; a
lower-precedence source never wins regardless of freshness). Within a tier,
`compose_field` compares `fetched_at` (falling back to `source_as_of` when
`fetched_at` is absent) and rejects an incoming observation whose parsed
timestamp is strictly OLDER than the currently composed value's timestamp.
An observation with no parseable timestamp at all is never allowed to prove
itself "newer" than one that does have a real timestamp (conservative
default); when NEITHER side has a usable timestamp, the tie is broken by
the documented `PREFERRED_SOURCE_BY_FIELD` order, never a coin flip.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from src.services.live_player_intelligence_identity_mapping_v1_service import (
    CommonSourceRow,
    IdentityMappingRow,
)
from src.services.live_player_intelligence_shadow_v1_service import ShadowPlayerStatus
from src.services.player_availability_status_service import PlayerAvailabilityStatus

# ---------------------------------------------------------------------------
# Precedence tiers
# ---------------------------------------------------------------------------

PRECEDENCE_MANUAL_VERIFIED_OVERRIDE = 1
PRECEDENCE_ADMITTED_AUTOMATED_FACTUAL_SOURCE = 2
PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE = 3
_PRECEDENCE_UNKNOWN = 0  # internal marker only -- never assigned to a real observation

PRECEDENCE_LABELS: dict[int, str] = {
    PRECEDENCE_MANUAL_VERIFIED_OVERRIDE: "MANUAL_VERIFIED_OVERRIDE",
    PRECEDENCE_ADMITTED_AUTOMATED_FACTUAL_SOURCE: "ADMITTED_AUTOMATED_FACTUAL_SOURCE",
    PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE: "SUPPLEMENTARY_SHADOW_SOURCE",
    _PRECEDENCE_UNKNOWN: "UNKNOWN_NO_SOURCE",
}

# The full field vocabulary this engine governs -- the SAME normalized
# factual fields Work Unit 4 added to `PlayerAvailabilityStatus`, plus the
# pre-existing fields the manual override wrapper already sets. Never
# expanded to news prose, analyst commentary, projected return date, or
# role speculation (same exclusion Work Unit 4's module docstring already
# committed to).
COMPOSABLE_FIELDS: tuple[str, ...] = (
    "status_category",
    "injury_designation",
    "practice_state",
    "ir_pup_nfi",
    "on_injured_reserve",
    "on_pup",
    "on_nfi",
    "suspension",
    "administrative_exempt",
    "released",
    "current_team",
    "active_inactive",
    "game_status",
    "depth_chart_position",
    "depth_chart_context",
)

# Real, evidence-based exclusion -- see module docstring. Structurally
# defended even though `observations_from_sleeper_shadow` also never emits
# these on its own.
REJECTED_SOURCE_FIELD_PAIRS: frozenset[tuple[str, str]] = frozenset(
    {
        ("SLEEPER_PUBLIC_PLAYERS_CATALOG", "injury_designation"),
    }
)

# Per-field preferred-source tie-break order, reusing
# `live_player_intelligence_shadow_v1_service.precedence_design()`'s
# already-documented proposal (this module is its first real
# implementation). Only used when freshness cannot decide (see module
# docstring).
PREFERRED_SOURCE_BY_FIELD: dict[str, tuple[str, ...]] = {
    "injury_designation": ("NFLVERSE_OFFICIAL_INJURY_REPORT",),
    "practice_state": ("NFLVERSE_OFFICIAL_INJURY_REPORT",),
    "current_team": ("SLEEPER_PUBLIC_PLAYERS_CATALOG",),
    "active_inactive": ("SLEEPER_PUBLIC_PLAYERS_CATALOG",),
    "ir_pup_nfi": ("SLEEPER_PUBLIC_PLAYERS_CATALOG",),
    "on_injured_reserve": ("SLEEPER_PUBLIC_PLAYERS_CATALOG",),
    "on_pup": ("SLEEPER_PUBLIC_PLAYERS_CATALOG",),
    "on_nfi": ("SLEEPER_PUBLIC_PLAYERS_CATALOG",),
    "suspension": ("SLEEPER_PUBLIC_PLAYERS_CATALOG",),
    "depth_chart_position": ("NFLVERSE_DEPTH_CHARTS",),
    "depth_chart_context": ("NFLVERSE_DEPTH_CHARTS",),
}


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(frozen=True)
class FieldObservation:
    """One real, single-field observation from a single source, ready to be
    folded into a `ComposedPlayerStatus` by `compose_field`."""

    field: str
    value: Any
    precedence_tier: int
    source: str
    source_as_of: str | None = None
    fetched_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "precedenceTier": self.precedence_tier,
            "precedenceLabel": PRECEDENCE_LABELS.get(self.precedence_tier, "UNKNOWN"),
            "source": self.source,
            "sourceAsOf": self.source_as_of,
            "fetchedAt": self.fetched_at,
        }


@dataclass(frozen=True)
class ComposedField:
    field: str
    value: Any
    precedence_tier: int
    source: str
    source_as_of: str | None
    fetched_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "precedenceTier": self.precedence_tier,
            "precedenceLabel": PRECEDENCE_LABELS.get(self.precedence_tier, "UNKNOWN"),
            "source": self.source,
            "sourceAsOf": self.source_as_of,
            "fetchedAt": self.fetched_at,
        }


def _unknown_field(field: str) -> ComposedField:
    return ComposedField(
        field=field,
        value=None,
        precedence_tier=_PRECEDENCE_UNKNOWN,
        source="NONE",
        source_as_of=None,
        fetched_at=None,
    )


def _accept(observation: FieldObservation) -> ComposedField:
    return ComposedField(
        field=observation.field,
        value=observation.value,
        precedence_tier=observation.precedence_tier,
        source=observation.source,
        source_as_of=observation.source_as_of,
        fetched_at=observation.fetched_at,
    )


def _prefers(field: str, candidate_source: str, other_source: str) -> bool:
    """True if `candidate_source` is documented as preferred over
    `other_source` for `field`. Conservative default (False, i.e. keep the
    existing value) when there is no documented preference to break the tie
    with -- never a coin flip."""

    order = PREFERRED_SOURCE_BY_FIELD.get(field, ())
    if candidate_source in order and other_source in order:
        return order.index(candidate_source) < order.index(other_source)
    return candidate_source in order and other_source not in order


def compose_field(existing: ComposedField | None, incoming: FieldObservation) -> ComposedField:
    """Applies precedence (Gate 6) + freshness monotonicity for ONE field.
    See module docstring for the full rule set. Pure -- no I/O, no reliance
    on wall-clock "now"; every decision is a function of its two inputs."""

    if (incoming.source, incoming.field) in REJECTED_SOURCE_FIELD_PAIRS:
        # Defense-in-depth: this source/field pair failed real admission
        # gates and must never enter composition, regardless of what any
        # caller passes in.
        return existing if existing is not None else _unknown_field(incoming.field)

    if incoming.value is None:
        # A non-observation ("this source has nothing to say"). Never
        # regresses an already-known composed value to unknown.
        return existing if existing is not None else _unknown_field(incoming.field)

    if existing is None or existing.value is None:
        return _accept(incoming)

    if incoming.precedence_tier < existing.precedence_tier:
        return _accept(incoming)  # strictly higher precedence always wins (Gate 6)

    if incoming.precedence_tier > existing.precedence_tier:
        return existing  # strictly lower precedence never wins, regardless of freshness

    # Same tier -- freshness monotonicity decides.
    existing_ts = _parse_timestamp(existing.fetched_at) or _parse_timestamp(existing.source_as_of)
    incoming_ts = _parse_timestamp(incoming.fetched_at) or _parse_timestamp(incoming.source_as_of)

    if incoming_ts is None and existing_ts is None:
        if _prefers(incoming.field, incoming.source, existing.source):
            return _accept(incoming)
        return existing
    if incoming_ts is None:
        return existing  # can't prove incoming is newer -- conservative, keep existing
    if existing_ts is None:
        return _accept(incoming)  # incoming carries real, verifiable evidence; existing does not
    if incoming_ts >= existing_ts:
        return _accept(incoming)
    return existing  # incoming is strictly OLDER -- rejected, this IS the monotonicity guarantee


@dataclass(frozen=True)
class ComposedPlayerStatus:
    player_id: str
    player_name: str
    fields: Mapping[str, ComposedField]

    def get(self, field: str) -> Any:
        composed = self.fields.get(field)
        return composed.value if composed is not None else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "playerId": self.player_id,
            "playerName": self.player_name,
            "fields": {name: field.to_dict() for name, field in self.fields.items()},
        }


def compose_player_availability(
    player_id: str,
    player_name: str,
    observations: Sequence[FieldObservation],
    *,
    existing: ComposedPlayerStatus | None = None,
) -> ComposedPlayerStatus:
    """Folds a real sequence of `FieldObservation`s (in whatever order the
    caller has them -- order does not change the outcome, since
    `compose_field` is order-independent within a tier only up to freshness/
    preference, and higher-tier observations always win regardless of when
    they arrive) into one `ComposedPlayerStatus`. Every field in
    `COMPOSABLE_FIELDS` is always present in the result, explicitly marked
    unknown (`UNKNOWN_NO_SOURCE`) when no source has ever reported a real
    value for it -- Gate 1's 'unknown stays unknown', never a guessed
    default."""

    fields: dict[str, ComposedField] = dict(existing.fields) if existing is not None else {}
    for observation in observations:
        if observation.field not in COMPOSABLE_FIELDS:
            continue
        fields[observation.field] = compose_field(fields.get(observation.field), observation)
    for field in COMPOSABLE_FIELDS:
        if field not in fields:
            fields[field] = _unknown_field(field)
    return ComposedPlayerStatus(player_id=player_id, player_name=player_name, fields=fields)


# ---------------------------------------------------------------------------
# Real source-specific observation builders. Each is a small, honest adapter
# -- no new identity/matching logic, no new vocabulary invented -- from an
# already-existing production-adjacent record shape into this module's
# `FieldObservation` shape.
# ---------------------------------------------------------------------------


def observations_from_manual_override(status: PlayerAvailabilityStatus) -> tuple[FieldObservation, ...]:
    """Every field the manual-override wrapper actually sets (non-`None`,
    or a real boolean it always populates) becomes a tier-1
    `MANUAL_VERIFIED_OVERRIDE` observation. Fields it leaves `None` (today,
    every Work Unit 4 field: `game_status`, `on_injured_reserve`, `on_pup`,
    `on_nfi`, `active_inactive`, `depth_chart_position`,
    `depth_chart_context`, plus `practice_state`/`ir_pup_nfi` which the
    wrapper has never populated) emit NO observation at all, so a real
    lower-precedence automated source can fill them -- this module never
    fabricates a tier-1 "manual says unknown" record that would block a
    real signal from ever reaching a field the override mechanism was
    never designed to cover."""

    candidate_values: dict[str, Any] = {
        "status_category": status.status_category,
        "injury_designation": status.injury_designation,
        "practice_state": status.practice_state,
        "ir_pup_nfi": status.ir_pup_nfi,
        "on_injured_reserve": status.on_injured_reserve,
        "on_pup": status.on_pup,
        "on_nfi": status.on_nfi,
        "suspension": status.suspension,
        "administrative_exempt": status.administrative_exempt,
        "released": status.released,
        "current_team": status.current_team,
        "active_inactive": status.active_inactive,
        "game_status": status.game_status,
        "depth_chart_position": status.depth_chart_position,
        "depth_chart_context": status.depth_chart_context,
    }
    observations: list[FieldObservation] = []
    for field, value in candidate_values.items():
        if value is None:
            continue
        observations.append(
            FieldObservation(
                field=field,
                value=value,
                precedence_tier=PRECEDENCE_MANUAL_VERIFIED_OVERRIDE,
                source=status.source,
                source_as_of=status.source_as_of,
                fetched_at=status.fetched_at,
            )
        )
    return tuple(observations)


def observations_from_nflverse_injury_shadow(
    records: Sequence[ShadowPlayerStatus],
    *,
    fetched_at: str | None,
) -> tuple[FieldObservation, ...]:
    """nflverse's official weekly injury report -- SHADOW standing (Gate 3/5
    not independently measurable this cycle, but NOT rejected). Emits
    `injury_designation`/`practice_state` only, tier 3."""

    observations: list[FieldObservation] = []
    for record in records:
        if not record.matched_canonical_player_id:
            continue
        if record.injury_designation:
            observations.append(
                FieldObservation(
                    field="injury_designation",
                    value=record.injury_designation,
                    precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
                    source=record.source,
                    source_as_of=record.source_as_of,
                    fetched_at=fetched_at,
                )
            )
        if record.practice_state:
            observations.append(
                FieldObservation(
                    field="practice_state",
                    value=record.practice_state,
                    precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
                    source=record.source,
                    source_as_of=record.source_as_of,
                    fetched_at=fetched_at,
                )
            )
    return tuple(observations)


_SLEEPER_IR_PUP_NFI_TO_BOOL_FIELD: dict[str, str] = {
    "Injured Reserve": "on_injured_reserve",
    "IR": "on_injured_reserve",
    "Physically Unable to Perform": "on_pup",
    "PUP": "on_pup",
    "Non Football Injury": "on_nfi",
    "NFI": "on_nfi",
}


def observations_from_sleeper_shadow(
    records: Sequence[ShadowPlayerStatus],
    *,
    fetched_at: str | None,
) -> tuple[FieldObservation, ...]:
    """Sleeper's public players catalog -- SHADOW standing for
    `ir_pup_nfi`-class/`current_team`/`active_inactive` fields (real, but
    small-n / not-yet-evaluated per `SOURCE_QUALITY_EVALUATION_V1.md`).
    **Deliberately never emits an `injury_designation` observation** -- that
    field's Sleeper source REJECTED (28.57% agreement, 32.69% coverage, one
    real hard contradiction). This is the structural, load-bearing
    enforcement of that exclusion; `REJECTED_SOURCE_FIELD_PAIRS` in
    `compose_field` is defense-in-depth on top of it, not the only
    safeguard."""

    observations: list[FieldObservation] = []
    for record in records:
        if not record.matched_canonical_player_id:
            continue
        if record.team:
            observations.append(
                FieldObservation(
                    field="current_team",
                    value=record.team,
                    precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
                    source=record.source,
                    source_as_of=record.source_as_of,
                    fetched_at=fetched_at,
                )
            )
        if record.status_category:
            observations.append(
                FieldObservation(
                    field="active_inactive",
                    value=record.status_category,
                    precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
                    source=record.source,
                    source_as_of=record.source_as_of,
                    fetched_at=fetched_at,
                )
            )
        if record.ir_pup_nfi:
            observations.append(
                FieldObservation(
                    field="ir_pup_nfi",
                    value=record.ir_pup_nfi,
                    precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
                    source=record.source,
                    source_as_of=record.source_as_of,
                    fetched_at=fetched_at,
                )
            )
            bool_field = _SLEEPER_IR_PUP_NFI_TO_BOOL_FIELD.get(record.ir_pup_nfi)
            if bool_field:
                observations.append(
                    FieldObservation(
                        field=bool_field,
                        value=True,
                        precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
                        source=record.source,
                        source_as_of=record.source_as_of,
                        fetched_at=fetched_at,
                    )
                )
        if record.suspension:
            observations.append(
                FieldObservation(
                    field="suspension",
                    value=True,
                    precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
                    source=record.source,
                    source_as_of=record.source_as_of,
                    fetched_at=fetched_at,
                )
            )
    return tuple(observations)


def observations_from_nflverse_depth_chart_shadow(
    common_rows: Sequence[CommonSourceRow],
    classified_rows: Sequence[IdentityMappingRow],
    *,
    fetched_at: str | None,
) -> tuple[FieldObservation, ...]:
    """nflverse depth charts -- the strongest real Gate-4 coverage of any
    source this cycle (100% of the official-report population), SHADOW
    standing, role/context only (no injury field at all). `common_rows` and
    `classified_rows` MUST be the same sequence, same order, same length
    (i.e. `classified_rows = classify_rows(common_rows, canonical_pool)`)
    -- this is exactly how `classify_rows` is documented to behave
    (preserves input order 1:1), not a new assumption invented here."""

    if len(common_rows) != len(classified_rows):
        raise ValueError("common_rows and classified_rows must be the same length and order")

    observations: list[FieldObservation] = []
    for common_row, classified in zip(common_rows, classified_rows):
        if not classified.matched_canonical_player_id:
            continue
        raw = common_row.raw
        pos_abb = str(raw.get("pos_abb") or "").strip()
        pos_rank = str(raw.get("pos_rank") or "").strip()
        source_as_of = str(raw.get("dt") or "").strip() or None
        if pos_abb:
            observations.append(
                FieldObservation(
                    field="depth_chart_position",
                    value=pos_abb,
                    precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
                    source="NFLVERSE_DEPTH_CHARTS",
                    source_as_of=source_as_of,
                    fetched_at=fetched_at,
                )
            )
        if pos_abb or pos_rank:
            context = f"{pos_abb}{pos_rank}" if pos_abb and pos_rank else (pos_abb or pos_rank)
            observations.append(
                FieldObservation(
                    field="depth_chart_context",
                    value=context,
                    precedence_tier=PRECEDENCE_SUPPLEMENTARY_SHADOW_SOURCE,
                    source="NFLVERSE_DEPTH_CHARTS",
                    source_as_of=source_as_of,
                    fetched_at=fetched_at,
                )
            )
    return tuple(observations)
