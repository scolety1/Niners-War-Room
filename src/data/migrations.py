from __future__ import annotations

import sqlite3

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS players (
        player_id TEXT PRIMARY KEY,
        player_name TEXT NOT NULL,
        merge_name TEXT,
        position TEXT,
        nfl_team TEXT,
        birth_date TEXT,
        rookie_year INTEGER,
        height_in INTEGER,
        weight_lb INTEGER,
        sleeper_id TEXT,
        fantasypros_id TEXT,
        ktc_id TEXT,
        fantasycalc_id TEXT,
        pfr_id TEXT,
        cfb_id TEXT,
        active_flag INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS teams (
        team_id TEXT PRIMARY KEY,
        team_name TEXT NOT NULL UNIQUE,
        owner_name TEXT,
        active_flag INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS owners (
        owner_id TEXT PRIMARY KEY,
        owner_name TEXT NOT NULL,
        team_id TEXT,
        FOREIGN KEY (team_id) REFERENCES teams(team_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rosters (
        roster_id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT NOT NULL,
        season INTEGER NOT NULL,
        league_id TEXT,
        team_id TEXT NOT NULL,
        team_name TEXT,
        owner_name TEXT,
        player_id TEXT,
        player_name TEXT,
        position TEXT,
        nfl_team TEXT,
        roster_status TEXT,
        official_rank INTEGER,
        source TEXT,
        FOREIGN KEY (team_id) REFERENCES teams(team_id),
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS official_rankings (
        ranking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT NOT NULL,
        season INTEGER NOT NULL,
        source TEXT,
        rank_source_name TEXT,
        rank_source_date TEXT,
        player_id TEXT,
        player_name TEXT,
        position TEXT,
        nfl_team TEXT,
        official_rank INTEGER,
        rank_tier TEXT,
        is_rank_placeholder INTEGER DEFAULT 0,
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS future_picks (
        future_pick_id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT NOT NULL,
        season INTEGER NOT NULL,
        pick_year INTEGER NOT NULL,
        round INTEGER NOT NULL,
        slot INTEGER,
        pick_label TEXT NOT NULL,
        overall_pick INTEGER,
        original_team_id TEXT,
        original_team_name TEXT,
        current_team_id TEXT,
        current_team_name TEXT,
        current_owner_name TEXT,
        certainty TEXT,
        source TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pick_values (
        pick_value_id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT NOT NULL,
        pick_year INTEGER NOT NULL,
        pick_label TEXT NOT NULL,
        round INTEGER NOT NULL,
        slot INTEGER NOT NULL,
        overall_pick INTEGER NOT NULL,
        base_value_1000 REAL NOT NULL,
        future_discount REAL DEFAULT 1.0,
        certainty_adjustment REAL DEFAULT 1.0,
        declaration_adjustment REAL DEFAULT 0.0,
        final_pick_value REAL NOT NULL,
        bucket TEXT,
        source TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS market_values (
        market_value_id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT NOT NULL,
        source TEXT,
        player_id TEXT,
        player_name TEXT,
        position TEXT,
        market_rank INTEGER,
        market_value REAL,
        adp_overall REAL,
        adp_position REAL,
        trend TEXT,
        format TEXT,
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS player_features (
        feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT NOT NULL,
        player_id TEXT,
        player_name TEXT,
        position TEXT,
        draft_pick INTEGER,
        draft_cap_value REAL,
        opportunity_score REAL,
        production_score REAL,
        receiving_score REAL,
        elusiveness_score REAL,
        age_adj_production REAL,
        target_earning_efficiency REAL,
        breakout_score REAL,
        film_separation_score REAL,
        athleticism_score REAL,
        size_durability_score REAL,
        environment_score REAL,
        risk_flags TEXT,
        upside_flags TEXT,
        data_completeness REAL,
        source TEXT,
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS model_outputs (
        output_id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT NOT NULL,
        player_id TEXT,
        player_name TEXT,
        position TEXT,
        private_score REAL,
        market_score REAL,
        war_score REAL,
        keeper_score REAL,
        drop_candidate_score REAL,
        smash_prob REAL,
        hit_prob REAL,
        useful_prob REAL,
        replaceable_prob REAL,
        miss_prob REAL,
        bust_prob REAL,
        pick_adjusted_value REAL,
        confidence_score REAL,
        risk_level TEXT,
        recommendation TEXT,
        do_not_draft_before_pick TEXT,
        notes TEXT,
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS owner_notes (
        note_id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id TEXT,
        owner_name TEXT,
        team_id TEXT,
        team_name TEXT,
        note_date TEXT,
        category TEXT,
        note_text TEXT,
        confidence TEXT,
        source TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS metadata_sources (
        metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT NOT NULL,
        data_pack_name TEXT NOT NULL,
        file_name TEXT NOT NULL,
        source_name TEXT,
        source_type TEXT,
        source_url_or_description TEXT,
        pulled_at TEXT,
        imported_at TEXT,
        review_status TEXT,
        notes TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS import_errors (
        import_error_id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT,
        data_pack_name TEXT,
        severity TEXT NOT NULL,
        file_name TEXT,
        row_number INTEGER,
        entity_type TEXT,
        entity_name TEXT,
        issue TEXT NOT NULL,
        suggested_fix TEXT,
        status TEXT DEFAULT 'open',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
)

INDEX_STATEMENTS: tuple[str, ...] = (
    "CREATE INDEX IF NOT EXISTS idx_players_player_id ON players(player_id)",
    "CREATE INDEX IF NOT EXISTS idx_players_merge_name ON players(merge_name)",
    "CREATE INDEX IF NOT EXISTS idx_rosters_team_id ON rosters(team_id)",
    "CREATE INDEX IF NOT EXISTS idx_rosters_player_id ON rosters(player_id)",
    "CREATE INDEX IF NOT EXISTS idx_rosters_snapshot_date ON rosters(snapshot_date)",
    "CREATE INDEX IF NOT EXISTS idx_official_rankings_player_id ON official_rankings(player_id)",
    "CREATE INDEX IF NOT EXISTS idx_official_rankings_rank ON official_rankings(official_rank)",
    "CREATE INDEX IF NOT EXISTS idx_future_picks_current_team ON future_picks(current_team_id)",
    (
        "CREATE INDEX IF NOT EXISTS idx_future_picks_year_round_slot "
        "ON future_picks(pick_year, round, slot)"
    ),
    "CREATE INDEX IF NOT EXISTS idx_pick_values_pick_label ON pick_values(pick_label)",
    "CREATE INDEX IF NOT EXISTS idx_model_outputs_player_id ON model_outputs(player_id)",
)


def initialize_database(connection: sqlite3.Connection) -> None:
    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
    for statement in INDEX_STATEMENTS:
        connection.execute(statement)
