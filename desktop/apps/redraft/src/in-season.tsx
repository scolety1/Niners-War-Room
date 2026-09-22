import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type {
  RedraftBootstrap,
  TradeAnalysisResult,
  TradeFinderCandidate,
  TradePlayerImpact,
  WaiverAddCandidate,
  WaiverDropCandidate,
  WaiversResult,
} from "@nwr/contracts";
import {
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  MetricCard,
  PageHeader,
  Panel,
  SearchInput,
  SegmentedControl,
  SelectField,
  StatusBadge,
  type TableColumn,
  formatNumber,
} from "@nwr/ui";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { DecisionExplain } from "./decision-explain";
import { explainHomeAction } from "./home-action-explain";
import { explainLineupSwap, findResultingSlot } from "./lineup-explain";
import { SnapshotProvenanceNotice } from "./snapshot-provenance";
import { addUniqueTradeSideCandidate, tradeFinderAnalysisLinkTarget } from "./trades-explain";
import { leagueFormat, resolveDisplayLifecycle, resolveLeagueLifecycle } from "./league-context";
import {
  describeOwnerBracketEntry,
  formatRecord,
  formatStandingsRank,
  matchupStatusText,
  ownerStandingsRow,
  playoffStatusText,
} from "./league-summary";
import { usePlayerDetailOpener } from "./player-detail-context";
import { playerAvailabilityBadgeLabel, playerAvailabilityBadgeTone } from "./player-detail-state";
import {
  ACTION_CATEGORY_LINK,
  FAAB_URGENCY_TONE,
  FREE_AGENT_COLUMNS,
  ProviderStatusLine,
  RefreshProjectionsButton,
  WeekControl,
  appendPlayerDetailColumn,
  describeUnmatchedRosterPlayers,
  formatClock,
  resolveHomeActionFreshness,
  resolveWeekDisplay,
  statusTone,
  useAsync,
  useProviderWeek,
  useWeekSelection,
} from "./weekly-shared";

const HOME_MAX_ACTIONS = 5;

const LIFECYCLE_STAGE_LABEL: Record<string, string> = {
  PRE_DRAFT: "Pre-Draft",
  LIVE_DRAFT: "Live Draft",
  IN_SEASON: "In Season",
  OFFSEASON: "Offseason",
};

/**
 * NWR in-season owner UI pass (2026-09-10). Owner governance for this file:
 * (1) the weekly-projection endpoint behind every "THIS WEEK" figure here is
 * an approved TEMPORARY/STOPGAP provider -- every fetch goes through the
 * canonical facade methods, never a Sleeper call of its own; (2) every page
 * here is read-only -- none of them ever writes a lineup, waiver claim, or
 * trade to Sleeper (see each result's own `writeBehavior` field, always
 * "NO_SLEEPER_WRITES").
 */

const SLOT_LABEL: Record<string, string> = {
  QB: "QB", RB: "RB", WR: "WR", TE: "TE", FLEX: "FLEX", SUPERFLEX: "SUPERFLEX", K: "K", DST: "DST",
};

// P1-1 (2026-09-12): real record/points-for standings, straight off
// LeagueWorkspaceContext.standings (Sleeper's own roster `settings`
// block) -- no simulated finish or playoff-odds column.
const STANDINGS_COLUMNS: TableColumn[] = [
  { key: "teamName", label: "Team", sort: "text", render: (row) => <span>{row.isOwner ? <strong>{String(row.teamName)} (you)</strong> : String(row.teamName)}</span> },
  { key: "wins", label: "W", sort: "number", align: "right" },
  { key: "losses", label: "L", sort: "number", align: "right" },
  { key: "ties", label: "T", sort: "number", align: "right" },
  { key: "pointsFor", label: "Points for", sort: "number", align: "right", render: (row) => formatNumber(Number(row.pointsFor), 1) },
  { key: "pointsAgainst", label: "Points against", sort: "number", align: "right", render: (row) => formatNumber(Number(row.pointsAgainst), 1) },
];

// ---------------------------------------------------------------------------
// Weekly Home
// ---------------------------------------------------------------------------

