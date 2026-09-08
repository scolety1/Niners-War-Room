"""NWR next-draft final blocker closure, section 1: real, honest, actionable
diagnostics for the projection-snapshot freshness gate.

Real root cause traced and confirmed this session: `load_projection_snapshot`'s
row-level `source_as_of` freshness gate (`MAX_PROJECTION_AGE_DAYS = 30`) is
real, working-as-designed governance -- not a bug. The real owner's own
live-installed 2026 projection snapshot (`source_as_of` 2026-07-30/2026-08-08)
has now organically aged past that window as real calendar time advances, and
its one real `DRAFT_DAY_AUTHORIZATION.json` (scoped to the real 2026-09-07
403 N 18th draft) has correctly self-expired (`expires_at_utc`
2026-09-08T10:00:00Z). Verified directly, read-only, against the real
`AppData\\...\\projections\\2026\\current.csv`: all 608 real rows blocked for
the identical real reason.

The real fix here is diagnostic-only: `load_projection_snapshot`'s top-level
`errors` message is upgraded from a generic "no rankable player rows" to a
specific, actionable one identifying the real cause (freshness) and the real
authorization-file status, when every blocked row shares that one real
reason. The real admission/blocking LOGIC itself (`_source_as_of_reason`,
`_load_draft_day_authorization`, `MAX_PROJECTION_AGE_DAYS`) is completely
unchanged -- these tests prove the message is honest, not that governance
was loosened.

Uses dynamically-computed dates (never a hardcoded calendar date) so these
tests remain valid regardless of when they are run -- the same real
"environmental source_as_of date-cliff" this session found rotting several
OTHER, pre-existing tests in `test_redraft_engine_v1_service.py` (unrelated,
not fixed here; those fixtures predate this session)."""

from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from src.services.redraft_engine_v1_service import (
    DRAFT_DAY_AUTHORIZATION_FILENAME,
    MAX_PROJECTION_AGE_DAYS,
    load_projection_snapshot,
)

TODAY = date.today()
STALE_SOURCE_AS_OF = (TODAY - timedelta(days=MAX_PROJECTION_AGE_DAYS + 5)).isoformat()
FRESH_SOURCE_AS_OF = (TODAY - timedelta(days=5)).isoformat()
# Real seasons in this codebase are labeled by the calendar year of the
# season being drafted for (e.g. season 2026 during real calendar 2026) --
# matches `_source_as_of_reason`'s own real earliest-bound
# `date(season - 1, 12, 1)`, so a real "5 days ago" source_as_of always
# falls inside the real, current season's real admitted window.
SEASON = TODAY.year


def _row(player_id: str, name: str, *, source_as_of: str) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": name,
        "position": "RB",
        "team": "TST",
        "season": SEASON,
        "source_status": "GOVERNED",
        "evidence_status": "ADMITTED_CURRENT_SEASON",
        "source_as_of": source_as_of,
        "rushing_yards": 900,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _authorization(
    *,
    label: str = "OWNER_DRAFT_DAY_APPROVAL_2026_TEST",
    bound_source_sha256: str,
    expires_at_utc: str,
    player_ids: list[str],
) -> dict[str, object]:
    return {
        "label": label,
        "bound_source_sha256": bound_source_sha256,
        "expires_at_utc": expires_at_utc,
        "player_ids": player_ids,
    }


def test_fresh_data_root_with_no_authorization_gets_a_real_actionable_message(
    tmp_path: Path,
) -> None:
    """A clean, fresh bootstrap (no `DRAFT_DAY_AUTHORIZATION.json` at all) --
    the real, most common "next-draft blocker" scenario for a brand-new
    profile/data root."""
    csv_path = tmp_path / "current.csv"
    _write_csv(csv_path, [_row("P1", "Player One", source_as_of=STALE_SOURCE_AS_OF)])
    snapshot = load_projection_snapshot(csv_path, season=SEASON)
    assert snapshot.players == ()
    assert len(snapshot.blocked_rows) == 1
    assert len(snapshot.errors) == 1
    message = snapshot.errors[0]
    assert "freshness window" in message
    assert "no draft-day authorization file is present" in message
    assert "governed admission" in message.lower()


def test_existing_data_root_with_expired_authorization_reports_expiry(tmp_path: Path) -> None:
    """The real scenario this session found live against the owner's actual
    install: a real authorization file exists, was real and valid for a
    past draft, and has since correctly self-expired."""
    csv_path = tmp_path / "current.csv"
    _write_csv(csv_path, [_row("P1", "Player One", source_as_of=STALE_SOURCE_AS_OF)])
    digest = load_projection_snapshot(csv_path, season=SEASON).source_sha256
    expired_at = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    (tmp_path / DRAFT_DAY_AUTHORIZATION_FILENAME).write_text(
        json.dumps(_authorization(bound_source_sha256=digest, expires_at_utc=expired_at, player_ids=["P1"])),
        encoding="utf-8",
    )
    snapshot = load_projection_snapshot(csv_path, season=SEASON)
    assert snapshot.players == ()
    message = snapshot.errors[0]
    assert "expired at" in message


