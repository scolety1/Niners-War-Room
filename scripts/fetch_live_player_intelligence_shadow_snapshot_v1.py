"""Real network fetch for the P1-5 Live Player Intelligence shadow bakeoff.

Standalone script -- NOT imported by any production path, NOT exercised by
pytest (real network I/O, same convention every other network-fetching
script in this repo already follows, e.g.
`scripts/backfill_active_pack_public_veteran_model.py`,
`scripts/build_model_v4_sleeper_age_supplement.py`).

Writes RAW snapshots only, to a new, clearly-separate, gitignored
`local_exports/` location -- never near `config/nwr_verified_current_player_
status_overrides_v1.json` (the real manual-override authority) and never
read by any consumer other than
`src/services/live_player_intelligence_shadow_v1_service.py`'s pure,
network-free processing functions.

Two real, free, keyless sources:
  * nflverse's official weekly injury report
    (`github.com/nflverse/nflverse-data`, release tag `injuries`,
    `injuries_<season>.csv`) -- no rate limit documented; safe to fetch
    any time.
  * Sleeper's public `players/nfl` catalog (`api.sleeper.app`) -- Sleeper's
    own docs (https://docs.sleeper.com/) say this ~14MB endpoint is
    "intended only to be used once per day at most" and must be cached
    locally, not re-fetched on demand. This script enforces that for real:
    it refuses to re-fetch within 24h of its own last recorded fetch
    (`fetch_log.json`) unless `--force` is passed.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
SHADOW_ROOT = REPO_ROOT / "local_exports" / "live_player_intelligence_shadow_v1"

NFLVERSE_INJURIES_DIR = SHADOW_ROOT / "nflverse_injuries" / "latest"
SLEEPER_CATALOG_DIR = SHADOW_ROOT / "sleeper_players" / "latest"
SLEEPER_FETCH_LOG = SLEEPER_CATALOG_DIR / "fetch_log.json"

USER_AGENT = "NWR-LivePlayerIntelligenceShadowBakeoff-V1 (research/reference-only, no writes)"
SLEEPER_MIN_REFETCH_INTERVAL = timedelta(hours=24)


def _get(url: str, timeout: int = 60) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 -- fixed https URLs only
        return response.read()


def fetch_nflverse_injuries(season: int) -> Path:
    """Real GET against nflverse's public GitHub release asset. No auth, no
    rate limit documented, no caching policy stated -- still written to a
    versioned local file rather than re-fetched implicitly by any caller."""

    url = f"https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{season}.csv"
    payload = _get(url)
    NFLVERSE_INJURIES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = NFLVERSE_INJURIES_DIR / f"injuries_{season}.csv"
    out_path.write_bytes(payload)
    manifest = {
        "source": "NFLVERSE_OFFICIAL_INJURY_REPORT",
        "source_url": url,
        "season": season,
        "fetched_at_utc": datetime.now(UTC).isoformat(),
        "byte_size": len(payload),
    }
    (NFLVERSE_INJURIES_DIR / f"manifest_{season}.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return out_path


def _sleeper_last_fetch() -> datetime | None:
    if not SLEEPER_FETCH_LOG.exists():
        return None
    try:
        raw = json.loads(SLEEPER_FETCH_LOG.read_text(encoding="utf-8"))
        return datetime.fromisoformat(str(raw["fetched_at_utc"]))
    except (OSError, ValueError, KeyError):
        return None


def fetch_sleeper_players_catalog(*, force: bool = False) -> Path | None:
    """Real GET against Sleeper's public players/nfl catalog, respecting
    Sleeper's own documented once-per-day caching requirement. Returns
    `None` (and fetches nothing) if the real last-fetch timestamp is under
    24h old and `force` was not passed -- this is a hard, disclosed policy,
    not a soft suggestion."""

    last_fetch = _sleeper_last_fetch()
    now = datetime.now(UTC)
    if not force and last_fetch is not None and (now - last_fetch) < SLEEPER_MIN_REFETCH_INTERVAL:
        print(
            f"SKIPPED: last real fetch was {now - last_fetch} ago (< 24h). "
            "Pass --force to override Sleeper's own once-per-day caching policy."
        )
        return None

    payload = _get("https://api.sleeper.app/v1/players/nfl", timeout=90)
    SLEEPER_CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SLEEPER_CATALOG_DIR / "sleeper_players_snapshot.json"
    out_path.write_bytes(payload)
    manifest = {
        "source": "SLEEPER_PUBLIC_PLAYERS_CATALOG",
        "source_url": "https://api.sleeper.app/v1/players/nfl",
        "fetched_at_utc": now.isoformat(),
        "byte_size": len(payload),
        "caching_policy": "Sleeper docs: fetch at most once per 24h, cache locally. Enforced by this script.",
    }
    SLEEPER_FETCH_LOG.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["nflverse", "sleeper", "both"], default="both")
    parser.add_argument("--season", type=int, default=datetime.now(UTC).year)
    parser.add_argument("--force", action="store_true", help="Bypass Sleeper's 24h re-fetch guard.")
    args = parser.parse_args()

    if args.source in ("nflverse", "both"):
        path = fetch_nflverse_injuries(args.season)
        print(f"nflverse injuries snapshot written: {path}")
    if args.source in ("sleeper", "both"):
        path = fetch_sleeper_players_catalog(force=args.force)
        if path is not None:
            print(f"Sleeper players catalog snapshot written: {path}")


if __name__ == "__main__":
    main()