export function WeeklyHomePage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  // Flaim-integration cycle (2026-09-19), Worker 4: gate on the
  // provider-agnostic capability flag instead of a blanket
  // `provider === "sleeper"` check -- same field/precedent as the backend's
  // `_active_sleeper_context` guard. See
  // docs/codex/flaim_integration_20260919/LEDGER.md.
  const isSleeper = Boolean(data.leagueCapabilities?.hasVerifiedIdentity);
  const profileId = isSleeper ? data.activeProfileId : null;

  // P1-1 (2026-09-12): the provider-known current NFL week (from Sleeper's
  // own live state, read via LeagueWorkspaceContext) is now the DEFAULT
  // authority for "what week is it" -- manual entry (WeekControl below) is
  // only a FALLBACK for when the provider is unavailable (a non-Sleeper
  // profile, or a failed read), not the default it used to be
  // (hardcoded `useState(1)`). `manualWeekOverride` stays `null` until the
  // owner explicitly changes it, and is reset on every league switch so a
  // previous league's manual choice never leaks into a newly opened one.
  // NWR Sunday Readiness overnight cycle, Worker 2: pure refactor onto the
  // now-shared `useProviderWeek`/`useWeekSelection` hooks (weekly-shared.tsx)
  // -- same resolved values, same `?? 1` display fallback at this one call
  // site, unchanged behavior from before this pass. Start/Sit and Improve
  // Team now reuse this exact mechanism instead of hardcoding Week 1.
  const { context, error: contextError } = useProviderWeek(client, data.activeProfileId);
  const { week: resolvedWeek, manualWeekOverride, setManualWeekOverride, usingProviderWeek } = useWeekSelection(
    context?.currentWeek ?? null,
    data.activeProfileId,
  );
  const providerWeek = context?.currentWeek ?? null;
  const week = resolvedWeek ?? 1;

  // NWR pre-UI architecture CLOSURE pass (directive section 3): ONE
  // request builds the whole Home render -- `redraftWeeklyHomeActions` now
  // embeds the SAME lineup/free-agent sub-payloads it already used
  // internally to build the action list, under one shared
  // `leagueSnapshotId`. This used to be 3 independent HTTP calls (this
  // one, a second `redraftWeeklyLineup`, a third `redraftFreeAgents`),
  // each performing its own live Sleeper roster read with no snapshot
  // value threaded/asserted across them (PRODUCT_ARCHITECTURE.md
  // invariant F). Do not reintroduce those extra calls here -- every
  // decision card below must keep deriving from `actions.lineup`/
  // `actions.freeAgents`, not a second fetch.
  const actionsLoader = useCallback(
    () => (profileId ? client.redraftWeeklyHomeActions(week) : null),
    [client, profileId, week],
  );
  const { result: actions, error: actionsError, working: actionsWorking } = useAsync(actionsLoader, [profileId, week]);
  // Week-display race fix (shared upgrade B, 2026-09-16): the title/"Week"
  // chip below render `weekDisplay.displayWeek` -- the SAME resolved
  // `actions` response the action cards/lineup/free-agent panels already
  // come from -- never the raw `week` input state directly, so the header
  // can never claim a week the body isn't actually showing yet. See
  // `resolveWeekDisplay` in weekly-shared.tsx for the full rationale.
  const weekDisplay = resolveWeekDisplay(week, actions?.week ?? null);
  const lineup = actions?.lineup ?? null;
  const freeAgents = actions?.freeAgents ?? null;
  const freeAgentsWorking = actionsWorking;
  const freeAgentError = !freeAgents && actions?.unavailableSections.some((section) => section.section === "FREE_AGENTS")
    ? { message: actions.unavailableSections.find((section) => section.section === "FREE_AGENTS")?.reason ?? "Free agents unavailable.", recoveryAction: undefined as string | undefined }
    : null;

  const activeName = data.activeProfile?.leagueName ?? "Choose a league";
  // NWR Sunday Readiness overnight cycle, Worker 5: real, pre-existing
  // display bug fixed (flagged by Worker 4) -- this "Stage" row previously
  // called ONLY the local, bootstrap-only `resolveLeagueLifecycle` heuristic,
  // which has no live provider-status read (see that function's own
  // docstring) and returns PRE_DRAFT for any real Sleeper league that was
  // never drafted inside this app's own Draft Room (both real leagues,
  // Fantasy Gamers and Enginerds, drafted on Sleeper itself) -- confirmed
  // live this pass: both showed "PRE-DRAFT" despite real IN_SEASON data.
  // `context` (already fetched above via `useProviderWeek` ->
  // `useLeagueWorkspaceContext` -> `/api/v1/redraft/league-workspace-context`,
  // NO new network call added) already carries the correct, live,
  // provider-status-aware `lifecycle` field -- prefer it, falling back to
  // the local heuristic only while that request hasn't resolved yet (or
  // for a non-Sleeper profile, where the workspace-context loader
  // deliberately returns null -- see `useLeagueWorkspaceContext`).
  const lifecycle = data.activeProfile
    ? resolveDisplayLifecycle(resolveLeagueLifecycle(data.activeProfile, data.draftBoard), context?.lifecycle)
    : null;
  // NWR UI foundation pass (directive Phase 4): only 3-5 meaningful
  // prioritized actions, never a dumped full list -- `actions.actions` is
  // already priority-sorted server-side (see redraft_weekly_home_actions),
  // so this is a display cap on already-ranked data, not a new ranking.
  const shownActions = (actions?.actions ?? []).slice(0, HOME_MAX_ACTIONS);
  const hiddenActionCount = Math.max(0, (actions?.actions.length ?? 0) - shownActions.length);
  const freshnessNote = lineup?.providerHealth
    ? `${lineup.providerHealth.provider} · updated ${formatClock(lineup.providerHealth.retrievedAt)}${lineup.providerHealth.freshness === "STALE" ? " (stale)" : ""}`
    : null;

  const ownerRow = ownerStandingsRow(context?.standings);
  // Sleeper pre-seeds an empty bracket skeleton (mostly null team slots)
  // well before the actual playoffs -- real data, but noisy/premature to
  // lead with during the regular season. Only surface the owner's actual
  // bracket matchup once the league has really reached its playoff weeks;
  // otherwise show the plain "Playoffs start Week N" fact instead.
  const bracketNote = context?.playoff?.inPlayoffs
    ? describeOwnerBracketEntry(context.playoff, ownerRow?.rosterId)
    : null;
  const playoffNote = bracketNote ?? playoffStatusText(context?.playoff);
  const matchupNote = matchupStatusText(context?.matchup);

  return <>
    <PageHeader
      eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"}
      title={`${activeName} · Week ${weekDisplay.displayWeek}`}
      description="What needs your attention this week -- not a stats dashboard. Matchup, record, and standings below reflect only what Sleeper directly reports; nothing here is simulated or predicted."
      status={<StatusBadge tone={data.status.tone} label={data.health.status || "Review"} />}
      actions={<div className="profile-edit-actions">
        <WeekControl week={week} onChange={setManualWeekOverride} label={usingProviderWeek ? "NFL week (auto)" : "NFL week (manual)"} />
        {manualWeekOverride !== null && providerWeek !== null && manualWeekOverride !== providerWeek ? (
          <Button variant="ghost" onClick={() => setManualWeekOverride(null)}>Use current week ({providerWeek})</Button>
        ) : null}
      </div>}
    />
    {!isSleeper ? <EmptyState title="Verified league data required" message="Weekly in-season tools (Start/Sit, Waivers, Trade, streamers) require verified league data. Import league data (e.g. via Sleeper), then choose it here." action={<Link to="/leagues">Open league chooser</Link>} /> : null}
    {isSleeper ? <>
      {/* THIS WEEK strip (Phase 4 top block, extended by P1-1): only real,
          already-available signals -- league/team identity, week,
          lifecycle stage, data freshness, plus (when Sleeper directly
          reports them) this week's opponent/score and the owner's
          record. Opponent/score/record are omitted entirely, never
          fabricated, when the provider doesn't have them (see
          `LeagueWorkspaceContext.matchup`/`.standings`, both nullable). */}
      <section className="nwr-this-week" aria-label="This week">
        <div className="nwr-this-week__item"><span>League</span><strong>{activeName}</strong></div>
        <div className="nwr-this-week__item"><span>Week</span><strong>{weekDisplay.displayWeek}</strong></div>
        {lifecycle ? <div className="nwr-this-week__item"><span>Stage</span><strong>{LIFECYCLE_STAGE_LABEL[lifecycle] ?? lifecycle}</strong></div> : null}
        {/* The matchup/score below are always for the provider's real
            current week (`context.matchup.week`), independent of the
            "Week" figure above -- which, once the owner manually
            overrides it (fallback control), drives ONLY the lineup/
            free-agent projections and can legitimately differ. The
            explicit "(Wk N)" label keeps that unambiguous rather than
            implying stale-week matchup data belongs to a different week. */}
        {context?.matchup?.hasOpponent ? (
          <div className="nwr-this-week__item"><span>Opponent (Wk {context.matchup.week})</span><strong>{context.matchup.opponentTeamName}</strong></div>
        ) : null}
        {context?.matchup?.hasOpponent && context.matchup.ownerPoints != null && context.matchup.opponentPoints != null ? (
          <div className="nwr-this-week__item"><span>Score (Wk {context.matchup.week})</span><strong>{formatNumber(context.matchup.ownerPoints, 1)} – {formatNumber(context.matchup.opponentPoints, 1)}</strong></div>
        ) : null}
        {ownerRow ? (
          <div className="nwr-this-week__item"><span>Record</span><strong>{formatRecord(ownerRow)}{formatStandingsRank(context?.standings) ? ` (${formatStandingsRank(context?.standings)})` : ""}</strong></div>
        ) : null}
        <div className="nwr-this-week__spacer" />
        {freshnessNote ? <div className="nwr-this-week__item"><span>Data</span><strong>{freshnessNote}</strong></div> : null}
      </section>
      {contextError ? <ErrorState message={contextError.message} recovery={contextError.recoveryAction} /> : null}
      {matchupNote || playoffNote ? (
        <p className="copy-muted" style={{ margin: "0 0 14px" }}>
          {[matchupNote, playoffNote].filter(Boolean).join(" · ")}
        </p>
      ) : null}

      {context?.standings ? (
        <Panel title="Standings" eyebrow="Real Sleeper wins/losses/points-for" action={<Link to="/league">Open League</Link>}>
          <DataTable
            columns={STANDINGS_COLUMNS}
            rows={context.standings.rows as unknown as Array<Record<string, unknown>>}
            rowKey={(row) => String(row.rosterId)}
          />
        </Panel>
      ) : null}

      <h2 className="nwr-text-section-heading" style={{ margin: "0 0 8px" }}>NWR Actions</h2>
      {actionsError ? <ErrorState message={actionsError.message} recovery={actionsError.recoveryAction} /> : null}
      {/* Week-display race fix: `weekDisplay.isStale` is a structural check
          (resolved response's own week vs. the currently requested week),
          not a `working`-flag guess -- true exactly when the actions/
          lineup/free-agent panels below still show a PRIOR week's data
          while a newer week's fetch is in flight, so it stays correct even
          across StrictMode double-invokes or overlapping requests. */}
      {weekDisplay.isStale ? (
        <div className="alert-strip alert-strip--pending" role="status">
          <strong>Updating…</strong>
          <span>Reading live data for Week {week} -- Actions, Projected lineup, and Top free agents below are still Week {weekDisplay.displayWeek}'s.</span>
        </div>
      ) : actionsWorking ? <p className="draft-feedback">Reading live data…</p> : null}
      {actions && shownActions.length === 0 ? (
        <div className="nwr-home-settled">
          <div>
            <strong>You're set for now.</strong>
            <span>Lineup, waivers, trades, and streamers were all checked live -- none returned anything worth flagging this week.</span>
          </div>
        </div>
      ) : null}
      {shownActions.length > 0 ? (
        <div className="nwr-action-grid">
          {shownActions.map((action, index) => {
            const explanation = explainHomeAction(action);
            const link = ACTION_CATEGORY_LINK[action.category];
            const tone = explanation.confidence === "LOW" ? "warning" : "recommended";
            // Full Cycle V1, Worker 4 (Section 3C): WAIVER/TRADE cards are
            // built from the season-level governed ranking
            // (`redraft_waivers`/`redraft_trade_finder`), not the weekly
            // Sleeper provider `freshnessNote` above was previously applied
            // to unconditionally -- see `resolveHomeActionFreshness`.
            const actionFreshness = resolveHomeActionFreshness(
              action.category,
              freshnessNote,
              data.status.sourceAsOf,
            );
            return (
              <DecisionExplain
                key={`${action.category}-${index}`}
                eyebrow={explanation.categoryLabel}
                headline={explanation.doThis}
                why={explanation.why}
                secondaryWhy={explanation.secondaryWhy}
                alternative={explanation.alternative}
                impact={explanation.expectedImpact}
                freshness={actionFreshness}
                confidence={explanation.confidence ?? null}
                tone={tone}
                actions={link ? <Link to={link}>Open</Link> : null}
              />
            );
          })}
        </div>
      ) : null}
      {hiddenActionCount > 0 ? (
        <p className="copy-muted" style={{ margin: "8px 0 0" }}>
          Showing the top {shownActions.length} of {actions?.actions.length} ranked actions this week.
        </p>
      ) : null}
      {actions?.unavailableSections.length ? (
        <div className="alert-strip">
          <strong>Some sections unavailable</strong>
          <span>{actions.unavailableSections.map((section) => `${section.section}: ${section.reason}`).join(" · ")}</span>
        </div>
      ) : null}

      <div className="split-view" style={{ marginTop: 18 }}>
        <Panel title="Projected lineup" eyebrow="THIS WEEK · Start/Sit summary" action={<Link to="/lineup">Open full Start/Sit</Link>}>
          {lineup ? <>
            <p className="draft-feedback">
              Projected total: <strong>{formatNumber(lineup.projectedTotal, 1)}</strong> pts
              {lineup.unprojectedStarterCount ? ` · ${lineup.unprojectedStarterCount} starter(s) unprojected` : ""}
              {lineup.swaps.length ? ` · ${lineup.swaps.length} recommended change${lineup.swaps.length === 1 ? "" : "s"}` : " · lineup already matches NWR's optimal"}
            </p>
            <ProviderStatusLine health={lineup.providerHealth} />
          </> : <p className="copy-muted">Weekly lineup unavailable for week {week}.</p>}
        </Panel>
        <Panel title="Top free agents" eyebrow="Live Sleeper availability" action={<Link to="/waivers">Open Waivers</Link>}>
          {freeAgentError ? <ErrorState message={freeAgentError.message} recovery={freeAgentError.recoveryAction} /> : null}
          {freeAgents ? <DataTable columns={FREE_AGENT_COLUMNS} rows={freeAgents.freeAgents.slice(0, 8) as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.sleeperPlayerId)} /> : freeAgentsWorking ? <p className="draft-feedback">Reading…</p> : <p className="copy-muted">Free agent data unavailable for week {week}.</p>}
        </Panel>
      </div>
      <div className="profile-edit-actions">
        <Link to="/my-roster">My roster</Link>
        <Link to="/opponent-rosters">Opponent rosters</Link>
        <Link to="/trade-finder">Trade Finder</Link>
        <Link to="/weekly-tools">K/DST Streamer</Link>
      </div>
      <Panel title="Weekly data status" eyebrow="Source freshness · profile record">
        <ProviderStatusLine health={lineup?.providerHealth ?? null} />
        <dl className="health-list"><div><dt>Profile last updated</dt><dd>{data.activeProfile?.updatedAtUtc ?? "unavailable"}</dd></div></dl>
      </Panel>
    </> : null}
  </>;
}

