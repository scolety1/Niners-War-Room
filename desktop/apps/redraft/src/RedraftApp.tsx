import { createNwrClient, NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { CommandItem, NavigationGroup, RedraftBootstrap } from "@nwr/contracts";
import { AppShell, Button, ErrorState, LoadingScreen, WindowChrome } from "@nwr/ui";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { assertRedraftBootstrap } from "./bootstrap-guard";
import { AdpProvidersPage } from "./adp-providers";
import { CheatSheetPage } from "./cheat-sheet";
import { leagueFormat } from "./league-context";
import { ComparePage, DataHealthPage, DraftRoomPage, RankingsPage, TiersPage, WeeklyToolsPage } from "./pages";
import { DraftRoomV2Page } from "./draft-room-v2";
import { ProfilePage } from "./profile";

const NAVIGATION: NavigationGroup[] = [
  // Consolidation pass (NWR Draft Room GUI Consolidation): the tabbed room
  // at /draft-room-v2 is now the primary "Draft Room" surface; the
  // original single-page room stays reachable, unmodified, as the
  // "Legacy Draft Room" fallback -- routes are intentionally unchanged
  // ("/" still resolves to the legacy page) so no existing bookmark,
  // keyboard shortcut, or hash link breaks the night before a real draft.
  { label: "Draft command", items: [{ label: "Draft Room", path: "/draft-room-v2", icon: "draft" }, { label: "Legacy Draft Room", path: "/", icon: "draft", shortcut: "1" }] },
  { label: "Player board", items: [{ label: "Rankings", path: "/rankings", icon: "board", shortcut: "2" }, { label: "Tiers & Positions", path: "/tiers", icon: "layers" }, { label: "Compare", path: "/compare", icon: "compare", shortcut: "3" }, { label: "Cheat Sheet", path: "/cheat-sheet", icon: "target" }] },
  { label: "League", items: [{ label: "Profile & Scoring", path: "/profile", icon: "settings", shortcut: "4" }, { label: "ADP Providers", path: "/adp", icon: "activity" }] },
  { label: "Weekly tools", items: [{ label: "K/DST Streamer", path: "/weekly-tools", icon: "target" }] },
  { label: "System", items: [{ label: "Projection & Data Health", path: "/data-health", icon: "health" }] },
];

const SIDEBAR_COLLAPSED_STORAGE_KEY = "nwr-redraft-sidebar-collapsed";

function readStoredSidebarCollapsed(): boolean {
  try {
    return window.localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY) === "1";
  } catch {
    return false; // localStorage can throw (private mode, blocked storage) -- default to expanded, never crash the shell.
  }
}

