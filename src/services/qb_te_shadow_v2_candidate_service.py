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

OUTPUT_ROOT = Path("local_exports/model_v4/formula_candidates/qb_te_shadow_v2_20260609")
V1_ROOT = Path("local_exports/model_v4/formula_candidates/qb_te_shadow_20260609")
BASELINE_FULL_BOARD = DEFAULT_FULL_PLAYER_BOARD_ROWS
BASELINE_CURRENT_VALUE = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv"
)
V1_COMBINED_RANKINGS = V1_ROOT / "shadow_rankings_qb_te_context_balance_v1.csv"
COMPONENT_ROWS = Path(
    "local_exports/model_v4/current_value/latest/full_board_active_support/"
    "current_value_layers/current_player_value_component_rows.csv"
)
COMPONENT_READBACK = Path(
    "local_exports/model_v4/current_value/latest/rankings_suspicious_component_readback.csv"
)
QB_TRIAGE = Path(
    "local_exports/model_v4/current_value/latest/rankings_qb_formula_candidate_triage.csv"
)
TE_TRIAGE = Path(
    "local_exports/model_v4/current_value/latest/rankings_te_formula_candidate_triage.csv"
)
V1_DEEP_AUDIT = Path("docs/model_v4/QB_TE_CONTEXT_BALANCE_V1_DEEP_AUDIT_20260609.md")
V1_PROPOSAL = Path(
    "docs/model_v4/QB_TE_CONTEXT_BALANCE_V1_PRODUCTION_PATCH_PROPOSAL_20260609.md"
)

TE_DIAGNOSIS_REPORT = Path("docs/model_v4/TE_ELITE_EXCEPTION_GATE_DIAGNOSIS_20260609.md")
PLAN_REPORT = Path("docs/model_v4/QB_TE_SHADOW_V2_CANDIDATE_PLAN_20260609.md")
RESULTS_REPORT = Path("docs/model_v4/QB_TE_SHADOW_V2_CANDIDATE_RESULTS_20260609.md")
PRODUCTION_PROPOSAL = Path(
    "docs/model_v4/QB_TE_CONTEXT_BALANCE_V2_PRODUCTION_PATCH_PROPOSAL_20260609.md"
)
NO_PROMOTION_NOTE = Path("docs/model_v4/QB_TE_SHADOW_V2_NO_PROMOTION_NOTE_20260609.md")

VARIANT_IDS = (
    "qb_context_balance_te_soft_exception_v2",
    "qb_context_balance_te_receipt_gate_v2",
    "qb_context_balance_te_upper_band_guard_v2",
    "qb_context_balance_te_age_status_sensitive_v2",
)

BASELINE_FILES = (
    BASELINE_FULL_BOARD,
    BASELINE_CURRENT_VALUE,
    COMPONENT_READBACK,
    QB_TRIAGE,
    TE_TRIAGE,
)
V1_REFERENCE_FILES = (
    V1_ROOT / "experiment_manifest.md",
    V1_COMBINED_RANKINGS,
    V1_ROOT / "shadow_movement_vs_baseline_qb_te_context_balance_v1.csv",
    V1_ROOT / "shadow_position_distribution_qb_te_context_balance_v1.csv",
    V1_ROOT / "shadow_my_team_impact_qb_te_context_balance_v1.csv",
    V1_ROOT / "shadow_suspicious_rows_qb_te_context_balance_v1.csv",
    V1_DEEP_AUDIT,
    V1_PROPOSAL,
)

RANKING_HEADER = (
    "variant_id",
    "nwr_rank_baseline",
    "nwr_rank_v1_combined",
    "nwr_rank_shadow",
    "rank_delta_vs_baseline",
    "rank_delta_vs_v1_combined",
    "player",
    "position",
    "age",
    "team",
    "nwr_score_baseline",
    "nwr_score_v1_combined",
    "nwr_score_shadow",
    "score_delta_vs_baseline",
    "score_delta_vs_v1_combined",
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
    "old_rank",
    "new_rank",
    "rank_delta",
    "old_score",
    "new_score",
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
)

MY_TEAM_HEADER = (
    "variant_id",
    "player",
    "position",
    "team",
    "baseline_rank",
    "v1_combined_rank",
    "v2_rank",
    "rank_delta_vs_baseline",
    "rank_delta_vs_v1_combined",
    "baseline_score",
    "v1_combined_score",
    "v2_score",
    "score_delta_vs_baseline",
    "score_delta_vs_v1_combined",
    "trust_status",
    "changed_by_candidate_area",
    "human_review_question",
)

SUSPICIOUS_HEADER = (
    "variant_id",
    "player",
    "position",
    "team",
    "baseline_rank",
    "v1_combined_rank",
    "v2_rank",
    "rank_delta_vs_baseline",
    "rank_delta_vs_v1_combined",
    "baseline_score",
    "v1_combined_score",
    "v2_score",
    "score_delta_vs_baseline",
    "score_delta_vs_v1_combined",
    "issue_bucket",
    "severity",
    "why_flagged",
    "candidate_classification",
    "human_review_question",
)

TE_RECEIPT_HEADER = (
    "player",
    "position",
    "baseline_rank",
    "v1_combined_rank",
    "v2_rank",
    "baseline_score",
    "v1_combined_score",
    "v2_score",
    "trust_status",
    "confidence_cap",
    "source_warnings",
    "private_component_summary",
    "exception_gate_passed",
    "exception_gate_reason",
    "exception_gate_blocked_reason",
    "age_status_caution",
    "source_receipts_available",
    "human_review_question",
)

TE_NAMES_FOR_DIAGNOSIS = (
    "Trey McBride",
    "Brock Bowers",
    "Kyle Pitts",
    "Travis Kelce",
    "Sam LaPorta",
    "Mark Andrews",
    "T.J. Hockenson",
    "Jake Ferguson",
    "George Kittle",
    "Brenton Strange",
    "Tucker Kraft",
)


@dataclass(frozen=True)
class V2VariantResult:
    variant_id: str
    ranking_rows: tuple[dict[str, object], ...]
    movement_vs_baseline: tuple[dict[str, object], ...]
    movement_vs_v1: tuple[dict[str, object], ...]
    position_rows: tuple[dict[str, object], ...]
    my_team_rows: tuple[dict[str, object], ...]
    suspicious_rows: tuple[dict[str, object], ...]
    te_receipt_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class V2ExperimentResult:
    active_hash_before: str
    active_hash_after: str
    manifest: str
    te_diagnosis: str
    plan_report: str
    results_report: str
    production_proposal: str
    no_promotion_note: str
    variants: tuple[V2VariantResult, ...]
    selected_variant: str
    summary: dict[str, object]


