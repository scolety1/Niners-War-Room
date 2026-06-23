"""Build sanitized DynastyProcess market context for NWR review.

This script fetches raw DynastyProcess CSVs into an ignored cache and writes
repo-safe derived review artifacts. DynastyProcess values are display-only
market context and must not drive NWR rank/model code without later approval.
"""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.connectors.dynastyprocess_connector import (
    DEFAULT_CACHE_ROOT,
    DEFAULT_FILE_NAMES,
    DynastyProcessConnector,
    validate_schema,
)

DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "dynastyprocess_market_baseline_20260622"
)
FULL_DYNASTY_PATH = (
    REPO_ROOT
    / "local_exports"
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.csv"
)
FROZEN_BOARD_PATH = (
    REPO_ROOT
    / "docs"
    / "draft_day_exports"
    / "final_board_v1_20260622"
    / "FINAL_DRAFT_BOARD_V1_FROZEN.csv"
)
PDF_POOL_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_accuracy_max_20260622"
    / "free_agent_pdf_page3_draftable_pool.csv"
)
CANDIDATE_OVERLAY_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_accuracy_max_20260622"
    / "tuned_v2_current_draft_pool_overlay.csv"
)
ROOKIE_AGE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "age_source_audit_20260622"
    / "rookie_verified_age_display_20260622.csv"
)
DISPLAY_ONLY_WARNING = (
    "Display-only DynastyProcess market baseline; not NWR source truth; "
    "not used for model inputs, candidate rank, or hidden sort."
)


