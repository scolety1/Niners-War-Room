from __future__ import annotations

import csv
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

DEFAULT_REGISTRY_ROOT = Path("docs/hq/rookie_evidence_workspace_v1")

PURPOSES = (
    "LOCAL_RETENTION",
    "CANONICAL_HQ_SUMMARY",
    "RAW_RECEIPT_STORAGE",
    "DISPLAY",
    "RESEARCH",
    "MODEL_TRAINING",
    "PRODUCTION_SCORING",
    "REDISTRIBUTION",
    "EXPORT",
)

DECISION_VALUES = (
    "ALLOWED",
    "ALLOWED_WITH_CAVEATS",
    "REVIEW_ONLY",
    "BLOCKED",
    "NOT_ENOUGH_INFORMATION",
    "NOT_APPLICABLE",
)

BLOCKING_DECISION_VALUES = frozenset({"BLOCKED", "NOT_ENOUGH_INFORMATION"})


@dataclass(frozen=True)
class DecisionResult:
    dataset_id: str
    field_family: str
    purpose: str
    decision_value: str
    evidence_state: str
    use_decision_id: str | None
    caveat: str


@dataclass(frozen=True)
class RegistrySummary:
    artifact_count: int
    authority_count: int
    source_count: int
    dataset_count: int
    receipt_count: int
    explicit_decision_count: int
    duplicate_conflict_count: int
    no_recreate_count: int
    locality_counts: Mapping[str, int]
    evidence_state_counts: Mapping[str, int]


class RookieEvidenceRegistry:
    """Read-only access to metadata registries; never loads player evidence values."""

    def __init__(self, root: str | Path = DEFAULT_REGISTRY_ROOT) -> None:
        self.root = Path(root)
        self.registry_root = self.root / "registries"
        self._schemas = self._read_json(self.root / "governance/SCHEMAS.json")
        self._artifacts = self._read_csv(self.registry_root / "EVIDENCE_ARTIFACT_REGISTRY.csv")
        self._authorities = self._read_csv(self.registry_root / "AUTHORITY_REGISTRY.csv")
        self._sources = self._read_csv(self.registry_root / "SOURCE_REGISTRY.csv")
        self._datasets = self._read_csv(self.registry_root / "DATASET_REGISTRY.csv")
        self._receipts = self._read_csv(self.registry_root / "SOURCE_RECEIPT_REGISTRY.csv")
        self._decisions = self._read_csv(self.registry_root / "SOURCE_USE_DECISION_LEDGER.csv")
        self._duplicates = self._read_csv(
            self.root / "conflicts/DUPLICATE_CONFLICT_RELATIONSHIP_LEDGER.csv"
        )
        self._no_recreate = self._read_csv(
            self.root / "governance/NO_RECREATE_RELATIONSHIP_LEDGER.csv"
        )
        self._artifact_by_id = MappingProxyType(
            {row["artifact_id"]: row for row in self._artifacts}
        )
        self._decision_by_grain = MappingProxyType(
            {
                (
                    row["dataset_id"],
                    row["field_family"],
                    row["purpose"],
                    row["decision_version"],
                ): row
                for row in self._decisions
            }
        )

    @property
    def schemas(self) -> Mapping[str, object]:
        return MappingProxyType(self._schemas)

    def artifact(self, artifact_id: str) -> Mapping[str, str] | None:
        row = self._artifact_by_id.get(artifact_id)
        return MappingProxyType(row) if row is not None else None

    def artifacts_by_metadata(
        self,
        *,
        locality_class: str | None = None,
        evidence_state: str | None = None,
        artifact_scope_class: str | None = None,
    ) -> tuple[Mapping[str, str], ...]:
        rows = self._artifacts
        if locality_class is not None:
            rows = tuple(row for row in rows if row["locality_class"] == locality_class)
        if evidence_state is not None:
            rows = tuple(row for row in rows if row["evidence_state"] == evidence_state)
        if artifact_scope_class is not None:
            rows = tuple(row for row in rows if row["artifact_scope_class"] == artifact_scope_class)
        return tuple(MappingProxyType(row) for row in rows)

    def decision(
        self,
        *,
        dataset_id: str,
        field_family: str,
        purpose: str,
        decision_version: str = "1.0.0",
    ) -> DecisionResult:
        if purpose not in PURPOSES:
            raise ValueError(f"Unknown purpose: {purpose}")
        row = self._decision_by_grain.get((dataset_id, field_family, purpose, decision_version))
        if row is None:
            return DecisionResult(
                dataset_id=dataset_id,
                field_family=field_family,
                purpose=purpose,
                decision_value="NOT_ENOUGH_INFORMATION",
                evidence_state="SOURCE_UNADMITTED",
                use_decision_id=None,
                caveat=(
                    "No exact receipt-backed dataset × field-family × purpose decision; "
                    "permission is not inferred."
                ),
            )
        return DecisionResult(
            dataset_id=dataset_id,
            field_family=field_family,
            purpose=purpose,
            decision_value=row["decision_value"],
            evidence_state=(
                "USE_BLOCKED"
                if row["decision_value"] in BLOCKING_DECISION_VALUES
                else "CANONICAL_REVIEW_ONLY"
            ),
            use_decision_id=row["use_decision_id"],
            caveat=row["caveat_text"],
        )

    def summary(self) -> RegistrySummary:
        locality: dict[str, int] = {}
        states: dict[str, int] = {}
        for row in self._artifacts:
            locality[row["locality_class"]] = locality.get(row["locality_class"], 0) + 1
            states[row["evidence_state"]] = states.get(row["evidence_state"], 0) + 1
        return RegistrySummary(
            artifact_count=len(self._artifacts),
            authority_count=len(self._authorities),
            source_count=len(self._sources),
            dataset_count=len(self._datasets),
            receipt_count=len(self._receipts),
            explicit_decision_count=len(self._decisions),
            duplicate_conflict_count=len(self._duplicates),
            no_recreate_count=len(self._no_recreate),
            locality_counts=MappingProxyType(dict(sorted(locality.items()))),
            evidence_state_counts=MappingProxyType(dict(sorted(states.items()))),
        )

    @staticmethod
    def _read_csv(path: Path) -> tuple[dict[str, str], ...]:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return tuple(dict(row) for row in csv.DictReader(handle))

    @staticmethod
    def _read_json(path: Path) -> dict[str, object]:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object: {path}")
        return value


def narrower_blocker_wins(
    *,
    family_default: str,
    dataset_decision: str | None = None,
    field_decision: str | None = None,
    purpose_decision: str | None = None,
    legal_or_privacy_blocked: bool = False,
) -> str:
    """Resolve only restriction precedence; never turns missing metadata into permission."""

    candidates = (purpose_decision, field_decision, dataset_decision, family_default)
    if legal_or_privacy_blocked:
        return "BLOCKED"
    for index, value in enumerate(candidates):
        if value is None:
            continue
        if value not in DECISION_VALUES:
            raise ValueError(f"Unknown decision value: {value}")
        if value in BLOCKING_DECISION_VALUES or value in {
            "REVIEW_ONLY",
            "NOT_APPLICABLE",
        }:
            return value
        # An allowed narrower row is explicit only at its own grain. Continue solely when
        # it is the purpose decision; broad allowed values never expand a missing purpose.
        if value in {"ALLOWED", "ALLOWED_WITH_CAVEATS"}:
            return value if index == 0 else "NOT_ENOUGH_INFORMATION"
    return "NOT_ENOUGH_INFORMATION"
