from __future__ import annotations

from dataclasses import dataclass

from src.services.lve_stats_first_preview_service import (
    stats_first_preview_review_rows,
    stats_first_preview_review_summary_rows,
    stats_first_preview_snapshot_rows,
)
from src.services.lve_stats_first_veteran_formula_service import (
    score_stats_first_veteran_row,
)


@dataclass(frozen=True)
class StatsFirstCalibrationReport:
    scenario_rows: list[dict[str, object]]
    sensitivity_rows: list[dict[str, object]]
    preview_rows: list[dict[str, object]]
    summary_rows: list[dict[str, object]]


def build_stats_first_calibration_report(
    preview_root: str = "local_exports/nflverse_model_previews",
) -> StatsFirstCalibrationReport:
    scenarios = _scenario_rows()
    sensitivity = _sensitivity_rows()
    preview_rows = stats_first_preview_replay_rows(preview_root)
    return StatsFirstCalibrationReport(
        scenario_rows=scenarios,
        sensitivity_rows=sensitivity,
        preview_rows=preview_rows,
        summary_rows=_summary_rows(scenarios, sensitivity, preview_rows),
    )


def stats_first_preview_replay_rows(
    preview_root: str,
) -> list[dict[str, object]]:
    snapshots = stats_first_preview_snapshot_rows(preview_root)
    review_rows = stats_first_preview_review_rows(preview_root)
    review_summary = stats_first_preview_review_summary_rows(review_rows)
    review_counts = {
        str(row["review_status"]): int(row["rows"])
        for row in review_summary
        if str(row.get("review_status") or "") != "needed"
    }
    rows: list[dict[str, object]] = []
    for snapshot in snapshots:
        rows.append(
            {
                "preview_id": snapshot.get("preview_id", ""),
                "created_at": snapshot.get("created_at", ""),
                "model_version": snapshot.get("model_version", ""),
                "row_count": snapshot.get("row_count", 0),
                "preview_review_status": snapshot.get("review_status", ""),
                "ready_rows": review_counts.get("ready", 0),
                "review_rows": review_counts.get("review", 0),
                "blocked_rows": review_counts.get("blocked", 0),
                "calibration_note": (
                    "Preview replay is review-only; compare movements before apply."
                ),
            }
        )
    if not rows:
        rows.append(
            {
                "preview_id": "",
                "created_at": "",
                "model_version": "",
                "row_count": 0,
                "preview_review_status": "needed",
                "ready_rows": 0,
                "review_rows": 0,
                "blocked_rows": 0,
                "calibration_note": "Create a stats-first preview before replay review.",
            }
        )
    return rows


def stats_first_calibration_readiness_rows(
    report: StatsFirstCalibrationReport,
) -> list[dict[str, object]]:
    scenario_count = len(report.scenario_rows)
    scenario_passes = sum(1 for row in report.scenario_rows if row["passed"])
    high_volatility = sum(1 for row in report.sensitivity_rows if row["volatility"] == "high")
    preview_blocked = sum(int(row.get("blocked_rows") or 0) for row in report.preview_rows)
    return [
        {
            "area": "stats_first_scenarios",
            "status": "ready" if scenario_passes == scenario_count else "review",
            "value": f"{scenario_passes}/{scenario_count}",
            "meaning": "Stats-first fixtures behave as expected."
            if scenario_passes == scenario_count
            else "At least one stats-first fixture needs formula review.",
        },
        {
            "area": "stats_first_sensitivity",
            "status": "ready" if high_volatility == 0 else "review",
            "value": high_volatility,
            "meaning": "Tested input perturbations are not highly volatile."
            if high_volatility == 0
            else "A tested input produces too much movement.",
        },
        {
            "area": "preview_replay",
            "status": "review" if preview_blocked else "ready",
            "value": preview_blocked,
            "meaning": "No blocked stats-first preview rows."
            if not preview_blocked
            else "Blocked preview rows must be fixed before apply.",
        },
        {
            "area": "current_score_safety",
            "status": "ready",
            "value": "isolated",
            "meaning": "Calibration rows do not mutate live model outputs.",
        },
    ]


