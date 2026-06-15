"""Build the Sprint 5CK consolidated historical package readiness audit.

This script reads only local, internal 2010-2019 historical feature/label
packages. It writes local-only audit CSV/JSON files and does not train models,
score current players, produce probabilities, or create app-readable artifacts.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTCOME_EXPORT_ROOT = REPO_ROOT / "local_exports" / "outcome_probability"
RUN_ID = "sprint_5ck_r2_consolidated_2010_2019_historical_model_readiness_reaudit"
OUT_DIR = OUTCOME_EXPORT_ROOT / RUN_ID

ACCEPTED_EXCLUDED_BLOCKER = {
    "sprint": "5BV",
    "package_seasons": "2018_2019",
    "target_season": "2019",
    "feature_source_season": "2018",
    "player_id": "00-0033357",
    "player_name": "Taysom Hill",
    "position": "QB",
    "target_position": "TE",
    "block_reason": "blocked_source_target_position_mismatch",
}

PACKAGES = [
    {
        "sprint": "5CI",
        "seasons": "2010_2011",
        "path": OUTCOME_EXPORT_ROOT / "sprint_5ci_2010_2011_historical_feature_label_rebuild",
        "metadata": "metadata_sprint_5ci.json",
    },
    {
        "sprint": "5CF",
        "seasons": "2012_2013",
        "path": OUTCOME_EXPORT_ROOT / "sprint_5cf_2012_2013_historical_feature_label_rebuild",
        "metadata": "metadata_sprint_5cf.json",
    },
    {
        "sprint": "5CC",
        "seasons": "2014_2015",
        "path": OUTCOME_EXPORT_ROOT / "sprint_5cc_2014_2015_historical_feature_label_rebuild",
        "metadata": "metadata_sprint_5cc.json",
    },
    {
        "sprint": "5BZ",
        "seasons": "2016_2017",
        "path": OUTCOME_EXPORT_ROOT / "sprint_5bz_2016_2017_historical_feature_label_rebuild",
        "metadata": "metadata_sprint_5bz.json",
    },
    {
        "sprint": "5BV",
        "seasons": "2018_2019",
        "path": OUTCOME_EXPORT_ROOT / "sprint_5bv_2018_2019_historical_feature_label_rebuild",
        "metadata": "metadata_sprint_5bv.json",
    },
]

SUGGESTED_HEADS = {
    "QB": ["same_year_qb_t6", "same_year_qb_t12", "same_year_qb_t18", "same_year_qb_t24"],
    "RB": [
        "same_year_rb_t6",
        "same_year_rb_t12",
        "same_year_rb_t24",
        "same_year_rb_t36",
        "same_year_rb_t48",
    ],
    "WR": [
        "same_year_wr_t6",
        "same_year_wr_t12",
        "same_year_wr_t24",
        "same_year_wr_t36",
        "same_year_wr_t48",
    ],
    "TE": [
        "same_year_te_t3",
        "same_year_te_t6",
        "same_year_te_t12",
        "same_year_te_t18",
        "same_year_te_t24",
    ],
}

FORBIDDEN_TERMS = [
    "fantasy",
    "epa",
    "wopr",
    "racr",
    "pacr",
    "dakota",
    "target_share",
    "air_yards_share",
    "adp",
    "ranking",
    "projection",
    "market",
    "trade",
    "rotowire",
    "private_score",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_package(package: dict[str, object]) -> dict[str, object]:
    base = package["path"]
    seasons = package["seasons"]
    if not isinstance(base, Path) or not isinstance(seasons, str):
        raise TypeError("Invalid package configuration.")
    if not base.exists():
        raise FileNotFoundError(f"Missing local-only package: {base}")

    files = {
        "features": base / f"historical_{seasons}_feature_snapshots.csv",
        "labels": base / f"historical_{seasons}_outcome_labels.csv",
        "blocked": base / f"blocked_historical_{seasons}_rows.csv",
        "duplicates": base / f"historical_{seasons}_duplicate_key_audit.csv",
        "identity": base / f"historical_{seasons}_identity_team_position_audit.csv",
        "first_downs": base / f"historical_{seasons}_first_down_completeness.csv",
        "forbidden": base / f"historical_{seasons}_forbidden_feature_scan.csv",
        "support": base / f"historical_{seasons}_label_support.csv",
        "artifact": base / "artifact_quarantine_audit.csv",
        "release": base / "release_blockers.csv",
    }
    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing package files:\n" + "\n".join(missing))

    metadata_path = base / str(package["metadata"])
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}

    return {
        "config": package,
        "metadata": metadata,
        "features": read_csv(files["features"]),
        "labels": read_csv(files["labels"]),
        "blocked": read_csv(files["blocked"]),
        "duplicates": read_csv(files["duplicates"]),
        "identity": read_csv(files["identity"]),
        "first_downs": read_csv(files["first_downs"]),
        "forbidden": read_csv(files["forbidden"]),
        "support": read_csv(files["support"]),
        "artifact": read_csv(files["artifact"]),
        "release": read_csv(files["release"]),
    }


def support_status(event_count: int, non_event_count: int, seasons: int, sparse_seasons: int) -> str:
    if event_count < 10 or non_event_count < 10 or seasons < 3:
        return "RED_SUPPORT_THIN"
    if event_count < 25 or non_event_count < 25 or seasons < 5 or sparse_seasons > 6:
        return "YELLOW_SUPPORT_CONSTRAINED"
    return "GREEN_SUPPORT_ONLY_FUTURE_EXPERIMENT_ELIGIBLE"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    loaded = [load_package(package) for package in PACKAGES]

    inventory_rows: list[dict[str, object]] = []
    blocked_rows: list[dict[str, object]] = []
    detailed_blocked_rows: list[dict[str, object]] = []
    duplicate_rows: list[dict[str, object]] = []
    identity_rows: list[dict[str, object]] = []
    first_down_rows: list[dict[str, object]] = []
    forbidden_rows: list[dict[str, object]] = []
    artifact_rows: list[dict[str, object]] = []
    release_rows: list[dict[str, object]] = []
    support_rows: list[dict[str, object]] = []

    consolidated_label_keys: Counter[tuple[str, str, str, str]] = Counter()
    consolidated_feature_keys: Counter[tuple[str, str, str, str]] = Counter()

    for package in loaded:
        config = package["config"]
        sprint = str(config["sprint"])
        seasons = str(config["seasons"])

        row_counts = Counter((row["target_season"], row["position"]) for row in package["labels"])
        for (target_season, position), count in sorted(row_counts.items()):
            inventory_rows.append(
                {
                    "output_scope": "internal_only_not_app_readable",
                    "sprint": sprint,
                    "package_seasons": seasons,
                    "target_season": target_season,
                    "position": position,
                    "label_rows": count,
                }
            )

        blocked_counts = Counter(
            (row["target_season"], row["position"], row["block_reason"]) for row in package["blocked"]
        )
        for row in package["blocked"]:
            detailed_blocked_rows.append(
                {
                    "output_scope": "internal_only_not_app_readable",
                    "sprint": sprint,
                    "package_seasons": seasons,
                    "target_season": row.get("target_season", ""),
                    "feature_source_season": row.get("feature_source_season", ""),
                    "player_id": row.get("player_id", ""),
                    "player_name": row.get("player_name", ""),
                    "position": row.get("position", ""),
                    "block_reason": row.get("block_reason", ""),
                    "accepted_excluded_blocker": "no",
                }
            )
        for (target_season, position, reason), count in sorted(blocked_counts.items()):
            blocked_rows.append(
                {
                    "output_scope": "internal_only_not_app_readable",
                    "sprint": sprint,
                    "package_seasons": seasons,
                    "target_season": target_season,
                    "position": position,
                    "block_reason": reason,
                    "blocked_rows": count,
                }
            )

        for row in package["duplicates"]:
            duplicate_rows.append({"sprint": sprint, **row})
        for row in package["identity"]:
            identity_rows.append({"sprint": sprint, **row})
        for row in package["first_downs"]:
            first_down_rows.append({"sprint": sprint, **row})
        for row in package["forbidden"]:
            forbidden_rows.append({"sprint": sprint, **row})
        for row in package["artifact"]:
            artifact_rows.append({"sprint": sprint, **row})
        for row in package["release"]:
            release_rows.append({"sprint": sprint, **row})
        for row in package["support"]:
            support_rows.append({"sprint": sprint, **row})

        for row in package["labels"]:
            consolidated_label_keys[(row["target_season"], row["position"], row["player_id"], row["row_id"])] += 1
        for row in package["features"]:
            consolidated_feature_keys[(row["target_season"], row["position"], row["player_id"], row["row_id"])] += 1

    support_by_head: dict[tuple[str, str], dict[str, object]] = {}
    for position, heads in SUGGESTED_HEADS.items():
        for outcome in heads:
            head_rows = [
                row
                for row in support_rows
                if row.get("position") == position and row.get("outcome") == outcome
            ]
            event_count = sum(int(row["event_count"]) for row in head_rows)
            non_event_count = sum(int(row["non_event_count"]) for row in head_rows)
            row_count = sum(int(row["row_count"]) for row in head_rows)
            seasons = len({row["target_season"] for row in head_rows})
            sparse_seasons = sum(1 for row in head_rows if row.get("sparse_flag") == "yes")
            one_class_seasons = sum(1 for row in head_rows if row.get("one_class_flag") == "yes")
            status = support_status(event_count, non_event_count, seasons, sparse_seasons)
            support_by_head[(position, outcome)] = {
                "output_scope": "internal_only_not_app_readable",
                "position": position,
                "outcome_head": outcome,
                "eligible_labeled_rows": row_count,
                "positive_examples": event_count,
                "negative_examples": non_event_count,
                "seasons_represented": seasons,
                "sparse_seasons": sparse_seasons,
                "one_class_seasons": one_class_seasons,
                "support_status": status,
                "notes": "Support-only readiness. No model training, prediction, calibration, display, ranking, or release.",
            }

    duplicate_extra_failures = [
        row for row in duplicate_rows if int(row.get("duplicate_extra_rows", "0") or 0) != 0
    ]
    identity_failures = [row for row in identity_rows if row.get("status") != "pass"]
    first_down_failures = [row for row in first_down_rows if row.get("status") != "pass"]
    forbidden_failures = [
        row
        for row in forbidden_rows
        if str(row.get("used_in_features", "no")).lower() == "yes"
        and (
            str(row.get("blocker", "no")).lower() == "yes"
            or bool(str(row.get("forbidden_or_quarantined_match", "")).strip())
            or any(term in str(row.get("source_field", "")).lower() for term in FORBIDDEN_TERMS)
        )
    ]
    non_missing_label_blockers = [
        row for row in detailed_blocked_rows if row["block_reason"] != "blocked_missing_label"
    ]
    accepted_blockers = [
        row
        for row in non_missing_label_blockers
        if all(str(row.get(key, "")) == value for key, value in ACCEPTED_EXCLUDED_BLOCKER.items() if key != "target_position")
    ]
    for row in accepted_blockers:
        row["target_position"] = ACCEPTED_EXCLUDED_BLOCKER["target_position"]
        row["accepted_excluded_blocker"] = "yes"
    unaccepted_blockers = [
        row
        for row in non_missing_label_blockers
        if row.get("accepted_excluded_blocker") != "yes"
    ]
    accepted_blocker_contract_pass = len(accepted_blockers) == 1 and not unaccepted_blockers
    app_artifact_failures = [
        row
        for row in artifact_rows
        if row.get("status") != "pass" or row.get("output_scope") != "internal_only_not_app_readable"
    ]
    release_failures = [
        row
        for row in release_rows
        if row.get("status") not in {"blocked", "pass"}
        or row.get("output_scope") != "internal_only_not_app_readable"
    ]
    duplicate_consolidated_labels = [
        key for key, count in consolidated_label_keys.items() if count > 1
    ]
    duplicate_consolidated_features = [
        key for key, count in consolidated_feature_keys.items() if count > 1
    ]

    readiness_counts = Counter(row["support_status"] for row in support_by_head.values())
    audit_verdict = "GREEN" if not any(
        [
            duplicate_extra_failures,
            identity_failures,
            first_down_failures,
            forbidden_failures,
            not accepted_blocker_contract_pass,
            app_artifact_failures,
            release_failures,
            duplicate_consolidated_labels,
            duplicate_consolidated_features,
        ]
    ) else "YELLOW"

    package_inventory = []
    for package in loaded:
        config = package["config"]
        package_inventory.append(
            {
                "output_scope": "internal_only_not_app_readable",
                "sprint": config["sprint"],
                "package_seasons": config["seasons"],
                "feature_rows": len(package["features"]),
                "label_rows": len(package["labels"]),
                "blocked_rows": len(package["blocked"]),
                "metadata_commit": package["metadata"].get("code_version_git_commit", ""),
                "source_dependency": json.dumps(package["metadata"].get("target_source_map", {}), sort_keys=True),
                "model_training_performed": package["metadata"].get("model_training_performed", False),
                "probabilities_generated": package["metadata"].get("probabilities_generated", False),
            }
        )

    write_csv(
        OUT_DIR / "package_inventory.csv",
        package_inventory,
        [
            "output_scope",
            "sprint",
            "package_seasons",
            "feature_rows",
            "label_rows",
            "blocked_rows",
            "metadata_commit",
            "source_dependency",
            "model_training_performed",
            "probabilities_generated",
        ],
    )
    write_csv(
        OUT_DIR / "rows_by_target_season_position.csv",
        inventory_rows,
        ["output_scope", "sprint", "package_seasons", "target_season", "position", "label_rows"],
    )
    write_csv(
        OUT_DIR / "blocked_rows_by_target_season_position_reason.csv",
        blocked_rows,
        [
            "output_scope",
            "sprint",
            "package_seasons",
            "target_season",
            "position",
            "block_reason",
            "blocked_rows",
        ],
    )
    write_csv(
        OUT_DIR / "accepted_excluded_blocker_contract.csv",
        accepted_blockers,
        [
            "output_scope",
            "sprint",
            "package_seasons",
            "target_season",
            "feature_source_season",
            "player_id",
            "player_name",
            "position",
            "target_position",
            "block_reason",
            "accepted_excluded_blocker",
        ],
    )
    write_csv(
        OUT_DIR / "unaccepted_non_missing_label_blockers.csv",
        unaccepted_blockers,
        [
            "output_scope",
            "sprint",
            "package_seasons",
            "target_season",
            "feature_source_season",
            "player_id",
            "player_name",
            "position",
            "block_reason",
            "accepted_excluded_blocker",
        ],
    )
    write_csv(
        OUT_DIR / "label_support_by_head_season_position.csv",
        support_rows,
        [
            "sprint",
            "output_scope",
            "target_season",
            "position",
            "outcome",
            "row_count",
            "event_count",
            "non_event_count",
            "one_class_flag",
            "sparse_flag",
            "notes",
        ],
    )
    write_csv(
        OUT_DIR / "support_readiness_by_head.csv",
        list(support_by_head.values()),
        [
            "output_scope",
            "position",
            "outcome_head",
            "eligible_labeled_rows",
            "positive_examples",
            "negative_examples",
            "seasons_represented",
            "sparse_seasons",
            "one_class_seasons",
            "support_status",
            "notes",
        ],
    )
    write_csv(
        OUT_DIR / "consolidated_duplicate_key_audit.csv",
        duplicate_rows,
        ["sprint", "output_scope", "key_type", "season", "duplicate_extra_rows", "status"],
    )
    write_csv(
        OUT_DIR / "consolidated_identity_team_position_audit.csv",
        identity_rows,
        [
            "sprint",
            "output_scope",
            "row_family",
            "season",
            "row_count",
            "missing_player_id",
            "missing_player_name",
            "missing_player_display_name",
            "missing_team",
            "missing_position",
            "missing_position_group",
            "status",
        ],
    )
    write_csv(
        OUT_DIR / "consolidated_first_down_completeness.csv",
        first_down_rows,
        [
            "sprint",
            "output_scope",
            "row_family",
            "season",
            "modeled_rows",
            "missing_rushing_first_downs",
            "missing_receiving_first_downs",
            "status",
        ],
    )
    write_csv(
        OUT_DIR / "consolidated_forbidden_feature_scan.csv",
        forbidden_rows,
        [
            "sprint",
            "output_scope",
            "source_field",
            "allowlist_status",
            "forbidden_or_quarantined_match",
            "used_in_features",
            "blocker",
            "recommended_handling",
        ],
    )

    metadata = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "audit_verdict": audit_verdict,
        "output_scope": "internal_only_not_app_readable",
        "app_release_status": "blocked_not_app_readable",
        "packages_audited": [package["config"]["sprint"] for package in loaded],
        "target_seasons": list(range(2010, 2020)),
        "total_feature_rows": sum(len(package["features"]) for package in loaded),
        "total_label_rows": sum(len(package["labels"]) for package in loaded),
        "total_blocked_rows": sum(len(package["blocked"]) for package in loaded),
        "non_missing_label_blockers": len(non_missing_label_blockers),
        "accepted_excluded_blockers": len(accepted_blockers),
        "unaccepted_non_missing_label_blockers": len(unaccepted_blockers),
        "accepted_blocker_contract_pass": accepted_blocker_contract_pass,
        "accepted_blocker_contract": ACCEPTED_EXCLUDED_BLOCKER,
        "duplicate_key_failures": len(duplicate_extra_failures),
        "identity_failures": len(identity_failures),
        "first_down_failures": len(first_down_failures),
        "forbidden_feature_failures": len(forbidden_failures),
        "app_artifact_failures": len(app_artifact_failures),
        "release_failures": len(release_failures),
        "support_readiness_counts": dict(readiness_counts),
        "return_stat_limitation": "granular return_yards and return_tds remain unavailable; no return scoring included",
        "model_training_performed": False,
        "probabilities_generated": False,
        "exact_percentages": "blocked",
        "coarse_bands": "blocked",
        "app_wiring": "blocked",
        "rankings_sorting": "blocked",
        "hidden_sort_keys": "blocked",
        "promoted_artifacts": "blocked",
    }
    (OUT_DIR / "metadata_sprint_5ck.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "README_SPRINT_5CK.md").write_text(
        "# Sprint 5CK-R2 Local-Only Consolidated Re-Audit\n\n"
        "Internal-only consolidated inventory for 2010-2019 historical feature/label packages. "
        "The only accepted non-missing-label blocker is the committed 5CK-R Taysom Hill "
        "2018 QB to 2019 TE excluded row. No model training, probabilities, bands, app outputs, "
        "rankings, hidden sort keys, or promoted artifacts.\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