// ---------------------------------------------------------------------------
// Start / Sit (Lineup)
// ---------------------------------------------------------------------------

export function LineupPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  // Flaim-integration cycle (2026-09-19), Worker 4: capability gate, see
  // WeeklyHomePage above.
  const isSleeper = Boolean(data.leagueCapabilities?.hasVerifiedIdentity);
  const profileId = isSleeper ? data.activeProfileId : null;
  // NWR Sunday Readiness overnight cycle, Worker 2 (W1 fix): this page
  // used to `useState(1)` -- a hardcoded Week 1 default that could serve
  // (and silently REQUEST) a Week 1 lineup during a real later week, with
  // no loading/unknown state in between. Now reuses the same
  // provider-week mechanism Weekly Home already used (`useProviderWeek`/
  // `useWeekSelection`, weekly-shared.tsx) -- `week` stays `null` (never a
  // fabricated 1) until the real provider week resolves or the owner
  // picks one manually, and the loader below gates on `week != null` so
  // no request is ever sent for an unresolved week.
  const { providerWeek, error: contextError, working: contextWorking } = useProviderWeek(client, profileId);
  const { week, manualWeekOverride, setManualWeekOverride, usingProviderWeek } = useWeekSelection(providerWeek, profileId);
  const resolvingWeek = week === null && (contextWorking || (profileId != null && providerWeek == null));
  const loader = useCallback(
    () => (isSleeper && week != null ? client.redraftWeeklyLineup(week) : null),
    [client, isSleeper, week],
  );
  const { result, error, working, reload } = useAsync(loader, [isSleeper, week, data.activeProfileId]);
  // Week-display race fix (shared upgrade B, 2026-09-16): same bug class
  // and fix as WeeklyHomePage above -- see `resolveWeekDisplay` in
  // weekly-shared.tsx. The title used to render the raw `week` input
  // while the starters/swaps/bench below still showed the PREVIOUS
  // week's resolved `result` until the new fetch landed.
  const weekDisplay = resolveWeekDisplay(week ?? 0, result?.week ?? null);
  // NWR pre-UI architecture CLOSURE pass (directive section 5): the same
  // global Player Detail primitive Waivers uses below -- see
  // player-detail-context.tsx.
  const openPlayerDetail = usePlayerDetailOpener(data.activeProfileId, "LINEUP");
  // Same freshness-note shape Weekly Home already derives from this exact
  // providerHealth field -- one shared vocabulary for "how current is
  // this" across surfaces, not a second one invented here.
  const freshnessNote = result?.providerHealth
    ? `${result.providerHealth.provider} · updated ${formatClock(result.providerHealth.retrievedAt)}${result.providerHealth.freshness === "STALE" ? " (stale)" : ""}`
    : null;

  const benchColumns: TableColumn[] = [
    { key: "playerName", label: "Player", sort: "text" },
    { key: "position", label: "Pos", sort: "text" },
    { key: "projectedPoints", label: "Proj pts", sort: "number", align: "right", render: (row) => row.projectedPoints == null ? "—" : formatNumber(Number(row.projectedPoints), 1) },
    {
      key: "view", label: "", render: (row) => (
        <Button variant="ghost" onClick={() => openPlayerDetail({ playerId: String(row.canonicalPlayerId ?? row.sleeperPlayerId), playerName: String(row.playerName), position: String(row.position) })}>View</Button>
      ),
    },
  ];

  return <>
    <PageHeader
      eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"}
      title={week == null ? "Start / Sit — THIS WEEK (week loading…)" : `Start / Sit — THIS WEEK (Week ${weekDisplay.displayWeek})`}
      description="NWR's recommended legal lineup for this week only -- never confused with rest-of-season rankings. Recommendation-only: NWR never writes a lineup to Sleeper."
      status={result ? <StatusBadge tone={result.providerHealth.freshness === "STALE" ? "review" : "safe"} label={`${result.matched} matched · ${result.unmatched} unmatched`} /> : undefined}
      actions={<div className="profile-edit-actions">
        <WeekControl week={week ?? providerWeek ?? 1} onChange={setManualWeekOverride} label={usingProviderWeek ? "NFL week (auto)" : "NFL week (manual)"} />
        {manualWeekOverride !== null && providerWeek !== null && manualWeekOverride !== providerWeek ? (
          <Button variant="ghost" onClick={() => setManualWeekOverride(null)}>Use current week ({providerWeek})</Button>
        ) : null}
        <RefreshProjectionsButton onRefresh={reload} working={working} />
      </div>}
    />
    {!isSleeper ? <EmptyState title="Verified league data required" message="Start/Sit needs a live roster and the real weekly-projection source. Import league data (e.g. via Sleeper) to continue." /> : null}
    {/* W1 fix: while the real provider week is still resolving, show an
        honest loading state instead of silently requesting Week 1. */}
    {isSleeper && resolvingWeek ? (
      <div className="alert-strip alert-strip--pending" role="status">
        <strong>Loading…</strong>
        <span>Reading this league's real current NFL week before requesting a lineup.</span>
      </div>
    ) : null}
    {contextError ? <ErrorState message={contextError.message} recovery={contextError.recoveryAction} /> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {/* Week-display race fix: structural check against `result.week` itself
        (see WeeklyHomePage above), not a `working`-flag guess -- true
        exactly when the starters/swaps/bench below still reflect a PRIOR
        week while a newer week's fetch is in flight. */}
    {weekDisplay.isStale ? (
      <div className="alert-strip alert-strip--pending" role="status">
        <strong>Updating…</strong>
        <span>Reading Week {week}'s lineup -- the recommendations and starters below are still Week {weekDisplay.displayWeek}'s.</span>
      </div>
    ) : null}
    {result ? <>
      <ProviderStatusLine health={result.providerHealth} />
      {result.swaps.length ? (
        <Panel title="Recommended changes" eyebrow={`${result.swaps.length} change${result.swaps.length === 1 ? "" : "s"} vs. Sleeper's current starters`}>
          {/* NWR UI expansion pass (Lineup surface): only real decisions --
              a swap only exists when NWR's optimal starter differs from
              Sleeper's current one (redraft_weekly_lineup's own `swaps`
              field, unchanged) -- rendered with the same decision grammar
              Weekly Home uses, so a close call reads as visually distinct
              (tone="warning") from a confident recommendation
              (tone="recommended"), never a bare list. */}
          <div className="nwr-action-grid">
            {result.swaps.map((swap, index) => {
              const resultingSlot = findResultingSlot(swap, result.starters);
              const explanation = explainLineupSwap(swap, resultingSlot);
              return (
                <DecisionExplain
                  key={`${swap.slotType}-${index}`}
                  eyebrow={SLOT_LABEL[swap.slotType] ?? swap.slotType}
                  headline={explanation.headline}
                  why={explanation.why}
                  alternative={explanation.alternative}
                  impact={explanation.impact}
                  status={explanation.status ? { tone: statusTone(explanation.status), label: explanation.status } : null}
                  freshness={freshnessNote}
                  confidence={explanation.confidence}
                  tone={explanation.tone}
                  actions={resultingSlot?.player ? (
                    <Button
                      variant="ghost"
                      onClick={() => openPlayerDetail({
                        playerId: resultingSlot.player!.canonicalPlayerId ?? resultingSlot.player!.sleeperPlayerId,
                        playerName: resultingSlot.player!.playerName,
                        position: resultingSlot.player!.position,
                        team: resultingSlot.player!.team,
                      })}
                    >
                      View {swap.startPlayer}
                    </Button>
                  ) : null}
                />
              );
            })}
          </div>
        </Panel>
      ) : (
        <Panel title="Recommended changes" eyebrow="0 changes"><EmptyState title="Already optimal" message="Sleeper's current starters already match NWR's optimal lineup for this week." /></Panel>
      )}
      <Panel title="Starting lineup" eyebrow={`Projected total ${formatNumber(result.projectedTotal, 1)} pts`}>
        {result.nonExactScoringInTotal ? (
          // NWR Sunday Readiness overnight cycle, Worker 3 (W7 fix): a
          // real, previously-undisclosed gap -- the projected total above
          // can genuinely blend league-exact points with generic
          // provider-scored K/DST points (or a partial league-exact K/DST
          // match) with no visible distinction. Hover a player's points
          // below for its real scoring basis.
          <p className="copy-muted">
            This total includes at least one player scored by generic provider points or a partial
            league-scoring match, not this league&apos;s exact scoring -- hover a player&apos;s points for its
            real basis.
          </p>
        ) : null}
        <div className="tier-player-grid">
          {result.starters.map((slot, index) => (
            <article key={index} className={slot.closeCall ? "tier-player-grid__article--close-call" : undefined}>
              <span>{SLOT_LABEL[slot.slotType] ?? slot.slotType}</span>
              <div>
                <strong>{slot.player?.playerName ?? "Empty slot"}</strong>
                <small>{slot.player ? `${slot.player.team} · ${slot.player.position}` : "No eligible player"}</small>
              </div>
              <b title={slot.player?.scoringContext ?? undefined}>
                {slot.player?.projectedPoints == null ? "—" : formatNumber(slot.player.projectedPoints, 1)}
              </b>
              <StatusBadge
                tone={slot.closeCall ? "review" : statusTone(slot.status)}
                label={slot.closeCall ? `CLOSE CALL vs ${slot.closeCallAlternative ?? "alt"} (${formatNumber(slot.closeCallMargin ?? 0, 1)})` : slot.status}
              />
              {slot.player ? (
                <Button
                  variant="ghost"
                  onClick={() => openPlayerDetail({
                    playerId: slot.player!.canonicalPlayerId ?? slot.player!.sleeperPlayerId,
                    playerName: slot.player!.playerName,
                    position: slot.player!.position,
                    team: slot.player!.team,
                  })}
                >
                  View
                </Button>
              ) : null}
            </article>
          ))}
        </div>
      </Panel>
      <Panel title="Bench" eyebrow={`${result.bench.length} players`}>
        <DataTable columns={benchColumns} rows={result.bench as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.sleeperPlayerId)} />
      </Panel>
      {/* NWR Sunday Readiness overnight cycle, Worker 2 (W2): reserve/taxi
          and locked-bench members are real roster coverage -- shown
          explicitly, never silently dropped, and never offered as a
          startable option. Distinct panels from "Not included this week"
          (a real status-override exclusion, e.g. SEASON_OUT). */}
      {result.reserve && result.reserve.length ? (
        <Panel title="Reserve / taxi (not startable)" eyebrow={`${result.reserve.length} player(s)`}>
          <p className="copy-muted">
            {result.reserve.map((player) => `${player.playerName}${player.isTaxi ? " (taxi)" : " (reserve)"}`).join(", ")}
            {" "}-- on your real reserve/taxi slot(s). Activation would be a separate roster transaction NWR does not perform here; not an available start this week.
          </p>
        </Panel>
      ) : null}
      {result.lockedUnavailable && result.lockedUnavailable.length ? (
        <Panel title="Locked -- game already started" eyebrow={`${result.lockedUnavailable.length} player(s)`}>
          <p className="copy-muted">
            {result.lockedUnavailable.map((player) => player.playerName).join(", ")}
            {" "}-- real kickoff for their game has already passed and they were not already in your starting lineup; cannot be legally added to a starting slot now.
          </p>
        </Panel>
      ) : null}
      {result.excluded.length ? (
        <Panel title="Not included this week" eyebrow={`${result.excluded.length} player(s)`}>
          <p className="copy-muted">{result.excluded.map((player) => player.playerName).join(", ")} -- no roster slot they're eligible for, or no usable projection.</p>
        </Panel>
      ) : null}
      {result.gameLock && result.gameLock.sourceStatus === "UNAVAILABLE" ? (
        <p className="copy-muted">Real kickoff/lock data was unavailable this pass -- no player was treated as locked. Recheck closer to kickoff.</p>
      ) : null}
    </> : null}
  </>;
}

