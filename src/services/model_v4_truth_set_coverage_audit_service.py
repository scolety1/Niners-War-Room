from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

TRUTH_SET_PLAYER_UNIVERSE_PATH = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")
TRUTH_SET_COVERAGE_AUDIT_CSV_PATH = Path("docs/model_v4/TRUTH_SET_COVERAGE_AUDIT.csv")
TRUTH_SET_COVERAGE_AUDIT_MD_PATH = Path("docs/model_v4/TRUTH_SET_COVERAGE_AUDIT.md")
NINERS_ROSTER_RANK_PATH = Path(
    "docs/model_v4/official_inputs/NINERS_ROSTER_RANKS_20260331.csv"
)
ACTIVE_PUBLIC_SOURCE_ROOT = Path("local_exports/active_veteran_model_public_sources")
TRUTH_SET_V2_YOUNG_BRIDGE_PATH = Path(
    "local_exports/truth_set_lab/v2/reports/young_bridge_prior_preview.csv"
)
V3_2_PROMOTED_ROOT = Path("local_exports/truth_set_lab/v3_2/promoted_review_models")

TRUTH_SET_COVERAGE_AUDIT_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "truth_set_group",
    "lifecycle_expected",
    "roster_context",
    "source_priority",
    "identity_coverage",
    "production_coverage",
    "first_down_coverage",
    "usage_coverage",
    "snap_coverage",
    "projection_coverage",
    "age_bio_coverage",
    "injury_context_coverage",
    "young_prior_coverage",
    "market_context_availability",
    "roster_rank_context",
    "formula_rebuild_blockers",
    "review_warnings",
    "readiness_for_fixture_testing",
    "notes",
)

CORE_NFL_LIFECYCLES = {
    "year_one_nfl_bridge",
    "year_two_nfl_bridge",
    "year_three_nfl_bridge",
    "established_veteran",
    "free_agent",
    "released_veteran",
}
YOUNG_LIFECYCLES = {
    "incoming_rookie",
    "year_one_nfl_bridge",
    "year_two_nfl_bridge",
    "year_three_nfl_bridge",
}


@dataclass(frozen=True)
class ModelV4TruthSetCoverageAudit:
    rows: tuple[dict[str, str], ...]
    summary: dict[str, str]
    source_paths: dict[str, str]


def build_model_v4_truth_set_coverage_audit(
    *,
    truth_set_path: str | Path = TRUTH_SET_PLAYER_UNIVERSE_PATH,
    output_csv_path: str | Path | None = None,
    output_md_path: str | Path | None = None,
    v3_2_root: str | Path = V3_2_PROMOTED_ROOT,
    active_source_root: str | Path = ACTIVE_PUBLIC_SOURCE_ROOT,
    young_bridge_path: str | Path = TRUTH_SET_V2_YOUNG_BRIDGE_PATH,
    roster_rank_path: str | Path = NINERS_ROSTER_RANK_PATH,
) -> ModelV4TruthSetCoverageAudit:
    truth_set = _read_rows(truth_set_path)
    v3_2_path = _latest_v3_2_promotion_path(v3_2_root)
    active_root = Path(active_source_root)

    v3_bucket_rows = _read_rows_if_exists(v3_2_path / "truth_set_v3_source_coverage.csv")
    active_coverage_rows = _read_rows_if_exists(active_root / "stats_first_source_coverage.csv")
    active_normalized_rows = _read_rows_if_exists(
        active_root / "stats_first_normalized_features.csv"
    )
    identity_rows = _read_rows_if_exists(active_root / "sleeper_nflverse_identity_bridge.csv")
    roster_rank_rows = _read_rows_if_exists(roster_rank_path)
    young_prior_rows = _read_rows_if_exists(young_bridge_path)

    v3_by_name_bucket = _bucket_rows_by_name(v3_bucket_rows)
    active_coverage_by_name = _index_rows_by_name(active_coverage_rows, "player_name")
    active_normalized_by_name = _index_rows_by_name(active_normalized_rows, "player_name")
    identity_by_name = _identity_index(identity_rows)
    roster_rank_by_name = _index_rows_by_name(roster_rank_rows, "player_name")
    young_prior_by_name = _index_rows_by_name(young_prior_rows, "player_name")

    audit_rows = tuple(
        _audit_truth_set_player(
            row,
            v3_by_name_bucket=v3_by_name_bucket,
            active_coverage_by_name=active_coverage_by_name,
            active_normalized_by_name=active_normalized_by_name,
            identity_by_name=identity_by_name,
            roster_rank_by_name=roster_rank_by_name,
            young_prior_by_name=young_prior_by_name,
        )
        for row in truth_set
    )
    summary = _summary(audit_rows)
    source_paths = {
        "truth_set": str(Path(truth_set_path)),
        "v3_2_promotion_root": str(v3_2_path),
        "active_public_source_root": str(active_root),
        "young_bridge_path": str(Path(young_bridge_path)),
        "roster_rank_path": str(Path(roster_rank_path)),
    }

    if output_csv_path is not None:
        _write_csv(output_csv_path, audit_rows)
    if output_md_path is not None:
        _write_markdown(output_md_path, audit_rows, summary, source_paths)

    return ModelV4TruthSetCoverageAudit(
        rows=audit_rows,
        summary=summary,
        source_paths=source_paths,
    )