def _scenario_rows() -> list[dict[str, object]]:
    obvious_keep = score_stats_first_veteran_row(_wr_row("obvious_keep", projection=92, role=91))
    obvious_cut = score_stats_first_veteran_row(
        _rb_row(
            "obvious_cut",
            projection=44,
            role=42,
            workload=38,
            fit=40,
            age=35,
            injury=50,
        )
    )
    solid_wr = score_stats_first_veteran_row(_wr_row("solid_wr", projection=82, role=84))
    speculative_rb = score_stats_first_veteran_row(
        _rb_row("speculative_rb", projection=74, role=58, workload=56, fit=55)
    )
    pocket_qb = score_stats_first_veteran_row(
        _base_row(
            "pocket_qb",
            "QB",
            projection=84,
            role=86,
            first_down_fit=42,
            market=95,
        )
    )
    no_premium_te = score_stats_first_veteran_row(
        _base_row(
            "no_premium_te",
            "TE",
            projection=77,
            role=74,
            target=66,
            route=64,
            first_down_fit=69,
            market=90,
        )
    )
    market_low = score_stats_first_veteran_row(_wr_row("market_low", market=5))
    market_high = score_stats_first_veteran_row(_wr_row("market_high", market=100))
    brian_thomas = score_stats_first_veteran_row(
        _wr_row(
            "brian_thomas_jr",
            projection=88,
            role=86,
            target=84,
            route=87,
            first_down_fit=84,
            age=92,
            injury=82,
        )
        | {
            "player_name": "Brian Thomas Jr.",
            "draft_year": "2024",
            "draft_round": "1",
            "draft_ovr": "23",
            "confidence": "88",
        }
    )
    luther_burden = score_stats_first_veteran_row(
        _wr_row(
            "luther_burden",
            projection=50,
            role=23,
            target=0,
            route=0,
            first_down_fit=50,
            age=92,
            injury=92,
        )
        | {
            "player_name": "Luther Burden",
            "draft_year": "2025",
            "draft_round": "2",
            "draft_ovr": "39",
            "confidence": "82",
            "warnings": (
                "missing_lve_scoring_history|missing_projection_features|"
                "missing_participation_proxy"
            ),
        }
    )
    chase_brown = score_stats_first_veteran_row(
        _rb_row(
            "chase_brown",
            projection=84,
            role=82,
            workload=80,
            fit=78,
            age=78,
            injury=76,
        )
        | {
            "player_name": "Chase Brown",
            "draft_year": "2023",
            "draft_round": "5",
            "draft_ovr": "163",
            "confidence": "84",
        }
    )
    kaleb_johnson = score_stats_first_veteran_row(
        _rb_row(
            "kaleb_johnson",
            projection=58,
            role=52,
            workload=58,
            fit=72,
            age=91,
            injury=84,
        )
        | {
            "player_name": "Kaleb Johnson",
            "draft_year": "2025",
            "draft_round": "3",
            "draft_ovr": "83",
            "confidence": "80",
            "warnings": "missing_lve_scoring_history|missing_participation_proxy",
        }
    )
    older_fragile_rb = score_stats_first_veteran_row(
        _rb_row(
            "older_fragile_rb",
            projection=68,
            role=66,
            workload=64,
            fit=64,
            age=44,
            injury=48,
        )
        | {"player_name": "Older Fragile RB"}
    )
    jayden_higgins = score_stats_first_veteran_row(
        _wr_row(
            "jayden_higgins",
            projection=50,
            role=45,
            target=50,
            route=50,
            first_down_fit=56,
            age=92,
            injury=88,
        )
        | {
            "player_name": "Jayden Higgins",
            "draft_year": "2025",
            "draft_round": "2",
            "draft_ovr": "34",
            "confidence": "80",
            "warnings": "missing_lve_scoring_history|missing_projection_features",
        }
    )
    low_upside_veteran_wr = score_stats_first_veteran_row(
        _wr_row(
            "low_upside_veteran_wr",
            projection=56,
            role=58,
            target=52,
            route=58,
            first_down_fit=52,
            age=58,
            injury=74,
        )
        | {"player_name": "Low Upside Veteran WR", "draft_year": "2020"}
    )
    high_cap_limited_wr = score_stats_first_veteran_row(
        _wr_row(
            "high_cap_limited_wr",
            projection=50,
            role=50,
            target=50,
            route=50,
            first_down_fit=50,
            age=92,
            injury=86,
        )
        | {
            "player_name": "High Draft-Capital Young WR",
            "draft_year": "2025",
            "draft_round": "1",
            "draft_ovr": "18",
            "confidence": "80",
            "warnings": "missing_lve_scoring_history|missing_participation_proxy",
        }
    )
    low_cap_limited_wr = score_stats_first_veteran_row(
        _wr_row(
            "low_cap_limited_wr",
            projection=50,
            role=50,
            target=50,
            route=50,
            first_down_fit=50,
            age=92,
            injury=86,
        )
        | {
            "player_name": "Low Draft-Capital Young WR",
            "draft_year": "2025",
            "draft_round": "6",
            "draft_ovr": "185",
            "confidence": "80",
            "warnings": "missing_lve_scoring_history|missing_participation_proxy",
        }
    )
    young_uncertain_rb = score_stats_first_veteran_row(
        _rb_row(
            "young_uncertain_rb",
            projection=52,
            role=44,
            workload=46,
            fit=62,
            age=92,
            injury=82,
        )
        | {
            "player_name": "Young RB With Uncertain Role",
            "draft_year": "2025",
            "draft_round": "3",
            "draft_ovr": "90",
            "confidence": "78",
            "warnings": "missing_participation_proxy",
        }
    )
    established_strong = score_stats_first_veteran_row(
        _wr_row(
            "established_strong_veteran",
            projection=86,
            role=88,
            target=86,
            route=88,
            first_down_fit=84,
            age=78,
            injury=82,
        )
        | {"player_name": "Established Strong Veteran", "draft_year": "2020"}
    )
    return [
        _scenario(
            "obvious_keep",
            "veteran",
            "Elite stats-first profile should be a strong keeper.",
            f"keeper={obvious_keep.keeper_score}, drop={obvious_keep.drop_candidate_score}",
            obvious_keep.keeper_score >= 82 and obvious_keep.drop_candidate_score < 25,
            "Checks the model does not over-cut strong football profiles.",
        ),
        _scenario(
            "obvious_cut",
            "veteran",
            "Weak role/production profile should be a release candidate.",
            f"keeper={obvious_cut.keeper_score}, drop={obvious_cut.drop_candidate_score}",
            obvious_cut.keeper_score < 55 and obvious_cut.drop_candidate_score >= 45,
            "Checks low stat signal does not survive as a false keep.",
        ),
        _scenario(
            "solid_wr_over_speculative_rb",
            "lve_lineup",
            "A solid WR should beat a speculative RB shot.",
            f"wr={solid_wr.keeper_score}, rb={speculative_rb.keeper_score}",
            solid_wr.keeper_score > speculative_rb.keeper_score,
            "Matches LVE philosophy: prefer bankable WR signal over thin RB bets.",
        ),
        _scenario(
            "qb_1qb_suppression",
            "format_gate",
            "Non-elite QB should remain suppressed in 1QB.",
            f"keeper={pocket_qb.keeper_score}, adjustment={pocket_qb.structural_adjustment}",
            pocket_qb.structural_adjustment <= -8 and pocket_qb.keeper_score < 82,
            "Protects against Superflex drift.",
        ),
        _scenario(
            "te_no_premium_suppression",
            "format_gate",
            "Non-elite TE should stay suppressed without TE premium.",
            (
                f"keeper={no_premium_te.keeper_score}, "
                f"adjustment={no_premium_te.structural_adjustment}"
            ),
            no_premium_te.structural_adjustment <= -8 and no_premium_te.keeper_score < 78,
            "Protects against TE-premium drift.",
        ),
        _scenario(
            "market_not_private_value",
            "market_guardrail",
            "Market should not change private LVE value.",
            f"low={market_low.private_lve_value}, high={market_high.private_lve_value}",
            market_low.private_lve_value == market_high.private_lve_value
            and market_high.trade_value > market_low.trade_value,
            "Keeps private value statistics-first while preserving trade liquidity.",
        ),
        _scenario(
            "brian_thomas_jr_over_luther_burden",
            "young_nfl_bridge",
            "Strong year-two NFL evidence should beat year-one draft prior alone.",
            _comparison_observed(brian_thomas, luther_burden),
            brian_thomas.keeper_score > luther_burden.keeper_score
            and _has_bridge_receipts(luther_burden),
            _receipt_notes(
                luther_burden,
                "BTJ should not lose to Luther unless Luther has receipts beyond draft prior.",
            ),
        ),
        _scenario(
            "chase_brown_over_luther_burden",
            "young_nfl_bridge",
            "A productive year-three RB should beat a year-one WR with no NFL evidence.",
            _comparison_observed(chase_brown, luther_burden),
            chase_brown.keeper_score > luther_burden.keeper_score
            and _has_bridge_receipts(luther_burden),
            _receipt_notes(
                luther_burden,
                "If Luther jumps Chase, receipts must show real NFL evidence, not only capital.",
            ),
        ),
        _scenario(
            "kaleb_johnson_over_older_fragile_rb",
            "young_nfl_bridge",
            "Young RB draft prior can beat an older fragile RB profile.",
            _comparison_observed(kaleb_johnson, older_fragile_rb),
            kaleb_johnson.keeper_score > older_fragile_rb.keeper_score
            and _has_bridge_receipts(kaleb_johnson),
            _receipt_notes(kaleb_johnson, "Kaleb needs bridge receipts and age/health support."),
        ),
        _scenario(
            "jayden_higgins_over_low_upside_veteran_wr",
            "young_nfl_bridge",
            "Young second-round WR can beat a low-upside veteran WR.",
            _comparison_observed(jayden_higgins, low_upside_veteran_wr),
            jayden_higgins.keeper_score > low_upside_veteran_wr.keeper_score
            and _has_bridge_receipts(jayden_higgins),
            _receipt_notes(
                jayden_higgins,
                "Jayden must show bridge contribution, not fake production.",
            ),
        ),
        _scenario(
            "high_cap_limited_wr_review_needed",
            "young_nfl_bridge",
            "High-capital young WR with limited production should stay review-needed.",
            (
                f"keeper={high_cap_limited_wr.keeper_score}, "
                f"warning={high_cap_limited_wr.warning_status}, "
                f"bridge={high_cap_limited_wr.young_nfl_bridge_weight}"
            ),
            high_cap_limited_wr.warning_status in {"review_needed", "model_warning"}
            and _has_bridge_receipts(high_cap_limited_wr),
            _receipt_notes(
                high_cap_limited_wr,
                "Capital can preserve upside but cannot create certainty.",
            ),
        ),
        _scenario(
            "low_cap_limited_wr_not_boosted",
            "young_nfl_bridge",
            "Low-capital young WR with limited production should not be boosted into keep range.",
            (
                f"keeper={low_cap_limited_wr.keeper_score}, "
                f"prior={low_cap_limited_wr.young_nfl_bridge_prior_score}"
            ),
            low_cap_limited_wr.keeper_score < high_cap_limited_wr.keeper_score
            and low_cap_limited_wr.young_nfl_bridge_prior_score < 50,
            _receipt_notes(
                low_cap_limited_wr,
                "Low draft capital should remain visible as caution.",
            ),
        ),
        _scenario(
            "young_rb_uncertain_role_review_needed",
            "young_nfl_bridge",
            "Young RB with uncertain role should be review-needed, not blindly boosted.",
            (
                f"keeper={young_uncertain_rb.keeper_score}, "
                f"warning={young_uncertain_rb.warning_status}, "
                f"bridge={young_uncertain_rb.young_nfl_bridge_weight}"
            ),
            young_uncertain_rb.keeper_score < 75
            and young_uncertain_rb.warning_status in {"review_needed", "model_warning"}
            and _has_bridge_receipts(young_uncertain_rb),
            _receipt_notes(
                young_uncertain_rb,
                "Role uncertainty should remain in the warning path.",
            ),
        ),
        _scenario(
            "established_strong_veteran_over_young_limited",
            "young_nfl_bridge",
            "Established veteran with strong production should beat limited young profiles.",
            _comparison_observed(established_strong, high_cap_limited_wr),
            established_strong.keeper_score > high_cap_limited_wr.keeper_score
            and established_strong.young_nfl_bridge_weight == 0,
            "Strong real NFL evidence should win and should not carry bridge receipts.",
        ),
    ]


