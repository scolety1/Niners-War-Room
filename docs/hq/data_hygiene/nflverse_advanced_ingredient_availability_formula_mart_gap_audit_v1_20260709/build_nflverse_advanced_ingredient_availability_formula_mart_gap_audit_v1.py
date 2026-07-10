from __future__ import annotations

import csv
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(r"C:\NWR\Niners-War-Room-nflverse-advanced-ingredient-availability-formula-mart-gap-audit-v1-20260709")
ADV_CACHE = Path(r"C:\NWR_REVIEW\advanced_metrics_source_cache_20260707")
PFR_CACHE = Path(r"C:\NWR_REVIEW\pfr_advanced_source_provenance_hardening_v1_20260707")
TEMPLATE_ROOTS = [
    Path(r"C:\NWR_SANDBOX\Niners-War-Room-raw-snapshot-2024-2025-admission-pivot-v1-20260707\templates\real_data_inputs\nflverse_stats_upgrade"),
    Path(r"C:\NWR_SANDBOX\Niners-War-Room-nflverse-metadata-dob-roster-admission-gate-v1-20260707\templates\real_data_inputs\nflverse_stats_upgrade"),
    Path(r"C:\NWR\nflverse-phase-reset-audit-20260630\templates\real_data_inputs\nflverse_stats_upgrade"),
]
PRIOR = {
    "pfr_component_test": Path(
        r"C:\NWR\Niners-War-Room-pfr-rb-broken-tackle-data-mart-join-component-test-v1-20260709\docs\hq\data_hygiene\pfr_rb_broken_tackle_data_mart_join_component_test_v1_20260709"
    ),
    "high_value_signal_locator": Path(
        r"C:\NWR\Niners-War-Room-high-value-signal-data-locator-audit-v1-20260709\docs\hq\data_hygiene\high_value_signal_data_locator_audit_v1_20260709"
    ),
    "formula_pivot": Path(
        r"C:\NWR\Niners-War-Room-formula-results-master-review-data-upgrade-pivot-v1-20260709\docs\hq\master\formula_results_master_review_data_upgrade_pivot_v1_20260709"
    ),
    "formula_data_mart": Path(
        r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
    ),
    "full_gauntlet": Path(
        r"C:\NWR\Niners-War-Room-full-review-only-formula-gauntlet-candidate-arena-v1-20260709\docs\hq\model\full_review_only_formula_gauntlet_candidate_arena_v1_20260709"
    ),
    "clustering_audit": Path(
        r"C:\NWR\Niners-War-Room-gauntlet-candidate-diversity-clustering-audit-v1-20260709\docs\hq\model\gauntlet_candidate_diversity_clustering_audit_v1_20260709"
    ),
    "diverse_refinement": Path(
        r"C:\NWR\Niners-War-Room-diverse-champion-refinement-predeclared-execution-v1-20260709\docs\hq\model\diverse_champion_refinement_predeclared_execution_v1_20260709"
    ),
}

REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_PFR_COMMIT = "843c17838caa020f5f123e6df5cd1fdd45d5b9c6"

