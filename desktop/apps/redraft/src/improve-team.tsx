import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type {
  ExternalConsensusStatus,
  KdstStreamerResult,
  RedraftBootstrap,
  WaiverAddCandidate,
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
  normalizeCommandSearch,
} from "@nwr/ui";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { DecisionExplain } from "./decision-explain";
import { explainStreamerPlay, explainWaiverTarget } from "./improve-team-explain";
import { AddDropDetail } from "./in-season";
import { leagueFormat } from "./league-context";
import { STREAMER_HORIZON_OPTIONS, STREAMER_HORIZON_WEEKS, type StreamerHorizon } from "./pages";
import { usePlayerDetailOpener } from "./player-detail-context";
import { playerAvailabilityBadgeLabel, playerAvailabilityBadgeTone } from "./player-detail-state";
import {
  FAAB_URGENCY_TONE,
  FREE_AGENT_COLUMNS,
  ProviderStatusLine,
  WeekControl,
  appendPlayerDetailColumn,
  useAsync,
  useFreeAgents,
} from "./weekly-shared";

/**
 * NWR UI expansion pass (2026-09-12, Improve Team surface): ONE coherent
 * owner workspace answering "How can I improve my roster?", unifying the
 * previously separately-built Waivers / Add-Drop / FAAB / K-DST Streamer /
 * Free Agents pages under a single set of tabs (TARGETS / ADD-DROP / FAAB /
 * STREAMERS / ALL FREE AGENTS). Presentation-layer only, over the exact
 * same frozen contracts those pages already read (`redraftWaivers` /
 * `kdstStreamer` / `redraftFreeAgents`, unchanged) -- no new scoring, no
 * new marginal-utility/FAAB/ECR heuristic. See `improve-team-explain.ts`
 * for the pure grammar derivation and `WaiversPage`/`WeeklyToolsPage`/
 * `FreeAgentsPage` (in-season.tsx / pages.tsx, left in place as harmless,
 * unlinked-from-nav legacy fallbacks) for the pages this consolidates.
 */

type ImproveTeamTab = "targets" | "add-drop" | "faab" | "streamers" | "free-agents";

const IMPROVE_TEAM_TABS: Array<{ key: ImproveTeamTab; label: string }> = [
  { key: "targets", label: "Targets" },
  { key: "add-drop", label: "Add/Drop" },
  { key: "faab", label: "FAAB" },
  { key: "streamers", label: "Streamers" },
  { key: "free-agents", label: "All Free Agents" },
];

const TARGETS_DISPLAY_CAP = 10;

type PlayerViewer = (player: { playerId: string; playerName: string; position?: string; team?: string }) => void;