def _sensitivity_rows() -> list[dict[str, object]]:
    baseline = score_stats_first_veteran_row(_wr_row("sensitivity_wr", projection=82, role=84))
    role_plus = score_stats_first_veteran_row(_wr_row("sensitivity_wr", projection=82, role=89))
    market_plus = score_stats_first_veteran_row(
        _wr_row("sensitivity_wr", projection=82, role=84, market=55)
    )
    rows = [
        _sensitivity(
            "wr_role_security_plus_5",
            "role_security",
            baseline.keeper_score,
            role_plus.keeper_score,
        ),
        _sensitivity(
            "wr_market_liquidity_plus_5",
            "market_liquidity",
            baseline.keeper_score,
            market_plus.keeper_score,
        ),
        _sensitivity(
            "market_private_value_guardrail",
            "market_liquidity",
            baseline.private_lve_value,
            market_plus.private_lve_value,
        ),
    ]
    return rows


def _summary_rows(
    scenarios: list[dict[str, object]],
    sensitivity: list[dict[str, object]],
    preview_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "area": "scenario_pass_rate",
            "value": f"{sum(row['passed'] for row in scenarios)}/{len(scenarios)}",
            "notes": "Stats-first formula fixtures check LVE-specific traps.",
        },
        {
            "area": "max_sensitivity_change",
            "value": max(float(row["absolute_change"]) for row in sensitivity),
            "notes": "Single input perturbations should not create wild movement.",
        },
        {
            "area": "preview_replay_rows",
            "value": len(preview_rows),
            "notes": "Preview replay rows are review-only and do not alter current boards.",
        },
    ]