// ---------------------------------------------------------------------------
// Waivers + Add/Drop + FAAB
// ---------------------------------------------------------------------------

// Exported for the Improve Team workspace (`improve-team.tsx`), which
// reuses this exact panel for its own ADD-DROP tab -- one detail view,
// not a second competing one.
export function formatKnownWaiverNumber(value: number | null | undefined): string {
  return value == null ? 'unavailable' : formatNumber(value, 1);
}

export function AddDropDetail({
  add,
  waivers,
  mode,
  onClose,
}: {
  add: WaiverAddCandidate;
  waivers: WaiversResult;
  mode: "THIS_WEEK" | "REST_OF_SEASON";
  onClose: () => void;
}) {
  const pairing = waivers.addDropPairings.find((row) => row.add.canonicalPlayerId === add.canonicalPlayerId) ?? null;
  const suggestedDrop: WaiverDropCandidate | null = pairing?.drop ?? null;
  // The backend supplies counts from the actual full Sleeper roster. Drop
  // candidates are intentionally only the legally droppable bench subset,
  // so deriving roster construction from that list would omit starters,
  // reserve/taxi assets, and out-of-model K/DST identities.
  const depthBefore = useMemo(
    () => ({ ...waivers.rosterPositionCounts }),
    [waivers.rosterPositionCounts],
  );
  const depthAfter = useMemo(() => {
    const counts = { ...depthBefore };
    if (suggestedDrop) counts[suggestedDrop.position] = Math.max(0, (counts[suggestedDrop.position] ?? 0) - 1);
    counts[add.position] = (counts[add.position] ?? 0) + 1;
    return counts;
  }, [depthBefore, suggestedDrop, add.position]);
  const positions = Array.from(new Set([...Object.keys(depthBefore), ...Object.keys(depthAfter)])).sort();
  const alternativeDrops = waivers.dropCandidates.filter((drop) => drop.canonicalPlayerId !== suggestedDrop?.canonicalPlayerId).slice(0, 3);

  return (
    <Panel title={`ADD ${add.playerName}${suggestedDrop ? ` / DROP ${suggestedDrop.playerName}` : ""}`} eyebrow="Add/Drop detail" action={<Button variant="ghost" onClick={onClose}>Close</Button>}>
      <div className="split-view">
        <div>
          <h3>Weekly-lineup impact</h3>
          {mode === "THIS_WEEK" ? (
            // NWR Sunday Readiness overnight cycle, Worker 3 (W5 fix):
            // `add.becomesStarter` now carries a REAL, independently
            // recomputed weekly-lineup answer (see `becomesStarterBasis`),
            // never the season-long flag it used to silently borrow --
            // and it can genuinely be `null` (not evaluated this pass),
            // which must read as "unavailable", never as a false "no".
            add.becomesStarterBasis === "THIS_WEEK_LINEUP_EVALUATION" ? (
              <p>
                {add.becomesStarter
                  ? `Projected to become a starter this week (real legal-lineup gain: ${formatNumber(add.thisWeekLineupGain ?? 0, 1)} pts).`
                  : `Would not become a starter this week under NWR's lineup optimizer (real legal-lineup gain: ${formatNumber(add.thisWeekLineupGain ?? 0, 1)} pts).`}
              </p>
            ) : (
              <p className="copy-muted">
                A real weekly-lineup evaluation was not computed for this candidate this pass -- this is
                NOT the same as "would not start". Weekly projected points: {formatKnownWaiverNumber(add.weeklyProjectedPoints)}.
              </p>
            )
          ) : <p className="copy-muted">Switch to THIS WEEK mode above for a weekly-lineup estimate.</p>}
          <h3>Rest-of-season impact</h3>
          <p>
            Replacement value {formatKnownWaiverNumber(add.rosReplacementValue)} · Marginal utility {formatKnownWaiverNumber(add.marginalUtility)}
            {suggestedDrop ? <> vs. dropping {suggestedDrop.playerName} ({formatKnownWaiverNumber(suggestedDrop.marginalUtility)}) — net {formatKnownWaiverNumber(pairing?.netMarginalUtility)}</> : null}
          </p>
          {/* Waiver Night V1 (Section 4, add/drop context repair): the "net"
              above is now a same-context comparison -- both sides measured
              against the roster AFTER the proposed drop, not a mix of two
              different rosters. Spelled out here so the owner can see both
              reference points, not just the final number, and so this is
              never mistaken for an authoritative total-roster/
              completed-transaction value. */}
          {suggestedDrop && pairing?.contextLabel === "SAME_CONTEXT_MARGINAL_COMPARISON" ? (
            <p className="copy-muted">
              Same-context comparison: adding {add.playerName} after dropping {suggestedDrop.playerName} would be worth{" "}
              {formatKnownWaiverNumber(pairing?.addUtilityVsPostDropRoster)} (vs. {formatKnownWaiverNumber(pairing?.addUtilityVsOriginalRoster)} against your roster as it stands today, before any drop);{" "}
              {suggestedDrop.playerName}'s own value on that same post-drop roster is {formatKnownWaiverNumber(pairing?.dropUtilityVsPostDropRoster)}.
              This is a same-context marginal comparison, not a total-roster or completed-transaction value.
            </p>
          ) : null}
          <h3>Status / risk</h3>
          <p>{add.marginalUtilityExplanation}{suggestedDrop ? <><br /><span className="copy-muted">Drop rationale: {suggestedDrop.explanation}</span></> : null}</p>
          <h3>FAAB recommendation</h3>
          {add.faabBidLowDollars == null ? <p className="copy-muted">No FAAB estimate available for this candidate.</p> : add.faabBidLowDollars <= 0 ? (
            <p className="copy-muted">No positive FAAB bid is recommended. {add.faabRationale}</p>
          ) : (
            <p>
              Suggested bid <strong>${add.faabBidLowDollars}–${add.faabBidHighDollars}</strong>{" "}
              <StatusBadge tone={FAAB_URGENCY_TONE[add.faabUrgency ?? ""] ?? "review"} label={`${add.faabUrgency ?? "unknown"} urgency`} />
              <br /><small className="copy-muted">{add.faabRationale}. Not a mathematically exact bid — a suggested range only; NWR has no competing-bidder model.</small>
            </p>
          )}
        </div>
        <div>
          <h3>Position depth on your roster</h3>
          <dl className="health-list">{positions.map((position) => <div key={position}><dt>{position}</dt><dd>{depthBefore[position] ?? 0} → {depthAfter[position] ?? 0}</dd></div>)}</dl>
          {!suggestedDrop ? (
            pairing?.contextLabel === "OPEN_ROSTER_SLOT_ADD_ONLY" ? (
              <p className="copy-muted">NWR verified a real open roster slot on your bench -- this add is legal without dropping anyone.</p>
            ) : pairing?.contextLabel === "NO_DROP_CANDIDATE_AVAILABLE" ? (
              <p className="copy-muted">This roster is full and NWR found no legal bench drop. The add is not currently executable; do not treat it as a completed move.</p>
            ) : (
              <p className="copy-muted">NWR did not suggest a drop pairing for this add -- pick one from the candidates below, or add without dropping if you have an open bench slot.</p>
            )
          ) : null}
          <h3>Alternative drops</h3>
          {alternativeDrops.length ? (
            <ul className="health-list">{alternativeDrops.map((drop) => <li key={drop.canonicalPlayerId}>{drop.playerName} ({drop.position}) — marginal utility {formatNumber(drop.marginalUtility ?? 0, 1)}</li>)}</ul>
          ) : <p className="copy-muted">No other real drop candidates on this roster.</p>}
        </div>
      </div>
    </Panel>
  );
}

