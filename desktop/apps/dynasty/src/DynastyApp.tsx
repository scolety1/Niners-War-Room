import { createNwrClient, NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { CommandItem, DynastyBootstrap, NavigationGroup } from "@nwr/contracts";
import { AppShell, Button, ErrorState, LoadingScreen, WindowChrome } from "@nwr/ui";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { assertDynastyBootstrap } from "./bootstrap-guard";

import {
  ComparePage,
  DataHealthPage,
  DraftCockpitPage,
  HomePage,
  AssetExplorerPage,
  MarketPage,
  PlanningPage,
  PlayerDetailPage,
  RankingsPage,
  RookieReviewPage,
  TeamWorkspacePage,
  TradeLabPage,
} from "./pages";

const NAVIGATION: NavigationGroup[] = [
  { label: "Command", items: [{ label: "Home", path: "/", icon: "home", shortcut: "1" }] },
  {
    label: "Players",
    items: [
      { label: "Dynasty Rankings", path: "/rankings", icon: "board", shortcut: "2" },
      { label: "Asset Explorer", path: "/assets", icon: "players" },
      { label: "Player Detail", path: "/players", icon: "players" },
      { label: "Compare", path: "/compare", icon: "compare", shortcut: "3" },
      { label: "Market Analysis", path: "/market", icon: "market" },
      { label: "Rookie Review", path: "/rookies", icon: "rookie" },
    ],
  },
  {
    label: "Decisions",
    items: [
      { label: "Trade Decision Lab", path: "/trades", icon: "trade", shortcut: "4" },
      { label: "My Board & Decisions", path: "/workspace", icon: "board" },
      { label: "Scenario Playground", path: "/planning", icon: "target" },
    ],
  },
  { label: "Draft", items: [{ label: "Draft Cockpit", path: "/draft", icon: "draft" }] },
  { label: "System", items: [{ label: "Data Health", path: "/data-health", icon: "health" }] },
];

export function DynastyApp() {
  const [client, setClient] = useState<NwrApiClient | null>(null);
  const [data, setData] = useState<DynastyBootstrap | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [attempt, setAttempt] = useState(0);

  const reload = useCallback(() => setAttempt((value) => value + 1), []);

  useEffect(() => {
    let active = true;
    setError(null);
    setRefreshing(true);
    void createNwrClient("dynasty")
      .then(async (nextClient) => {
        const bootstrap = assertDynastyBootstrap(await nextClient.bootstrap<DynastyBootstrap>());
        if (!active) return;
        setClient(nextClient);
        setData(bootstrap);
        setRefreshing(false);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setError(
          reason instanceof NwrApiError
            ? reason
            : new NwrApiError("NWR Dynasty could not initialize its local service."),
        );
        setRefreshing(false);
      });
    return () => { active = false; };
  }, [attempt]);

  const commands = useMemo<CommandItem[]>(() => {
    const navigationCommands = NAVIGATION.flatMap((group) => group.items).map((item) => ({
      id: `nav:${item.path}`,
      label: item.label,
      detail: `Open ${item.label}`,
      path: item.path,
      icon: item.icon,
      keywords: ["tool", "dynasty", "long term"],
    }));
    const assetCommands = (data?.assetOptions ?? []).map((asset) => ({
      id: `asset:${asset.assetId}`,
      label: asset.name,
      detail: `${asset.assetType} · ${asset.rank == null ? "Unranked" : `NWR #${asset.rank}`} · ${asset.team || asset.authority}`,
      path: `/players/${encodeURIComponent(asset.assetId)}`,
      icon: "players",
      keywords: [asset.assetType, asset.position, asset.team, asset.authority, asset.blocked ? "blocked evidence" : "available"],
    }));
    return [...navigationCommands, ...assetCommands];
  }, [data]);

  if (!data && !error) return <div className="standalone-frame"><WindowChrome title="Niners War Room — Dynasty" /><LoadingScreen label="Opening Dynasty command center" /></div>;
  if (!data || !client) {
    return <div className="standalone-frame"><WindowChrome title="Niners War Room — Dynasty" /><div className="standalone-state"><ErrorState message={error?.message ?? "The governed Dynasty service is unavailable."} recovery={error?.recoveryAction} onRetry={reload} /></div></div>;
  }

  const status = data.status;
  return (
    <AppShell
      commands={commands}
      contextLabel="Dynasty · Long term"
      healthLabel={status.ready ? "Decision system ready" : status.tone === "blocked" ? "Evidence blocked" : "Review required"}
      healthTone={status.tone}
      mode="dynasty"
      navigation={NAVIGATION}
      profileLabel={data.product.leagueLabel || "10-team · 1QB"}
      sourceAsOf={data.marketFreshness.sourceAsOf ? `Market ${data.marketFreshness.sourceAsOf}` : status.sourceAsOf}
      title="Niners War Room — Dynasty"
    >
      {error ? <div className="alert-strip alert-strip--blocked refresh-failure" role="alert"><strong>Snapshot refresh failed</strong><span>{error.message} The last successfully loaded Dynasty snapshot remains on screen.</span><Button disabled={refreshing} icon="undo" onClick={reload} variant="secondary">Retry</Button></div> : null}
      {!error && refreshing ? <div aria-live="polite" className="alert-strip refresh-failure"><strong>Refreshing</strong><span>Checking the local Dynasty snapshot…</span></div> : null}
      <Routes>
        <Route path="/" element={<HomePage data={data} />} />
        <Route path="/rankings" element={<RankingsPage data={data} />} />
        <Route path="/assets" element={<AssetExplorerPage data={data} />} />
        <Route path="/players" element={<PlayerDetailPage client={client} data={data} />} />
        <Route path="/players/:assetId" element={<PlayerDetailPage client={client} data={data} />} />
        <Route path="/compare" element={<ComparePage client={client} data={data} />} />
        <Route path="/market" element={<MarketPage data={data} />} />
        <Route path="/rookies" element={<RookieReviewPage data={data} />} />
        <Route path="/trades" element={<TradeLabPage client={client} data={data} />} />
        <Route path="/workspace" element={<TeamWorkspacePage client={client} data={data} />} />
        <Route path="/planning" element={<PlanningPage data={data} />} />
        <Route path="/draft" element={<DraftCockpitPage data={data} />} />
        <Route path="/data-health" element={<DataHealthPage data={data} onReload={reload} />} />
        <Route path="*" element={<Navigate replace to="/" />} />
      </Routes>
    </AppShell>
  );
}
