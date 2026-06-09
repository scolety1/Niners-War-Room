from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    build_player_feature_receipts,
)
from src.services.young_nfl_bridge_service import young_nfl_bridge_prior_from_row

NORMALIZED_FILE = "stats_first_normalized_features.csv"
OUTPUT_FILE = "stats_first_veteran_model_preview_outputs.csv"
YOUNG_BUCKETS = {
    "year_one_nfl_player",
    "year_two_nfl_player",
    "year_three_nfl_player",
}


@dataclass(frozen=True)
class YoungPlayerReviewReport:
    rows: list[dict[str, object]]
    flag_rows: list[dict[str, object]]
    summary_rows: list[dict[str, object]]
    issues: list[str]

    @property
    def has_review_flags(self) -> bool:
        return any(row["flags"] for row in self.rows)


def build_young_player_review(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
) -> YoungPlayerReviewReport:
    source_root = (
        Path(veteran_model_dir) if veteran_model_dir else DEFAULT_RECEIPT_VETERAN_MODEL_DIR
    )
    issues: list[str] = []
    normalized_path = source_root / NORMALIZED_FILE
    output_path = source_root / OUTPUT_FILE
    if not normalized_path.exists():
        return YoungPlayerReviewReport(
            rows=[],
            flag_rows=[],
            summary_rows=[],
            issues=[f"Young player review missing normalized features: {normalized_path}"],
        )

    normalized_rows = _read_csv(normalized_path)
    output_rows = _read_csv(output_path) if output_path.exists() else []
    if not output_path.exists():
        issues.append(f"Young player review missing model preview outputs: {output_path}")

    receipt_report = build_player_feature_receipts(
        data_pack_path,
        veteran_model_dir=source_root,
    )
    issues.extend(receipt_report.issues)
    output_lookup = {
        str(row.get("player_id") or ""): row for row in output_rows if row.get("player_id")
    }
    receipt_lookup = _receipt_lookup(receipt_report.rows)

    rows: list[dict[str, object]] = []
    for normalized in normalized_rows:
        bucket = str(normalized.get("experience_bucket") or "")
        if bucket not in YOUNG_BUCKETS:
            continue
        player_id = str(normalized.get("player_id") or "")
        output = output_lookup.get(player_id, {})
        prior = young_nfl_bridge_prior_from_row(normalized)
        receipt = receipt_lookup.get(player_id, {})
        flags = _flags(normalized, output, prior, receipt)
        rows.append(
            {
                "player": normalized.get("player_name", ""),
                "position": normalized.get("position", ""),
                "nfl_team": output.get("team") or normalized.get("team", ""),
                "draft_year": prior.draft_year or normalized.get("draft_year", ""),
                "draft_round": prior.draft_round or normalized.get("draft_round", ""),
                "draft_pick": prior.draft_overall
                or normalized.get("draft_overall", "")
                or normalized.get("draft_pick", ""),
                "experience_bucket": bucket,
                "rookie_prior_score": prior.rookie_prior_score,
                "bridge_weight": prior.bridge_weight,
                "nfl_evidence_weight": prior.nfl_evidence_weight,
                "bridge_contribution": receipt.get("bridge_contribution", 0.0),
                "bridge_contribution_share": receipt.get("bridge_contribution_share", 0.0),
                "private_stat_value": _float(
                    output.get("private_lve_value")
                    or output.get("private_score")
                    or normalized.get("private_stat_value"),
                ),
                "confidence": _float(
                    output.get("confidence_score") or normalized.get("confidence"),
                ),
                "warning": _warning_text(output, normalized),
                "flags": "|".join(flag["flag_type"] for flag in flags),
                "next_action": _next_action(flags),
            }
        )

    flag_rows = [
        flag_row
        for row in rows
        for flag_row in _flag_rows_for_player(row)
    ]
    return YoungPlayerReviewReport(
        rows=sorted(
            rows,
            key=lambda row: (
                -len(str(row["flags"]).split("|")) if row["flags"] else 0,
                str(row["position"]),
                str(row["player"]),
            ),
        ),
        flag_rows=sorted(
            flag_rows,
            key=lambda row: (str(row["flag_type"]), str(row["player"])),
        ),
        summary_rows=_summary_rows(rows, flag_rows),
        issues=issues,
    )