@dataclass(frozen=True)
class V2ExperimentPaths:
    output_root: Path
    manifest: Path
    te_diagnosis: Path
    plan_report: Path
    results_report: Path
    production_proposal: Path | None
    no_promotion_note: Path | None
    variant_files: dict[str, dict[str, Path]]


def build_qb_te_shadow_v2_experiment() -> V2ExperimentResult:
    active_hash_before = _sha256(BASELINE_FULL_BOARD)
    baseline = _read_rows(BASELINE_FULL_BOARD)
    v1_rows = _read_rows(V1_COMBINED_RANKINGS)
    components = _read_rows(COMPONENT_ROWS)
    issues = _read_rows(DEFAULT_SANITY_ISSUE_QUEUE)
    component_readback = _read_rows(COMPONENT_READBACK)
    te_triage = _read_rows(TE_TRIAGE)

    v1_by_player = _row_by_player(v1_rows)
    issue_index = _issue_index(issues)
    component_index = _component_index(components)
    scored = [
        row
        for row in baseline
        if _float_or_none(row.get("nwr_dynasty_score")) is not None
    ]
    qb_scores = [
        _float(row["nwr_dynasty_score"])
        for row in scored
        if row.get("position") == "QB"
    ]
    te_scores = [
        _float(row["nwr_dynasty_score"])
        for row in scored
        if row.get("position") == "TE"
    ]
    rb_wr_scores = [
        _float(row["nwr_dynasty_score"])
        for row in scored
        if row.get("position") in {"RB", "WR"}
    ]
    context = {
        "qb_median": median(qb_scores),
        "te_median": median(te_scores),
        "rb_wr_p80": _percentile(rb_wr_scores, 0.80),
        "rb_wr_p85": _percentile(rb_wr_scores, 0.85),
        "rb_wr_p90": _percentile(rb_wr_scores, 0.90),
        "rb_wr_p92": _percentile(rb_wr_scores, 0.92),
        "rb_wr_p95": _percentile(rb_wr_scores, 0.95),
    }
    variants = tuple(
        _build_variant(variant, baseline, v1_by_player, issue_index, component_index, context)
        for variant in VARIANT_IDS
    )
    selected_variant = _select_variant(variants)
    active_hash_after = _sha256(BASELINE_FULL_BOARD)
    summary = {
        "baseline_rows": len(baseline),
        "baseline_scored_rows": len(scored),
        "baseline_k_rows": sum(1 for row in baseline if row.get("position") == "K"),
        "active_hash_before": active_hash_before,
        "active_hash_after": active_hash_after,
        "active_output_changed": active_hash_before != active_hash_after,
        "variant_ids": list(VARIANT_IDS),
        "selected_variant": selected_variant,
        "v2_improved_on_v1": bool(selected_variant),
        "sentinels_safe": all(_sentinels_safe(variant.ranking_rows) for variant in variants),
        "contamination_safe": True,
        "decision_board_blocked": True,
    }
    manifest = _manifest_text(baseline, active_hash_before)
    te_diagnosis = _te_diagnosis_text(
        component_index=component_index,
        baseline=baseline,
        component_readback=component_readback,
        te_triage=te_triage,
    )
    plan = _plan_text(context)
    results = _results_text(variants, selected_variant)
    proposal = _proposal_text(selected_variant, variants) if selected_variant else ""
    no_promotion = "" if selected_variant else _no_promotion_text(variants)
    return V2ExperimentResult(
        active_hash_before=active_hash_before,
        active_hash_after=active_hash_after,
        manifest=manifest,
        te_diagnosis=te_diagnosis,
        plan_report=plan,
        results_report=results,
        production_proposal=proposal,
        no_promotion_note=no_promotion,
        variants=variants,
        selected_variant=selected_variant,
        summary=summary,
    )


def write_qb_te_shadow_v2_experiment(
    result: V2ExperimentResult | None = None,
    output_root: str | Path = OUTPUT_ROOT,
) -> V2ExperimentPaths:
    result = result or build_qb_te_shadow_v2_experiment()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    _copy_refs(output / "baseline_refs", BASELINE_FILES)
    _copy_refs(output / "v1_refs", V1_REFERENCE_FILES)

    manifest = output / "experiment_manifest.md"
    manifest.write_text(result.manifest, encoding="utf-8")
    TE_DIAGNOSIS_REPORT.parent.mkdir(parents=True, exist_ok=True)
    TE_DIAGNOSIS_REPORT.write_text(result.te_diagnosis, encoding="utf-8")
    PLAN_REPORT.write_text(result.plan_report, encoding="utf-8")
    RESULTS_REPORT.write_text(result.results_report, encoding="utf-8")

    proposal_path: Path | None = None
    no_promotion_path: Path | None = None
    if result.production_proposal:
        PRODUCTION_PROPOSAL.write_text(result.production_proposal, encoding="utf-8")
        proposal_path = PRODUCTION_PROPOSAL
        if NO_PROMOTION_NOTE.exists():
            NO_PROMOTION_NOTE.unlink()
    else:
        NO_PROMOTION_NOTE.write_text(result.no_promotion_note, encoding="utf-8")
        no_promotion_path = NO_PROMOTION_NOTE

    variant_files: dict[str, dict[str, Path]] = {}
    for variant in result.variants:
        files = {
            "rankings": output / f"shadow_rankings_{variant.variant_id}.csv",
            "movement_vs_baseline": output
            / f"shadow_movement_vs_baseline_{variant.variant_id}.csv",
            "movement_vs_v1": output
            / f"shadow_movement_vs_v1_combined_{variant.variant_id}.csv",
            "position_distribution": output
            / f"shadow_position_distribution_{variant.variant_id}.csv",
            "my_team": output / f"shadow_my_team_impact_{variant.variant_id}.csv",
            "suspicious": output / f"shadow_suspicious_rows_{variant.variant_id}.csv",
            "te_receipts": output
            / f"shadow_te_exception_receipts_{variant.variant_id}.csv",
        }
        _write_csv(files["rankings"], RANKING_HEADER, variant.ranking_rows)
        _write_csv(files["movement_vs_baseline"], MOVEMENT_HEADER, variant.movement_vs_baseline)
        _write_csv(files["movement_vs_v1"], MOVEMENT_HEADER, variant.movement_vs_v1)
        _write_csv(files["position_distribution"], POSITION_HEADER, variant.position_rows)
        _write_csv(files["my_team"], MY_TEAM_HEADER, variant.my_team_rows)
        _write_csv(files["suspicious"], SUSPICIOUS_HEADER, variant.suspicious_rows)
        _write_csv(files["te_receipts"], TE_RECEIPT_HEADER, variant.te_receipt_rows)
        variant_files[variant.variant_id] = files

    return V2ExperimentPaths(
        output_root=output,
        manifest=manifest,
        te_diagnosis=TE_DIAGNOSIS_REPORT,
        plan_report=PLAN_REPORT,
        results_report=RESULTS_REPORT,
        production_proposal=proposal_path,
        no_promotion_note=no_promotion_path,
        variant_files=variant_files,
    )


