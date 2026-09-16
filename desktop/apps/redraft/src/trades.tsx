import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { RedraftBootstrap, TradeAnalysisResult, TradePackageCandidate, TradePackageSearchMode, TradePlayerImpact } from "@nwr/contracts";
import {
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  MetricCard,
  PageHeader,
  Panel,
  SegmentedControl,
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
import { describeTradePackageSearchError, explainTradeAnalysis, explainTradePackageCandidate, isTradePackageSearchStale } from "./trades-explain";
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
        <FindTradesTab client={client} data={data} onOpenPlayer={openPlayerDetail} targetCandidates={receiveCandidates} />
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
// FIND TRADES -- Trade Package Search (P1-3, Worker 6's backend), three
// modes (FIND WIN-WIN PACKAGES / TARGET PLAYER / IMPROVE POSITION), each a
// real, bounded, multi-player (1-for-1 through 2-for-2) candidate search
// across every live opponent roster -- a real superset of the prior
// 1-for-1-only Trade Finder this tab used to call directly (`TradeFinderResult`/
// `explainTradeFinderCandidate` are unchanged and still power Weekly Home's
// own "TRADE" action cards via a different endpoint -- see
// `home-action-explain.ts` -- only THIS tab's data source changed). One
// DecisionExplain card per candidate: YOU SEND / YOU RECEIVE / WHY IT HELPS
// YOU / WHY IT MAY FIT THEM / WEEKLY IMPACT / ROS IMPACT. Never fabricates
// an acceptance probability -- the backend supplies none, in any mode.
//
// Deliberately NO "Open in Analyze" cross-tab jump on these cards (the old
// 1-for-1 Trade Finder flow had one): a real, pre-existing, NOT-fixed-here
// bug was found while wiring this -- `youSend`/`youReceive` (and the old
// `TradeFinderCandidate.myGivePlayerId`/`opponentGivePlayerId` before it)
// are NWR's own canonical (GSIS-style, e.g. "00-0023459") player ids, not
// raw Sleeper ids, but `redraftTradeAnalysis` requires raw Sleeper ids
// (resolved against the Sleeper `players/nfl` catalog in
// `redraft_trade_analysis_service`) -- reproduced live (see the ledger).
// The owner's own "You send" side COULD be resolved via
// `RedraftMyRosterPlayer.canonicalPlayerId`, but the opponent's "You
// receive" side has no such field on `RedraftOpponentPlayer` today, so a
// correct fix needs a small backend contract addition, not a UI-only
// patch -- flagged for the next worker rather than shipped half-working
// or silently left broken.
// ---------------------------------------------------------------------------

const PACKAGE_SEARCH_MODES: Array<{ key: TradePackageSearchMode; label: string }> = [
  { key: "FIND_WIN_WIN", label: "Find win-win packages" },
  { key: "TARGET_PLAYER", label: "Target a player" },
  { key: "IMPROVE_POSITION", label: "Improve a position" },
];

const IMPROVE_POSITION_OPTIONS = ["QB", "RB", "WR", "TE", "K", "DST"];

function FindTradesTab({
  client,
  data,
  onOpenPlayer,
  targetCandidates,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onOpenPlayer: PlayerViewer;
  targetCandidates: TradeSide[];
}) {
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const [mode, setMode] = useState<TradePackageSearchMode>("FIND_WIN_WIN");
  const [targetPlayer, setTargetPlayer] = useState<TradeSide | null>(null);
  const [position, setPosition] = useState("RB");

  const loader = useCallback(() => {
    if (!isSleeper) return null;
    if (mode === "TARGET_PLAYER" && !targetPlayer) return null;
    return client.redraftTradePackageSearch({
      mode,
      ...(mode === "TARGET_PLAYER" && targetPlayer ? { targetPlayerSleeperId: targetPlayer.sleeperPlayerId } : {}),
      ...(mode === "IMPROVE_POSITION" ? { position } : {}),
    });
  }, [client, isSleeper, mode, targetPlayer, position]);
  const { result, error, working, reload } = useAsync(loader, [isSleeper, mode, targetPlayer?.sleeperPlayerId, position, data.activeProfileId]);

  const softenedError = error ? describeTradePackageSearchError(error) : null;
  // Find-trades mode-display race fix (shared upgrade B, 2026-09-16): a
  // structural check against the resolved response's own `mode` field --
  // see `isTradePackageSearchStale` in trades-explain.ts. True exactly
  // when the candidate cards below are still the PREVIOUS mode's search
  // results while a newer mode's fetch is in flight.
  const stale = isTradePackageSearchStale(result, mode);

  return <>
    <SegmentedControl label="Search mode" options={PACKAGE_SEARCH_MODES.map((item) => item.key)} value={mode} onChange={(value) => setMode(value as TradePackageSearchMode)} />
    <p className="copy-muted">{PACKAGE_SEARCH_MODES.find((item) => item.key === mode)?.label}</p>

    {mode === "TARGET_PLAYER" ? (
      <Panel title="Who do you want to target?">
        <TradeSidePicker
          label="Target player"
          side={targetPlayer ? [targetPlayer] : []}
          candidates={targetCandidates}
          onAdd={(candidate) => setTargetPlayer(candidate)}
          onRemove={() => setTargetPlayer(null)}
        />
      </Panel>
    ) : null}

    {mode === "IMPROVE_POSITION" ? (
      <SegmentedControl label="Position" options={IMPROVE_POSITION_OPTIONS} value={position} onChange={setPosition} />
    ) : null}

    <div className="toolbar">
      <Button disabled={working || (mode === "TARGET_PLAYER" && !targetPlayer)} icon="activity" onClick={reload} variant="secondary">{working ? "Searching…" : "Refresh"}</Button>
    </div>

    {mode === "TARGET_PLAYER" && !targetPlayer ? (
      <EmptyState title="Pick a player to target" message="Search the opponent roster above and pick a real player -- NWR will search every legal package (1-for-1 through 2-for-2) that could land them." />
    ) : null}

    {softenedError ? <ErrorState message={softenedError.message} recovery={softenedError.recovery} /> : null}
    {working && !result ? <p className="draft-feedback">Searching every live opponent roster for a real package…</p> : null}
    {stale ? (
      <div className="alert-strip alert-strip--pending" role="status">
        <strong>Updating…</strong>
        <span>Searching "{PACKAGE_SEARCH_MODES.find((item) => item.key === mode)?.label}" -- the candidates below are still from the previous search mode.</span>
      </div>
    ) : null}

    {result && !error ? (
      <p className="copy-muted">
        {result.candidates.length} candidate{result.candidates.length === 1 ? "" : "s"} found across {result.opponentsSearched} opponent roster{result.opponentsSearched === 1 ? "" : "s"} ({result.packagesEvaluated} package{result.packagesEvaluated === 1 ? "" : "s"} evaluated).{" "}
        {result.truncated ? (
          <StatusBadge tone="review" label="Search capped -- more legal packages may exist beyond this bound" />
        ) : null}
      </p>
    ) : null}

    {result && result.candidates.length === 0 && !error ? (
      <EmptyState
        title="No candidates found"
        message={
          mode === "FIND_WIN_WIN"
            ? "NWR's evaluator did not find any legal package (1-for-1 through 2-for-2) across any opponent roster where both sides' real marginal utility improves right now."
            : mode === "TARGET_PLAYER"
              ? `NWR could not build a legal package for ${targetPlayer?.name ?? "that player"} where the trade partner's own real utility stays non-negative.`
              : `NWR could not build a legal package that improves your ${position} spot without hurting the other team's roster, within the current search bounds.`
        }
      />
    ) : null}

    {result && !error && result.candidates.length ? (
      <div className="nwr-action-grid">
        {result.candidates.map((candidate, index) => (
          <TradePackageCandidateCard
            candidate={candidate}
            key={`${candidate.opponentRosterId}-${candidate.packageShape}-${candidate.youSend.join(",")}-${candidate.youReceive.join(",")}-${index}`}
            onOpenPlayer={onOpenPlayer}
          />
        ))}
      </div>
    ) : null}
  </>;
}

function TradePackageCandidateCard({
  candidate,
  onOpenPlayer,
}: {
  candidate: TradePackageCandidate;
  onOpenPlayer: PlayerViewer;
}) {
  const explanation = explainTradePackageCandidate(candidate);
  return (
    <DecisionExplain
      actions={<>
        <span className="copy-muted">You send:</span>
        {candidate.ownerEvaluation.gives.map((player) => (
          <span key={player.playerId}>
            <StatusBadge tone={playerAvailabilityBadgeTone(player.playerAvailabilityStatus)} label={playerAvailabilityBadgeLabel(player.playerAvailabilityStatus)} />
            <Button onClick={() => onOpenPlayer({ playerId: player.playerId, playerName: player.playerName, position: player.position })} variant="ghost">View {player.playerName}</Button>
          </span>
        ))}
        <span className="copy-muted">You receive:</span>
        {candidate.ownerEvaluation.receives.map((player) => (
          <span key={player.playerId}>
            <StatusBadge tone={playerAvailabilityBadgeTone(player.playerAvailabilityStatus)} label={playerAvailabilityBadgeLabel(player.playerAvailabilityStatus)} />
            <Button onClick={() => onOpenPlayer({ playerId: player.playerId, playerName: player.playerName, position: player.position })} variant="ghost">View {player.playerName}</Button>
          </span>
        ))}
      </>}
      depth={explanation.depth}
      eyebrow={`vs. ${candidate.opponentTeamName} · ${candidate.packageShape}`}
      headline={explanation.headline}
      positionEffect={explanation.positionEffect}
      risk={explanation.risk}
      rosImpact={explanation.rosImpact}
      secondaryWhy={explanation.secondaryWhy}
      thisWeekImpact={explanation.thisWeekImpact}
      tone={explanation.tone}
      why={explanation.why}
    />
  );
}
