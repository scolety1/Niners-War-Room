import type { NwrApiClient } from "@nwr/api-client";
import type { PlayerAvailabilityStatus } from "@nwr/contracts";
import { Button, StatusBadge } from "@nwr/ui";
import { useEffect, useRef, useState } from "react";

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
  // NWR UI expansion pass (2026-09-12, Improve Team surface): without this
  // entry, opening the drawer from ANY Improve Team tab would fall back to
  // the raw `active.source` string ("IMPROVE_TEAM") in the "Opened from"
  // line -- exactly the internal-language leak Phase 5 already fixed for
  // every other surface. Found before any live render, by reading this
  // map against the new call site in improve-team.tsx.
  IMPROVE_TEAM: "Improve Team",
  // NWR UI expansion pass (2026-09-12, Trades surface): the new unified
  // `TradesPage` opens the drawer with source "TRADES" from both its
  // ANALYZE and FIND TRADES tabs. TRADE_ANALYSIS/TRADE_FINDER stay mapped
  // below for the pre-existing pages, left in place unrouted.
  TRADES: "Trades",
  TRADE_ANALYSIS: "Trade Analysis",
  TRADE_FINDER: "Trade Finder",
  FREE_AGENTS: "Free Agents",
  OPPONENT_ROSTERS: "Opponent Rosters",
  // NWR UI expansion pass (2026-09-12, League surface): My Roster never had
  // Player Drawer wiring at all before this pass (a real, disclosed gap,
  // not a regression) -- without this entry, opening the drawer from it
  // would fall back to the raw "MY_ROSTER" string, the same
  // internal-language leak class fixed for IMPROVE_TEAM/TRADES/
  // PLAYERS_MARKET. Found before any live render, by reading this map
  // against the new call site in in-season.tsx.
  MY_ROSTER: "My Roster",
  PLAYERS_RANKINGS: "Players / Rankings",
  PLAYERS_TIERS: "Players / Tiers",
  PLAYERS_COMPARE: "Players / Compare",
  // NWR UI expansion pass (2026-09-12, Players surface): the unified
  // Market tab (players.tsx -> adp-providers.tsx's `MarketDataContent`)
  // opens the drawer from a real matched-player row in the ADP import
  // preview table -- without this entry it would fall back to the raw
  // "PLAYERS_MARKET" string, the same internal-language leak class fixed
  // for IMPROVE_TEAM/TRADES. Found before any live render, by reading this
  // map against the new call site.
  PLAYERS_MARKET: "Players / Market",
};

export function PlayerDetailDrawer({ client }: { client: NwrApiClient }) {
  const { active, closePlayerDetail } = usePlayerDetail();
  const [statuses, setStatuses] = useState<readonly PlayerAvailabilityStatus[]>([]);
  // NWR UI expansion pass (2026-09-12, Worker 8 -- failure/degraded
  // states): a real, found-before-any-live-render bug -- the status fetch
  // below silently caught a failure by setting `statuses` to `[]`, the
  // exact SAME shape `derivePlayerDetailBackbone` produces for "the
  // authority has no entry for this player" (a genuine, honest, safe
  // no-issue case). A real endpoint failure (the authority itself
  // unreachable) was therefore indistinguishable from "nothing to flag" --
  // the owner would see a false all-clear instead of an honest "status
  // could not be checked". Tracked separately so the two cases render
  // differently below.
  const [statusUnavailable, setStatusUnavailable] = useState(false);
  const drawerRef = useRef<HTMLElement | null>(null);

  // NWR Work Unit 7 (responsive/a11y hardening): real, reproduced gap --
  // opening this drawer left keyboard focus wherever it already was (the
  // trigger "View" button, still technically focused but now visually
  // behind the drawer overlay), so a keyboard/screen-reader user had no
  // signal they had entered a new dialog and had to Tab blindly to find
  // it. Moves focus onto the dialog itself on open (the standard WAI-ARIA
  // dialog pattern) -- `tabIndex={-1}` below makes the otherwise
  // non-interactive `<aside>` a valid, one-time programmatic focus target
  // without adding it to the normal Tab order.
  useEffect(() => {
    if (!active) return;
    drawerRef.current?.focus();
  }, [active?.playerId, active?.source]);

  // NWR UI expansion pass (2026-09-12, Lineup surface interaction trial):
  // real bug found live -- this global drawer had no Escape-to-close
  // wiring at all (every other dismissible overlay in this app, e.g. the
  // shell's Switch League menu and freshness popover, already closes on
  // Escape). Fixed here once, in the shared primitive, since every
  // surface that opens this same drawer inherits the fix.
  useEffect(() => {
    if (!active) return undefined;
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") closePlayerDetail();
    };
    document.addEventListener("keydown", onEscape);
    return () => document.removeEventListener("keydown", onEscape);
  }, [active, closePlayerDetail]);

  useEffect(() => {
    if (!active) return;
    let cancelled = false;
    setStatusUnavailable(false);
    client
      .redraftPlayerAvailabilityStatus()
      .then((result) => {
        if (!cancelled) setStatuses(result.statuses);
      })
      .catch(() => {
        if (!cancelled) {
          setStatuses([]);
          setStatusUnavailable(true);
        }
      });
    return () => { cancelled = true; };
  }, [client, active?.leagueKey, active?.playerId]);

  if (!active) return null;
  const backbone = derivePlayerDetailBackbone(active, statuses);
  const sourceLabel = SOURCE_LABEL[active.source] ?? active.source;

  return (
    <aside
      className="player-drawer"
      role="dialog"
      aria-label={`${backbone.identity.playerName} detail`}
      tabIndex={-1}
      ref={drawerRef}
    >
      <PlayerIdentityHeader identity={backbone.identity} onClose={closePlayerDetail} />
      <div className="player-drawer__lede" style={{ padding: "0 18px 12px" }}>
        <StatusBadge
          tone={statusUnavailable ? "review" : playerAvailabilityBadgeTone(backbone.status)}
          label={statusUnavailable ? "Status unknown" : playerAvailabilityBadgeLabel(backbone.status)}
        />
        <span className="player-drawer__ownership">Opened from {sourceLabel}</span>
      </div>
      <div className="player-drawer__body">
        <section>
          <h3>Status / News</h3>
          {statusUnavailable ? (
            <p className="copy-muted">
              NWR's canonical availability authority could not be reached, so no status could be
              checked for this player -- this is NOT confirmation that nothing is wrong. Everything
              else in this drawer (identity, opened-from context) is unaffected. Close and reopen
              to retry.
            </p>
          ) : backbone.status ? (
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