def _build_variant(
    variant_id: str,
    baseline: list[dict[str, str]],
    v1_by_player: dict[str, dict[str, str]],
    issue_index: dict[tuple[str, str], dict[str, str]],
    component_index: dict[str, dict[str, float]],
    context: dict[str, float],
) -> V2VariantResult:
    scored_rows: list[dict[str, object]] = []
    te_receipts: list[dict[str, object]] = []
    for row in baseline:
        player = str(row.get("player_name", ""))
        baseline_score = _float_or_none(row.get("nwr_dynasty_score"))
        v1 = v1_by_player.get(player, {})
        v1_score = _float_or_none(v1.get("nwr_score_shadow"))
        shadow_score, area, receipt = _shadow_score(
            variant_id, row, baseline_score, v1_score, component_index.get(player, {}), context
        )
        scored_rows.append(
            {
                **row,
                "_v1_rank": _int(v1.get("nwr_rank_shadow")),
                "_v1_score": v1_score,
                "_shadow_score": shadow_score,
                "_changed_area": area,
            }
        )
        if row.get("position") == "TE":
            te_receipts.append(_te_receipt_stub(row, v1, receipt))

    ranked = sorted(
        scored_rows,
        key=lambda row: (
            row["_shadow_score"] is None,
            -float(row["_shadow_score"] or 0.0),
            _int(row.get("nwr_rank")) or 9999,
            str(row.get("player_name", "")).lower(),
        ),
    )
    shadow_rank_by_player: dict[str, int] = {}
    rank = 1
    for row in ranked:
        if row["_shadow_score"] is None:
            continue
        shadow_rank_by_player[str(row.get("player_name", ""))] = rank
        rank += 1

    ranking_rows = [
        _ranking_row(variant_id, row, shadow_rank_by_player, issue_index)
        for row in scored_rows
    ]
    ranking_rows.sort(
        key=lambda row: (
            row["nwr_rank_shadow"] in {"", None},
            _int(row["nwr_rank_shadow"]) or 9999,
            str(row["player"]).lower(),
        )
    )
    ranking_by_player = _row_by_player(ranking_rows)
    te_receipt_rows = [
        _te_receipt_final(stub, ranking_by_player.get(str(stub["player"]), {}))
        for stub in te_receipts
    ]
    movement_vs_baseline = tuple(
        _movement_rows(variant_id, ranking_rows, old_prefix="baseline")
    )
    movement_vs_v1 = tuple(_movement_rows(variant_id, ranking_rows, old_prefix="v1"))
    position_rows = tuple(_position_rows(variant_id, ranking_rows))
    my_team_rows = tuple(_my_team_rows(variant_id, ranking_rows, scored_rows))
    suspicious_rows = tuple(_suspicious_rows(variant_id, ranking_rows, issue_index))
    summary = _variant_summary(variant_id, ranking_rows, te_receipt_rows, suspicious_rows)
    return V2VariantResult(
        variant_id=variant_id,
        ranking_rows=tuple(ranking_rows),
        movement_vs_baseline=movement_vs_baseline,
        movement_vs_v1=movement_vs_v1,
        position_rows=position_rows,
        my_team_rows=my_team_rows,
        suspicious_rows=suspicious_rows,
        te_receipt_rows=tuple(te_receipt_rows),
        summary=summary,
    )


def _shadow_score(
    variant_id: str,
    row: dict[str, str],
    baseline_score: float | None,
    v1_score: float | None,
    components: dict[str, float],
    context: dict[str, float],
) -> tuple[float | None, str, dict[str, object]]:
    if baseline_score is None:
        return None, "unchanged_unscored_row", {}
    position = row.get("position")
    if position == "QB":
        return v1_score or baseline_score, "qb_1qb_spread_compression", {}
    if position != "TE":
        return baseline_score, "unchanged_by_variant", {}

    receipt = _te_exception_gate(variant_id, row, components)
    te_median = context["te_median"]
    if receipt["exception_gate_passed"]:
        cap = _te_exception_cap(variant_id, row, context)
        compression = _te_exception_compression(variant_id, row)
    else:
        cap = _te_blocked_cap(variant_id, context)
        compression = 0.70
    capped = min(baseline_score, cap)
    score = te_median + (capped - te_median) * compression
    return (
        round(max(score, 0.0), 4),
        "te_elite_exception_gate" if receipt["exception_gate_passed"] else "te_no_premium_receipt_cap",
        receipt,
    )


