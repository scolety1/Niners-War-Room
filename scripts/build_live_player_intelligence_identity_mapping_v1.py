"""Real run: canonical identity mapping for all three Live Player
Intelligence V1 candidate sources (Worker 2 / Work Unit 2-3).

Standalone script -- NOT imported by any production path, NOT exercised by
pytest (reads real local files only, no network I/O of its own; the raw
source files it reads were already fetched by
`scripts/fetch_live_player_intelligence_shadow_snapshot_v1.py`).

Reads:
  * `docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/
    GOVERNED_COMBINED_564_PROJECTION_SNAPSHOT.csv` (the real 564-player
    canonical pool)
  * `local_exports/live_player_intelligence_shadow_v1/nflverse_injuries/
    latest/injuries_2026.csv`
  * `local_exports/live_player_intelligence_shadow_v1/nflverse_depth_charts/
    latest/depth_charts_2026.csv` (latest single-day snapshot only)
  * `local_exports/live_player_intelligence_shadow_v1/sleeper_players/
    latest/sleeper_players_snapshot.json`

Writes:
  * `local_exports/live_player_intelligence_shadow_v1/identity_mapping_v1/
    <source>_all_rows.csv` -- full per-row classification (gitignored, raw,
    can be large -- e.g. 12k+ Sleeper rows).
  * `docs/codex/live_player_intelligence_v1/identity_mapping_v1/
    <source>_quarantined.csv` -- ONLY the quarantined (ambiguous + team-
    mismatch) rows for each source, committed, explicitly listed per the
    directive ("Quarantine... list them explicitly rather than silently
    dropping them").
  * `docs/codex/live_player_intelligence_v1/identity_mapping_v1/
    summary.json` -- the exact counts per source, committed.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(REPO_ROOT))

from src.services.live_player_intelligence_identity_mapping_v1_service import (  # noqa: E402
    classify_rows,
    common_rows_from_nflverse_depth_charts,
    common_rows_from_nflverse_injuries,
    common_rows_from_sleeper_catalog,
    latest_snapshot_only,
    load_canonical_pool,
    quarantined_rows,
    summarize_identity_mapping,
)

SHADOW_ROOT = REPO_ROOT / "local_exports" / "live_player_intelligence_shadow_v1"
RAW_OUTPUT_ROOT = SHADOW_ROOT / "identity_mapping_v1"
COMMITTED_OUTPUT_ROOT = REPO_ROOT / "docs" / "codex" / "live_player_intelligence_v1" / "identity_mapping_v1"

ROW_FIELDS = (
    "source",
    "sourceRowId",
    "playerName",
    "position",
    "team",
    "providerId",
    "primaryClassification",
    "matchedCanonicalPlayerId",
    "teamMismatchCandidateTeam",
    "nameMismatch",
    "providerIdMismatch",
    "teamMismatchIsKnownCodeAlias",
)


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ROW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    canonical_rows = load_canonical_pool()
    print(f"Canonical pool loaded: {len(canonical_rows)} players")

    summary: dict[str, dict] = {}

    # (A) Sleeper -- ALL catalog rows.
    with (SHADOW_ROOT / "sleeper_players" / "latest" / "sleeper_players_snapshot.json").open(encoding="utf-8") as handle:
        sleeper_catalog = json.load(handle)
    sleeper_common = common_rows_from_sleeper_catalog(sleeper_catalog)
    sleeper_results = classify_rows(sleeper_common, canonical_rows)
    _run_source("SLEEPER_PUBLIC_PLAYERS_CATALOG", sleeper_results, summary, len(canonical_rows))

    # (B) nflverse injuries -- ALL rows (182, Week 1, all 32 teams).
    with (SHADOW_ROOT / "nflverse_injuries" / "latest" / "injuries_2026.csv").open(newline="", encoding="utf-8") as handle:
        injuries_rows = list(csv.DictReader(handle))
    injuries_common = common_rows_from_nflverse_injuries(injuries_rows)
    injuries_results = classify_rows(injuries_common, canonical_rows)
    _run_source("NFLVERSE_OFFICIAL_INJURY_REPORT", injuries_results, summary, len(canonical_rows))

    # (C) nflverse depth charts -- latest single-day snapshot only (2,222 rows).
    with (SHADOW_ROOT / "nflverse_depth_charts" / "latest" / "depth_charts_2026.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        depth_chart_rows_all = list(csv.DictReader(handle))
    depth_chart_latest = latest_snapshot_only(depth_chart_rows_all)
    depth_chart_common = common_rows_from_nflverse_depth_charts(depth_chart_latest)
    depth_chart_results = classify_rows(depth_chart_common, canonical_rows)
    _run_source("NFLVERSE_DEPTH_CHARTS", depth_chart_results, summary, len(canonical_rows))

    summary["canonicalPoolSize"] = len(canonical_rows)
    COMMITTED_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (COMMITTED_OUTPUT_ROOT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("\nWrote", COMMITTED_OUTPUT_ROOT / "summary.json")


def _run_source(name: str, results, summary: dict, canonical_pool_size: int) -> None:
    stats = summarize_identity_mapping(results, canonical_pool_size=canonical_pool_size)
    summary[name] = stats
    print(f"\n=== {name} ===")
    print(json.dumps(stats, indent=2))

    all_rows = [r.to_dict() for r in results]
    _write_csv(RAW_OUTPUT_ROOT / f"{name.lower()}_all_rows.csv", all_rows)

    quarantined = [r.to_dict() for r in quarantined_rows(results)]
    _write_csv(COMMITTED_OUTPUT_ROOT / f"{name.lower()}_quarantined.csv", quarantined)
    print(f"Quarantined rows written: {len(quarantined)} -> docs/codex/live_player_intelligence_v1/identity_mapping_v1/{name.lower()}_quarantined.csv")


if __name__ == "__main__":
    main()
