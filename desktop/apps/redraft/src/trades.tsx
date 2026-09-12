import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { RedraftBootstrap, TradeAnalysisResult, TradePlayerImpact } from "@nwr/contracts";
import {
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  MetricCard,
  PageHeader,
  Panel,
  StatusBadge,
  type TableColumn,
  formatNumber,
} from "@nwr/ui";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { DecisionExplain } from "./decision-explain";
import { TradeSidePicker, type TradeSide } from "./in-season";
import { leagueFormat } from "./league-context";
import { usePlayerDetailOpener } from "./player-detail-context";
import { playerAvailabilityBadgeLabel, playerAvailabilityBadgeTone } from "./player-detail-state";
import { explainTradeAnalysis, explainTradeFinderCandidate } from "./trades-explain";
import { useAsync } from "./weekly-shared";

/**
 * NWR UI expansion pass (2026-09-12, Trades surface): ONE coherent owner
 * workspace answering "Should I make this trade?" / "Is there a trade I
 * should pursue?", unifying the previously separately-built Trade
 * Analysis / Trade Finder pages under two tabs (ANALYZE / FIND TRADES) --
 * same consolidation shape as Improve Team's own pass. Presentation-layer
 * only, over the exact same frozen contracts those pages already read
 * (`redraftTradeAnalysis` / `redraftTradeFinder`, unchanged) -- no new
 * trade math. See `trades-explain.ts` for the pure grammar derivation and
 * `TradeAnalysisPage`/`TradeFinderPage` (in-season.tsx, left in place as a
 * harmless, unrouted legacy fallback) for the pages this consolidates.
 */

type TradesTab = "analyze" | "find";

const TRADES_TABS: Array<{ key: TradesTab; label: string }> = [
  { key: "analyze", label: "Analyze" },
  { key: "find", label: "Find Trades" },
];

type PlayerViewer = (player: { playerId: string; playerName: string; position?: string; team?: string }) => void;