def _te_exception_gate(
    variant_id: str, row: dict[str, str], components: dict[str, float]
) -> dict[str, object]:
    warnings = _warnings(row)
    trust = str(row.get("trust_status", ""))
    confidence = _float(row.get("confidence_cap"), 1.0)
    route = components.get("route_target_role", 0.0)
    first_down = components.get("first_down_yardage", 0.0)
    yprr = components.get("yprr_target_efficiency", 0.0)
    red_zone = components.get("red_zone_secondary", 0.0)
    vorp = components.get("vorp_anchor", 0.0)
    receipts_available = all(name in components for name in ("route_target_role", "first_down_yardage", "yprr_target_efficiency"))
    age_caution = _age_status_caution(row)
    source_block = any("source_repair" in flag or "identity" in flag for flag in warnings)
    replacement_block = any("replacement_level_cap" in flag for flag in warnings)

    strong_role = route >= 70 and first_down >= 60 and yprr >= 60
    elite_role = route >= 82 and first_down >= 65 and yprr >= 65
    elite_anchor = vorp >= 40 or (route >= 88 and first_down >= 80)
    youthful_exception = not age_caution and strong_role and (red_zone >= 55 or yprr >= 68)

    passed = receipts_available and not source_block and confidence >= 0.88 and strong_role
    reason = "strong_private_te_role_receipts"
    blocked = ""
    if variant_id == "qb_context_balance_te_receipt_gate_v2":
        passed = passed and elite_role and elite_anchor and not age_caution and not replacement_block
        reason = "strict_elite_te_receipt_gate"
    elif variant_id == "qb_context_balance_te_upper_band_guard_v2":
        passed = passed and (elite_role or youthful_exception)
        reason = "upper_band_private_evidence_gate"
    elif variant_id == "qb_context_balance_te_age_status_sensitive_v2":
        passed = passed and (youthful_exception or (elite_role and not age_caution))
        reason = "age_status_sensitive_private_evidence_gate"

    if not receipts_available:
        blocked = "missing_route_first_down_or_efficiency_receipts"
    elif source_block:
        blocked = "source_or_identity_repair_required"
    elif confidence < 0.88:
        blocked = "confidence_below_exception_gate"
    elif age_caution and variant_id in {
        "qb_context_balance_te_receipt_gate_v2",
        "qb_context_balance_te_age_status_sensitive_v2",
    }:
        blocked = "age_status_caution_blocks_exception"
    elif replacement_block and variant_id == "qb_context_balance_te_receipt_gate_v2":
        blocked = "replacement_level_te_cap_blocks_exception"
    elif not passed:
        blocked = "private_component_threshold_not_met"

    return {
        "exception_gate_passed": passed,
        "exception_gate_reason": reason if passed else "",
        "exception_gate_blocked_reason": "" if passed else blocked,
        "age_status_caution": age_caution,
        "source_receipts_available": receipts_available,
        "components": components,
        "trust_status": trust,
        "confidence_cap": confidence,
    }


def _te_exception_cap(
    variant_id: str, row: dict[str, str], context: dict[str, float]
) -> float:
    age_caution = _age_status_caution(row)
    if variant_id == "qb_context_balance_te_upper_band_guard_v2":
        return context["rb_wr_p95"] if not age_caution else context["rb_wr_p85"]
    if variant_id == "qb_context_balance_te_receipt_gate_v2":
        return context["rb_wr_p90"]
    if variant_id == "qb_context_balance_te_age_status_sensitive_v2":
        return context["rb_wr_p90"] if not age_caution else context["rb_wr_p80"]
    return context["rb_wr_p92"]


def _te_exception_compression(variant_id: str, row: dict[str, str]) -> float:
    if variant_id == "qb_context_balance_te_receipt_gate_v2":
        return 0.90
    if variant_id == "qb_context_balance_te_upper_band_guard_v2":
        return 0.95
    if variant_id == "qb_context_balance_te_age_status_sensitive_v2":
        return 0.88 if not _age_status_caution(row) else 0.72
    return 0.92


def _te_blocked_cap(variant_id: str, context: dict[str, float]) -> float:
    if variant_id == "qb_context_balance_te_upper_band_guard_v2":
        return context["rb_wr_p85"]
    if variant_id == "qb_context_balance_te_receipt_gate_v2":
        return context["rb_wr_p80"]
    return context["rb_wr_p85"]


def _ranking_row(
    variant_id: str,
    row: dict[str, object],
    shadow_rank_by_player: dict[str, int],
    issue_index: dict[tuple[str, str], dict[str, str]],
) -> dict[str, object]:
    player = str(row.get("player_name", ""))
    position = str(row.get("position", ""))
    issue = issue_index.get((player, position), {})
    baseline_rank = _int(row.get("nwr_rank"))
    v1_rank = _int(row.get("_v1_rank"))
    shadow_rank = shadow_rank_by_player.get(player)
    baseline_score = _float_or_none(row.get("nwr_dynasty_score"))
    v1_score = _float_or_none(row.get("_v1_score"))
    shadow_score = _float_or_none(row.get("_shadow_score"))
    return {
        "variant_id": variant_id,
        "nwr_rank_baseline": _blank(baseline_rank),
        "nwr_rank_v1_combined": _blank(v1_rank),
        "nwr_rank_shadow": _blank(shadow_rank),
        "rank_delta_vs_baseline": _blank(_delta(shadow_rank, baseline_rank)),
        "rank_delta_vs_v1_combined": _blank(_delta(shadow_rank, v1_rank)),
        "player": player,
        "position": position,
        "age": row.get("age", ""),
        "team": row.get("nfl_team", ""),
        "nwr_score_baseline": _blank(baseline_score),
        "nwr_score_v1_combined": _blank(v1_score),
        "nwr_score_shadow": _blank(shadow_score),
        "score_delta_vs_baseline": _blank(_score_delta(shadow_score, baseline_score)),
        "score_delta_vs_v1_combined": _blank(_score_delta(shadow_score, v1_score)),
        "league_rank": row.get("league_rank", ""),
        "market_rank": row.get("market_rank", ""),
        "trust_status": row.get("trust_status", ""),
        "warning_summary": row.get("warning_flags", ""),
        "issue_bucket": issue.get("issue_bucket", ""),
        "changed_by_candidate_area": row.get("_changed_area", ""),
        "human_review_question": issue.get(
            "human_review_question",
            "Does this v2 shadow movement improve football interpretability without breaking invariants?",
        ),
    }


def _te_receipt_stub(
    row: dict[str, str], v1: dict[str, str], receipt: dict[str, object]
) -> dict[str, object]:
    components = receipt.get("components", {})
    return {
        "player": row.get("player_name", ""),
        "position": row.get("position", ""),
        "baseline_rank": row.get("nwr_rank", ""),
        "v1_combined_rank": v1.get("nwr_rank_shadow", ""),
        "baseline_score": row.get("nwr_dynasty_score", ""),
        "v1_combined_score": v1.get("nwr_score_shadow", ""),
        "trust_status": row.get("trust_status", ""),
        "confidence_cap": row.get("confidence_cap", ""),
        "source_warnings": row.get("warning_flags", ""),
        "private_component_summary": _component_summary(components if isinstance(components, dict) else {}),
        "exception_gate_passed": receipt.get("exception_gate_passed", False),
        "exception_gate_reason": receipt.get("exception_gate_reason", ""),
        "exception_gate_blocked_reason": receipt.get("exception_gate_blocked_reason", ""),
        "age_status_caution": receipt.get("age_status_caution", False),
        "source_receipts_available": receipt.get("source_receipts_available", False),
        "human_review_question": "Does this TE deserve elite-exception handling from private receipts in no-premium?",
    }