def _audit_truth_set_player(
    truth_row: dict[str, str],
    *,
    v3_by_name_bucket: dict[str, dict[str, dict[str, str]]],
    active_coverage_by_name: dict[str, dict[str, str]],
    active_normalized_by_name: dict[str, dict[str, str]],
    identity_by_name: dict[str, dict[str, str]],
    roster_rank_by_name: dict[str, dict[str, str]],
    young_prior_by_name: dict[str, dict[str, str]],
) -> dict[str, str]:
    player_name = truth_row["player_name"]
    v3_buckets = _lookup_index(v3_by_name_bucket, player_name, {})
    active_coverage = _lookup_index(active_coverage_by_name, player_name, {})
    active_normalized = _lookup_index(active_normalized_by_name, player_name, {})
    identity = _lookup_index(identity_by_name, player_name, {})
    young_prior = _lookup_index(young_prior_by_name, player_name, {})
    lifecycle = truth_row["lifecycle_expected"]
    source_priority = truth_row["source_priority"]

    identity_status = _identity_status(identity, active_normalized, v3_buckets)
    production_status = _production_status(v3_buckets, active_coverage)
    first_down_status = _first_down_status(v3_buckets, active_coverage, active_normalized)
    usage_status = _usage_status(v3_buckets, active_coverage)
    snap_status = _snap_status(v3_buckets, active_normalized)
    projection_status = _projection_status(v3_buckets, active_coverage, active_normalized)
    age_status = _age_bio_status(active_coverage, active_normalized)
    injury_status = _context_status(v3_buckets, active_coverage, "injury")
    young_prior_status = _young_prior_status(
        lifecycle,
        source_priority,
        v3_buckets,
        active_normalized,
        young_prior,
    )
    market_status = _market_status(v3_buckets, active_coverage)
    roster_status = _roster_rank_status(
        _lookup_index(roster_rank_by_name, player_name, {}),
        truth_row["roster_context"],
    )

    blockers, warnings = _gaps(
        lifecycle=lifecycle,
        source_priority=source_priority,
        identity_status=identity_status,
        production_status=production_status,
        first_down_status=first_down_status,
        usage_status=usage_status,
        snap_status=snap_status,
        projection_status=projection_status,
        age_status=age_status,
        injury_status=injury_status,
        young_prior_status=young_prior_status,
        market_status=market_status,
    )
    readiness = _readiness(blockers, warnings)

    return {
        "player_name": player_name,
        "position": truth_row["position"],
        "nfl_team": truth_row["nfl_team"],
        "truth_set_group": truth_row["truth_set_group"],
        "lifecycle_expected": lifecycle,
        "roster_context": truth_row["roster_context"],
        "source_priority": source_priority,
        "identity_coverage": identity_status,
        "production_coverage": production_status,
        "first_down_coverage": first_down_status,
        "usage_coverage": usage_status,
        "snap_coverage": snap_status,
        "projection_coverage": projection_status,
        "age_bio_coverage": age_status,
        "injury_context_coverage": injury_status,
        "young_prior_coverage": young_prior_status,
        "market_context_availability": market_status,
        "roster_rank_context": roster_status,
        "formula_rebuild_blockers": "|".join(blockers),
        "review_warnings": "|".join(warnings),
        "readiness_for_fixture_testing": readiness,
        "notes": _notes(lifecycle, v3_buckets, active_coverage, active_normalized),
    }


