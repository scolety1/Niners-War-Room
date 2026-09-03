"""Calibration toolkit: Pick Score / Team Score / Championship Equity
calibrators (sections 9-11 of the follow-up directive).

Implemented now, with NO meaningful parameters fit from synthetic data --
every fit function requires the caller to state `data_source` and, when
it is not real evidence, marks the resulting model
`PIPELINE_TEST_ONLY` in its own `model_version` string, so a synthetic
fit can never be mistaken for a real calibration later. No historical or
synthetic fit performed by this module itself is ever silently treated
as meaningful; that judgment stays with the caller and is recorded on
the model object.

Pure Python (no numpy/scipy/sklearn dependency) -- draft-sized data (tens
to a few hundred points), so a hand-written Pool Adjacent Violators
isotonic fit and a Pearson-on-ranks Spearman (already in
`outcome_evaluation_framework_service`) are all this needs.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from src.services.outcome_evaluation_framework_service import (
    OUTCOME_EVALUATION_SOURCES,
    spearman_rank_correlation,
)

PIPELINE_TEST_ONLY = "PIPELINE_TEST_ONLY"
REAL_EVIDENCE = "REAL_EVIDENCE"
DATA_SOURCE_LABELS = frozenset({PIPELINE_TEST_ONLY, REAL_EVIDENCE})


class CalibrationToolkitError(ValueError):
    pass


# --- Shared monotonic transform primitive (Pool Adjacent Violators) --------


@dataclass(frozen=True)
class IsotonicModel:
    """A fitted, non-decreasing step function: x -> y. `knots` are
    (x, y) breakpoints in ascending x order; predict() does nearest-
    left-neighbor lookup (standard isotonic-regression prediction)."""

    knots: tuple[tuple[float, float], ...]
    data_source: str
    model_version: str
    sample_size: int

    def predict(self, x: float) -> float:
        if not self.knots:
            raise CalibrationToolkitError("Cannot predict from an empty IsotonicModel.")
        if x <= self.knots[0][0]:
            return self.knots[0][1]
        if x >= self.knots[-1][0]:
            return self.knots[-1][1]
        for i in range(len(self.knots) - 1):
            lo_x, lo_y = self.knots[i]
            hi_x, hi_y = self.knots[i + 1]
            if lo_x <= x <= hi_x:
                if hi_x == lo_x:
                    return lo_y
                fraction = (x - lo_x) / (hi_x - lo_x)
                return lo_y + fraction * (hi_y - lo_y)
        return self.knots[-1][1]


def fit_isotonic_regression(
    x: Sequence[float], y: Sequence[float], *, data_source: str, model_version: str
) -> IsotonicModel:
    """Pool Adjacent Violators Algorithm -- a standard, exact isotonic
    (non-decreasing) least-squares fit. `data_source` must be
    PIPELINE_TEST_ONLY or REAL_EVIDENCE; there is no default, so a
    caller can never accidentally fit "real" without saying so."""
    if data_source not in DATA_SOURCE_LABELS:
        raise CalibrationToolkitError(f"Unknown data_source: {data_source!r}")
    if len(x) != len(y):
        raise CalibrationToolkitError("x and y must be the same length.")
    if len(x) < 2:
        raise CalibrationToolkitError("Isotonic regression needs at least 2 points.")
    order = sorted(range(len(x)), key=lambda i: x[i])
    sorted_x = [x[i] for i in order]
    sorted_y = [y[i] for i in order]

    # PAVA: maintain a stack of (sum_y, count, x_start) blocks; merge
    # adjacent blocks whenever the running mean would decrease.
    blocks: list[list[float]] = []  # each: [sum_y, count, x_min, x_max]
    for xi, yi in zip(sorted_x, sorted_y, strict=True):
        blocks.append([yi, 1, xi, xi])
        while len(blocks) > 1 and (blocks[-2][0] / blocks[-2][1]) > (blocks[-1][0] / blocks[-1][1]):
            prev = blocks.pop()
            blocks[-1][0] += prev[0]
            blocks[-1][1] += prev[1]
            blocks[-1][3] = prev[3]

    knots: list[tuple[float, float]] = []
    for sum_y, count, x_min, x_max in blocks:
        mean_y = sum_y / count
        knots.append((x_min, mean_y))
        if x_max != x_min:
            knots.append((x_max, mean_y))
    return IsotonicModel(
        knots=tuple(knots), data_source=data_source, model_version=model_version,
        sample_size=len(x),
    )


# --- Pick Score calibrator (section 9) --------------------------------------

PICK_SCORE_CALIBRATOR_VERSION = "pick-score-calibrator-v1"


@dataclass(frozen=True)
class PickScoreCalibrationModel:
    isotonic: IsotonicModel
    data_source: str
    model_version: str

    def calibrate(self, raw_decision_utility: float) -> float:
        """Maps a raw decision utility to a 0-100 owner-facing scale via
        the fitted monotonic transform, then clamps -- higher raw utility
        never produces a lower calibrated score (monotonic by
        construction from the isotonic fit)."""
        value = self.isotonic.predict(raw_decision_utility)
        return round(min(100.0, max(0.0, value)), 2)


def fit_pick_score_calibrator(
    raw_utility_and_realized_quality: Sequence[tuple[float, float]],
    *,
    data_source: str,
) -> PickScoreCalibrationModel:
    """`realized_quality` must already be on a 0-100 scale (the caller's
    responsibility -- e.g. a percentile of realized pick outcomes). The
    semantic goal is deliberately NOT "Pick Score = probability of being
    correct" -- only "higher Pick Score = historically stronger decision"
    -- see docs/codex/RAW_DECISION_UTILITY_CONSTRUCTION_20260903.md."""
    if not raw_utility_and_realized_quality:
        raise CalibrationToolkitError("Need at least one (raw_utility, realized_quality) pair.")
    xs = [pair[0] for pair in raw_utility_and_realized_quality]
    ys = [pair[1] for pair in raw_utility_and_realized_quality]
    model_version = (
        f"{PICK_SCORE_CALIBRATOR_VERSION}:{PIPELINE_TEST_ONLY}"
        if data_source == PIPELINE_TEST_ONLY
        else PICK_SCORE_CALIBRATOR_VERSION
    )
    isotonic = fit_isotonic_regression(
        xs, ys, data_source=data_source, model_version=model_version
    )
    return PickScoreCalibrationModel(
        isotonic=isotonic, data_source=data_source, model_version=model_version,
    )


# --- Team Score calibrator (section 10) -------------------------------------


@dataclass(frozen=True)
class TeamScoreBucket:
    bucket_index: int
    score_range: tuple[float, float]
    mean_realized_value: float
    sample_size: int


@dataclass(frozen=True)
class TeamScoreCalibrationReport:
    data_source: str
    buckets: tuple[TeamScoreBucket, ...]
    monotonic: bool
    spearman: float | None
    sample_size: int


def bucket_team_score_outcomes(
    team_score_and_realized_value: Sequence[tuple[float, float]],
    *,
    data_source: str,
    bucket_count: int = 5,
) -> TeamScoreCalibrationReport:
    """Buckets (Team Score percentile, realized roster value) pairs into
    `bucket_count` equal-width Team Score ranges, reports the mean
    realized value per bucket and whether those means are monotonically
    non-decreasing -- "do Team Score 80 rosters actually outperform Team
    Score 60 rosters?" answered directly, not asserted."""
    if data_source not in DATA_SOURCE_LABELS:
        raise CalibrationToolkitError(f"Unknown data_source: {data_source!r}")
    if not team_score_and_realized_value:
        raise CalibrationToolkitError("Need at least one (team_score, realized_value) pair.")
    scores = [pair[0] for pair in team_score_and_realized_value]
    values = [pair[1] for pair in team_score_and_realized_value]
    lo, hi = min(scores), max(scores)
    width = (hi - lo) / bucket_count if hi > lo else 1.0

    bucketed: list[list[float]] = [[] for _ in range(bucket_count)]
    for score, value in zip(scores, values, strict=True):
        index = min(bucket_count - 1, int((score - lo) / width)) if hi > lo else 0
        bucketed[index].append(value)

    buckets: list[TeamScoreBucket] = []
    means: list[float] = []
    for index, group in enumerate(bucketed):
        if not group:
            continue
        mean_value = sum(group) / len(group)
        means.append(mean_value)
        buckets.append(
            TeamScoreBucket(
                bucket_index=index,
                score_range=(round(lo + index * width, 2), round(lo + (index + 1) * width, 2)),
                mean_realized_value=round(mean_value, 4),
                sample_size=len(group),
            )
        )
    monotonic = all(means[i] <= means[i + 1] for i in range(len(means) - 1))
    return TeamScoreCalibrationReport(
        data_source=data_source, buckets=tuple(buckets), monotonic=monotonic,
        spearman=spearman_rank_correlation(scores, values),
        sample_size=len(team_score_and_realized_value),
    )