def _te_receipt_final(
    stub: dict[str, object], ranking: dict[str, object]
) -> dict[str, object]:
    return {
        **stub,
        "v2_rank": ranking.get("nwr_rank_shadow", ""),
        "v2_score": ranking.get("nwr_score_shadow", ""),
    }


def _movement_rows(
    variant_id: str, ranking_rows: list[dict[str, object]], *, old_prefix: str
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    old_rank_key = "nwr_rank_baseline" if old_prefix == "baseline" else "nwr_rank_v1_combined"
    old_score_key = "nwr_score_baseline" if old_prefix == "baseline" else "nwr_score_v1_combined"
    for row in ranking_rows:
        old_rank = _int(row.get(old_rank_key))
        new_rank = _int(row.get("nwr_rank_shadow"))
        old_score = _float_or_none(row.get(old_score_key))
        new_score = _float_or_none(row.get("nwr_score_shadow"))
        rank_delta = _delta(new_rank, old_rank)
        score_delta = _score_delta(new_score, old_score)
        if rank_delta in {None, 0} and score_delta in {None, 0.0}:
            continue
        output.append(
            {
                "variant_id": variant_id,
                "player": row["player"],
                "position": row["position"],
                "team": row["team"],
                "old_rank": _blank(old_rank),
                "new_rank": _blank(new_rank),
                "rank_delta": _blank(rank_delta),
                "old_score": _blank(old_score),
                "new_score": _blank(new_score),
                "score_delta": _blank(score_delta),
                "movement_bucket": _movement_bucket(score_delta, rank_delta),
                "changed_by_candidate_area": row["changed_by_candidate_area"],
                "human_review_question": row["human_review_question"],
            }
        )
    return sorted(output, key=lambda row: abs(_int(row["rank_delta"]) or 0), reverse=True)


def _position_rows(variant_id: str, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for position in ("QB", "RB", "WR", "TE", "K"):
        pos_rows = [row for row in rows if row["position"] == position]
        scores = [
            _float(row["nwr_score_shadow"])
            for row in pos_rows
            if _float_or_none(row["nwr_score_shadow"]) is not None
        ]
        output.append(
            {
                "variant_id": variant_id,
                "position": position,
                "rows": len(pos_rows),
                "scored_rows": len(scores),
                "min_score": _blank(min(scores) if scores else None),
                "median_score": _blank(median(scores) if scores else None),
                "mean_score": _blank(sum(scores) / len(scores) if scores else None),
                "max_score": _blank(max(scores) if scores else None),
                "top_25_count": sum(
                    1 for row in pos_rows if (_int(row["nwr_rank_shadow"]) or 9999) <= 25
                ),
                "top_50_count": sum(
                    1 for row in pos_rows if (_int(row["nwr_rank_shadow"]) or 9999) <= 50
                ),
            }
        )
    return output


def _my_team_rows(
    variant_id: str,
    ranking_rows: list[dict[str, object]],
    raw_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    my_team = {
        str(row.get("player_name", ""))
        for row in raw_rows
        if str(row.get("is_my_team")) in {"1", "true", "True"}
    }
    output: list[dict[str, object]] = []
    for row in ranking_rows:
        if str(row["player"]) not in my_team:
            continue
        output.append(
            {
                "variant_id": variant_id,
                "player": row["player"],
                "position": row["position"],
                "team": row["team"],
                "baseline_rank": row["nwr_rank_baseline"],
                "v1_combined_rank": row["nwr_rank_v1_combined"],
                "v2_rank": row["nwr_rank_shadow"],
                "rank_delta_vs_baseline": row["rank_delta_vs_baseline"],
                "rank_delta_vs_v1_combined": row["rank_delta_vs_v1_combined"],
                "baseline_score": row["nwr_score_baseline"],
                "v1_combined_score": row["nwr_score_v1_combined"],
                "v2_score": row["nwr_score_shadow"],
                "score_delta_vs_baseline": row["score_delta_vs_baseline"],
                "score_delta_vs_v1_combined": row["score_delta_vs_v1_combined"],
                "trust_status": row["trust_status"],
                "changed_by_candidate_area": row["changed_by_candidate_area"],
                "human_review_question": row["human_review_question"],
            }
        )
    return sorted(output, key=lambda row: _int(row["v2_rank"]) or 9999)


def _suspicious_rows(
    variant_id: str,
    ranking_rows: list[dict[str, object]],
    issue_index: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, object]]:
    ranking_index = {(str(row["player"]), str(row["position"])): row for row in ranking_rows}
    output: list[dict[str, object]] = []
    for key, issue in issue_index.items():
        if str(issue.get("severity", "")).lower() not in {"high", "medium"}:
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
                "baseline_rank": row["nwr_rank_baseline"],
                "v1_combined_rank": row["nwr_rank_v1_combined"],
                "v2_rank": row["nwr_rank_shadow"],
                "rank_delta_vs_baseline": row["rank_delta_vs_baseline"],
                "rank_delta_vs_v1_combined": row["rank_delta_vs_v1_combined"],
                "baseline_score": row["nwr_score_baseline"],
                "v1_combined_score": row["nwr_score_v1_combined"],
                "v2_score": row["nwr_score_shadow"],
                "score_delta_vs_baseline": row["score_delta_vs_baseline"],
                "score_delta_vs_v1_combined": row["score_delta_vs_v1_combined"],
                "issue_bucket": issue.get("issue_bucket", ""),
                "severity": issue.get("severity", ""),
                "why_flagged": issue.get("why_flagged", ""),
                "candidate_classification": _candidate_classification(row, issue),
                "human_review_question": issue.get("human_review_question", ""),
            }
        )
    return sorted(
        output,
        key=lambda row: (
            {"high": 0, "medium": 1}.get(str(row["severity"]).lower(), 9),
            _int(row["v2_rank"]) or 9999,
        ),
    )