export function WaiversPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  // Flaim-integration cycle (2026-09-19), Worker 4: capability gate, see
  // WeeklyHomePage above.
  const isSleeper = Boolean(data.leagueCapabilities?.hasVerifiedIdentity);
  const [mode, setMode] = useState<"THIS_WEEK" | "REST_OF_SEASON">("REST_OF_SEASON");
  const [week, setWeek] = useState(1);
  const [position, setPosition] = useState("ALL");
  const [view, setView] = useState("Available to add");
  const [selectedAddId, setSelectedAddId] = useState<string | null>(null);

  // NWR Waiver Night V1 (Worker 4, LIVE/SCENARIO budget separation): this
  // page is an unrouted legacy fallback (superseded by Improve Team's FAAB
  // tab, which now owns the real LIVE/SCENARIO budget UI). Simplified to
  // LIVE-only here -- no `budgetScenario` sent, so the backend derives the
  // real FAAB budget itself from this same request's own live Sleeper
  // reads. The old manually-editable "FAAB settings" panel (hardcoded
  // $100/$100/14-week defaults, indistinguishable from a real live number)
  // is removed rather than carried forward into the new contract.
  const loader = useCallback(
    () => (isSleeper
      ? client.redraftWaivers({
          mode,
          ...(mode === "THIS_WEEK" ? { week } : {}),
        })
      : null),
    [client, isSleeper, mode, week],
  );
  const { result, error, working, reload } = useAsync(loader, [isSleeper, mode, week, data.activeProfileId]);

  const positions = ["ALL", ...new Set((result?.addCandidates ?? []).map((row) => row.position))];
  const addRows = useMemo(() => (result?.addCandidates ?? []).filter((row) => position === "ALL" || row.position === position), [result, position]);
  const dropRows = useMemo(() => (result?.dropCandidates ?? []).filter((row) => position === "ALL" || row.position === position), [result, position]);
  const pairingRows = useMemo(() => (result?.addDropPairings ?? []).filter((row) => position === "ALL" || row.add.position === position), [result, position]);
  const selectedAdd = result?.addCandidates.find((row) => row.canonicalPlayerId === selectedAddId) ?? null;
  // NWR pre-UI architecture CLOSURE pass (directive section 5): the same
  // global Player Detail primitive Lineup uses above.
  const openPlayerDetail = usePlayerDetailOpener(data.activeProfileId, "WAIVER");

  const addColumns: TableColumn[] = [
    { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span> },
    { key: "rosOverallRank", label: "ROS rank", sort: "number", align: "right", render: (row) => row.rosOverallRank == null ? "Unranked" : `#${String(row.rosOverallRank)}` },
    { key: "weeklyProjectedPoints", label: mode === "THIS_WEEK" ? "This week pts" : "Weekly pts", sort: "number", align: "right", render: (row) => row.weeklyProjectedPoints == null ? "—" : formatNumber(Number(row.weeklyProjectedPoints), 1) },
    { key: "marginalUtility", label: mode === "THIS_WEEK" ? "Season utility (long-term)" : "Marginal utility", sort: "number", align: "right", render: (row) => row.marginalUtility == null ? "—" : formatNumber(Number(row.marginalUtility), 1) },
    // NWR Sunday Readiness overnight cycle, Worker 3 (W5 fix): THIS_WEEK
    // now ranks by this real, legal-lineup usable gain -- surfaced as its
    // own column rather than only implied by row order.
    ...(mode === "THIS_WEEK"
      ? [{
          key: "thisWeekLineupGain", label: "This week usable gain", sort: "number" as const, align: "right" as const,
          render: (row: Record<string, unknown>) => row.thisWeekLineupGain == null ? "Not evaluated" : formatNumber(Number(row.thisWeekLineupGain), 1),
        }]
      : []),
    {
      key: "becomesStarter", label: "Becomes starter", sort: "text",
      render: (row) => (
        row.becomesStarterBasis === "UNAVAILABLE_NOT_EVALUATED_THIS_PASS"
          ? <StatusBadge tone="review" label="Unknown" />
          : row.becomesStarter
            ? <StatusBadge tone="safe" label="Yes" />
            : "No"
      ),
    },
    {
      key: "faabBidLowDollars",
      label: "Suggested FAAB",
      sort: "number",
      align: "right",
      render: (row) => row.faabBidLowDollars == null ? "—" : (
        <span title={String(row.faabRationale ?? "")}>
          ${String(row.faabBidLowDollars)}–${String(row.faabBidHighDollars)}{" "}
          <StatusBadge tone={FAAB_URGENCY_TONE[String(row.faabUrgency)] ?? "review"} label={String(row.faabUrgency ?? "")} />
        </span>
      ),
    },
    {
      key: "playerDetail", label: "", render: (row) => (
        <Button variant="ghost" onClick={() => openPlayerDetail({ playerId: String(row.canonicalPlayerId), playerName: String(row.playerName), position: String(row.position), team: String(row.team) })}>View</Button>
      ),
    },
    { key: "action", label: "", render: (row) => <Button variant="secondary" onClick={() => setSelectedAddId(String(row.canonicalPlayerId))}>View Add/Drop</Button> },
  ];

  const dropColumns: TableColumn[] = [
    { key: "playerName", label: "Player", sort: "text" },
    { key: "position", label: "Pos", sort: "text" },
    { key: "marginalUtility", label: "Marginal utility", sort: "number", align: "right", render: (row) => row.marginalUtility == null ? "—" : formatNumber(Number(row.marginalUtility), 1) },
    { key: "explanation", label: "Why", sort: "text" },
  ];

  const pairingColumns: TableColumn[] = [
    { key: "addName", label: "Add", sort: "text", render: (row) => (row as unknown as (typeof pairingRows)[number]).add.playerName },
    { key: "dropName", label: "Drop", sort: "text", render: (row) => (row as unknown as (typeof pairingRows)[number]).drop?.playerName ?? "— (no drop needed)" },
    { key: "netMarginalUtility", label: "Net marginal utility", sort: "number", align: "right", render: (row) => { const value = (row as unknown as (typeof pairingRows)[number]).netMarginalUtility; return value == null ? "—" : formatNumber(value, 1); } },
    { key: "action", label: "", render: (row) => <Button variant="secondary" onClick={() => setSelectedAddId((row as unknown as (typeof pairingRows)[number]).add.canonicalPlayerId)}>View</Button> },
  ];

  return <>
    <PageHeader
      eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"}
      title="Waivers"
      description="Who should I add? Ranked by real marginal roster utility -- never a generic external ranking dump."
      status={result ? <StatusBadge tone="safe" label={`${result.addCandidates.length} candidates`} /> : undefined}
    />
    {!isSleeper ? <EmptyState title="Verified league data required" message="Waivers needs a live roster and the governed NWR ranking. Import league data (e.g. via Sleeper) to continue." /> : null}
    <div className="toolbar">
      <SegmentedControl label="Mode" options={["REST_OF_SEASON", "THIS_WEEK"]} value={mode} onChange={(value) => setMode(value as "THIS_WEEK" | "REST_OF_SEASON")} />
      {mode === "THIS_WEEK" ? <WeekControl week={week} onChange={setWeek} /> : null}
      <SelectField label="Position" value={position} onChange={setPosition} options={positions.map((value) => ({ value, label: value }))} />
      <SegmentedControl label="View" options={["Available to add", "Add/Drop pairings", "Consider dropping"]} value={view} onChange={setView} />
      <Button icon="activity" variant="secondary" onClick={reload} disabled={working}>{working ? "Reading…" : "Refresh"}</Button>
    </div>
    {/* NWR Sunday Readiness overnight cycle, Worker 3 (W5 fix): see the
        same caption on Improve Team's Targets tab (the real, routed
        surface -- this page is an unrouted legacy fallback, kept
        consistent anyway). THIS_WEEK now ranks by real, legal-lineup
        usable gain, not season marginal utility. */}
    <p className="copy-muted">
      {mode === "THIS_WEEK"
        ? "THIS WEEK ranks candidates by real, legal-lineup usable gain this week (an actual before/after roster simulation) -- long-term season value is shown separately, it does not drive this ranking."
        : "Ranked by real marginal roster utility (rest-of-season oriented). Switch to THIS WEEK to rank by real usable weekly-lineup gain instead."}
    </p>
    {result?.faabContext ? (
      <Panel title="FAAB (live)" eyebrow="Real, live Sleeper budget -- plan scenarios on the Improve Team FAAB tab instead">
        <p className="copy-muted">
          {result.faabContext.isFaabLeague === false
            ? `Waiver priority order, not FAAB -- your real position is #${result.faabContext.waiverPosition ?? "?"}.`
            : result.faabContext.remainingBudgetDollars != null
              ? `$${result.faabContext.remainingBudgetDollars} of $${result.faabContext.totalBudgetDollars} remaining, read live this request.`
              : "Live FAAB budget unavailable this request."}
        </p>
      </Panel>
    ) : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result?.rankingWarning ? <div className="alert-strip"><strong>Ranking unavailable</strong><span>{result.rankingWarning}</span></div> : null}
    {mode === "THIS_WEEK" ? <ProviderStatusLine health={result?.weeklyProviderHealth ?? null} /> : null}
    {result ? <>
      {view === "Available to add" ? <Panel title="Available to add" eyebrow={`${addRows.length} shown`}><DataTable columns={addColumns} rows={addRows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.canonicalPlayerId)} /></Panel> : null}
      {view === "Add/Drop pairings" ? <Panel title="Suggested add/drop pairings" eyebrow={`${pairingRows.length} shown`}><DataTable columns={pairingColumns} rows={pairingRows as unknown as Array<Record<string, unknown>>} rowKey={(row) => (row as unknown as (typeof pairingRows)[number]).add.canonicalPlayerId} /></Panel> : null}
      {view === "Consider dropping" ? <Panel title="Weakest current roster players" eyebrow={`${dropRows.length} shown, weakest first`}><DataTable columns={dropColumns} rows={dropRows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.canonicalPlayerId)} /></Panel> : null}
      {selectedAdd ? <AddDropDetail add={selectedAdd} waivers={result} mode={mode} onClose={() => setSelectedAddId(null)} /> : null}
      {result.unmatchedRosterSleeperPlayerIds.length ? (
        <p className="copy-muted">
          Roster slots outside this ranking:{" "}
          {describeUnmatchedRosterPlayers(result.unmatchedRosterSleeperPlayerIds, result.unmatchedRosterSleeperPlayers).join("; ")}
        </p>
      ) : null}
    </> : null}
  </>;
}

