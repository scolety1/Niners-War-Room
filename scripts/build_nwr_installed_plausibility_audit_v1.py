"""Build the read-only NWR installed plausibility audit evidence tables.

The script exercises the same framework-neutral facade used by the installed
desktop sidecar.  All writable service roots are explicit disposable paths.
It does not change ranks, projections, trade rules, or owner state.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.application.desktop_facade import DesktopBackendFacade


OUTPUT_ROOT = (
    REPO_ROOT / "docs" / "hq" / "product" / "nwr_installed_plausibility_audit_v1_20260813"
)
DISPOSABLE_ROOT = REPO_ROOT / ".qa-nwr-installed-plausibility-v1-20260813"


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value)


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: text(row.get(key)) for key in fieldnames})


def require_asset(name: str, options: list[dict[str, Any]]) -> str:
    matches = [row for row in options if row.get("name") == name]
    if len(matches) != 1:
        raise AssertionError(f"Expected one governed asset named {name!r}; found {len(matches)}")
    if matches[0].get("blocked"):
        raise AssertionError(f"Governed asset {name!r} is blocked")
    return str(matches[0]["assetId"])


def dimension_string(decision: dict[str, Any]) -> str:
    return "; ".join(
        f"{row['code']}={row['outcome']}({row['confidence']})"
        for row in decision.get("dimensions", [])
    )


def trade_row(
    facade: DesktopBackendFacade,
    asset_ids: dict[str, str],
    *,
    scenario_id: str,
    structural_type: str,
    give: list[str],
    receive: list[str],
    team_window: str,
    predeclared_expectation: str,
) -> dict[str, Any]:
    decision = facade.evaluate_dynasty_trade(
        give=[asset_ids[name] for name in give],
        receive=[asset_ids[name] for name in receive],
        team_window=team_window,
    ).data
    return {
        "scenario_id": scenario_id,
        "structural_type": structural_type,
        "team_window": team_window,
        "give": " | ".join(give),
        "receive": " | ".join(receive),
        "predeclared_expectation": predeclared_expectation,
        "recommendation": decision["recommendation"],
        "preferred_side": decision["preferredSide"],
        "confidence": decision["confidence"],
        "summary": decision["summary"],
        "main_uncertainty": decision["mainUncertainty"],
        "reasons": " || ".join(decision.get("reasons", [])),
        "what_would_change": " || ".join(decision.get("whatWouldChange", [])),
        "dimensions": dimension_string(decision),
        "counter_status": decision.get("counterStatus", ""),
        "counter_message": decision.get("counterMessage", ""),
    }


def pct(value: Any) -> float | None:
    raw = str(value or "").strip()
    if not raw or raw == "—" or not raw.endswith("%"):
        return None
    try:
        return float(raw[:-1])
    except ValueError:
        return None


def outcome_checks(outcome: dict[str, Any]) -> tuple[bool, bool, list[str]]:
    notes: list[str] = []
    values = [pct(value) for key, value in outcome.items() if key not in {"Player", "Pos", "NWR Rank"}]
    bounds_ok = all(value is None or 0 <= value <= 100 for value in values)
    nested_ok = True
    for prefix in ("2026", "2027", "2028", "Within 3Y", "Within 5Y", "2 of 3Y"):
        series = [pct(outcome.get(f"{prefix} T{threshold}")) for threshold in (6, 12, 24, 36)]
        observed = [value for value in series if value is not None]
        if any(left > right for left, right in zip(observed, observed[1:], strict=False)):
            nested_ok = False
            notes.append(f"{prefix} threshold nesting failed: {observed}")
    for threshold in (6, 12, 24, 36):
        three = pct(outcome.get(f"Within 3Y T{threshold}"))
        five = pct(outcome.get(f"Within 5Y T{threshold}"))
        if three is not None and five is not None and five < three:
            nested_ok = False
            notes.append(f"Within 5Y T{threshold} is below Within 3Y")
    return bounds_ok, nested_ok, notes


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    DISPOSABLE_ROOT.mkdir(parents=True, exist_ok=True)

    dynasty = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="dynasty",
        workspace_root=DISPOSABLE_ROOT / "workspace",
        legacy_workspace_root=DISPOSABLE_ROOT / "legacy-workspace",
    )
    dynasty_data = dynasty.dynasty_bootstrap().data
    options = list(dynasty_data["assetOptions"])
    names = {str(row["name"]) for row in options if not row.get("blocked")}
    required_names = {
        "Luther Burden", "Chris Bell", "2027 1st", "George Kittle", "Chuba Hubbard",
        "Brock Purdy", "2028 2nd", "2028 1st", "Puka Nacua", "Ja'Marr Chase",
        "DeVonta Smith", "D'Andre Swift", "2027 2nd", "Tetairoa McMillan",
        "Davante Adams", "Courtland Sutton", "Carnell Tate", "Christian McCaffrey",
        "Josh Allen", "A.J. Brown", "Jameson Williams", "Gabe Davis", "2028 1st",
        "De'Von Achane", "James Cook", "Jonathan Taylor", "Jeremiyah Love",
        "Trey McBride", "Kyle Pitts", "Brock Bowers", "Drake Maye", "Trevor Lawrence",
        "Jalen Hurts", "Bijan Robinson",
    }
    missing = sorted(required_names - names)
    if missing:
        raise AssertionError(f"Required governed assets are missing: {missing}")
    asset_ids = {name: require_asset(name, options) for name in required_names}

    # Ranking observations are selected by fixed rank before any outside comparison.
    sample_ranks = {1, 3, 8, 13, 20, 25, 29, 33, 45, 50, 51, 60, 75, 85, 100,
                    101, 117, 125, 150, 151, 175, 185, 200, 225, 240}
    ranking_rows: list[dict[str, Any]] = []
    for row in dynasty_data["rankings"]:
        if row.get("rank") is None:
            continue
        if int(row["rank"]) not in sample_ranks:
            continue
        rank = int(row["rank"])
        segment = "Top 25" if rank <= 25 else "26-50" if rank <= 50 else "51-100" if rank <= 100 else "101-200" if rank <= 200 else "201-240"
        ranking_rows.append({
            "segment": segment,
            "player": row["player"],
            "position": row["position"],
            "team": row["team"],
            "age": row["age"],
            "nwr_rank": rank,
            "position_rank": row["positionRank"],
            "nwr_score": row["nwrScore"],
            "market_rank_july17": row["marketRank"],
            "market_gap_july17": row["marketGap"],
            "market_band": row["marketBand"],
            "confidence": row["confidence"],
            "risk": row["risk"],
            "external_source": "",
            "external_rank_neighborhood": "",
            "difference": "",
            "direction": "",
            "format_compatibility": "",
            "classification": "PENDING_EXTERNAL_BENCHMARK",
            "nwr_explanation": "",
        })
    write_csv(OUTPUT_ROOT / "DYNASTY_RANKING_BENCHMARK.csv", ranking_rows, list(ranking_rows[0]))

    original_give = ["Luther Burden", "Chris Bell", "2027 1st"]
    original_receive = ["George Kittle", "Chuba Hubbard", "Brock Purdy", "2028 2nd"]
    perturbations = [
        ("T1", "Original", original_give, original_receive, "Balanced", "Baseline"),
        ("T2", "Remove outgoing 2027 1st", ["Luther Burden", "Chris Bell"], original_receive, "Balanced", "Must not become less favorable to owner"),
        ("T3", "Upgrade incoming pick", original_give, ["George Kittle", "Chuba Hubbard", "Brock Purdy", "2028 1st"], "Balanced", "Incoming side must not worsen"),
        ("T4", "Remove incoming Brock Purdy", original_give, ["George Kittle", "Chuba Hubbard", "2028 2nd"], "Balanced", "Incoming side must not improve without roster-fit explanation"),
        ("T5", "Replace Kittle with young premium", original_give, ["Puka Nacua", "Chuba Hubbard", "Brock Purdy", "2028 2nd"], "Balanced", "Move toward incoming side"),
        ("T6", "Remove outgoing Chris Bell", ["Luther Burden", "2027 1st"], original_receive, "Balanced", "Owner package becomes less expensive"),
        ("T7", "Contending window", original_give, original_receive, "Contending", "Only team-window interpretation changes"),
        ("T8", "Balanced window", original_give, original_receive, "Balanced", "Only team-window interpretation changes"),
        ("T9", "Rebuilding window", original_give, original_receive, "Rebuilding", "Only team-window interpretation changes"),
    ]
    perturbation_rows = [
        trade_row(dynasty, asset_ids, scenario_id=identifier, structural_type=kind,
                  give=give, receive=receive, team_window=window,
                  predeclared_expectation=expectation)
        for identifier, kind, give, receive, window, expectation in perturbations
    ]
    base = perturbation_rows[0]
    for row in perturbation_rows:
        row["before_recommendation"] = base["recommendation"]
        row["after_recommendation"] = row["recommendation"]
        row["before_preferred_side"] = base["preferred_side"]
        row["after_preferred_side"] = row["preferred_side"]
        row["monotonicity_review"] = "REVIEW_MANUALLY"
    write_csv(OUTPUT_ROOT / "TRADE_PERTURBATION_RESULTS.csv", perturbation_rows, list(perturbation_rows[0]))

    trade_scenarios = [
        ("S1", "Premium asset vs depth", ["Ja'Marr Chase"], ["DeVonta Smith", "D'Andre Swift", "2027 2nd"], "Balanced", "Premium side should remain credible despite depth"),
        ("S2", "Young WR vs aging producers", ["Tetairoa McMillan"], ["Davante Adams", "Courtland Sutton"], "Rebuilding", "Young WR should gain rebuilding preference"),
        ("S3", "Rookie plus pick vs veteran", ["Carnell Tate", "2027 1st"], ["Christian McCaffrey"], "Balanced", "Should surface separated rookie certainty and veteran age risk"),
        ("S4", "QB-heavy package in 1QB", ["Luther Burden"], ["Josh Allen", "Brock Purdy", "2027 2nd"], "Balanced", "QB depth should be discounted in 10-team 1QB"),
        ("S5", "Pick-heavy rebuilding trade", ["A.J. Brown"], ["2027 1st", "2028 1st", "2027 2nd"], "Rebuilding", "Rebuilding should value flexibility without inventing pick slots"),
        ("S6", "Close trade", ["DeVonta Smith"], ["Jameson Williams", "2027 2nd"], "Balanced", "Mixed/close result expected"),
        ("S7", "Clearly lopsided", ["Puka Nacua"], ["Gabe Davis", "2028 2nd"], "Balanced", "Strongly prefer premium side"),
    ]
    scenario_rows = [
        trade_row(dynasty, asset_ids, scenario_id=identifier, structural_type=kind,
                  give=give, receive=receive, team_window=window,
                  predeclared_expectation=expectation)
        for identifier, kind, give, receive, window, expectation in trade_scenarios
    ]
    write_csv(OUTPUT_ROOT / "TRADE_SCENARIO_RESULTS.csv", scenario_rows, list(scenario_rows[0]))

    compare_pairs = [
        ("C1", "Elite WR vs elite WR", "Puka Nacua", "Ja'Marr Chase"),
        ("C2", "Young RB vs established RB", "De'Von Achane", "Jonathan Taylor"),
        ("C3", "Young WR vs aging WR", "Tetairoa McMillan", "Davante Adams"),
        ("C4", "Veteran vs rookie", "Courtland Sutton", "Carnell Tate"),
        ("C5", "QB vs QB in 1QB", "Josh Allen", "Brock Purdy"),
    ]
    comparison_rows: list[dict[str, Any]] = []
    for identifier, archetype, left, right in compare_pairs:
        result = dynasty.compare_dynasty_assets([asset_ids[left], asset_ids[right]]).data
        leans = {row["horizon"]: row for row in result["leans"]}
        ranges = {row["player"]: row for row in result["ranges"]}
        rank_by_name = {row["player"]: row["rank"] for row in dynasty_data["rankings"]}
        for name in (left, right):
            value = ranges[name]
            comparison_rows.append({
                "pair_id": identifier,
                "archetype": archetype,
                "player": name,
                "nwr_rank": rank_by_name.get(name, "ROOKIE_REVIEW"),
                "short_term_preference": leans["Short term"]["preferred"],
                "short_term_reason": leans["Short term"]["reason"],
                "medium_term_preference": leans["Medium term"]["preferred"],
                "medium_term_reason": leans["Medium term"]["reason"],
                "long_term_preference": leans["Long term"]["preferred"],
                "long_term_reason": leans["Long term"]["reason"],
                "floor": value["floor"],
                "expected": value["expected"],
                "ceiling": value["ceiling"],
                "risk": value["risk"],
                "range_authority": value["authority"],
                "warnings": " || ".join(result.get("warnings", [])),
                "internal_consistency": "PENDING_REVIEW",
                "external_direction": "PENDING_EXTERNAL_BENCHMARK",
            })
    write_csv(OUTPUT_ROOT / "PLAYER_COMPARE_RESULTS.csv", comparison_rows, list(comparison_rows[0]))

    rookie_names = {
        "Jeremiyah Love", "Carnell Tate", "KC Concepcion", "Chris Bell",
    }
    selected_rookies = []
    for row in dynasty_data["rookies"]:
        selected_rank = int(row["rank"]) if row.get("rank") is not None else None
        if row["player"] in rookie_names or selected_rank in {1, 2, 3, 4, 5, 8, 9, 14, 25, 40, 60, 75, 80}:
            selected_rookies.append({
                **row,
                "actual_draft_capital_check": "PENDING_EXTERNAL_BENCHMARK",
                "public_rookie_consensus": "PENDING_EXTERNAL_BENCHMARK",
                "disagreement_explainable": "PENDING_REVIEW",
                "classification": "PENDING_REVIEW",
            })
    blocked = next(row for row in options if row["name"] == "De'Zhaun Stribling")
    selected_rookies.append({
        "assetId": blocked["assetId"], "rank": "", "playerId": "dezhaun-stribling",
        "player": blocked["name"], "position": blocked["position"], "team": blocked["team"],
        "rookieTier": "BLOCKED", "draftRange": "Unavailable", "nflDraftCapital": "Identity blocked",
        "boardScore": "", "reviewScore": "", "authority": blocked["authority"],
        "blockedReason": "Governed identity/evidence authority remains blocked", "warnings": "Truthfully blocked",
        "confidence": "BLOCKED", "age": "", "collegeProduction": "", "athleticContext": "",
        "researchTier": "", "floor": "Unavailable", "expected": "Unavailable", "ceiling": "Unavailable",
        "actual_draft_capital_check": "PENDING_EXTERNAL_BENCHMARK",
        "public_rookie_consensus": "PENDING_EXTERNAL_BENCHMARK",
        "disagreement_explainable": "YES_BLOCKED_TRUTHFULLY", "classification": "GREEN_BROADLY_PLAUSIBLE",
    })
    rookie_fields = list(selected_rookies[0])
    for extra in selected_rookies[1:]:
        for key in extra:
            if key not in rookie_fields:
                rookie_fields.append(key)
    write_csv(OUTPUT_ROOT / "ROOKIE_PLAUSIBILITY.csv", selected_rookies, rookie_fields)

    outcome_samples = {
        "QB": ["Josh Allen", "Drake Maye", "Trevor Lawrence", "Jalen Hurts"],
        "RB": ["Bijan Robinson", "Jonathan Taylor", "De'Von Achane", "Christian McCaffrey"],
        "WR": ["Puka Nacua", "Ja'Marr Chase", "Courtland Sutton", "Tetairoa McMillan"],
        "TE": ["Trey McBride", "Kyle Pitts", "Brock Bowers", "George Kittle"],
    }
    outcome_rows: list[dict[str, Any]] = []
    for position, players in outcome_samples.items():
        for name in players:
            detail = dynasty.dynasty_asset(asset_ids[name]).data
            matrices = detail.get("outcomes", [])
            if not matrices:
                outcome_rows.append({"position": position, "player": name, "available": False,
                                     "bounds_ok": True, "nested_thresholds_ok": True,
                                     "notes": "Unavailable remains unavailable"})
                continue
            matrix = matrices[0]
            bounds_ok, nested_ok, notes = outcome_checks(matrix)
            outcome_rows.append({"position": position, "player": name, "available": True,
                                 "bounds_ok": bounds_ok, "nested_thresholds_ok": nested_ok,
                                 "notes": " || ".join(notes), **matrix})
    outcome_fields = ["position", "player", "available", "bounds_ok", "nested_thresholds_ok", "notes"]
    for row in outcome_rows:
        for key in row:
            if key not in outcome_fields:
                outcome_fields.append(key)
    write_csv(OUTPUT_ROOT / "OUTCOME_SANITY.csv", outcome_rows, outcome_fields)

    ranked = list(dynasty_data["rankings"])
    matched = [
        row for row in ranked
        if row.get("rank") is not None
        and row.get("marketRank") is not None
        and row.get("marketBand") != "Market data unavailable"
    ]
    positive = sorted(matched, key=lambda row: float(row.get("marketGap") or 0), reverse=True)[:10]
    negative = sorted(matched, key=lambda row: float(row.get("marketGap") or 0))[:5]
    aligned = sorted(matched, key=lambda row: abs(float(row.get("marketGap") or 0)))[:5]
    market_rows = []
    for row in positive + aligned + negative:
        gap = float(row.get("marketGap") or 0)
        band = str(row.get("marketBand") or "")
        sign_valid = (
            (gap > 0 and band in {"Potential Buy", "NWR Higher"})
            or (gap < 0 and band in {"Market Higher", "Potential Sell / Caution"})
            or (abs(gap) < 6 and band == "Aligned")
        )
        market_rows.append({
            "player": row["player"], "position": row["position"], "nwr_rank": row["rank"],
            "market_rank_july17": row["marketRank"], "gap": gap, "label": band,
            "sign_valid": sign_valid, "current_public_context": "PENDING_EXTERNAL_BENCHMARK",
            "stale_snapshot_effect": "PENDING_REVIEW", "nwr_thesis": "PENDING_DETAIL_REVIEW",
            "classification": "PENDING_REVIEW",
        })
    write_csv(OUTPUT_ROOT / "MARKET_GAP_SANITY.csv", market_rows, list(market_rows[0]))

    redraft = DesktopBackendFacade(
        repo_root=REPO_ROOT,
        mode="redraft",
        redraft_root=DISPOSABLE_ROOT / "redraft",
    )
    redraft.redraft_bootstrap()
    profile_specs = [
        ("10_TEAM_1QB_STANDARD", "10-team 1QB Standard"),
        ("12_TEAM_1QB_HALF_PPR", "12-team Half-PPR"),
        ("12_TEAM_PPR", "12-team PPR"),
        ("12_TEAM_SUPERFLEX_PPR", "12-team Superflex PPR"),
    ]
    redraft_rows: list[dict[str, Any]] = []
    sutton_rows: list[dict[str, Any]] = []
    redraft_by_profile: dict[str, dict[str, dict[str, Any]]] = {}
    for preset_key, league_name in profile_specs:
        created = redraft.create_redraft_profile(preset_key=preset_key, league_name=f"QA {league_name}").data["profile"]
        redraft.activate_redraft_profile(created["profileId"])
        data = redraft.redraft_bootstrap().data
        leaders: set[str] = set()
        for position in ("QB", "RB", "WR", "TE"):
            rows = [row for row in data["rankings"] if row["position"] == position]
            if rows:
                leaders.add(rows[0]["playerName"])
        redraft_by_profile[league_name] = {row["playerName"]: row for row in data["rankings"]}
        for row in data["rankings"]:
            if int(row["overallRank"]) <= 50 or row["playerName"] in leaders or row["playerName"] == "Courtland Sutton" or (row["rookie"] and int(row["overallRank"]) <= 100):
                redraft_rows.append({
                    "profile": league_name, "preset_key": preset_key, **row,
                    "external_source": "", "external_rank_neighborhood": "",
                    "difference": "", "direction": "", "classification": "PENDING_EXTERNAL_BENCHMARK",
                })
            if row["playerName"] == "Courtland Sutton":
                sutton_rows.append({"profile": league_name, **row})
    write_csv(OUTPUT_ROOT / "REDRAFT_BENCHMARK.csv", redraft_rows, list(redraft_rows[0]))

    cross_names = ["Courtland Sutton", "Luther Burden", "Brock Purdy", "George Kittle", "Puka Nacua", "Jeremiyah Love", "Carnell Tate"]
    ranking_by_name = {row["player"]: row for row in dynasty_data["rankings"]}
    rookie_by_name = {row["player"]: row for row in dynasty_data["rookies"]}
    cross_rows = []
    for name in cross_names:
        detail = dynasty.dynasty_asset(asset_ids[name]).data
        rank_row = ranking_by_name.get(name, {})
        redraft_standard = redraft_by_profile["10-team 1QB Standard"].get(name, {})
        cross_rows.append({
            "player": name, "asset_id": detail["assetId"], "team": detail["team"],
            "age": detail.get("age"), "dynasty_rank": rank_row.get("rank"),
            "detail_rank": detail.get("rank"), "detail_position_rank": detail.get("positionRank"),
            "market_band": detail["market"].get("band"), "market_gap": detail["market"].get("gap"),
            "outcome_rows": len(detail.get("outcomes", [])),
            "rookie_rank": rookie_by_name.get(name, {}).get("rank"),
            "redraft_standard_rank": redraft_standard.get("overallRank"),
            "redraft_projected_points": redraft_standard.get("projectedPoints"),
            "identity_consistent": detail["assetId"] == asset_ids[name],
            "rank_consistent": not rank_row or detail.get("rank") == rank_row.get("rank"),
            "notes": "Targets differ legitimately across Dynasty, Rookie Review, Outcome, and Redraft",
        })
    write_csv(OUTPUT_ROOT / "CROSS_SYSTEM_CONSISTENCY.csv", cross_rows, list(cross_rows[0]))

    projection_path = REPO_ROOT / "docs" / "hq" / "model" / "nwr_redraft_2026_rookie_projection_candidate_v1_20260809" / "GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv"
    projection = pd.read_csv(projection_path)
    archetype_names = ["Puka Nacua", "Courtland Sutton", "Wan'Dale Robinson", "Jerry Jeudy", "Alec Pierce", "Davante Adams", "Tetairoa McMillan"]
    archetype_rows = []
    standard = redraft_by_profile["10-team 1QB Standard"]
    for name in archetype_names:
        row = projection.loc[projection["player_name"] == name].iloc[0]
        targets = float(row.get("targets") or 0)
        yards = float(row.get("receiving_yards") or 0)
        archetype_rows.append({
            "player": name, "position": row["position"], "targets": targets,
            "receptions": row.get("receptions"), "receiving_yards": yards,
            "receiving_tds": row.get("receiving_tds"),
            "yards_per_target": round(yards / targets, 3) if targets else "",
            "projection_low": row.get("projection_low"), "projection_high": row.get("projection_high"),
            "availability_probability": row.get("availability_probability"),
            "standard_rank": standard.get(name, {}).get("overallRank"),
            "standard_points": standard.get(name, {}).get("projectedPoints"),
        })
    write_csv(OUTPUT_ROOT / "OPPORTUNITY_EFFICIENCY_SAMPLE.csv", archetype_rows, list(archetype_rows[0]))

    defect_rows: list[dict[str, Any]] = []
    invalid_market = [row for row in market_rows if not row["sign_valid"]]
    invalid_outcomes = [row for row in outcome_rows if not row["bounds_ok"] or not row["nested_thresholds_ok"]]
    if invalid_market:
        defect_rows.append({"id": "PD-001", "severity": "RED", "surface": "Market gaps", "finding": "Market label sign inversion", "evidence": text(invalid_market), "status": "LIKELY_DEFECT"})
    if invalid_outcomes:
        defect_rows.append({"id": "PD-002", "severity": "RED", "surface": "Outcomes", "finding": "Outcome probability bounds or nesting violation", "evidence": text(invalid_outcomes), "status": "LIKELY_DEFECT"})
    defect_rows.append({
        "id": "PD-003", "severity": "YELLOW", "surface": "Range presentation",
        "finding": "Floor and ceiling are labeled downside/ceiling signals, not values on one ordered scale",
        "evidence": "Observed ranges can show a numerically larger downside percentage than ceiling percentage; the method text explains separate signals but the labels invite literal Floor <= Expected <= Ceiling reading.",
        "status": "PRODUCT_CLARITY_RISK_NOT_MODEL_DEFECT",
    })
    defect_rows.append({
        "id": "PD-004", "severity": "YELLOW", "surface": "Installed launcher runtime",
        "finding": "One launch emitted an Application Control block for an extracted NumPy DLL while the contained retry reached ready state",
        "evidence": "api.stderr.log recorded _multiarray_umath DLL load blocked; the installed app still reached an authenticated ready listener and rendered successfully.",
        "status": "INTERMITTENT_RUNTIME_RELIABILITY_REVIEW",
    })
    write_csv(OUTPUT_ROOT / "POTENTIAL_DEFECTS.csv", defect_rows, list(defect_rows[0]))

    (OUTPUT_ROOT / "SUTTON_CASE.md").write_text(
        "# Courtland Sutton sanity case\n\n"
        + "## Installed results\n\n"
        + "| Profile | Overall | Pos | Projected points | Value over replacement | Confidence |\n"
        + "| --- | ---: | ---: | ---: | ---: | --- |\n"
        + "".join(
            f"| {row['profile']} | {row['overallRank']} | WR{row['positionRank']} | {row['projectedPoints']} | {row['replacementAdjustedValue']} | {row['confidence']} |\n"
            for row in sutton_rows
        )
        + "\nDynasty places Sutton #29 (WR16), with a top research neighborhood, low stated risk, a 37.8% downside signal, a 36.6% ceiling signal, and an evidence confidence cap. The July market lens was #109 and is explicitly stale/display-only.\n\n"
        + "External classification is completed in the executive verdict after contemporary public benchmarking.\n",
        encoding="utf-8",
    )

    (OUTPUT_ROOT / "VALIDATION_RESULTS.md").write_text(
        "# Validation results\n\n"
        f"- Candidate: `{REPO_ROOT}`\n"
        f"- Dynasty board rows: {len(dynasty_data['rankings'])}\n"
        f"- Rookie review rows: {len(dynasty_data['rookies'])}\n"
        f"- Market observations sampled: {len(market_rows)}\n"
        f"- Outcome players sampled: {len(outcome_rows)}\n"
        f"- Trade perturbations: {len(perturbation_rows)}\n"
        f"- Additional trade scenarios: {len(scenario_rows)}\n"
        f"- Compare pairs: {len(compare_pairs)}\n"
        f"- Redraft benchmark rows: {len(redraft_rows)}\n"
        f"- Market sign inversions: {len(invalid_market)}\n"
        f"- Outcome bound/nesting failures: {len(invalid_outcomes)}\n"
        "- All analytical service writes were directed to the disposable QA root.\n"
        "- No model, rank, projection, trade rule, source authority, or owner workspace was changed.\n",
        encoding="utf-8",
    )

    # These narrative files are intentionally concise; the external benchmark pass
    # appends evidence-backed classifications after this deterministic extraction.
    placeholders = {
        "EXECUTIVE_VERDICT.md": "# Executive verdict\n\nPending contemporary external benchmark synthesis.\n",
        "OPPORTUNITY_VS_EFFICIENCY.md": "# Opportunity vs efficiency\n\nSee `OPPORTUNITY_EFFICIENCY_SAMPLE.csv`; synthesis follows the external benchmark pass.\n",
        "NWR_DISAGREEMENT_PLAYBOOK.md": "# NWR disagreement playbook\n\nPending benchmark archetype synthesis.\n",
        "NWR_BLIND_SPOTS.md": "# NWR blind spots\n\nPending synthesis.\n",
        "NWR_POTENTIAL_EDGES.md": "# NWR potential edges\n\nPending synthesis.\n",
    }
    for filename, content in placeholders.items():
        (OUTPUT_ROOT / filename).write_text(content, encoding="utf-8")

    archetype_seed = [
        {"archetype": "Opportunity / volume", "examples": "", "count": "", "direction": "", "median_difference": "", "largest_examples": "", "positions": "", "consistency": "", "internal_explanation": "", "historical_helpfulness": "NOT_ENOUGH_INFORMATION", "owner_category": "PENDING"},
        {"archetype": "Age / veteran lifecycle", "examples": "", "count": "", "direction": "", "median_difference": "", "largest_examples": "", "positions": "", "consistency": "", "internal_explanation": "", "historical_helpfulness": "NOT_ENOUGH_INFORMATION", "owner_category": "PENDING"},
        {"archetype": "Position economics - QB in 1QB", "examples": "", "count": "", "direction": "", "median_difference": "", "largest_examples": "", "positions": "QB", "consistency": "", "internal_explanation": "10-team 1QB replacement pool explicitly encoded", "historical_helpfulness": "NOT_ENOUGH_INFORMATION", "owner_category": "PENDING"},
        {"archetype": "Rookie evidence separation", "examples": "", "count": "", "direction": "", "median_difference": "", "largest_examples": "", "positions": "", "consistency": "", "internal_explanation": "Rookie Review is a separate review-only authority", "historical_helpfulness": "NOT_ENOUGH_INFORMATION", "owner_category": "PENDING"},
        {"archetype": "Stale market snapshot", "examples": "", "count": "", "direction": "", "median_difference": "", "largest_examples": "", "positions": "", "consistency": "", "internal_explanation": "July 17 market evidence is display-only and labeled stale", "historical_helpfulness": "NOT_ENOUGH_INFORMATION", "owner_category": "PENDING"},
    ]
    write_csv(OUTPUT_ROOT / "NWR_DISAGREEMENT_ARCHETYPES.csv", archetype_seed, list(archetype_seed[0]))
    watch_seed = [{"scenario": "", "nwr_tendency": "", "why": "", "owner_action": "", "owner_category": "PENDING"}]
    write_csv(OUTPUT_ROOT / "OWNER_WATCHLIST.csv", watch_seed, list(watch_seed[0]))
    outlier_seed = [{"player": "", "position": "", "nwr_view": "", "benchmark_view": "", "magnitude": "", "direction": "", "why_nwr_differs": "", "confidence": "", "archetype": "", "owner_watch_action": "", "classification": "PENDING"}]
    write_csv(OUTPUT_ROOT / "CURRENT_MAJOR_OUTLIERS.csv", outlier_seed, list(outlier_seed[0]))

    print(json.dumps({
        "output_root": str(OUTPUT_ROOT),
        "rankings": len(dynasty_data["rankings"]),
        "rookies": len(dynasty_data["rookies"]),
        "trade_perturbations": len(perturbation_rows),
        "trade_scenarios": len(scenario_rows),
        "compare_pairs": len(compare_pairs),
        "outcome_samples": len(outcome_rows),
        "market_samples": len(market_rows),
        "redraft_rows": len(redraft_rows),
        "sutton": sutton_rows,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
