import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import {
  isSamePlayerDetailTarget,
  togglePlayerDetail,
  type PlayerDetailTarget,
} from "./player-detail-state";

/**
 * Global Player Detail primitive -- React wiring (NWR pre-UI
 * architecture CLOSURE pass, 2026-09-10, directive section 5). See
 * `player-detail-state.ts` for the pure open/close/dedup logic this
 * wraps.
 *
 * Mounted ONCE (`RedraftApp.tsx`) above the router so it is a true
 * singleton -- every surface that calls `openPlayerDetail(...)` shares
 * the SAME open/closed state, which is what guarantees "the same player
 * should never have multiple competing detail drawers" (directive
 * section 5) even when two different pages could otherwise both try to
 * show one.
 */

interface PlayerDetailContextValue {
  active: PlayerDetailTarget | null;
  openPlayerDetail: (target: PlayerDetailTarget) => void;
  closePlayerDetail: () => void;
}

const PlayerDetailContext = createContext<PlayerDetailContextValue | null>(null);

export function PlayerDetailProvider({
  children,
  activeLeagueKey = null,
}: {
  children: ReactNode;
  // NWR UI expansion pass, Work Unit 9 (endurance QA) -- real, reproduced
  // bug found via league-switch endurance cycling: this provider is a
  // true app-wide singleton mounted ABOVE the router (see RedraftApp.tsx's
  // own module doc), so nothing ever closed an already-open drawer when
  // the ACTIVE LEAGUE changed underneath it -- switching leagues while a
  // drawer was open left it showing the PRIOR league's player, silently,
  // with no visual signal anything was wrong. `player-detail-state.ts`'s
  // own `isSamePlayerDetailTarget` already documents this exact invariant
  // ("switching leagues ... is always a real state change") but nothing
  // enforced it outside the same-player toggle path. Optional and
  // additive -- a caller that omits this prop (none exist today, but this
  // keeps the primitive usable standalone/in a future test) renders
  // byte-for-byte as before, just without the auto-close.
  activeLeagueKey?: string | null;
}) {
  const [active, setActive] = useState<PlayerDetailTarget | null>(null);

  useEffect(() => {
    setActive((current) => (current && current.leagueKey !== activeLeagueKey ? null : current));
  }, [activeLeagueKey]);

  const openPlayerDetail = useCallback((target: PlayerDetailTarget) => {
    setActive((current) => togglePlayerDetail(current, target));
  }, []);
  const closePlayerDetail = useCallback(() => setActive(null), []);

  const value = useMemo<PlayerDetailContextValue>(
    () => ({ active, openPlayerDetail, closePlayerDetail }),
    [active, openPlayerDetail, closePlayerDetail],
  );

  return <PlayerDetailContext.Provider value={value}>{children}</PlayerDetailContext.Provider>;
}

export function usePlayerDetail(): PlayerDetailContextValue {
  const context = useContext(PlayerDetailContext);
  if (!context) {
    throw new Error("usePlayerDetail() must be called beneath <PlayerDetailProvider>.");
  }
  return context;
}

/** Convenience for a table row's "View" action -- callers only need to
 * supply the identity fields they already have on hand from their own
 * already-fetched row data (no new fetch to open the drawer). */
export function usePlayerDetailOpener(leagueKey: string | null, source: string) {
  const { openPlayerDetail } = usePlayerDetail();
  return useCallback(
    (player: { playerId: string; playerName: string; position?: string; team?: string }) => {
      if (!leagueKey) return;
      openPlayerDetail({
        leagueKey,
        playerId: player.playerId,
        playerName: player.playerName,
        position: player.position ?? "",
        team: player.team ?? "",
        source,
      });
    },
    [leagueKey, openPlayerDetail, source],
  );
}

export function isPlayerDetailActive(
  active: PlayerDetailTarget | null,
  leagueKey: string | null,
  playerId: string,
): boolean {
  if (!leagueKey) return false;
  return isSamePlayerDetailTarget(active, { leagueKey, playerId, playerName: "", position: "", team: "", source: "" });
}
