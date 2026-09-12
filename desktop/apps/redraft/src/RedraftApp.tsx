import { createNwrClient, NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { CommandItem, KhaHistoricalReplayPreview, LeagueLifecycle, LeagueProfile, NavigationGroup, PlayerStatusOverride, RedraftBootstrap } from "@nwr/contracts";
import { AppShell, Button, EmptyState, ErrorState, LoadingScreen, WindowChrome } from "@nwr/ui";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Link, Navigate, Route, Routes, useLocation, useParams } from "react-router-dom";

import { assertRedraftBootstrap } from "./bootstrap-guard";
import { CheatSheetPage } from "./cheat-sheet";
import { legacyRedirectTarget, resolveActiveNavPath, resolveLeagueHomeSubpath, resolveLeagueLifecycle } from "./league-context";
import { LeaguesPage } from "./leagues";
import { DataHealthPage, FreeAgentsPage, OpponentRostersPage, WeeklyToolsPage } from "./pages";
import { LineupPage, MyRosterPage, WeeklyHomePage } from "./in-season";
import { ImproveTeamPage } from "./improve-team";
import { PlayersPage } from "./players";
import { TradesPage } from "./trades";
import { DraftRoomV2Page } from "./draft-room-v2";
import { ProfilePage } from "./profile";
import { PlayerDetailProvider } from "./player-detail-context";
import { PlayerDetailDrawer } from "./player-detail-drawer";
import { FreshnessIndicator, ShellIdentity } from "./shell-identity";

/**
 * NWR UI foundation pass (2026-09-10, directive Phase 3): the canonical
 * owner task map HOME / DRAFT / LINEUP / IMPROVE TEAM / TRADES / PLAYERS /
 * LEAGUE, already documented as the architectural truth in
 * `PRODUCT_ARCHITECTURE.md`'s "Canonical owner task map" (written by the
 * pre-UI structure-freeze pass, never implemented in the nav itself until
 * now). Every route below already existed -- this only relabels/regroups
 * the SAME flat legacy paths the nav always used (each already resolves
 * to the active league's scoped route via `legacyRedirectTarget`) into
 * the canonical buckets, and reorders the buckets by the active league's
 * real lifecycle (directive: "responsive to lifecycle... don't hide
 * routes entirely without strong reason" -- nothing below is hidden,
 * only reordered/labeled).
 */
const NAV_HOME: NavigationGroup = { label: "Home", items: [{ label: "Weekly Home", path: "/league-home", icon: "home" }] };
const NAV_DRAFT: NavigationGroup = { label: "Draft", items: [{ label: "Draft Room", path: "/draft-room-v2", icon: "draft" }] };
const NAV_LINEUP: NavigationGroup = { label: "Lineup", items: [{ label: "Start / Sit", path: "/lineup", icon: "board" }] };
// NWR UI expansion pass (2026-09-12, Improve Team surface): ONE nav item,
// not three -- Waivers/Add-Drop/FAAB/Streamers/Free Agents are now tabs
// inside a single unified `ImproveTeamPage` workspace (see improve-team.tsx)
// rather than separate destinations that only shared a nav group. `/waivers`
// is reused as the entry path unchanged (no route-table/alias churn) --
// its scoped route now renders `ImproveTeamPage` instead of the old
// standalone `WaiversPage` (below).
const NAV_IMPROVE: NavigationGroup = {
  label: "Improve Team",
  items: [{ label: "Improve Team", path: "/waivers", icon: "activity" }],
};
// NWR UI expansion pass (2026-09-12, Trades surface): ONE nav item, not
// two -- Trade Analysis/Trade Finder are now tabs (ANALYZE/FIND TRADES)
// inside a single unified `TradesPage` workspace (see trades.tsx), same
// consolidation shape as Improve Team. `/trade-analysis` is reused as the
// entry path unchanged (no route-table/alias churn) -- its scoped route
// now renders `TradesPage` instead of the old standalone
// `TradeAnalysisPage` (in-season.tsx, left in place unrouted).
const NAV_TRADES: NavigationGroup = {
  label: "Trades",
  items: [{ label: "Trades", path: "/trade-analysis", icon: "trade" }],
};
// NWR UI expansion pass (2026-09-12, Players surface): ONE nav item, not
// four -- Rankings/Tiers & Positions/Compare/Market Data are now tabs
// (RANKINGS/TIERS/COMPARE/MARKET) inside a single unified `PlayersPage`
// workspace (see players.tsx), same consolidation shape as Improve Team
// and Trades. `/rankings` is reused as the entry path unchanged (no
// route-table/alias churn beyond the new `ROUTE_ALIAS_SUBPATH` entries in
// league-context.ts) -- its scoped route now renders `PlayersPage` instead
// of the old standalone `RankingsPage` (pages.tsx, left in place unrouted).
// Cheat Sheet stays its own separate nav item/page -- a different,
// already-unified consumer surface, out of this consolidation's scope.
const NAV_PLAYERS: NavigationGroup = {
  label: "Players",
  items: [
    { label: "Players", path: "/rankings", icon: "board", shortcut: "2" },
    { label: "Cheat Sheet", path: "/cheat-sheet", icon: "target" },
  ],
};
const NAV_LEAGUE: NavigationGroup = {
  label: "League",
  items: [
    { label: "My Roster", path: "/my-roster", icon: "profile" },
    { label: "Opponent Rosters", path: "/opponent-rosters", icon: "layers" },
    { label: "Profile & Scoring", path: "/profile", icon: "settings", shortcut: "4" },
    { label: "Data Health", path: "/data-health", icon: "health" },
  ],
};

