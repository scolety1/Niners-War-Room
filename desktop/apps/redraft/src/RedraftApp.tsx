import { createNwrClient, NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { CommandItem, KhaHistoricalReplayPreview, LeagueProfile, NavigationGroup, PlayerStatusOverride, RedraftBootstrap } from "@nwr/contracts";
import { AppShell, Button, ErrorState, LoadingScreen, WindowChrome, EmptyState } from "@nwr/ui";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";

import { assertRedraftBootstrap } from "./bootstrap-guard";
import { AdpProvidersPage } from "./adp-providers";
import { CheatSheetPage } from "./cheat-sheet";
import { leagueFormat, legacyRedirectTarget, resolveLeagueHomeSubpath } from "./league-context";
import { LeaguesPage } from "./leagues";
import { ComparePage, DataHealthPage, FreeAgentsPage, OpponentRostersPage, RankingsPage, TiersPage, WeeklyToolsPage } from "./pages";
import { LineupPage, MyRosterPage, TradeAnalysisPage, TradeFinderPage, WaiversPage, WeeklyHomePage } from "./in-season";
import { DraftRoomV2Page } from "./draft-room-v2";
import { ProfilePage } from "./profile";

const NAVIGATION: NavigationGroup[] = [
  {
    label: "League workspace",
    items: [
      { label: "Weekly Home", path: "/league-home", icon: "home" },
      { label: "Start / Sit", path: "/lineup", icon: "board" },
      { label: "Waivers", path: "/waivers", icon: "activity" },
      { label: "My Roster", path: "/my-roster", icon: "profile" },
      { label: "Free Agents", path: "/free-agents", icon: "players" },
      { label: "Opponent Rosters", path: "/opponent-rosters", icon: "layers" },
      { label: "Trade Analysis", path: "/trade-analysis", icon: "trade" },
      { label: "Trade Finder", path: "/trade-finder", icon: "search" },
    ],
  },
  // Consolidation pass (NWR Draft Room GUI Consolidation): the tabbed room
  // at /draft-room-v2 is the "Draft Room" surface. It originally existed
  // alongside an older single-page "Legacy Draft Room", hidden from this
  // nav/command-palette array (and thus the Ctrl+K palette, both built
  // from it) once the owner started using the new room for a real draft,
  // then kept dormant at "/" as an emergency rollback through that draft.
  // NWR post-draft overnight (phase 23, "remove Legacy for real"): the
  // real draft is complete, capability parity was confirmed (Draft Setup/
  // slot/restart/Refresh FFC ADP/Paste Rankings-ADP/Import owner ADP CSV
  // all already exist here), and the Legacy component itself is now
  // removed from pages.tsx -- "/" redirects to this room instead.
  { label: "Draft command", items: [{ label: "Draft Room", path: "/draft-room-v2", icon: "draft" }] },
  { label: "Player board", items: [{ label: "Rankings", path: "/rankings", icon: "board", shortcut: "2" }, { label: "Tiers & Positions", path: "/tiers", icon: "layers" }, { label: "Compare", path: "/compare", icon: "compare", shortcut: "3" }, { label: "Cheat Sheet", path: "/cheat-sheet", icon: "target" }] },
  { label: "League", items: [{ label: "Profile & Scoring", path: "/profile", icon: "settings", shortcut: "4" }, { label: "Market Data", path: "/adp", icon: "activity" }] },
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
  const location = useLocation();
  const [client, setClient] = useState<NwrApiClient | null>(null);
  const [data, setData] = useState<RedraftBootstrap | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [attempt, setAttempt] = useState(0);
  // These artifacts are global rather than league-scoped. Keep them
  // above the keyed Draft Room route so a league switch cannot clear a
  // shared override list or the fixed historical replay cache.
  const [statusOverrides, setStatusOverrides] = useState<PlayerStatusOverride[]>([]);
  const [statusOverridesReloadKey, setStatusOverridesReloadKey] = useState(0);
  const [historicalReplay, setHistoricalReplay] = useState<KhaHistoricalReplayPreview | null>(null);
  const [historicalReplayLoading, setHistoricalReplayLoading] = useState(false);
  const [historicalReplayError, setHistoricalReplayError] = useState<string | null>(null);
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
  useEffect(() => {
    if (!client) return;
    let cancelled = false;
    client
      .listPlayerStatusOverrides()
      .then((response) => {
        if (!cancelled) setStatusOverrides(response.overrides);
      })
      .catch(() => {
        if (!cancelled) setStatusOverrides([]);
      });
    return () => { cancelled = true; };
  }, [client, statusOverridesReloadKey]);
  const update = useCallback((next: RedraftBootstrap) => setData(next), []);
  const reloadStatusOverrides = useCallback(() => setStatusOverridesReloadKey((key) => key + 1), []);
  const commands = useMemo<CommandItem[]>(() => {
    const tools = NAVIGATION.flatMap((group) => group.items).map((item) => ({ id: `nav:${item.path}`, label: item.label, detail: `Open ${item.label}`, path: item.path, icon: item.icon, keywords: ["redraft", "current season"] }));
    const players = (data?.rankings ?? []).map((row) => ({ id: `player:${row.playerId}`, label: row.playerName, detail: `${row.position}${row.positionRank} · #${row.overallRank} · ${row.team}`, path: `/rankings?player=${encodeURIComponent(row.playerId)}`, icon: "players", keywords: [row.position, row.team, `tier ${row.tier}`] }));
    return [...tools, ...players];
  }, [data]);
  if (!data && !error) return <div className="standalone-frame"><WindowChrome title="Niners War Room — Redraft" /><LoadingScreen label="Opening Redraft command center" /></div>;
  if (!data || !client) return <div className="standalone-frame"><WindowChrome title="Niners War Room — Redraft" /><div className="standalone-state"><ErrorState message={error?.message ?? "The governed Redraft service is unavailable."} recovery={error?.recoveryAction} onRetry={reload} /></div></div>;
  return <AppShell commands={commands} contextLabel={data.activeProfile ? `Redraft · ${leagueFormat(data.activeProfile)}` : "Redraft · Choose a league"} healthLabel={data.status.ready ? "Draft board ready" : data.status.tone === "blocked" ? "Projections blocked" : "Review required"} healthTone={data.status.tone} mode="redraft" navigation={NAVIGATION} onToggleSidebarCollapsed={toggleSidebarCollapsed} profileLabel={data.activeProfile?.leagueName ?? "Choose league profile"} sidebarCollapsed={sidebarCollapsed} sourceAsOf={data.status.sourceAsOf ? `Projections ${data.status.sourceAsOf}` : "Projection date unavailable"} title="Niners War Room — Redraft">
    {location.pathname === "/leagues" ? null : <ActiveLeagueSelector client={client} data={data} onUpdate={update} />}
    {error ? <div className="alert-strip alert-strip--blocked refresh-failure" role="alert"><strong>Snapshot refresh failed</strong><span>{error.message} The last successfully loaded Redraft snapshot remains on screen.</span><Button disabled={refreshing} icon="undo" onClick={reload} variant="secondary">Retry</Button></div> : null}
    {!error && refreshing ? <div aria-live="polite" className="alert-strip refresh-failure"><strong>Refreshing</strong><span>Checking the local Redraft snapshot…</span></div> : null}
    <Routes>
      {/* NWR pre-UI product-architecture hardening pass (2026-09-10,
          directive sections 1/2/7): `/league/:leagueKey/*` is now the
          CANONICAL, deep-linkable route tree -- see LEAGUE_CONTEXT.md.
          Every flat legacy path below (`/lineup`, `/waivers`, ...) is now
          a compatibility redirect INTO that tree, preserving the exact
          same destination page it always rendered (directive invariant
          I). "/" and the league chooser both resolve where to land via
          the lifecycle resolver (`resolveLeagueHomeSubpath`) instead of
          a hardcoded target -- this is the fix for a real, reproduced bug
          this pass found: opening ANY league (including an already-
          in-season one) used to unconditionally navigate to the Draft
          Room (invariant A). */}
      <Route path="/" element={<Navigate replace to={
        data.activeProfileId && data.activeProfile
          ? `/league/${encodeURIComponent(data.activeProfileId)}/${resolveLeagueHomeSubpath(data.activeProfile, data.draftBoard)}`
          : "/leagues"
      } />} />
      <Route path="/leagues" element={<LeaguesPage client={client} data={data} onUpdate={update} />} />

      {/* Compatibility redirects (directive invariant I): each old flat
          path resolves to the SAME sub-page inside the currently active
          league's scoped route -- content is unchanged, only the URL
          gains a real league identity. */}
      <Route path="/league-home" element={<LegacyRedirect data={data} subpath="home" />} />
      <Route path="/lineup" element={<LegacyRedirect data={data} subpath="lineup" />} />
      <Route path="/waivers" element={<LegacyRedirect data={data} subpath="waivers" />} />
      <Route path="/my-roster" element={<LegacyRedirect data={data} subpath="my-roster" />} />
      <Route path="/trade-analysis" element={<LegacyRedirect data={data} subpath="trade-analysis" />} />
      <Route path="/trade-finder" element={<LegacyRedirect data={data} subpath="trade-finder" />} />
      <Route path="/free-agents" element={<LegacyRedirect data={data} subpath="free-agents" />} />
      <Route path="/opponent-rosters" element={<LegacyRedirect data={data} subpath="opponent-rosters" />} />
      <Route path="/draft-room-v2" element={<LegacyRedirect data={data} subpath="draft" />} />
      <Route path="/rankings" element={<LegacyRedirect data={data} subpath="rankings" />} />
      <Route path="/tiers" element={<LegacyRedirect data={data} subpath="tiers" />} />
      <Route path="/compare" element={<LegacyRedirect data={data} subpath="compare" />} />
      <Route path="/cheat-sheet" element={<LegacyRedirect data={data} subpath="cheat-sheet" />} />
      <Route path="/profile" element={<LegacyRedirect data={data} subpath="profile" />} />
      <Route path="/adp" element={<LegacyRedirect data={data} subpath="adp" />} />
      <Route path="/weekly-tools" element={<LegacyRedirect data={data} subpath="weekly-tools" />} />
      <Route path="/data-health" element={<LegacyRedirect data={data} subpath="data-health" />} />

      {/* Canonical league-scoped route tree. `:leagueKey` is the target
          league's profileId -- deep-linking here always resolves that
          SAME league regardless of what was previously globally active
          (directive invariant H), because `LeagueScopedPage` activates it
          on mismatch before rendering anything underneath. Includes the
          section-7 canonical task-map aliases (home/draft/lineup/improve/
          trades/players/league) alongside every existing concrete page so
          no working route is lost -- see PRODUCT_ARCHITECTURE.md. */}
      <Route path="/league/:leagueKey/home" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><WeeklyHomePage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/lineup" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><LineupPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/waivers" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><WaiversPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/improve" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><WaiversPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/my-roster" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><MyRosterPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/league" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><MyRosterPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/trade-analysis" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><TradeAnalysisPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/trades" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><TradeAnalysisPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/trade-finder" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><TradeFinderPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/free-agents" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><FreeAgentsPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/opponent-rosters" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><OpponentRostersPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/draft" element={<LeagueScopedPage client={client} data={data} onUpdate={update}>
        <DraftRoomV2Page
          key={data.activeProfileId ?? "draft-room"}
          client={client}
          data={data}
          onUpdate={update}
          globalSidebarCollapsed={sidebarCollapsed}
          onToggleGlobalSidebarCollapsed={toggleSidebarCollapsed}
          statusOverrides={statusOverrides}
          onStatusOverridesChanged={reloadStatusOverrides}
          historicalReplay={historicalReplay}
          setHistoricalReplay={setHistoricalReplay}
          historicalReplayLoading={historicalReplayLoading}
          setHistoricalReplayLoading={setHistoricalReplayLoading}
          historicalReplayError={historicalReplayError}
          setHistoricalReplayError={setHistoricalReplayError}
        />
      </LeagueScopedPage>} />
      <Route path="/league/:leagueKey/rankings" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><RankingsPage data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/players" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><RankingsPage data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/tiers" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><TiersPage data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/compare" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><ComparePage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/cheat-sheet" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><CheatSheetPage data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/profile" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><ProfilePage client={client} data={data} onUpdate={update} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/adp" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><AdpProvidersPage client={client} data={data} onUpdate={update} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/weekly-tools" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><WeeklyToolsPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/data-health" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><DataHealthPage client={client} data={data} onReload={reload} /></LeagueScopedPage>} />

      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  </AppShell>;
}

