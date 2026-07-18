from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

VALID_CURRENT = "VALID_CURRENT"
STALE = "STALE"
MISSING = "MISSING"
GATED = "GATED"
UNAVAILABLE = "UNAVAILABLE"
IDENTITY_EXCEPTION = "IDENTITY_EXCEPTION"
SOURCE_EXCEPTION = "SOURCE_EXCEPTION"
NOT_ENOUGH_INFORMATION = "NOT_ENOUGH_INFORMATION"

STATE_LABELS = {
    VALID_CURRENT: "Valid / current",
    STALE: "Stale",
    MISSING: "Missing",
    GATED: "Gated",
    UNAVAILABLE: "Unavailable",
    IDENTITY_EXCEPTION: "Identity exception",
    SOURCE_EXCEPTION: "Source exception",
    NOT_ENOUGH_INFORMATION: "Not enough information",
}

FIELD_ORDER = (
    "evidence_source",
    "as_of_freshness",
    "identity_join",
    "missingness_completeness",
    "material_caveats",
    "receipt_details",
)

FIELD_LABELS = {
    "evidence_source": "Evidence / source",
    "as_of_freshness": "As of / freshness",
    "identity_join": "Identity / join",
    "missingness_completeness": "Completeness",
    "material_caveats": "Material caveats",
    "receipt_details": "Receipts / details",
}

_BLANKS = {"", "nan", "none", "null", "n/a"}
_NOT_ENOUGH = {"not enough information", "unknown", "not available from current row"}
_WORD_PATTERN = re.compile(r"[a-z0-9]+")
_LEXICAL_NEGATIONS = {"no", "not", "never", "without"}
_NEGATED_STATUS_WORDS = {"failed", "invalid", "uncurrent", "unmatched", "unready", "unscored"}
_POSITIVE_STATUS_WORDS = {
    "available",
    "current",
    "exact",
    "green",
    "matched",
    "ready",
    "scored",
}


@dataclass(frozen=True)
class TrustStripField:
    key: str
    label: str
    state: str
    value: str
    detail: str = ""


@dataclass(frozen=True)
class DecisionTrustStrip:
    surface: str
    entity_label: str
    fields: tuple[TrustStripField, ...]
    review_only: bool = True

    def field(self, key: str) -> TrustStripField:
        return next(item for item in self.fields if item.key == key)


def state_from_existing_status(value: object, *, field: str) -> str:
    """Map existing status language for display; never calculate a new factual status."""
    if not isinstance(value, str):
        return NOT_ENOUGH_INFORMATION
    text = _text(value)
    lower = text.lower()
    words = tuple(_WORD_PATTERN.findall(lower))
    word_set = set(words)
    if lower in _BLANKS or lower in _NOT_ENOUGH:
        return NOT_ENOUGH_INFORMATION
    if field == "identity_join" and word_set & {
        "ambiguous",
        "blocked",
        "exception",
        "partial",
        "review",
        "unmatched",
        "unresolved",
    }:
        return IDENTITY_EXCEPTION
    if "gated" in word_set or _has_phrase(words, "not admitted", "blocked use"):
        return GATED
    if "stale" in word_set or _has_phrase(words, "last cache"):
        return STALE
    if "unavailable" in word_set or _has_phrase(
        words,
        "not available",
        "not currently available",
        "cannot supply",
    ):
        return UNAVAILABLE
    if word_set & {"absent", "missing"} or _has_phrase(words, "not found"):
        return MISSING
    if field in {"evidence_source", "material_caveats"} and (
        word_set & {"caveat", "conflict", "restricted", "warning"}
        or _has_phrase(words, "review only")
    ):
        return SOURCE_EXCEPTION
    if word_set & (_LEXICAL_NEGATIONS | _NEGATED_STATUS_WORDS):
        return NOT_ENOUGH_INFORMATION
    if word_set & _POSITIVE_STATUS_WORDS or _has_phrase(
        words,
        "full dynasty source",
        "admitted identifier present",
    ):
        return VALID_CURRENT
    return NOT_ENOUGH_INFORMATION