def test_authorization_bound_to_a_different_artifact_is_reported_as_a_hash_mismatch(
    tmp_path: Path,
) -> None:
    csv_path = tmp_path / "current.csv"
    _write_csv(csv_path, [_row("P1", "Player One", source_as_of=STALE_SOURCE_AS_OF)])
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    (tmp_path / DRAFT_DAY_AUTHORIZATION_FILENAME).write_text(
        json.dumps(
            _authorization(
                bound_source_sha256="0" * 64, expires_at_utc=future, player_ids=["P1"]
            )
        ),
        encoding="utf-8",
    )
    snapshot = load_projection_snapshot(csv_path, season=SEASON)
    assert snapshot.players == ()
    message = snapshot.errors[0]
    assert "different projection artifact hash" in message


def test_valid_active_authorization_admits_the_real_covered_rows(tmp_path: Path) -> None:
    """A real, currently-valid authorization (not expired, hash-bound to the
    exact real snapshot, covering the real player_id) lets that row through
    -- the existing, unmodified bypass mechanism, proven still working."""
    csv_path = tmp_path / "current.csv"
    _write_csv(csv_path, [_row("P1", "Player One", source_as_of=STALE_SOURCE_AS_OF)])
    digest = load_projection_snapshot(csv_path, season=SEASON).source_sha256
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    (tmp_path / DRAFT_DAY_AUTHORIZATION_FILENAME).write_text(
        json.dumps(
            _authorization(bound_source_sha256=digest, expires_at_utc=future, player_ids=["P1"])
        ),
        encoding="utf-8",
    )
    snapshot = load_projection_snapshot(csv_path, season=SEASON)
    assert [p.player_id for p in snapshot.players] == ["P1"]
    assert snapshot.blocked_rows == ()
    assert snapshot.players[0].draft_day_prior_override is True


def test_veteran_component_authorized_rookie_component_still_blocked(tmp_path: Path) -> None:
    """Real, exact reproduction of the owner's own real authorization scope
    (`DRAFT_DAY_AUTHORIZATION.json`'s own real, disclosed reason: "veteran
    component ONLY... deliberately does NOT cover the 78 rookie rows"). A
    real authorization covering only SOME player_ids must leave the
    uncovered ones genuinely blocked -- never a blanket bypass."""
    csv_path = tmp_path / "current.csv"
    _write_csv(
        csv_path,
        [
            _row("VET1", "Veteran One", source_as_of=STALE_SOURCE_AS_OF),
            _row("ROOK1", "Rookie One", source_as_of=STALE_SOURCE_AS_OF),
        ],
    )
    digest = load_projection_snapshot(csv_path, season=SEASON).source_sha256
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    (tmp_path / DRAFT_DAY_AUTHORIZATION_FILENAME).write_text(
        json.dumps(
            _authorization(bound_source_sha256=digest, expires_at_utc=future, player_ids=["VET1"])
        ),
        encoding="utf-8",
    )
    snapshot = load_projection_snapshot(csv_path, season=SEASON)
    assert [p.player_id for p in snapshot.players] == ["VET1"]
    assert [row["player_id"] for row in snapshot.blocked_rows] == ["ROOK1"]
    # Partial admission: our new all-rows-freshness-blocked diagnostic must
    # NOT fire here (not every row is blocked) -- the real, generic
    # "no rankable player rows" message is never emitted either, since real
    # players WERE admitted; no top-level freshness error at all.
    assert not any("freshness window" in message for message in snapshot.errors)


def test_fresh_projection_rows_are_never_blocked_or_diagnosed(tmp_path: Path) -> None:
    """A real, currently-fresh snapshot (well inside the 30-day window) --
    the real, healthy case -- must show zero blocked rows and no freshness
    diagnostic, with no authorization file needed at all."""
    csv_path = tmp_path / "current.csv"
    _write_csv(csv_path, [_row("P1", "Player One", source_as_of=FRESH_SOURCE_AS_OF)])
    snapshot = load_projection_snapshot(csv_path, season=SEASON)
    assert [p.player_id for p in snapshot.players] == ["P1"]
    assert snapshot.blocked_rows == ()
    assert not any("freshness window" in message for message in snapshot.errors)


def test_two_unrelated_leagues_do_not_leak_authorization_across_data_roots(
    tmp_path: Path,
) -> None:
    """Real, explicit no-cross-league-leakage proof: two independent
    snapshot directories (as two real league profiles would each have,
    since `_load_draft_day_authorization`/`_draft_day_authorization_status`
    both key off the real snapshot's own parent directory) -- an active
    authorization in one must have zero effect on the other, even for the
    exact same real player_id and even when both real CSVs are byte-
    identical."""
    league_a = tmp_path / "league_a"
    league_b = tmp_path / "league_b"
    league_a.mkdir()
    league_b.mkdir()
    rows = [_row("SHARED1", "Shared Player", source_as_of=STALE_SOURCE_AS_OF)]
    _write_csv(league_a / "current.csv", rows)
    _write_csv(league_b / "current.csv", rows)
    digest = load_projection_snapshot(league_a / "current.csv", season=SEASON).source_sha256
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    (league_a / DRAFT_DAY_AUTHORIZATION_FILENAME).write_text(
        json.dumps(
            _authorization(
                bound_source_sha256=digest, expires_at_utc=future, player_ids=["SHARED1"]
            )
        ),
        encoding="utf-8",
    )
    snapshot_a = load_projection_snapshot(league_a / "current.csv", season=SEASON)
    snapshot_b = load_projection_snapshot(league_b / "current.csv", season=SEASON)
    assert [p.player_id for p in snapshot_a.players] == ["SHARED1"]
    assert snapshot_b.players == ()
    assert "no draft-day authorization file is present" in snapshot_b.errors[0]