/** Lifecycle-aware nav ordering (directive Phase 3): PRE_DRAFT/LIVE_DRAFT
 * make Draft the dominant/current task; IN_SEASON emphasizes Home/Lineup/
 * Improve Team; OFFSEASON shifts toward Draft/Players/League (history,
 * research) per the directive's own wording. No active league yet uses
 * the same order as PRE_DRAFT -- Draft is the very next real task after
 * creating/importing a league. */
function buildNavigation(lifecycle: LeagueLifecycle | null): NavigationGroup[] {
  if (lifecycle === "IN_SEASON") return [NAV_HOME, NAV_LINEUP, NAV_IMPROVE, NAV_TRADES, NAV_PLAYERS, NAV_LEAGUE, NAV_DRAFT];
  if (lifecycle === "OFFSEASON") return [NAV_DRAFT, NAV_PLAYERS, NAV_LEAGUE, NAV_HOME, NAV_LINEUP, NAV_IMPROVE, NAV_TRADES];
  return [NAV_DRAFT, NAV_HOME, NAV_LINEUP, NAV_IMPROVE, NAV_TRADES, NAV_PLAYERS, NAV_LEAGUE];
}

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
  // NWR UI foundation pass (directive Phase 3): the nav is reordered by
  // the active league's real lifecycle, using the exact same shared
  // resolver every other lifecycle-aware surface in this app already
  // uses -- never a second lifecycle heuristic.
  const lifecycle: LeagueLifecycle | null = data?.activeProfile
    ? resolveLeagueLifecycle(data.activeProfile, data.draftBoard)
    : null;
  const navigation = useMemo(() => buildNavigation(lifecycle), [lifecycle]);
  // NWR UI foundation-propagation pass (directive Phase 1, nav-active-
  // route bug fix): resolve which nav item is active from the ONE
  // canonical mapping (`resolveActiveNavPath`) rather than NavLink's own
  // prefix match, which cannot see past the `/league/:leagueKey/...`
  // redirect every legacy flat nav path now goes through -- see
  // league-context.ts for why. `useLocation` here (not `data.activeProfile`
  // routing state) so this reacts to every navigation, including client-
  // side ones that don't reload `data`.
  const location = useLocation();
  const activeNavPath = useMemo(
    () => resolveActiveNavPath(location.pathname, navigation.flatMap((group) => group.items.map((item) => item.path))),
    [location.pathname, navigation],
  );
  const commands = useMemo<CommandItem[]>(() => {
    const tools = navigation.flatMap((group) => group.items).map((item) => ({ id: `nav:${item.path}`, label: item.label, detail: `Open ${item.label}`, path: item.path, icon: item.icon, keywords: ["redraft", "current season"] }));
    const players = (data?.rankings ?? []).map((row) => ({ id: `player:${row.playerId}`, label: row.playerName, detail: `${row.position}${row.positionRank} · #${row.overallRank} · ${row.team}`, path: `/rankings?player=${encodeURIComponent(row.playerId)}`, icon: "players", keywords: [row.position, row.team, `tier ${row.tier}`] }));
    return [...tools, ...players];
  }, [data, navigation]);
  if (!data && !error) return <div className="standalone-frame"><WindowChrome title="Niners War Room — Redraft" /><LoadingScreen label="Opening Redraft command center" /></div>;
  if (!data || !client) return <div className="standalone-frame"><WindowChrome title="Niners War Room — Redraft" /><div className="standalone-state"><ErrorState message={error?.message ?? "The governed Redraft service is unavailable."} recovery={error?.recoveryAction} onRetry={reload} /></div></div>;
  // NWR pre-UI architecture CLOSURE pass (directive section 5):
  // PlayerDetailProvider/PlayerDetailDrawer are mounted ONCE here, above
  // the router -- a true app-wide singleton, so the same player can
  // never show two competing detail drawers regardless of which route
  // opened it, and the drawer survives a route change (e.g. clicking a
  // "View" link inside it) without being unmounted.
  // NWR UI foundation pass (directive Phase 3): league identity now lives
  // in the sidebar's actual top-left (`sidebarIdentity`, under the brand
  // lockup) and the four freshness pills collapse into one quiet header
  // chip (`statusExtra`) -- replacing the old full-width `ActiveLeagueSelector`
  // content-area bar that used to compete with every page's real content.
  return <PlayerDetailProvider><AppShell activeNavPath={activeNavPath} commands={commands} contextLabel={data.activeProfile ? "Redraft workspace" : "Redraft · Choose a league"} healthLabel={data.status.ready ? "Draft board ready" : data.status.tone === "blocked" ? "Projections blocked" : "Review required"} healthTone={data.status.tone} mode="redraft" navigation={navigation} onToggleSidebarCollapsed={toggleSidebarCollapsed} profileLabel={data.activeProfile?.leagueName ?? "Choose league profile"} sidebarCollapsed={sidebarCollapsed} sidebarIdentity={<ShellIdentity client={client} data={data} onUpdate={update} />} sourceAsOf={data.status.sourceAsOf ? `Projections ${data.status.sourceAsOf}` : "Projection date unavailable"} statusExtra={<FreshnessIndicator data={data} />} title="Niners War Room — Redraft">
    <PlayerDetailDrawer client={client} />
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
      {/* NOT a LegacyRedirect: ProfilePage is the create-a-new-league UI
          too (leagues.tsx's "Set up a league" button lands here with NO
          active league yet), so it must stay reachable regardless of
          league-activation state. It also doubles as the active league's
          scoped edit view at /league/:leagueKey/profile below. */}
      <Route path="/profile" element={<ProfilePage client={client} data={data} onUpdate={update} />} />
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
      <Route path="/league/:leagueKey/waivers" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><ImproveTeamPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/improve" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><ImproveTeamPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/my-roster" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><MyRosterPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/league" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><MyRosterPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/trade-analysis" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><TradesPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/trades" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><TradesPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/trade-finder" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><TradesPage client={client} data={data} defaultTab="find" /></LeagueScopedPage>} />
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
      <Route path="/league/:leagueKey/rankings" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><PlayersPage client={client} data={data} onUpdate={update} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/players" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><PlayersPage client={client} data={data} onUpdate={update} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/tiers" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><PlayersPage client={client} data={data} onUpdate={update} defaultTab="tiers" /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/compare" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><PlayersPage client={client} data={data} onUpdate={update} defaultTab="compare" /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/cheat-sheet" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><CheatSheetPage data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/profile" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><ProfilePage client={client} data={data} onUpdate={update} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/adp" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><PlayersPage client={client} data={data} onUpdate={update} defaultTab="market" /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/weekly-tools" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><WeeklyToolsPage client={client} data={data} /></LeagueScopedPage>} />
      <Route path="/league/:leagueKey/data-health" element={<LeagueScopedPage client={client} data={data} onUpdate={update}><DataHealthPage client={client} data={data} onReload={reload} /></LeagueScopedPage>} />

      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  </AppShell></PlayerDetailProvider>;
}