def _identity_status(
    identity: dict[str, str],
    active_normalized: dict[str, str],
    v3_buckets: dict[str, dict[str, str]],
) -> str:
    if identity:
        if identity.get("match_status") == "matched":
            if _truthy(identity.get("manual_review_required")):
                return "review"
            return "covered"
        return "review"
    if active_normalized.get("player_id") or any(v3_buckets.values()):
        return "partial"
    return "missing"


def _production_status(
    v3_buckets: dict[str, dict[str, str]],
    active_coverage: dict[str, str],
) -> str:
    v3_status = _bucket_status(v3_buckets, "production")
    if v3_status == "covered":
        return "covered"
    active_status = active_coverage.get("production", "")
    if active_status in {"ready", "review"}:
        return "partial"
    if active_status == "review_missing":
        return "missing"
    return "missing"


def _first_down_status(
    v3_buckets: dict[str, dict[str, str]],
    active_coverage: dict[str, str],
    active_normalized: dict[str, str],
) -> str:
    production = v3_buckets.get("production", {})
    if (
        production.get("coverage_status") == "covered"
        and "first_down_td_fit" in production.get("fields", "")
    ):
        return "covered"
    if active_normalized.get("first_down_td_fit"):
        warnings = active_normalized.get("warnings", "")
        if "missing_lve_scoring_history" in warnings:
            return "review"
        return "partial"
    if active_coverage.get("production") in {"ready", "review"}:
        return "review"
    return "missing"


def _usage_status(
    v3_buckets: dict[str, dict[str, str]],
    active_coverage: dict[str, str],
) -> str:
    if _bucket_status(v3_buckets, "role_usage") == "covered":
        return "covered"
    if active_coverage.get("role_usage") == "ready":
        return "partial"
    if active_coverage.get("role_usage") == "review":
        return "review"
    return "missing"


def _snap_status(
    v3_buckets: dict[str, dict[str, str]],
    active_normalized: dict[str, str],
) -> str:
    if _bucket_status(v3_buckets, "snap_share") == "covered":
        return "covered"
    if "missing_snap_counts" in active_normalized.get("warnings", ""):
        return "missing"
    if active_normalized.get("role_security"):
        return "review"
    return "missing"


def _projection_status(
    v3_buckets: dict[str, dict[str, str]],
    active_coverage: dict[str, str],
    active_normalized: dict[str, str],
) -> str:
    v3_projection = v3_buckets.get("projection", {})
    if v3_projection.get("coverage_status") == "covered":
        return "covered"
    projection_source_status = (
        active_coverage.get("projection_source_status")
        or active_normalized.get("projection_source_status")
    )
    if projection_source_status == "local_baseline_projection":
        return "review"
    if projection_source_status == "missing_projection":
        return "missing"
    if active_coverage.get("projection") in {"ready", "review"}:
        return "review"
    return "missing"


def _age_bio_status(
    active_coverage: dict[str, str],
    active_normalized: dict[str, str],
) -> str:
    if active_coverage.get("age_bio") == "ready":
        return "covered"
    if active_normalized.get("age_raw"):
        return "covered"
    return "missing"


def _context_status(
    v3_buckets: dict[str, dict[str, str]],
    active_coverage: dict[str, str],
    bucket: str,
) -> str:
    v3_row = v3_buckets.get(bucket, {})
    if v3_row.get("coverage_status") == "covered":
        return "context_only"
    if v3_row.get("coverage_status") == "review":
        return "review"
    active_status = active_coverage.get(bucket, "")
    if active_status == "ready":
        return "context_only"
    if active_status == "review_missing":
        return "missing"
    return "missing"


def _young_prior_status(
    lifecycle: str,
    source_priority: str,
    v3_buckets: dict[str, dict[str, str]],
    active_normalized: dict[str, str],
    young_prior: dict[str, str],
) -> str:
    if lifecycle not in YOUNG_LIFECYCLES:
        return "not_applicable"
    if _bucket_status(v3_buckets, "young_bridge_prior") == "covered":
        return "covered"
    if active_normalized.get("young_nfl_bridge_prior_score"):
        return "partial"
    if young_prior.get("draft_capital_prior_score"):
        return "preview_only"
    if source_priority in {"critical", "high"}:
        return "missing"
    return "review"


def _market_status(
    v3_buckets: dict[str, dict[str, str]],
    active_coverage: dict[str, str],
) -> str:
    v3_market = v3_buckets.get("market_liquidity", {})
    if v3_market.get("coverage_status") == "covered":
        return "context_only"
    if v3_market.get("coverage_status") in {"missing", "review"}:
        return "missing"
    if active_coverage.get("market_liquidity") == "ready":
        return "context_only"
    return "missing"


