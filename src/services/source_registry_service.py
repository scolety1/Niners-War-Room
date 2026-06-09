from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SOURCE_REGISTRY_PATH = Path("config/source_registry.csv")

SOURCE_REGISTRY_HEADER = (
    "source_name",
    "source_table",
    "source_kind",
    "default_admissibility",
    "private_value_allowed",
    "display_only",
    "source_risk",
    "license_note",
    "allowed_model_components",
    "forbidden_model_components",
)

PRIVATE_FORBIDDEN_ADMISSIBILITY = {
    "DISPLAY_MARKET",
    "DISPLAY_PROJECTION",
    "DISPLAY_OUTCOME_CONTEXT",
    "REJECTED",
}

PRIVATE_FORBIDDEN_SOURCE_KIND_MARKERS = (
    "market",
    "projection",
    "rank",
    "mock",
    "big_board",
    "outcome_context",
)

PRIVATE_FORBIDDEN_TERM_MARKERS = (
    "adp",
    "ecr",
    "rank",
    "ranking",
    "projection",
    "projected",
    "mock",
    "big_board",
    "trade_value",
    "dynasty_value",
    "consensus",
    "expert",
    "salary",
    "betting",
)


@dataclass(frozen=True)
class SourceRegistryIssue:
    source_name: str
    source_table: str
    issue_code: str
    detail: str

    def to_row(self) -> dict[str, str]:
        return {
            "source_name": self.source_name,
            "source_table": self.source_table,
            "issue_code": self.issue_code,
            "detail": self.detail,
        }


def load_source_registry_rows(
    path: str | Path = DEFAULT_SOURCE_REGISTRY_PATH,
) -> tuple[dict[str, str], ...]:
    registry_path = Path(path)
    if not registry_path.exists():
        raise FileNotFoundError(f"Missing source registry: {registry_path}")
    with registry_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        if header != SOURCE_REGISTRY_HEADER:
            raise ValueError(f"Unexpected source registry header: {header}")
        return tuple(dict(row) for row in reader)


def source_registry_firewall_issues(
    rows: tuple[dict[str, str], ...] | None = None,
) -> tuple[dict[str, str], ...]:
    registry_rows = rows or load_source_registry_rows()
    issues: list[SourceRegistryIssue] = []
    for row in registry_rows:
        source_name = row["source_name"]
        source_table = row["source_table"]
        private_allowed = _bool(row["private_value_allowed"])
        display_only = _bool(row["display_only"])
        source_kind = row["source_kind"].lower()
        admissibility = row["default_admissibility"]
        searchable_text = " ".join(
            row[key].lower()
            for key in (
                "source_name",
                "source_table",
                "source_kind",
                "allowed_model_components",
            )
        )
        if display_only and private_allowed:
            issues.append(
                SourceRegistryIssue(
                    source_name,
                    source_table,
                    "display_only_private_value_allowed",
                    "Display-only rows cannot be private value sources.",
                )
            )
        if private_allowed and admissibility in PRIVATE_FORBIDDEN_ADMISSIBILITY:
            issues.append(
                SourceRegistryIssue(
                    source_name,
                    source_table,
                    "forbidden_admissibility_private_value_allowed",
                    f"{admissibility} cannot drive private value.",
                )
            )
        if private_allowed and any(
            marker in source_kind for marker in PRIVATE_FORBIDDEN_SOURCE_KIND_MARKERS
        ):
            issues.append(
                SourceRegistryIssue(
                    source_name,
                    source_table,
                    "forbidden_source_kind_private_value_allowed",
                    f"{row['source_kind']} cannot drive private value.",
                )
            )
        if private_allowed and any(
            marker in searchable_text for marker in PRIVATE_FORBIDDEN_TERM_MARKERS
        ):
            issues.append(
                SourceRegistryIssue(
                    source_name,
                    source_table,
                    "forbidden_term_private_value_allowed",
                    "Market, projection, rank, mock, salary, or expert term appears in a "
                    "private row.",
                )
            )
    return tuple(issue.to_row() for issue in issues)


def private_value_sources() -> tuple[dict[str, str], ...]:
    return tuple(
        row for row in load_source_registry_rows() if _bool(row["private_value_allowed"])
    )


def display_only_sources() -> tuple[dict[str, str], ...]:
    return tuple(row for row in load_source_registry_rows() if _bool(row["display_only"]))


def _bool(value: object) -> bool:
    return str(value).strip().lower() == "true"