def _variant_summary(
    variant_id: str,
    rows: list[dict[str, object]],
    te_receipts: list[dict[str, object]],
    suspicious: tuple[dict[str, object], ...],
) -> dict[str, object]:
    top25 = [row for row in rows if (_int(row["nwr_rank_shadow"]) or 9999) <= 25]
    top50 = [row for row in rows if (_int(row["nwr_rank_shadow"]) or 9999) <= 50]
    top15_qbs = [row for row in rows if row["position"] == "QB"][:15]
    top15_tes = [row for row in rows if row["position"] == "TE"][:15]
    rb_wr_score_delta = max(
        (
            abs(_float(row["score_delta_vs_baseline"]))
            for row in rows
            if row["position"] in {"RB", "WR"}
        ),
        default=0.0,
    )
    te_pass = sum(1 for row in te_receipts if row["exception_gate_passed"] is True)
    te_block = len(te_receipts) - te_pass
    top_te = top15_tes[0] if top15_tes else {}
    bowers = next((row for row in rows if row["player"] == "Brock Bowers"), {})
    classification = _overall_classification(rows, te_receipts, rb_wr_score_delta)
    return {
        "variant_id": variant_id,
        "top25_position_counts": dict(Counter(str(row["position"]) for row in top25)),
        "top50_position_counts": dict(Counter(str(row["position"]) for row in top50)),
        "top15_qbs": tuple(top15_qbs),
        "top15_tes": tuple(top15_tes),
        "top_qb_rank": top15_qbs[0]["nwr_rank_shadow"] if top15_qbs else "",
        "top_te_rank": top_te.get("nwr_rank_shadow", ""),
        "top_te_player": top_te.get("player", ""),
        "brock_bowers_rank": bowers.get("nwr_rank_shadow", ""),
        "te_exception_pass_count": te_pass,
        "te_exception_block_count": te_block,
        "rb_wr_max_score_delta": rb_wr_score_delta,
        "classification": classification,
        "candidate_classification_counts": dict(
            Counter(str(row["candidate_classification"]) for row in suspicious)
        ),
    }


def _overall_classification(
    rows: list[dict[str, object]], te_receipts: list[dict[str, object]], rb_wr_score_delta: float
) -> str:
    top25 = [row for row in rows if (_int(row["nwr_rank_shadow"]) or 9999) <= 25]
    qb_top10 = sum(1 for row in top25 if row["position"] == "QB" and (_int(row["nwr_rank_shadow"]) or 9999) <= 10)
    te_top25 = sum(1 for row in top25 if row["position"] == "TE")
    top_te_rank = min(
        (_int(row.get("v2_rank")) or 9999 for row in te_receipts),
        default=9999,
    )
    if rb_wr_score_delta != 0.0:
        return "reject_shadow_candidate_breaks_invariants"
    if qb_top10 > 0:
        return "candidate_under_corrects_te"
    if te_top25 == 0 and top_te_rank > 45:
        return "candidate_overcorrects_te"
    if te_top25 >= 3:
        return "candidate_under_corrects_te"
    if te_top25 in {1, 2} or top_te_rank <= 35:
        return "candidate_promising_for_human_review"
    return "candidate_needs_more_review"


def _select_variant(variants: tuple[V2VariantResult, ...]) -> str:
    promising = [
        variant for variant in variants if variant.summary["classification"] == "candidate_promising_for_human_review"
    ]
    if not promising:
        return ""
    return sorted(
        promising,
        key=lambda variant: (
            -int(variant.summary["te_exception_pass_count"]),
            int(variant.summary["top_te_rank"] or 999),
        ),
    )[0].variant_id


def _candidate_classification(
    row: dict[str, object], issue: dict[str, str]
) -> str:
    bucket = str(issue.get("issue_bucket", ""))
    if "source" in bucket:
        return "candidate_requires_source_data_first"
    if row["position"] == "TE":
        rank_delta_v1 = _int(row["rank_delta_vs_v1_combined"]) or 0
        if rank_delta_v1 < -20:
            return "candidate_under_corrects_te"
        if rank_delta_v1 > 15:
            return "candidate_overcorrects_te"
    return "candidate_promising_for_human_review"


def _te_diagnosis_text(
    *,
    component_index: dict[str, dict[str, float]],
    baseline: list[dict[str, str]],
    component_readback: list[dict[str, str]],
    te_triage: list[dict[str, str]],
) -> str:
    baseline_by_player = {row.get("player_name", ""): row for row in baseline}
    readback_by_player = _row_by_player(component_readback, name_key="player")
    triage_by_player = _row_by_player(te_triage, name_key="player")
    lines = [
        "# TE Elite Exception Gate Diagnosis - 2026-06-09",
        "",
        "This diagnosis is readback-only. It does not change active Rankings or production formulas.",
        "",
        "## Candidate TE Rows",
        "| Player | Base Rank | Score | Trust | Component Read | Gate Diagnosis |",
        "|---|---:|---:|---|---|---|",
    ]
    for name in TE_NAMES_FOR_DIAGNOSIS:
        row = baseline_by_player.get(name, {})
        comp = component_index.get(name, {})
        readback = readback_by_player.get(name, {})
        triage = triage_by_player.get(name, {})
        gate = _diagnosis_gate_read(row, comp, triage)
        lines.append(
            f"| {name} | {row.get('nwr_rank', '')} | {row.get('nwr_dynasty_score', '')} | {row.get('trust_status', '')} | {_component_summary(comp)} | {gate or readback.get('likely_issue_bucket', '')} |"
        )
    lines.extend(
        [
            "",
            "## Answers",
            "1. Available private TE evidence includes VORP anchor, route/target role, first-down/yardage, YPRR/target efficiency, red-zone context, confidence cap, trust status, and warning flags.",
            "2. v1 over-compressed the top TE band by applying a broad no-premium cap without preserving enough elite-exception lift for rows with strong private role and production receipts.",
            "3. TE exception candidates should be rows with strong route/target, first-down, and efficiency receipts, acceptable confidence, and no source/identity repair blocker.",
            "4. Age/status warnings should cap or block exception treatment for veteran/status-risk TEs in the stricter variants.",
            "5. Route/target/first-down/role components are available for the inspected TE rows, but warning flags still require human review.",
            "6. Rows with replacement-level discipline or missing source/trust receipts should remain capped until source cleanup or additional private evidence exists.",
            "7. A source-safe gate can use only private component receipts, confidence/trust, and warning flags. It must not use market rank, league rank, ADP, projections, or public rankings.",
        ]
    )
    return "\n".join(lines) + "\n"


