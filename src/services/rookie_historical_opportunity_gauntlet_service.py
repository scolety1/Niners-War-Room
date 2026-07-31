"""Leakage-safe contracts for the historical rookie opportunity gauntlet.

This module is deliberately research-only.  It owns fail-closed source,
identity, temporal-fold, feature-semantic, evaluation, and preservation gates;
it has no app, ranking, provider, scheduler, or persistence integration.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

AS_OF_DATE = "2026-07-31"
CANONICAL_HQ = "18792a8bbf3f39c03086163c1f5d672b1e2ba5a6"
CANONICAL_TREE = "b91e9b41c192494fbed2facd85bd64b1a1a8d18d"
CFBD_AGGREGATE_SHA256 = "370ce01696c305f64792e45e1f8671cfb788b8419b257040206a6f14e5c2770a"
COMBINE_AGGREGATE_SHA256 = "5e6847b155d87a27954204d6b6e6192f6264c0e04556fbfbe20983954ddcee65"
FINISHED_V1_SHA256 = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
OUTCOME_V3_SHA256 = "e3b44047d36bd62d9573295db64d96f214922a20f0083cf49105f104970b3d20"
FROZEN_COMPARATOR_SHA256 = "b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179"
RESEARCH_STATUS = "RESEARCH_ONLY_NOT_CANONICAL_NOT_PRODUCTION"

POSITIONS = ("QB", "RB", "WR", "TE")
MATURE_MAX_CLASS = {"Y1": 2025, "Y2": 2024, "Y3": 2023}
FAMILY_POSITIONS = {
    "T01": ("QB",),
    "T02": ("RB",),
    "T03": ("WR",),
    "T04": ("TE",),
    "T05": POSITIONS,
    "T06": POSITIONS,
    "T07": ("QB",),
    "T09": ("WR",),
}
BLOCKED_FAMILIES = {
    "T05": "FEATURE_FAMILY_BLOCKED_SEMANTIC_MISMATCH",
    "T07": "FEATURE_FAMILY_BLOCKED_SOURCE",
    "T09": "FEATURE_FAMILY_BLOCKED_SEMANTIC_MISMATCH",
}
TESTABLE_FAMILIES = {
    "T01": "FEATURE_FAMILY_TESTABLE_WITH_LOWER_FIDELITY",
    "T02": "FEATURE_FAMILY_TESTABLE_WITH_LOWER_FIDELITY",
    "T03": "FEATURE_FAMILY_TESTABLE_WITH_LOWER_FIDELITY",
    "T04": "FEATURE_FAMILY_TESTABLE_WITH_LOWER_FIDELITY",
    "T06": "FEATURE_FAMILY_TESTABLE",
}

FORBIDDEN_FEATURE_TOKENS = (
    "adp",
    "recruiting",
    "ras",
    "medical",
    "route",
    "missed_tackle",
    "pressure_to_sack",
    "camp",
    "preseason",
)
PROHIBITED_JOIN_MODES = (
    "name_only",
    "normalized_name",
    "nearest_name",
    "name_plus_college",
    "manual_invented_id",
)
ALLOWED_JOIN_MODES = (
    "exact_gsis_id",
    "exact_pfr_cfb_bridge",
    "cfbd_draft_year_overall_to_exact_gsis",
    "reviewed_multifield_mapping",
)

MUTATIONS = (
    "random player split",
    "future-class normalization",
    "use 2026 outcome",
    "use name-only identity",
    "silently drop unresolved players",
    "combine drafted and UDFA cohorts without a flag",
    "label receptions as targets",
    "label sacks as pressures",
    "infer first down from yards alone",
    "use post-draft ADP",
    "use current camp/preseason information",
    "convert missing values to zero",
    "combine pro-day and official-combine results",
    "compare candidate on different rows without same-row baseline",
    "select feature form using outer-test results",
    "change Model V4 weights",
    "rescore the 2026 class",
    "alter Finished V1",
    "alter Outcome V3",
    "alter Trading Lab or active-pack data",
)


class GauntletContractError(RuntimeError):
    """Raised when research would cross an owning safety boundary."""


@dataclass(frozen=True)
class Fold:
    test_class: int
    train_classes: tuple[int, ...]


@dataclass(frozen=True)
class PromotionGate:
    median_delta: float
    favorable_fraction: float
    ndcg_delta: float
    spearman_delta: float
    calibration_deterioration: float
    same_row: bool
    stable: bool
    adequate_coverage: bool

    def passes(self) -> bool:
        material = self.ndcg_delta >= 0.01 or self.spearman_delta >= 0.02
        return (
            self.median_delta > 0
            and self.favorable_fraction >= 0.60
            and material
            and self.calibration_deterioration <= 0.01
            and self.same_row
            and self.stable
            and self.adequate_coverage
        )


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_snapshot_hash(path: str | Path, expected: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise GauntletContractError(f"snapshot hash mismatch: {actual} != {expected}")


def validate_join_mode(mode: str) -> None:
    if mode in PROHIBITED_JOIN_MODES or mode not in ALLOWED_JOIN_MODES:
        raise GauntletContractError(f"identity join mode is prohibited: {mode}")


def validate_feature_name(name: str) -> None:
    lowered = name.lower()
    if any(token in lowered for token in FORBIDDEN_FEATURE_TOKENS):
        raise GauntletContractError(f"forbidden feature token in {name}")
    if "target" in lowered and name not in {"target_name", "target_kind"}:
        raise GauntletContractError("receptions or provider usage may not be labeled targets")
    if "pressure" in lowered:
        raise GauntletContractError("sacks may not be labeled pressures")


def validate_outcome_season(draft_class: int, horizon: int, outcome_season: int) -> None:
    if draft_class == 2026 or outcome_season >= 2026:
        raise GauntletContractError("2026 NFL outcomes are prohibited")
    if horizon not in (1, 2, 3) or outcome_season != draft_class + horizon - 1:
        raise GauntletContractError("outcome season/horizon mismatch")
    if draft_class > MATURE_MAX_CLASS[f"Y{horizon}"]:
        raise GauntletContractError("outcome horizon is not mature as of 2026-07-31")


def chronological_outer_folds(
    draft_classes: Iterable[int], *, min_train_classes: int = 4
) -> tuple[Fold, ...]:
    classes = tuple(sorted(set(int(value) for value in draft_classes if int(value) < 2026)))
    folds = []
    for index, test_class in enumerate(classes):
        train = classes[:index]
        if len(train) >= min_train_classes:
            folds.append(Fold(test_class=test_class, train_classes=train))
    return tuple(folds)


def validate_fold(fold: Fold, normalization_classes: Sequence[int]) -> None:
    if not fold.train_classes or max(fold.train_classes) >= fold.test_class:
        raise GauntletContractError("outer fold uses same/future draft class")
    if any(int(value) >= fold.test_class for value in normalization_classes):
        raise GauntletContractError("future-class normalization is prohibited")


def same_row_ids(
    baseline_ids: Iterable[str], candidate_ids: Iterable[str]
) -> tuple[str, ...]:
    left = tuple(sorted(str(value) for value in baseline_ids))
    right = tuple(sorted(str(value) for value in candidate_ids))
    if left != right:
        raise GauntletContractError("candidate and baseline rows differ")
    return left


def safe_ratio(numerator: Any, denominator: Any) -> float | None:
    if numerator is None or denominator is None:
        return None
    try:
        top = float(numerator)
        bottom = float(denominator)
    except (TypeError, ValueError):
        return None
    if bottom <= 0:
        return None
    return top / bottom


def stable_rank(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: (float(values[index]), index))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        rank = (cursor + end - 1) / 2 + 1
        for index in order[cursor:end]:
            ranks[index] = rank
        cursor = end
    return ranks


def spearman(actual: Sequence[float], predicted: Sequence[float]) -> float | None:
    if len(actual) != len(predicted) or len(actual) < 2:
        return None
    left = stable_rank(actual)
    right = stable_rank(predicted)
    return pearson(left, right)


def pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum((a - mean_left) * (b - mean_right) for a, b in zip(left, right, strict=True))
    denom_left = math.sqrt(sum((value - mean_left) ** 2 for value in left))
    denom_right = math.sqrt(sum((value - mean_right) ** 2 for value in right))
    if denom_left == 0 or denom_right == 0:
        return None
    return numerator / (denom_left * denom_right)


def ndcg(actual: Sequence[float], predicted: Sequence[float]) -> float | None:
    if len(actual) != len(predicted) or not actual:
        return None
    floor = min(actual)
    relevance = [max(0.0, float(value) - floor) for value in actual]
    predicted_order = sorted(range(len(actual)), key=lambda i: (-predicted[i], i))
    ideal_order = sorted(range(len(actual)), key=lambda i: (-relevance[i], i))

    def dcg(order: Sequence[int]) -> float:
        return sum(relevance[index] / math.log2(rank + 2) for rank, index in enumerate(order))

    ideal = dcg(ideal_order)
    return dcg(predicted_order) / ideal if ideal > 0 else None


def pr_auc(actual: Sequence[int], probability: Sequence[float]) -> float | None:
    positives = sum(int(value) for value in actual)
    if not actual or positives == 0:
        return None
    ordered = sorted(range(len(actual)), key=lambda i: (-probability[i], i))
    true_positive = 0
    prior_recall = 0.0
    area = 0.0
    for rank, index in enumerate(ordered, start=1):
        if int(actual[index]) == 1:
            true_positive += 1
            recall = true_positive / positives
            precision = true_positive / rank
            area += (recall - prior_recall) * precision
            prior_recall = recall
    return area


def expected_calibration_error(
    actual: Sequence[int], probability: Sequence[float], *, bins: int = 5
) -> float | None:
    if not actual:
        return None
    total = len(actual)
    error = 0.0
    for bucket in range(bins):
        low = bucket / bins
        high = (bucket + 1) / bins
        ids = [
            index
            for index, value in enumerate(probability)
            if value >= low and (value < high or (bucket == bins - 1 and value <= high))
        ]
        if not ids:
            continue
        observed = sum(actual[index] for index in ids) / len(ids)
        forecast = sum(probability[index] for index in ids) / len(ids)
        error += len(ids) / total * abs(observed - forecast)
    return error


def validate_mutation(name: str) -> None:
    if name not in MUTATIONS:
        raise GauntletContractError(f"unknown mutation: {name}")
    raise GauntletContractError(f"mutation blocked: {name}")


def validate_output_path(relative_path: str | Path) -> None:
    normalized = str(relative_path).replace("\\", "/").lower()
    allowed = "docs/hq/master/nwr_rookie_historical_opportunity_feature_gauntlet_v1_20260731/"
    if not normalized.startswith(allowed):
        raise GauntletContractError("research output attempted to leave governed packet")
    protected = ("data_packs/", "local_exports/", "app/", "src/services/trading_lab")
    if any(token in normalized for token in protected):
        raise GauntletContractError("protected production/state path is not a write target")


def preservation_hashes(paths: Mapping[str, str | Path]) -> dict[str, str]:
    return {name: sha256_file(path) for name, path in sorted(paths.items())}