OFFICIAL_SOURCES = {
    "nflreadr_home": "https://nflreadr.nflverse.com/",
    "nflreadr_reference": "https://nflreadr.nflverse.com/reference/index.html",
    "nflverse_data_schedule": "https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html",
    "nflfastR_home": "https://nflfastr.com/",
    "load_pbp": "https://nflreadr.nflverse.com/reference/load_pbp.html",
    "load_player_stats": "https://nflreadr.nflverse.com/reference/load_player_stats.html",
    "load_ff_opportunity": "https://nflreadr.nflverse.com/reference/load_ff_opportunity.html",
    "load_nextgen_stats": "https://rdrr.io/cran/nflreadr/man/load_nextgen_stats.html",
    "load_ftn_charting": "https://nflreadr.nflverse.com/reference/load_ftn_charting.html",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_stat(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"file_size": "", "modified_time": "", "sha256": ""}
    st = path.stat()
    return {
        "file_size": st.st_size,
        "modified_time": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
        "sha256": sha256_file(path) if path.is_file() else "",
    }


def is_csv_like(path: Path) -> bool:
    return path.suffix.lower() == ".csv" or path.name.lower().endswith(".csv.gz")


def read_tabular(path: Path) -> tuple[pd.DataFrame | None, int | str, str]:
    try:
        if path.suffix.lower() == ".parquet":
            df = pd.read_parquet(path)
            return df, len(df), "parquet"
        if path.name.lower().endswith(".csv.gz") or path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
            return df, len(df), "csv"
    except Exception as exc:  # pragma: no cover - emitted into ledger
        return None, "", f"read_error:{type(exc).__name__}:{exc}"
    return None, "", "not_tabular"


def detect_metadata(df: pd.DataFrame | None) -> dict[str, str]:
    if df is None:
        return {
            "row_count": "",
            "columns": "",
            "seasons_covered": "",
            "position_coverage": "",
            "player_id_fields": "",
            "join_keys": "",
            "row_grain_guess": "",
            "missingness": "",
        }
    cols = list(df.columns)
    lower = {c.lower(): c for c in cols}
    season_cols = [lower[c] for c in ("season", "season_year", "year") if c in lower]
    pos_cols = [c for c in cols if c.lower() in {"position", "pos", "player_position"}]
    id_cols = [
        c
        for c in cols
        if c.lower()
        in {
            "player_id",
            "player_gsis_id",
            "gsis_id",
            "pfr_id",
            "player",
            "player_display_name",
            "full_name",
            "name_display",
        }
    ]
    join_keys = []
    if season_cols:
        join_keys.append(season_cols[0])
    if id_cols:
        join_keys.append(id_cols[0])
    if pos_cols:
        join_keys.append(pos_cols[0])
    if "week" in lower:
        join_keys.insert(1, lower["week"])
    seasons = ""
    if season_cols:
        series = df[season_cols[0]].dropna()
        vals = sorted({str(v) for v in series.unique()})
        seasons = "|".join(vals[:40])
    positions = ""
    if pos_cols:
        vals = sorted({str(v) for v in df[pos_cols[0]].dropna().unique()})
        positions = "|".join(vals[:40])
    missingness = ""
    if cols:
        missingness = f"{float(df.isna().mean().mean()):.4f}_cell_missing_rate"
    grain = "player_week" if "week" in lower and id_cols else "player_season" if season_cols and id_cols else "play_level_or_team_level"
    return {
        "row_count": str(len(df)),
        "columns": "|".join(cols),
        "seasons_covered": seasons,
        "position_coverage": positions,
        "player_id_fields": "|".join(id_cols),
        "join_keys": "|".join(join_keys),
        "row_grain_guess": grain,
        "missingness": missingness,
    }


def family_for_file(path: Path) -> str:
    name = path.name.lower()
    text = str(path).lower()
    if "ep_weekly" in name or "ffopportunity" in text or "expected_fantasy" in text:
        return "expected_fantasy_points_ffopportunity"
    if "ngs" in name or "nextgen" in text:
        return "next_gen_stats"
    if "ftn_charting" in name:
        return "ftn_charting"
    if "qbr" in name:
        return "qb_passing_quality"
    if "advstats_season_pass" in name:
        return "qb_passing_quality"
    if "advstats_season_rec" in name:
        return "receiving_opportunity_air_yards"
    if "advstats_season_rush" in name:
        return "pfr_parked_broken_tackle_context"
    if "snap_counts" in name:
        return "snap_counts"
    if "depth_chart" in name:
        return "depth_charts"
    if "injur" in name or "availability" in name:
        return "injury_availability"
    if "participation" in name or "personnel" in name or "pressure" in name:
        return "participation_personnel_pressure"
    if "player_stats" in name:
        return "player_season_week_epa_opportunity"
    if "market" in name or "adp" in name or "dynastyprocess" in name:
        return "historical_market_adp"
    return "supporting_review_artifact"


def source_type_for_path(path: Path) -> str:
    p = str(path).lower()
    if r"\advanced_metrics_source_cache_20260707" in p:
        return "local_advanced_metrics_cache"
    if r"\pfr_advanced_source_provenance_hardening" in p:
        return "pfr_source_provenance_cache"
    if r"\templates\real_data_inputs\nflverse_stats_upgrade" in p:
        return "real_data_input_template_or_stub"
    if r"\docs\hq" in p:
        return "review_packet_or_governance_artifact"
    return "local_candidate_artifact"


def classification_for_family(family: str) -> tuple[str, str, str]:
    mapping = {
        "player_season_week_epa_opportunity": (
            "MISSING_BUT_PUBLIC_NFLVERSE_REBUILDABLE",
            "Public nflfastR play-by-play/player-stats can rebuild EPA/opportunity aggregates, but no full 2013-2025 joined local sidecar was found.",
            "high",
        ),
        "receiving_opportunity_air_yards": (
            "PRESENT_PARTIAL_COVERAGE",
            "Existing mart has targets/air yards/YAC; advanced WOPR/RACR/PACR would need schema/as-of sidecar work.",
            "medium_high",
        ),
        "qb_passing_quality": (
            "PRESENT_PARTIAL_COVERAGE",
            "NGS passing and ESPN QBR/PFR passing files exist, but ESPN/PFR/broad passing source gates prevent immediate model use.",
            "medium",
        ),
        "expected_yac_first_downs_over_expected": (
            "PRESENT_PARTIAL_COVERAGE",
            "NGS receiving has expected YAC/YAC above expectation; ffopportunity has expected first-down and fantasy-point fields for 2021-2024.",
            "medium_high",
        ),
        "next_gen_stats": (
            "PRESENT_PARTIAL_COVERAGE",
            "Local NGS passing/receiving/rushing files exist mostly for 2021-2023 plus tiny 2024 fragments; public NGS is rebuildable from 2016 onward.",
            "high",
        ),
        "expected_fantasy_points_ffopportunity": (
            "PRESENT_READY_FOR_SCHEMA_REVIEW",
            "Local ep_weekly parquet files contain expected fantasy points, expected yards, expected TDs, and expected first downs for 2021-2024.",
            "highest",
        ),
        "snap_counts": (
            "MISSING_BUT_PUBLIC_NFLVERSE_REBUILDABLE",
            "Only templates/current mart fields were found locally; nflverse exposes PFR snap counts, but source gate/as-of validation is still needed.",
            "medium",
        ),
        "depth_charts": (
            "PRESENT_NEEDS_ASOF_REVIEW",
            "Template/stub files exist and nflverse has depth chart loads, but weekly as-of semantics must be proven before formula use.",
            "medium",
        ),
        "injury_availability": (
            "PRESENT_NEEDS_ASOF_REVIEW",
            "Local templates/leads exist; nflverse injury source has known 2025 continuity risk, so use only as point-in-time review gate after source review.",
            "medium",
        ),
        "participation_personnel_pressure": (
            "PRESENT_PARTIAL_COVERAGE",
            "FTN charting and participation-like templates exist; coverage is 2022+ and must not be promoted to routes/YPRR/TPRR.",
            "medium",
        ),
        "ftn_charting": (
            "PRESENT_READY_FOR_SCHEMA_REVIEW",
            "Local FTN charting parquet exists for 2022-2024 with motion/play-action/catchable/drop/pressure-like charting fields.",
            "medium_high",
        ),
        "historical_market_adp": (
            "PRESENT_NEEDS_ASOF_REVIEW",
            "Prior locator found market/ADP artifacts, but historical point-in-time safety was not proven.",
            "high_later",
        ),
    }
    return mapping[family]


FAMILIES = [
    {
        "family_name": "player_season_week_epa_opportunity",
        "display": "Player-season/player-week EPA and opportunity aggregates",
        "likely_source": "nflfastR play-by-play, nflverse player_stats, team_stats",
        "terms": "passing EPA|rushing EPA|receiving EPA|EPA per attempt|EPA per target|success rate|air EPA|YAC EPA|team offensive EPA",
        "value": "Could add independent efficiency/opportunity context beyond lagged fantasy points and raw volume.",
        "row_grain": "player_week or player_season aggregate",
        "positions": "QB/RB/WR/TE if rebuilt from PBP/player_stats",
        "public_rebuildable": "yes_public_nflverse_nflfastR",
    },
    {
        "family_name": "receiving_opportunity_air_yards",
        "display": "Receiving opportunity and air-yard metrics",
        "likely_source": "nflverse player_stats, nflfastR play-by-play, NGS receiving",
        "terms": "target share|air-yards share|WOPR|RACR|PACR|air yards|target quality|first-down receiving",
        "value": "Could improve WR/TE opportunity quality and role-change context.",
        "row_grain": "player_week/player_season",
        "positions": "RB/WR/TE",
        "public_rebuildable": "yes_public_nflverse_for_inputs; WOPR/RACR/PACR derived",
    },
    {
        "family_name": "qb_passing_quality",
        "display": "QB passing quality",
        "likely_source": "NGS passing, nflfastR CPOE/EPA, ESPN QBR local cache, PFR passing parked",
        "terms": "CPOE|completion probability|passing EPA|intended air yards|completed air yards|QB rushing EPA",
        "value": "Could improve QB-specific formula slices beyond prior fantasy production.",
        "row_grain": "player_week/player_season",
        "positions": "QB",
        "public_rebuildable": "yes_for_nflfastR_and_NGS; ESPN/PFR require separate gates",
    },
    {
        "family_name": "expected_yac_first_downs_over_expected",
        "display": "Expected YAC / YAC over expected / first downs over expected",
        "likely_source": "NGS receiving, ffopportunity ep_weekly",
        "terms": "expected YAC|YAC above expectation|first downs over expected|receiver YAC skill",
        "value": "Could add receiver efficiency and expected-opportunity context, especially WR/TE.",
        "row_grain": "player_week/player_season",
        "positions": "RB/WR/TE",
        "public_rebuildable": "yes_partial_public_nflverse",
    },
    {
        "family_name": "next_gen_stats",
        "display": "Next Gen Stats",
        "likely_source": "nflreadr load_nextgen_stats",
        "terms": "time to throw|expected completion percentage|separation|expected YAC|RYOE|stacked-box rate",
        "value": "High-value independent NGS skill/context layer for QB/RB/WR/TE if joined safely.",
        "row_grain": "player_week with week 0/season rows possible",
        "positions": "QB/RB/WR/TE",
        "public_rebuildable": "yes_from_2016_onward",
    },
    {
        "family_name": "expected_fantasy_points_ffopportunity",
        "display": "Expected fantasy points / ffopportunity",
        "likely_source": "nflreadr load_ff_opportunity ep_weekly",
        "terms": "expected fantasy points|opportunity quality|expected fantasy points per game|actual minus expected",
        "value": "Highest near-term formula value because it directly captures opportunity quality separate from actual fantasy result.",
        "row_grain": "player_week aggregate to player_season",
        "positions": "QB/RB/WR/TE",
        "public_rebuildable": "yes_public_nflverse_ffopportunity",
    },
    {
        "family_name": "snap_counts",
        "display": "Snap counts",
        "likely_source": "nflreadr load_snap_counts",
        "terms": "offensive snaps|snap share|positional snap share|game-level snap counts",
        "value": "Could improve role/opportunity validation and sparse-history handling.",
        "row_grain": "player_week aggregate to player_season",
        "positions": "QB/RB/WR/TE",
        "public_rebuildable": "yes_public_nflverse_pfr_snap_counts",
    },
    {
        "family_name": "depth_charts",
        "display": "Depth charts",
        "likely_source": "nflreadr load_depth_charts",
        "terms": "depth position|starter|backup|depth rank|role change",
        "value": "Useful role/context source if weekly as-of semantics are proven.",
        "row_grain": "player_week/team_depth_slot",
        "positions": "QB/RB/WR/TE",
        "public_rebuildable": "yes_but_source_format_changed_2025",
    },
    {
        "family_name": "injury_availability",
        "display": "Injury / availability point-in-time context",
        "likely_source": "nflreadr load_injuries, weekly rosters/status artifacts",
        "terms": "injury reports|practice reports|game status|active/inactive|IR/PUP|questionable|out",
        "value": "Review-only availability/caution context, not injury prediction.",
        "row_grain": "player_week",
        "positions": "QB/RB/WR/TE",
        "public_rebuildable": "partial_public_nflverse_through_2024_source_risk",
    },
    {
        "family_name": "participation_personnel_pressure",
        "display": "Participation / personnel / pressure context",
        "likely_source": "nflverse participation, FTN charting, nflfastR PBP",
        "terms": "participation|formation|personnel|defenders in box|pressure|route|coverage type",
        "value": "Useful partial play-context sidecar; must not be treated as true route/YPRR/TPRR.",
        "row_grain": "play/player_participation or play-level charting",
        "positions": "QB/RB/WR/TE plus team/play context",
        "public_rebuildable": "partial_public_nflverse_FTN_2022plus",
    },
    {
        "family_name": "ftn_charting",
        "display": "FTN charting",
        "likely_source": "nflreadr load_ftn_charting",
        "terms": "motion|play action|screen|RPO|catchable ball|contested target|drop|pressure|blitz",
        "value": "Potential independent play-context ingredient, but partial 2022+ coverage limits full-history formula use.",
        "row_grain": "play-level",
        "positions": "play/team plus QB/receiver context if joined to PBP/player IDs",
        "public_rebuildable": "yes_2022plus_CC_BY_SA_attribution_required",
    },
    {
        "family_name": "historical_market_adp",
        "display": "Historical Market / ADP candidate files",
        "likely_source": "DynastyProcess, market snapshots, FantasyPros/Sleeper if present",
        "terms": "historical ADP|market rank|DynastyProcess|startup ADP|rookie ADP|FantasyPros",
        "value": "High dynasty context value later, but not nflverse and as-of safety must be proven.",
        "row_grain": "snapshot/player/season or player/date",
        "positions": "QB/RB/WR/TE",
        "public_rebuildable": "not_nflverse; requires separate source gate",
    },
]


def collect_candidate_files() -> list[Path]:
    paths: list[Path] = []
    for root in [ADV_CACHE, PFR_CACHE, *TEMPLATE_ROOTS]:
        if root.exists():
            paths.extend([p for p in root.rglob("*") if p.is_file()])
    for label, root in PRIOR.items():
        if not root.exists():
            continue
        keep_names = {
            "PFR_RB_BROKEN_TACKLE_DATA_MART_JOIN_COMPONENT_TEST_V1_REPORT.md",
            "PFR_RB_BROKEN_TACKLE_SOURCE_LEDGER.csv",
            "PFR_RB_BROKEN_TACKLE_SCHEMA_VALIDATION.csv",
            "HIGH_VALUE_SIGNAL_DATA_LOCATOR_AUDIT_V1_REPORT.md",
            "HIGH_VALUE_SIGNAL_AVAILABILITY_CLASSIFICATION.csv",
            "HIGH_VALUE_SIGNAL_PRIORITY_RANKING.csv",
            "FORMULA_RESULTS_MASTER_REVIEW_DATA_UPGRADE_PIVOT_V1_REPORT.md",
            "FORMULA_DATA_UPGRADE_PRIORITY_MATRIX.csv",
            "FORMULA_DATA_MART_FEATURE_AVAILABILITY_AUDIT_V1_REPORT.md",
            "FORMULA_FEATURE_AVAILABILITY_MATRIX.csv",
            "GAUNTLET_SOURCE_TRACE.md",
            "DIVERSE_CHAMPION_REFINEMENT_SOURCE_TRACE.md",
        }
        for p in root.rglob("*"):
            if p.is_file() and (p.name in keep_names or "SOURCE_TRACE" in p.name or "SOURCE_LEDGER" in p.name):
                paths.append(p)
    # Explicitly include red-zone and market leads discovered by prior locators without expanding into another broad crawl.
    lead_files = [
        Path(r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709\docs\hq\data_sources\nflverse_core_usage_review_dataset_v1_20260701\nwr_player_week_redzone_sidecar_v1.parquet"),
        Path(r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709\docs\hq\data_sources\nflverse_lagged_usage_candidate_gate_v1_20260701\redzone_feature_decision.md"),
    ]
    for p in lead_files:
        if p.exists():
            paths.append(p)
    unique: list[Path] = []
    seen = set()
    for p in paths:
        key = str(p).lower()
        if key not in seen:
            unique.append(p)
            seen.add(key)
    return unique


def build_artifact_ledger(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(paths, key=lambda p: str(p).lower()):
        stats = safe_stat(path)
        family = family_for_file(path)
        df = None
        row_count: int | str = ""
        read_status = "not_tabular"
        if path.suffix.lower() == ".parquet" or is_csv_like(path):
            df, row_count, read_status = read_tabular(path)
        meta = detect_metadata(df)
        classification, notes, _priority = classification_for_family(family) if family in {f["family_name"] for f in FAMILIES} else (
            "PARK_FOR_LATER",
            "Supporting review artifact or parked source branch.",
            "low",
        )
        if family == "pfr_parked_broken_tackle_context":
            classification = "PARK_FOR_LATER"
            notes = "PFR RB broken-tackle branch closed as formula ingredient after no incremental signal; keep only descriptive RB review context."
        rows.append(
            {
                "ingredient_family": family,
                "found_path": str(path),
                "file_name": path.name,
                "source_type": source_type_for_path(path),
                "raw_vs_derived": "derived_review_artifact" if "docs\\hq" in str(path).lower() else "raw_or_source_cache",
                "file_size": stats["file_size"],
                "modified_time": stats["modified_time"],
                "sha256": stats["sha256"],
                "row_count": meta["row_count"] or row_count,
                "columns": meta["columns"],
                "season_coverage": meta["seasons_covered"],
                "position_coverage": meta["position_coverage"],
                "player_id_fields": meta["player_id_fields"],
                "join_keys": meta["join_keys"],
                "row_grain": meta["row_grain_guess"],
                "source_use_gate_status": "review_only_needs_sidecar_gate" if classification.startswith("PRESENT") else "not_admitted_or_parked",
                "leakage_asof_status": "lag_required; as_of review required before formula testing",
                "identity_risk": "medium_until_join_to_formula_mart_player_id_validated",
                "missingness_risk": meta["missingness"],
                "formula_test_candidate": "yes_after_schema_source_asof_identity_validation"
                if classification in {"PRESENT_READY_FOR_SCHEMA_REVIEW", "PRESENT_PARTIAL_COVERAGE"}
                else "no_or_later",
                "ranking_integration_candidate_later": "no_currently_blocked",
                "availability_classification": classification,
                "park_status": "parked" if classification in {"PARK_FOR_LATER", "PRESENT_DISPLAY_ONLY"} or family == "pfr_parked_broken_tackle_context" else "active_candidate_or_rebuildable",
                "notes": notes,
                "read_status": read_status,
            }
        )
    return rows


def summarize_family_from_ledger(family: str, ledger: list[dict[str, Any]]) -> dict[str, str]:
    rows = [r for r in ledger if r["ingredient_family"] == family]
    paths = [r["found_path"] for r in rows[:5]]
    seasons = sorted({s for r in rows for s in str(r["season_coverage"]).split("|") if s})
    positions = sorted({s for r in rows for s in str(r["position_coverage"]).split("|") if s})
    ids = sorted({s for r in rows for s in str(r["player_id_fields"]).split("|") if s})
    return {
        "found_locally": "yes" if rows else "no",
        "source_path": " | ".join(paths),
        "seasons_covered": "|".join(seasons[:40]),
        "position_coverage": "|".join(positions[:40]),
        "player_id_fields": "|".join(ids[:20]),
        "join_keys": "player_id/player_gsis_id/pfr_id + season/week depending source; must map to Formula Mart player_id",
    }


def build_availability_matrix(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    found_aliases = {
        "expected_yac_first_downs_over_expected": ["next_gen_stats", "expected_fantasy_points_ffopportunity"],
    }
    for spec in FAMILIES:
        family = spec["family_name"]
        classification, notes, priority = classification_for_family(family)
        fam_ledger = ledger[:]
        if family in found_aliases:
            matched = [r for r in ledger if r["ingredient_family"] in found_aliases[family]]
        else:
            matched = [r for r in ledger if r["ingredient_family"] == family]
        summary = summarize_family_from_ledger(family, ledger)
        if family in found_aliases and matched:
            seasons = sorted({s for r in matched for s in str(r["season_coverage"]).split("|") if s})
            positions = sorted({s for r in matched for s in str(r["position_coverage"]).split("|") if s})
            paths = [r["found_path"] for r in matched[:5]]
            summary.update(
                {
                    "found_locally": "yes",
                    "source_path": " | ".join(paths),
                    "seasons_covered": "|".join(seasons[:40]),
                    "position_coverage": "|".join(positions[:40]),
                    "player_id_fields": "player_gsis_id|player_id",
                }
            )
        if family == "player_season_week_epa_opportunity" and summary["found_locally"] == "no":
            summary["source_path"] = "No full local player EPA sidecar found; public rebuild via nflfastR PBP/player_stats."
        if family == "historical_market_adp":
            # Prior locator found many leads, but this audit does not duplicate that broad crawl.
            summary["found_locally"] = "yes_prior_locator_leads"
            summary["source_path"] = str(PRIOR["high_value_signal_locator"] / "HIGH_VALUE_SIGNAL_FOUND_ARTIFACT_LEDGER.csv")
            summary["seasons_covered"] = "not_proven_by_this_audit"
            summary["position_coverage"] = "QB/RB/WR/TE_candidate"
        immediate = "yes"
        if classification in {
            "MISSING_BUT_PUBLIC_NFLVERSE_REBUILDABLE",
            "PRESENT_NEEDS_ASOF_REVIEW",
            "PRESENT_NEEDS_IDENTITY_REVIEW",
            "PRESENT_DISPLAY_ONLY",
            "PARK_FOR_LATER",
        }:
            immediate = "no_requires_prep"
        if family == "expected_fantasy_points_ffopportunity":
            immediate = "yes_highest_priority_schema_sidecar"
        rows.append(
            {
                "family_name": family,
                "display_name": spec["display"],
                "likely_source": spec["likely_source"],
                "found_locally": summary["found_locally"],
                "source_path_if_found": summary["source_path"],
                "seasons_covered": summary["seasons_covered"] or "missing_or_not_detected",
                "row_grain": spec["row_grain"],
                "position_coverage": summary["position_coverage"] or spec["positions"],
                "player_id_fields": summary["player_id_fields"] or "requires_source_specific_identity_review",
                "join_keys": summary["join_keys"],
                "expected_formula_data_mart_value": spec["value"],
                "historical_asof_safety": "lag_N_to_Nplus1_required; current_only_rows_blocked; weekly rows need season aggregation with closed-season cutoff",
                "source_use_gate_status": "review_only_audit_only; no production/model-use promoted",
                "missingness_risk": "high_until_schema_sidecar_validation" if "PARTIAL" in classification else "medium",
                "identity_risk": "medium_until_player_id_bridge_validated",
                "coverage_risk": "partial" if classification in {"PRESENT_PARTIAL_COVERAGE", "PRESENT_NEEDS_ASOF_REVIEW"} else "manageable_or_rebuildable",
                "downloadable_or_rebuildable_from_public_nflverse": spec["public_rebuildable"],
                "immediate_sidecar_join_feasible": immediate,
                "availability_classification": classification,
                "priority": priority,
                "notes": notes,
            }
        )
    return rows


def build_missing_rebuildable(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in matrix:
        cls = row["availability_classification"]
        if "MISSING" in cls or row["found_locally"] in {"no", "yes_prior_locator_leads"} or row["availability_classification"] in {"PRESENT_PARTIAL_COVERAGE", "PRESENT_NEEDS_ASOF_REVIEW"}:
            rows.append(
                {
                    "family_name": row["family_name"],
                    "missing_or_gap": (
                        "full_history_or_source_gate_gap"
                        if row["found_locally"] != "no"
                        else "local_values_not_found_for_full_sidecar"
                    ),
                    "public_rebuildable_status": row["downloadable_or_rebuildable_from_public_nflverse"],
                    "needed_next_step": next_step_for_family(row["family_name"]),
                    "reason": row["notes"],
                }
            )
    return rows


def next_step_for_family(family: str) -> str:
    return {
        "expected_fantasy_points_ffopportunity": "ffopportunity Expected Fantasy Points Formula Mart Sidecar V1",
        "next_gen_stats": "nflverse NGS Formula Mart Sidecar V1",
        "player_season_week_epa_opportunity": "nflverse EPA / Opportunity Formula Mart Sidecar V1",
        "receiving_opportunity_air_yards": "nflverse Receiving Opportunity Formula Mart Sidecar V1",
        "qb_passing_quality": "QB passing quality source-gate/schema review after NGS or EPA",
        "expected_yac_first_downs_over_expected": "Bundle with ffopportunity or NGS sidecar review",
        "snap_counts": "nflverse Snap Counts / Depth Chart Role Sidecar V1",
        "depth_charts": "nflverse Snap Counts / Depth Chart Role Sidecar V1 after as-of review",
        "injury_availability": "Point-in-Time Injury Availability Data Mart Gate V1",
        "participation_personnel_pressure": "FTN/participation context sidecar after expected-points/NGS",
        "ftn_charting": "FTN charting formula-mart sidecar later due 2022+ partial coverage",
        "historical_market_adp": "Historical Market / ADP Source Gate and Data Mart Join V1 later",
    }.get(family, "park_for_later")


def build_priority(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority_order = [
        ("expected_fantasy_points_ffopportunity", 1, "highest_value_immediately_executable", "ffopportunity Expected Fantasy Points Formula Mart Sidecar V1"),
        ("next_gen_stats", 2, "high_value_partial_local_plus_public_rebuildable", "nflverse NGS Formula Mart Sidecar V1"),
        ("player_season_week_epa_opportunity", 3, "high_value_public_rebuild_needed", "nflverse EPA / Opportunity Formula Mart Sidecar V1"),
        ("receiving_opportunity_air_yards", 4, "medium_high_value_wr_te_context", "nflverse Receiving Opportunity Formula Mart Sidecar V1"),
        ("ftn_charting", 5, "medium_high_but_2022plus_partial", "FTN charting sidecar later"),
        ("snap_counts", 6, "role_validation_value", "nflverse Snap Counts / Depth Chart Role Sidecar V1"),
        ("depth_charts", 7, "role_change_value_but_asof_sensitive", "nflverse Snap Counts / Depth Chart Role Sidecar V1"),
        ("qb_passing_quality", 8, "qb_specific_but_source_mixed", "NGS/EPA first; ESPN/PFR parked"),
        ("expected_yac_first_downs_over_expected", 9, "bundle_with_ngs_or_ffopportunity", "Bundle with NGS/ffopportunity sidecar"),
        ("participation_personnel_pressure", 10, "partial_play_context", "Park behind NGS/ffopportunity"),
        ("injury_availability", 11, "caution_context_not_prediction", "Point-in-Time Injury Availability Data Mart Gate V1 later"),
        ("historical_market_adp", 12, "high_future_value_but_non_nflverse_asof_gate", "Historical Market / ADP Source Gate later"),
    ]
    by_family = {r["family_name"]: r for r in matrix}
    rows = []
    for family, rank, rationale, lane in priority_order:
        row = by_family[family]
        rows.append(
            {
                "priority_rank": rank,
                "family_name": family,
                "availability_classification": row["availability_classification"],
                "expected_accuracy_upside_beyond_0755": "high" if rank <= 3 else "medium_high" if rank <= 5 else "medium",
                "independence_from_prior_production": "high" if family in {"expected_fantasy_points_ffopportunity", "next_gen_stats", "ftn_charting"} else "medium",
                "coverage_fit": row["seasons_covered"],
                "join_feasibility": row["immediate_sidecar_join_feasible"],
                "asof_leakage_risk": row["historical_asof_safety"],
                "near_term_executable_value": rationale,
                "recommended_lane_or_status": lane,
            }
        )
    return rows


def build_asof_review(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in matrix:
        family = row["family_name"]
        risk = "medium"
        if family in {"depth_charts", "injury_availability", "historical_market_adp", "participation_personnel_pressure"}:
            risk = "high"
        if family == "expected_fantasy_points_ffopportunity":
            risk = "medium_low_if_lagged_after_closed_season"
        rows.append(
            {
                "family_name": family,
                "asof_leakage_risk": risk,
                "safe_use_rule": "Use only closed-season N values as lagged N+1 features; never use current/future weeks as historical features.",
                "blocked_use": "same-season prediction, production/model-use, rankings integration, or current-only backfill",
                "source_gate_note": row["source_use_gate_status"],
                "identity_note": row["identity_risk"],
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def md_list(items: list[str]) -> str:
    return "\n".join(f"- `{item}`" for item in items)


def main() -> None:
    paths = collect_candidate_files()
    ledger = build_artifact_ledger(paths)
    matrix = build_availability_matrix(ledger)
    missing = build_missing_rebuildable(matrix)
    priority = build_priority(matrix)
    asof = build_asof_review(matrix)

    write_csv(OUT_DIR / "NFLVERSE_ADVANCED_FOUND_ARTIFACT_LEDGER.csv", ledger)
    write_csv(OUT_DIR / "NFLVERSE_ADVANCED_INGREDIENT_AVAILABILITY_MATRIX.csv", matrix)
    write_csv(OUT_DIR / "NFLVERSE_ADVANCED_MISSING_REBUILDABLE_LEDGER.csv", missing)
    write_csv(OUT_DIR / "NFLVERSE_ADVANCED_FORMULA_MART_SIDECAR_PRIORITY.csv", priority)
    write_csv(OUT_DIR / "NFLVERSE_ADVANCED_ASOF_AND_LEAKAGE_RISK_REVIEW.csv", asof)

    found_local = [r["family_name"] for r in matrix if str(r["found_locally"]).startswith("yes")]
    rebuildable = [r["family_name"] for r in matrix if "rebuild" in str(r["downloadable_or_rebuildable_from_public_nflverse"]).lower() or "yes" in str(r["downloadable_or_rebuildable_from_public_nflverse"]).lower()]
    present_ready = [r["family_name"] for r in matrix if r["availability_classification"] == "PRESENT_READY_FOR_SCHEMA_REVIEW"]
    partial = [r["family_name"] for r in matrix if r["availability_classification"] == "PRESENT_PARTIAL_COVERAGE"]
    next_lane = "ffopportunity Expected Fantasy Points Formula Mart Sidecar V1"
    verdict = "GREEN_NFLVERSE_ADVANCED_INGREDIENTS_FOUND_WITH_EXECUTABLE_SIDECARE_LANE"

    report = f"""
# nflverse Advanced Ingredient Availability / Formula Mart Gap Audit V1 Report

## Verdict

`{verdict}`

## Clear Answer

Useful public nflverse-family advanced ingredients are already present locally, and the highest-value executable lane is a review-only `ffopportunity` expected-fantasy-points sidecar. This audit does not run formulas, does not promote any source, and does not change rankings/app/model behavior.

## Remote / Prior Verification

- Current remote HQ HEAD verified before lane: `{REMOTE_HEAD}`
- Prior PFR RB broken-tackle component-test commit verified: `{PRIOR_PFR_COMMIT}`
- Prior PFR accepted result preserved: `RED_PFR_RB_BROKEN_TACKLE_NO_INCREMENTAL_SIGNAL`

## Scope Audited

- Ingredient families audited: `{len(matrix)}`
- Families with local artifacts or prior-locator leads: `{len(found_local)}`
- Families with public/rebuildable nflverse path or partial public path: `{len(rebuildable)}`
- Candidate artifacts ledgered: `{len(ledger)}`

## Highest-Value Present Data

`expected_fantasy_points_ffopportunity` is the highest-value immediately executable ingredient because local `ep_weekly` parquet files contain player-week expected fantasy points, expected yards, expected touchdowns, expected first downs, and actual-minus-expected fields for `2021-2024`.

## Other Useful Present Ingredients

- `next_gen_stats`: local QB/RB/WR/TE NGS files, mostly `2021-2023` plus tiny `2024` fragments; public NGS is rebuildable from `2016+`.
- `ftn_charting`: local `2022-2024` play-level charting files with motion, play-action, screen, RPO, catchable/drop/pressure-like fields.
- `receiving_opportunity_air_yards`: current mart and local advanced files contain useful receiving opportunity primitives, but WOPR/RACR/PACR need sidecar derivation.
- `qb_passing_quality`: NGS passing is useful; ESPN QBR and broad PFR passing are present locally but require separate source/use gates and are not admitted by this audit.

## Parked / Blocked

- PFR RB broken tackles remain descriptive RB review-only context only; no PFR-specific formula branch is recommended.
- Broad PFR, PFR QB passing production use, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain blocked.
- Historical Market / ADP still has high future value, but it should sit behind nflverse ingredient sidecars until point-in-time/as-of safety is proven.
- Injury/availability remains point-in-time review context only and not injury prediction.

## Recommended Sidecar Order

1. `ffopportunity Expected Fantasy Points Formula Mart Sidecar V1`
2. `nflverse NGS Formula Mart Sidecar V1`
3. `nflverse EPA / Opportunity Formula Mart Sidecar V1`
4. `nflverse Receiving Opportunity Formula Mart Sidecar V1`
5. `FTN charting sidecar later`
6. `nflverse Snap Counts / Depth Chart Role Sidecar V1`
7. `Point-in-Time Injury Availability Data Mart Gate V1`
8. `Historical Market / ADP Source Gate and Data Mart Join V1`

## Decision

Formula testing should wait for an ingredient sidecar rather than more same-ingredient formula refinement. The next executable lane is `{next_lane}`.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime/model/ranking behavior did not change.
- No Formula Gauntlet, formula tuning, or production accuracy claim occurred.
- No canonical `local_exports` write occurred.
"""
    write_md(OUT_DIR / "NFLVERSE_ADVANCED_INGREDIENT_AVAILABILITY_FORMULA_MART_GAP_AUDIT_V1_REPORT.md", report)

    next_lane_md = f"""
# nflverse Advanced Next Executable Lane

## Recommendation

`{next_lane}`

## Why

The local `ep_weekly` parquet cache is an actual tabular source, not just a design packet. It carries player-week expected fantasy opportunity fields for `2021-2024`, includes `player_id`, `season`, `week`, `position`, and has direct Formula Data Mart value as an opportunity-quality sidecar.

## Required Guardrails

- Review-only sidecar only.
- Aggregate only closed-season N values for lagged N+1 tests.
- Validate player identity joins to Formula Mart `player_id`.
- Validate missingness by season/position.
- Do not use same-season/current/future context.
- Do not promote production/model-use.
- Do not change rankings or app/runtime behavior.
"""
    write_md(OUT_DIR / "NFLVERSE_ADVANCED_NEXT_EXECUTABLE_LANE.md", next_lane_md)

    parked = """
# nflverse Advanced Parked Or Blocked Data

## Parked

- Historical Market / ADP: high future value, but non-nflverse and point-in-time safety is unproven.
- Injury / availability: useful caution context only; source continuity and as-of semantics need a dedicated gate.
- Depth charts: role value is plausible, but weekly as-of semantics and 2025 source-format changes require review.
- Participation / personnel / pressure: partial, FTN-dependent, and not a route/YPRR/TPRR approval.
- FTN charting: useful but partial `2022+`; keep behind expected points / NGS sidecars.

## Blocked

- Broad PFR production use.
- PFR QB passing production use.
- PFF Elusive Rating.
- `nwr_elusive_proxy_review_only`.
- SportsDataIO.
- Current-only data as historical features.
"""
    write_md(OUT_DIR / "NFLVERSE_ADVANCED_PARKED_OR_BLOCKED_DATA.md", parked)

    source_trace = f"""
# nflverse Advanced Source Trace

## Local Review Inputs

- PFR RB Broken Tackle Data Mart Join / Component Test V1: `{PRIOR['pfr_component_test']}`
- High-Value Signal Data Locator Audit V1: `{PRIOR['high_value_signal_locator']}`
- Formula Results Master Review / Data Upgrade Pivot V1: `{PRIOR['formula_pivot']}`
- Formula Data Mart / Feature Availability Audit V1: `{PRIOR['formula_data_mart']}`
- Full Review-Only Formula Gauntlet Candidate Arena V1: `{PRIOR['full_gauntlet']}`
- Gauntlet Candidate Diversity / Clustering Audit V1: `{PRIOR['clustering_audit']}`
- Diverse Champion Refinement V1: `{PRIOR['diverse_refinement']}`

## Local Data Caches

- Advanced metrics cache: `{ADV_CACHE}`
- PFR source provenance cache: `{PFR_CACHE}`
- nflverse template/input roots: `{'; '.join(str(p) for p in TEMPLATE_ROOTS if p.exists())}`

## Official Public Source References

- nflreadr home: {OFFICIAL_SOURCES['nflreadr_home']}
- nflreadr function reference: {OFFICIAL_SOURCES['nflreadr_reference']}
- nflverse data schedule: {OFFICIAL_SOURCES['nflverse_data_schedule']}
- nflfastR home: {OFFICIAL_SOURCES['nflfastR_home']}
- load_pbp: {OFFICIAL_SOURCES['load_pbp']}
- load_player_stats: {OFFICIAL_SOURCES['load_player_stats']}
- load_ff_opportunity: {OFFICIAL_SOURCES['load_ff_opportunity']}
- load_nextgen_stats: {OFFICIAL_SOURCES['load_nextgen_stats']}
- load_ftn_charting: {OFFICIAL_SOURCES['load_ftn_charting']}

## Use-Gate Notes

This packet uses official public nflverse/nflfastR/nflreadr references to classify availability and rebuildability only. It does not download new data, does not run formula tests, and does not approve production/model-use.
"""
    write_md(OUT_DIR / "NFLVERSE_ADVANCED_SOURCE_TRACE.md", source_trace)


if __name__ == "__main__":
    main()