/** Compatibility redirect for a legacy flat path (directive invariant I).
 * Resolves to the SAME sub-page inside the currently active league's
 * scoped route when a league is active; otherwise sends the owner to the
 * league chooser rather than a broken/empty scoped route. */
function LegacyRedirect({ data, subpath }: { data: RedraftBootstrap; subpath: string }) {
  return <Navigate replace to={legacyRedirectTarget(data.activeProfileId, subpath)} />;
}

/** ONE gate every league-scoped route passes through (directive section 1,
 * invariant H: "a deep link always resolves the same league"). Reads
 * `:leagueKey` from the URL, and:
 * - unknown leagueKey -> an honest "League not found" state, never a
 *   silently wrong league.
 * - known but not currently active -> activates it (a real API call,
 *   `activateRedraftProfile`) before rendering anything underneath, so a
 *   deep link or a bookmark can never show stale data from whatever
 *   league happened to be active before (invariant G).
 * - already active -> renders immediately, no extra round trip.
 * The rendered subtree is keyed by `leagueKey` so page-local state (a
 * selected week, a search query, ...) never survives a league switch. */
function LeagueScopedPage({
  client,
  data,
  onUpdate,
  children,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
  children: ReactNode;
}) {
  const { leagueKey } = useParams<{ leagueKey: string }>();
  const [activating, setActivating] = useState(false);
  const [activationError, setActivationError] = useState<string | null>(null);
  const inFlightFor = useRef<string | null>(null);
  const targetProfile: LeagueProfile | undefined = data.profiles.find(
    (profile) => profile.profileId === leagueKey,
  );
  const isActive = Boolean(leagueKey) && data.activeProfileId === leagueKey;

  useEffect(() => {
    if (!leagueKey || !targetProfile || isActive) return undefined;
    if (inFlightFor.current === leagueKey) return undefined;
    inFlightFor.current = leagueKey;
    setActivating(true);
    setActivationError(null);
    let active = true;
    void client
      .activateRedraftProfile(leagueKey)
      .then((next) => {
        if (!active) return;
        onUpdate(next);
      })
      .catch(() => {
        if (active) setActivationError("This league could not be opened. It may have been removed.");
      })
      .finally(() => {
        if (active) setActivating(false);
        inFlightFor.current = null;
      });
    return () => {
      active = false;
    };
  }, [client, leagueKey, targetProfile, isActive, onUpdate]);

  if (!leagueKey || !targetProfile) {
    return (
      <EmptyState
        icon="alert"
        title="League not found"
        message="This league link doesn't match any saved profile. It may have been removed or renamed."
        action={<Link to="/leagues">Open league chooser</Link>}
      />
    );
  }
  if (activationError) {
    return <ErrorState message={activationError} recovery="Open the league chooser and select the league again." />;
  }
  if (!isActive || activating) {
    return <LoadingScreen label={`Opening ${targetProfile.leagueName}…`} />;
  }
  return <div key={leagueKey}>{children}</div>;
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
  // NWR DRAFT-DAY CONFIGURATION (section 12, "Fix the Switch League
  // control"): a native <select> was the underlying problem -- its own
  // OPEN dropdown popup sizes itself to the widest option text (a full,
  // never-truncated league name, e.g.
  // "TEMPORARY_QA_CONFIG_UNVERIFIED_REAL_LEAGUE_SETTINGS (10-team)") with
  // no CSS override available in any browser, so it rendered far wider
  // than the compact header and clipped/overflowed at the owner's real
  // desktop width no matter how the closed control itself was bounded.
  // Replaced with a compact button + our own bounded menu, so both the
  // closed affordance and the open menu stay inside a fixed max-width
  // with the league list scrolling internally instead of stretching the
  // header.
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const active = data.activeProfile;
  const location = useLocation();
  const navigate = useNavigate();
  const switchLeague = async (profileId: string) => {
    if (!profileId || profileId === data.activeProfileId || working) return;
    setMenuOpen(false);
    setWorking(true); setError("");
    // NWR pre-UI architecture pass (directive invariant G, "switching
    // leagues cannot leak prior league state"): if the owner is on a
    // league-scoped deep link (`/league/<old>/...`), rewrite the URL's
    // league-key segment to the NEW profile FIRST, before activation
    // resolves -- otherwise `LeagueScopedPage` would see a URL still
    // naming the old league and try to reactivate it right back,
    // fighting this switch. Any other (legacy flat) path is left alone;
    // its page re-renders from the new `data` once `onUpdate` resolves.
    const pathSegments = location.pathname.split("/");
    if (pathSegments[1] === "league" && pathSegments[2]) {
      const rest = pathSegments.slice(3).join("/");
      navigate(`/league/${encodeURIComponent(profileId)}/${rest}${location.search}`, { replace: true });
    }
    try { onUpdate(await client.activateRedraftProfile(profileId)); }
    catch { setError("League switch could not be saved. The current workspace remains active."); }
    finally { setWorking(false); }
  };
  useEffect(() => {
    if (!menuOpen) return undefined;
    const onOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setMenuOpen(false);
    };
    const onEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setMenuOpen(false); };
    document.addEventListener("mousedown", onOutside);
    document.addEventListener("keydown", onEscape);
    return () => {
      document.removeEventListener("mousedown", onOutside);
      document.removeEventListener("keydown", onEscape);
    };
  }, [menuOpen]);
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
      <Link className="active-league-selector__chooser-link" title="Open league chooser" to="/leagues">
        <strong title={active?.leagueName ?? undefined}>{active?.leagueName ?? "Choose a league"}</strong>
      </Link>
      <small>{active ? leagueFormat(active, false) : "Create or import a Redraft league profile"}</small>
      {error ? <em role="status">{error}</em> : null}
    </div>
    <div className="active-league-selector__switch" ref={menuRef}>
      <button
        type="button"
        className="active-league-selector__switch-btn"
        disabled={working || !data.profiles.length}
        aria-haspopup="listbox"
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen((open) => !open)}
      >
        Switch league <span aria-hidden="true">{menuOpen ? "▴" : "▾"}</span>
      </button>
      {menuOpen ? (
        <ul className="active-league-selector__switch-menu" role="listbox" aria-label="Available leagues">
          {data.profiles.map((profile) => {
            const isActive = profile.profileId === data.activeProfileId;
            return (
              <li key={profile.profileId}>
                <button
                  type="button"
                  role="option"
                  aria-selected={isActive}
                  className={isActive ? "active-league-selector__switch-option active-league-selector__switch-option--active" : "active-league-selector__switch-option"}
                  title={profile.leagueName}
                  onClick={() => void switchLeague(profile.profileId)}
                >
                  {profile.leagueName}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
    <div className="active-league-selector__badges">
      <span className={data.health?.playerUniverseAvailable ? "active-league-adp" : "active-league-adp active-league-adp--review"} title="Real, current-team player identity data -- separate from projections, ADP, and news freshness.">{identityLabel}</span>
      <span className={`active-league-adp ${adp?.available ? "" : "active-league-adp--review"}`}>{adpLabel}</span>
      <span className="active-league-adp">{projectionsLabel}</span>
      <span className={data.status.ready ? "active-league-ready" : "active-league-adp active-league-adp--review"}>{readyLabel}</span>
    </div>
  </section>;
}