export function RedraftApp() {
  const [client, setClient] = useState<NwrApiClient | null>(null);
  const [data, setData] = useState<RedraftBootstrap | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [attempt, setAttempt] = useState(0);
  // Global sidebar collapse (owner requirement: maximum horizontal room
  // during a live draft). Persisted across sessions the same way any
  // per-viewer UI preference would be -- see readStoredSidebarCollapsed.
  const [sidebarCollapsed, setSidebarCollapsed] = useState(readStoredSidebarCollapsed);
  const toggleSidebarCollapsed = useCallback(() => {
    setSidebarCollapsed((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(SIDEBAR_COLLAPSED_STORAGE_KEY, next ? "1" : "0");
      } catch {
        // Best-effort persistence only -- the toggle still works this session either way.
      }
      return next;
    });
  }, []);
  const reload = useCallback(() => setAttempt((value) => value + 1), []);
  useEffect(() => {
    let active = true;
    setError(null);
    setRefreshing(true);
    void createNwrClient("redraft").then(async (nextClient) => {
      const bootstrap = assertRedraftBootstrap(await nextClient.bootstrap<RedraftBootstrap>());
      if (!active) return;
      setClient(nextClient); setData(bootstrap); setRefreshing(false);
    }).catch((reason: unknown) => {
      if (active) {
        setError(reason instanceof NwrApiError ? reason : new NwrApiError("NWR Redraft could not initialize its local service."));
        setRefreshing(false);
      }
    });
    return () => { active = false; };
  }, [attempt]);
  const update = useCallback((next: RedraftBootstrap) => setData(next), []);
  const commands = useMemo<CommandItem[]>(() => {
    const tools = NAVIGATION.flatMap((group) => group.items).map((item) => ({ id: `nav:${item.path}`, label: item.label, detail: `Open ${item.label}`, path: item.path, icon: item.icon, keywords: ["redraft", "current season"] }));
    const players = (data?.rankings ?? []).map((row) => ({ id: `player:${row.playerId}`, label: row.playerName, detail: `${row.position}${row.positionRank} · #${row.overallRank} · ${row.team}`, path: `/rankings?player=${encodeURIComponent(row.playerId)}`, icon: "players", keywords: [row.position, row.team, `tier ${row.tier}`] }));
    return [...tools, ...players];
  }, [data]);
  if (!data && !error) return <div className="standalone-frame"><WindowChrome title="Niners War Room — Redraft" /><LoadingScreen label="Opening Redraft command center" /></div>;
  if (!data || !client) return <div className="standalone-frame"><WindowChrome title="Niners War Room — Redraft" /><div className="standalone-state"><ErrorState message={error?.message ?? "The governed Redraft service is unavailable."} recovery={error?.recoveryAction} onRetry={reload} /></div></div>;
  return <AppShell commands={commands} contextLabel={data.activeProfile ? `Redraft · ${leagueFormat(data.activeProfile)}` : "Redraft · Choose a league"} healthLabel={data.status.ready ? "Draft board ready" : data.status.tone === "blocked" ? "Projections blocked" : "Review required"} healthTone={data.status.tone} mode="redraft" navigation={NAVIGATION} onToggleSidebarCollapsed={toggleSidebarCollapsed} profileLabel={data.activeProfile?.leagueName ?? "Choose league profile"} sidebarCollapsed={sidebarCollapsed} sourceAsOf={data.status.sourceAsOf ? `Projections ${data.status.sourceAsOf}` : "Projection date unavailable"} title="Niners War Room — Redraft">
    <ActiveLeagueSelector client={client} data={data} onUpdate={update} />
    {error ? <div className="alert-strip alert-strip--blocked refresh-failure" role="alert"><strong>Snapshot refresh failed</strong><span>{error.message} The last successfully loaded Redraft snapshot remains on screen.</span><Button disabled={refreshing} icon="undo" onClick={reload} variant="secondary">Retry</Button></div> : null}
    {!error && refreshing ? <div aria-live="polite" className="alert-strip refresh-failure"><strong>Refreshing</strong><span>Checking the local Redraft snapshot…</span></div> : null}
    <Routes>
      <Route path="/" element={<DraftRoomPage client={client} data={data} onUpdate={update} />} />
      <Route path="/draft-room-v2" element={<DraftRoomV2Page client={client} data={data} onUpdate={update} globalSidebarCollapsed={sidebarCollapsed} onToggleGlobalSidebarCollapsed={toggleSidebarCollapsed} />} />
      <Route path="/rankings" element={<RankingsPage data={data} />} />
      <Route path="/tiers" element={<TiersPage data={data} />} />
      <Route path="/compare" element={<ComparePage data={data} />} />
      <Route path="/cheat-sheet" element={<CheatSheetPage data={data} onImportUdk={(file) => { if (file && client && data.activeProfileId) void file.text().then((csvText) => client.importUdkRankings(data.activeProfileId!, csvText)).then(update); }} />} />
      <Route path="/profile" element={<ProfilePage client={client} data={data} onUpdate={update} />} />
      <Route path="/adp" element={<AdpProvidersPage client={client} data={data} onUpdate={update} />} />
      <Route path="/weekly-tools" element={<WeeklyToolsPage client={client} data={data} />} />
      <Route path="/data-health" element={<DataHealthPage data={data} onReload={reload} />} />
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  </AppShell>;
}

