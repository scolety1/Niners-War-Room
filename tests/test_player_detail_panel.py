from app.components.player_detail_panel import (
    PlayerDetail,
    detail_summary,
    display_value,
    warning_summary,
)


def test_display_value_marks_missing_values_honestly() -> None:
    assert display_value("") == "Missing"
    assert display_value(None) == "Missing"
    assert display_value("n/a") == "Missing"
    assert display_value("24.5") == "24.5"


def test_detail_summary_keeps_age_and_trust_missing_explicit() -> None:
    summary = detail_summary(PlayerDetail(player="Example Player"))

    assert summary["Age"] == "Age missing"
    assert summary["Trust"] == "Trust unknown"
    assert summary["Warnings"] == "No major warning"


def test_warning_summary_uses_human_labels() -> None:
    assert (
        warning_summary("model_edge_weirdness|no_premium_te_cap")
        == "Model edge; No-TE-premium cap"
    )


def test_detail_summary_combines_team_and_college() -> None:
    summary = detail_summary(
        PlayerDetail(player="Rookie", nfl_team="ARI", college="Notre Dame")
    )

    assert summary["NFL Team / College"] == "ARI / Notre Dame"
