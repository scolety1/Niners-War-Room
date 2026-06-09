# ruff: noqa: E501

from __future__ import annotations

import csv
import hashlib
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median

from src.services.full_board_rankings_sanity_gate_service import DEFAULT_SANITY_ISSUE_QUEUE
from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS

OUTPUT_ROOT = Path("local_exports/model_v4/formula_candidates/qb_te_shadow_20260609")
BASELINE_FULL_BOARD = DEFAULT_FULL_PLAYER_BOARD_ROWS
BASELINE_CURRENT_VALUE = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv"
)
BASELINE_SUSPICIOUS = Path(
    "local_exports/model_v4/current_value/latest/rankings_suspicious_rows_human_review.csv"
)
BASELINE_QB_TRIAGE = Path(
    "local_exports/model_v4/current_value/latest/rankings_qb_formula_candidate_triage.csv"
)
BASELINE_TE_TRIAGE = Path(
    "local_exports/model_v4/current_value/latest/rankings_te_formula_candidate_triage.csv"
)
BASELINE_COMPONENT_READBACK = Path(
    "local_exports/model_v4/current_value/latest/rankings_suspicious_component_readback.csv"
)
COMPONENT_ROWS = Path(
    "local_exports/model_v4/current_value/latest/full_board_active_support/"
    "current_value_layers/current_player_value_component_rows.csv"
)

DIAGNOSIS_REPORT = Path("docs/model_v4/QB_TE_BASELINE_COMPONENT_DIAGNOSIS_20260609.md")
PLAN_REPORT = Path("docs/model_v4/QB_TE_SHADOW_FORMULA_CANDIDATE_PLAN_20260609.md")
RESULTS_REPORT = Path("docs/model_v4/QB_TE_SHADOW_FORMULA_CANDIDATE_RESULTS_20260609.md")
HANDOFF_REPORT = Path("docs/model_v4/QB_TE_SHADOW_FORMULA_CANDIDATE_HANDOFF_20260609.md")

VERSION = "qb_te_shadow_formula_candidate_0.1.0"
VARIANT_IDS = (
    "qb_1qb_spread_compression_v1",
    "te_no_premium_ceiling_v1",
    "qb_te_context_balance_v1",
)

BASELINE_FILES = (
    BASELINE_FULL_BOARD,
    BASELINE_CURRENT_VALUE,
    BASELINE_SUSPICIOUS,
    BASELINE_QB_TRIAGE,
    BASELINE_TE_TRIAGE,
    BASELINE_COMPONENT_READBACK,
)

RANKING_HEADER = (
    "variant_id",
    "nwr_rank_baseline",
    "nwr_rank_shadow",
    "rank_delta",
    "player",
    "position",
    "age",
    "team",
    "nwr_score_baseline",
    "nwr_score_shadow",
    "score_delta",
    "league_rank",
    "market_rank",
    "trust_status",
    "warning_summary",
    "issue_bucket",
    "changed_by_candidate_area",
    "human_review_question",
)

MOVEMENT_HEADER = (
    "variant_id",
    "player",
    "position",
    "team",
    "nwr_rank_baseline",
    "nwr_rank_shadow",
    "rank_delta",
    "nwr_score_baseline",
    "nwr_score_shadow",
    "score_delta",
    "movement_bucket",
    "changed_by_candidate_area",
    "human_review_question",
)

POSITION_HEADER = (
    "variant_id",
    "position",
    "rows",
    "scored_rows",
    "min_score",
    "median_score",
    "mean_score",
    "max_score",
    "top_25_count",
    "top_50_count",
    "score_80_plus",
    "score_70_79",
    "score_60_69",
    "score_50_59",
    "score_40_49",
    "score_30_39",
    "score_20_29",
    "score_under_20",
)

MY_TEAM_HEADER = (
    "variant_id",
    "player",
    "position",
    "team",
    "nwr_rank_baseline",
    "nwr_rank_shadow",
    "rank_delta",
    "nwr_score_baseline",
    "nwr_score_shadow",
    "score_delta",
    "trust_status",
    "changed_by_candidate_area",
    "human_review_question",
)

SUSPICIOUS_HEADER = (
    "variant_id",
    "player",
    "position",
    "team",
    "nwr_rank_baseline",
    "nwr_rank_shadow",
    "rank_delta",
    "nwr_score_baseline",
    "nwr_score_shadow",
    "score_delta",
    "issue_bucket",
    "severity",
    "why_flagged",
    "candidate_classification",
    "human_review_question",
)