# --- Championship Equity calibrator (section 11) ----------------------------


@dataclass(frozen=True)
class ReliabilityBin:
    bin_index: int
    predicted_probability_range: tuple[float, float]
    mean_predicted_probability: float
    observed_frequency: float
    sample_size: int


@dataclass(frozen=True)
class ProbabilityCalibrationReport:
    label_source: str  # OBSERVED or SIMULATED -- never defaulted
    brier_score: float
    reliability_bins: tuple[ReliabilityBin, ...]
    expected_calibration_error: float
    sample_size: int


def evaluate_probability_calibration(
    predicted_probability_and_outcome: Sequence[tuple[float, float]],
    *,
    label_source: str,
    bin_count: int = 5,
) -> ProbabilityCalibrationReport:
    """`outcome` must be 0.0/1.0 (a real binary realized result) --
    `label_source` states plainly whether that 0/1 is an OBSERVED real
    championship result or a SIMULATED proxy outcome; this function
    never assumes OBSERVED and never invents a label. Do not invent
    observed win/loss labels when they do not exist -- the directive's
    own explicit instruction, enforced by requiring the caller to state
    label_source rather than defaulting it."""
    if label_source not in OUTCOME_EVALUATION_SOURCES:
        raise CalibrationToolkitError(f"Unknown label_source: {label_source!r}")
    if not predicted_probability_and_outcome:
        raise CalibrationToolkitError("Need at least one (predicted_probability, outcome) pair.")
    n = len(predicted_probability_and_outcome)
    brier = sum(
        (prob - outcome) ** 2 for prob, outcome in predicted_probability_and_outcome
    ) / n

    bins: list[list[tuple[float, float]]] = [[] for _ in range(bin_count)]
    for prob, outcome in predicted_probability_and_outcome:
        index = min(bin_count - 1, int(prob * bin_count))
        bins[index].append((prob, outcome))

    reliability_bins: list[ReliabilityBin] = []
    ece_terms = []
    for index, group in enumerate(bins):
        if not group:
            continue
        mean_pred = sum(p for p, _ in group) / len(group)
        observed_freq = sum(o for _, o in group) / len(group)
        reliability_bins.append(
            ReliabilityBin(
                bin_index=index,
                predicted_probability_range=(index / bin_count, (index + 1) / bin_count),
                mean_predicted_probability=round(mean_pred, 4),
                observed_frequency=round(observed_freq, 4),
                sample_size=len(group),
            )
        )
        ece_terms.append((len(group) / n) * abs(mean_pred - observed_freq))

    return ProbabilityCalibrationReport(
        label_source=label_source, brier_score=round(brier, 4),
        reliability_bins=tuple(reliability_bins),
        expected_calibration_error=round(sum(ece_terms), 4), sample_size=n,
    )
