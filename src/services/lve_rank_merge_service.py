from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

RANK_PROVENANCE = "FantasyPros February 27, 2026"
PDF_ROSTER_SOURCE = "lve_rosters_pdf_033126_rosters"
PDF_FREE_AGENT_SOURCE = "lve_rosters_pdf_033126_free_agents"

PLAYER_ALIASES = {
    "bam knight": "zonovan knight",
    "dontayvionwicks": "dontayvion wicks",
    "rhamondrestevenson": "rhamondre stevenson",
}

ROSTER_ENTRY_PATTERN = re.compile(
    r"(?:^|\s)(?P<slot>\d{1,2})\s+"
    r"(?P<player>.+?)\s*"
    r"(?P<pos>QB|RB|WR|TE|K)\s+"
    r"(?P<nfl>[A-Z]{2,3}|FA)\s+"
    r"(?P<rank>\d{1,3})(?=\s+\d{1,2}\s+|$)"
)
FREE_AGENT_ENTRY_PATTERN = re.compile(
    r"(?:^|\s)(?P<rank>\d{1,3})\s+"
    r"(?P<player>.+?)\s+"
    r"(?P<nfl>[A-Z]{2,3}|FA)\s+"
    r"(?P<pos>QB|RB|WR|TE|K)(?P<pos_rank>\d{1,3})(?=\s+\d{1,3}\s+|$)"
)


@dataclass(frozen=True)
class RankMergeResult:
    output_dir: Path
    files: dict[str, Path]
    counts: dict[str, int]


def merge_lve_roster_ranks(
    *,
    sleeper_rosters_csv: str | Path,
    rank_text_path: str | Path,
    output_dir: str | Path,
) -> RankMergeResult:
    sleeper_rows = _read_csv(Path(sleeper_rosters_csv))
    rank_text = Path(rank_text_path).read_text(encoding="utf-8")
    paper_roster_rows, paper_free_agents = parse_lve_rank_text(rank_text, sleeper_rows)
    merged_rows, review_rows = merge_rank_rows(
        sleeper_rows,
        paper_roster_rows,
        paper_free_agents,
    )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files = {
        "paper_roster_ranks": output / "paper_roster_ranks.csv",
        "paper_free_agents": output / "paper_free_agents.csv",
        "sleeper_rosters_with_pdf_ranks": output / "sleeper_rosters_with_pdf_ranks.csv",
        "rank_review_notes": output / "rank_review_notes.csv",
        "comparison_summary": output / "comparison_summary.csv",
    }
    summary_rows = [
        {"metric": "sleeper_roster_rows", "value": len(sleeper_rows)},
        {"metric": "paper_roster_rows_parsed", "value": len(paper_roster_rows)},
        {
            "metric": "matched_from_paper_rosters",
            "value": _count_source(merged_rows, PDF_ROSTER_SOURCE),
        },
        {
            "metric": "matched_from_paper_free_agents",
            "value": _count_source(merged_rows, PDF_FREE_AGENT_SOURCE),
        },
        {
            "metric": "sleeper_unmatched_in_pdf_roster_or_fa",
            "value": _count_unmatched(merged_rows),
        },
        {"metric": "paper_free_agents_parsed", "value": len(paper_free_agents)},
        {"metric": "rank_review_notes", "value": len(review_rows)},
    ]

    _write_csv(files["paper_roster_ranks"], paper_roster_rows)
    _write_csv(files["paper_free_agents"], paper_free_agents)
    _write_csv(files["sleeper_rosters_with_pdf_ranks"], merged_rows)
    _write_csv(files["rank_review_notes"], review_rows)
    _write_csv(files["comparison_summary"], summary_rows)
    return RankMergeResult(
        output_dir=output,
        files=files,
        counts={name: _row_count(path) for name, path in files.items()},
    )