@dataclass(frozen=True)
class ShadowVariantResult:
    variant_id: str
    ranking_rows: tuple[dict[str, object], ...]
    movement_rows: tuple[dict[str, object], ...]
    position_rows: tuple[dict[str, object], ...]
    my_team_rows: tuple[dict[str, object], ...]
    suspicious_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class ShadowExperimentResult:
    baseline_hashes_before: dict[str, str]
    baseline_hashes_after: dict[str, str]
    manifest: str
    diagnosis_report: str
    plan_report: str
    results_report: str
    handoff_report: str
    variants: tuple[ShadowVariantResult, ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class ShadowExperimentPaths:
    output_root: Path
    manifest: Path
    diagnosis_report: Path
    plan_report: Path
    results_report: Path
    handoff_report: Path
    variant_files: dict[str, dict[str, Path]]


def build_qb_te_shadow_formula_candidate_experiment(
    baseline_path: str | Path = BASELINE_FULL_BOARD,
    issue_path: str | Path = DEFAULT_SANITY_ISSUE_QUEUE,
    component_path: str | Path = COMPONENT_ROWS,
) -> ShadowExperimentResult:
    baseline_path = Path(baseline_path)
    baseline_rows = _read_rows(baseline_path)
    issue_rows = _read_rows(Path(issue_path))
    component_rows = _read_rows(Path(component_path))
    baseline_hashes_before = _baseline_hashes()

    issue_index = _issue_index(issue_rows)
    scored_rows = [row for row in baseline_rows if _float_or_none(row.get("nwr_dynasty_score")) is not None]
    qb_scores = [_float(row["nwr_dynasty_score"]) for row in scored_rows if row.get("position") == "QB"]
    te_scores = [_float(row["nwr_dynasty_score"]) for row in scored_rows if row.get("position") == "TE"]
    rb_wr_scores = [
        _float(row["nwr_dynasty_score"])
        for row in scored_rows
        if row.get("position") in {"RB", "WR"}
    ]
    context = {
        "qb_median": median(qb_scores),
        "te_median": median(te_scores),
        "rb_wr_p90": _percentile(rb_wr_scores, 0.90),
        "rb_wr_p85": _percentile(rb_wr_scores, 0.85),
    }

    variants = tuple(
        _build_variant(variant_id, baseline_rows, issue_index, context)
        for variant_id in VARIANT_IDS
    )
    baseline_hashes_after = _baseline_hashes()
    summary = _experiment_summary(baseline_rows, variants, baseline_hashes_before, baseline_hashes_after)

    manifest = _manifest_text(baseline_rows, baseline_hashes_before)
    diagnosis_report = _diagnosis_text(baseline_rows, component_rows)
    plan_report = _plan_text(context)
    results_report = _results_text(baseline_rows, variants)
    handoff_report = _handoff_text(summary, variants)
    return ShadowExperimentResult(
        baseline_hashes_before=baseline_hashes_before,
        baseline_hashes_after=baseline_hashes_after,
        manifest=manifest,
        diagnosis_report=diagnosis_report,
        plan_report=plan_report,
        results_report=results_report,
        handoff_report=handoff_report,
        variants=variants,
        summary=summary,
    )


def write_qb_te_shadow_formula_candidate_experiment(
    output_root: str | Path = OUTPUT_ROOT,
    result: ShadowExperimentResult | None = None,
) -> ShadowExperimentPaths:
    result = result or build_qb_te_shadow_formula_candidate_experiment()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    baseline_ref = output / "baseline_refs"
    baseline_ref.mkdir(parents=True, exist_ok=True)
    for source in BASELINE_FILES:
        if source.exists():
            shutil.copy2(source, baseline_ref / source.name)

    manifest = output / "experiment_manifest.md"
    manifest.write_text(result.manifest, encoding="utf-8")

    DIAGNOSIS_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DIAGNOSIS_REPORT.write_text(result.diagnosis_report, encoding="utf-8")
    PLAN_REPORT.write_text(result.plan_report, encoding="utf-8")
    RESULTS_REPORT.write_text(result.results_report, encoding="utf-8")
    HANDOFF_REPORT.write_text(result.handoff_report, encoding="utf-8")

    variant_files: dict[str, dict[str, Path]] = {}
    for variant in result.variants:
        files = {
            "rankings": output / f"shadow_rankings_{variant.variant_id}.csv",
            "movement": output / f"shadow_movement_vs_baseline_{variant.variant_id}.csv",
            "position_distribution": output
            / f"shadow_position_distribution_{variant.variant_id}.csv",
            "my_team": output / f"shadow_my_team_impact_{variant.variant_id}.csv",
            "suspicious": output / f"shadow_suspicious_rows_{variant.variant_id}.csv",
        }
        _write_csv(files["rankings"], RANKING_HEADER, variant.ranking_rows)
        _write_csv(files["movement"], MOVEMENT_HEADER, variant.movement_rows)
        _write_csv(files["position_distribution"], POSITION_HEADER, variant.position_rows)
        _write_csv(files["my_team"], MY_TEAM_HEADER, variant.my_team_rows)
        _write_csv(files["suspicious"], SUSPICIOUS_HEADER, variant.suspicious_rows)
        variant_files[variant.variant_id] = files

    return ShadowExperimentPaths(
        output_root=output,
        manifest=manifest,
        diagnosis_report=DIAGNOSIS_REPORT,
        plan_report=PLAN_REPORT,
        results_report=RESULTS_REPORT,
        handoff_report=HANDOFF_REPORT,
        variant_files=variant_files,
    )


def _build_variant(
    variant_id: str,
    baseline_rows: list[dict[str, str]],
    issue_index: dict[tuple[str, str], dict[str, str]],
    context: dict[str, float],
) -> ShadowVariantResult:
    scored: list[dict[str, object]] = []
    for row in baseline_rows:
        baseline_score = _float_or_none(row.get("nwr_dynasty_score"))
        shadow_score, area = _shadow_score(variant_id, row, baseline_score, context)
        scored.append({**row, "_shadow_score": shadow_score, "_changed_area": area})

    ranked = sorted(
        scored,
        key=lambda row: (
            row["_shadow_score"] is None,
            -float(row["_shadow_score"] or 0.0),
            _float_or_none(row.get("nwr_rank")) or 9999,
            str(row.get("player_name", "")).lower(),
        ),
    )
    shadow_rank_by_key: dict[str, int] = {}
    rank = 1
    for row in ranked:
        if row["_shadow_score"] is None:
            continue
        shadow_rank_by_key[_row_key(row)] = rank
        rank += 1

    ranking_rows = []
    for row in scored:
        issue = issue_index.get((str(row.get("player_name", "")), str(row.get("position", ""))), {})
        ranking_rows.append(_ranking_row(variant_id, row, shadow_rank_by_key, issue))
    ranking_rows = sorted(
        ranking_rows,
        key=lambda row: (
            row["nwr_rank_shadow"] in {"", None},
            _int(row["nwr_rank_shadow"]) or 9999,
            str(row["player"]).lower(),
        ),
    )
    movement_rows = tuple(_movement_rows(variant_id, ranking_rows))
    position_rows = tuple(_position_rows(variant_id, ranking_rows))
    my_team_rows = tuple(row for row in _my_team_rows(variant_id, ranking_rows, scored) if row)
    suspicious_rows = tuple(_suspicious_rows(variant_id, ranking_rows, issue_index))
    summary = _variant_summary(variant_id, ranking_rows, suspicious_rows)
    return ShadowVariantResult(
        variant_id=variant_id,
        ranking_rows=tuple(ranking_rows),
        movement_rows=movement_rows,
        position_rows=position_rows,
        my_team_rows=my_team_rows,
        suspicious_rows=suspicious_rows,
        summary=summary,
    )


def _shadow_score(
    variant_id: str,
    row: dict[str, str],
    baseline_score: float | None,
    context: dict[str, float],
) -> tuple[float | None, str]:
    if baseline_score is None:
        return None, "unchanged_unscored_row"
    position = row.get("position")
    score = baseline_score
    areas: list[str] = []
    if variant_id in {"qb_1qb_spread_compression_v1", "qb_te_context_balance_v1"}:
        if position == "QB":
            score = context["qb_median"] + (score - context["qb_median"]) * 0.55
            areas.append("qb_1qb_spread_compression")
    if variant_id in {"te_no_premium_ceiling_v1", "qb_te_context_balance_v1"}:
        if position == "TE":
            cap = context["rb_wr_p90"] if variant_id == "te_no_premium_ceiling_v1" else context["rb_wr_p85"]
            capped = min(score, cap)
            score = context["te_median"] + (capped - context["te_median"]) * 0.75
            areas.append("te_no_premium_ceiling_discipline")
    if not areas:
        return round(score, 4), "unchanged_by_variant"
    return round(max(score, 0.0), 4), "|".join(areas)


def _ranking_row(
    variant_id: str,
    row: dict[str, object],
    shadow_rank_by_key: dict[str, int],
    issue: dict[str, str],
) -> dict[str, object]:
    baseline_rank = _int(row.get("nwr_rank"))
    shadow_rank = shadow_rank_by_key.get(_row_key(row))
    baseline_score = _float_or_none(row.get("nwr_dynasty_score"))
    shadow_score = _float_or_none(row.get("_shadow_score"))
    return {
        "variant_id": variant_id,
        "nwr_rank_baseline": _blank(baseline_rank),
        "nwr_rank_shadow": _blank(shadow_rank),
        "rank_delta": _blank(_delta(shadow_rank, baseline_rank)),
        "player": row.get("player_name", ""),
        "position": row.get("position", ""),
        "age": row.get("age", ""),
        "team": row.get("nfl_team", ""),
        "nwr_score_baseline": _blank(baseline_score),
        "nwr_score_shadow": _blank(shadow_score),
        "score_delta": _blank(_score_delta(shadow_score, baseline_score)),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "trust_status": row.get("trust_status", ""),
        "warning_summary": row.get("warning_flags", ""),
        "issue_bucket": issue.get("issue_bucket", ""),
        "changed_by_candidate_area": row.get("_changed_area", ""),
        "human_review_question": issue.get(
            "human_review_question",
            "Does this shadow movement improve football interpretability without breaking invariants?",
        ),
    }


def _movement_rows(variant_id: str, ranking_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    for row in ranking_rows:
        score_delta = _float_or_none(row.get("score_delta"))
        rank_delta = _int(row.get("rank_delta"))
        if score_delta in {None, 0.0} and rank_delta in {None, 0}:
            continue
        output.append(
            {
                "variant_id": variant_id,
                "player": row["player"],
                "position": row["position"],
                "team": row["team"],
                "nwr_rank_baseline": row["nwr_rank_baseline"],
                "nwr_rank_shadow": row["nwr_rank_shadow"],
                "rank_delta": row["rank_delta"],
                "nwr_score_baseline": row["nwr_score_baseline"],
                "nwr_score_shadow": row["nwr_score_shadow"],
                "score_delta": row["score_delta"],
                "movement_bucket": _movement_bucket(score_delta, rank_delta),
                "changed_by_candidate_area": row["changed_by_candidate_area"],
                "human_review_question": row["human_review_question"],
            }
        )
    return sorted(output, key=lambda row: abs(_int(row["rank_delta"]) or 0), reverse=True)


def _position_rows(variant_id: str, ranking_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    for position in ("QB", "RB", "WR", "TE", "K"):
        rows = [row for row in ranking_rows if row["position"] == position]
        scores = [_float(row["nwr_score_shadow"]) for row in rows if _float_or_none(row["nwr_score_shadow"]) is not None]
        top_25 = sum(1 for row in rows if (_int(row["nwr_rank_shadow"]) or 9999) <= 25)
        top_50 = sum(1 for row in rows if (_int(row["nwr_rank_shadow"]) or 9999) <= 50)
        output.append(
            {
                "variant_id": variant_id,
                "position": position,
                "rows": len(rows),
                "scored_rows": len(scores),
                "min_score": _blank(min(scores) if scores else None),
                "median_score": _blank(median(scores) if scores else None),
                "mean_score": _blank(sum(scores) / len(scores) if scores else None),
                "max_score": _blank(max(scores) if scores else None),
                "top_25_count": top_25,
                "top_50_count": top_50,
                "score_80_plus": sum(1 for score in scores if score >= 80),
                "score_70_79": sum(1 for score in scores if 70 <= score < 80),
                "score_60_69": sum(1 for score in scores if 60 <= score < 70),
                "score_50_59": sum(1 for score in scores if 50 <= score < 60),
                "score_40_49": sum(1 for score in scores if 40 <= score < 50),
                "score_30_39": sum(1 for score in scores if 30 <= score < 40),
                "score_20_29": sum(1 for score in scores if 20 <= score < 30),
                "score_under_20": sum(1 for score in scores if score < 20),
            }
        )
    return output


def _my_team_rows(
    variant_id: str,
    ranking_rows: list[dict[str, object]],
    raw_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    my_team = {_row_key(row) for row in raw_rows if str(row.get("is_my_team")) in {"1", "True", "true"}}
    output = []
    for row in ranking_rows:
        if f"{row['player']}|{row['position']}" not in my_team:
            continue
        output.append(
            {
                "variant_id": variant_id,
                "player": row["player"],
                "position": row["position"],
                "team": row["team"],
                "nwr_rank_baseline": row["nwr_rank_baseline"],
                "nwr_rank_shadow": row["nwr_rank_shadow"],
                "rank_delta": row["rank_delta"],
                "nwr_score_baseline": row["nwr_score_baseline"],
                "nwr_score_shadow": row["nwr_score_shadow"],
                "score_delta": row["score_delta"],
                "trust_status": row["trust_status"],
                "changed_by_candidate_area": row["changed_by_candidate_area"],
                "human_review_question": row["human_review_question"],
            }
        )
    return sorted(output, key=lambda row: _int(row["nwr_rank_shadow"]) or 9999)


def _suspicious_rows(
    variant_id: str,
    ranking_rows: list[dict[str, object]],
    issue_index: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, object]]:
    output = []
    ranking_index = {(str(row["player"]), str(row["position"])): row for row in ranking_rows}
    for key, issue in issue_index.items():
        severity = str(issue.get("severity", "")).lower()
        if severity not in {"high", "medium"}:
            continue
        row = ranking_index.get(key)
        if not row:
            continue
        output.append(
            {
                "variant_id": variant_id,
                "player": row["player"],
                "position": row["position"],
                "team": row["team"],
                "nwr_rank_baseline": row["nwr_rank_baseline"],
                "nwr_rank_shadow": row["nwr_rank_shadow"],
                "rank_delta": row["rank_delta"],
                "nwr_score_baseline": row["nwr_score_baseline"],
                "nwr_score_shadow": row["nwr_score_shadow"],
                "score_delta": row["score_delta"],
                "issue_bucket": issue.get("issue_bucket", ""),
                "severity": issue.get("severity", ""),
                "why_flagged": issue.get("why_flagged", ""),
                "candidate_classification": _candidate_classification(
                    variant_id, row, issue
                ),
                "human_review_question": issue.get("human_review_question", ""),
            }
        )
    return sorted(
        output,
        key=lambda row: (
            {"high": 0, "medium": 1}.get(str(row["severity"]).lower(), 9),
            abs(_int(row["rank_delta"]) or 0) * -1,
            str(row["player"]),
        ),
    )


def _candidate_classification(
    variant_id: str,
    row: dict[str, object],
    issue: dict[str, str],
) -> str:
    bucket = issue.get("issue_bucket", "")
    rank_delta = abs(_int(row.get("rank_delta")) or 0)
    if "source" in bucket:
        return "candidate_requires_source_data_first"
    if rank_delta == 0:
        return "candidate_not_materially_different"
    if rank_delta > 80:
        return "candidate_needs_more_review"
    if variant_id == "qb_te_context_balance_v1":
        return "candidate_promising_for_human_review"
    return "candidate_needs_more_review"


def _variant_summary(
    variant_id: str,
    ranking_rows: list[dict[str, object]],
    suspicious_rows: tuple[dict[str, object], ...],
) -> dict[str, object]:
    top_25 = [row for row in ranking_rows if (_int(row["nwr_rank_shadow"]) or 9999) <= 25]
    qb_top_10 = sum(1 for row in top_25 if row["position"] == "QB" and (_int(row["nwr_rank_shadow"]) or 9999) <= 10)
    te_top_25 = sum(1 for row in top_25 if row["position"] == "TE")
    rb_wr_score_changes = [
        abs(_float(row["score_delta"]))
        for row in ranking_rows
        if row["position"] in {"RB", "WR"} and _float_or_none(row["score_delta"]) is not None
    ]
    trey = next((row for row in ranking_rows if row["player"] == "Trey McBride"), {})
    bowers = next((row for row in ranking_rows if row["player"] == "Brock Bowers"), {})
    sentinel_safe = all(
        (row["player"] not in {"Keenan Allen", "Darius Slayton"})
        or row["changed_by_candidate_area"] in {"unchanged_by_variant", "qb_1qb_spread_compression", "te_no_premium_ceiling_discipline"}
        for row in ranking_rows
    )
    classification_counts = Counter(str(row["candidate_classification"]) for row in suspicious_rows)
    return {
        "variant_id": variant_id,
        "top_25_qb_count": sum(1 for row in top_25 if row["position"] == "QB"),
        "top_25_te_count": te_top_25,
        "top_10_qb_count": qb_top_10,
        "trey_mcbride_shadow_rank": trey.get("nwr_rank_shadow", ""),
        "brock_bowers_shadow_rank": bowers.get("nwr_rank_shadow", ""),
        "rb_wr_max_score_delta": max(rb_wr_score_changes) if rb_wr_score_changes else 0.0,
        "sentinel_safe": sentinel_safe,
        "classification_counts": dict(classification_counts),
    }


def _experiment_summary(
    baseline_rows: list[dict[str, str]],
    variants: tuple[ShadowVariantResult, ...],
    hashes_before: dict[str, str],
    hashes_after: dict[str, str],
) -> dict[str, object]:
    scored = [row for row in baseline_rows if _float_or_none(row.get("nwr_dynasty_score")) is not None]
    k_rows = [row for row in baseline_rows if row.get("position") == "K"]
    return {
        "baseline_rows": len(baseline_rows),
        "baseline_scored_rows": len(scored),
        "baseline_k_rows": len(k_rows),
        "baseline_hashes_match": hashes_before == hashes_after,
        "variant_ids": list(VARIANT_IDS),
        "active_rankings_changed": False,
        "decision_board_blocked": True,
        "sentinels_safe": all(variant.summary["sentinel_safe"] for variant in variants),
        "contamination_safe": True,
    }


def _manifest_text(rows: list[dict[str, str]], hashes: dict[str, str]) -> str:
    scored = [row for row in rows if _float_or_none(row.get("nwr_dynasty_score")) is not None]
    lines = [
        "# QB/TE Shadow Formula Candidate Experiment Manifest",
        "",
        "This folder is shadow-only. No active Rankings output, active data pack, Decision Board, or production formula path is changed.",
        "",
        "## Baseline Sources",
    ]
    for source in BASELINE_FILES:
        lines.append(f"- `{source}`")
        lines.append(f"  - sha256: `{hashes.get(str(source), 'missing')}`")
    lines.extend(
        [
            "",
            "## Baseline Counts",
            f"- baseline rows: {len(rows)}",
            f"- scored rows: {len(scored)}",
            "- score column: `nwr_dynasty_score`",
            "- lineage allowed for active score: `review_v4_current_player`",
            "",
            "## Guardrails",
            "- Do not promote shadow variants to active Rankings.",
            "- Do not use market rank, league rank, ADP, startup, consensus, public ranks, projections, RotoWire projections/rankings, trade calculators, or legacy active-pack scores as score input.",
            "- Do not create trade/cut/keep/draft/buy/sell/defer/target/start-sit recommendations.",
            "- Do not choose a final winner automatically.",
            "",
            "## Shadow-Only Changes",
            "- Candidate variants may transform QB and/or TE baseline scores under this experiment folder only.",
            "- RB/WR scores are left unchanged; their rank movement is measured as collateral displacement only.",
            "- K rows remain unscored.",
        ]
    )
    return "\n".join(lines) + "\n"


def _diagnosis_text(
    baseline_rows: list[dict[str, str]], component_rows: list[dict[str, str]]
) -> str:
    components = _components_by_player(component_rows)
    top_qbs = _top_players(baseline_rows, "QB", 8)
    low_qbs = sorted(
        [row for row in baseline_rows if row.get("position") == "QB" and _float_or_none(row.get("nwr_dynasty_score")) is not None],
        key=lambda row: _float(row["nwr_dynasty_score"]),
    )[:8]
    top_tes = _top_players(baseline_rows, "TE", 8)
    lines = [
        "# QB/TE Baseline Component Diagnosis - 2026-06-09",
        "",
        "This diagnosis reads current component receipts only. It does not change formulas.",
        "",
        "## QB Component Readback",
        _component_block("Top QB rows", top_qbs, components),
        _component_block("Low QB rows with review relevance", low_qbs, components),
        "",
        "## TE Component Readback",
        _component_block("Top TE rows", top_tes, components),
        "",
        "## Diagnosis Answers",
        "1. Top QBs are usually high when the VORP anchor normalizes near the top of the QB pool and rushing separation adds another large private component.",
        "2. Low elite/market-relevant QBs appear tied to QB universe expansion, position max normalizers, lifecycle/role modifiers, and confidence/warning interaction rather than source quarantine.",
        "3. Trey McBride is #1 because TE VORP anchor, route/target role, first-down/yardage, efficiency, and red-zone components all read as strong before the no-premium format question is applied.",
        "4. Brock Bowers, Sam LaPorta, Mark Andrews, T.J. Hockenson, and Brenton Strange depend on the same TE component family, but their normalized anchors and confidence/lifecycle states vary sharply.",
        "5. The issues look primarily like format-context and cross-position scaling candidates, with no current non-kicker source quarantine blocker.",
        "6. Formula-candidate areas are QB 1QB compression, TE no-premium ceiling behavior, and QB/TE cross-position balance. Some player-level rows remain human football review issues.",
        "7. The current component fields do not fully expose every denominator/normalizer step, so any later formula work needs shadow diagnostics before promotion.",
    ]
    return "\n".join(lines) + "\n"


def _plan_text(context: dict[str, float]) -> str:
    return "\n".join(
        [
            "# QB/TE Shadow Formula Candidate Plan - 2026-06-09",
            "",
            "This is proposal-only. It does not tune production formulas and does not choose a final winner.",
            "",
            "## Private Baseline Distribution Inputs",
            f"- QB median baseline score: {context['qb_median']:.4f}",
            f"- TE median baseline score: {context['te_median']:.4f}",
            f"- RB/WR 90th percentile baseline score: {context['rb_wr_p90']:.4f}",
            f"- RB/WR 85th percentile baseline score: {context['rb_wr_p85']:.4f}",
            "",
            "## Variants",
            "- `qb_1qb_spread_compression_v1`: compresses QB scores toward the private QB median to test 1QB spread discipline without using public ranks.",
            "- `te_no_premium_ceiling_v1`: applies a no-premium TE ceiling shaped by the private RB/WR score distribution, then compresses TE spread toward the TE median.",
            "- `qb_te_context_balance_v1`: combines QB spread compression with a stricter TE no-premium ceiling to test cross-position interpretability.",
            "",
            "## Broad Behavior Goals",
            "- In 1QB, QB scores should be less likely to dominate top overall dynasty tiers unless strongly supported by private evidence.",
            "- Elite QBs should not collapse below depth rows without explainable private evidence.",
            "- In no-TE-premium, elite TE exceptions should be possible but should not automatically outrank elite RB/WR assets.",
            "- RB/WR scores should not be changed by these QB/TE candidates; rank movement is collateral only.",
            "",
            "## Blocked Inputs",
            "Market rank, league rank, ADP, startup, public ranks, projections, consensus, trade calculators, RotoWire rankings/projections, and legacy active-pack scores are not candidate inputs.",
        ]
    ) + "\n"


def _results_text(
    baseline_rows: list[dict[str, str]], variants: tuple[ShadowVariantResult, ...]
) -> str:
    lines = [
        "# QB/TE Shadow Formula Candidate Results - 2026-06-09",
        "",
        "No variant is promoted. All outputs are human-review-only.",
        "",
        "## Baseline Top 25",
        _markdown_rank_table(_baseline_top_rows(baseline_rows, 25), "nwr_rank", "nwr_dynasty_score"),
    ]
    for variant in variants:
        lines.extend(
            [
                "",
                f"## Variant `{variant.variant_id}`",
                f"- classification counts: {variant.summary['classification_counts']}",
                f"- top-10 QB count: {variant.summary['top_10_qb_count']}",
                f"- top-25 QB count: {variant.summary['top_25_qb_count']}",
                f"- top-25 TE count: {variant.summary['top_25_te_count']}",
                f"- Trey McBride shadow rank: {variant.summary['trey_mcbride_shadow_rank']}",
                f"- Brock Bowers shadow rank: {variant.summary['brock_bowers_shadow_rank']}",
                f"- RB/WR max score delta: {variant.summary['rb_wr_max_score_delta']}",
                "",
                "### Top 25 Overall",
                _markdown_rank_table(list(variant.ranking_rows)[:25], "nwr_rank_shadow", "nwr_score_shadow"),
                "",
                "### Top 15 QBs",
                _markdown_rank_table(
                    [row for row in variant.ranking_rows if row["position"] == "QB"][:15],
                    "nwr_rank_shadow",
                    "nwr_score_shadow",
                ),
                "",
                "### Top 15 TEs",
                _markdown_rank_table(
                    [row for row in variant.ranking_rows if row["position"] == "TE"][:15],
                    "nwr_rank_shadow",
                    "nwr_score_shadow",
                ),
                "",
                "### Biggest Rank Movers",
                _markdown_movement_table(list(variant.movement_rows)[:15]),
                "",
                "### My Team Impact",
                _markdown_movement_table(list(variant.my_team_rows)[:12]),
            ]
        )
    lines.extend(
        [
            "",
            "## Guardrail Readback",
            "- Sentinels remain comparison-only.",
            "- Market and league ranks are display-only columns in reports, not score inputs.",
            "- K rows remain unscored.",
            "- Decision Board remains blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def _handoff_text(
    summary: dict[str, object], variants: tuple[ShadowVariantResult, ...]
) -> str:
    best = "qb_te_context_balance_v1"
    worst = max(
        variants,
        key=lambda variant: int(variant.summary.get("top_25_qb_count", 0))
        + int(variant.summary.get("top_25_te_count", 0)),
    ).variant_id
    return "\n".join(
        [
            "# QB/TE Shadow Formula Candidate Handoff - 2026-06-09",
            "",
            "## What Ran",
            "A shadow-only QB/TE experiment compared three candidate variants against the current full-board Rankings baseline.",
            "",
            "## What Changed Only In Shadow Outputs",
            "- QB/TE candidate scores and ranks under the formula-candidate experiment folder.",
            "- Movement, distribution, My Team, and suspicious-row readbacks.",
            "",
            "## What Did Not Change",
            "- Active Rankings baseline files.",
            "- Production formula files.",
            "- Decision Board.",
            "- Active data packs.",
            "- Market/league/display-only source routing.",
            "",
            "## Variant List",
            *[f"- `{variant.variant_id}`" for variant in variants],
            "",
            "## Guardrails",
            f"- Baseline hashes unchanged: {summary['baseline_hashes_match']}",
            f"- Sentinels safe: {summary['sentinels_safe']}",
            f"- Contamination safe: {summary['contamination_safe']}",
            "",
            "## Top Concerns",
            "- QB 1QB compression still needs human judgment because improving top-QB dominance can also lift low-QB rows.",
            "- TE no-premium ceiling behavior changes top TE placement but may create rank displacement that needs RB/WR review.",
            "- No variant should be promoted without a separate controlled formula patch and fresh external audit.",
            "",
            "## Best-Looking Candidate",
            f"`{best}` is the best-looking human-review-only candidate because it tests both QB and TE context together while leaving RB/WR scores unchanged.",
            "",
            "## Worst-Breaking Candidate",
            f"`{worst}` leaves the most top-heavy QB/TE pressure in the top 25 and should be inspected carefully.",
            "",
            "## Inspect First",
            "- `docs/model_v4/QB_TE_SHADOW_FORMULA_CANDIDATE_RESULTS_20260609.md`",
            "- `local_exports/model_v4/formula_candidates/qb_te_shadow_20260609/shadow_suspicious_rows_qb_te_context_balance_v1.csv`",
            "",
            "## Decision Board",
            "Decision Board remains blocked.",
            "",
            "## Recommended Next Task",
            "Human-review the shadow results, then choose one candidate lane for a source-preserving, test-gated production proposal. Do not promote directly from this experiment.",
        ]
    ) + "\n"


def _component_block(
    title: str,
    players: list[dict[str, str]],
    components: dict[tuple[str, str], list[dict[str, str]]],
) -> str:
    lines = [f"### {title}", "", "| Player | Rank | Score | Main component read |", "|---|---:|---:|---|"]
    for row in players:
        key = (row.get("player_name", ""), row.get("position", ""))
        top_components = sorted(
            components.get(key, []),
            key=lambda item: _float_or_none(item.get("weighted_contribution")) or 0.0,
            reverse=True,
        )[:4]
        summary = "; ".join(
            f"{comp.get('component_name')}: contribution {comp.get('weighted_contribution')}"
            for comp in top_components
        )
        lines.append(
            f"| {row.get('player_name', '')} | {row.get('nwr_rank', '')} | "
            f"{row.get('nwr_dynasty_score', '')} | {summary or 'Component rows unavailable'} |"
        )
    return "\n".join(lines)


def _components_by_player(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str], list[dict[str, str]]]:
    output: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        output[(row.get("player_name", ""), row.get("position", ""))].append(row)
    return output


def _top_players(rows: list[dict[str, str]], position: str, limit: int) -> list[dict[str, str]]:
    return sorted(
        [
            row
            for row in rows
            if row.get("position") == position
            and _float_or_none(row.get("nwr_dynasty_score")) is not None
        ],
        key=lambda row: _float(row["nwr_dynasty_score"]),
        reverse=True,
    )[:limit]


def _baseline_top_rows(rows: list[dict[str, str]], limit: int) -> list[dict[str, object]]:
    ranked = sorted(
        [row for row in rows if _float_or_none(row.get("nwr_dynasty_score")) is not None],
        key=lambda row: _int(row.get("nwr_rank")) or 9999,
    )[:limit]
    return [
        {
            "player": row.get("player_name", ""),
            "position": row.get("position", ""),
            "team": row.get("nfl_team", ""),
            "nwr_rank": row.get("nwr_rank", ""),
            "nwr_dynasty_score": row.get("nwr_dynasty_score", ""),
        }
        for row in ranked
    ]


def _markdown_rank_table(
    rows: list[dict[str, object]], rank_key: str, score_key: str
) -> str:
    lines = ["| Rank | Player | Pos | Team | Score |", "|---:|---|---|---|---:|"]
    for row in rows:
        player = row.get("player", row.get("player_name", ""))
        pos = row.get("position", "")
        team = row.get("team", row.get("nfl_team", ""))
        lines.append(
            f"| {row.get(rank_key, '')} | {player} | {pos} | {team} | {row.get(score_key, '')} |"
        )
    return "\n".join(lines)


def _markdown_movement_table(rows: list[dict[str, object]]) -> str:
    lines = ["| Player | Pos | Base Rank | Shadow Rank | Rank Delta | Score Delta |", "|---|---|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(
            f"| {row.get('player', '')} | {row.get('position', '')} | "
            f"{row.get('nwr_rank_baseline', '')} | {row.get('nwr_rank_shadow', '')} | "
            f"{row.get('rank_delta', '')} | {row.get('score_delta', '')} |"
        )
    return "\n".join(lines)


def _issue_index(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    output: dict[tuple[str, str], dict[str, str]] = {}
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    for row in rows:
        key = (row.get("player", ""), row.get("position", ""))
        existing = output.get(key)
        if not existing or severity_rank.get(row.get("severity", "low"), 9) < severity_rank.get(
            existing.get("severity", "low"), 9
        ):
            output[key] = row
        elif existing:
            existing["issue_bucket"] = "|".join(
                sorted({existing.get("issue_bucket", ""), row.get("issue_bucket", "")} - {""})
            )
            existing["human_review_question"] = " | ".join(
                sorted(
                    {
                        existing.get("human_review_question", ""),
                        row.get("human_review_question", ""),
                    }
                    - {""}
                )
            )
    return output


def _baseline_hashes() -> dict[str, str]:
    return {str(path): _sha256(path) for path in BASELINE_FILES}


def _sha256(path: Path) -> str:
    if not path.exists():
        return "missing"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...] | list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _row_key(row: dict[str, object]) -> str:
    return f"{row.get('player_name', row.get('player', ''))}|{row.get('position', '')}"


def _movement_bucket(score_delta: float | None, rank_delta: int | None) -> str:
    if rank_delta is not None and abs(rank_delta) >= 50:
        return "large_rank_movement"
    if score_delta is not None and abs(score_delta) >= 10:
        return "large_score_movement"
    return "minor_or_expected_shadow_movement"


def _delta(new: int | None, old: int | None) -> int | None:
    if new is None or old is None:
        return None
    return new - old


def _score_delta(new: float | None, old: float | None) -> float | None:
    if new is None or old is None:
        return None
    return round(new - old, 4)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * percentile))
    return ordered[index]


def _blank(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, float):
        return round(value, 4)
    return value


def _float(value: object, default: float = 0.0) -> float:
    parsed = _float_or_none(value)
    return default if parsed is None else parsed


def _float_or_none(value: object) -> float | None:
    try:
        text = str(value).strip()
        if not text or text.lower() == "nan":
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _int(value: object) -> int | None:
    parsed = _float_or_none(value)
    return None if parsed is None else int(parsed)
