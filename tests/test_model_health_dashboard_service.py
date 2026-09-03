import pytest

from src.services.model_health_dashboard_service import (
    HEALTH_AREA_PICK_SCORE,
    HEALTH_AREA_QB,
    HEALTH_AREA_TEAM_SCORE,
    SMALL_SAMPLE_THRESHOLD,
    ModelHealthDashboardError,
    ModelHealthMetric,
    build_model_health_report,
    filter_confident_metrics,
    is_small_sample,
)


def test_is_small_sample_uses_the_declared_threshold() -> None:
    assert is_small_sample(SMALL_SAMPLE_THRESHOLD - 1) is True
    assert is_small_sample(SMALL_SAMPLE_THRESHOLD) is False


def test_metric_rejects_an_unknown_health_area() -> None:
    with pytest.raises(ModelHealthDashboardError):
        ModelHealthMetric(health_area="NOT_A_REAL_AREA", metric_name="x", value=1.0, sample_size=10)


def test_metric_flags_low_confidence_below_the_threshold() -> None:
    metric = ModelHealthMetric(
        health_area=HEALTH_AREA_TEAM_SCORE, metric_name="spearman", value=0.6, sample_size=5,
    )
    assert metric.low_confidence is True


def test_metric_does_not_flag_a_well_supported_sample() -> None:
    metric = ModelHealthMetric(
        health_area=HEALTH_AREA_TEAM_SCORE, metric_name="spearman", value=0.6, sample_size=200,
    )
    assert metric.low_confidence is False


def test_build_model_health_report_groups_by_area_and_counts_low_confidence() -> None:
    metrics = [
        ModelHealthMetric(HEALTH_AREA_TEAM_SCORE, "spearman", 0.6, 200),
        ModelHealthMetric(HEALTH_AREA_QB, "mean_regret", 1.2, 5, position="QB"),
        ModelHealthMetric(HEALTH_AREA_PICK_SCORE, "regret", 0.3, 8),
    ]
    report = build_model_health_report(metrics)
    assert len(report.metrics_by_area[HEALTH_AREA_TEAM_SCORE]) == 1
    assert len(report.metrics_by_area[HEALTH_AREA_QB]) == 1
    assert report.low_confidence_count == 2
    assert report.total_sample_size == 213


def test_filter_confident_metrics_excludes_small_n_by_default() -> None:
    metrics = [
        ModelHealthMetric(HEALTH_AREA_TEAM_SCORE, "spearman", 0.6, 200),
        ModelHealthMetric(HEALTH_AREA_TEAM_SCORE, "kendall", 0.5, 3),
    ]
    report = build_model_health_report(metrics)
    confident = filter_confident_metrics(report, health_area=HEALTH_AREA_TEAM_SCORE)
    assert len(confident) == 1
    assert confident[0].metric_name == "spearman"


def test_filter_confident_metrics_across_all_areas_when_unrestricted() -> None:
    metrics = [
        ModelHealthMetric(HEALTH_AREA_TEAM_SCORE, "spearman", 0.6, 200),
        ModelHealthMetric(HEALTH_AREA_QB, "mean_regret", 1.2, 500),
    ]
    report = build_model_health_report(metrics)
    confident = filter_confident_metrics(report)
    assert len(confident) == 2