def parse_lve_rank_text(
    rank_text: str,
    sleeper_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    sleeper_by_team = _sleeper_match_keys_by_team(sleeper_rows)
    team_names = sorted(sleeper_by_team)
    blocks: list[list[dict[str, str]]] = [[] for _ in range(len(team_names))]
    free_agents: list[dict[str, str]] = []
    block_index = 0
    in_free_agents = False

    for line in rank_text.splitlines():
        if line.startswith("Free Agents"):
            in_free_agents = True
            continue
        if in_free_agents:
            free_agents.extend(_free_agent_rows_from_line(line))
            continue

        matches = list(ROSTER_ENTRY_PATTERN.finditer(line))
        if len(matches) < 4:
            continue

        start_column = block_index * 5
        if _line_has_collapsed_blank_first_cell(matches[0]):
            start_column += 1
        for offset, match in enumerate(matches[:5]):
            column = start_column + offset
            if column >= len(blocks):
                continue
            row = _paper_roster_row(match)
            if row["player_name"]:
                blocks[column].append(row)
        if matches[0].group("slot") == "24":
            block_index += 1

    column_to_team = _match_pdf_columns_to_sleeper_teams(blocks, sleeper_by_team)
    roster_rows: list[dict[str, str]] = []
    for column, rows in enumerate(blocks):
        team_name = column_to_team.get(column, "")
        for row in rows:
            next_row = dict(row)
            next_row["team_name"] = team_name
            next_row["match_key"] = canonical_name(row["player_name"])
            next_row["compact_key"] = compact_name(row["player_name"])
            roster_rows.append(next_row)
    return roster_rows, free_agents


def merge_rank_rows(
    sleeper_rows: list[dict[str, str]],
    paper_roster_rows: list[dict[str, str]],
    paper_free_agents: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    roster_rank_by_team_player: dict[tuple[str, str], dict[str, str]] = {}
    for row in paper_roster_rows:
        for key in match_keys(row["player_name"]):
            roster_rank_by_team_player[(row["team_name"], key)] = row

    free_agent_rank_by_player: dict[str, dict[str, str]] = {}
    for row in paper_free_agents:
        for key in match_keys(row["player_name"]):
            free_agent_rank_by_player[key] = row

    merged_rows: list[dict[str, str]] = []
    review_rows: list[dict[str, str]] = []
    for sleeper_row in sleeper_rows:
        paper_row = _find_roster_rank(sleeper_row, roster_rank_by_team_player)
        source = PDF_ROSTER_SOURCE if paper_row else ""
        if paper_row is None:
            paper_row = _find_free_agent_rank(sleeper_row, free_agent_rank_by_player)
            if paper_row is not None:
                source = PDF_FREE_AGENT_SOURCE
                review_rows.append(_review_row(sleeper_row, paper_row))

        merged_rows.append(_merged_row(sleeper_row, paper_row, source))
    return merged_rows, review_rows


def canonical_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace(".", "").replace("'", "").replace("’", "")
    text = text.replace("-", " ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return PLAYER_ALIASES.get(text, text)


def compact_name(value: str) -> str:
    return canonical_name(value).replace(" ", "")


def match_keys(value: str) -> set[str]:
    return {canonical_name(value), compact_name(value)}


def _line_has_collapsed_blank_first_cell(match: re.Match[str]) -> bool:
    first_word = match.group("player").strip().split(" ", 1)[0]
    return first_word.isdigit()


def _paper_roster_row(match: re.Match[str]) -> dict[str, str]:
    player_name = match.group("player").strip()
    parts = player_name.split(" ", 1)
    if parts and parts[0].isdigit():
        player_name = parts[1] if len(parts) > 1 else ""
    return {
        "roster_slot": match.group("slot").strip(),
        "player_name": player_name,
        "position": match.group("pos").strip(),
        "nfl_team": match.group("nfl").strip(),
        "league_rank": match.group("rank").strip(),
        "source": PDF_ROSTER_SOURCE,
        "rank_provenance": RANK_PROVENANCE,
    }


def _free_agent_rows_from_line(line: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for match in FREE_AGENT_ENTRY_PATTERN.finditer(line):
        rows.append(
            {
                "league_rank": match.group("rank").strip(),
                "player_name": match.group("player").strip(),
                "nfl_team": match.group("nfl").strip(),
                "position": match.group("pos").strip(),
                "positional_rank": match.group("pos_rank").strip(),
                "source": PDF_FREE_AGENT_SOURCE,
                "rank_provenance": RANK_PROVENANCE,
            }
        )
    return rows


def _sleeper_match_keys_by_team(
    sleeper_rows: list[dict[str, str]],
) -> dict[str, set[str]]:
    keys_by_team: dict[str, set[str]] = {}
    for row in sleeper_rows:
        keys_by_team.setdefault(row["team_name"], set()).update(
            match_keys(row["player_name"])
        )
    return keys_by_team


def _match_pdf_columns_to_sleeper_teams(
    blocks: list[list[dict[str, str]]],
    sleeper_by_team: dict[str, set[str]],
) -> dict[int, str]:
    column_to_team: dict[int, str] = {}
    for column, rows in enumerate(blocks):
        names: set[str] = set()
        for row in rows:
            names.update(match_keys(row["player_name"]))
        best_overlap = -1
        best_team = ""
        for team_name, sleeper_names in sleeper_by_team.items():
            overlap = len(names & sleeper_names)
            if overlap > best_overlap:
                best_overlap = overlap
                best_team = team_name
        column_to_team[column] = best_team
    return column_to_team


def _find_roster_rank(
    sleeper_row: dict[str, str],
    roster_rank_by_team_player: dict[tuple[str, str], dict[str, str]],
) -> dict[str, str] | None:
    for key in match_keys(sleeper_row["player_name"]):
        paper_row = roster_rank_by_team_player.get((sleeper_row["team_name"], key))
        if paper_row is not None:
            return paper_row
    return None


def _find_free_agent_rank(
    sleeper_row: dict[str, str],
    free_agent_rank_by_player: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    for key in match_keys(sleeper_row["player_name"]):
        paper_row = free_agent_rank_by_player.get(key)
        if paper_row is not None:
            return paper_row
    return None


def _merged_row(
    sleeper_row: dict[str, str],
    paper_row: dict[str, str] | None,
    paper_source: str,
) -> dict[str, str]:
    row = dict(sleeper_row)
    row.pop("official_rank", None)
    row["league_rank"] = paper_row["league_rank"] if paper_row else ""
    row["league_rank_provenance"] = RANK_PROVENANCE if paper_row else ""
    row["paper_player_name"] = paper_row["player_name"] if paper_row else ""
    row["paper_nfl_team"] = paper_row["nfl_team"] if paper_row else ""
    row["paper_position"] = paper_row["position"] if paper_row else ""
    row["paper_source"] = paper_source
    return row


def _review_row(
    sleeper_row: dict[str, str],
    paper_row: dict[str, str],
) -> dict[str, str]:
    return {
        "team_name": sleeper_row["team_name"],
        "player_name": sleeper_row["player_name"],
        "position": sleeper_row["position"],
        "nfl_team": sleeper_row["nfl_team"],
        "league_rank": paper_row["league_rank"],
        "paper_player_name": paper_row["player_name"],
        "paper_source": PDF_FREE_AGENT_SOURCE,
        "review_note": (
            "Sleeper roster ownership kept as current truth; "
            "PDF free-agent row used only as summer league-rank provenance."
        ),
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str] | dict[str, int]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _count_source(rows: list[dict[str, str]], source: str) -> int:
    return sum(1 for row in rows if row.get("paper_source") == source)


def _count_unmatched(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if not row.get("league_rank"))


def _row_count(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)