export function ImproveTeamPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get("tab");
  const tab: ImproveTeamTab = IMPROVE_TEAM_TABS.some((item) => item.key === tabParam) ? (tabParam as ImproveTeamTab) : "targets";
  const setTab = useCallback(
    (next: ImproveTeamTab) => {
      const nextParams = new URLSearchParams(searchParams);
      nextParams.set("tab", next);
      setSearchParams(nextParams, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  // Shared Waivers read -- backs Targets, Add-Drop, and FAAB alike (all
  // three are different views over the exact same `WaiversResult`).
  const [mode, setMode] = useState<"THIS_WEEK" | "REST_OF_SEASON">("REST_OF_SEASON");
  const [week, setWeek] = useState(1);
  const [position, setPosition] = useState("ALL");
  const [remainingBudget, setRemainingBudget] = useState(100);
  const [weeksRemaining, setWeeksRemaining] = useState(14);
  const [totalBudget, setTotalBudget] = useState(100);
  const [selectedAddId, setSelectedAddId] = useState<string | null>(null);

  const waiversLoader = useCallback(
    () => (isSleeper
      ? client.redraftWaivers({
        mode,
        remainingBudgetDollars: remainingBudget,
        weeksRemaining,
        totalBudgetDollars: totalBudget,
        ...(mode === "THIS_WEEK" ? { week } : {}),
      })
      : null),
    [client, isSleeper, mode, week, remainingBudget, weeksRemaining, totalBudget],
  );
  const { result: waivers, error: waiversError, working: waiversWorking, reload: reloadWaivers } = useAsync(
    waiversLoader,
    [isSleeper, mode, week, remainingBudget, weeksRemaining, totalBudget, data.activeProfileId],
  );

  const positions = useMemo(() => ["ALL", ...new Set((waivers?.addCandidates ?? []).map((row) => row.position))], [waivers]);
  const addRows = useMemo(
    () => (waivers?.addCandidates ?? []).filter((row) => position === "ALL" || row.position === position),
    [waivers, position],
  );

  // K/DST Streamer read -- own week/horizon, independent of the Waivers
  // week above (a streamer decision and a weekly-lineup decision are real,
  // separate NFL weeks the owner may be planning at once).
  const [streamerWeek, setStreamerWeek] = useState(1);
  const [streamerHorizon, setStreamerHorizon] = useState<StreamerHorizon>("This Week");
  const [streamerResults, setStreamerResults] = useState<KdstStreamerResult[]>([]);
  const [streamerError, setStreamerError] = useState<NwrApiError | null>(null);
  const [streamerWorking, setStreamerWorking] = useState(false);
  const provider: ExternalConsensusStatus | undefined = data.externalConsensus;
  useEffect(() => {
    setStreamerResults([]);
    setStreamerError(null);
  }, [data.activeProfileId]);
  const loadStreamers = useCallback(async () => {
    if (streamerWorking || !provider?.configured) return;
    setStreamerWorking(true);
    setStreamerError(null);
    setStreamerResults([]);
    const weekCount = STREAMER_HORIZON_WEEKS[streamerHorizon];
    const loaded: KdstStreamerResult[] = [];
    try {
      // Sequential, not parallel -- mirrors WeeklyToolsPage's own reasoning:
      // caps this at 3 real FantasyPros ECR reads, never a burst.
      for (let offset = 0; offset < weekCount; offset += 1) {
        const targetWeek = Math.min(18, streamerWeek + offset);
        loaded.push(await client.kdstStreamer(targetWeek));
      }
      setStreamerResults(loaded);
    } catch (reason) {
      setStreamerError(reason instanceof NwrApiError ? reason : new NwrApiError("K/DST Streamer could not read its sources."));
    } finally {
      setStreamerWorking(false);
    }
  }, [streamerWorking, provider, streamerHorizon, streamerWeek, client]);

  // Free Agents read -- the browse/deep-search mode of this same workspace.
  const { result: freeAgents, error: freeAgentsError, working: freeAgentsWorking } = useFreeAgents(
    client,
    isSleeper ? data.activeProfileId : null,
  );
  const [freeAgentQuery, setFreeAgentQuery] = useState("");

  const openPlayerDetail = usePlayerDetailOpener(data.activeProfileId, "IMPROVE_TEAM");

  const freeAgentColumns = useMemo(
    () => appendPlayerDetailColumn(FREE_AGENT_COLUMNS, (row) => openPlayerDetail({
      playerId: String(row.playerId ?? row.sleeperPlayerId),
      playerName: String(row.playerName),
      position: String(row.position),
      team: String(row.team),
    })),
    [openPlayerDetail],
  );
  const filteredFreeAgents = useMemo(() => {
    const rows = freeAgents?.freeAgents ?? [];
    const query = normalizeCommandSearch(freeAgentQuery);
    const matched = query
      ? rows.filter((row) => normalizeCommandSearch(row.playerName).includes(query) || normalizeCommandSearch(row.team).includes(query))
      : rows;
    return matched as unknown as Array<Record<string, unknown>>;
  }, [freeAgents, freeAgentQuery]);

  return <>
    <PageHeader
      eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"}
      title="Improve Team"
      description="How can I improve my roster? Targets, Add/Drop, FAAB, Streamers, and the full free agent pool -- one workspace, ranked by NWR's real marginal roster utility."
      status={waivers ? <StatusBadge tone="safe" label={`${waivers.addCandidates.length} targets`} /> : undefined}
    />
    {!isSleeper ? <EmptyState title="Sleeper league required" message="Improve Team needs a live Sleeper roster and the governed NWR ranking." /> : null}
    <nav aria-label="Improve Team sections" className="nwr-tabbar" role="tablist">
      {IMPROVE_TEAM_TABS.map((item) => (
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

    {tab === "targets" ? (
      <TargetsTab
        addRows={addRows}
        error={waiversError}
        mode={mode}
        onOpenAddDrop={(id) => { setSelectedAddId(id); setTab("add-drop"); }}
        onOpenPlayer={openPlayerDetail}
        position={position}
        positions={positions}
        reload={reloadWaivers}
        setMode={setMode}
        setPosition={setPosition}
        setWeek={setWeek}
        waivers={waivers}
        week={week}
        working={waiversWorking}
      />
    ) : null}

    {tab === "add-drop" ? (
      <AddDropTab
        error={waiversError}
        mode={mode}
        onOpenPlayer={openPlayerDetail}
        position={position}
        positions={positions}
        reload={reloadWaivers}
        selectedAddId={selectedAddId}
        setPosition={setPosition}
        setSelectedAddId={setSelectedAddId}
        waivers={waivers}
        working={waiversWorking}
      />
    ) : null}

    {tab === "faab" ? (
      <FaabTab
        error={waiversError}
        onOpenPlayer={openPlayerDetail}
        remainingBudget={remainingBudget}
        setRemainingBudget={setRemainingBudget}
        setTotalBudget={setTotalBudget}
        setWeeksRemaining={setWeeksRemaining}
        totalBudget={totalBudget}
        waivers={waivers}
        weeksRemaining={weeksRemaining}
      />
    ) : null}

    {tab === "streamers" ? (
      <StreamersTab
        error={streamerError}
        hasProfile={Boolean(data.activeProfile)}
        horizon={streamerHorizon}
        onLoad={() => void loadStreamers()}
        onOpenPlayer={openPlayerDetail}
        provider={provider}
        results={streamerResults}
        setHorizon={setStreamerHorizon}
        setWeek={setStreamerWeek}
        week={streamerWeek}
        working={streamerWorking}
      />
    ) : null}

    {tab === "free-agents" ? (
      <AllFreeAgentsTab
        columns={freeAgentColumns}
        error={freeAgentsError}
        isSleeper={isSleeper}
        query={freeAgentQuery}
        result={freeAgents}
        rows={filteredFreeAgents}
        setQuery={setFreeAgentQuery}
        working={freeAgentsWorking}
      />
    ) : null}
  </>;
}

// ---------------------------------------------------------------------------
// TARGETS -- the curated, capped, DecisionExplain-card recommendation view.
// ---------------------------------------------------------------------------

function TargetsTab({
  mode,
  setMode,
  week,
  setWeek,
  position,
  setPosition,
  positions,
  waivers,
  error,
  working,
  reload,
  addRows,
  onOpenAddDrop,
  onOpenPlayer,
}: {
  mode: "THIS_WEEK" | "REST_OF_SEASON";
  setMode: (mode: "THIS_WEEK" | "REST_OF_SEASON") => void;
  week: number;
  setWeek: (week: number) => void;
  position: string;
  setPosition: (position: string) => void;
  positions: string[];
  waivers: WaiversResult | null;
  error: NwrApiError | null;
  working: boolean;
  reload: () => void;
  addRows: WaiverAddCandidate[];
  onOpenAddDrop: (canonicalPlayerId: string) => void;
  onOpenPlayer: PlayerViewer;
}) {
  const capped = addRows.slice(0, TARGETS_DISPLAY_CAP);
  return <>
    <div className="toolbar">
      <SegmentedControl label="Mode" options={["REST_OF_SEASON", "THIS_WEEK"]} value={mode} onChange={(value) => setMode(value as "THIS_WEEK" | "REST_OF_SEASON")} />
      {mode === "THIS_WEEK" ? <WeekControl week={week} onChange={setWeek} /> : null}
      <SelectField label="Position" value={position} onChange={setPosition} options={positions.map((value) => ({ value, label: value }))} />
      <Button icon="activity" variant="secondary" onClick={reload} disabled={working}>{working ? "Reading…" : "Refresh"}</Button>
    </div>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {waivers?.rankingWarning ? <div className="alert-strip"><strong>Ranking unavailable</strong><span>{waivers.rankingWarning}</span></div> : null}
    {mode === "THIS_WEEK" ? <ProviderStatusLine health={waivers?.weeklyProviderHealth ?? null} /> : null}
    {working && !waivers ? <p className="draft-feedback">Reading current waiver targets…</p> : null}
    {waivers && capped.length === 0 ? (
      <EmptyState
        title="No available recommendation"
        message="No add candidate currently beats a player already on your roster under NWR's real marginal roster utility. Check back after this week's games, or browse the full free agent pool."
      />
    ) : null}
    {capped.length ? <>
      <p className="nwr-text-section-heading">
        Top targets{addRows.length > capped.length ? ` — showing ${capped.length} of ${addRows.length}, refine by position or open Add/Drop for the full list` : ""}
      </p>
      <div className="nwr-action-grid">
        {capped.map((add, index) => {
          const pairing = waivers?.addDropPairings.find((row) => row.add.canonicalPlayerId === add.canonicalPlayerId) ?? null;
          const alternativeAdd = capped[index + 1] ?? null;
          const explanation = explainWaiverTarget(add, pairing, mode, alternativeAdd);
          return (
            <DecisionExplain
              key={add.canonicalPlayerId}
              headline={explanation.headline}
              why={explanation.why}
              bid={explanation.bid}
              thisWeekImpact={explanation.thisWeekImpact}
              rosImpact={explanation.rosImpact}
              alternative={explanation.alternative}
              tone={explanation.tone}
              confidence={explanation.confidence}
              status={{ tone: playerAvailabilityBadgeTone(add.playerAvailabilityStatus), label: playerAvailabilityBadgeLabel(add.playerAvailabilityStatus) }}
              actions={<>
                <Button variant="ghost" onClick={() => onOpenPlayer({ playerId: add.canonicalPlayerId, playerName: add.playerName, position: add.position, team: add.team })}>View {add.playerName}</Button>
                <Button variant="secondary" onClick={() => onOpenAddDrop(add.canonicalPlayerId)}>Open in Add/Drop</Button>
              </>}
            />
          );
        })}
      </div>
    </> : null}
  </>;
}

// ---------------------------------------------------------------------------
// ADD-DROP -- the full browse/pairing workflow (was WaiversPage's table
// body). Same `WaiversResult`, a different, more exhaustive view of it.
// ---------------------------------------------------------------------------

function AddDropTab({
  waivers,
  error,
  working,
  reload,
  position,
  setPosition,
  positions,
  selectedAddId,
  setSelectedAddId,
  mode,
  onOpenPlayer,
}: {
  waivers: WaiversResult | null;
  error: NwrApiError | null;
  working: boolean;
  reload: () => void;
  position: string;
  setPosition: (position: string) => void;
  positions: string[];
  selectedAddId: string | null;
  setSelectedAddId: (id: string | null) => void;
  mode: "THIS_WEEK" | "REST_OF_SEASON";
  onOpenPlayer: PlayerViewer;
}) {
  const [view, setView] = useState("Available to add");
  const addRows = useMemo(() => (waivers?.addCandidates ?? []).filter((row) => position === "ALL" || row.position === position), [waivers, position]);
  const dropRows = useMemo(() => (waivers?.dropCandidates ?? []).filter((row) => position === "ALL" || row.position === position), [waivers, position]);
  const pairingRows = useMemo(() => (waivers?.addDropPairings ?? []).filter((row) => position === "ALL" || row.add.position === position), [waivers, position]);
  const selectedAdd = waivers?.addCandidates.find((row) => row.canonicalPlayerId === selectedAddId) ?? null;

  const addColumns: TableColumn[] = [
    { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span> },
    { key: "rosOverallRank", label: "ROS rank", sort: "number", align: "right", render: (row) => row.rosOverallRank == null ? "Unranked" : `#${String(row.rosOverallRank)}` },
    { key: "weeklyProjectedPoints", label: mode === "THIS_WEEK" ? "This week pts" : "Weekly pts", sort: "number", align: "right", render: (row) => row.weeklyProjectedPoints == null ? "—" : formatNumber(Number(row.weeklyProjectedPoints), 1) },
    { key: "marginalUtility", label: "Marginal utility", sort: "number", align: "right", render: (row) => row.marginalUtility == null ? "—" : formatNumber(Number(row.marginalUtility), 1) },
    { key: "becomesStarter", label: "Becomes starter", sort: "text", render: (row) => row.becomesStarter ? <StatusBadge tone="safe" label="Yes" /> : "No" },
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
        <Button variant="ghost" onClick={() => onOpenPlayer({ playerId: String(row.canonicalPlayerId), playerName: String(row.playerName), position: String(row.position), team: String(row.team) })}>View</Button>
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
    <div className="toolbar">
      <SelectField label="Position" value={position} onChange={setPosition} options={positions.map((value) => ({ value, label: value }))} />
      <SegmentedControl label="View" options={["Available to add", "Add/Drop pairings", "Consider dropping"]} value={view} onChange={setView} />
      <Button icon="activity" variant="secondary" onClick={reload} disabled={working}>{working ? "Reading…" : "Refresh"}</Button>
    </div>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {waivers ? <>
      {view === "Available to add" ? (
        <Panel title="Available to add" eyebrow={`${addRows.length} shown`}>
          {addRows.length ? <DataTable columns={addColumns} rows={addRows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.canonicalPlayerId)} /> : <EmptyState title="No available recommendation" message="No add candidates match this position filter." />}
        </Panel>
      ) : null}
      {view === "Add/Drop pairings" ? (
        <Panel title="Suggested add/drop pairings" eyebrow={`${pairingRows.length} shown`}>
          {pairingRows.length ? <DataTable columns={pairingColumns} rows={pairingRows as unknown as Array<Record<string, unknown>>} rowKey={(row) => (row as unknown as (typeof pairingRows)[number]).add.canonicalPlayerId} /> : <EmptyState title="No available recommendation" message="No add/drop pairing matches this position filter." />}
        </Panel>
      ) : null}
      {view === "Consider dropping" ? (
        <Panel title="Weakest current roster players" eyebrow={`${dropRows.length} shown, weakest first`}>
          {dropRows.length ? <DataTable columns={dropColumns} rows={dropRows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.canonicalPlayerId)} /> : <EmptyState title="No drop candidates" message="No roster player matches this position filter." />}
        </Panel>
      ) : null}
      {selectedAdd ? <AddDropDetail add={selectedAdd} waivers={waivers} mode={mode} onClose={() => setSelectedAddId(null)} /> : null}
      {waivers.unmatchedRosterSleeperPlayerIds.length ? <p className="copy-muted">Unresolved roster Sleeper IDs: {waivers.unmatchedRosterSleeperPlayerIds.join(", ")}</p> : null}
    </> : null}
  </>;
}

// ---------------------------------------------------------------------------
// FAAB -- budget planning: settings + every real bid estimate, sorted by
// the backend's own urgency signal, rendered as DecisionExplain cards.
// ---------------------------------------------------------------------------

const FAAB_URGENCY_RANK: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };

function FaabTab({
  waivers,
  error,
  remainingBudget,
  setRemainingBudget,
  totalBudget,
  setTotalBudget,
  weeksRemaining,
  setWeeksRemaining,
  onOpenPlayer,
}: {
  waivers: WaiversResult | null;
  error: NwrApiError | null;
  remainingBudget: number;
  setRemainingBudget: (value: number) => void;
  totalBudget: number;
  setTotalBudget: (value: number) => void;
  weeksRemaining: number;
  setWeeksRemaining: (value: number) => void;
  onOpenPlayer: PlayerViewer;
}) {
  const bidCandidates = useMemo(
    () => (waivers?.addCandidates ?? [])
      .filter((row) => row.faabBidLowDollars != null)
      .slice()
      .sort((a, b) => (FAAB_URGENCY_RANK[a.faabUrgency ?? ""] ?? 3) - (FAAB_URGENCY_RANK[b.faabUrgency ?? ""] ?? 3) || (b.marginalUtility ?? 0) - (a.marginalUtility ?? 0)),
    [waivers],
  );
  const perWeekBudget = weeksRemaining > 0 ? remainingBudget / weeksRemaining : remainingBudget;

  return <>
    <div className="metric-grid">
      <MetricCard icon="activity" label="Remaining budget" value={`$${remainingBudget}`} detail={`of $${totalBudget} total`} tone="gold" />
      <MetricCard icon="target" label="Weeks remaining" value={weeksRemaining} detail="regular season weeks left" tone="violet" />
      <MetricCard icon="board" label="Per-week budget" value={`$${perWeekBudget.toFixed(1)}`} detail="remaining ÷ weeks remaining" tone="cyan" />
    </div>
    <Panel title="FAAB settings" eyebrow="Used to compute every suggested bid range below">
      <div className="profile-edit-actions">
        <label className="form-field"><span>Remaining budget ($)</span><input type="number" min={0} value={remainingBudget} onChange={(event) => setRemainingBudget(Math.max(0, Number(event.target.value) || 0))} /></label>
        <label className="form-field"><span>Total season budget ($)</span><input type="number" min={1} value={totalBudget} onChange={(event) => setTotalBudget(Math.max(1, Number(event.target.value) || 1))} /></label>
        <label className="form-field"><span>Weeks remaining</span><input type="number" min={1} max={18} value={weeksRemaining} onChange={(event) => setWeeksRemaining(Math.min(18, Math.max(1, Number(event.target.value) || 1)))} /></label>
      </div>
    </Panel>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {waivers && bidCandidates.length === 0 ? (
      <EmptyState title="No available recommendation" message="No current add candidate carries a real FAAB estimate. FAAB guidance needs a live Sleeper league with waivers still open." />
    ) : null}
    {bidCandidates.length ? (
      <div className="nwr-action-grid">
        {bidCandidates.map((candidate) => {
          const pairing = waivers?.addDropPairings.find((row) => row.add.canonicalPlayerId === candidate.canonicalPlayerId) ?? null;
          const explanation = explainWaiverTarget(candidate, pairing, "REST_OF_SEASON", null);
          return (
            <DecisionExplain
              key={candidate.canonicalPlayerId}
              headline={`BID ${explanation.bid ?? "—"} for ${candidate.playerName}`}
              why={candidate.faabRationale || explanation.why}
              rosImpact={explanation.rosImpact}
              tone="recommended"
              status={{ tone: FAAB_URGENCY_TONE[candidate.faabUrgency ?? ""] ?? "review", label: `${candidate.faabUrgency ?? "unknown"} urgency` }}
              actions={<Button variant="ghost" onClick={() => onOpenPlayer({ playerId: candidate.canonicalPlayerId, playerName: candidate.playerName, position: candidate.position, team: candidate.team })}>View {candidate.playerName}</Button>}
            />
          );
        })}
      </div>
    ) : null}
  </>;
}

// ---------------------------------------------------------------------------
// STREAMERS -- same DecisionExplain grammar as Targets/FAAB (directive:
// "not feel like a different app"), plus the full ECR comparison table for
// a deep, position-by-position read.
// ---------------------------------------------------------------------------

// KdstStreamerRow carries no canonical player id (unchanged backend
// contract) -- a stable synthetic key from real, already-known identity
// fields (position + name) is the honest choice here, matching how this
// exact row is already keyed for its own table (`rowKey` below). The
// drawer's own status lookup is keyed on this same id, so a synthetic id
// means it will not resolve a match against the canonical availability
// authority -- that renders as an honest "no status issue" absence, not a
// fabricated one, the same degrade-honestly rule every other surface here
// already follows for an unmatched identity.
function streamerPlayerId(row: { position: string; playerName: string }): string {
  return `kdst-${row.position}-${row.playerName}`;
}

function buildStreamerColumns(onOpenPlayer: PlayerViewer): TableColumn[] {
  const base: TableColumn[] = [
    { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span> },
    { key: "ecr", label: "FantasyPros ECR", sort: "number", align: "right" },
    { key: "tier", label: "Tier", sort: "number" },
    { key: "rosterStatus", label: "Sleeper status", sort: "text" },
    { key: "recommendation", label: "Action", sort: "text", render: (row) => <StatusBadge tone={String(row.recommendation) === "ADD" || String(row.recommendation) === "START" ? "safe" : "review"} label={String(row.recommendation)} /> },
  ];
  return appendPlayerDetailColumn(base, (row) => onOpenPlayer({
    playerId: streamerPlayerId({ position: String(row.position), playerName: String(row.playerName) }),
    playerName: String(row.playerName),
    position: String(row.position),
    team: String(row.team),
  }));
}

function StreamersTab({
  provider,
  week,
  setWeek,
  horizon,
  setHorizon,
  results,
  error,
  working,
  onLoad,
  onOpenPlayer,
  hasProfile,
}: {
  provider: ExternalConsensusStatus | undefined;
  week: number;
  setWeek: (week: number) => void;
  horizon: StreamerHorizon;
  setHorizon: (horizon: StreamerHorizon) => void;
  results: KdstStreamerResult[];
  error: NwrApiError | null;
  working: boolean;
  onLoad: () => void;
  onOpenPlayer: PlayerViewer;
  hasProfile: boolean;
}) {
  const columns = useMemo(() => buildStreamerColumns(onOpenPlayer), [onOpenPlayer]);
  return <>
    <Panel title="External consensus authority" eyebrow={provider?.authority ?? "EXTERNAL CONSENSUS — FANTASYPROS"}>
      <p>{provider?.message ?? "Provider status is unavailable."}</p>
      <p className="copy-muted">Use a FantasyPros API key authorized for your account in the local Desktop environment, then restart. No API key is shown, stored in a profile, or sent to Sleeper.</p>
      <div className="profile-edit-actions">
        <label className="form-field"><span>NFL week</span><input min={1} max={18} type="number" value={week} onChange={(event) => setWeek(Number(event.target.value))} /></label>
        <SegmentedControl label="Horizon" options={STREAMER_HORIZON_OPTIONS as unknown as string[]} value={horizon} onChange={(value) => setHorizon(value as StreamerHorizon)} />
        <Button disabled={!provider?.configured || working || !hasProfile} icon="activity" onClick={onLoad}>{working ? "Reading…" : `Refresh K/DST ECR (${horizon})`}</Button>
      </div>
    </Panel>
    {!provider?.configured ? <EmptyState title="Provider key required" message="K/DST streaming needs a FantasyPros API key configured in this Desktop install." /> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {provider?.configured && !working && results.length === 0 ? (
      <EmptyState title="No streamer read yet" message="Refresh K/DST ECR above to see this week's start/add/hold guidance." />
    ) : null}
    {results.map((result) => (
      <div key={result.week}>
        <p className="draft-feedback">Week {result.week} · {result.writeBehavior.replaceAll("_", " ")} · provider-scored ECR only; schedule, betting, weather, and hidden weights are not used.</p>
        {(["K", "DST"] as const).map((pos) => {
          const rows = result.positions.filter((row) => row.position === pos);
          const topIndex = rows.findIndex((row) => row.recommendation === "START" || row.recommendation === "ADD");
          const top = topIndex >= 0 ? rows[topIndex] : rows[0] ?? null;
          const alternativeRow = top ? (rows[(topIndex >= 0 ? topIndex : 0) + 1] ?? null) : null;
          const explanation = top ? explainStreamerPlay(top, alternativeRow) : null;
          return (
            <div key={`${result.week}-${pos}`}>
              {explanation && top ? (
                <div className="nwr-action-grid">
                  <DecisionExplain
                    headline={explanation.headline}
                    why={explanation.why}
                    thisWeekImpact={explanation.thisWeekImpact}
                    alternative={explanation.alternative}
                    tone={explanation.tone}
                    actions={<Button variant="ghost" onClick={() => onOpenPlayer({ playerId: streamerPlayerId(top), playerName: top.playerName, position: top.position, team: top.team })}>View {top.playerName}</Button>}
                  />
                </div>
              ) : <EmptyState title="No available recommendation" message={`No ${pos} streamer read for Week ${result.week}.`} />}
              <Panel title={`Week ${result.week} · ${pos} streamer actions`} eyebrow="FantasyPros ECR (provider-scored) · Sleeper availability">
                {rows.length ? <DataTable columns={columns} rows={rows as unknown as Array<Record<string, unknown>>} rowKey={(row) => `${pos}-${String(row.playerName)}-${String(row.ecr)}`} /> : <EmptyState title="No candidates" message={`No ${pos} rows returned for Week ${result.week}.`} />}
              </Panel>
            </div>
          );
        })}
      </div>
    ))}
  </>;
}

// ---------------------------------------------------------------------------
// ALL FREE AGENTS -- the browse/deep-search mode of this same workspace.
// ---------------------------------------------------------------------------

function AllFreeAgentsTab({
  isSleeper,
  result,
  error,
  working,
  query,
  setQuery,
  rows,
  columns,
}: {
  isSleeper: boolean;
  result: { freeAgents: unknown[]; rankingWarning: string } | null;
  error: NwrApiError | null;
  working: boolean;
  query: string;
  setQuery: (value: string) => void;
  rows: Array<Record<string, unknown>>;
  columns: TableColumn[];
}) {
  return <>
    {!isSleeper ? null : (
      <div className="toolbar">
        <SearchInput value={query} onChange={setQuery} placeholder="Search free agents by name or team…" />
      </div>
    )}
    {working ? <p className="draft-feedback">Reading current Sleeper rosters…</p> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result?.rankingWarning ? <div className="alert-strip"><strong>Ranking unavailable</strong><span>{result.rankingWarning}</span></div> : null}
    {result && rows.length === 0 ? (
      <EmptyState
        title={query ? "No matches" : "No free agents"}
        message={query ? "No free agent matches that search." : "Every fantasy-relevant player in this league is currently rostered."}
      />
    ) : null}
    {result && rows.length ? (
      <Panel title={`${rows.length} unrostered player${rows.length === 1 ? "" : "s"}`} eyebrow="AVAILABLE · all fantasy positions">
        <DataTable columns={columns} rows={rows} rowKey={(row) => String(row.sleeperPlayerId)} />
      </Panel>
    ) : null}
  </>;
}
