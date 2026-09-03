"""Champion/Challenger registry (section 28) -- registries/contracts
only, no automatic promotion.

Storage mirrors nwr_pure_experiment_service.py's own pattern: a
write-once `registration.json` per challenger, then an append-only
`decisions.jsonl` of promotion-decision events. No code path in this
module -- or anywhere else in the repo, verified via grep -- can mark a
challenger PROMOTED without an explicit record_promotion_decision() call
carrying a non-empty, human-authored reason. There is no scheduler, no
threshold-based auto-promotion, and no default value that resolves to
PROMOTED.

A "champion" here is always an already-shipped, already-governed
production value (e.g. NWR's admitted rank, or
NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1's raw output). A
"challenger" is always a SHADOW/RESEARCH module (e.g.
rookie_market_blend_challenger_service.py) evaluated against real
evidence but never itself production-authoritative until an explicit
promotion decision is recorded here -- and even then, this registry only
RECORDS the decision. It does not wire anything into desktop_facade.py
or any production ranking path; actually swapping a champion for a
challenger remains a separate, explicit code change reviewed on its own
merits, not something this registry can trigger.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REGISTRY_SCHEMA_VERSION = 1
# RESEARCH_ONLY (section 23): a challenger explicitly marked never eligible
# for promotion -- distinct from REJECTED, which means it WAS evaluated for
# promotion and found wanting. A caller records RESEARCH_ONLY the same way
# as any other decision (record_promotion_decision); current_status() then
# reports it like any other terminal decision.
VALID_DECISIONS = frozenset({"PROMOTED", "REJECTED", "RETIRED", "RESEARCH_ONLY"})
# Fields a PROMOTED decision's receipt must carry (section 23's own list),
# enforced only for PROMOTED -- a REJECTED/RETIRED/RESEARCH_ONLY decision
# does not need a full promotion receipt.
PROMOTION_RECEIPT_REQUIRED_FIELDS = ("baseline", "metrics", "confidence")


class ChampionChallengerRegistryError(ValueError):
    """Raised for registry integrity violations."""


def _registry_root(root: str | Path) -> Path:
    return Path(root) / "champion_challenger_registry"


def _registration_path(root: str | Path, challenger_id: str) -> Path:
    return _registry_root(root) / challenger_id / "registration.json"


def _decisions_path(root: str | Path, challenger_id: str) -> Path:
    return _registry_root(root) / challenger_id / "decisions.jsonl"


@dataclass(frozen=True)
class ChallengerRegistration:
    challenger_id: str  # stable slug, e.g. "rookie-market-blend-v1"
    champion_name: str  # what it challenges, e.g. the champion source_id/version
    challenger_name: str  # e.g. ROOKIE_MARKET_BLEND_CHALLENGER_VERSION
    # dotted import path, e.g. "src.services.rookie_market_blend_challenger_service"
    challenger_module: str
    hypothesis: str  # the specific weakness this challenger targets, not a vague "improve accuracy"
    # the real backtest/evidence numbers this challenger was registered with, not a bare claim
    evaluation_summary: Mapping[str, Any]
    registered_at_utc: str
    registered_by: str
    # parent: another challenger_id this one supersedes/derives from, or
    # None for a first-generation challenger (section 23's "parent" field).
    parent: str | None = None
    code_sha: str = ""
    feature_set_sha: str = ""
    training_dataset_sha: str = ""
    calibration_dataset_sha: str = ""
    evaluation_dataset_sha: str = ""
    algorithm_parameters: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = REGISTRY_SCHEMA_VERSION


def register_challenger(root: str | Path, registration: ChallengerRegistration) -> Path:
    """Write the registration once. Refuses to overwrite an existing
    registration for the same challenger_id -- a real re-registration
    (e.g. a new hypothesis or module version) needs a new challenger_id,
    so the history of what was actually evaluated is never silently
    rewritten."""
    if not registration.hypothesis.strip():
        raise ChampionChallengerRegistryError("hypothesis must be a non-empty description.")
    if not registration.evaluation_summary:
        raise ChampionChallengerRegistryError(
            "evaluation_summary must not be empty -- a challenger is registered with real "
            "evidence, not a bare claim."
        )
    if (
        registration.parent is not None
        and load_registration(root, registration.parent) is None
    ):
        raise ChampionChallengerRegistryError(
            f"parent {registration.parent!r} is not a registered challenger_id."
        )
    path = _registration_path(root, registration.challenger_id)
    if path.exists():
        raise ChampionChallengerRegistryError(
            f"Challenger {registration.challenger_id!r} is already registered; "
            "use a new challenger_id for a new hypothesis or module version."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(asdict(registration), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)
    return path


def load_registration(root: str | Path, challenger_id: str) -> ChallengerRegistration | None:
    path = _registration_path(root, challenger_id)
    if not path.is_file():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    document.pop("schema_version", None)
    return ChallengerRegistration(**document)


def list_registered_challengers(root: str | Path) -> tuple[str, ...]:
    registry_root = _registry_root(root)
    if not registry_root.is_dir():
        return ()
    return tuple(
        sorted(
            entry.name
            for entry in registry_root.iterdir()
            if entry.is_dir() and (entry / "registration.json").is_file()
        )
    )


@dataclass(frozen=True)
class PromotionDecision:
    challenger_id: str
    decided_at_utc: str
    decision: str  # "PROMOTED" | "REJECTED" | "RETIRED"
    decided_by: str  # a human identity/role, never "system" or "auto"
    reason: str
    # Rollback pointer mechanics (section 19): for a RETIRED decision,
    # names what becomes effective again -- either the literal string
    # "CHAMPION" (fall back to NWR's own default, no challenger active),
    # or another registered challenger_id this one superseded (so
    # retiring v2 can roll back to v1 rather than all the way to the
    # champion). Validated in record_promotion_decision(): a
    # challenger_id target must itself have a real registration on disk.
    rollback_pointer: str | None = None
    # Promotion receipt fields (section 23) -- required (non-empty) only
    # when decision == "PROMOTED", enforced in record_promotion_decision().
    baseline: str = ""
    metrics: Mapping[str, Any] = field(default_factory=dict)
    confidence: str = ""
    season_splits: Mapping[str, Any] = field(default_factory=dict)
    guardrails: tuple[str, ...] = ()
    schema_version: int = REGISTRY_SCHEMA_VERSION


def record_promotion_decision(root: str | Path, decision: PromotionDecision) -> None:
    """Append-only. This is the ONLY function in this module that can
    change a challenger's status, and it always requires an explicit,
    non-empty, human-authored reason -- see the module docstring for why
    that is a hard invariant, not a convention."""
    if decision.decision not in VALID_DECISIONS:
        raise ChampionChallengerRegistryError(f"Unknown decision: {decision.decision!r}")
    if not decision.reason.strip():
        raise ChampionChallengerRegistryError(
            f"{decision.decision} requires a non-empty, human-authored reason."
        )
    if not decision.decided_by.strip() or decision.decided_by.strip().lower() in {
        "system",
        "auto",
        "automatic",
    }:
        raise ChampionChallengerRegistryError(
            "decided_by must name a real human identity/role, not an automated actor."
        )
    if load_registration(root, decision.challenger_id) is None:
        raise ChampionChallengerRegistryError(
            f"Challenger {decision.challenger_id!r} has no registration; "
            "register_challenger() must run before a promotion decision can be recorded."
        )
    if (
        decision.rollback_pointer is not None
        and decision.rollback_pointer != "CHAMPION"
        and load_registration(root, decision.rollback_pointer) is None
    ):
        raise ChampionChallengerRegistryError(
            f"rollback_pointer {decision.rollback_pointer!r} is neither 'CHAMPION' nor a "
            "registered challenger_id."
        )
    if decision.decision == "PROMOTED":
        missing_receipt_fields = [
            name for name in PROMOTION_RECEIPT_REQUIRED_FIELDS if not getattr(decision, name)
        ]
        if missing_receipt_fields:
            raise ChampionChallengerRegistryError(
                "PROMOTED requires a full promotion receipt; missing/empty: "
                + ", ".join(missing_receipt_fields)
            )
    path = _decisions_path(root, decision.challenger_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(decision), sort_keys=True, separators=(",", ":")) + "\n")


def read_promotion_decisions(root: str | Path, challenger_id: str) -> list[dict[str, Any]]:
    path = _decisions_path(root, challenger_id)
    if not path.is_file():
        return []
    decisions: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            decisions.append(json.loads(line))
    return decisions


def current_status(root: str | Path, challenger_id: str) -> str:
    """"UNREGISTERED" if no registration exists; "REGISTERED" if
    registered with no decision yet; otherwise the most recent decision's
    value ("PROMOTED" / "REJECTED" / "RETIRED"). A challenger can move
    PROMOTED -> RETIRED later (a later decision always wins), but never
    moves to PROMOTED except via an explicit record_promotion_decision()
    call somewhere in this challenger's own history."""
    if load_registration(root, challenger_id) is None:
        return "UNREGISTERED"
    decisions = read_promotion_decisions(root, challenger_id)
    if not decisions:
        return "REGISTERED"
    return str(decisions[-1]["decision"])


def resolve_rollback_target(root: str | Path, challenger_id: str) -> str:
    """Follows a challenger's own RETIRED -> rollback_pointer chain to
    find what is actually effective right now: "CHAMPION" if nothing is
    promoted, or the challenger_id of whichever challenger in the chain
    is currently PROMOTED. Detects and raises on a cycle rather than
    looping forever -- a malformed chain is a real integrity error, not
    something to silently paper over."""
    visited: set[str] = set()
    current = challenger_id
    while True:
        if current in visited:
            raise ChampionChallengerRegistryError(
                f"Rollback pointer cycle detected starting from {challenger_id!r}."
            )
        visited.add(current)
        status = current_status(root, current)
        if status == "PROMOTED":
            return current
        if status != "RETIRED":
            return "CHAMPION"
        decisions = read_promotion_decisions(root, current)
        pointer = decisions[-1].get("rollback_pointer")
        if pointer is None or pointer == "CHAMPION":
            return "CHAMPION"
        current = str(pointer)