def _roster_rank_status(row: dict[str, str], roster_context: str) -> str:
    if row:
        if roster_context == "required_top_five_release_pool":
            return "covered_required_top_five"
        return "covered_niners_roster"
    if roster_context in {"", "league_context", "draft_room_control", "draft_room_review"}:
        return "not_applicable"
    return "missing"


def _gaps(
    *,
    lifecycle: str,
    source_priority: str,
    identity_status: str,
    production_status: str,
    first_down_status: str,
    usage_status: str,
    snap_status: str,
    projection_status: str,
    age_status: str,
    injury_status: str,
    young_prior_status: str,
    market_status: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    blockers: list[str] = []
    warnings: list[str] = []
    is_incoming = lifecycle == "incoming_rookie"
    is_core_nfl = lifecycle in CORE_NFL_LIFECYCLES
    high_priority = source_priority in {"critical", "high"}

    if identity_status == "missing":
        blockers.append("missing_identity")
    elif identity_status in {"partial", "review"}:
        warnings.append("identity_review")

    if is_core_nfl:
        _block_or_warn(blockers, warnings, "production", production_status, high_priority)
        _block_or_warn(blockers, warnings, "first_downs", first_down_status, high_priority)
        _block_or_warn(blockers, warnings, "usage", usage_status, high_priority)
        _block_or_warn(blockers, warnings, "age_bio", age_status, high_priority)
    elif is_incoming:
        if young_prior_status == "missing":
            blockers.append("missing_young_prior")
        if age_status == "missing":
            warnings.append("missing_age_bio")

    if lifecycle in YOUNG_LIFECYCLES and young_prior_status in {"missing", "review"}:
        if high_priority:
            blockers.append("missing_young_prior")
        else:
            warnings.append("missing_young_prior")
    elif young_prior_status in {"partial", "preview_only"}:
        warnings.append("young_prior_preview_only")

    if snap_status in {"missing", "review"} and is_core_nfl:
        warnings.append("snap_share_gap")
    if projection_status in {"missing", "review"}:
        warnings.append("projection_gap")
    if injury_status in {"missing", "review"}:
        warnings.append("injury_context_gap")
    if market_status == "missing":
        warnings.append("market_context_gap")

    return tuple(dict.fromkeys(blockers)), tuple(dict.fromkeys(warnings))


def _block_or_warn(
    blockers: list[str],
    warnings: list[str],
    label: str,
    status: str,
    high_priority: bool,
) -> None:
    if status == "missing":
        if high_priority:
            blockers.append(f"missing_{label}")
        else:
            warnings.append(f"missing_{label}")
    elif status in {"review", "partial"}:
        warnings.append(f"{label}_review")


def _readiness(blockers: tuple[str, ...], warnings: tuple[str, ...]) -> str:
    if blockers:
        return "blocked_missing_input"
    if warnings:
        return "review"
    return "ready"


def _notes(
    lifecycle: str,
    v3_buckets: dict[str, dict[str, str]],
    active_coverage: dict[str, str],
    active_normalized: dict[str, str],
) -> str:
    notes: list[str] = []
    if lifecycle == "incoming_rookie":
        notes.append("incoming rookie; NFL production gaps are expected")
    if v3_buckets:
        notes.append("has Truth Set Lab v3/v3.2 coverage rows")
    if active_coverage:
        notes.append("has active public-source coverage row")
    if "missing_participation_proxy" in active_normalized.get("warnings", ""):
        notes.append("route/participation remains unavailable from safe free data")
    return "; ".join(notes)


def _summary(rows: tuple[dict[str, str], ...]) -> dict[str, str]:
    readiness_counts = Counter(row["readiness_for_fixture_testing"] for row in rows)
    blocker_rows = [row for row in rows if row["formula_rebuild_blockers"]]
    warning_rows = [row for row in rows if row["review_warnings"]]
    return {
        "truth_set_players": str(len(rows)),
        "ready": str(readiness_counts.get("ready", 0)),
        "review": str(readiness_counts.get("review", 0)),
        "blocked_missing_input": str(readiness_counts.get("blocked_missing_input", 0)),
        "players_with_formula_rebuild_blockers": str(len(blocker_rows)),
        "players_with_review_warnings": str(len(warning_rows)),
    }


def _write_markdown(
    path: str | Path,
    rows: tuple[dict[str, str], ...],
    summary: dict[str, str],
    source_paths: dict[str, str],
) -> None:
    blockers = [row for row in rows if row["formula_rebuild_blockers"]]
    review_only = [row for row in rows if row["review_warnings"]]
    lines = [
        "# Model v4 Truth Set Coverage Audit",
        "",
        "Created: 2026-05-16",
        "",
        "This audit checks whether the broad Model v4 truth set has enough currently",
        "available evidence to support formula rebuild work. It does not score players,",
        "change formulas, unlock readiness, or promote rankings.",
        "",
        "Machine-readable file:",
        "",
        "- `docs/model_v4/TRUTH_SET_COVERAGE_AUDIT.csv`",
        "",
        "## Source Inputs Checked",
        "",
    ]
    lines.extend(f"- `{name}`: `{source_path}`" for name, source_path in source_paths.items())
    lines.extend(
        [
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "| --- | --- |",
        ]
    )
    lines.extend(f"| {key} | {value} |" for key, value in summary.items())
    lines.extend(
        [
            "",
            "## Formula Rebuild Blockers",
            "",
        ]
    )
    if blockers:
        lines.extend(
            [
                "| Player | Lifecycle | Source Priority | Blockers |",
                "| --- | --- | --- | --- |",
            ]
        )
        lines.extend(
            "| {player_name} | {lifecycle_expected} | {source_priority} | "
            "{formula_rebuild_blockers} |".format(**row)
            for row in blockers
        )
    else:
        lines.append("No formula rebuild blockers were found.")

    warning_counts = Counter()
    for row in review_only:
        for warning in row["review_warnings"].split("|"):
            if warning:
                warning_counts[warning] += 1
    lines.extend(
        [
            "",
            "## Review Warning Counts",
            "",
            "| Warning | Players |",
            "| --- | --- |",
        ]
    )
    if warning_counts:
        lines.extend(
            f"| {warning} | {count} |" for warning, count in sorted(warning_counts.items())
        )
    else:
        lines.append("| none | 0 |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `blocked_missing_input` means a player lacks evidence needed before formula",
            "  rebuild fixtures can fairly evaluate that player.",
            "- `review` means formula work can proceed, but receipts must surface the gap.",
            "- Projection, injury, and market gaps are review warnings unless a later",
            "  contract explicitly promotes them to blocking status.",
            "- Incoming rookies are expected to lack NFL production, usage, and snap data;",
            "  their key blocker is missing identity or young/prospect prior evidence.",
            "",
        ]
    )
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _write_csv(path: str | Path, rows: tuple[dict[str, str], ...]) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRUTH_SET_COVERAGE_AUDIT_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def _latest_v3_2_promotion_path(root: str | Path) -> Path:
    root_path = Path(root)
    if not root_path.exists():
        return root_path
    dirs = [path for path in root_path.iterdir() if path.is_dir()]
    if not dirs:
        return root_path
    return sorted(dirs, key=lambda path: path.name)[-1]


