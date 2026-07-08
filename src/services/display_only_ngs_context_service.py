from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKET_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "display_only_ngs_devlab_datahealth_v1_20260707"
)

NGS_GATE = "REVIEW_ONLY_NGS_CONTEXT"
REVIEW_ONLY_WARNING = (
    "Display-only context. Not used in rankings. Not a model score. "
    "NGS public thresholds may exclude low-volume players."
)


def development_lab_ngs_rows() -> list[dict[str, str]]:
    rows = _read_csv(PACKET_DIR / "display_only_ngs_development_lab_fields.csv")
    return [
        {
            "Position": row["position_scope"],
            "Metric": row["display_label"],
            "Display mode": row["display_mode"],
            "Direction": row["directionality"],
            "Gate": row["gate"],
            "Tooltip": row["tooltip"],
            "Missingness caveat": row["missingness_caveat"],
        }
        for row in rows
        if row.get("gate") == NGS_GATE
    ]


def data_health_ngs_rows() -> list[dict[str, str]]:
    rows = _read_csv(PACKET_DIR / "display_only_ngs_data_health_fields.csv")
    return [
        {
            "Source family": row["source_family"],
            "Seasons": row["seasons_available"],
            "Source rows": row["source_rows"],
            "Unique players": row["unique_players"],
            "Safe display count": row["safe_display_count"],
            "Identity-review count": row["identity_review_count"],
            "Blocked count": row["blocked_count"],
            "Gate": row["gate"],
            "Caveat": row["public_threshold_caveat"],
        }
        for row in rows
        if row.get("gate") == NGS_GATE
    ]


def blocked_ngs_metric_rows() -> list[dict[str, str]]:
    rows = _read_csv(PACKET_DIR / "display_only_ngs_blocked_metrics_scan.csv")
    return [
        {
            "Metric or source": row["metric_or_source"],
            "Status": row["blocked_status"],
            "Runtime included": row["runtime_included"],
            "Reason": row["reason"],
        }
        for row in rows
    ]


def ngs_gate_validation_rows() -> list[dict[str, str]]:
    return _read_csv(PACKET_DIR / "display_only_ngs_gate_validation.csv")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {str(key): str(value or "") for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]
