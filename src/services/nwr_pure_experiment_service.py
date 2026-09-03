"""NWR PURE 001 — experiment freeze receipt, immutable decision receipts,
and the pre-draft readiness check (sections 14/16/18 of the Saturday NWR
PURE release-candidate wave).

Storage is append-only JSON Lines under
`<redraft_root>/nwr_pure_experiments/<experiment_id>/`:
- `freeze_receipt.json` -- written once, at freeze time. Never rewritten;
  a re-freeze of the same experiment_id is refused.
- `decisions.jsonl` -- one JSON object per line, appended per pick, never
  rewritten or deleted. A correction to draft state (event ledger
  REPLACE/CLEAR/FILL GAP) never mutates an existing line here -- it can
  only add a new ReceiptCorrectionRecord line referencing the original
  pick_number, appended after it.

This module does not decide anything and does not compute Team Score /
Championship Equity / Pick Score itself -- it records values a caller
(the facade, wiring the SHADOW module in) computed. Keeping receipt
storage separate from the decision math means a receipt schema change
never risks the tested SHADOW algorithms, and vice versa.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

EXPERIMENT_SCHEMA_VERSION = 1


class NwrPureExperimentError(ValueError):
    """Raised for experiment-receipt integrity violations."""


def _canonical_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def hash_player_universe(available_player_ids: Sequence[str]) -> str:
    """Deterministic hash of exactly which players were available at a
    given moment -- lets a receipt prove what the candidate set actually
    was, independent of the (mutable, append-only-but-growing) live
    board state.
    """
    canonical = sorted(str(pid) for pid in available_player_ids)
    return hashlib.sha256("\n".join(canonical).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExperimentFreezeReceipt:
    experiment_id: str
    frozen_at_utc: str
    app_branch: str
    app_head: str
    app_tree: str
    model_sha: str  # RankingResult.projection_sha256
    player_universe_sha: str  # current.manifest.json source_sha256
    player_universe_row_count: int
    player_universe_valid_until: str
    league_profile_hash: str  # sha256 of the LeagueProfile as canonical JSON
    market_snapshot_sha: str  # AdpSnapshot.source_sha256, "" if unavailable
    identity_registry_sha: (
        str  # "NOT_YET_IMPLEMENTED" until a real registry exists -- never fabricated
    )
    algorithm_version: str  # MODEL_FAMILY
    authority_label: str  # REDRAFT_AUTHORITY_LABEL
    team_score_version: str
    championship_equity_version: str
    pick_score_version: str
    source_as_of: str
    schema_version: int = EXPERIMENT_SCHEMA_VERSION


def build_league_profile_hash(profile_document: Mapping[str, Any]) -> str:
    return _canonical_hash(profile_document)


def freeze_experiment(
    root: str | Path,
    receipt: ExperimentFreezeReceipt,
) -> Path:
    """Write the freeze receipt once. Refuses to overwrite an existing
    freeze for the same experiment_id -- a real re-freeze needs a new
    experiment_id, matching section 16's 'do not silently change the
    experiment mid-draft' rule.
    """
    experiment_dir = Path(root) / "nwr_pure_experiments" / receipt.experiment_id
    path = experiment_dir / "freeze_receipt.json"
    if path.exists():
        raise NwrPureExperimentError(
            f"Experiment {receipt.experiment_id!r} is already frozen; use a new experiment_id."
        )
    experiment_dir.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)
    return path


def load_freeze_receipt(root: str | Path, experiment_id: str) -> ExperimentFreezeReceipt | None:
    path = Path(root) / "nwr_pure_experiments" / experiment_id / "freeze_receipt.json"
    if not path.is_file():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    document.pop("schema_version", None)
    return ExperimentFreezeReceipt(**document)


@dataclass(frozen=True)
class DecisionReceipt:
    experiment_id: str
    timestamp_utc: str
    pick_number: int
    round: int
    owner_slot: int
    available_player_universe_hash: str
    roster_before: tuple[str, ...]
    production_nwr_recommendation: str | None  # playerId, the currently-admitted authority's pick
    optimizer_recommendation: str | None  # playerId, the experimental Pick Score winner
    candidate_set: tuple[str, ...]
    player_score_by_candidate: Mapping[str, float]
    team_score_before: float | None
    team_score_after_by_candidate: Mapping[str, float]
    championship_equity_before: float | None
    championship_equity_after_by_candidate: Mapping[str, float]
    equity_gain_by_candidate: Mapping[str, float]
    cost_of_waiting_by_candidate: Mapping[str, float]
    pick_score_by_candidate: Mapping[str, float]
    simulation_assumptions: Mapping[str, Any]
    simulation_count: int
    uncertainty: Mapping[str, float]  # e.g. {"championship_equity_standard_error": 0.03}
    selected_player: str
    decision_policy: str  # "OPTIMIZER" | "PRODUCTION_FALLBACK" | "OWNER_OVERRIDE"
    fallback_reason: str | None  # set when decision_policy == PRODUCTION_FALLBACK
    owner_override: bool
    override_reason: str | None
    factual_alerts: tuple[str, ...]
    external_comparators: Mapping[
        str, Any
    ]  # UDK/FantasyPros, logged silently, never shown pre-pick
    schema_version: int = EXPERIMENT_SCHEMA_VERSION


VALID_DECISION_POLICIES = frozenset({"OPTIMIZER", "PRODUCTION_FALLBACK", "OWNER_OVERRIDE"})
FALLBACK_REASONS = frozenset(
    {
        "INSUFFICIENT_EVIDENCE",
        "SIMULATION_FAILED",
        "IDENTITY_BLOCKED",
        "PLAYER_STATUS_BLOCKED",
        "NO_VALID_CANDIDATE",
    }
)


def _decisions_path(root: str | Path, experiment_id: str) -> Path:
    return Path(root) / "nwr_pure_experiments" / experiment_id / "decisions.jsonl"


def append_decision_receipt(root: str | Path, receipt: DecisionReceipt) -> None:
    """Append-only write. Refuses a duplicate pick_number (a correction
    to draft state must go through append_correction_record, never a
    second decision receipt claiming to BE pick N)."""
    if receipt.decision_policy not in VALID_DECISION_POLICIES:
        raise NwrPureExperimentError(f"Unknown decision_policy: {receipt.decision_policy!r}")
    if (
        receipt.decision_policy == "PRODUCTION_FALLBACK"
        and receipt.fallback_reason not in FALLBACK_REASONS
    ):
        raise NwrPureExperimentError(
            f"PRODUCTION_FALLBACK requires one of {sorted(FALLBACK_REASONS)}, "
            f"got {receipt.fallback_reason!r}"
        )
    if receipt.owner_override and not receipt.override_reason:
        raise NwrPureExperimentError("owner_override=True requires a non-empty override_reason.")
    path = _decisions_path(root, receipt.experiment_id)
    existing_pick_numbers = {
        entry["pick_number"] for entry in read_decision_receipts(root, receipt.experiment_id)
    }
    if receipt.pick_number in existing_pick_numbers:
        raise NwrPureExperimentError(
            f"Pick {receipt.pick_number} already has a decision receipt; "
            "use append_correction_record for a correction, never a second receipt "
            "for the same pick."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(receipt), sort_keys=True, separators=(",", ":")) + "\n")


def read_decision_receipts(root: str | Path, experiment_id: str) -> list[dict[str, Any]]:
    path = _decisions_path(root, experiment_id)
    if not path.is_file():
        return []
    receipts = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                receipts.append(json.loads(line))
    return receipts


@dataclass(frozen=True)
class ReceiptCorrectionRecord:
    experiment_id: str
    timestamp_utc: str
    original_pick_number: int
    reason: str
    correction_type: str  # "REPLACE_PICK" | "CLEAR_PICK" | "FILL_GAP" | "EXPERIMENT_RUNTIME_PATCH"
    detail: Mapping[str, Any]
    schema_version: int = EXPERIMENT_SCHEMA_VERSION


def _corrections_path(root: str | Path, experiment_id: str) -> Path:
    return Path(root) / "nwr_pure_experiments" / experiment_id / "corrections.jsonl"


def append_correction_record(root: str | Path, record: ReceiptCorrectionRecord) -> None:
    """Never mutates the original decision receipt line -- appends a new,
    separate record referencing it. This is the ONLY sanctioned way a
    correction (draft-state or, via EXPERIMENT_RUNTIME_PATCH,
    algorithm-runtime) is reflected in the experiment's permanent record.
    """
    path = _corrections_path(root, record.experiment_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) + "\n")


def read_correction_records(root: str | Path, experiment_id: str) -> list[dict[str, Any]]:
    path = _corrections_path(root, experiment_id)
    if not path.is_file():
        return []
    records = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# --- Pre-draft check (section 18) ---


@dataclass(frozen=True)
class PreDraftCheckResult:
    ready: bool
    checks: Mapping[str, bool]
    reasons: Mapping[str, str]  # populated only for failed checks

    @property
    def verdict(self) -> str:
        return "READY_FOR_NWR_PURE" if self.ready else "BLOCKED"


def run_pre_draft_check(
    *,
    player_universe_current: bool,
    player_universe_reason: str = "",
    projection_authority_valid: bool,
    projection_authority_reason: str = "",
    league_profile_valid: bool,
    league_profile_reason: str = "",
    roster_rules_valid: bool,
    roster_rules_reason: str = "",
    market_snapshot_available: bool,
    market_snapshot_reason: str = "",
    identity_registry_healthy: bool,
    identity_registry_reason: str = "",
    kdst_available: bool,
    kdst_reason: str = "",
    checkpoint_path_valid: bool,
    checkpoint_path_reason: str = "",
    decision_logger_writable: bool,
    decision_logger_reason: str = "",
    draft_state_writable: bool,
    draft_state_reason: str = "",
    sync_ready_or_manual_fallback_ready: bool,
    sync_reason: str = "",
) -> PreDraftCheckResult:
    """Pure aggregation -- every input is a fact the caller already
    verified elsewhere (this function invents nothing, checks nothing
    itself; it only combines already-verified booleans into one
    READY_FOR_NWR_PURE / BLOCKED verdict with reasons)."""
    checks = {
        "PLAYER_UNIVERSE_CURRENT": player_universe_current,
        "PROJECTION_AUTHORITY_VALID": projection_authority_valid,
        "LEAGUE_PROFILE_VALID": league_profile_valid,
        "ROSTER_RULES_VALID": roster_rules_valid,
        "MARKET_SNAPSHOT_AVAILABLE": market_snapshot_available,
        "IDENTITY_REGISTRY_HEALTHY": identity_registry_healthy,
        "KDST_AVAILABLE": kdst_available,
        "CHECKPOINT_PATH_VALID": checkpoint_path_valid,
        "DECISION_LOGGER_WRITABLE": decision_logger_writable,
        "DRAFT_STATE_WRITABLE": draft_state_writable,
        "SYNC_READY_OR_MANUAL_FALLBACK_READY": sync_ready_or_manual_fallback_ready,
    }
    reason_map = {
        "PLAYER_UNIVERSE_CURRENT": player_universe_reason,
        "PROJECTION_AUTHORITY_VALID": projection_authority_reason,
        "LEAGUE_PROFILE_VALID": league_profile_reason,
        "ROSTER_RULES_VALID": roster_rules_reason,
        "MARKET_SNAPSHOT_AVAILABLE": market_snapshot_reason,
        "IDENTITY_REGISTRY_HEALTHY": identity_registry_reason,
        "KDST_AVAILABLE": kdst_reason,
        "CHECKPOINT_PATH_VALID": checkpoint_path_reason,
        "DECISION_LOGGER_WRITABLE": decision_logger_reason,
        "DRAFT_STATE_WRITABLE": draft_state_reason,
        "SYNC_READY_OR_MANUAL_FALLBACK_READY": sync_reason,
    }
    reasons = {name: reason_map[name] for name, passed in checks.items() if not passed}
    return PreDraftCheckResult(ready=all(checks.values()), checks=checks, reasons=reasons)
