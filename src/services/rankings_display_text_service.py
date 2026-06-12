from __future__ import annotations

import ast

SAFE_DATA_NEEDED_LABELS = {
    "missing model v4 current player row": "Needs data",
    "missing_model_v4_current_player_row": "Needs data",
    "need a current model v4 private score row": "Needs data",
    "unmatched identity join key": "Identity match needed",
    "unmatched_identity_join_key": "Identity match needed",
    "duplicate identity join key": "Identity match needed",
    "duplicate_identity_join_key": "Identity match needed",
    "team mismatch or missing model team": "Data review",
    "team_mismatch_or_missing_model_team": "Data review",
    "missing score disclosure fields": "Data review",
    "missing_score_disclosure_fields": "Data review",
}


def safe_data_needed_items(value: object) -> list[str]:
    """Convert raw diagnostic values into compact product-facing labels."""
    raw_items = _split_data_needed(value)
    safe_items = [_safe_data_needed_label(item) for item in raw_items]
    return list(dict.fromkeys(item for item in safe_items if item))


def _split_data_needed(value: object) -> list[str]:
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "none", "null", "n/a"}:
        return []
    if "|" in text:
        return [part.strip() for part in text.split("|") if part.strip()]
    if text[:1] in {"[", "(", "{"} and text[-1:] in {"]", ")", "}"}:
        try:
            parsed = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            parsed = None
        if isinstance(parsed, (list, tuple, set)):
            return [str(part).strip() for part in parsed if str(part).strip()]
    return [text]


def _safe_data_needed_label(value: object) -> str:
    text = str(value or "").strip().strip("'\"")
    normalized = " ".join(text.replace("_", " ").lower().split())
    if not normalized:
        return ""
    if normalized.endswith(" more") and normalized.split(" ", 1)[0].isdigit():
        return ""
    if normalized in SAFE_DATA_NEEDED_LABELS:
        return SAFE_DATA_NEEDED_LABELS[normalized]
    if "identity join" in normalized:
        return "Identity match needed"
    if "missing" in normalized or "source" in normalized or "lineage" in normalized:
        return "Data review"
    return text
