import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

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

export function PlayerDetailProvider({ children }: { children: ReactNode }) {
  const [active, setActive] = useState<PlayerDetailTarget | null>(null);

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