/** NWR FINAL OWNER-FEEDBACK RECONCILIATION (P0, "Active League header
 * cleanup"): the owner's screenshot showed a broken box -- the full
 * league/profile name repeated (once as a large heading, again inside the
 * Switch selector's own selected-option text), an ADP badge overlapping
 * the Switch control, no Projections freshness (shown elsewhere, in the
 * window title bar only), and a "Draft board ready" badge that was
 * HARD-CODED to always read ready regardless of real status. This is now
 * the one compact row the owner specified: League/Practice Name (ellipsis
 * + full-name tooltip, never a raw technical ID in prime text) · compact
 * league format · Switch · ADP status · Projections status · real
 * draft-board-ready status. */
function ActiveLeagueSelector({ client, data, onUpdate }: { client: NwrApiClient; data: RedraftBootstrap; onUpdate: (data: RedraftBootstrap) => void }) {
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const active = data.activeProfile;
  const switchLeague = async (profileId: string) => {
    if (!profileId || profileId === data.activeProfileId || working) return;
    setWorking(true); setError("");
    try { onUpdate(await client.activateRedraftProfile(profileId)); }
    catch { setError("League switch could not be saved. The current workspace remains active."); }
    finally { setWorking(false); }
  };
  const adp = data.draftBoard?.adp;
  const adpLabel = adp?.available ? `ADP: ${adp.source.replace(/^Owner-imported /i, "Owner ")} · ${adp.freshness ?? "cached"}` : "ADP: unavailable";
  const projectionsLabel = data.status.sourceAsOf ? `Projections: ${data.status.sourceAsOf}` : "Projections: unavailable";
  const readyLabel = data.status.ready ? "Draft board ready" : data.status.tone === "blocked" ? "Projections blocked" : "Review required";
  // NWR FINAL OWNER-FEEDBACK CLOSURE (section 9, "Freshness -- all four
  // categories"): Identity/Team is a REAL, already-computed signal
  // (`health.playerUniverseAvailable` + `health.lastGeneratedTimestamp`)
  // that previously had no owner-facing surface at all -- never
  // fabricated, never merged with Projections (a separate, independently
  // stale/fresh field). News/status freshness already has its own real,
  // separate surface (the "News Nh stale" chip in Suggestions) -- kept
  // there rather than duplicated here, so this row stays compact instead
  // of growing back into the giant box the owner already rejected.
  const identityLabel = data.health?.playerUniverseAvailable
    ? `Identity: ${data.health.lastGeneratedTimestamp || "current"}`
    : "Identity: unavailable";
  return <section className="active-league-selector" aria-label="Active League">
    <div className="active-league-selector__identity">
      <span>Active League</span>
      <strong title={active?.leagueName ?? undefined}>{active?.leagueName ?? "Choose a league"}</strong>
      <small>{active ? leagueFormat(active, false) : "Create or import a Redraft league profile"}</small>
      {error ? <em role="status">{error}</em> : null}
    </div>
    <label><span>Switch</span><select aria-label="Switch active league" disabled={working || !data.profiles.length} value={data.activeProfileId ?? ""} onChange={(event) => void switchLeague(event.target.value)}>{!data.activeProfileId ? <option value="">Choose a league</option> : null}{data.profiles.map((profile) => <option key={profile.profileId} value={profile.profileId} title={profile.leagueName}>{profile.leagueName}</option>)}</select></label>
    <div className="active-league-selector__badges">
      <span className={data.health?.playerUniverseAvailable ? "active-league-adp" : "active-league-adp active-league-adp--review"} title="Real, current-team player identity data -- separate from projections, ADP, and news freshness.">{identityLabel}</span>
      <span className={`active-league-adp ${adp?.available ? "" : "active-league-adp--review"}`}>{adpLabel}</span>
      <span className="active-league-adp">{projectionsLabel}</span>
      <span className={data.status.ready ? "active-league-ready" : "active-league-adp active-league-adp--review"}>{readyLabel}</span>
    </div>
  </section>;
}
