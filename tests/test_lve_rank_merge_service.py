from __future__ import annotations

import csv

from src.services.lve_rank_merge_service import (
    PDF_FREE_AGENT_SOURCE,
    RANK_PROVENANCE,
    merge_lve_roster_ranks,
    merge_rank_rows,
    parse_lve_rank_text,
)


def test_parse_lve_rank_text_matches_pdf_columns_to_sleeper_teams() -> None:
    sleeper_rows = _sleeper_rows()
    rank_text = "\n".join(
        [
            "Las Vegas Enginerds 2026 Offseason Ranking List March 31, 2026",
            (
                "1 De'Von Achane RB MIA 10 1 RhamondreStevenson RB NE 85 "
                "1 Zonovan Knight RB ARI 250 1 Player Four WR SF 44 "
                "1 Player Five TE DAL 55"
            ),
            (
                "2 Lamar Jackson QB BAL 31 2 DontayvionWicks WR GB 230 "
                "2 Other Two WR SEA 299 2 Player Four B WR SF 144 "
                "2 Player Five B TE DAL 155"
            ),
            (
                "24 Daniel Jones QB IND 246 24 Tre Harris WR LAC 194 "
                "24 Last Two WR SEA 400 24 Player Four C WR SF 244 "
                "24 Player Five C TE DAL 255"
            ),
            "Free Agents",
            "194 Tre Harris LAC WR71 301 John Metchie NYJ WR108",
        ]
    )

    paper_rosters, paper_free_agents = parse_lve_rank_text(rank_text, sleeper_rows)

    niners = {row["player_name"]: row for row in paper_rosters if row["team_name"] == "Niners"}
    assert niners["De'Von Achane"]["league_rank"] == "10"
    assert niners["Lamar Jackson"]["league_rank"] == "31"
    assert niners["Daniel Jones"]["league_rank"] == "246"
    assert paper_free_agents[0]["player_name"] == "Tre Harris"
    assert paper_free_agents[0]["rank_provenance"] == RANK_PROVENANCE


def test_merge_rank_rows_preserves_sleeper_owner_and_uses_pdf_rank_aliases() -> None:
    sleeper_rows = _sleeper_rows()
    paper_rosters = [
        _paper_roster("Niners", "De'Von Achane", "10"),
        _paper_roster("Shamrockettes", "RhamondreStevenson", "85"),
        _paper_roster("Rabidmonkies", "Bam Knight", "250"),
        _paper_roster("WhoDat?", "DontayvionWicks", "230"),
    ]
    paper_free_agents = [
        {
            "player_name": "Tre Harris",
            "position": "WR",
            "nfl_team": "LAC",
            "league_rank": "194",
            "source": PDF_FREE_AGENT_SOURCE,
            "rank_provenance": RANK_PROVENANCE,
        }
    ]

    merged_rows, review_rows = merge_rank_rows(
        sleeper_rows,
        paper_rosters,
        paper_free_agents,
    )
    ranks = {row["player_name"]: row["league_rank"] for row in merged_rows}

    assert ranks["De'Von Achane"] == "10"
    assert ranks["Rhamondre Stevenson"] == "85"
    assert ranks["Zonovan Knight"] == "250"
    assert ranks["Dontayvion Wicks"] == "230"
    assert ranks["Tre' Harris"] == "194"
    assert review_rows == [
        {
            "team_name": "Precise Guesswork",
            "player_name": "Tre' Harris",
            "position": "WR",
            "nfl_team": "LAC",
            "league_rank": "194",
            "paper_player_name": "Tre Harris",
            "paper_source": PDF_FREE_AGENT_SOURCE,
            "review_note": (
                "Sleeper roster ownership kept as current truth; "
                "PDF free-agent row used only as summer league-rank provenance."
            ),
        }
    ]


def test_merge_lve_roster_ranks_writes_outputs(tmp_path) -> None:
    sleeper_path = tmp_path / "sleeper_rosters.csv"
    rank_text_path = tmp_path / "rank_text.txt"
    _write_csv(sleeper_path, _sleeper_rows())
    rank_text_path.write_text(
        "\n".join(
            [
                "1 De'Von Achane RB MIA 10 1 RhamondreStevenson RB NE 85 "
                "1 Zonovan Knight RB ARI 250 1 Player Four WR SF 44 "
                "1 Player Five TE DAL 55",
                "24 Daniel Jones QB IND 246 24 Tre Harris WR LAC 194 "
                "24 Last Two WR SEA 400 24 Player Four C WR SF 244 "
                "24 Player Five C TE DAL 255",
                "Free Agents",
                "194 Tre Harris LAC WR71",
            ]
        ),
        encoding="utf-8",
    )

    result = merge_lve_roster_ranks(
        sleeper_rosters_csv=sleeper_path,
        rank_text_path=rank_text_path,
        output_dir=tmp_path / "merged",
    )

    assert result.counts["sleeper_rosters_with_pdf_ranks"] == len(_sleeper_rows())
    assert result.files["rank_review_notes"].exists()


def _sleeper_rows() -> list[dict[str, str]]:
    return [
        _sleeper_row("Niners", "De'Von Achane", "RB", "MIA"),
        _sleeper_row("Niners", "Lamar Jackson", "QB", "BAL"),
        _sleeper_row("Niners", "Daniel Jones", "QB", "IND"),
        _sleeper_row("Shamrockettes", "Rhamondre Stevenson", "RB", "NE"),
        _sleeper_row("Rabidmonkies", "Zonovan Knight", "RB", "ARI"),
        _sleeper_row("WhoDat?", "Dontayvion Wicks", "WR", "PHI"),
        _sleeper_row("Precise Guesswork", "Tre' Harris", "WR", "LAC"),
    ]


def _sleeper_row(
    team_name: str,
    player_name: str,
    position: str,
    nfl_team: str,
) -> dict[str, str]:
    return {
        "snapshot_date": "2026-pre-draft",
        "season": "2026",
        "team_id": team_name.lower().replace("?", ""),
        "team_name": team_name,
        "owner_name": team_name,
        "player_id": player_name.lower().replace(" ", "_"),
        "player_name": player_name,
        "position": position,
        "nfl_team": nfl_team,
        "roster_status": "rostered",
        "league_rank": "",
        "source": "sleeper_api",
    }


def _paper_roster(team_name: str, player_name: str, rank: str) -> dict[str, str]:
    return {
        "team_name": team_name,
        "player_name": player_name,
        "position": "RB",
        "nfl_team": "MIA",
        "league_rank": rank,
        "source": "lve_rosters_pdf_033126_rosters",
        "rank_provenance": RANK_PROVENANCE,
        "match_key": player_name.lower(),
        "compact_key": player_name.lower().replace(" ", ""),
    }


def _write_csv(path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
