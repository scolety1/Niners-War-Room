import { Button } from "@nwr/ui";

/**
 * Universal player-detail primitive (NWR pre-UI architecture pass,
 * 2026-09-10, directive section 8). PARTIAL/seed this pass, disclosed
 * honestly: this is the shared identity header every player-detail
 * surface should eventually open into, extracted from the existing Draft
 * Room's `PlayerDrawer` (draft-room-v2.tsx) -- the one real, useful
 * player-detail surface this app already has (confirmed by search: no
 * other page had its own player drawer to duplicate or reconcile). This
 * pass proves the primitive by wiring it into that existing drawer,
 * unchanged in behavior/output; it does NOT yet wire a drawer into
 * Lineup/Waivers/Trades/Players/Free Agents/Opponent Rosters -- each of
 * those still shows player detail inline in its own table row. That
 * remaining adoption is real, scoped-down work, not silently dropped --
 * see PRODUCT_ARCHITECTURE.md's "Global player primitive" status.
 */
export interface UniversalPlayerIdentity {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
}

export function PlayerIdentityHeader({
  identity,
  onClose,
}: {
  identity: UniversalPlayerIdentity;
  onClose: () => void;
}) {
  return (
    <div className="player-drawer__header">
      <div>
        <strong>{identity.playerName || identity.playerId}</strong>
        <small>{identity.position} · {identity.team}</small>
      </div>
      <Button variant="ghost" onClick={onClose}>Close</Button>
    </div>
  );
}
