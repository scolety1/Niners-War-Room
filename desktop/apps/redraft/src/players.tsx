import type { NwrApiClient } from "@nwr/api-client";
import type { RedraftBootstrap } from "@nwr/contracts";
import { PageHeader, StatusBadge } from "@nwr/ui";
import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

import { MarketDataContent } from "./adp-providers";
import { leagueFormat } from "./league-context";
import { CompareContent, RankingsContent, TiersContent } from "./pages";

/**
 * NWR UI expansion pass (2026-09-12, Players surface): ONE coherent owner
 * workspace answering "What do I need to know about this player / the
 * player market?", unifying the previously separately-built Rankings /
 * Tiers & Positions / Compare / Market Data pages under a single set of
 * tabs (RANKINGS / TIERS / COMPARE / MARKET) -- same consolidation shape as
 * `improve-team.tsx` and `trades.tsx`. Presentation-layer only, over the
 * exact same frozen contracts those pages already read (`data.rankings`,
 * `redraftWeeklyProjections`, `redraftWaivers`, `redraftMyRoster`, the ADP/
 * Ballers import client methods) -- no new ranking/rating math, no scoring
 * change. Cheat Sheet is a deliberately SEPARATE nav item/page (its own
 * already-unified consumer surface, see `cheat-sheet.tsx` and the
 * "Combined Cheat Sheet V1" ledger entry) -- out of this surface's scope
 * per the directive's own SEARCH/RANKINGS/TIERS/COMPARE/MARKET-ADP list.
 *
 * "Search" is not a sixth tab: Rankings' own inline search box (filters
 * the same governed board in place) already serves that need and is kept
 * where it lives rather than duplicated at the workspace level -- no other
 * tab here had its own player-name search box to begin with, so there was
 * no real redundant control to remove. The app's global Ctrl+K command
 * palette (RedraftApp.tsx) is the actual "global search" the directive
 * asks to "naturally lead into this area" -- its player entries already
 * point at `/rankings?player=<id>`, which now lands on this workspace's
 * Rankings tab (the default) with that player's name pre-filled into the
 * exact same search box, unchanged.
 *
 * `RankingsPage`/`TiersPage`/`ComparePage`/`AdpProvidersPage` (pages.tsx /
 * adp-providers.tsx) are left in place as unrouted legacy fallbacks, same
 * precedent as `WaiversPage` after the Improve Team pass -- no route in
 * RedraftApp.tsx points to any of them any more.
 */

type PlayersTab = "rankings" | "tiers" | "compare" | "market";

const PLAYERS_TABS: Array<{ key: PlayersTab; label: string }> = [
  { key: "rankings", label: "Rankings" },
  { key: "tiers", label: "Tiers" },
  { key: "compare", label: "Compare" },
  { key: "market", label: "Market" },
];

export function PlayersPage({
  client,
  data,
  onUpdate,
  defaultTab = "rankings",
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
  defaultTab?: PlayersTab;
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get("tab");
  const tab: PlayersTab = PLAYERS_TABS.some((item) => item.key === tabParam) ? (tabParam as PlayersTab) : defaultTab;
  const setTab = useCallback(
    (next: PlayersTab) => {
      const nextParams = new URLSearchParams(searchParams);
      nextParams.set("tab", next);
      setSearchParams(nextParams, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const activeFormat = data.activeProfile ? leagueFormat(data.activeProfile, false) : "Choose a league profile";

  return <>
    <PageHeader
      eyebrow={activeFormat}
      title="Players"
      description="What do I need to know about this player, or the player market? Rankings, Tiers, Compare, and Market Data -- one research surface over the same governed board."
      status={<StatusBadge tone={data.rankings.length ? "safe" : "blocked"} label={`${data.rankings.length} ranked players`} />}
    />
    <nav aria-label="Players sections" className="nwr-tabbar" role="tablist">
      {PLAYERS_TABS.map((item) => (
        <button
          aria-selected={tab === item.key}
          className={`nwr-tabbar__tab${tab === item.key ? " nwr-tabbar__tab--active" : ""}`}
          key={item.key}
          onClick={() => setTab(item.key)}
          role="tab"
          type="button"
        >
          {item.label}
        </button>
      ))}
    </nav>

    {tab === "rankings" ? <RankingsContent data={data} /> : null}
    {tab === "tiers" ? <TiersContent data={data} /> : null}
    {tab === "compare" ? <CompareContent client={client} data={data} /> : null}
    {tab === "market" ? <MarketDataContent client={client} data={data} onUpdate={onUpdate} /> : null}
  </>;
}
