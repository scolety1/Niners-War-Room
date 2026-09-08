"""AI Intelligence backend skeleton (sections 19-21): News Scout event
schema + store, Impact Analyst hypothesis generator, Explanation layer.

No live API calls anywhere in this module -- news events are appended by
an owner/operator action (append_news_event), never fetched by this
module itself, so there is nothing here to gate behind
NWR_FANTASYPROS_API_KEY or any other provider credential (that key stays
scoped to fantasypros_kdst_consensus_service.py, its existing, already-
governed home). Nothing in this module logs, persists, or echoes any
credential.

Deterministic and fully offline by design:
- News Scout is a schema + an append-only, validated JSON Lines store
  (same architecture as nwr_pure_experiment_service.py's decision
  receipts) -- it does not go find news on its own.
- Impact Analyst is a disclosed, structural rule table over
  (event_type, severity) pairs, not a live model call. Every hypothesis
  it produces carries its own confidence and a requires_owner_review
  flag; nothing here is ever treated as ground truth.
- The Explanation layer assembles natural language strictly from real,
  already-computed decision factors the caller supplies (VOR, roster
  need, ADP context, Impact Analyst hypotheses) -- it never invents a
  reason not present in its inputs.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# --- News Scout -----------------------------------------------------------

NEWS_EVENT_TYPES = frozenset(
    {
        "INJURY",
        "IR",
        "DEPTH_CHART_CHANGE",
        "SUSPENSION",
        "TRADE",
        "RETIREMENT",
        "COACHING_CHANGE",
        "ROLE_CHANGE",
        # NWR post-draft overnight (phase 6/10): the directive's own status
        # taxonomy (IR/PUP/NFI/Commissioner's Exempt/suspension/released/
        # free agent) named three real, structurally distinct categories
        # that had no event_type at all before this pass -- everything
        # non-INJURY/SUSPENSION/IR degraded to the generic OTHER catch-all,
        # which has no rule in _DIRECT_IMPACT_RULES and so always fell
        # through to UNCERTAIN/LOW ("degrades... forces owner review rather
        # than guessing"). Added as real, distinct types with their own
        # rules below, each one still never guessing a specific duration:
        "PUP_NFI",  # Physically Unable to Perform / Non-Football Injury --
        # a real, well-defined NFL roster designation (a confirmed
        # multi-game absence by rule), distinct from a plain INJURY report.
        "ADMINISTRATIVE_EXEMPT",  # Commissioner's Exempt List or an active
        # legal/disciplinary proceeding with no announced outcome yet --
        # genuinely uncertain, deliberately never treated as a confident
        # NEGATIVE the way a real SUSPENSION already is.
        "RELEASED",  # cut/waived -- an immediate real absence from any
        # roster; whether/where the player signs next is unknown.
        "OTHER",
    }
)
NEWS_SEVERITIES = frozenset({"LOW", "MEDIUM", "HIGH"})
# Event types where a same-position teammate plausibly benefits -- gates
# generate_beneficiary_hypotheses(); everything else produces no
# beneficiary inference at all rather than a low-quality guess.
_BENEFICIARY_ELIGIBLE_EVENT_TYPES = frozenset({"INJURY", "IR", "SUSPENSION", "RETIREMENT"})


class AiIntelligenceError(ValueError):
    """Raised for News Scout schema violations or store integrity issues."""


@dataclass(frozen=True)
class NewsEvent:
    event_id: str
    player_id: str
    player_name: str
    position: str
    team: str
    event_type: str
    severity: str
    headline: str
    source: str
    source_url: str
    published_at_utc: str
    ingested_at_utc: str
    schema_version: int = 1


def validate_news_event(event: NewsEvent) -> None:
    """Raises on a malformed event -- never silently admitted."""
    if not event.event_id.strip():
        raise AiIntelligenceError("event_id must be non-empty.")
    if not event.player_id.strip():
        raise AiIntelligenceError("player_id must be non-empty.")
    if event.event_type not in NEWS_EVENT_TYPES:
        raise AiIntelligenceError(f"Unknown event_type: {event.event_type!r}")
    if event.severity not in NEWS_SEVERITIES:
        raise AiIntelligenceError(f"Unknown severity: {event.severity!r}")
    if not event.headline.strip():
        raise AiIntelligenceError("headline must be non-empty.")
    if not event.source.strip():
        raise AiIntelligenceError("source must be non-empty.")
    for field_name in ("published_at_utc", "ingested_at_utc"):
        value = getattr(event, field_name)
        try:
            datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise AiIntelligenceError(
                f"{field_name} is not a valid ISO datetime: {value!r}"
            ) from exc


def _news_events_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "news_scout" / f"{profile_id}.jsonl"


def append_news_event(root: str | Path, profile_id: str, event: NewsEvent) -> None:
    """Append-only. Refuses a duplicate event_id for this profile rather
    than silently overwriting or duplicating a record."""
    validate_news_event(event)
    existing_ids = {existing.event_id for existing in read_news_events(root, profile_id)}
    if event.event_id in existing_ids:
        raise AiIntelligenceError(f"event_id {event.event_id!r} is already recorded.")
    path = _news_events_path(root, profile_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), sort_keys=True, separators=(",", ":")) + "\n")


def read_news_events(
    root: str | Path, profile_id: str, *, player_id: str | None = None
) -> tuple[NewsEvent, ...]:
    path = _news_events_path(root, profile_id)
    if not path.is_file():
        return ()
    events: list[NewsEvent] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        document = json.loads(line)
        document.pop("schema_version", None)
        events.append(NewsEvent(**document))
    if player_id is not None:
        events = [event for event in events if event.player_id == player_id]
    return tuple(events)


# --- Impact Analyst ---------------------------------------------------------

IMPACT_DIRECTIONS = frozenset({"POSITIVE", "NEGATIVE", "NEUTRAL", "UNCERTAIN"})
IMPACT_CONFIDENCES = frozenset({"LOW", "MEDIUM", "HIGH"})
# How long the hypothesis is expected to hold, disclosed explicitly on
# every hypothesis (section 16's "confidence/horizon/reason must be
# explicit") -- never left implicit in the text alone.
IMPACT_HORIZONS = frozenset({"IMMEDIATE", "REST_OF_SEASON", "LONG_TERM"})


@dataclass(frozen=True)
class ImpactHypothesis:
    hypothesis_id: str
    subject_player_id: str  # who the hypothesis is ABOUT -- may differ from the event's own player
    direction: str
    confidence: str
    hypothesis_text: str
    evidence_event_ids: tuple[str, ...]
    requires_owner_review: bool
    generated_at_utc: str
    horizon: str = "REST_OF_SEASON"


# A disclosed, structural rule table -- not a live model call. Every rule
# maps a real, ingested (event_type, severity) pair to a
# (direction, confidence, horizon, template); anything not in this table
# degrades to UNCERTAIN/LOW/REST_OF_SEASON and forces owner review rather
# than guessing.
_DIRECT_IMPACT_RULES: dict[tuple[str, str], tuple[str, str, str, str]] = {
    ("INJURY", "HIGH"): (
        "NEGATIVE", "HIGH", "IMMEDIATE",
        "{player} ({event_type}, {severity} severity) -- expect reduced or zero "
        "near-term availability.",
    ),
    ("INJURY", "MEDIUM"): (
        "NEGATIVE", "MEDIUM", "IMMEDIATE",
        "{player} ({event_type}, {severity} severity) -- possible missed game(s) or reduced usage.",
    ),
    ("INJURY", "LOW"): (
        "NEGATIVE", "LOW", "IMMEDIATE",
        "{player} ({event_type}, {severity} severity) -- monitor; impact uncertain.",
    ),
    ("IR", "HIGH"): (
        "NEGATIVE", "HIGH", "REST_OF_SEASON",
        "{player} placed on injured reserve -- a minimum multi-week absence; treat "
        "as unavailable for the foreseeable near-term schedule.",
    ),
    ("IR", "MEDIUM"): (
        "NEGATIVE", "MEDIUM", "REST_OF_SEASON",
        "{player} placed on injured reserve (return timeline uncertain) -- "
        "unavailable at minimum for several weeks.",
    ),
    ("SUSPENSION", "HIGH"): (
        "NEGATIVE", "HIGH", "IMMEDIATE", "{player} ({event_type}) -- expect missed games.",
    ),
    ("SUSPENSION", "MEDIUM"): (
        "NEGATIVE", "MEDIUM", "IMMEDIATE", "{player} ({event_type}) -- possible missed game(s).",
    ),
    ("RETIREMENT", "HIGH"): (
        "NEGATIVE", "HIGH", "REST_OF_SEASON",
        "{player} ({event_type} reported) -- expect zero further availability.",
    ),
    ("DEPTH_CHART_CHANGE", "MEDIUM"): (
        "UNCERTAIN", "MEDIUM", "REST_OF_SEASON",
        "{player} ({event_type}) -- role may be shifting; confirm before acting.",
    ),
    ("ROLE_CHANGE", "MEDIUM"): (
        "UNCERTAIN", "MEDIUM", "REST_OF_SEASON",
        "{player} ({event_type} reported) -- opportunity shift, direction not yet confirmed.",
    ),
    ("ROLE_CHANGE", "HIGH"): (
        "UNCERTAIN", "HIGH", "REST_OF_SEASON",
        "{player} ({event_type} reported, {severity} confidence) -- a confirmed role "
        "shift; direction of fantasy impact still depends on which player is affected.",
    ),
    ("TRADE", "MEDIUM"): (
        "UNCERTAIN", "MEDIUM", "REST_OF_SEASON",
        "{player} (traded) -- new team context; situation not yet modeled.",
    ),
    ("COACHING_CHANGE", "LOW"): (
        "UNCERTAIN", "LOW", "LONG_TERM",
        "{player} (coaching change on team) -- long-horizon signal, no immediate action implied.",
    ),
    # NWR post-draft overnight (phase 6/10): three new, real, structurally
    # distinct status categories the directive named explicitly. Each
    # still follows the exact same disclosed principle as every rule
    # above -- a real, ingested (event_type, severity) pair, never a
    # guessed specific duration, never a player-name-specific rule.
    ("PUP_NFI", "HIGH"): (
        "NEGATIVE", "HIGH", "IMMEDIATE",
        "{player} placed on PUP/NFI -- a confirmed absence for at least the "
        "first 4 regular-season games by rule; return timing beyond that is "
        "not yet known.",
    ),
    ("ADMINISTRATIVE_EXEMPT", "HIGH"): (
        # Deliberately UNCERTAIN, not NEGATIVE, even at HIGH confidence --
        # unlike SUSPENSION (a confirmed penalty already imposed), an
        # Exempt-list placement or open legal/disciplinary proceeding has
        # NO announced outcome yet; treating it as a confident NEGATIVE
        # would be guessing the eventual result. Marking it UNCERTAIN
        # here (not a special case) already makes
        # generate_direct_impact_hypothesis's existing
        # `requires_owner_review = confidence != "HIGH" or direction ==
        # "UNCERTAIN"` rule force owner review regardless of severity.
        "UNCERTAIN", "HIGH", "IMMEDIATE",
        "{player} (administrative/exempt-list status, {severity} severity) -- "
        "expected availability is materially uncertain pending an outcome "
        "that has not yet been announced; do not assume a specific missed-"
        "game count.",
    ),
    ("ADMINISTRATIVE_EXEMPT", "MEDIUM"): (
        "UNCERTAIN", "MEDIUM", "IMMEDIATE",
        "{player} (administrative/exempt-list status reported, {severity} "
        "severity) -- monitor; outcome and duration not yet known.",
    ),
    ("RELEASED", "HIGH"): (
        "NEGATIVE", "HIGH", "IMMEDIATE",
        "{player} (released/waived) -- currently on no NFL roster; whether "
        "and where he signs next is not yet known.",
    ),
}


def _utc_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def generate_direct_impact_hypothesis(event: NewsEvent) -> ImpactHypothesis:
    """The hypothesis about the event's own player. Anything outside
    _DIRECT_IMPACT_RULES degrades to UNCERTAIN/LOW/REST_OF_SEASON with
    requires_owner_review=True rather than guessing."""
    validate_news_event(event)
    direction, confidence, horizon, template = _DIRECT_IMPACT_RULES.get(
        (event.event_type, event.severity),
        (
            "UNCERTAIN", "LOW", "REST_OF_SEASON",
            "{player} ({event_type}, {severity} severity) -- impact not modeled; "
            "owner review required.",
        ),
    )
    text = template.format(
        player=event.player_name,
        event_type=event.event_type.replace("_", " ").lower(),
        severity=event.severity.lower(),
    )
    return ImpactHypothesis(
        hypothesis_id=f"direct:{event.event_id}",
        subject_player_id=event.player_id,
        direction=direction,
        confidence=confidence,
        hypothesis_text=text,
        evidence_event_ids=(event.event_id,),
        requires_owner_review=confidence != "HIGH" or direction == "UNCERTAIN",
        generated_at_utc=_utc_now_iso(),
        horizon=horizon,
    )


def generate_beneficiary_hypotheses(
    event: NewsEvent,
    *,
    same_team_same_position_teammates: Sequence[tuple[str, str]],  # (player_id, player_name)
) -> tuple[ImpactHypothesis, ...]:
    """For an event type/severity that plausibly opens opportunity for a
    teammate (injury/suspension/retirement, medium+ severity), generates
    one low-confidence POSITIVE hypothesis per supplied teammate. The
    caller supplies the actual roster context (this function never
    invents a name or looks one up); every result is
    requires_owner_review=True -- this is a structural inference, not a
    depth-chart-verified fact."""
    validate_news_event(event)
    direct = generate_direct_impact_hypothesis(event)
    if (
        event.event_type not in _BENEFICIARY_ELIGIBLE_EVENT_TYPES
        or direct.direction != "NEGATIVE"
        or direct.confidence == "LOW"
    ):
        return ()
    results: list[ImpactHypothesis] = []
    for teammate_id, teammate_name in same_team_same_position_teammates:
        if teammate_id == event.player_id:
            continue
        results.append(
            ImpactHypothesis(
                hypothesis_id=f"beneficiary:{event.event_id}:{teammate_id}",
                subject_player_id=teammate_id,
                direction="POSITIVE",
                confidence="LOW",
                hypothesis_text=(
                    f"{teammate_name} ({event.position}, {event.team}) may see increased "
                    f"opportunity following {event.player_name}'s "
                    f"{event.event_type.replace('_', ' ').lower()} -- structural inference "
                    "from roster position only, not a confirmed depth-chart change."
                ),
                evidence_event_ids=(event.event_id,),
                requires_owner_review=True,
                generated_at_utc=_utc_now_iso(),
                horizon=direct.horizon,
            )
        )
    return tuple(results)


def generate_role_uncertainty_hypotheses(
    event: NewsEvent,
    *,
    other_same_position_players: Sequence[tuple[str, str]],  # (player_id, player_name)
) -> tuple[ImpactHypothesis, ...]:
    """The "other backfield" case: players who share the event's team and
    position but are NOT the primary beneficiary (that is
    generate_beneficiary_hypotheses's job) get a direction=UNCERTAIN,
    LOW-confidence role-uncertainty hypothesis instead of a POSITIVE
    one -- a real depth-chart shakeup can go either way for a 3rd/4th
    option, and asserting POSITIVE for all of them would overstate the
    real signal. Same eligibility gate as generate_beneficiary_hypotheses
    (a genuinely negative, medium+ confidence event on the primary
    player); always requires_owner_review=True."""
    validate_news_event(event)
    direct = generate_direct_impact_hypothesis(event)
    if (
        event.event_type not in _BENEFICIARY_ELIGIBLE_EVENT_TYPES
        or direct.direction != "NEGATIVE"
        or direct.confidence == "LOW"
    ):
        return ()
    results: list[ImpactHypothesis] = []
    for player_id, player_name in other_same_position_players:
        if player_id == event.player_id:
            continue
        results.append(
            ImpactHypothesis(
                hypothesis_id=f"role_uncertainty:{event.event_id}:{player_id}",
                subject_player_id=player_id,
                direction="UNCERTAIN",
                confidence="LOW",
                hypothesis_text=(
                    f"{player_name} ({event.position}, {event.team}) role uncertainty "
                    f"following {event.player_name}'s "
                    f"{event.event_type.replace('_', ' ').lower()} -- depth chart may shift "
                    "in either direction for this player; not a confirmed beneficiary."
                ),
                evidence_event_ids=(event.event_id,),
                requires_owner_review=True,
                generated_at_utc=_utc_now_iso(),
                horizon=direct.horizon,
            )
        )
    return tuple(results)


@dataclass(frozen=True)
class RosterContext:
    """Caller-supplied, real roster context for one event's team/position
    group -- who the likely primary beneficiary is, and who else shares
    that position group. This module never looks up a roster itself; the
    caller (with access to the real roster data) owns this step."""

    primary_beneficiary: tuple[str, str] | None = None  # (player_id, player_name)
    other_same_position_players: tuple[tuple[str, str], ...] = ()


def run_impact_pipeline(
    event: NewsEvent, *, roster_context: RosterContext | None = None
) -> tuple[ImpactHypothesis, ...]:
    """The end-to-end News Scout -> Impact Analyst pipeline (section 15):
    verified fact normalization (validate_news_event, raising on a
    malformed event rather than silently admitting it), the direct
    hypothesis about the event's own player, and -- when the caller
    supplies real roster context (the "affected player lookup" step,
    which this module does not perform itself) -- the primary-
    beneficiary and role-uncertainty hypotheses too. Returns every
    hypothesis this event produces, in a stable
    (direct, beneficiary, role-uncertainty) order, directly consumable by
    explain_pick_recommendation's impact_hypotheses field -- this is the
    "downstream explanation availability" step."""
    hypotheses = [generate_direct_impact_hypothesis(event)]
    if roster_context is not None:
        if roster_context.primary_beneficiary is not None:
            hypotheses.extend(
                generate_beneficiary_hypotheses(
                    event, same_team_same_position_teammates=(roster_context.primary_beneficiary,)
                )
            )
        excluded_id = (
            roster_context.primary_beneficiary[0] if roster_context.primary_beneficiary else None
        )
        others = tuple(
            player
            for player in roster_context.other_same_position_players
            if player[0] != excluded_id
        )
        if others:
            hypotheses.extend(
                generate_role_uncertainty_hypotheses(event, other_same_position_players=others)
            )
    return tuple(hypotheses)


# --- Explanation layer -------------------------------------------------------


@dataclass(frozen=True)
class PickExplanationInputs:
    player_id: str
    player_name: str
    position: str
    overall_rank: int
    replacement_adjusted_value: float
    roster_position_count: int
    position_max: int | None
    adp_expected_pick: float | None
    current_pick_number: int
    impact_hypotheses: tuple[ImpactHypothesis, ...] = ()


def explain_pick_recommendation(inputs: PickExplanationInputs) -> str:
    """Assembles a natural-language explanation strictly from real,
    already-computed factors on `inputs` -- never a reason not present
    there. Every clause traces to a field the caller supplied."""
    parts = [
        f"{inputs.player_name} ({inputs.position}) is ranked #{inputs.overall_rank} overall "
        f"with a replacement-adjusted value of {inputs.replacement_adjusted_value:.1f}."
    ]
    if inputs.position_max is not None:
        parts.append(
            f"Roster currently has {inputs.roster_position_count} of a "
            f"{inputs.position_max}-max at {inputs.position}."
        )
    if inputs.adp_expected_pick is not None:
        gap = inputs.adp_expected_pick - inputs.current_pick_number
        if gap > 0.5:
            parts.append(
                f"Market ADP ({inputs.adp_expected_pick:.1f}) suggests this player often "
                f"lasts roughly {gap:.1f} more picks -- waiting carries real risk but is not "
                "guaranteed to lose the player."
            )
        elif gap < -0.5:
            parts.append(
                f"Market ADP ({inputs.adp_expected_pick:.1f}) suggests this player is "
                "typically already gone by this pick in the broader market."
            )
        else:
            parts.append(f"Market ADP ({inputs.adp_expected_pick:.1f}) matches this pick closely.")
    for hypothesis in inputs.impact_hypotheses:
        flag = " (needs owner review)" if hypothesis.requires_owner_review else ""
        parts.append(f"News: {hypothesis.hypothesis_text}{flag}")
    return " ".join(parts)