def _bucket_rows_by_name(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, dict[str, str]]]:
    by_name: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        by_name[_name_key(row.get("player_name"))][row.get("bucket", "")] = row
    return dict(by_name)


def _identity_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        for field in ("player_name", "bridge_name", "stat_player_name"):
            key = _name_key(row.get(field))
            if key:
                indexed.setdefault(key, row)
    return indexed


def _lookup_index(
    index: dict[str, object],
    player_name: str,
    default: object,
) -> object:
    return (
        index.get(_name_key(player_name))
        or index.get(_name_key_without_suffix(player_name))
        or default
    )


def _index_rows_by_name(
    rows: list[dict[str, str]],
    name_field: str,
) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        key = _name_key(row.get(name_field))
        if key:
            indexed[key] = row
            no_suffix = _name_key_without_suffix(row.get(name_field))
            indexed.setdefault(no_suffix, row)
    return indexed


def _bucket_status(
    v3_buckets: dict[str, dict[str, str]],
    bucket: str,
) -> str:
    return v3_buckets.get(bucket, {}).get("coverage_status", "")


def _read_rows_if_exists(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    if not path.exists():
        return []
    return _read_rows(path)


def _read_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _name_key(value: object) -> str:
    name = str(value or "").lower()
    name = name.replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "", name)


def _name_key_without_suffix(value: object) -> str:
    name = str(value or "")
    name = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?\b", "", name, flags=re.IGNORECASE)
    return _name_key(name)


def _truthy(value: object) -> bool:
    return str(value or "").lower() in {"true", "1", "yes"}
