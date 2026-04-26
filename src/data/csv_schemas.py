from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CsvSchema:
    table_name: str
    required_columns: tuple[str, ...]
    optional_columns: tuple[str, ...] = ()
    integer_columns: tuple[str, ...] = ()
    float_columns: tuple[str, ...] = ()

    @property
    def all_columns(self) -> tuple[str, ...]:
        return (*self.required_columns, *self.optional_columns)


REQUIRED_V1_FILES = (
    "dim_players.csv",
    "fact_rosters.csv",
    "fact_official_rankings.csv",
    "fact_future_picks.csv",
    "fact_pick_values.csv",
    "model_outputs.csv",
    "metadata_sources.csv",
)

CSV_SCHEMAS: dict[str, CsvSchema] = {
    "dim_players.csv": CsvSchema(
        table_name="players",
        required_columns=("player_id", "player_name"),
        optional_columns=(
            "merge_name",
            "position",
            "nfl_team",
            "birth_date",
            "rookie_year",
            "height_in",
            "weight_lb",
            "sleeper_id",
            "fantasypros_id",
            "ktc_id",
            "fantasycalc_id",
            "pfr_id",
            "cfb_id",
            "active_flag",
            "created_at",
            "updated_at",
        ),
        integer_columns=("rookie_year", "height_in", "weight_lb", "active_flag"),
    ),
    "fact_rosters.csv": CsvSchema(
        table_name="rosters",
        required_columns=("snapshot_date", "season", "team_id", "team_name", "player_id"),
        optional_columns=(
            "league_id",
            "owner_name",
            "player_name",
            "position",
            "nfl_team",
            "roster_status",
            "official_rank",
            "source",
        ),
        integer_columns=("season", "official_rank"),
    ),
    "fact_official_rankings.csv": CsvSchema(
        table_name="official_rankings",
        required_columns=("snapshot_date", "season", "player_id"),
        optional_columns=(
            "source",
            "rank_source_name",
            "rank_source_date",
            "player_name",
            "position",
            "nfl_team",
            "official_rank",
            "rank_tier",
            "is_rank_placeholder",
        ),
        integer_columns=("season", "official_rank", "is_rank_placeholder"),
    ),
    "fact_future_picks.csv": CsvSchema(
        table_name="future_picks",
        required_columns=("snapshot_date", "season", "pick_year", "round", "pick_label"),
        optional_columns=(
            "slot",
            "overall_pick",
            "original_team_id",
            "original_team_name",
            "current_team_id",
            "current_team_name",
            "current_owner_name",
            "certainty",
            "source",
        ),
        integer_columns=("season", "pick_year", "round", "slot", "overall_pick"),
    ),
    "fact_pick_values.csv": CsvSchema(
        table_name="pick_values",
        required_columns=(
            "snapshot_date",
            "pick_year",
            "pick_label",
            "round",
            "slot",
            "overall_pick",
            "base_value_1000",
            "final_pick_value",
        ),
        optional_columns=(
            "future_discount",
            "certainty_adjustment",
            "declaration_adjustment",
            "bucket",
            "source",
        ),
        integer_columns=("pick_year", "round", "slot", "overall_pick"),
        float_columns=(
            "base_value_1000",
            "future_discount",
            "certainty_adjustment",
            "declaration_adjustment",
            "final_pick_value",
        ),
    ),
    "model_outputs.csv": CsvSchema(
        table_name="model_outputs",
        required_columns=("snapshot_date", "player_id", "player_name"),
        optional_columns=(
            "position",
            "private_score",
            "market_score",
            "war_score",
            "keeper_score",
            "drop_candidate_score",
            "smash_prob",
            "hit_prob",
            "useful_prob",
            "replaceable_prob",
            "miss_prob",
            "bust_prob",
            "pick_adjusted_value",
            "confidence_score",
            "risk_level",
            "recommendation",
            "do_not_draft_before_pick",
            "notes",
        ),
        float_columns=(
            "private_score",
            "market_score",
            "war_score",
            "keeper_score",
            "drop_candidate_score",
            "smash_prob",
            "hit_prob",
            "useful_prob",
            "replaceable_prob",
            "miss_prob",
            "bust_prob",
            "pick_adjusted_value",
            "confidence_score",
        ),
    ),
    "metadata_sources.csv": CsvSchema(
        table_name="metadata_sources",
        required_columns=("snapshot_date", "data_pack_name", "file_name"),
        optional_columns=(
            "source_name",
            "source_type",
            "source_url_or_description",
            "pulled_at",
            "imported_at",
            "review_status",
            "notes",
        ),
    ),
}
