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

Four kinds of override, and only these four:

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
- `ADMINISTRATIVE_EXEMPT`: NWR OVERNIGHT V3 (Lane 1, item 1.12) -- a real,
  evidenced taxonomy gap this closes. A player can carry a real, current,
  sourced NFL roster-status code (e.g. Commissioner Exempt / "Ex/Comm.
  Perm.") that is neither an injury nor a release: he remains on an NFL
  roster in a formal sense but is not currently practicing or eligible to
  play. Before this kind existed, no diligent human could file a
  compliant override for that state -- it fit none of the other three.
  Same zero-value effect as `SEASON_OUT`/`NOT_WITH_TEAM` for automatic-
  recommendation purposes (he is not currently available to help a
  fantasy roster), same "never altered original projection, never
  removed from the pool" guarantee, kept as its own distinct kind for the
  same disclosure reason as `NOT_WITH_TEAM` -- an administrative-exempt
  reason must never be silently relabeled as an injury. This kind exists
  for any player who is genuinely in this real, sourced status; it is not
  scoped to any one named player, and adding this kind does not itself
  add or imply any specific player's override -- each still requires its
  own individually verified, cited entry via `add_verified_status_override`.
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
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.redraft_engine_v1_service import RankingResult

OVERRIDES_RELATIVE_PATH = Path("config/nwr_verified_current_player_status_overrides_v1.json")


@dataclass(frozen=True)
class StatusOverride:
    player_id: str
    player_name: str
    kind: str  # "SEASON_OUT" | "NOT_WITH_TEAM" | "ADMINISTRATIVE_EXEMPT" | "TEAM_CORRECTION"
    reason: str
    effective_date: str
    verified_at_utc: str
    sources: tuple[str, ...]
    corrected_team: str = ""


# Zero-value kinds: distinct, honestly-labeled REASONS (injury vs. simply
# unsigned/released vs. a real administrative-exempt roster status), but
# the same real effect on automatic-recommendation value -- none of these
# implies another, and the UI/report text must not collapse "not with any
# team" or "administratively exempt" into "injured."
ZERO_VALUE_KINDS = frozenset({"SEASON_OUT", "NOT_WITH_TEAM", "ADMINISTRATIVE_EXEMPT"})


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


class StatusOverrideIntakeError(ValueError):
    """A real event/status intake rejection (NWR post-draft overnight,
    section 13) -- distinguishes a REFUSED submission (missing citation,
    bad kind, malformed date, conflicting duplicate) from any other
    ValueError, so a future UI/facade caller can surface the real reason
    to the owner rather than a generic failure."""


def add_verified_status_override(
    repo_root: str | Path,
    *,
    player_id: str,
    player_name: str,
    kind: str,
    reason: str,
    effective_date: str,
    verified_at_utc: str,
    sources: tuple[str, ...],
    corrected_team: str = "",
) -> StatusOverride:
    """The real intake contract this module previously lacked: every
    existing override in the committed file was added by hand, outside
    any validated path. This is the one place a NEW real, individually-
    verified status event enters the system -- and it enforces the same
    discipline the module's own docstring already promises for the
    hand-authored entries: never a fabricated event, never a blanket
    rule, never a mislabeled reason.

    Rejects (raises `StatusOverrideIntakeError`, never silently drops or
    guesses a fix) rather than accepting:
    - a `kind` outside the four real, disclosed kinds
    - zero cited `sources` -- an override with no verifiable source is
      exactly the "fabricated event" this contract exists to refuse
    - a `TEAM_CORRECTION` with no `corrected_team`, or a non-
      `TEAM_CORRECTION` that supplies one (keeps each kind's real effect
      unambiguous -- see `apply_status_overrides_to_ranking`)
    - an `effective_date` or `verified_at_utc` that doesn't parse as a
      real date/timestamp (never accepts a free-text non-date string)
    - a `player_id` that already has an override on file -- a real status
      change to an already-overridden player must be a deliberate
      correction to the existing entry, not a second, silently-stacked
      one this module would then have to arbitrate between

    On success, appends the new entry to the real committed config file
    and returns the `StatusOverride` that was written -- this function
    performs the write; it is the caller's responsibility to only invoke
    it with a real, sourced event (this contract enforces citation, not
    truth -- it cannot verify a URL actually supports the claim, only
    that one was provided)."""
    kind = str(kind)
    if kind not in (ZERO_VALUE_KINDS | {"TEAM_CORRECTION"}):
        raise StatusOverrideIntakeError(
            "kind must be one of SEASON_OUT, NOT_WITH_TEAM, ADMINISTRATIVE_EXEMPT, "
            f"TEAM_CORRECTION -- got {kind!r}"
        )
    if not player_id:
        raise StatusOverrideIntakeError("player_id is required")
    cleaned_sources = tuple(str(url).strip() for url in sources if str(url).strip())
    if not cleaned_sources:
        raise StatusOverrideIntakeError(
            "at least one real, cited source URL is required -- an uncited event is "
            "exactly what this intake contract exists to refuse"
        )
    if not reason or not str(reason).strip():
        raise StatusOverrideIntakeError("reason is required")
    for label, value in (("effective_date", effective_date), ("verified_at_utc", verified_at_utc)):
        try:
            if label == "effective_date":
                date.fromisoformat(str(value))
            else:
                datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise StatusOverrideIntakeError(f"{label} is not a real ISO date/timestamp: {value!r}") from exc
    corrected_team = str(corrected_team or "").strip()
    if kind == "TEAM_CORRECTION" and not corrected_team:
        raise StatusOverrideIntakeError("TEAM_CORRECTION requires corrected_team")
    if kind != "TEAM_CORRECTION" and corrected_team:
        raise StatusOverrideIntakeError(f"corrected_team is only valid for TEAM_CORRECTION, not {kind}")

    path = Path(repo_root) / OVERRIDES_RELATIVE_PATH
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StatusOverrideIntakeError(f"could not read the existing overrides file: {exc}") from exc
    existing_overrides = raw.get("overrides") if isinstance(raw, dict) else None
    if not isinstance(existing_overrides, list):
        raise StatusOverrideIntakeError("the overrides file's 'overrides' field is missing or malformed")
    if any(str(entry.get("player_id")) == player_id for entry in existing_overrides if isinstance(entry, dict)):
        raise StatusOverrideIntakeError(
            f"player_id {player_id!r} already has an override on file -- edit that entry "
            "directly rather than adding a second, conflicting one"
        )

    new_entry: dict[str, object] = {
        "player_id": player_id,
        "player_name": str(player_name or ""),
        "kind": kind,
        "effective_date": str(effective_date),
        "verified_at_utc": str(verified_at_utc),
        "reason": str(reason),
        "sources": list(cleaned_sources),
    }
    if corrected_team:
        new_entry["corrected_team"] = corrected_team
    existing_overrides.append(new_entry)
    path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
    return StatusOverride(
        player_id=player_id,
        player_name=str(player_name or ""),
        kind=kind,
        reason=str(reason),
        effective_date=str(effective_date),
        verified_at_utc=str(verified_at_utc),
        sources=cleaned_sources,
        corrected_team=corrected_team,
    )


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
