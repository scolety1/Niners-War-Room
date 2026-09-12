import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { DataHealthReport, LeagueWorkspaceContext, RedraftBootstrap } from "@nwr/contracts";
import { Button, EmptyState, ErrorState, PageHeader, Panel, StatusBadge } from "@nwr/ui";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { MyRosterContent } from "./in-season";
import { leagueFormat, leagueIdentityFormat, providerFormat, scoringFormat } from "./league-context";
import { formatCurrentWeek, rosterCompositionRows, scoringSummaryGroups, syncHealthLabel, syncHealthTone } from "./league-summary";
import { dataHealthTone, OpponentRostersContent } from "./pages";
import { editableProfile, ProfileEditor, type EditableProfile } from "./profile";
import { useAsync } from "./weekly-shared";

/**
 * NWR UI expansion pass (2026-09-12, League surface): ONE coherent owner
 * workspace answering "What is this league/team context?", unifying the
 * previously separately-built My Roster / Opponent Rosters / Profile &
 * Scoring pages into OVERVIEW / MY ROSTER / TEAMS / SCORING / SETTINGS /
 * SYNC tabs -- same consolidation shape as `players.tsx`/`improve-team.tsx`/
 * `trades.tsx`. Presentation-layer only, over the exact same frozen
 * contracts those pages already read (`LeagueProfile`, `RedraftMyRosterResult`,
 * `RedraftOpponentRostersResult`, `RedraftProfileUpdateInput`) plus one
 * genuinely new, previously-unused-anywhere read: `LeagueWorkspaceContext`
 * (`currentWeek`/`syncStatus`/`syncAsOf`/`issues`) -- read-only, its
 * semantics are the hard-boundary authority this pass does not touch.
 *
 * `ProfilePage` (profile.tsx) is a DELIBERATELY separate surface, not
 * folded in here: it doubles as the create-a-new-league / import-a-Sleeper-
 * league / switch-between-profiles flow, which is "manage MY LEAGUES"
 * (plural), not "what is THIS league" (singular) -- the directive's own
 * framing. It stays reachable at its own nav item ("Manage Leagues") and
 * route. This workspace's SETTINGS tab reuses `ProfileEditor` +
 * `editableProfile` directly from that file (both gained `export` for this
 * reuse) -- the exact same roster/scoring/draft-settings form and
 * `updateRedraftProfile` contract call, not a second drifting editor.
 *
 * "Data Health" (pages.tsx's `DataHealthPage`) also stays a separate nav
 * item -- it is a genuinely broader, whole-system diagnostic (weekly/ROS
 * projections, market ADP, player status, decision engine, snapshot) that
 * is not specific to "this league's own context"; only its real
 * `LEAGUE_SYNC` category is reused here (SYNC tab), read via the exact
 * same `client.redraftDataHealth()` call and `dataHealthTone` mapping that
 * page already uses.
 */

export type LeagueTab = "overview" | "roster" | "teams" | "scoring" | "settings" | "sync";

const LEAGUE_TABS: Array<{ key: LeagueTab; label: string }> = [
  { key: "overview", label: "Overview" },
  { key: "roster", label: "My Roster" },
  { key: "teams", label: "Teams" },
  { key: "scoring", label: "Scoring" },
  { key: "settings", label: "Settings" },
  { key: "sync", label: "Sync" },
];

