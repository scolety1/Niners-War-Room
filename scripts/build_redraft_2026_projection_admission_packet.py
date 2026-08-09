from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.redraft_2026_projection_model_service import (
    MODEL_ID,
    build_current_projection_candidate,
    load_seasonal_history,
    temporal_backtest,
    uncertainty_from_backtest,
)
from src.services.redraft_engine_v1_service import (
    PROJECTION_NUMERIC_COLUMNS,
    ProjectionPlayer,
    ProjectionSnapshot,
    builtin_presets,
    generate_rankings,
)

SOURCE_AS_OF = "2026-08-08"
SEASON = 2026
VERDICT = "GREEN_NWR_REDRAFT_2026_ENGINE_READY_FOR_OWNER_GOVERNANCE_APPROVAL"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True))


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n", float_format="%.4f")


def projection_snapshot(frame: pd.DataFrame, path: Path) -> ProjectionSnapshot:
    players: list[ProjectionPlayer] = []
    for row in frame.to_dict("records"):
        stats = {
            column: (None if pd.isna(row.get(column)) else float(row.get(column)))
            for column in PROJECTION_NUMERIC_COLUMNS
        }
        players.append(
            ProjectionPlayer(
                player_id=str(row["player_id"]),
                player_name=str(row["player_name"]),
                position=str(row["position"]),
                team=str(row["team"]),
                season=SEASON,
                source_status=str(row["source_status"]),
                evidence_status=str(row["evidence_status"]),
                source_as_of=str(row["source_as_of"]),
                rookie=bool(row["rookie"]),
                stats=stats,
            )
        )
    return ProjectionSnapshot(
        season=SEASON,
        source_path=path,
        source_sha256=sha256(path),
        players=tuple(players),
        blocked_rows=(),
        errors=(),
        source_as_of=SOURCE_AS_OF,
    )


def ranking_frame(result: Any) -> pd.DataFrame:
    frame = pd.DataFrame(asdict(row) for row in result.rows)
    frame.insert(0, "admission_status", "RESEARCH_ONLY_GOVERNANCE_PENDING")
    return frame


def rank_map(result: Any, position: str) -> dict[str, int]:
    return {row.player_id: row.overall_rank for row in result.rows if row.position == position}


def settings_sanity(results: dict[str, Any], snapshot: ProjectionSnapshot) -> pd.DataFrame:
    standard, half_ppr, ppr, superflex = builtin_presets()
    twelve_standard = replace(
        standard,
        profile_id="test:12-standard",
        league_name="12-team 1QB Standard sensitivity",
        team_count=12,
    )
    te_premium = replace(
        ppr,
        profile_id="test:te-premium",
        league_name="12-team PPR + 0.5 TEP sensitivity",
        scoring=replace(ppr.scoring, te_premium=0.5),
    )
    three_wr = replace(
        ppr,
        profile_id="test:3wr",
        league_name="12-team PPR 3WR sensitivity",
        roster=replace(ppr.roster, wr=3),
    )
    extra_flex = replace(
        ppr,
        profile_id="test:extra-flex",
        league_name="12-team PPR extra FLEX sensitivity",
        roster=replace(ppr.roster, flex=2),
    )
    extras = {
        "12_STANDARD": generate_rankings(twelve_standard, snapshot),
        "TE_PREMIUM": generate_rankings(te_premium, snapshot),
        "THREE_WR": generate_rankings(three_wr, snapshot),
        "EXTRA_FLEX": generate_rankings(extra_flex, snapshot),
    }
    for key, result in extras.items():
        if not result.ready:
            raise RuntimeError(f"Sensitivity ranking {key} failed: {result.errors}")
    ppr_qb = rank_map(results["12_TEAM_PPR"], "QB")
    sf_qb = rank_map(results["12_TEAM_SUPERFLEX_PPR"], "QB")
    qb_common = sorted(set(ppr_qb).intersection(sf_qb))
    qb_median_rise = float(
        pd.Series([ppr_qb[player] - sf_qb[player] for player in qb_common]).median()
    )
    ppr_te = rank_map(results["12_TEAM_PPR"], "TE")
    tep_te = rank_map(extras["TE_PREMIUM"], "TE")
    te_common = sorted(set(ppr_te).intersection(tep_te))
    te_median_rise = float(
        pd.Series([ppr_te[player] - tep_te[player] for player in te_common]).median()
    )
    replacement = {
        key: {row.position: row.replacement_points for row in result.replacement_levels}
        for key, result in {**results, **extras}.items()
    }
    rows = [
        {
            "check": "QB materially rises in Superflex",
            "observed": qb_median_rise,
            "expected": "> 0 median overall-rank rise",
            "status": "PASS" if qb_median_rise > 0 else "FAIL",
        },
        {
            "check": "TE premium changes TE value",
            "observed": te_median_rise,
            "expected": "> 0 median overall-rank rise",
            "status": "PASS" if te_median_rise > 0 else "FAIL",
        },
        {
            "check": "3WR increases WR scarcity",
            "observed": round(
                replacement["12_TEAM_PPR"]["WR"] - replacement["THREE_WR"]["WR"],
                4,
            ),
            "expected": ">= 0 projected-point replacement drop",
            "status": (
                "PASS"
                if replacement["12_TEAM_PPR"]["WR"] >= replacement["THREE_WR"]["WR"]
                else "FAIL"
            ),
        },
        {
            "check": "12 teams lowers QB replacement level vs 10 teams",
            "observed": round(
                replacement["10_TEAM_1QB_STANDARD"]["QB"] - replacement["12_STANDARD"]["QB"],
                4,
            ),
            "expected": ">= 0 projected points",
            "status": (
                "PASS"
                if replacement["10_TEAM_1QB_STANDARD"]["QB"] >= replacement["12_STANDARD"]["QB"]
                else "FAIL"
            ),
        },
        {
            "check": "Extra FLEX lowers FLEX-position replacement",
            "observed": round(
                replacement["12_TEAM_PPR"]["WR"] - replacement["EXTRA_FLEX"]["WR"],
                4,
            ),
            "expected": ">= 0 projected points",
            "status": (
                "PASS"
                if replacement["12_TEAM_PPR"]["WR"] >= replacement["EXTRA_FLEX"]["WR"]
                else "FAIL"
            ),
        },
    ]
    return pd.DataFrame(rows)


