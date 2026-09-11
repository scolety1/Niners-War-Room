import type { NwrApiClient } from "@nwr/api-client";
import type { PlayerAvailabilityStatus } from "@nwr/contracts";
import { Button, StatusBadge } from "@nwr/ui";
import { useEffect, useState } from "react";

import { PlayerIdentityHeader } from "./player-drawer-core";
import { usePlayerDetail } from "./player-detail-context";
import {
  derivePlayerDetailBackbone,
  playerAvailabilityBadgeLabel,
  playerAvailabilityBadgeTone,
} from "./player-detail-state";

/**
 * Global Player Detail drawer (NWR pre-UI architecture CLOSURE pass,
 * 2026-09-10, directive section 5). The generalized, league-aware
 * successor to `player-drawer-core.tsx`'s identity-header-only seed --
 * launchable from any surface via `usePlayerDetailOpener` (Lineup and
 * Waivers are wired this pass; see PRODUCT_ARCHITECTURE.md for the exact
 * adoption status/remaining surfaces). Mounted once in `RedraftApp.tsx`,
 * singleton via `PlayerDetailProvider`.
 *
 * Draft Room's own existing `PlayerDrawer` (`draft-room-v2.tsx`) is
 * DELIBERATELY left untouched by this pass -- it is deeply specific to
 * live draft-time data (roster legality, DecisionBundle candidate,
 * queue/draft actions) that has no equivalent outside a draft in
 * progress, and it already reuses this primitive's own
 * `PlayerIdentityHeader`. Migrating it onto this exact context is real,
 * disclosed follow-up work, not silently done here.
 *
 * Renders the shared identity/status backbone
 * (`derivePlayerDetailBackbone`) from the SAME canonical
 * `PlayerAvailabilityStatus` authority every migrated facade surface
 * now attaches to its own rows (see `DATA_AUTHORITY.md`) -- fetched
 * fresh on open, not duplicated from whatever local heuristic the
 * calling page's table might separately render.
 */
export function PlayerDetailDrawer({ client }: { client: NwrApiClient }) {
  const { active, closePlayerDetail } = usePlayerDetail();
  const [statuses, setStatuses] = useState<readonly PlayerAvailabilityStatus[]>([]);

  useEffect(() => {
    if (!active) return;
    let cancelled = false;
    client
      .redraftPlayerAvailabilityStatus()
      .then((result) => {
        if (!cancelled) setStatuses(result.statuses);
      })
      .catch(() => {
        if (!cancelled) setStatuses([]);
      });
    return () => { cancelled = true; };
  }, [client, active?.leagueKey, active?.playerId]);

  if (!active) return null;
  const backbone = derivePlayerDetailBackbone(active, statuses);

  return (
    <aside className="player-drawer" role="dialog" aria-label={`${backbone.identity.playerName} detail`}>
      <PlayerIdentityHeader identity={backbone.identity} onClose={closePlayerDetail} />
      <div className="player-drawer__body">
        <section>
          <h3>Availability status</h3>
          {backbone.status ? (
            <>
              <p>
                <StatusBadge
                  tone={playerAvailabilityBadgeTone(backbone.status)}
                  label={playerAvailabilityBadgeLabel(backbone.status)}
                />
              </p>
              <p>{backbone.status.reason}</p>
              <p>Source: {backbone.status.source} (as of {backbone.status.sourceAsOf})</p>
            </>
          ) : (
            <p className="copy-muted">
              No status issue is recorded for this player in NWR's canonical availability
              authority.
            </p>
          )}
        </section>
        <section>
          <h3>Opened from</h3>
          <p className="copy-muted">{active.source}</p>
        </section>
      </div>
      <div className="player-drawer__actions">
        <Button variant="ghost" onClick={closePlayerDetail}>Close</Button>
      </div>
    </aside>
  );
}