// ---------------------------------------------------------------------------
// My Roster (needed for Trade Analysis's "I give" picker; also a real,
// useful standalone read -- no existing page showed the owner's own roster
// with live Sleeper identity).
// ---------------------------------------------------------------------------

// NWR UI expansion pass (2026-09-12, League surface): split into an
// exported `MyRosterContent` (no `PageHeader` of its own) + a thin
// `MyRosterPage` wrapper, same shape as the Players/Improve Team/Trades
// consolidations before it -- pure extraction plus one real bug fix (see
// below), zero other behavior change. `MyRosterContent` is what the new
// unified League workspace's MY ROSTER tab actually renders (league.tsx);
// `MyRosterPage` is kept as an unrouted legacy fallback.
export function MyRosterContent({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  // Flaim-integration cycle (2026-09-19), Worker 4: capability gate, see
  // WeeklyHomePage above.
  const isSleeper = Boolean(data.leagueCapabilities?.hasVerifiedIdentity);
  const loader = useCallback(() => (isSleeper ? client.redraftMyRoster() : null), [client, isSleeper]);
  const { result, error, working } = useAsync(loader, [isSleeper, data.activeProfileId]);
  // Real bug found and fixed (before any live render, by reading this
  // component against the directive's "players clickable -> Player
  // Drawer" requirement): My Roster had NO drawer/"View" wiring at all,
  // unlike every other roster/table surface already adopted (Opponent
  // Rosters, Free Agents, Rankings, ...) -- confirmed by reading the
  // pre-existing component before assuming otherwise. Added the same
  // global primitive, alongside (not instead of) the existing "Add to
  // Trade Analysis" link.
  const openPlayerDetail = usePlayerDetailOpener(data.activeProfileId, "MY_ROSTER");
  const columns: TableColumn[] = useMemo(
    () => appendPlayerDetailColumn(
      [
        { key: "playerName", label: "Player", sort: "text" },
        { key: "position", label: "Pos", sort: "text" },
        { key: "team", label: "Team", sort: "text" },
        { key: "starter", label: "Lineup", sort: "text", render: (row) => row.starter ? <StatusBadge tone="safe" label="Starter" /> : "Bench" },
        { key: "identityStatus", label: "NWR identity", sort: "text", render: (row) => row.identityStatus === "MATCHED" ? <StatusBadge tone="safe" label="Matched" /> : <StatusBadge tone="review" label="Unmatched" /> },
        {
          key: "action", label: "", render: (row) => (
            <Link to={`/trade-analysis?giveSleeperId=${encodeURIComponent(String(row.sleeperPlayerId))}&giveName=${encodeURIComponent(String(row.playerName))}`}>
              Add to Trade Analysis
            </Link>
          ),
        },
      ],
      (row) => openPlayerDetail({ playerId: String(row.sleeperPlayerId), playerName: String(row.playerName), position: String(row.position), team: String(row.team) }),
    ),
    [openPlayerDetail],
  );
  // WU10 honesty fix (2026-09-15): tell the owner WHERE their last-known
  // roster actually lives (Draft Room's own board, real `updatedAtUtc`)
  // instead of just a dead end -- there is no live sync or manual roster
  // editor for these providers, so this is genuinely the only real
  // roster data NWR has for this league.
  const draftRosterAsOf = data.draftBoard?.updatedAtUtc;
  return <>
    {!isSleeper ? (
      <EmptyState
        title="Verified league data required"
        message={
          draftRosterAsOf
            ? `No live roster source is available for this league yet. NWR's last known roster for this league is from draft results as of ${draftRosterAsOf}; it does not reflect any waiver, trade, or free-agent move since.`
            : "No live roster source is available for this league yet, and no draft data has been recorded for this profile yet."
        }
        action={<Link to="/draft-room-v2">Open Draft Room (My Team)</Link>}
      />
    ) : null}
    {working ? <p className="draft-feedback">Reading current Sleeper roster…</p> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result?.rankingWarning ? <div className="alert-strip"><strong>Ranking unavailable</strong><span>{result.rankingWarning}</span></div> : null}
    <SnapshotProvenanceNotice provenance={result?.leagueStateProvenance} />
    {result ? <Panel title={`${result.roster.length} rostered players`} eyebrow="Read-only"><DataTable columns={columns} rows={result.roster as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.sleeperPlayerId)} /></Panel> : null}
  </>;
}

