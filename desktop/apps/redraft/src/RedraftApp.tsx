import { createNwrClient, NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { CommandItem, NavigationGroup, RedraftBootstrap } from "@nwr/contracts";
import { AppShell, Button, ErrorState, LoadingScreen, WindowChrome } from "@nwr/ui";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { CheatSheetPage } from "./cheat-sheet";
import { ComparePage, DataHealthPage, DraftRoomPage, RankingsPage, TiersPage } from "./pages";
import { ProfilePage } from "./profile";
import { assertRedraftBootstrap } from "./bootstrap-guard";

const NAVIGATION: NavigationGroup[] = [
  { label: "Draft command", items: [{ label: "Draft Room", path: "/", icon: "draft", shortcut: "1" }] },
  { label: "Player board", items: [{ label: "Rankings", path: "/rankings", icon: "board", shortcut: "2" }, { label: "Tiers & Positions", path: "/tiers", icon: "layers" }, { label: "Compare", path: "/compare", icon: "compare", shortcut: "3" }, { label: "Cheat Sheet", path: "/cheat-sheet", icon: "target" }] },
  { label: "League", items: [{ label: "Profile & Scoring", path: "/profile", icon: "settings", shortcut: "4" }] },
  { label: "System", items: [{ label: "Projection & Data Health", path: "/data-health", icon: "health" }] },
];

export function RedraftApp() {
  const [client, setClient] = useState<NwrApiClient | null>(null);
  const [data, setData] = useState<RedraftBootstrap | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  useEffect(() => {
    let active = true;
    setError(null);
    setRefreshing(true);
    void createNwrClient("redraft").then(async (nextClient) => {
      const bootstrap = assertRedraftBootstrap(await nextClient.bootstrap<RedraftBootstrap>());
      if (!active) return;
      setClient(nextClient); setData(bootstrap); setRefreshing(false);
    }).catch((reason: unknown) => { if (active) { setError(reason instanceof NwrApiError ? reason : new NwrApiError("NWR Redraft could not initialize its local service.")); setRefreshing(false); } });
    return () => { active = false; };
  }, [attempt]);
  const update = useCallback((next: RedraftBootstrap) => setData(next), []);
  const commands = useMemo<CommandItem[]>(() => {
    const tools = NAVIGATION.flatMap((group) => group.items).map((item) => ({ id: `nav:${item.path}`, label: item.label, detail: `Open ${item.label}`, path: item.path, icon: item.icon, keywords: ["redraft", "current season"] }));
    const players = (data?.rankings ?? []).map((row) => ({ id: `player:${row.playerId}`, label: row.playerName, detail: `${row.position}${row.positionRank} · #${row.overallRank} · ${row.team}`, path: `/rankings?player=${encodeURIComponent(row.playerId)}`, icon: "players", keywords: [row.position,row.team,`tier ${row.tier}`] }));
    return [...tools, ...players];
  }, [data]);
  if (!data && !error) return <div className="standalone-frame"><WindowChrome title="Niners War Room — Redraft" /><LoadingScreen label="Opening Redraft command center" /></div>;
  if (!data || !client) return <div className="standalone-frame"><WindowChrome title="Niners War Room — Redraft" /><div className="standalone-state"><ErrorState message={error?.message ?? "The governed Redraft service is unavailable."} recovery={error?.recoveryAction} onRetry={reload} /></div></div>;
  return <AppShell commands={commands} contextLabel="Redraft · Current season" healthLabel={data.status.ready ? "Draft board ready" : data.status.tone === "blocked" ? "Projections blocked" : "Review required"} healthTone={data.status.tone} mode="redraft" navigation={NAVIGATION} profileLabel={data.activeProfile?.leagueName ?? "Choose league profile"} sourceAsOf={data.status.sourceAsOf ? `Projections ${data.status.sourceAsOf}` : "Projection date unavailable"} title="Niners War Room — Redraft">
    {error ? <div className="alert-strip alert-strip--blocked refresh-failure" role="alert"><strong>Snapshot refresh failed</strong><span>{error.message} The last successfully loaded Redraft snapshot remains on screen.</span><Button disabled={refreshing} icon="undo" onClick={reload} variant="secondary">Retry</Button></div> : null}
    {!error && refreshing ? <div aria-live="polite" className="alert-strip refresh-failure"><strong>Refreshing</strong><span>Checking the local Redraft snapshot…</span></div> : null}
    <Routes>
      <Route path="/" element={<DraftRoomPage client={client} data={data} onUpdate={update} />} />
      <Route path="/rankings" element={<RankingsPage data={data} />} />
      <Route path="/tiers" element={<TiersPage data={data} />} />
      <Route path="/compare" element={<ComparePage data={data} />} />
      <Route path="/cheat-sheet" element={<CheatSheetPage data={data} />} />
      <Route path="/profile" element={<ProfilePage client={client} data={data} onUpdate={update} />} />
      <Route path="/data-health" element={<DataHealthPage data={data} onReload={reload} />} />
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  </AppShell>;
}