@dataclass
class NwrPlayer:
    nwr_player_id: str = ""
    nwr_name: str = ""
    nwr_pos: str = ""
    nwr_team: str = ""
    nwr_age: str = ""
    nwr_final_board_rank: str = ""
    nwr_dynasty_rank: str = ""
    nwr_candidate_rank: str = ""
    source_membership: set[str] = field(default_factory=set)


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def normalize_name(value: str) -> str:
    """Normalize names for conservative player matching."""

    text = value.casefold().strip()
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?$", "", text).strip()
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def _clean_id(value: object) -> str:
    text = str(value or "").strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _rank(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _upsert_player(players: dict[tuple[str, str], NwrPlayer], key: tuple[str, str]) -> NwrPlayer:
    player = players.get(key)
    if player is None:
        player = NwrPlayer()
        players[key] = player
    return player


def _apply_common(
    player: NwrPlayer,
    *,
    name: str,
    pos: str,
    source: str,
    player_id: str = "",
    team: str = "",
    age: str = "",
) -> None:
    if name and not player.nwr_name:
        player.nwr_name = name
    if pos and not player.nwr_pos:
        player.nwr_pos = pos
    if team and not player.nwr_team:
        player.nwr_team = team
    if age and not player.nwr_age:
        player.nwr_age = age
    if player_id and not player.nwr_player_id:
        player.nwr_player_id = player_id
    player.source_membership.add(source)


def load_nwr_universe() -> tuple[pd.DataFrame, dict[str, int]]:
    """Load NWR review player universe without mutating source truth."""

    players: dict[tuple[str, str], NwrPlayer] = {}
    counts: dict[str, int] = {}

    full = _read_csv(FULL_DYNASTY_PATH)
    counts["full_dynasty_rankings"] = len(full)
    for row in full.to_dict("records"):
        name = row.get("player_name", "")
        pos = row.get("position", "")
        key = (_clean_id(row.get("player_id")) or normalize_name(name), pos)
        player = _upsert_player(players, key)
        _apply_common(
            player,
            name=name,
            pos=pos,
            source="full_dynasty_rankings",
            player_id=_clean_id(row.get("player_id")),
            team=row.get("nfl_team", ""),
            age=row.get("age", ""),
        )
        player.nwr_dynasty_rank = row.get("nwr_rank", "") or player.nwr_dynasty_rank

    frozen = _read_csv(FROZEN_BOARD_PATH)
    counts["frozen_board_66"] = len(frozen)
    for row in frozen.to_dict("records"):
        name = row.get("player", "")
        pos = row.get("position", "")
        key = (normalize_name(name), pos)
        player = _upsert_player(players, key)
        _apply_common(
            player,
            name=name,
            pos=pos,
            source="frozen_board_66",
            team=row.get("nfl_team", ""),
        )
        player.nwr_final_board_rank = (
            row.get("final_board_rank", "") or player.nwr_final_board_rank
        )

    pdf_pool = _read_csv(PDF_POOL_PATH)
    counts["pdf_free_agent_pool"] = len(pdf_pool)
    for row in pdf_pool.to_dict("records"):
        name = row.get("player", "")
        pos = row.get("pos", "")
        key = (_clean_id(row.get("player_id")) or normalize_name(name), pos)
        player = _upsert_player(players, key)
        _apply_common(
            player,
            name=name,
            pos=pos,
            source="pdf_free_agent_pool",
            player_id=_clean_id(row.get("player_id")),
            team=row.get("nfl_team", ""),
            age=row.get("age", ""),
        )
        if row.get("matched_full_dynasty_rank"):
            player.nwr_dynasty_rank = (
                row.get("matched_full_dynasty_rank") or player.nwr_dynasty_rank
            )

    candidates = _read_csv(CANDIDATE_OVERLAY_PATH)
    counts["current_candidate_overlay"] = len(candidates)
    for row in candidates.to_dict("records"):
        name = row.get("player", "")
        pos = row.get("pos", "")
        key = (_clean_id(row.get("player_id")) or normalize_name(name), pos)
        player = _upsert_player(players, key)
        _apply_common(
            player,
            name=name,
            pos=pos,
            source="current_candidate_overlay",
            player_id=_clean_id(row.get("player_id")),
            team=row.get("nfl_team", ""),
        )
        player.nwr_candidate_rank = (
            row.get("tuned_v2_cross_asset_rank")
            or row.get("current_candidate_rank", "")
            or player.nwr_candidate_rank
        )
        player.nwr_final_board_rank = (
            row.get("final_board_rank", "") or player.nwr_final_board_rank
        )

    if ROOKIE_AGE_PATH.exists():
        rookie_ages = _read_csv(ROOKIE_AGE_PATH)
        counts["verified_rookie_age_context"] = len(rookie_ages)
        for row in rookie_ages.to_dict("records"):
            name = row.get("player", "")
            pos = row.get("position", "")
            key = (normalize_name(name), pos)
            player = players.get(key)
            if player and row.get("age") and not player.nwr_age:
                player.nwr_age = row["age"]

    records = []
    for player in players.values():
        records.append(
            {
                "nwr_player_id": player.nwr_player_id,
                "nwr_name": player.nwr_name,
                "nwr_pos": player.nwr_pos,
                "nwr_team": player.nwr_team,
                "nwr_age": player.nwr_age,
                "nwr_final_board_rank": player.nwr_final_board_rank,
                "nwr_dynasty_rank": player.nwr_dynasty_rank,
                "nwr_candidate_rank": player.nwr_candidate_rank,
                "source_membership": ";".join(sorted(player.source_membership)),
                "name_pos_key": normalize_name(player.nwr_name) + "|" + player.nwr_pos,
                "exact_name_pos_key": player.nwr_name.casefold().strip() + "|" + player.nwr_pos,
            }
        )
    return pd.DataFrame(records), counts


def load_dp_players(snapshot_dir: Path) -> pd.DataFrame:
    values = _read_csv(snapshot_dir / "values-players.csv")
    playerids = _read_csv(snapshot_dir / "db_playerids.csv")
    validate_schema(values.columns, "values-players.csv")
    validate_schema(playerids.columns, "db_playerids.csv")
    values["fp_id_join"] = values["fp_id"].map(_clean_id)
    playerids["fp_id_join"] = playerids["fantasypros_id"].map(_clean_id)
    playerids_subset = playerids[
        [
            "fp_id_join",
            "fantasypros_id",
            "sleeper_id",
            "gsis_id",
            "name",
            "merge_name",
            "position",
            "team",
            "birthdate",
            "age",
            "draft_year",
        ]
    ].rename(
        columns={
            "name": "dp_id_name",
            "position": "dp_id_pos",
            "team": "dp_id_team",
            "age": "dp_id_age",
            "draft_year": "dp_id_draft_year",
        }
    )
    merged = values.merge(playerids_subset, on="fp_id_join", how="left")
    merged["sleeper_id"] = merged["sleeper_id"].map(_clean_id)
    merged["gsis_id"] = merged["gsis_id"].map(_clean_id)
    merged["fp_id"] = merged["fp_id"].map(_clean_id)
    merged["dp_market_rank_1qb"] = merged["ecr_1qb"]
    merged["dp_value_1qb"] = merged["value_1qb"]
    merged["name_pos_key"] = merged.apply(
        lambda row: normalize_name(row["player"]) + "|" + row["pos"], axis=1
    )
    merged["exact_name_pos_key"] = merged.apply(
        lambda row: row["player"].casefold().strip() + "|" + row["pos"], axis=1
    )
    return merged


def _nwr_rank_basis(row: pd.Series) -> float | None:
    for column in ("nwr_candidate_rank", "nwr_final_board_rank", "nwr_dynasty_rank"):
        value = _rank(row.get(column))
        if value is not None:
            return value
    return None


def _market_flag(nwr_rank: float | None, dp_rank: float | None, matched: bool) -> str:
    if not matched or dp_rank is None:
        return "no DP match"
    if nwr_rank is None:
        return "aligned"
    gap = nwr_rank - dp_rank
    if gap <= -20:
        return "NWR much higher than market"
    if gap >= 20:
        return "NWR much lower than market"
    return "aligned"


def join_dp_to_nwr(dp_players: pd.DataFrame, nwr: pd.DataFrame) -> pd.DataFrame:
    id_lookup: dict[str, dict[str, str]] = {}
    for record in nwr.to_dict("records"):
        nwr_id = _clean_id(record.get("nwr_player_id"))
        if nwr_id:
            id_lookup[nwr_id] = record

    exact_lookup = {
        record["exact_name_pos_key"]: record for record in nwr.to_dict("records")
    }
    normalized_lookup = {
        record["name_pos_key"]: record for record in nwr.to_dict("records")
    }

    output_records = []
    for row in dp_players.to_dict("records"):
        match: dict[str, str] | None = None
        method = "unmatched"
        confidence = "none"
        for dp_id_field in ("sleeper_id", "gsis_id", "fp_id"):
            dp_id = _clean_id(row.get(dp_id_field))
            if dp_id and dp_id in id_lookup:
                match = id_lookup[dp_id]
                method = dp_id_field
                confidence = "high"
                break
        if match is None and row["exact_name_pos_key"] in exact_lookup:
            match = exact_lookup[row["exact_name_pos_key"]]
            method = "exact_name_position"
            confidence = "medium"
        if match is None and row["name_pos_key"] in normalized_lookup:
            match = normalized_lookup[row["name_pos_key"]]
            method = "normalized_name_position"
            confidence = "review"

        matched = match is not None
        nwr_rank = _nwr_rank_basis(pd.Series(match or {}))
        dp_rank = _rank(row.get("dp_market_rank_1qb"))
        nwr_vs_dp_gap = ""
        if nwr_rank is not None and dp_rank is not None:
            nwr_vs_dp_gap = round(nwr_rank - dp_rank, 2)
        output_records.append(
            {
                "player": row.get("player", ""),
                "pos": row.get("pos", ""),
                "team": row.get("team", ""),
                "age": row.get("age", "") or row.get("dp_id_age", ""),
                "draft_year": row.get("draft_year", "") or row.get("dp_id_draft_year", ""),
                "ecr_1qb": row.get("ecr_1qb", ""),
                "ecr_pos": row.get("ecr_pos", ""),
                "value_1qb": row.get("value_1qb", ""),
                "scrape_date": row.get("scrape_date", ""),
                "fp_id": row.get("fp_id", ""),
                "sleeper_id": row.get("sleeper_id", ""),
                "nwr_player_id": (match or {}).get("nwr_player_id", ""),
                "nwr_name": (match or {}).get("nwr_name", ""),
                "nwr_pos": (match or {}).get("nwr_pos", ""),
                "nwr_final_board_rank": (match or {}).get("nwr_final_board_rank", ""),
                "nwr_dynasty_rank": (match or {}).get("nwr_dynasty_rank", ""),
                "nwr_candidate_rank": (match or {}).get("nwr_candidate_rank", ""),
                "dp_market_rank_1qb": row.get("dp_market_rank_1qb", ""),
                "dp_value_1qb": row.get("dp_value_1qb", ""),
                "nwr_vs_dp_gap": nwr_vs_dp_gap,
                "market_sanity_flag": _market_flag(nwr_rank, dp_rank, matched),
                "join_method": method,
                "join_confidence": confidence,
                "source_note": "DynastyProcess public data, GPL-3.0.",
                "dp_display_only_warning": DISPLAY_ONLY_WARNING,
            }
        )
    joined = pd.DataFrame(output_records)
    joined["_matched_sort"] = joined["nwr_name"].astype(bool)
    joined = joined.sort_values(
        by=["_matched_sort", "nwr_candidate_rank", "nwr_final_board_rank", "ecr_1qb"],
        ascending=[False, True, True, True],
        na_position="last",
    ).drop(columns=["_matched_sort"])
    return joined


def build_pick_context(snapshot_dir: Path) -> pd.DataFrame:
    picks = _read_csv(snapshot_dir / "values-picks.csv")
    validate_schema(picks.columns, "values-picks.csv")
    values = _read_csv(snapshot_dir / "values.csv")
    validate_schema(values.columns, "values.csv")
    pick_values = values[values["pos"].eq("PICK")][["player", "value_1qb"]].rename(
        columns={"value_1qb": "value_1qb_from_values_csv"}
    )
    picks = picks.merge(pick_values, on="player", how="left")
    picks["pick_label"] = picks["player"].str.replace(" Pick ", " ", regex=False)
    picks["value_1qb"] = picks["value_1qb_from_values_csv"]
    picks["source_note"] = (
        "DynastyProcess pick context; display-only sanity layer; not a model input."
    )
    return picks[
        ["pick_label", "value_1qb", "ecr_1qb", "scrape_date", "source_note"]
    ].sort_values(["pick_label"])


def _coverage_row(source_name: str, nwr: pd.DataFrame, joined: pd.DataFrame) -> dict[str, object]:
    source_mask = nwr["source_membership"].str.contains(source_name, regex=False)
    source_nwr = nwr[source_mask]
    source_names = set(source_nwr["name_pos_key"])
    matched = joined[joined["nwr_name"].astype(bool)]
    matched_source = matched[
        matched.apply(
            lambda row: normalize_name(row["nwr_name"]) + "|" + row["nwr_pos"] in source_names,
            axis=1,
        )
    ]
    dp_age = matched_source["age"].astype(str).str.strip().ne("").sum()
    nwr_age = source_nwr["nwr_age"].astype(str).str.strip().ne("").sum()
    total = len(source_nwr)
    matched_count = len(matched_source.drop_duplicates(["nwr_name", "nwr_pos"]))
    return {
        "source_name": source_name,
        "nwr_rows": total,
        "dp_matched_rows": matched_count,
        "dp_match_rate": round(matched_count / total, 4) if total else 0,
        "nwr_age_rows_before_dp": int(nwr_age),
        "dp_age_rows_when_matched": int(dp_age),
        "age_gain_possible_rows": int(max(dp_age - nwr_age, 0)),
        "notes": DISPLAY_ONLY_WARNING,
    }


def build_coverage(nwr: pd.DataFrame, joined: pd.DataFrame, counts: dict[str, int]) -> pd.DataFrame:
    rows = [
        _coverage_row(source_name, nwr, joined)
        for source_name in (
            "full_dynasty_rankings",
            "frozen_board_66",
            "pdf_free_agent_pool",
            "current_candidate_overlay",
        )
    ]
    rows.append(
        {
            "source_name": "combined_nwr_universe",
            "nwr_rows": len(nwr),
            "dp_matched_rows": int(joined["nwr_name"].astype(bool).sum()),
            "dp_match_rate": round(
                joined["nwr_name"].astype(bool).sum() / len(nwr), 4
            )
            if len(nwr)
            else 0,
            "nwr_age_rows_before_dp": int(nwr["nwr_age"].astype(str).str.strip().ne("").sum()),
            "dp_age_rows_when_matched": int(
                joined.loc[joined["nwr_name"].astype(bool), "age"]
                .astype(str)
                .str.strip()
                .ne("")
                .sum()
            ),
            "age_gain_possible_rows": "",
            "notes": f"Input counts: {counts}. {DISPLAY_ONLY_WARNING}",
        }
    )
    return pd.DataFrame(rows)


def build_crosswalk_audit(joined: pd.DataFrame) -> pd.DataFrame:
    matched = joined[joined["nwr_name"].astype(bool)].copy()
    columns = [
        "player",
        "pos",
        "team",
        "fp_id",
        "sleeper_id",
        "nwr_player_id",
        "nwr_name",
        "nwr_pos",
        "join_method",
        "join_confidence",
        "source_note",
        "dp_display_only_warning",
    ]
    return matched[columns].drop_duplicates()


def write_outputs(snapshot_dir: Path, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    nwr, counts = load_nwr_universe()
    dp_players = load_dp_players(snapshot_dir)
    joined = join_dp_to_nwr(dp_players, nwr)
    matched_context = joined[
        joined["nwr_name"].astype(bool)
        | joined["player"].isin(
            [
                "Jeremiyah Love",
                "Zay Flowers",
                "Chris Olave",
                "Jameson Williams",
                "Drake Maye",
                "Brian Thomas Jr.",
                "Jaylen Warren",
                "Rashee Rice",
                "Brock Purdy",
                "Dak Prescott",
                "Tyreek Hill",
                "Dallas Goedert",
            ]
        )
    ].copy()
    paths = {
        "market": output_dir / "dp_market_baseline_context.csv",
        "picks": output_dir / "dp_pick_value_context.csv",
        "crosswalk": output_dir / "dp_playerid_crosswalk_audit.csv",
        "coverage": output_dir / "dp_nwr_join_coverage.csv",
    }
    matched_context.to_csv(paths["market"], index=False)
    build_pick_context(snapshot_dir).to_csv(paths["picks"], index=False)
    build_crosswalk_audit(joined).to_csv(paths["crosswalk"], index=False)
    build_coverage(nwr, joined, counts).to_csv(paths["coverage"], index=False)
    return paths


def run(
    *,
    cache_root: Path = DEFAULT_CACHE_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    snapshot_label: str | None = None,
    snapshot_dir: Path | None = None,
) -> tuple[Path, dict[str, Path]]:
    if snapshot_dir is None:
        connector = DynastyProcessConnector(cache_root=cache_root)
        result = connector.fetch_snapshot(
            file_names=DEFAULT_FILE_NAMES,
            snapshot_label=snapshot_label,
        )
        snapshot_dir = Path(result.snapshot_dir)
    paths = write_outputs(snapshot_dir=snapshot_dir, output_dir=output_dir)
    return snapshot_dir, paths


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--snapshot-label", default=None)
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    snapshot_dir, paths = run(
        cache_root=args.cache_root,
        output_dir=args.output_dir,
        snapshot_label=args.snapshot_label,
        snapshot_dir=args.snapshot_dir,
    )
    print(f"DynastyProcess raw cache: {snapshot_dir}")
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