def build_decision_trust_strip(
    row: Mapping[str, object],
    *,
    surface: str,
    entity_label: str,
    receipt_label: str,
    receipt_available: bool,
) -> DecisionTrustStrip:
    source = _first(row, ("source_status", "source_coverage", "data_status", "trust_status"))
    freshness = _first(
        row, ("freshness_status", "market_freshness_status", "score_as_of_date", "as_of_date")
    )
    identity = _first(
        row,
        (
            "identity_join_status",
            "nflverse_identity_status_display_only",
            "identity_status",
            "identity_match_method",
        ),
    )
    if not identity:
        identity_value = _first(row, ("player_id", "nwr_player_id", "canonical_player_key"))
        identity = (
            "Admitted identifier present"
            if _usable_identifier(identity_value)
            else "Not enough information"
        )
    missing = _missingness_value(row)
    caveat = _first(
        row,
        (
            "identity_caveat",
            "nflverse_identity_caveat_display_only",
            "warning_flags",
            "warnings",
            "risk_manual_review_notes",
            "caveat",
        ),
    )
    fields = (
        _field("evidence_source", source),
        _field("as_of_freshness", freshness),
        _field("identity_join", identity),
        _field("missingness_completeness", missing),
        _field("material_caveats", caveat),
        TrustStripField(
            key="receipt_details",
            label=FIELD_LABELS["receipt_details"],
            state=VALID_CURRENT if receipt_available else UNAVAILABLE,
            value=receipt_label
            if receipt_available
            else "Receipt path unavailable for this context",
            detail="Uses the existing surface disclosure; no receipt is copied into this strip.",
        ),
    )
    return DecisionTrustStrip(
        surface=surface,
        entity_label=entity_label,
        fields=fields,
    )


def build_rankings_dataset_trust_strip(
    *,
    source_available: bool,
    source_label: str,
    source_hash: str,
    freshness_status: object,
    identity_review_rows: int,
    missing_rows: int,
    warnings: Sequence[str],
) -> DecisionTrustStrip:
    source = f"Available: {source_label}" if source_available else "Source unavailable"
    identity = (
        "Matched"
        if identity_review_rows == 0
        else f"Identity review required: {identity_review_rows} rows"
    )
    completeness = "Complete" if missing_rows == 0 else f"Missing evidence: {missing_rows} rows"
    caveat = " | ".join(str(item) for item in warnings if str(item).strip())
    return build_decision_trust_strip(
        {
            "source_status": source,
            "freshness_status": freshness_status,
            "identity_join_status": identity,
            "missing_evidence": completeness,
            "warnings": caveat,
        },
        surface="Dynasty Rankings",
        entity_label="Visible rankings evidence",
        receipt_label=f"Source diagnostics · SHA-256 {source_hash or 'unavailable'}",
        receipt_available=bool(source_hash),
    )


def _field(key: str, value: object) -> TrustStripField:
    text = _text(value) or "Not enough information"
    state = state_from_existing_status(value, field=key)
    if key == "missingness_completeness" and text.lower() in {"complete", "0", "0 missing"}:
        state = VALID_CURRENT
    return TrustStripField(key=key, label=FIELD_LABELS[key], state=state, value=text)


def _missingness_value(row: Mapping[str, object]) -> str:
    explicit = _first(
        row,
        (
            "missing_evidence",
            "missing_context_display",
            "missingness_status",
            "missing_score_component_count_display",
        ),
    )
    if explicit:
        try:
            count = int(float(explicit))
        except (TypeError, ValueError):
            return explicit
        return "Complete" if count == 0 else f"Missing evidence: {count}"
    return "Not enough information"


def _first(row: Mapping[str, object], keys: Sequence[str]) -> object:
    for key in keys:
        value = row.get(key, "")
        if _text(value).lower() not in _BLANKS:
            return value
    return ""


def _usable_identifier(value: object) -> bool:
    text = _text(value)
    return bool(text) and text.lower() not in _BLANKS | _NOT_ENOUGH


def _text(value: object) -> str:
    return str(value or "").strip()


def _has_phrase(words: Sequence[str], *phrases: str) -> bool:
    padded = f" {' '.join(words)} "
    return any(f" {phrase} " in padded for phrase in phrases)