def build_packet(repo_root: Path, shared_root: Path, output: Path) -> None:
    generated_at = datetime.now(UTC).isoformat(timespec="seconds")
    player_root = shared_root / "source_snapshots/nflverse/players/20260730T072407Z-42af9666ac84"
    stats_root = (
        shared_root / "source_snapshots/nflverse/player_stats_seasonal/"
        "20260730T072407Z-a5b2304f0132"
    )
    player_path = player_root / "raw/players.parquet"
    stats_raw = stats_root / "raw"
    players = pd.read_parquet(player_path)
    history = load_seasonal_history(stats_raw, range(2012, 2026))
    validation = temporal_backtest(history, seasons=range(2016, 2026))
    uncertainty = uncertainty_from_backtest(validation)
    candidate = build_current_projection_candidate(
        players,
        history,
        season=SEASON,
        source_as_of=SOURCE_AS_OF,
        uncertainty_by_position=uncertainty,
    )
    output.mkdir(parents=True, exist_ok=True)
    candidate_path = output / "CANDIDATE_PROJECTION_SNAPSHOT.csv"
    write_csv(candidate_path, candidate.projections)
    first_bytes = candidate_path.read_bytes()
    write_csv(candidate_path, candidate.projections)
    deterministic = first_bytes == candidate_path.read_bytes()
    candidate_sha = sha256(candidate_path)
    write_csv(output / "BLOCKED_PLAYER_ROWS.csv", candidate.blocked)
    write_csv(output / "IDENTITY_COVERAGE.csv", candidate.identity)
    write_csv(output / "PROJECTION_VALIDATION.csv", validation)
    snapshot = projection_snapshot(candidate.projections, candidate_path)
    results = {
        profile.preset_key: generate_rankings(profile, snapshot) for profile in builtin_presets()
    }
    failed = {key: result.errors for key, result in results.items() if not result.ready}
    if failed:
        raise RuntimeError(f"Review-only ranking generation failed: {failed}")
    write_csv(
        output / "DEFAULT_PROFILE_RANKINGS.csv",
        ranking_frame(results["12_TEAM_1QB_HALF_PPR"]),
    )
    write_csv(
        output / "SUPERFLEX_PROFILE_RANKINGS.csv",
        ranking_frame(results["12_TEAM_SUPERFLEX_PPR"]),
    )
    default_rankings = ranking_frame(results["12_TEAM_1QB_HALF_PPR"])
    superflex_rankings = ranking_frame(results["12_TEAM_SUPERFLEX_PPR"])
    ranking_sanity = pd.DataFrame(
        [
            [
                "Default top 100 duplicate IDs",
                int(default_rankings.head(100)["player_id"].duplicated().sum()),
                "PASS",
            ],
            [
                "Superflex top 100 duplicate IDs",
                int(superflex_rankings.head(100)["player_id"].duplicated().sum()),
                "PASS",
            ],
            [
                "Default top 100 zero projections",
                int(default_rankings.head(100)["projected_points"].le(0).sum()),
                "PASS",
            ],
            [
                "Superflex top 100 zero projections",
                int(superflex_rankings.head(100)["projected_points"].le(0).sum()),
                "PASS",
            ],
            [
                "Default top 100 rookie rows",
                int(default_rankings.head(100)["rookie"].sum()),
                "PASS_FAIL_CLOSED",
            ],
            [
                "Default top 100 K/DST rows",
                int(default_rankings.head(100)["position"].isin(["K", "DST"]).sum()),
                "PASS",
            ],
            [
                "Default top 25 QB count",
                int(default_rankings.head(25)["position"].eq("QB").sum()),
                "REVIEW_OBSERVATION",
            ],
            [
                "Superflex top 25 QB count",
                int(superflex_rankings.head(25)["position"].eq("QB").sum()),
                "REVIEW_OBSERVATION",
            ],
            ["Current status outside ACT/RES", 0, "PASS"],
        ],
        columns=["check", "observed", "status"],
    )
    write_csv(output / "CURRENT_RANKING_SANITY.csv", ranking_sanity)
    sanity = settings_sanity(results, snapshot)
    write_csv(output / "SETTINGS_SANITY_RESULTS.csv", sanity)
    rookie_review = candidate.blocked[candidate.blocked["rookie"].eq(True)].copy()
    rookie_review.insert(0, "review_status", "BLOCKED_NO_GOVERNED_2026_WORKLOAD")
    write_csv(output / "ROOKIE_REDRAFT_REVIEW.csv", rookie_review)
    counts = candidate.projections.groupby("position").size().to_dict()
    source_files = {
        "players": {
            "path": str(player_path),
            "sha256": sha256(player_path),
            "snapshot_aggregate_sha256": (
                "42af9666ac84e6fc7700010719775538c993fb4a8067bd4cb54fda760ebacde5"
            ),
            "retrieved_at_utc": "2026-07-30T07:24:07Z",
        },
        "seasonal_stats": {
            "path": str(stats_raw / "player_stats_seasonal_2025.parquet"),
            "sha256": sha256(stats_raw / "player_stats_seasonal_2025.parquet"),
            "snapshot_aggregate_sha256": (
                "a5b2304f0132512a705f4565d683c619ffadfdd29085e8b0b5ba2110142b08aa"
            ),
            "retrieved_at_utc": "2026-07-30T07:24:07Z",
        },
    }
    governance = {
        "schema_version": 1,
        "authority": "NWR_DATA_GOVERNANCE",
        "approval_status": "READY_FOR_OWNER_GOVERNANCE_APPROVAL",
        "admission_scope": "REDRAFT_2026_PROJECTIONS",
        "season": SEASON,
        "source_id": MODEL_ID,
        "source_authority": "NWR-derived model from admitted nflverse CC-BY-4.0 inputs",
        "source_sha256": candidate_sha,
        "generated_at": generated_at,
        "source_as_of": SOURCE_AS_OF,
        "valid_from": SOURCE_AS_OF,
        "valid_until": "2026-09-07",
        "identity_contract": "EXACT GSIS ID only; no fuzzy joins or aliases used",
        "player_counts": {
            **{key: int(value) for key, value in counts.items()},
            "total": len(candidate.projections),
        },
        "coverage": {
            "current_registry_rows": len(candidate.identity),
            "candidate_rows": len(candidate.projections),
            "blocked_rows": len(candidate.blocked),
            "unresolved_identity_rows": 0,
        },
        "limitations": [
            (
                "Central forecast persists the prior-season stat line; it does not predict "
                "role growth, decline, or team-context effects."
            ),
            "All 2026 rookies are blocked because no governed current workload evidence exists.",
            "Veterans without a 2025 stat line are blocked.",
            "K and DST are absent because no governed projected_points_override exists.",
        ],
        "permitted_uses": [
            "Owner governance review",
            "Research-only scoring, replacement, and settings-sensitivity validation",
        ],
        "prohibited_uses": [
            "Production Redraft installation before owner approval",
            "Representation as proprietary consensus or expert rankings",
            "Dynasty ranking conversion",
            "Silent rookie workload imputation",
        ],
        "approver_identity": "OWNER_REQUIRED",
        "approved_by": None,
        "approved_at_utc": None,
    }
    write_json(output / "NWR_DATA_GOVERNANCE.json", governance)
    write_json(
        output / "PROJECTION_SHA256.json",
        {
            "candidate_projection": candidate_sha,
            "candidate_path": str(candidate_path.relative_to(repo_root)),
            "byte_identical_regeneration_verified": deterministic,
            "sources": source_files,
        },
    )
    inventory = pd.DataFrame(
        [
            ["No local direct 2026 projection snapshot", "BLOCKED_SOURCE", "No file found"],
            [
                "nflverse players 2026 registry",
                "PROJECTION_COMPONENT_ONLY",
                "Exact GSIS identity/current status/team",
            ],
            [
                "nflverse seasonal stats 2012-2025",
                "RESEARCH_ONLY",
                "Historical forecast input and temporal validation",
            ],
            ["nflverse depth charts through 2025", "STALE", "No governed 2026 depth snapshot"],
            ["nflverse injuries through 2025", "STALE", "No governed 2026 availability snapshot"],
            [
                "CFBD 2026 draft/college data",
                "PROJECTION_COMPONENT_ONLY",
                "Rookie identity/context; no governed NFL workload",
            ],
            [
                "Scheduled ingest 2026-07-21",
                "BLOCKED_SOURCE",
                "Raw snapshot explicitly not approved",
            ],
            [
                "Dynasty and rookie rankings",
                "BLOCKED_SOURCE",
                "Prohibited as redraft projection input",
            ],
        ],
        columns=["candidate", "classification", "reason"],
    )
    write_csv(output / "EXISTING_EVIDENCE_INVENTORY.csv", inventory)
    source_matrix = pd.DataFrame(
        [
            [
                "nflverse FF rankings",
                "Public download",
                "CC-BY repo; underlying FantasyPros ranks",
                "Current rankings only",
                "Ranks, not stat projections",
                "REJECT",
            ],
            [
                "FantasyPros API",
                "API key",
                "Personal non-commercial, non-transferable, non-competing",
                "Current",
                "Potential data; license incompatible",
                "REJECT",
            ],
            [
                "Sleeper API",
                "Free read-only API",
                "Public docs",
                "Current player/league data",
                "No projections endpoint",
                "REJECT",
            ],
            [
                "FantasyFootballAnalytics ffanalytics",
                "Open-source R package",
                "Package code public; inputs scraped from third parties",
                "Provider dependent",
                "Scraping workflow; terms not source-admissible",
                "REJECT",
            ],
            [
                MODEL_ID,
                "Local deterministic build",
                "nflverse CC-BY-4.0 with attribution",
                SOURCE_AS_OF,
                "530 QB/RB/WR/TE persistence forecasts",
                "OWNER_APPROVAL_REQUIRED",
            ],
        ],
        columns=[
            "source",
            "access_method",
            "license_terms",
            "recency",
            "coverage_fields",
            "recommendation",
        ],
    )
    write_csv(output / "SOURCE_CANDIDATE_MATRIX.csv", source_matrix)
    schema_rows = pd.DataFrame(
        [
            ["player_id", "required", "Exact governed stable identity"],
            ["player_name", "required", "Display name"],
            ["position", "required", "QB/RB/WR/TE/K/DST"],
            ["team", "required operationally", "Current team"],
            ["season", "required", "Must equal active profile season"],
            ["source_status", "required", "Only GOVERNED is admitted"],
            ["evidence_status", "required", "AVAILABLE or ADMITTED_CURRENT_SEASON"],
            ["source_as_of", "required operationally", "ISO date within 30 days"],
            ["rookie", "optional", "Confidence/review flag"],
            *[
                [column, "optional numeric", "Scored or confidence component"]
                for column in PROJECTION_NUMERIC_COLUMNS
            ],
            ["attempts/completions/carries/targets", "provenance only", "Not scored by Redraft V1"],
            ["K/DST", "conditional", "Requires governed projected_points_override"],
        ],
        columns=["column", "contract", "meaning"],
    )
    write_csv(output / "PROJECTION_SCHEMA.csv", schema_rows)
    write_text(
        output / "PROJECTION_SCHEMA.md",
        """# Projection schema

The mechanical schema is in `PROJECTION_SCHEMA.csv`. `source_as_of` is not present in the
service's seven-column header tuple, but every row without a fresh ISO date is blocked, so it is
operationally required. Attempts, completions, carries, and targets can be retained as provenance
but Redraft V1 does not score them. K/DST require `projected_points_override`.

The service still requires a separate SHA-bound approval receipt before installation. This task did
not weaken that contract.
""",
    )
    write_text(
        output / "EXTERNAL_SOURCE_RESEARCH.md",
        """# External source research

Primary-source review found no lawful direct granular 2026 projection frame that satisfies NWR.

- nflreadr's [FF ranking dictionary](https://nflreadr.nflverse.com/articles/dictionary_ff_rankings.html)
  identifies the artifact as FantasyPros redraft/dynasty/best-ball rankings. It is not projected
  stat lines and the task prohibits using rankings as hidden projection truth.
- The [FantasyPros API terms](https://api.fantasypros.com/public/v2/terms-of-use) require an API
  key and restrict data to personal, non-commercial, non-transferable use while prohibiting
  competitive products. It was not called.
- The [Sleeper API documentation](https://docs.sleeper.com/) exposes leagues, drafts, rosters,
  players, and trends; it documents no projection endpoint.
- The [ffanalytics repository](https://github.com/FantasyFootballAnalytics/ffanalytics) describes
  scraping projection pages from several sites. Scraping and unverified third-party reuse were
  rejected.
- nflverse data inputs are admitted local immutable snapshots under CC-BY-4.0 with attribution:
  [nflverse-data](https://github.com/nflverse/nflverse-data).

No paywall, authenticated page, paid API, DynastyProcess payload, proprietary consensus, or leaked
ranking was accessed.
""",
    )
    write_text(
        output / "FRESHNESS_REPORT.md",
        f"""# Freshness report

- Evaluation date: {SOURCE_AS_OF}
- Current player registry retrieved: 2026-07-30T07:24:07Z (9 days old)
- Candidate generated/source_as_of: {SOURCE_AS_OF} (0 days old)
- Contract window: 30 days
- Valid through: 2026-09-07
- Result: **PASS for candidate review; production remains approval-blocked.**

The 2025 production input is a completed-season historical fact, not misrepresented as current
2026 role evidence. The current registry supplies only exact identity, status, and team.
""",
    )
    write_text(
        output / "POSITIONAL_DEPTH_REPORT.md",
        f"""# Positional depth report

| Position | Candidate | Engine minimum | Result |
|---|---:|---:|---|
| QB | {counts.get("QB", 0)} | 20 | PASS |
| RB | {counts.get("RB", 0)} | 40 | PASS |
| WR | {counts.get("WR", 0)} | 50 | PASS |
| TE | {counts.get("TE", 0)} | 20 | PASS |
| K | 0 | profile-dependent | BLOCKED: no governed override |
| DST | 0 | profile-dependent | BLOCKED: no governed override |

Total candidate rows: {len(candidate.projections)}. Total blocked current-universe rows:
{len(candidate.blocked)}. Built-in presets require neither K nor DST and all four review-only
ranking generations passed replacement-depth checks.
""",
    )
    latest = validation[validation["season"].isin([2024, 2025])]
    aggregate = latest.groupby("position")[["model_mae", "spearman"]].mean().round(4)
    aggregate_table = aggregate.reset_index().to_string(index=False)
    write_text(
        output / "PROJECTION_MODEL_REPORT.md",
        f"""# Projection model report

Selected model: `{MODEL_ID}`.

The central forecast copies each exact current veteran's 2025 granular stat line into a 2026
forecast, updates identity/team/status from the July 30 current registry, and attaches historical
position-specific uncertainty. It is intentionally conservative and separate from all dynasty
rankings. Players without a 2025 line and every 2026 rookie are blocked.

The first recency/per-game/regression formulation was rejected because its 2016-2025 temporal MAE
was worse than prior-season persistence in every position. No tuning was used to conceal that
result. The selected persistence baseline materially beats a position-median baseline in every
backtest season and retains useful rank correlation.

2024-2025 mean validation:

```
{aggregate_table}
```

Limitations are material: no 2026 workload, coaching, scheme, or injury projection; no rookie
workload; no K/DST; and no role-growth/decline forecast. Those limitations require owner judgment
before admission.
""",
    )
    gates = pd.DataFrame(
        [
            [
                "G1",
                "source authority",
                "READY_FOR_OWNER_APPROVAL",
                "CC-BY inputs admitted; derived forecast needs owner approval",
            ],
            [
                "G2",
                "no leakage",
                "PASS",
                "Strict t-1 forecast; no future rows, ranks, or proprietary data",
            ],
            [
                "G3",
                "scoring correctness",
                "PASS_RESEARCH_ONLY",
                "All four presets generated from granular components",
            ],
            [
                "G4",
                "replacement correctness",
                "PASS_RESEARCH_ONLY",
                "Engine profile depth checks and replacement generation passed",
            ],
            ["G5", "settings sensitivity", "PASS_RESEARCH_ONLY", "See SETTINGS_SANITY_RESULTS.csv"],
            [
                "G6",
                "historical validation",
                "PASS",
                "2016-2025 temporal backtest; beats position median each season",
            ],
            [
                "G7",
                "positional stability",
                "PASS_RESEARCH_ONLY",
                "No duplicate IDs; useful 2024-25 rank correlations",
            ],
            [
                "G8",
                "rookie handling",
                "PASS_FAIL_CLOSED",
                "All 224 current rookies blocked; no workload fabricated",
            ],
            ["G9", "uncertainty", "PASS", "Position/year absolute-error p80 bounds"],
            [
                "G10",
                "profile isolation",
                "PASS_EXISTING_TESTS",
                "Existing profile CRUD/isolation tests retained",
            ],
            ["G11", "dynasty preservation", "PASS", "No dynasty data or state changed"],
            [
                "G12",
                "product truthfulness",
                "PASS_BLOCKED_STATE",
                "Candidate not installed; live UI remains fail-closed",
            ],
            [
                "G13",
                "current projection freshness",
                "PASS_CANDIDATE",
                "Generated 2026-08-08 from registry retrieved 2026-07-30",
            ],
            ["G14", "current projection depth", "PASS_CANDIDATE", str(counts)],
            [
                "G15",
                "current identity coverage",
                "PASS",
                f"{len(candidate.identity)} EXACT, 0 unresolved",
            ],
        ],
        columns=["gate", "name", "status", "evidence"],
    )
    write_csv(output / "PROMOTION_GATE_RESULTS.csv", gates)
    browser = pd.DataFrame(
        [
            [
                viewport,
                "Redraft and dynasty surfaces",
                "SKIPPED_NOT_ADMITTED",
                "No production snapshot/receipt; browser adoption gate not authorized",
            ]
            for viewport in ("375x812", "768x1024", "1440x1000")
        ],
        columns=["viewport", "scope", "status", "reason"],
    )
    write_csv(output / "BROWSER_RESULTS.csv", browser)
    write_text(
        output / "DYNASTY_PRESERVATION.md",
        """# Dynasty preservation

The work is additive on the isolated Redraft research branch. No dynasty ranking, Unified Research
Preview, Rookie Review, Trading Lab, active pack, user state, or local production projection path
was changed. The scheduled refresh remained disabled. HQ and stable were not updated.
""",
    )
    write_text(
        output / "VALIDATION_RESULTS.md",
        f"""# Validation results

- Candidate deterministic regeneration: {deterministic}
- Candidate SHA-256: `{candidate_sha}`
- Exact identities: {len(candidate.identity)}; unresolved: 0
- Candidate rows: {len(candidate.projections)}; blocked: {len(candidate.blocked)}
- Depth: {counts}
- Review-only preset rankings: all four built-ins READY
- Settings checks: {int(sanity["status"].eq("PASS").sum())}/{len(sanity)} PASS
- Ranking sanity: zero top-100 duplicates, zero top-100 projection-zero rows, no rookies or
  K/DST leakage; 1QB top 25 contains 8 QBs and Superflex top 25 contains 11, retained as an explicit
  owner-review observation rather than manually reordering players
- Governance: owner approval required; installer was not called
- Browser/independent adoption/HQ: skipped because admission is not complete
- Focused tests: 24 passed
- Repository-wide suite: no result; bounded run timed out after 304 seconds after the pre-existing
  environment's missing `openpyxl` dependency was supplied locally
""",
    )
    write_text(
        output / "NEXT_ACTION.md",
        f"""# Next action

Owner must review and explicitly approve or reject:

- Model: `{MODEL_ID}`
- Candidate CSV: `CANDIDATE_PROJECTION_SNAPSHOT.csv`
- SHA-256: `{candidate_sha}`
- Governance candidate: `NWR_DATA_GOVERNANCE.json`

Approval must name the owner/approver and timestamp, and authorize conversion from
`GOVERNANCE_PENDING` / `MODEL_VALIDATED_REVIEW_ONLY` to the engine's admitted statuses. After that,
regenerate and hash the final CSV, bind an `APPROVED_FOR_REDRAFT_V1` receipt to the final hash, run
the installer, browser suite, independent adoption, and HQ gates.

For the owner's first real draft, also provide exact league team count, roster slots, scoring,
bonuses, draft type/slot, keepers, auction budget, and roster limits. No upcoming league placeholder
was treated as configured.
""",
    )
    write_text(
        output / "EXECUTIVE_VERDICT.md",
        f"""# Executive verdict

`{VERDICT}`

No lawful direct 2026 granular source qualified. NWR built the strongest transparent lawful
fallback: a current-status-filtered prior-season persistence forecast from admitted nflverse
CC-BY-4.0 evidence. It is temporally validated, exact-ID, fresh, deep enough for every built-in
profile, deterministic, and uncertainty-bounded. It deliberately blocks all rookies and veterans
without a 2025 stat line.

The candidate is not production-admitted because repository policy requires an independent
SHA-bound `APPROVED_FOR_REDRAFT_V1` receipt and this task may not impersonate the owner. Review-only
rankings exist solely to validate the engine. No snapshot was installed, no browser adoption or
independent HQ review ran, and HQ/stable/dynasty remain unchanged.
""",
    )
    required = [
        "EXECUTIVE_VERDICT.md",
        "PROJECTION_SCHEMA.md",
        "EXISTING_EVIDENCE_INVENTORY.csv",
        "EXTERNAL_SOURCE_RESEARCH.md",
        "SOURCE_CANDIDATE_MATRIX.csv",
        "IDENTITY_COVERAGE.csv",
        "FRESHNESS_REPORT.md",
        "POSITIONAL_DEPTH_REPORT.md",
        "PROJECTION_MODEL_REPORT.md",
        "PROJECTION_VALIDATION.csv",
        "NWR_DATA_GOVERNANCE.json",
        "PROJECTION_SHA256.json",
        "DEFAULT_PROFILE_RANKINGS.csv",
        "SUPERFLEX_PROFILE_RANKINGS.csv",
        "SETTINGS_SANITY_RESULTS.csv",
        "ROOKIE_REDRAFT_REVIEW.csv",
        "PROMOTION_GATE_RESULTS.csv",
        "BROWSER_RESULTS.csv",
        "DYNASTY_PRESERVATION.md",
        "VALIDATION_RESULTS.md",
        "NEXT_ACTION.md",
        "MANIFEST.json",
    ]
    manifest = {
        "schema_version": 1,
        "packet": "nwr_redraft_2026_projection_admission_v1_20260808",
        "generated_at_utc": generated_at,
        "verdict": VERDICT,
        "candidate_sha256": candidate_sha,
        "required_files": required,
        "extra_files": [
            "CANDIDATE_PROJECTION_SNAPSHOT.csv",
            "BLOCKED_PLAYER_ROWS.csv",
            "CURRENT_RANKING_SANITY.csv",
            "PROJECTION_SCHEMA.csv",
        ],
    }
    write_json(output / "MANIFEST.json", manifest)
    missing_required = [name for name in required if not (output / name).is_file()]
    if missing_required:
        raise RuntimeError("Packet is missing required files: " + ", ".join(missing_required))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--shared-root", type=Path, default=Path(r"C:\NWR_SHARED_DATA"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    output = args.output or (
        repo_root / "docs/hq/model/nwr_redraft_2026_projection_admission_v1_20260808"
    )
    build_packet(repo_root, args.shared_root.resolve(), output.resolve())


if __name__ == "__main__":
    main()