export function TradesPage({ client, data, defaultTab }: { client: NwrApiClient; data: RedraftBootstrap; defaultTab?: TradesTab }) {
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get("tab");
  const tab: TradesTab = TRADES_TABS.some((item) => item.key === tabParam) ? (tabParam as TradesTab) : (defaultTab ?? "analyze");
  const setTab = useCallback(
    (next: TradesTab) => {
      const nextParams = new URLSearchParams(searchParams);
      nextParams.set("tab", next);
      setSearchParams(nextParams, { replace: true });
    },
    [searchParams, setSearchParams],
  );

  const [gives, setGives] = useState<TradeSide[]>([]);
  const [receives, setReceives] = useState<TradeSide[]>([]);
  const [result, setResult] = useState<TradeAnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<NwrApiError | null>(null);
  const [working, setWorking] = useState(false);

  const myRosterLoader = useCallback(() => (isSleeper ? client.redraftMyRoster() : null), [client, isSleeper]);
  const { result: myRoster } = useAsync(myRosterLoader, [isSleeper, data.activeProfileId]);
  const opponentsLoader = useCallback(() => (isSleeper ? client.redraftOpponentRosters() : null), [client, isSleeper]);
  const { result: opponents } = useAsync(opponentsLoader, [isSleeper, data.activeProfileId]);

  // NWR pre-UI architecture CLOSURE pass (directive sections 1-2): the
  // same global Player Detail primitive every other surface uses, reused
  // here -- never a second drawer for Trades.
  const openPlayerDetail = usePlayerDetailOpener(data.activeProfileId, "TRADES");

  const giveCandidates: TradeSide[] = useMemo(
    () => (myRoster?.roster ?? []).map((player) => ({ sleeperPlayerId: player.sleeperPlayerId, name: `${player.playerName} (${player.position})` })),
    [myRoster],
  );
  const receiveCandidates: TradeSide[] = useMemo(
    () => (opponents?.opponents ?? []).flatMap((opponent) => opponent.players.map((player) => ({ sleeperPlayerId: player.sleeperPlayerId, name: `${player.playerName} (${player.position}) — ${opponent.teamName}` }))),
    [opponents],
  );

  // Query-param prefill (unchanged mechanism from the pre-existing Trade
  // Analysis page): My Roster's "Add to Trade Analysis" and Opponent
  // Rosters' "Add to trade" links still point at `/trade-analysis?...`,
  // now resolving here -- kept so those existing links continue to work
  // unchanged against this new workspace.
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

  const analyze = useCallback(async () => {
    if (!gives.length || !receives.length) return;
    setWorking(true);
    setAnalysisError(null);
    setResult(null);
    try {
      setResult(await client.redraftTradeAnalysis(gives.map((p) => p.sleeperPlayerId), receives.map((p) => p.sleeperPlayerId)));
    } catch (reason) {
      setAnalysisError(reason instanceof NwrApiError ? reason : new NwrApiError("Trade analysis could not be read."));
    } finally {
      setWorking(false);
    }
  }, [client, gives, receives]);

  // Find Trades' own "Open in Analyze" cross-tab jump (same shape as
  // Improve Team's Targets -> Add/Drop link): pre-selects both sides of a
  // real candidate package and switches tabs, but does not auto-fetch --
  // the owner still takes the deliberate "Analyze trade" action, same as
  // every other prefill path here.
  const openInAnalyze = useCallback(
    (give: TradeSide, receive: TradeSide) => {
      setGives([give]);
      setReceives([receive]);
      setResult(null);
      setAnalysisError(null);
      setTab("analyze");
    },
    [setTab],
  );

  return <>
    <PageHeader
      eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"}
      title="Trades"
      description="Should I make this trade? Is there a trade I should pursue? Real, structured before/after impact -- never a single opaque trade score. NWR never proposes or accepts a trade on Sleeper."
      status={isSleeper ? undefined : <StatusBadge tone="blocked" label="Sleeper profile required" />}
    />
    {!isSleeper ? <EmptyState title="Sleeper league required" message="Trades needs your live Sleeper roster and every live opponent roster." /> : null}
    {isSleeper ? <>
      <nav aria-label="Trades sections" className="nwr-tabbar" role="tablist">
        {TRADES_TABS.map((item) => (
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

      {tab === "analyze" ? (
        <AnalyzeTab
          error={analysisError}
          giveCandidates={giveCandidates}
          gives={gives}
          onAnalyze={() => void analyze()}
          onOpenPlayer={openPlayerDetail}
          receiveCandidates={receiveCandidates}
          receives={receives}
          result={result}
          setGives={setGives}
          setReceives={setReceives}
          working={working}
        />
      ) : null}

      {tab === "find" ? (
        <FindTradesTab client={client} data={data} onOpenAnalyze={openInAnalyze} onOpenPlayer={openPlayerDetail} />
      ) : null}
    </> : null}
  </>;
}

// ---------------------------------------------------------------------------
// ANALYZE -- I give / I receive pickers, an overall DecisionExplain
// verdict card (before/after framing), then the per-player and
// per-position detail underneath.
// ---------------------------------------------------------------------------

function AnalyzeTab({
  gives,
  setGives,
  receives,
  setReceives,
  giveCandidates,
  receiveCandidates,
  result,
  error,
  working,
  onAnalyze,
  onOpenPlayer,
}: {
  gives: TradeSide[];
  setGives: (updater: (current: TradeSide[]) => TradeSide[]) => void;
  receives: TradeSide[];
  setReceives: (updater: (current: TradeSide[]) => TradeSide[]) => void;
  giveCandidates: TradeSide[];
  receiveCandidates: TradeSide[];
  result: TradeAnalysisResult | null;
  error: NwrApiError | null;
  working: boolean;
  onAnalyze: () => void;
  onOpenPlayer: PlayerViewer;
}) {
  const impactColumns: TableColumn[] = useMemo(
    () => [
      { key: "playerName", label: "Player", sort: "text" },
      { key: "position", label: "Pos", sort: "text" },
      { key: "rosReplacementValue", label: "ROS replacement value", sort: "number", align: "right", render: (row) => row.rosReplacementValue == null ? "—" : formatNumber(Number(row.rosReplacementValue), 1) },
      { key: "marginalUtility", label: "Marginal utility", sort: "number", align: "right", render: (row) => row.marginalUtility == null ? "—" : formatNumber(Number(row.marginalUtility), 1) },
      { key: "becomesStarter", label: "Becomes starter", sort: "text", render: (row) => row.becomesStarter ? <StatusBadge tone="safe" label="Yes" /> : "No" },
      { key: "statusFlag", label: "Status/risk", sort: "text", render: (row) => row.statusFlag ? <StatusBadge tone="review" label={String(row.statusFlag)} /> : "—" },
      {
        // NWR pre-UI architecture CLOSURE pass (directive section 2): the
        // canonical PlayerAvailabilityStatus authority, already attached
        // to this row by the facade -- rendered here, never a second
        // status heuristic.
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
          <Button variant="ghost" onClick={() => onOpenPlayer({ playerId: String(row.playerId), playerName: String(row.playerName), position: String(row.position) })}>View</Button>
        ),
      },
    ],
    [onOpenPlayer],
  );

  const explanation = result ? explainTradeAnalysis(result, result.gives.map((p) => p.playerName), result.receives.map((p) => p.playerName)) : null;

  return <>
    <Panel title="Build a trade">
      <div className="split-view">
        <TradeSidePicker label="I give" side={gives} candidates={giveCandidates} onAdd={(candidate) => setGives((current) => [...current, candidate])} onRemove={(id) => setGives((current) => current.filter((p) => p.sleeperPlayerId !== id))} />
        <TradeSidePicker label="I receive" side={receives} candidates={receiveCandidates} onAdd={(candidate) => setReceives((current) => [...current, candidate])} onRemove={(id) => setReceives((current) => current.filter((p) => p.sleeperPlayerId !== id))} />
      </div>
      <div className="profile-edit-actions">
        <Button icon="activity" disabled={!gives.length || !receives.length || working} onClick={onAnalyze}>{working ? "Analyzing…" : "Analyze trade"}</Button>
        <Link to="/my-roster">Browse my roster</Link>
        <Link to="/opponent-rosters">Browse opponent rosters</Link>
      </div>
    </Panel>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result && explanation ? <>
      <div className="nwr-action-grid">
        <DecisionExplain
          eyebrow={explanation.eyebrow}
          headline={explanation.headline.toUpperCase()}
          why={explanation.why}
          thisWeekImpact={explanation.weeklyImpact}
          rosImpact={explanation.rosImpact}
          depth={explanation.depth}
          positionEffect={explanation.positionEffect}
          risk={explanation.risk}
          tone={explanation.tone}
        />
      </div>
      <div className="metric-grid">
        <MetricCard label="Bench contingency value" value={`${formatNumber(result.benchContingencyValueBefore, 1)} → ${formatNumber(result.benchContingencyValueAfter, 1)}`} detail="Depth remaining if a starter goes down" icon="layers" tone="violet" />
        <MetricCard label="Starter holes" value={`${result.starterHolesBefore.length} → ${result.starterHolesAfter.length}`} detail={result.starterHolesAfter.join(", ") || "None after trade"} icon="alert" tone="crimson" />
        <MetricCard label="Championship equity" value={result.championshipEquityNote ? "Noted" : "Not evaluated"} detail={result.championshipEquityNote ?? "Only shown where genuinely supported"} icon="target" tone="gold" />
      </div>
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
    {!result && !error && !working ? (
      <EmptyState title="No trade analyzed yet" message="Pick at least one player on each side above, then Analyze trade to see NWR's real before/after verdict." />
    ) : null}
  </>;
}

// ---------------------------------------------------------------------------
// FIND TRADES -- real win-win candidates, one DecisionExplain card per
// candidate (opponent / you-send / you-receive / why-this-fits /
// NWR-roster-impact). Never fabricates an acceptance probability -- the
// backend supplies none.
// ---------------------------------------------------------------------------

function FindTradesTab({
  client,
  data,
  onOpenPlayer,
  onOpenAnalyze,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onOpenPlayer: PlayerViewer;
  onOpenAnalyze: (give: TradeSide, receive: TradeSide) => void;
}) {
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const loader = useCallback(() => (isSleeper ? client.redraftTradeFinder() : null), [client, isSleeper]);
  const { result, error, working, reload } = useAsync(loader, [isSleeper, data.activeProfileId]);

  return <>
    <div className="toolbar">
      <Button disabled={working} icon="activity" onClick={reload} variant="secondary">{working ? "Searching…" : "Refresh"}</Button>
    </div>
    {result ? <p className="copy-muted">{result.candidates.length} candidate{result.candidates.length === 1 ? "" : "s"} found across every live opponent roster.</p> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {working && !result ? <p className="draft-feedback">Searching every live opponent roster for a real win-win…</p> : null}
    {result && result.candidates.length === 0 ? (
      <EmptyState title="No win-win candidates found" message="NWR's evaluator did not find any 1-for-1 package where both sides' real marginal utility improves right now." />
    ) : null}
    {result && result.candidates.length ? (
      <div className="nwr-action-grid">
        {result.candidates.map((candidate, index) => {
          const explanation = explainTradeFinderCandidate(candidate);
          return (
            <DecisionExplain
              actions={<>
                <span className="copy-muted">You send:</span>
                <StatusBadge tone={playerAvailabilityBadgeTone(candidate.myGivePlayerAvailabilityStatus)} label={playerAvailabilityBadgeLabel(candidate.myGivePlayerAvailabilityStatus)} />
                <Button onClick={() => onOpenPlayer({ playerId: candidate.myGivePlayerId, playerName: candidate.myGivePlayerName })} variant="ghost">View {candidate.myGivePlayerName}</Button>
                <span className="copy-muted">You receive:</span>
                <StatusBadge tone={playerAvailabilityBadgeTone(candidate.opponentGivePlayerAvailabilityStatus)} label={playerAvailabilityBadgeLabel(candidate.opponentGivePlayerAvailabilityStatus)} />
                <Button onClick={() => onOpenPlayer({ playerId: candidate.opponentGivePlayerId, playerName: candidate.opponentGivePlayerName })} variant="ghost">View {candidate.opponentGivePlayerName}</Button>
                <Button onClick={() => onOpenAnalyze(
                  { sleeperPlayerId: candidate.myGivePlayerId, name: candidate.myGivePlayerName },
                  { sleeperPlayerId: candidate.opponentGivePlayerId, name: candidate.opponentGivePlayerName },
                )} variant="secondary">Open in Analyze</Button>
              </>}
              eyebrow={`vs. ${candidate.opponentTeamName}`}
              headline={explanation.headline}
              impact={explanation.impact}
              key={`${candidate.opponentRosterId}-${candidate.myGivePlayerId}-${index}`}
              tone={explanation.tone}
              why={explanation.why}
            />
          );
        })}
      </div>
    ) : null}
  </>;
}