def _scenario(
    scenario_id: str,
    category: str,
    expected: str,
    observed: str,
    passed: bool,
    notes: str,
) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "category": category,
        "expected_behavior": expected,
        "observed_behavior": observed,
        "passed": passed,
        "notes": notes,
    }


def _comparison_observed(left: object, right: object) -> str:
    return (
        f"{left.player_name} keeper={left.keeper_score}, private={left.private_lve_value}, "
        f"warning={left.warning_status}; {right.player_name} keeper={right.keeper_score}, "
        f"private={right.private_lve_value}, warning={right.warning_status}"
    )


def _has_bridge_receipts(score: object) -> bool:
    receipt_features = {contribution.feature_name for contribution in score.contributions}
    return {
        "draft_capital_prior_score",
        "young_nfl_bridge_decay_weight",
        "young_nfl_bridge_nfl_evidence_weight",
        "young_nfl_bridge_prior",
    }.issubset(receipt_features)


def _receipt_notes(score: object, note: str) -> str:
    receipt_features = sorted(
        contribution.feature_name
        for contribution in score.contributions
        if contribution.feature_name.startswith("young_nfl_bridge")
        or contribution.feature_name == "draft_capital_prior_score"
    )
    return f"{note} receipt_features={','.join(receipt_features)}"