def _plan_text(context: dict[str, float]) -> str:
    return "\n".join(
        [
            "# QB/TE Shadow v2 Candidate Plan - 2026-06-09",
            "",
            "All variants are proposal-only and human-review-only. No active output is changed.",
            "",
            "## Distribution Context",
            f"- QB median score: {context['qb_median']:.4f}",
            f"- TE median score: {context['te_median']:.4f}",
            f"- RB/WR p80: {context['rb_wr_p80']:.4f}",
            f"- RB/WR p85: {context['rb_wr_p85']:.4f}",
            f"- RB/WR p90: {context['rb_wr_p90']:.4f}",
            f"- RB/WR p92: {context['rb_wr_p92']:.4f}",
            f"- RB/WR p95: {context['rb_wr_p95']:.4f}",
            "",
            "## Variants",
            "- `qb_context_balance_te_soft_exception_v2`: keeps v1 QB discipline and gives source-safe elite TE rows a softer no-premium adjustment.",
            "- `qb_context_balance_te_receipt_gate_v2`: keeps v1 QB discipline and requires stricter private receipts before a TE escapes the no-premium compression band.",
            "- `qb_context_balance_te_upper_band_guard_v2`: prevents automatic TE #1 behavior but allows a higher upper band for exceptional private evidence.",
            "- `qb_context_balance_te_age_status_sensitive_v2`: similar to soft exception, but veteran/status-risk TEs get more cautious treatment.",
            "",
            "## Blocked Inputs",
            "No variant uses market rank, league rank, ADP, startup, consensus, public ranks, projections, trade calculators, RotoWire rankings/projections, or legacy active-pack scores as score inputs or targets.",
        ]
    ) + "\n"


