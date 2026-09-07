"""Verified current-availability/identity overrides (NWR Overnight repair).

The admitted projection snapshot is frozen as of its own `source_as_of`
(currently 2026-08-08); real-world facts that change after that date --
season-ending injuries, trades that move a player's team -- do not reach
the projection until a new governed admission, which is a separate,
heavier process this module does not perform or bypass.

This module is a thin, additive, individually-sourced correction layer
applied to the already-generated LIVE `RankingResult` at the two real
call sites that build it for a live current-season redraft profile
(`_redraft_ranking_for_profile`, `redraft_bootstrap`'s inline duplicate of
the same two lines) -- deliberately NOT inside `_asset_pool`/
`_roster_players`, the lower-level primitives historical backtest/replay
code also shares, so a 2026 current-status correction can never leak into
a 2016-2024 historical evaluation. Every live consumer downstream of
`ranking.rows` (recommendations, CPU picks, rollouts, roster completion,
decision-bundle scoring) reads the corrected rows automatically, since
they all resolve players from this same `RankingResult`.

Three kinds of override, and only these three:

- `SEASON_OUT`: a real, current-team INJURY designation (e.g. a season-
  ending ACL tear while still rostered). The player's ORIGINAL projected
  value is left completely intact (the frozen projection is never
  altered), but the value this module surfaces for automatic
  recommendation/CPU-selection/roster-completion purposes is zero -- he
  cannot become an automatic top suggestion, CPU pick, or count toward a
  "complete" roster. He is never removed from the pool: still searchable,
  still directly draftable with an explicit override so an owner can
  record a real external pick.
- `NOT_WITH_TEAM`: the same zero-value effect as `SEASON_OUT`, for a
  DIFFERENT real reason -- released/unsigned, not currently on any NFL
  roster at all. Kept as a distinct kind rather than folded into
  `SEASON_OUT` so the disclosed reason never mislabels "unsigned" as
  "injured" or vice versa.
- `TEAM_CORRECTION`: only the `team` field is replaced; nothing about the
  player's value, identity, or projection changes.

Every override here was individually verified against current, named,
dated sources (see `sources` in the data file) -- never a blanket "IR
means unavailable" rule (a player on Reserve/Injured but Designated for
Return is deliberately NOT in this file; see
`explicitly_not_overridden_examples`), and never invented without a real
citation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.redraft_engine_v1_service import RankingResult

OVERRIDES_RELATIVE_PATH = Path("config/nwr_verified_current_player_status_overrides_v1.json")


@dataclass(frozen=True)
class StatusOverride:
    player_id: str
    player_name: str
    kind: str  # "SEASON_OUT" | "NOT_WITH_TEAM" | "TEAM_CORRECTION"
    reason: str
    effective_date: str
    verified_at_utc: str
    sources: tuple[str, ...]
    corrected_team: str = ""


# Zero-value kinds: distinct, honestly-labeled REASONS (injury vs. simply
# unsigned/released), but the same real effect on automatic-recommendation
# value -- neither implies the other, and the UI/report text must not
# collapse "not with any team" into "injured."
ZERO_VALUE_KINDS = frozenset({"SEASON_OUT", "NOT_WITH_TEAM"})


def load_status_overrides(repo_root: str | Path) -> tuple[StatusOverride, ...]:
    path = Path(repo_root) / OVERRIDES_RELATIVE_PATH
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ()
    overrides = raw.get("overrides") if isinstance(raw, dict) else None
    if not isinstance(overrides, list):
        return ()
    result: list[StatusOverride] = []
    for entry in overrides:
        if not isinstance(entry, dict):
            continue
        player_id = str(entry.get("player_id") or "")
        kind = str(entry.get("kind") or "")
        if not player_id or kind not in (ZERO_VALUE_KINDS | {"TEAM_CORRECTION"}):
            continue
        result.append(
            StatusOverride(
                player_id=player_id,
                player_name=str(entry.get("player_name") or ""),
                kind=kind,
                reason=str(entry.get("reason") or ""),
                effective_date=str(entry.get("effective_date") or ""),
                verified_at_utc=str(entry.get("verified_at_utc") or ""),
                sources=tuple(str(url) for url in entry.get("sources") or ()),
                corrected_team=str(entry.get("corrected_team") or ""),
            )
        )
    return tuple(result)


def apply_status_overrides_to_ranking(
    ranking: "RankingResult", overrides: tuple[StatusOverride, ...]
) -> "RankingResult":
    """Applies verified current-status overrides to an already-generated
    live `RankingResult`, at the ONE place both real live-ranking call
    sites (`_redraft_ranking_for_profile`, `redraft_bootstrap`) share --
    never inside `_asset_pool`/`_roster_players`, which historical
    backtest/replay code also uses, and which must never see a 2026
    current-status correction applied to a 2016-2024 season.

    A season-out player's `replacement_adjusted_value` (the field every
    recommendation/CPU-pick/roster-completion path reads as his value)
    goes to 0.0; `projected_points` -- the ORIGINAL, unmodified projection
    -- is preserved unchanged for provenance, exactly as the directive
    requires. He is never removed from `ranking.rows`: still searchable,
    still directly draftable to record a real external pick.

    Overall/position rank and row order are RE-DERIVED with the same sort
    key `generate_rankings` itself uses (value desc, projected desc,
    position, player_id) -- a zeroed season-out player naturally sinks to
    the bottom of both the field AND the row order, so every consumer
    that reads rank-by-field (CPU auto-pick's `_owner_auto_score`) and
    every consumer that reads list order (Suggestions shortlist
    generation) agree, instead of only one of the two being corrected.
    """
    if not overrides or not ranking.rows:
        return ranking
    by_id = {override.player_id: override for override in overrides}
    changed = False
    updated_rows = []
    for row in ranking.rows:
        override = by_id.get(row.player_id)
        if override is None:
            updated_rows.append(row)
            continue
        changed = True
        if override.kind == "TEAM_CORRECTION" and override.corrected_team:
            updated_rows.append(replace(row, team=override.corrected_team))
        elif override.kind in ZERO_VALUE_KINDS:
            updated_rows.append(replace(row, replacement_adjusted_value=0.0, starter_gap=0.0))
        else:
            updated_rows.append(row)
    if not changed:
        return ranking
    updated_rows.sort(
        key=lambda row: (
            -row.replacement_adjusted_value,
            -row.projected_points,
            row.position,
            row.player_id,
        )
    )
    position_ranks: dict[str, int] = {}
    final_rows = []
    for index, row in enumerate(updated_rows, start=1):
        position_ranks[row.position] = position_ranks.get(row.position, 0) + 1
        final_rows.append(
            replace(row, overall_rank=index, position_rank=position_ranks[row.position])
        )
    return replace(ranking, rows=tuple(final_rows))