export function LeagueWorkspacePage({
  client,
  data,
  onUpdate,
  defaultTab = "overview",
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
  defaultTab?: LeagueTab;
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get("tab");
  const tab: LeagueTab = LEAGUE_TABS.some((item) => item.key === tabParam) ? (tabParam as LeagueTab) : defaultTab;
  const setTab = useCallback(
    (next: LeagueTab) => {
      const nextParams = new URLSearchParams(searchParams);
      nextParams.set("tab", next);
      setSearchParams(nextParams, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const profile = data.activeProfile;
  const activeFormat = profile ? leagueFormat(profile, false) : "Choose a league profile";

  return <>
    <PageHeader
      eyebrow={activeFormat}
      title="League"
      description="What is this league/team context? My Roster, Teams, Scoring, Settings, and Sync -- one workspace for this league's identity and configuration."
      status={profile ? <StatusBadge tone="safe" label={profile.leagueName} /> : <StatusBadge tone="blocked" label="No active league" />}
    />
    {!profile ? (
      <EmptyState icon="alert" title="No active league" message="Choose a league to see its roster, teams, scoring, settings, and sync status." />
    ) : <>
      <nav aria-label="League sections" className="nwr-tabbar" role="tablist">
        {LEAGUE_TABS.map((item) => (
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
      {tab === "overview" ? <LeagueOverviewTab client={client} data={data} /> : null}
      {tab === "roster" ? <MyRosterContent client={client} data={data} /> : null}
      {tab === "teams" ? <OpponentRostersContent client={client} data={data} /> : null}
      {tab === "scoring" ? <LeagueScoringTab data={data} onOpenSettings={() => setTab("settings")} /> : null}
      {tab === "settings" ? <LeagueSettingsTab client={client} data={data} onUpdate={onUpdate} /> : null}
      {tab === "sync" ? <LeagueSyncTab client={client} data={data} onUpdate={onUpdate} /> : null}
    </>}
  </>;
}

/** Compact top-level summary (directive: "should show compactly: league
 * name, my team, platform, team count, scoring format, current week, sync
 * health"), with provider/internal/debug detail behind the same collapsed
 * `<details className="player-drawer__section">` disclosure pattern the
 * design system already documents for progressive disclosure -- never
 * dominating the primary view. */
function LeagueOverviewTab({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const profile = data.activeProfile;
  const isSleeper = profile?.provider === "sleeper";
  const contextLoader = useCallback(() => client.redraftLeagueWorkspaceContext(), [client, data.activeProfileId]);
  const { result: context, error: contextError } = useAsync<LeagueWorkspaceContext>(contextLoader, [client, data.activeProfileId]);
  const rosterLoader = useCallback(() => (isSleeper ? client.redraftMyRoster() : null), [client, isSleeper]);
  const { result: myRoster } = useAsync(rosterLoader, [isSleeper, data.activeProfileId]);

  if (!profile) return null;

  const myRosterSummary = !isSleeper
    ? "Not tracked for a Local/ESPN profile"
    : myRoster
      ? `${myRoster.roster.length} rostered player${myRoster.roster.length === 1 ? "" : "s"}`
      : "Reading your current roster…";

  return <>
    <Panel title="League summary" eyebrow="What is this league?">
      <dl className="health-list">
        <div><dt>League</dt><dd title={profile.leagueName}>{profile.leagueName}</dd></div>
        <div><dt>My roster</dt><dd>{myRosterSummary}</dd></div>
        <div><dt>Platform</dt><dd>{providerFormat(profile)}</dd></div>
        <div><dt>Teams</dt><dd>{profile.teamCount}</dd></div>
        <div><dt>Scoring format</dt><dd>{scoringFormat(profile)}</dd></div>
        <div><dt>Current week</dt><dd>{context ? formatCurrentWeek(context.currentWeek) : "Reading…"}</dd></div>
        <div>
          <dt>Sync health</dt>
          <dd>{context ? <StatusBadge tone={syncHealthTone(context.syncStatus)} label={syncHealthLabel(context.syncStatus)} /> : <StatusBadge tone="review" label="Reading…" />}</dd>
        </div>
      </dl>
    </Panel>
    {contextError ? <ErrorState message={contextError.message} recovery={contextError.recoveryAction} /> : null}
    <details className="player-drawer__section">
      <summary>Advanced / provenance</summary>
      <dl className="health-list">
        <div><dt>Identity</dt><dd>{leagueIdentityFormat(profile)}</dd></div>
        <div><dt>Profile ID</dt><dd>{profile.profileId}</dd></div>
        {context ? <>
          <div><dt>Lifecycle basis</dt><dd>{context.lifecycleBasis}</dd></div>
          <div><dt>Scoring profile hash</dt><dd>{context.scoringProfileHash}</dd></div>
          <div><dt>Roster state hash</dt><dd>{context.rosterStateHash ?? "unavailable"}</dd></div>
          <div><dt>Snapshot ID</dt><dd>{context.leagueSnapshotId}</dd></div>
          <div><dt>Sync as of</dt><dd>{context.syncAsOf ?? "unavailable"}</dd></div>
        </> : null}
      </dl>
      {context?.issues.length ? <p className="copy-muted">{context.issues.join(" · ")}</p> : null}
    </details>
  </>;
}

/** Read-only scoring display (directive state C: "Scoring settings
 * display") -- every real rule on `LeagueProfile.scoring`, including
 * several fields the editable form (SETTINGS tab) never exposed. Editing
 * lives in Settings; this tab is deliberately view-only with one jump
 * link there, mirroring Improve Team's Targets -> Add/Drop and Trades'
 * Find Trades -> Analyze cross-tab jump precedent. */
function LeagueScoringTab({ data, onOpenSettings }: { data: RedraftBootstrap; onOpenSettings: () => void }) {
  const profile = data.activeProfile;
  if (!profile) return null;
  const groups = scoringSummaryGroups(profile);
  const roster = rosterCompositionRows(profile);
  return <>
    <Panel
      title="Scoring rules"
      eyebrow={scoringFormat(profile)}
      action={<Button icon="settings" onClick={onOpenSettings} variant="secondary">Edit in Settings</Button>}
    >
      <div className="league-scoring-groups">
        {groups.map((group) => (
          <div className="league-scoring-group" key={group.title}>
            <h3>{group.title}</h3>
            <dl className="health-list">
              {group.rows.map((row) => <div key={row.label}><dt>{row.label}</dt><dd>{row.value}</dd></div>)}
            </dl>
          </div>
        ))}
      </div>
    </Panel>
    <Panel title="Roster construction" eyebrow={`${profile.teamCount} teams · ${profile.roster.benchSize} bench`}>
      <dl className="health-list">
        {roster.map((row) => <div key={row.label}><dt>{row.label}</dt><dd>{row.value}</dd></div>)}
      </dl>
    </Panel>
  </>;
}

/** League name / roster limits / scoring / draft settings editor
 * (directive state D: "Settings") -- reuses `ProfileEditor` +
 * `editableProfile` directly from `profile.tsx` (see the module doc above
 * for why), calling the exact same `client.updateRedraftProfile` /
 * `client.duplicateRedraftProfile` contract methods `ProfilePage` already
 * uses, with the exact same local `edit`/`working`/error/message state
 * shape. Zero behavior change to the editor itself. */
function LeagueSettingsTab({
  client,
  data,
  onUpdate,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
}) {
  const profile = data.activeProfile;
  const [edit, setEdit] = useState<EditableProfile | null>(profile ? editableProfile(profile) : null);
  const [working, setWorking] = useState("");
  const [error, setError] = useState<NwrApiError | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setEdit(profile ? editableProfile(profile) : null);
  }, [profile]);

  if (!profile || !edit) return null;

  const save = async () => {
    if (working) return;
    setWorking("save"); setError(null); setMessage("");
    try {
      onUpdate(await client.updateRedraftProfile(profile.profileId, edit));
      setMessage("Scoring, roster, and draft settings saved. Rankings were refreshed.");
    } catch (reason) {
      setError(reason instanceof NwrApiError ? reason : new NwrApiError("Profile settings could not be saved."));
    } finally {
      setWorking("");
    }
  };
  const duplicate = async () => {
    if (working) return;
    setWorking("duplicate"); setError(null); setMessage("");
    try {
      onUpdate(await client.duplicateRedraftProfile(profile.profileId));
      setMessage("Profile duplicated and activated. Its draft board starts empty.");
    } catch (reason) {
      setError(reason instanceof NwrApiError ? reason : new NwrApiError("Profile could not be duplicated."));
    } finally {
      setWorking("");
    }
  };

  return <>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    <p aria-live="polite" className="profile-feedback">{message}</p>
    <ProfileEditor disabled={Boolean(working)} edit={edit} onChange={setEdit} onDuplicate={() => void duplicate()} onSave={() => void save()} working={working} />
  </>;
}

/** Sync / connection health (directive states E/F: "Sync -- healthy" /
 * "Sync -- stale/degraded"), combining the real `LeagueWorkspaceContext`
 * (`syncStatus`/`syncAsOf`/`issues`/`currentWeek` -- new wiring, see the
 * module doc) with the real `LEAGUE_SYNC` category of the existing Data
 * Health report (`client.redraftDataHealth()`, already used elsewhere by
 * `DataHealthPage` -- reused, not duplicated), plus the real Sleeper
 * resync action `ProfilePage` already exposes (same contract call, no new
 * endpoint). */
function LeagueSyncTab({
  client,
  data,
  onUpdate,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
}) {
  const profile = data.activeProfile;
  const isSleeper = profile?.provider === "sleeper";
  const contextLoader = useCallback(() => client.redraftLeagueWorkspaceContext(), [client, data.activeProfileId]);
  const { result: context, error: contextError, working: contextWorking, reload: reloadContext } = useAsync<LeagueWorkspaceContext>(contextLoader, [client, data.activeProfileId]);
  const healthLoader = useCallback(() => client.redraftDataHealth(), [client, data.activeProfileId]);
  const { result: health } = useAsync<DataHealthReport>(healthLoader, [client, data.activeProfileId]);
  const [resyncWorking, setResyncWorking] = useState(false);
  const [resyncError, setResyncError] = useState<NwrApiError | null>(null);
  const [resyncMessage, setResyncMessage] = useState("");

  if (!profile) return null;

  const resync = async () => {
    if (resyncWorking) return;
    setResyncWorking(true); setResyncError(null); setResyncMessage("");
    try {
      onUpdate(await client.resyncSleeperRedraftProfile(profile.profileId));
      setResyncMessage("Sleeper league settings and your current roster were refreshed locally. No Sleeper data was changed.");
      reloadContext();
    } catch (reason) {
      setResyncError(reason instanceof NwrApiError ? reason : new NwrApiError("Sleeper league could not be refreshed."));
    } finally {
      setResyncWorking(false);
    }
  };

  const syncCategory = health?.categories.find((category) => category.category === "LEAGUE_SYNC") ?? null;

  return <>
    <Panel
      action={context ? <StatusBadge tone={syncHealthTone(context.syncStatus)} label={syncHealthLabel(context.syncStatus)} /> : undefined}
      eyebrow={leagueIdentityFormat(profile)}
      title="Connection & sync"
    >
      {contextError ? <ErrorState message={contextError.message} recovery={contextError.recoveryAction} /> : null}
      <dl className="health-list">
        <div><dt>Platform</dt><dd>{providerFormat(profile)}</dd></div>
        <div><dt>Sync status</dt><dd>{context ? syncHealthLabel(context.syncStatus) : contextWorking ? "Reading…" : "Unavailable"}</dd></div>
        <div><dt>Last synced</dt><dd>{context?.syncAsOf ?? "unavailable"}</dd></div>
        <div><dt>Current week</dt><dd>{context ? formatCurrentWeek(context.currentWeek) : "unavailable"}</dd></div>
      </dl>
      {context?.issues.length ? <p className="copy-muted">{context.issues.join(" · ")}</p> : null}
      {isSleeper ? (
        <div className="profile-create-footer">
          <p>Refresh league settings and your stored roster from Sleeper's read-only API. No Sleeper data is ever written.</p>
          {resyncError ? <ErrorState message={resyncError.message} recovery={resyncError.recoveryAction} /> : null}
          <p aria-live="polite" className="profile-feedback">{resyncMessage}</p>
          <Button disabled={resyncWorking} icon="activity" onClick={() => void resync()}>{resyncWorking ? "Refreshing…" : "Refresh from Sleeper"}</Button>
        </div>
      ) : (
        <EmptyState icon="alert" message="Local and ESPN profiles have no live connection to refresh -- scoring and roster changes are made manually in Settings." title="No live sync for this provider" />
      )}
    </Panel>
    {syncCategory ? (
      <Panel
        action={<StatusBadge tone={dataHealthTone(syncCategory.status)} label={syncCategory.status.replaceAll("_", " ")} />}
        eyebrow={syncCategory.source ?? "No source"}
        title="League sync detail"
      >
        <dl className="health-list">
          <div><dt>Last update</dt><dd>{syncCategory.lastUpdate ?? "unavailable"}</dd></div>
          <div><dt>Freshness</dt><dd>{syncCategory.freshness}</dd></div>
          <div><dt>Impact if degraded</dt><dd>{syncCategory.impactOnRecommendations}</dd></div>
        </dl>
        {syncCategory.degradationReason ? <p className="copy-muted">{syncCategory.degradationReason}</p> : null}
      </Panel>
    ) : null}
  </>;
}