export function MyRosterPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  // Flaim-integration cycle (2026-09-19), Worker 4: capability gate, see
  // WeeklyHomePage above.
  const isSleeper = Boolean(data.leagueCapabilities?.hasVerifiedIdentity);
  return <>
    <PageHeader eyebrow="Live league state" title="My Roster" description="Your current live roster. Read-only." status={<StatusBadge tone={isSleeper ? "safe" : "blocked"} label={isSleeper ? "Live read-only" : "Verified league data required"} />} />
    <MyRosterContent client={client} data={data} />
  </>;
}

// ---------------------------------------------------------------------------
// Redraft Trade Analysis
// ---------------------------------------------------------------------------

// NWR UI expansion pass (2026-09-12, Trades surface): exported so the new
// unified `TradesPage` workspace (trades.tsx) can reuse the exact same
// picker primitive rather than a second one -- this page's own
// `TradeAnalysisPage`/`TradeFinderPage` below are otherwise left in place
// unchanged as unrouted legacy fallbacks (same precedent as `WaiversPage`
// after the Improve Team pass).
export type TradeSide = { sleeperPlayerId: string; name: string };

export function verdictFor(result: TradeAnalysisResult): { label: string; tone: "safe" | "review" | "blocked" } {
  const netUtility = result.netMarginalUtility;
  const rosValue = result.rosValueDelta;
  if (netUtility > 0 && rosValue >= 0) return { label: "Improves my roster", tone: "safe" };
  if (netUtility < 0 && rosValue <= 0) return { label: "Hurts my roster", tone: "blocked" };
  return { label: "Close", tone: "review" };
}

export function TradeSidePicker({
  label,
  side,
  onAdd,
  onRemove,
  candidates,
}: {
  label: string;
  side: TradeSide[];
  onAdd: (candidate: TradeSide) => void;
  onRemove: (sleeperPlayerId: string) => void;
  candidates: TradeSide[];
}) {
  const [query, setQuery] = useState("");
  const filtered = query.trim()
    ? candidates.filter((candidate) => candidate.name.toLowerCase().includes(query.trim().toLowerCase())).slice(0, 8)
    : [];
  return (
    <div className="trade-side-picker">
      <h3>{label}</h3>
      <SearchInput value={query} onChange={setQuery} placeholder="Search a player…" />
      {filtered.length ? (
        <ul className="trade-side-picker__results">
          {filtered.map((candidate) => (
            <li key={candidate.sleeperPlayerId}>
              <button type="button" onClick={() => { onAdd(candidate); setQuery(""); }}>{candidate.name}</button>
            </li>
          ))}
        </ul>
      ) : null}
      <ul className="trade-side-picker__selected">
        {side.map((player) => (
          <li key={player.sleeperPlayerId}>
            {player.name}
            <button type="button" onClick={() => onRemove(player.sleeperPlayerId)} aria-label={`Remove ${player.name}`}>×</button>
          </li>
        ))}
        {!side.length ? <li className="copy-muted">None selected</li> : null}
      </ul>
    </div>
  );
}

