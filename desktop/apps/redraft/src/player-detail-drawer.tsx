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
 * 2026-09-10, directive section 5; visual grammar added by the
 * `ui/nwr-visual-redesign-v1` pass, directive Phase 5). The generalized,
 * league-aware successor to `player-drawer-core.tsx`'s identity-header-only
 * seed -- launchable from any surface via `usePlayerDetailOpener` (Lineup,
 * Waivers, Trade Analysis, Trade Finder, Free Agents, Opponent Rosters,
 * Players/Rankings-Tiers-Compare; see PRODUCT_ARCHITECTURE.md for the full
 * adoption table). Mounted once in `RedraftApp.tsx`, singleton via
 * `PlayerDetailProvider`.
 *
 * Draft Room's own existing `PlayerDrawer` (`draft-room-v2.tsx`) is
 * DELIBERATELY left untouched -- deeply specific to live draft-time data
 * (roster legality, DecisionBundle candidate, queue/draft actions) with no
 * equivalent outside a draft in progress.
 *
 * Visual grammar (this pass): header (identity + availability badge,
 * inline) -> STATUS / NEWS (primary, always visible) -> OPENED FROM (a
 * plain-language label for which surface launched this, no raw internal
 * source code) -> ADVANCED (collapsed by default: the raw provenance
 * fields -- player id, raw status category, raw source timestamp).
 * Everything rendered here reads the SAME canonical
 * `PlayerAvailabilityStatus` authority every migrated facade surface
 * already attaches to its own rows -- fetched fresh on open, never
 * duplicated from a calling page's own table.
 *
 * Honest, disclosed scope limit: this primitive currently carries
 * identity + availability status only. The directive's fuller vision
 * (THIS WEEK / ROS / ROSTER FIT / MARKET context-specific sections) needs
 * new per-surface data plumbing this presentation-only pass does not add
 * (see the UI foundation handoff notes) -- rather than fabricate those
 * sections with placeholder content, this drawer shows exactly what is
 * real today, cleanly.
 */

const SOURCE_LABEL: Record<string, string> = {
  LINEUP: "Start / Sit",
  WAIVER: "Waivers",
  TRADE_ANALYSIS: "Trade Analysis",
  TRADE_FINDER: "Trade Finder",
  FREE_AGENTS: "Free Agents",
  OPPONENT_ROSTERS: "Opponent Rosters",
  PLAYERS_RANKINGS: "Players / Rankings",
  PLAYERS_TIERS: "Players / Tiers",
  PLAYERS_COMPARE: "Players / Compare",
};

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
  const sourceLabel = SOURCE_LABEL[active.source] ?? active.source;

  return (
    <aside className="player-drawer" role="dialog" aria-label={`${backbone.identity.playerName} detail`}>
      <PlayerIdentityHeader identity={backbone.identity} onClose={closePlayerDetail} />
      <div className="player-drawer__lede" style={{ padding: "0 18px 12px" }}>
        <StatusBadge
          tone={playerAvailabilityBadgeTone(backbone.status)}
          label={playerAvailabilityBadgeLabel(backbone.status)}
        />
        <span className="player-drawer__ownership">Opened from {sourceLabel}</span>
      </div>
      <div className="player-drawer__body">
        <section>
          <h3>Status / News</h3>
          {backbone.status ? (
            <>
              <p className="nwr-text-body">{backbone.status.reason}</p>
              <p className="copy-muted">Source: {backbone.status.source} · as of {backbone.status.sourceAsOf}</p>
            </>
          ) : (
            <p className="copy-muted">
              No status issue is recorded for this player in NWR's canonical availability
              authority -- a real, honest "nothing to flag" state.
            </p>
          )}
        </section>
        <details className="player-drawer__section">
          <summary>Advanced / provenance</summary>
          <dl className="health-list">
            <div><dt>Player ID</dt><dd>{backbone.identity.playerId}</dd></div>
            {backbone.status ? (
              <>
                <div><dt>Status category</dt><dd>{backbone.status.statusCategory}</dd></div>
                <div><dt>Override kind</dt><dd>{backbone.status.overrideKind}</dd></div>
                {backbone.status.currentTeam ? <div><dt>Current team (authority)</dt><dd>{backbone.status.currentTeam}</dd></div> : null}
              </>
            ) : null}
            <div><dt>Opened from (raw)</dt><dd>{active.source}</dd></div>
          </dl>
        </details>
      </div>
      <div className="player-drawer__actions">
        <Button variant="ghost" onClick={closePlayerDetail}>Close</Button>
      </div>
    </aside>
  );
}