def _flags(
    normalized: dict[str, str],
    output: dict[str, str],
    prior: object,
    receipt: dict[str, float],
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    rookie_prior = _float(getattr(prior, "rookie_prior_score", 0.0))
    nfl_evidence = _float(getattr(prior, "nfl_evidence_weight", 0.0))
    bridge_weight = _float(getattr(prior, "bridge_weight", 0.0))
    private_value = _float(
        output.get("private_lve_value")
        or output.get("private_score")
        or normalized.get("private_stat_value"),
    )
    if rookie_prior >= 80.0 and nfl_evidence < 0.45:
        flags.append(
            _flag(
                "strong_prior_but_weak_nfl_evidence",
                "Strong rookie/draft prior, but current NFL production/role evidence is thin.",
                "Review receipts before trusting the rank; this may be patience, not proof.",
            )
        )
    if rookie_prior <= 55.0 and nfl_evidence >= 0.65 and private_value >= 65.0:
        flags.append(
            _flag(
                "weak_prior_but_strong_nfl_evidence",
                "Weak draft/prospect prior, but NFL evidence is already carrying value.",
                "Check whether the model found real production/usage edge.",
            )
        )
    if not (
        normalized.get("draft_year")
        or normalized.get("draft_round")
        or normalized.get("draft_overall")
        or normalized.get("draft_pick")
    ):
        flags.append(
            _flag(
                "missing_draft_capital",
                "Young NFL player is missing draft year/round/pick context.",
                "Backfill draft capital or mark the bridge prior as unavailable.",
            )
        )
    if nfl_evidence < 0.25:
        flags.append(
            _flag(
                "missing_nfl_evidence",
                "NFL evidence weight is too low for a confident young-player ranking.",
                "Backfill production, role/usage, projection, or confidence inputs.",
            )
        )
    bridge_share = _float(receipt.get("bridge_contribution_share"))
    if bridge_weight >= 0.30 or bridge_share >= 0.25:
        flags.append(
            _flag(
                "bridge_contribution_too_dominant",
                "Bridge prior is a large share of private value.",
                "Treat as review-only until NFL evidence confirms or rejects the prior.",
            )
        )
    return flags


def _flag(flag_type: str, reason: str, next_action: str) -> dict[str, str]:
    return {
        "flag_type": flag_type,
        "reason": reason,
        "next_action": next_action,
    }


def _receipt_lookup(rows: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        player_id = str(row.get("player_id") or "")
        if player_id:
            grouped.setdefault(player_id, []).append(row)

    output: dict[str, dict[str, float]] = {}
    for player_id, player_rows in grouped.items():
        private_rows = [
            row
            for row in player_rows
            if str(row.get("component") or "") == "private_lve_value"
        ]
        private_sum = sum(abs(_float(row.get("contribution"))) for row in private_rows)
        bridge_contribution = sum(
            _float(row.get("contribution"))
            for row in private_rows
            if str(row.get("formula_feature_name") or "") == "young_nfl_bridge_prior"
        )
        output[player_id] = {
            "bridge_contribution": round(bridge_contribution, 4),
            "bridge_contribution_share": round(
                abs(bridge_contribution) / private_sum if private_sum else 0.0,
                4,
            ),
        }
    return output


def _flag_rows_for_player(row: dict[str, object]) -> list[dict[str, object]]:
    flags = [flag for flag in str(row.get("flags") or "").split("|") if flag]
    return [
        {
            "player": row["player"],
            "position": row["position"],
            "nfl_team": row["nfl_team"],
            "flag_type": flag,
            "next_action": _FLAG_ACTIONS.get(flag, "Review player receipts."),
        }
        for flag in flags
    ]


def _summary_rows(
    rows: list[dict[str, object]],
    flag_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    flagged_players = {str(row["player"]) for row in rows if row["flags"]}
    summary = [
        {
            "metric": "young_players",
            "value": len(rows),
            "meaning": "Year-one, year-two, and year-three NFL players in the active model.",
        },
        {
            "metric": "flagged_players",
            "value": len(flagged_players),
            "meaning": "Young players needing receipt review before trusting the rank.",
        },
    ]
    flag_counts: dict[str, int] = {}
    for row in flag_rows:
        flag_counts[str(row["flag_type"])] = flag_counts.get(str(row["flag_type"]), 0) + 1
    for flag_type, count in sorted(flag_counts.items()):
        summary.append(
            {
                "metric": flag_type,
                "value": count,
                "meaning": _FLAG_REASONS.get(flag_type, "Review flag."),
            }
        )
    return summary


def _next_action(flags: list[dict[str, str]]) -> str:
    if not flags:
        return "No young-player review flag."
    return flags[0]["next_action"]


def _warning_text(output: dict[str, str], normalized: dict[str, str]) -> str:
    return (
        output.get("warning_reasons")
        or output.get("warning_status")
        or normalized.get("warnings")
        or ""
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


_FLAG_REASONS = {
    "strong_prior_but_weak_nfl_evidence": (
        "Strong rookie/draft prior, but current NFL production/role evidence is thin."
    ),
    "weak_prior_but_strong_nfl_evidence": (
        "Weak draft/prospect prior, but NFL evidence is already carrying value."
    ),
    "missing_draft_capital": "Young NFL player is missing draft year/round/pick context.",
    "missing_nfl_evidence": (
        "NFL evidence weight is too low for a confident young-player ranking."
    ),
    "bridge_contribution_too_dominant": (
        "Bridge prior is a large share of private value."
    ),
}

_FLAG_ACTIONS = {
    "strong_prior_but_weak_nfl_evidence": (
        "Review receipts before trusting the rank; this may be patience, not proof."
    ),
    "weak_prior_but_strong_nfl_evidence": (
        "Check whether the model found real production/usage edge."
    ),
    "missing_draft_capital": (
        "Backfill draft capital or mark the bridge prior as unavailable."
    ),
    "missing_nfl_evidence": (
        "Backfill production, role/usage, projection, or confidence inputs."
    ),
    "bridge_contribution_too_dominant": (
        "Treat as review-only until NFL evidence confirms or rejects the prior."
    ),
}