def _sensitivity(
    scenario_id: str,
    feature_name: str,
    baseline: float,
    perturbed: float,
) -> dict[str, object]:
    change = round(abs(perturbed - baseline), 2)
    return {
        "scenario_id": scenario_id,
        "feature_name": feature_name,
        "baseline_score": baseline,
        "perturbed_score": perturbed,
        "absolute_change": change,
        "volatility": "high" if change >= 6 else "medium" if change >= 3 else "low",
    }


def _wr_row(
    player_id: str,
    *,
    projection: float = 82,
    role: float = 84,
    target: float = 82,
    route: float | None = None,
    first_down_fit: float = 80,
    age: float = 80,
    injury: float = 80,
    market: float = 50,
) -> dict[str, object]:
    return _base_row(
        player_id,
        "WR",
        projection=projection,
        role=role,
        target=target,
        route=role if route is None else route,
        first_down_fit=first_down_fit,
        age=age,
        injury=injury,
        market=market,
    )


def _rb_row(
    player_id: str,
    *,
    projection: float,
    role: float,
    workload: float,
    fit: float,
    age: float = 82,
    injury: float = 76,
) -> dict[str, object]:
    row = _base_row(
        player_id,
        "RB",
        projection=projection,
        role=role,
        target=50,
        route=50,
        first_down_fit=fit,
        age=age,
        injury=injury,
    )
    row["workload_earning"] = workload
    return row


def _base_row(
    player_id: str,
    position: str,
    *,
    projection: float,
    role: float,
    target: float = 70,
    route: float = 70,
    first_down_fit: float = 70,
    age: float = 78,
    injury: float = 78,
    market: float = 50,
) -> dict[str, object]:
    return {
        "season": "2026",
        "player_id": player_id,
        "player_name": player_id.replace("_", " ").title(),
        "position": position,
        "team": "CAL",
        "weighted_recent_lve_ppg_score": projection,
        "expected_lve_points_score": projection,
        "lve_projection_value": projection,
        "role_security": role,
        "workload_earning": role,
        "target_earning_stability": target,
        "route_role": route,
        "first_down_td_fit": first_down_fit,
        "age_curve": age,
        "injury_durability": injury,
        "confidence": 88,
        "missing_data_penalty": 0,
        "warnings": "",
        "market_liquidity": market,
    }