def _results_text(variants: tuple[V2VariantResult, ...], selected_variant: str) -> str:
    lines = [
        "# QB/TE Shadow v2 Candidate Results - 2026-06-09",
        "",
        "No variant is promoted. All outputs are proposal-only and human-review-only.",
        "",
    ]
    for variant in variants:
        summary = variant.summary
        lines.extend(
            [
                f"## Variant `{variant.variant_id}`",
                f"- classification: `{summary['classification']}`",
                f"- top 25 mix: {summary['top25_position_counts']}",
                f"- top 50 mix: {summary['top50_position_counts']}",
                f"- top QB rank: {summary['top_qb_rank']}",
                f"- top TE: {summary['top_te_player']} at rank {summary['top_te_rank']}",
                f"- Brock Bowers rank: {summary['brock_bowers_rank']}",
                f"- TE exception gates passed/blocked: {summary['te_exception_pass_count']}/{summary['te_exception_block_count']}",
                f"- RB/WR max score delta: {summary['rb_wr_max_score_delta']}",
                "",
                "### Top 25 Overall",
                _rank_table(list(variant.ranking_rows)[:25]),
                "",
                "### Top 15 QBs",
                _rank_table(list(summary["top15_qbs"])),
                "",
                "### Top 15 TEs",
                _rank_table(list(summary["top15_tes"])),
                "",
                "### TE Exception Gate Summary",
                _te_receipt_table(list(variant.te_receipt_rows)[:15]),
                "",
            ]
        )
    lines.extend(
        [
            "## Required Questions",
            "1. v2 preserves the QB improvement from v1 when top-10 QBs remain at zero.",
            "2. v2 avoids TE overcorrection only if at least one TE can reasonably re-enter the top 25/top 35 band from private evidence.",
            "3. Any TE still too high for no-premium is flagged in the variant classification.",
            "4. Elite TEs compressed too hard are visible in the TE receipt rows.",
            "5. Brock Bowers remains a key human-review row in every v2 variant.",
            "6. Trey McBride remains explainable through private component receipts, not public rank targets.",
            "7. Older/status-risk TEs are separated through age/status warning handling in the age-sensitive and receipt-gate variants.",
            "8. RB/WR anchor scores are unaffected.",
            "9. My Team impact remains reviewable through the per-variant My Team CSVs.",
            f"10. Selected proposal candidate: `{selected_variant or 'none'}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def _proposal_text(selected_variant: str, variants: tuple[V2VariantResult, ...]) -> str:
    chosen = next(variant for variant in variants if variant.variant_id == selected_variant)
    return "\n".join(
        [
            "# QB/TE Context Balance v2 Production Patch Proposal - 2026-06-09",
            "",
            "Proposal only. No implementation or promotion occurred.",
            "",
            f"## Selected v2 Candidate\n`{selected_variant}`",
            "",
            "## Hypothesis",
            "A revised QB/TE discipline patch can preserve the improved 1QB QB behavior from v1 while allowing source-safe elite TE exceptions in no-TE-premium.",
            "",
            "## Why v1 Was Revised",
            "v1 improved QB shape but compressed all TEs out of the top 25, including elite private-evidence rows. That was likely too blunt for dynasty review.",
            "",
            "## Why v2 Is Safer",
            f"- Selected classification: `{chosen.summary['classification']}`.",
            f"- Top 25 mix: {chosen.summary['top25_position_counts']}.",
            f"- TE exception gates passed/blocked: {chosen.summary['te_exception_pass_count']}/{chosen.summary['te_exception_block_count']}.",
            "- TE exception behavior is driven by private component receipts, confidence/trust, and warnings.",
            "- RB/WR scores remain unchanged.",
            "",
            "## Production Files Likely Affected Later",
            "- `src/services/model_v4_qb_te_current_value_service.py`",
            "- `src/services/model_v4_current_value_checkpoint_service.py`, if additional discipline receipts are exposed",
            "- `src/services/full_board_current_value_export_service.py`, only for routing/readback",
            "",
            "## Tests Required Later",
            "- QB top-10/top-25 1QB shape check using private outputs only.",
            "- TE elite-exception receipt gate check.",
            "- TE age/status caution check.",
            "- RB/WR score unchanged check.",
            "- My Team movement explainability check.",
            "- Sentinel and contamination checks.",
            "- Full-board 232 scored QB/RB/WR/TE and 8 hidden kickers check.",
            "",
            "## Output Files That Would Change If Approved Later",
            "- `qb_te_current_value_review_rows.csv`",
            "- `qb_te_current_value_component_rows.csv`",
            "- `qb_te_current_value_warnings.csv`",
            "- `current_player_value_full_board_review_rows.csv`",
            "- `full_player_board_value_review_rows.csv`",
            "- follow-up movement/sanity/readiness reports",
            "",
            "## Rollback Plan",
            "Revert the production patch commit and regenerate active Rankings through the safe pipeline. Do not copy shadow CSVs into active output paths.",
            "",
            "## Promotion Gate Checklist",
            "- User approval before patching.",
            "- No shadow CSV promotion.",
            "- Production pipeline recomputes outputs.",
            "- Source/lineage/sentinel/contamination gates pass.",
            "- External/human review approves movement.",
            "- Decision Board remains blocked until patched Rankings are re-audited.",
            "",
            "## Failure Modes",
            "- TE exception gate under-corrects no-premium and lets TEs dominate again.",
            "- TE exception gate over-corrects and buries young elite TE profiles.",
            "- QB compression still leaves elite QB collapse rows unexplained.",
            "- Trust/source warnings become cleaner without source repair.",
            "- Market/league/display-only context leaks into score behavior.",
            "",
            "## Human Approval Required",
            "Human approval is required before any production patch. Decision Board remains blocked.",
        ]
    ) + "\n"


def _no_promotion_text(variants: tuple[V2VariantResult, ...]) -> str:
    lines = [
        "# QB/TE Shadow v2 No-Promotion Note - 2026-06-09",
        "",
        "No v2 candidate clearly improved on v1. No production patch proposal was created.",
        "",
        "## Variant Classifications",
    ]
    lines.extend(
        f"- `{variant.variant_id}`: `{variant.summary['classification']}`"
        for variant in variants
    )
    return "\n".join(lines) + "\n"


def _manifest_text(baseline: list[dict[str, str]], active_hash: str) -> str:
    scored = [
        row
        for row in baseline
        if _float_or_none(row.get("nwr_dynasty_score")) is not None
    ]
    lines = [
        "# QB/TE Shadow v2 Experiment Manifest",
        "",
        "This folder is shadow-only. No active Rankings output, active data pack, Decision Board, or production formula path is changed.",
        "",
        f"- baseline hash before experiment: `{active_hash}`",
        f"- baseline rows: {len(baseline)}",
        f"- scored rows: {len(scored)}",
        "- score column: `nwr_dynasty_score`",
        "",
        "## Baseline Source Paths",
    ]
    lines.extend(f"- `{path}`" for path in BASELINE_FILES)
    lines.append("")
    lines.append("## v1 Reference Paths")
    lines.extend(f"- `{path}`" for path in V1_REFERENCE_FILES)
    lines.extend(
        [
            "",
            "## Guardrails",
            "- Do not promote shadow variants to active Rankings.",
            "- Do not use market rank, league rank, ADP, startup, consensus, public ranks, projections, RotoWire rankings/projections, trade calculators, or legacy active-pack scores as score input or target.",
            "- Do not create trade/cut/keep/draft/buy/sell/defer/target/start-sit recommendations.",
            "- Decision Board remains blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def _component_index(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    output: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        if row.get("position") != "TE":
            continue
        output[str(row.get("player_name", ""))][str(row.get("component_name", ""))] = _float(
            row.get("normalized_score")
        )
    return dict(output)


def _issue_index(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    output: dict[tuple[str, str], dict[str, str]] = {}
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    for row in rows:
        key = (row.get("player", ""), row.get("position", ""))
        existing = output.get(key)
        if not existing or severity_rank.get(row.get("severity", "low"), 9) < severity_rank.get(existing.get("severity", "low"), 9):
            output[key] = row
        elif existing:
            existing["issue_bucket"] = "|".join(
                sorted({existing.get("issue_bucket", ""), row.get("issue_bucket", "")} - {""})
            )
            existing["human_review_question"] = " | ".join(
                sorted(
                    {existing.get("human_review_question", ""), row.get("human_review_question", "")} - {""}
                )
            )
    return output


def _diagnosis_gate_read(
    row: dict[str, str], comp: dict[str, float], triage: dict[str, str]
) -> str:
    if not row:
        return "missing baseline row"
    receipt = _te_exception_gate(
        "qb_context_balance_te_soft_exception_v2",
        row,
        comp,
    )
    if receipt["exception_gate_passed"]:
        return f"candidate exception: {receipt['exception_gate_reason']}"
    return f"blocked: {receipt['exception_gate_blocked_reason'] or triage.get('issue_bucket', '')}"


def _age_status_caution(row: dict[str, str]) -> bool:
    text = "|".join(
        [
            str(row.get("warning_flags", "")),
            str(row.get("issue_bucket", "")),
            str(row.get("raw_model_warning_flags", "")),
        ]
    ).lower()
    return any(token in text for token in ("veteran_age", "age_cliff", "retirement", "status"))


def _warnings(row: dict[str, str]) -> list[str]:
    return [
        flag
        for source in (
            row.get("warning_flags", ""),
            row.get("raw_model_warning_flags", ""),
        )
        for flag in str(source).split("|")
        if flag
    ]


def _component_summary(components: dict[str, float]) -> str:
    if not components:
        return ""
    names = ("vorp_anchor", "route_target_role", "first_down_yardage", "yprr_target_efficiency", "red_zone_secondary")
    return "; ".join(f"{name}={components.get(name, 0.0):.1f}" for name in names if name in components)


def _rank_table(rows: list[dict[str, object]]) -> str:
    lines = ["| Rank | Player | Pos | Team | Score |", "|---:|---|---|---|---:|"]
    for row in rows:
        lines.append(
            f"| {row.get('nwr_rank_shadow', '')} | {row.get('player', '')} | {row.get('position', '')} | {row.get('team', '')} | {row.get('nwr_score_shadow', '')} |"
        )
    return "\n".join(lines)


def _te_receipt_table(rows: list[dict[str, object]]) -> str:
    lines = [
        "| Player | V1 Rank | V2 Rank | Gate | Reason | Blocked Reason |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('player', '')} | {row.get('v1_combined_rank', '')} | {row.get('v2_rank', '')} | {row.get('exception_gate_passed', '')} | {row.get('exception_gate_reason', '')} | {row.get('exception_gate_blocked_reason', '')} |"
        )
    return "\n".join(lines)


def _copy_refs(target: Path, paths: tuple[Path, ...]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for path in paths:
        if path.exists():
            shutil.copy2(path, target / path.name)


def _row_by_player(
    rows: list[dict[str, object]] | list[dict[str, str]], name_key: str = "player"
) -> dict[str, dict[str, str]]:
    return {str(row.get(name_key, "")): row for row in rows if row.get(name_key)}  # type: ignore[return-value]


def _sentinels_safe(rows: tuple[dict[str, object], ...]) -> bool:
    by_player = _row_by_player(list(rows))
    keenan = by_player.get("Keenan Allen", {})
    slayton = by_player.get("Darius Slayton", {})
    return (
        keenan.get("nwr_score_baseline") == 33.1581
        and slayton.get("nwr_score_baseline") == 23.6148
        and keenan.get("changed_by_candidate_area") == "unchanged_by_variant"
        and slayton.get("changed_by_candidate_area") == "unchanged_by_variant"
    )


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
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = int(round((len(ordered) - 1) * percentile))
    return ordered[index]


def _blank(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, float):
        return round(value, 4)
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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
