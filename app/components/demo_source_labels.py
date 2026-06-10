from __future__ import annotations

from pathlib import Path

KNOWN_SOURCE_LABELS = {
    "model_outputs.csv": "Active data pack: 2026 pre-draft review pack",
    "scouting_prep_pool_review_rows.csv": "Draft Prep scouting pool review rows",
    "full_player_board_value_review_rows.csv": "Full-board NWR Dynasty Rankings export",
    "current_player_value_full_board_review_rows.csv": "Model v4 full-board current value export",
    "current_player_value_review_rows.csv": "Model v4 current value checkpoint",
}


def demo_source_label(value: object, *, fallback_prefix: str = "Source file") -> str:
    """Return a demo-safe label for local source paths.

    This only changes display text. Callers must keep using the real path for reads,
    fingerprints, session keys, and exports.
    """

    text = str(value or "").strip()
    if not text:
        return "Source not loaded"

    normalized = text.replace("\\", "/")
    name = Path(normalized).name
    if name in KNOWN_SOURCE_LABELS:
        return KNOWN_SOURCE_LABELS[name]
    if "/data_packs/" in normalized or normalized.startswith("local_exports/data_packs/"):
        return "Active data pack: 2026 pre-draft review pack"
    if (
        "/local_exports/" in normalized
        or normalized.startswith("local_exports/")
        or ":" in text
    ):
        return f"{fallback_prefix}: {name or 'local source'}"
    return text
