from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IdentityJoinLookup:
    rows_by_key: dict[tuple[str, str], dict[str, Any]]
    duplicate_keys: frozenset[tuple[str, str]]
    source_name: str


@dataclass(frozen=True)
class IdentityJoinGate:
    identity_uncertain: bool
    manual_decision_required: bool
    warning_flags: tuple[str, ...]


def build_identity_join_lookup(
    rows: list[dict[str, Any]],
    *,
    source_name: str,
    name_fields: tuple[str, ...] = ("player_name", "normalized_player_name"),
    position_field: str = "position",
) -> IdentityJoinLookup:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = identity_join_key(row, name_fields=name_fields, position_field=position_field)
        if key == ("", ""):
            continue
        grouped.setdefault(key, []).append(row)
    duplicate_keys = frozenset(key for key, matches in grouped.items() if len(matches) > 1)
    rows_by_key = {key: matches[0] for key, matches in grouped.items() if key not in duplicate_keys}
    return IdentityJoinLookup(
        rows_by_key=rows_by_key,
        duplicate_keys=duplicate_keys,
        source_name=source_name,
    )


def identity_join_key(
    row: Mapping[str, Any],
    *,
    name_fields: tuple[str, ...] = ("player_name", "normalized_player_name"),
    position_field: str = "position",
) -> tuple[str, str]:
    name = ""
    for field in name_fields:
        name = normalize_identity_name(row.get(field))
        if name:
            break
    return name, str(row.get(position_field) or "").upper().strip()


def identity_join_gate(
    key: tuple[str, str],
    lookup: IdentityJoinLookup,
) -> IdentityJoinGate:
    if key in lookup.duplicate_keys:
        return IdentityJoinGate(
            identity_uncertain=True,
            manual_decision_required=True,
            warning_flags=(
                "duplicate_identity_join_key",
                f"duplicate_identity_join_source:{lookup.source_name}",
            ),
        )
    if key not in lookup.rows_by_key:
        return IdentityJoinGate(
            identity_uncertain=True,
            manual_decision_required=True,
            warning_flags=(
                "unmatched_identity_join_key",
                f"unmatched_identity_join_source:{lookup.source_name}",
            ),
        )
    return IdentityJoinGate(
        identity_uncertain=False,
        manual_decision_required=False,
        warning_flags=(),
    )


def normalize_identity_name(value: object) -> str:
    text = str(value or "").lower()
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", text)
    return re.sub(r"[^a-z0-9]", "", text)