export function TradeAnalysisPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  // Flaim-integration cycle (2026-09-19), Worker 4: capability gate, see
  // WeeklyHomePage above.
  const isSleeper = Boolean(data.leagueCapabilities?.hasVerifiedIdentity);
  const [searchParams] = useSearchParams();
  const [gives, setGives] = useState<TradeSide[]>([]);
  const [receives, setReceives] = useState<TradeSide[]>([]);
  const [result, setResult] = useState<TradeAnalysisResult | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [working, setWorking] = useState(false);

  const myRosterLoader = useCallback(() => (isSleeper ? client.redraftMyRoster() : null), [client, isSleeper]);
  const { result: myRoster } = useAsync(myRosterLoader, [isSleeper, data.activeProfileId]);
  const opponentsLoader = useCallback(() => (isSleeper ? client.redraftOpponentRosters() : null), [client, isSleeper]);
  const { result: opponents } = useAsync(opponentsLoader, [isSleeper, data.activeProfileId]);
  // NWR pre-UI architecture CLOSURE pass (directive sections 1-2): the
  // same global Player Detail primitive Lineup/Waivers use, reused here
  // rather than a second drawer -- and the same shared status-badge
  // mapping (player-detail-state.ts) Draft/Trade Finder use below, not a
  // third, surface-local transformation.
  const openPlayerDetail = usePlayerDetailOpener(data.activeProfileId, "TRADE_ANALYSIS");

  const giveCandidates: TradeSide[] = useMemo(
    () => (myRoster?.roster ?? []).map((player) => ({ sleeperPlayerId: player.sleeperPlayerId, name: `${player.playerName} (${player.position})` })),
    [myRoster],
  );
  const receiveCandidates: TradeSide[] = useMemo(
    () => (opponents?.opponents ?? []).flatMap((opponent) => opponent.players.map((player) => ({ sleeperPlayerId: player.sleeperPlayerId, name: `${player.playerName} (${player.position}) — ${opponent.teamName}` }))),
    [opponents],
  );

  // select-and-jump prefill from Opponent Rosters ("Add to trade") or My
  // Roster ("Add to Trade Analysis") -- real Sleeper ids, no name matching.
  useEffect(() => {
    const receiveId = searchParams.get("receiveSleeperId");
    const receiveName = searchParams.get("receiveName");
    if (receiveId && receiveName) {
      setReceives((current) => (current.some((player) => player.sleeperPlayerId === receiveId) ? current : [...current, { sleeperPlayerId: receiveId, name: receiveName }]));
    }
    const giveId = searchParams.get("giveSleeperId");
    const giveName = searchParams.get("giveName");
    if (giveId && giveName) {
      setGives((current) => (current.some((player) => player.sleeperPlayerId === giveId) ? current : [...current, { sleeperPlayerId: giveId, name: giveName }]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const analyze = async () => {
    if (!gives.length || !receives.length) return;
    setWorking(true); setError(null); setResult(null);
    try {
      setResult(await client.redraftTradeAnalysis(gives.map((p) => p.sleeperPlayerId), receives.map((p) => p.sleeperPlayerId)));
    } catch (reason) {
      setError(reason instanceof NwrApiError ? reason : new NwrApiError("Trade analysis could not be read."));
    } finally {
      setWorking(false);
    }
  };

  const impactColumns: TableColumn[] = [
    { key: "playerName", label: "Player", sort: "text" },
    { key: "position", label: "Pos", sort: "text" },
    { key: "rosReplacementValue", label: "ROS replacement value", sort: "number", align: "right", render: (row) => row.rosReplacementValue == null ? "—" : formatNumber(Number(row.rosReplacementValue), 1) },
    { key: "marginalUtility", label: "Marginal utility", sort: "number", align: "right", render: (row) => row.marginalUtility == null ? "—" : formatNumber(Number(row.marginalUtility), 1) },
    { key: "becomesStarter", label: "Becomes starter", sort: "text", render: (row) => row.becomesStarter ? <StatusBadge tone="safe" label="Yes" /> : "No" },
    { key: "statusFlag", label: "Status/risk", sort: "text", render: (row) => row.statusFlag ? <StatusBadge tone="review" label={String(row.statusFlag)} /> : "—" },
    {
      // NWR pre-UI architecture CLOSURE pass (directive section 2): the
      // canonical PlayerAvailabilityStatus authority, already attached to
      // this row by the facade's shared `_player_availability_status_map()`
      // helper -- rendered here, never a second status heuristic.
      key: "playerAvailabilityStatus", label: "Availability", sort: "text",
      render: (row) => {
        const status = (row as unknown as TradePlayerImpact).playerAvailabilityStatus;
        return (
          <span title={status?.reason ?? "No status issue is recorded for this player in NWR's canonical availability authority."}>
            <StatusBadge tone={playerAvailabilityBadgeTone(status)} label={playerAvailabilityBadgeLabel(status)} />
          </span>
        );
      },
    },
    {
      key: "playerDetail", label: "", render: (row) => (
        <Button
          variant="ghost"
          onClick={() => openPlayerDetail({ playerId: String(row.playerId), playerName: String(row.playerName), position: String(row.position) })}
        >
          View
        </Button>
      ),
    },
  ];

  const verdict = result ? verdictFor(result) : null;

  return <>
    <PageHeader eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"} title="Redraft Trade Analysis" description="I-give / I-receive. Real, structured before/after impact -- never a single opaque trade score. NWR never proposes or accepts a trade on Sleeper." status={isSleeper ? undefined : <StatusBadge tone="blocked" label="Verified league data required" />} />
    {!isSleeper ? <EmptyState title="Verified league data required" message="Trade Analysis needs your live roster and a live opponent roster. Import league data (e.g. via Sleeper) to continue." /> : null}
    {isSleeper ? <>
      <Panel title="Build a trade">
        <div className="split-view">
          <TradeSidePicker label="I give" side={gives} candidates={giveCandidates} onAdd={(candidate) => setGives((current) => addUniqueTradeSideCandidate(current, candidate))} onRemove={(id) => setGives((current) => current.filter((p) => p.sleeperPlayerId !== id))} />
          <TradeSidePicker label="I receive" side={receives} candidates={receiveCandidates} onAdd={(candidate) => setReceives((current) => addUniqueTradeSideCandidate(current, candidate))} onRemove={(id) => setReceives((current) => current.filter((p) => p.sleeperPlayerId !== id))} />
        </div>
        <div className="profile-edit-actions">
          <Button icon="activity" disabled={!gives.length || !receives.length || working} onClick={() => void analyze()}>{working ? "Analyzing…" : "Analyze trade"}</Button>
          <Link to="/my-roster">Browse my roster</Link>
          <Link to="/opponent-rosters">Browse opponent rosters</Link>
        </div>
      </Panel>
      {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
      {result ? <>
        <section className={`lean-banner lean-banner--${verdict?.tone}`}>
          <span>NWR trade verdict</span>
          <strong>{verdict?.label}</strong>
          <p>
            Net marginal utility {formatNumber(result.netMarginalUtility, 1)} · ROS value delta {formatNumber(result.rosValueDelta, 1)} ·
            Starting lineup value {formatNumber(result.startingLineupValueBefore, 1)} → {formatNumber(result.startingLineupValueAfter, 1)}
            {" "}({result.startingLineupValueDelta >= 0 ? "+" : ""}{formatNumber(result.startingLineupValueDelta, 1)})
          </p>
        </section>
        <div className="metric-grid">
          <MetricCard label="Bench contingency value" value={`${formatNumber(result.benchContingencyValueBefore, 1)} → ${formatNumber(result.benchContingencyValueAfter, 1)}`} detail="Depth remaining if a starter goes down" icon="layers" tone="violet" />
          <MetricCard label="Starter holes" value={`${result.starterHolesBefore.length} → ${result.starterHolesAfter.length}`} detail={result.starterHolesAfter.join(", ") || "None after trade"} icon="alert" tone="crimson" />
          <MetricCard label="Championship equity" value={result.championshipEquityNote ? "Noted" : "Not evaluated"} detail={result.championshipEquityNote ?? "Only shown where genuinely supported"} icon="target" tone="gold" />
        </div>
        {result.riskFlags.length ? <div className="alert-strip"><strong>Risk flags</strong><span>{result.riskFlags.join(" · ")}</span></div> : null}
        <div className="split-view">
          <Panel title="You give" eyebrow={`${result.gives.length} player(s)`}><DataTable columns={impactColumns} rows={result.gives as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.playerId)} /></Panel>
          <Panel title="You receive" eyebrow={`${result.receives.length} player(s)`}><DataTable columns={impactColumns} rows={result.receives as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.playerId)} /></Panel>
        </div>
        <Panel title="Position redundancy" eyebrow="Before → after">
          <dl className="health-list">
            {Array.from(new Set([...Object.keys(result.positionRedundancyBefore), ...Object.keys(result.positionRedundancyAfter)])).sort().map((position) => (
              <div key={position}><dt>{position}</dt><dd>{result.positionRedundancyBefore[position] ?? 0} → {result.positionRedundancyAfter[position] ?? 0}</dd></div>
            ))}
          </dl>
        </Panel>
      </> : null}
    </> : null}
  </>;
}

// ---------------------------------------------------------------------------
// Trade Finder
// ---------------------------------------------------------------------------

function TradeFinderCard({
  candidate,
  onViewPlayer,
}: {
  candidate: TradeFinderCandidate;
  onViewPlayer: (player: { playerId: string; playerName: string }) => void;
}) {
  const fits = candidate.myNetMarginalUtility > 0 && candidate.opponentNetMarginalUtility > 0;
  return (
    <article className="trade-finder-card">
      <header>
        <strong>vs. {candidate.opponentTeamName}</strong>
        <StatusBadge tone={fits ? "safe" : "review"} label={fits ? "Mutual improvement" : "One-sided"} />
      </header>
      <p>
        You send: <strong>{candidate.myGivePlayerName}</strong>{" "}
        <StatusBadge tone={playerAvailabilityBadgeTone(candidate.myGivePlayerAvailabilityStatus)} label={playerAvailabilityBadgeLabel(candidate.myGivePlayerAvailabilityStatus)} />{" "}
        <Button variant="ghost" onClick={() => onViewPlayer({ playerId: candidate.myGivePlayerId, playerName: candidate.myGivePlayerName })}>View</Button>
      </p>
      <p>
        You receive: <strong>{candidate.opponentGivePlayerName}</strong>{" "}
        <StatusBadge tone={playerAvailabilityBadgeTone(candidate.opponentGivePlayerAvailabilityStatus)} label={playerAvailabilityBadgeLabel(candidate.opponentGivePlayerAvailabilityStatus)} />{" "}
        <Button variant="ghost" onClick={() => onViewPlayer({ playerId: candidate.opponentGivePlayerId, playerName: candidate.opponentGivePlayerName })}>View</Button>
      </p>
      <p className="copy-muted">
        Why it may fit: {fits
          ? "both sides' real marginal roster utility improves under NWR's evaluator."
          : "only one side's marginal utility improves under NWR's evaluator -- the other team may not agree."}
      </p>
      <p>NWR impact: your net marginal utility {formatNumber(candidate.myNetMarginalUtility, 1)} · ROS value delta {formatNumber(candidate.myRosValueDelta, 1)} · their net marginal utility {formatNumber(candidate.opponentNetMarginalUtility, 1)}</p>
      {/* NWR Post-UI closure pass (bug 2): the old version of this link
          built its query string directly from `candidate.myGivePlayerId`/
          `opponentGivePlayerId` -- NWR's own canonical ids -- which
          `TradeAnalysisPage` then sent to `redraftTradeAnalysis` as if they
          were raw Sleeper ids, an always-fails identity-boundary bug for
          the opponent side. `tradeFinderAnalysisLinkTarget` resolves the
          real raw Sleeper id the backend now returns for each side instead
          -- an unresolved id is disclosed honestly rather than building a
          link guaranteed to fail. */}
      {(() => {
        const target = tradeFinderAnalysisLinkTarget(candidate);
        return target.kind === "ok"
          ? <Link to={target.href}>Open in Trade Analysis</Link>
          : <p className="copy-muted" title={target.reason ?? undefined}>Open in Trade Analysis unavailable: {target.reason}</p>;
      })()}
    </article>
  );
}

export function TradeFinderPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  // Flaim-integration cycle (2026-09-19), Worker 4: capability gate, see
  // WeeklyHomePage above.
  const isSleeper = Boolean(data.leagueCapabilities?.hasVerifiedIdentity);
  const loader = useCallback(() => (isSleeper ? client.redraftTradeFinder() : null), [client, isSleeper]);
  const { result, error, working, reload } = useAsync(loader, [isSleeper, data.activeProfileId]);
  // NWR pre-UI architecture CLOSURE pass (directive sections 1-2): the
  // same global Player Detail primitive as Trade Analysis above -- a
  // candidate card's "View" opens the exact same drawer/authority, no
  // second player-detail system for Trade Finder.
  const openPlayerDetail = usePlayerDetailOpener(data.activeProfileId, "TRADE_FINDER");
  return <>
    <PageHeader
      eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"}
      title="Trade Finder"
      description="Real win-win candidates evaluated against every live opponent roster. NWR never claims an opponent will accept -- no acceptance model exists."
      status={result ? <StatusBadge tone="safe" label={`${result.candidates.length} candidates`} /> : undefined}
      actions={<Button icon="activity" onClick={reload} disabled={working} variant="secondary">{working ? "Searching…" : "Refresh"}</Button>}
    />
    {!isSleeper ? <EmptyState title="Verified league data required" message="Trade Finder needs your live roster and every live opponent roster. Import league data (e.g. via Sleeper) to continue." /> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result && result.candidates.length === 0 ? <EmptyState title="No win-win candidates found" message="NWR's evaluator did not find any 1-for-1 package where both sides' real marginal utility improves right now." /> : null}
    {result && result.candidates.length ? <div className="trade-finder-grid">{result.candidates.map((candidate, index) => <TradeFinderCard key={`${candidate.opponentRosterId}-${candidate.myGivePlayerId}-${index}`} candidate={candidate} onViewPlayer={(player) => openPlayerDetail({ playerId: player.playerId, playerName: player.playerName, position: "" })} />)}</div> : null}
  </>;
}
