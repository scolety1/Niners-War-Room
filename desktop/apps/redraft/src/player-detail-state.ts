import type { PlayerAvailabilityStatus } from "@nwr/contracts";

/**
 * Global Player Detail primitive -- pure state/logic (NWR pre-UI
 * architecture CLOSURE pass, 2026-09-10, directive section 5).
 *
 * `player-drawer-core.tsx` (prior pass) only extracted the Draft Room's
 * identity header, seeded but not adopted anywhere else. This module is
 * the real, league-aware, cross-surface primitive: ONE global target
 * (`PlayerDetailTarget`), so the app can never show two competing player
 * detail drawers at once regardless of which surface (Draft, Lineup,
 * Waivers, Free Agents, Trades, Opponent Rosters, Players/Search/
 * Rankings/Compare) opened it. Kept as plain, dependency-free functions
 * -- this repo's vitest config only collects `*.test.ts`, never
 * `*.test.tsx` (no React-rendering test infra exists at all), so the
 * testable logic lives here; `player-detail-context.tsx`/`player-detail-
 * drawer.tsx` are thin React wiring around it.
 *
 * Identity (`playerName`/`position`/`team`) is a caller-supplied SEED --
 * every existing surface already has this from its own already-fetched
 * row data, so opening the drawer never requires a new network round
 * trip just to show a name. The shared, canonical part is STATUS:
 * `deriveBackbone` looks the target's `playerId` up in the SAME
 * `PlayerAvailabilityStatus` list every surface reads from the one
 * standalone authority endpoint (`redraftPlayerAvailabilityStatus`) --
 * never a second, surface-local status heuristic.
 */

export interface PlayerDetailTarget {
  leagueKey: string;
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  /** Which owner-facing surface opened this drawer -- purely descriptive
   * (used for an optional context-specific section), never affects
   * identity/status resolution. */
  source: string;
}

export interface PlayerDetailBackbone {
  identity: { playerId: string; playerName: string; position: string; team: string };
  status: PlayerAvailabilityStatus | null;
}

/** Two targets are "the same open player detail" when they resolve the
 * same league + player -- switching leagues (or players) is always a
 * real state change, matching this pass's context-isolation invariant
 * (`league-context.ts`'s own leagueKey-keying pattern) rather than a
 * silently-stale drawer left open across a league switch. */
export function isSamePlayerDetailTarget(
  a: PlayerDetailTarget | null,
  b: PlayerDetailTarget | null,
): boolean {
  if (a === null || b === null) return a === b;
  return a.leagueKey === b.leagueKey && a.playerId === b.playerId;
}

/** Toggle semantics used by every "View player" trigger: opening the
 * SAME player again closes the drawer (a real, expected UI affordance),
 * opening a DIFFERENT player replaces it (never stacks two drawers). */
export function togglePlayerDetail(
  current: PlayerDetailTarget | null,
  next: PlayerDetailTarget,
): PlayerDetailTarget | null {
  return isSamePlayerDetailTarget(current, next) ? null : next;
}

/** The shared identity/status backbone every context-specific drawer
 * section renders on top of. `status` is `null` (not a fabricated "OK")
 * when the authority has no entry for this player -- an honest absence,
 * matching `player_availability_status_service.py`'s own contract. */
export function derivePlayerDetailBackbone(
  target: PlayerDetailTarget,
  statuses: readonly PlayerAvailabilityStatus[],
): PlayerDetailBackbone {
  const status = statuses.find((row) => row.playerId === target.playerId) ?? null;
  return {
    identity: {
      playerId: target.playerId,
      playerName: target.playerName,
      position: target.position,
      team: status?.currentTeam ?? target.team,
    },
    status,
  };
}

/**
 * ONE shared status -> badge-tone/label mapping (directive section 2,
 * CLOSURE pass): every surface that renders the canonical
 * `PlayerAvailabilityStatus` inline (Draft's Suggestions table + its own
 * PlayerDrawer, Trade Analysis's impact tables, Trade Finder's candidate
 * cards, and this primitive's own global drawer below) reuses these two
 * pure functions instead of each re-deriving its own tone/label -- the
 * exact "no duplicate per-surface status transformation" bar `DATA_
 * AUTHORITY.md` already holds `weekly-shared.tsx`'s `statusTone` to.
 * `OUT_FOR_SEASON` is the only kind severe enough to read "blocked"; the
 * other three real kinds (`NOT_WITH_TEAM`, `ADMINISTRATIVE_EXEMPT`,
 * `TEAM_CORRECTION`) are real but non-blocking, so they read "review" --
 * never fabricated as "safe", since an absent status (not present at all
 * in the authority) is the only genuinely "safe"/no-issue case.
 */
export function playerAvailabilityBadgeTone(
  status: PlayerAvailabilityStatus | null,
): "safe" | "review" | "blocked" {
  if (!status) return "safe";
  return status.statusCategory === "OUT_FOR_SEASON" ? "blocked" : "review";
}

export function playerAvailabilityBadgeLabel(status: PlayerAvailabilityStatus | null): string {
  return status ? status.statusCategory.replace(/_/g, " ") : "No status issue";
}