/** Compatibility redirect for a legacy flat path (directive invariant I).
 * Resolves to the SAME sub-page inside the currently active league's
 * scoped route when a league is active; otherwise sends the owner to the
 * league chooser rather than a broken/empty scoped route.
 *
 * NWR UI expansion pass (2026-09-12, Improve Team surface) -- real bug
 * found and fixed: this previously dropped the original URL's query
 * string entirely, so a link like `/waivers?tab=streamers` (Home's own
 * `ACTION_CATEGORY_LINK`, see weekly-shared.tsx) would silently land on
 * `/league/<key>/waivers` with NO `tab` param, defaulting to the wrong
 * tab. Preserving `location.search` through the redirect is what makes
 * every `?tab=...` deep link into the unified Improve Team workspace
 * actually work. */
function LegacyRedirect({ data, subpath }: { data: RedraftBootstrap; subpath: string }) {
  const location = useLocation();
  return <Navigate replace to={`${legacyRedirectTarget(data.activeProfileId, subpath)}${location.search}`} />;
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
        // NWR pre-UI architecture pass -- real bug found live in the
        // rendered acceptance pass (section 12): `setActivating(false)`
        // must run UNCONDITIONALLY here, not gated behind `active`. The
        // `active`/cleanup guard exists to stop a SUPERSEDED request from
        // overwriting fresher data via `onUpdate` -- but reusing that same
        // guard to also suppress clearing the loading spinner meant that
        // whenever this effect's own successful `onUpdate` immediately
        // triggered a re-render (activeProfileId now matching, isActive
        // true), the resulting cleanup set `active = false` BEFORE this
        // `.finally()` ran, so `setActivating(false)` was silently
        // skipped -- and the replacement effect invocation early-returns
        // on `isActive` without ever touching `activating` either. Net
        // effect: "Opening <league>…" never cleared, live-reproduced by
        // switching leagues from the header control. Only reset the
        // in-flight guard for THIS attempt, not a newer superseding one.
        setActivating(false);
        if (inFlightFor.current === leagueKey) inFlightFor.current = null;
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

