import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { KdstStreamerResult, RedraftBootstrap, RedraftExternalIntelligence, RedraftExternalIntelligenceEntry, RedraftOpponentRostersResult, RedraftRanking } from "@nwr/contracts";
import {
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  Icon,
  MetricCard,
  PageHeader,
  Panel,
  ProgressBar,
  SearchInput,
  SegmentedControl,
  SelectField,
  StatusBadge,
  type TableColumn,
  formatNumber,
  normalizeCommandSearch,
} from "@nwr/ui";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { draftFormat, leagueFormat } from "./league-context";
import { FREE_AGENT_COLUMNS, useAsync, useFreeAgents } from "./weekly-shared";

const POSITION_OPTIONS = ["ALL", "QB", "RB", "WR", "TE", "K", "DST"];
const DRAFT_ROOM_POSITION_OPTIONS = ["ALL", "FLEX", "QB", "RB", "WR", "TE", "K", "DST"];
const DRAFT_DEPTH_OPTIONS = [
  { value: "15", label: "15 players" },
  { value: "25", label: "25 players" },
  { value: "50", label: "50 players" },
  { value: "100", label: "100 players" },
  { value: "all", label: "All matches" },
];
const BOARD_DEPTH_OPTIONS = [
  { value: "50", label: "Top 50" },
  { value: "100", label: "Top 100" },
  { value: "250", label: "Top 250" },
  { value: "all", label: "All players" },
];
export const DRAFT_ROOM_ACCEPTANCE_LABELS = [
  "Draft board",
  "My Roster",
  "Available player panel",
  "Recent picks",
  "Full draft log",
  "Beat ADP pool",
  "Draft recommendations",
  "Advance to my pick",
  "Refresh FFC ADP",
  "Paste Rankings / ADP",
  "ADP unavailable",
] as const;

function draftedIds(data: RedraftBootstrap): string[] {
  return data.draftBoard?.drafted ?? [];
}

function rankingRows(data: RedraftBootstrap): Array<Record<string, unknown>> {
  const drafted = new Set(draftedIds(data));
  return data.rankings.map((row) => ({ ...row, drafted: drafted.has(row.playerId) || row.drafted }));
}

function withDepth<T>(rows: T[], depth: string): T[] {
  return depth === "all" ? rows : rows.slice(0, Number(depth));
}

export function rankingSearchRows<T>(rows: T[], depth: string, query: string): T[] {
  return query.trim() ? rows : withDepth(rows, depth);
}

export type PickSearchAsset = { playerId: string; playerName: string; team: string; position: string; drafted?: boolean; overallRank?: number; rosterLegal?: boolean; legalityCode?: string; legalityReason?: string };
export type PickSearchCandidate = PickSearchAsset & { source: "NWR" | "MANUAL" };

/**
 * Global pick-recording search: matches every draftable asset (ranked
 * skill-position players AND manual K/DST assets) by name, ignoring the
 * Player Panel's position filter entirely. A real opponent pick must always
 * be findable here regardless of what position the owner is currently
 * browsing -- see sample_data/kha_real_draft_2026/RECONCILIATION_LEDGER.md
 * (23/157 real KHA draft picks were misrecorded because the correct player
 * existed in NWR but wasn't the one selected under clock pressure; 14/157
 * more were K/DST picks that required first switching the position filter
 * to K or DST to even see manual assets).
 */
/**
 * Pure keyboard-navigation step for the rapid-capture suggestion list:
 * ArrowDown/Tab move forward, ArrowUp/Shift+Tab move backward, both
 * wrapping around a `resultCount`-length list. Returns null for any key
 * this box doesn't consume (Tab with no results, so focus moves on
 * normally instead of being trapped).
 */
export function nextRapidCaptureIndex(
  key: string,
  shiftKey: boolean,
  currentIndex: number,
  resultCount: number,
): number | null {
  if (!resultCount) return null;
  if (key === "ArrowDown" || (key === "Tab" && !shiftKey)) {
    return (currentIndex + 1) % resultCount;
  }
  if (key === "ArrowUp" || (key === "Tab" && shiftKey)) {
    return (currentIndex - 1 + resultCount) % resultCount;
  }
  return null;
}

export function globalPickSearchRows(
  rankedRows: PickSearchAsset[],
  manualRows: PickSearchAsset[],
  draftedIds: string[],
  query: string,
  limit = 20,
): PickSearchCandidate[] {
  // normalizeCommandSearch (the same helper the Ctrl+K command palette
  // already uses) strips diacritics and punctuation before matching --
  // real gap this closes: "Pineiro" (what an operator actually types)
  // must find "Piñeiro", and "AJ" must find "A.J." without a bespoke
  // alias table for every such case.
  const trimmed = normalizeCommandSearch(query.trim());
  if (!trimmed) return [];
  const drafted = new Set(draftedIds);
  // Owner-test follow-up: matches player name, team, AND position (e.g.
  // "SF" or "QB" alone) -- a real, narrow gap this closes; manual rows
  // already matched name+team, ranked rows previously matched name only.
  const fromRanked: PickSearchCandidate[] = rankedRows
    .filter((row) => !drafted.has(row.playerId) && !row.drafted && normalizeCommandSearch(`${row.playerName} ${row.team} ${row.position}`).includes(trimmed))
    .map((row) => ({ ...row, source: "NWR" }));
  const fromManual: PickSearchCandidate[] = manualRows
    .filter((row) => !drafted.has(row.playerId) && normalizeCommandSearch(`${row.playerName} ${row.team}`).includes(trimmed))
    .map((row) => ({ ...row, source: "MANUAL" }));
  return [...fromRanked, ...fromManual].slice(0, limit);
}

function rankingColumns(compact = false): TableColumn[] {
  const base: TableColumn[] = [
    { key: "overallRank", label: "Rank", sort: "number", width: "60px", render: (row) => <span className="rank-cell"><i /><b>#{String(row.overallRank)}</b></span> },
    { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}{String(row.positionRank)}</small></span> },
    { key: "position", label: "Pos", sort: "text", align: "center", render: (row) => <span className="position-pill">{String(row.position)}</span> },
    { key: "tier", label: "Tiers", sort: "number", render: (row) => <span className="player-cell"><strong>{String(row.overallTierLabel ?? `Tier ${String(row.tier)}`)}</strong><small>{String(row.positionTierLabel ?? "")}</small></span> },
    { key: "projectedPoints", label: "Proj pts", sort: "number", align: "right", render: (row) => formatNumber(row.projectedPoints as number, 1) },
    { key: "replacementAdjustedValue", label: "Value over replacement", sort: "number", align: "right", render: (row) => <span className="vor-cell"><strong>{formatNumber(row.replacementAdjustedValue as number, 1)}</strong><ProgressBar value={Number(row.replacementAdjustedValue ?? 0)} max={250} tone="gold" /></span> },
    {
      key: "confidence",
      label: "Projection evidence",
      sort: "text",
      render: (row) => (
        <span title="Projection evidence strength; separate from board readiness.">
          {`${String(row.confidence).charAt(0).toUpperCase()}${String(row.confidence).slice(1).toLowerCase()} evidence`}
        </span>
      ),
    },
  ];
  return compact ? base.slice(0, 6) : [...base, { key: "sourceAsOf", label: "Source as of", sort: "text" }];
}

export function RankingsPage({ data }: { data: RedraftBootstrap }) {
  const [searchParams] = useSearchParams();
  const requestedPlayer = searchParams.get("player");
  const requestedName = data.rankings.find((row) => row.playerId === requestedPlayer)?.playerName ?? "";
  const [query, setQuery] = useState(requestedName);
  const [position, setPosition] = useState("ALL");
  const [team, setTeam] = useState("ALL");
  const [availability, setAvailability] = useState("Available");
  const [depth, setDepth] = useState("100");
  const [tableResetKey, setTableResetKey] = useState(0);
  useEffect(() => { if (requestedName) setQuery(requestedName); }, [requestedName]);
  const teams = ["ALL", ...new Set(data.rankings.map((row) => row.team).filter(Boolean))].sort();
  const filteredRows = useMemo(() => rankingRows(data).filter((row) => (position === "ALL" || row.position === position) && (team === "ALL" || row.team === team) && (availability === "All" || (availability === "Drafted") === Boolean(row.drafted)) && (!query || `${String(row.playerName)} ${String(row.team)}`.toLowerCase().includes(query.toLowerCase()))), [availability, data, position, query, team]);
  const rows = useMemo(
    () => rankingSearchRows(filteredRows, depth, query),
    [depth, filteredRows, query],
  );
  const reset = () => {
    setQuery("");
    setPosition("ALL");
    setTeam("ALL");
    setAvailability("Available");
    setDepth("100");
    setTableResetKey((value) => value + 1);
  };
  const practical = Boolean(data.activeProfile?.practicalMode);
  const activeName = data.activeProfile?.leagueName ?? "Active League";
  const activeFormat = data.activeProfile ? leagueFormat(data.activeProfile, false) : "Choose a league profile";
  return <><PageHeader eyebrow={activeFormat} title={`${activeName} Rankings`} description={practical ? "Major QB/RB/WR/TE scoring rules are modeled. Five uncommon events are omitted; K/DST are separate manual assets." : "Current-season projection value, dynamic replacement level, confidence, and tiers for this active league."} status={<><StatusBadge tone={data.rankings.length ? "safe" : "blocked"} label={`${data.rankings.length} ranked players`} />{practical ? <StatusBadge tone="review" label="Approximate scoring" /> : <StatusBadge tone="safe" label="League specific" />}</>} /><Panel title="Current-season board" eyebrow={`Showing ${rows.length} of ${filteredRows.length} matches`}><div className="toolbar"><SearchInput value={query} onChange={setQuery} /><SegmentedControl label="Position" options={POSITION_OPTIONS} value={position} onChange={setPosition} /><SelectField label="Team" value={team} onChange={setTeam} options={teams.map((value) => ({ value, label: value === "ALL" ? "All teams" : value }))} /><SelectField label="Availability" value={availability} onChange={setAvailability} options={["Available", "Drafted", "All"].map((value) => ({ value, label: value }))} /><SelectField label="Board depth" value={depth} onChange={setDepth} options={BOARD_DEPTH_OPTIONS} /><Button icon="undo" onClick={reset} variant="ghost">Reset</Button></div><DataTable columns={rankingColumns()} resetKey={tableResetKey} rows={rows} rowKey={(row) => String(row.playerId)} /></Panel></>;
}

export function TiersPage({ data }: { data: RedraftBootstrap }) {
  const [position, setPosition] = useState("ALL");
  const [depth, setDepth] = useState("100");
  const filteredRows = useMemo(() => data.rankings.filter((row) => position === "ALL" || row.position === position), [data.rankings, position]);
  const visibleRows = useMemo(() => withDepth(filteredRows, depth), [depth, filteredRows]);
  const tierFor = (row: RedraftRanking) => position === "ALL" ? row.tier : row.positionTier;
  const tiers = Array.from(new Set(visibleRows.map(tierFor))).sort((a, b) => a - b);
  return <><PageHeader eyebrow="Draft board · Value cliffs" title="Tiers & Position Rooms" description="Evidence-gap overall tiers and position-specific rooms stay separate, stable, and bounded for draft-day scanning." status={<><StatusBadge tone={data.rankings.length ? "safe" : "blocked"} label={data.activeProfile?.leagueName ?? "No active profile"} /><StatusBadge tone="safe" label={`${visibleRows.length} of ${filteredRows.length} shown`} /></>} /><div className="toolbar"><SegmentedControl label="Position room" options={POSITION_OPTIONS} value={position} onChange={setPosition} /><SelectField label="Board depth" value={depth} onChange={setDepth} options={BOARD_DEPTH_OPTIONS} /></div><div className="tier-stack">{tiers.map((tier) => { const players = visibleRows.filter((row) => tierFor(row) === tier); const title = position === "ALL" ? players[0]?.overallTierLabel : players[0]?.positionTierLabel; return <Panel key={tier} title={title ?? `Tier ${tier}`} eyebrow={`${players.length} shown`}><div className="tier-player-grid">{players.map((row) => <article key={row.playerId}><span>{row.overallRank}</span><div><strong>{row.playerName}</strong><small>{row.team} · {row.position}{row.positionRank} · {row.positionTierLabel}</small></div><b>{formatNumber(row.replacementAdjustedValue, 1)}</b></article>)}</div></Panel>; })}</div></>;
}

const COMPARE_MODES = ["Rest of Season", "This Week", "Roster Fit", "Trade"] as const;
type CompareMode = (typeof COMPARE_MODES)[number];

export function ComparePage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const [left, setLeft] = useState(data.rankings[0]?.playerId ?? "");
  const [right, setRight] = useState(data.rankings[1]?.playerId ?? "");
  const [mode, setMode] = useState<CompareMode>("Rest of Season");
  const [week, setWeek] = useState(1);
  useEffect(() => {
    setLeft(data.rankings[0]?.playerId ?? "");
    setRight(data.rankings[1]?.playerId ?? "");
  }, [data.activeProfileId, data.rankings]);
  const a = data.rankings.find((row) => row.playerId === left);
  const b = data.rankings.find((row) => row.playerId === right);
  const options = data.rankings.map((row) => ({ value: row.playerId, label: `#${row.overallRank} ${row.playerName} · ${row.position}${row.positionRank}` }));
  const isSleeper = data.activeProfile?.provider === "sleeper";

  const weeklyLoader = useCallback(
    () => (isSleeper && mode === "This Week" ? client.redraftWeeklyProjections(week) : null),
    [client, isSleeper, mode, week],
  );
  const { result: weekly, error: weeklyError } = useAsync(weeklyLoader, [isSleeper, mode, week]);

  const waiversLoader = useCallback(
    () => (isSleeper && mode === "Roster Fit" ? client.redraftWaivers({ mode: "REST_OF_SEASON" }) : null),
    [client, isSleeper, mode],
  );
  const { result: waivers, error: waiversError } = useAsync(waiversLoader, [isSleeper, mode]);
  const myRosterLoader = useCallback(
    () => (isSleeper && mode === "Roster Fit" ? client.redraftMyRoster() : null),
    [client, isSleeper, mode],
  );
  const { result: myRoster } = useAsync(myRosterLoader, [isSleeper, mode]);

  const weeklyRowFor = (playerId: string) => weekly?.rows.find((row) => row.canonicalPlayerId === playerId) ?? null;
  const rosterFitFor = (playerId: string) => {
    const onRoster = myRoster?.roster.find((row) => row.canonicalPlayerId === playerId);
    if (onRoster) return { label: "Already on your roster", detail: onRoster.starter ? "Currently starting" : "Currently benched" };
    const candidate = waivers?.addCandidates.find((row) => row.canonicalPlayerId === playerId);
    if (candidate) return { label: candidate.becomesStarter ? "Would become a starter if added" : "Available, bench-only fit", detail: `Marginal utility ${formatNumber(candidate.marginalUtility ?? 0, 1)}` };
    return { label: "Not a current free agent on this league", detail: "Rostered by an opponent, or not identity-matched" };
  };

  return <>
    <PageHeader
      eyebrow={data.activeProfile ? leagueFormat(data.activeProfile, false) : "Choose a league profile"}
      title={`${data.activeProfile?.leagueName ?? "Redraft"} Player Compare`}
      description="Compare projection, replacement value, tier, and confidence inside the active league. Dynasty authority is never consulted."
      status={<><StatusBadge tone="safe" label="Current season" /><StatusBadge tone="safe" label="League specific" /></>}
    />
    <Panel title="Choose two players" eyebrow="Admitted ranking universe">
      <div className="compare-selectors"><SelectField label="Player A" value={left} onChange={setLeft} options={options} /><span><Icon name="compare" /></span><SelectField label="Player B" value={right} onChange={setRight} options={options} /></div>
      <div className="toolbar">
        <SegmentedControl label="Mode" options={COMPARE_MODES as unknown as string[]} value={mode} onChange={(value) => setMode(value as CompareMode)} />
        {mode === "This Week" ? <label className="form-field"><span>NFL week</span><input min={1} max={18} type="number" value={week} onChange={(event) => setWeek(Number(event.target.value))} /></label> : null}
      </div>
      {!isSleeper && mode !== "Rest of Season" ? <p className="copy-muted">This mode requires an active Sleeper league.</p> : null}
    </Panel>
    {a && b ? <CompareCards players={[a, b]} /> : <EmptyState title="Two players required" message="Governed rankings must contain at least two players." />}
    {a && b && mode === "This Week" && isSleeper ? <Panel title="This week" eyebrow={weekly ? `Week ${weekly.week}` : "Reading…"}>
      {weeklyError ? <ErrorState message={weeklyError.message} recovery={weeklyError.recoveryAction} /> : null}
      {weekly ? <div className="compare-card-grid">{[a, b].map((player) => { const row = weeklyRowFor(player.playerId); return <article key={player.playerId}><header><span className="position-pill">{player.position}</span><strong>{player.playerName}</strong></header><div><span>Projected points</span><strong>{row?.projectedPoints == null ? "—" : formatNumber(row.projectedPoints, 1)}</strong></div><div><span>Identity match</span><strong>{row?.identityMatch ?? "UNMATCHED"}</strong></div><div><span>Scoring context</span><strong>{row?.scoringContext ?? "—"}</strong></div></article>; })}</div> : null}
      {weekly ? <p className="copy-muted">Weekly projections: {weekly.providerHealth.provider} · updated {weekly.sourceAsOf}</p> : null}
    </Panel> : null}
    {a && b && mode === "Roster Fit" && isSleeper ? <Panel title="Roster fit" eyebrow="Your league only">
      {waiversError ? <ErrorState message={waiversError.message} recovery={waiversError.recoveryAction} /> : null}
      <div className="compare-card-grid">{[a, b].map((player) => { const fit = rosterFitFor(player.playerId); return <article key={player.playerId}><header><span className="position-pill">{player.position}</span><strong>{player.playerName}</strong></header><div><span>Fit</span><strong>{fit.label}</strong></div><div><span>Detail</span><strong>{fit.detail}</strong></div></article>; })}</div>
    </Panel> : null}
    {a && b && mode === "Trade" ? <Panel title="Trade" eyebrow="Opens the full Trade Analysis workspace">
      <p className="copy-muted">Compare does not embed a full trade evaluation -- that needs your live Sleeper roster and a specific opponent's roster, which Trade Analysis reads directly. Open it, then search for "{a.playerName}" and "{b.playerName}" there.</p>
      <Link to="/trade-analysis">Open Trade Analysis</Link>
    </Panel> : null}
  </>;
}

function CompareCards({ players }: { players: [RedraftRanking, RedraftRanking] }) {
  const preferred = players.slice().sort((a, b) => a.overallRank - b.overallRank)[0]!;
  const dimensions: Array<{ label: string; value: (row: RedraftRanking) => string }> = [
    { label: "Overall rank", value: (row) => `#${row.overallRank}` },
    { label: "Position rank", value: (row) => `${row.position}${row.positionRank}` },
    { label: "Projected points", value: (row) => formatNumber(row.projectedPoints, 1) },
    { label: "Replacement value", value: (row) => formatNumber(row.replacementAdjustedValue, 1) },
    { label: "Replacement points", value: (row) => formatNumber(row.replacementPoints, 1) },
    { label: "Starter gap", value: (row) => formatNumber(row.starterGap, 1) },
    { label: "Tier", value: (row) => String(row.tier) },
    { label: "Confidence", value: (row) => row.confidence },
  ];
  return <div className="redraft-compare"><section className="lean-banner"><span>NWR redraft lean</span><strong>{preferred.playerName}</strong><p>Ranks higher for this league profile. Use the full projection, replacement, tier, and confidence context together.</p></section><div className="compare-card-grid">{players.map((player) => <article key={player.playerId}><header><span className="position-pill">{player.position}</span><div><strong>{player.playerName}</strong><small>{player.team} · Current season</small></div><b>#{player.overallRank}</b></header>{dimensions.map((dimension) => <div key={dimension.label}><span>{dimension.label}</span><strong>{dimension.value(player)}</strong></div>)}</article>)}</div></div>;
}

export function DataHealthPage({ data, onReload }: { data: RedraftBootstrap; onReload: () => void }) {
  const health = data.health;
  return <><PageHeader eyebrow="System · Current-season authority" title="Projection & Data Health" description="Governed projection admission, profile validation, replacement calculation, and local runtime status." status={<><StatusBadge tone={data.status.tone} label={health.status || "Review"} /><StatusBadge tone="safe" label="Dynasty isolated" /></>} actions={<Button icon="activity" onClick={onReload}>Reload local snapshot</Button>} /><section className={`health-hero health-hero--${data.status.tone}`}><div className="health-hero__icon"><Icon name={data.status.ready ? "check" : "alert"} /></div><div><span>Redraft V1 · Review authority</span><h2>{data.status.summary}</h2><p>{data.status.sourceAsOf || "Projection date unavailable"} · {data.status.freshness}</p></div><div><strong>{health.status || "REVIEW"}</strong><small>Contract 1.0</small></div></section><div className="metric-grid"><MetricCard label="Ranked players" value={health.rankedPlayers} detail="Active profile" icon="board" tone="gold" /><MetricCard label="Blocked rows" value={health.blockedPlayers} detail="Visible, never imputed" icon="alert" tone="crimson" /><MetricCard label="Profiles" value={data.profiles.length} detail="Redraft namespace" icon="profile" tone="violet" /><MetricCard label="External network" value="OFF" detail="Local runtime only" icon="shield" tone="cyan" /></div><div className="split-view"><Panel title="Readiness checks" eyebrow="Deterministic validation"><dl className="health-list"><div><dt>Player universe</dt><dd><StatusBadge tone={health.playerUniverseAvailable ? "safe" : "blocked"} label={health.playerUniverseAvailable ? "Available" : "Blocked"} /></dd></div><div><dt>Current forecast</dt><dd><StatusBadge tone={health.currentSeasonForecastAvailable ? "safe" : "blocked"} label={health.currentSeasonForecastAvailable ? "Available" : "Blocked"} /></dd></div><div><dt>Scoring profile</dt><dd><StatusBadge tone={health.scoringProfileValid ? "safe" : "blocked"} label={health.scoringProfileValid ? "Valid" : "Invalid"} /></dd></div><div><dt>Replacement model</dt><dd><StatusBadge tone={health.replacementCalculationValid ? "safe" : "blocked"} label={health.replacementCalculationValid ? "Valid" : "Blocked"} /></dd></div></dl></Panel><Panel title="Desktop safeguards" eyebrow="Windows desktop"><dl className="health-list"><div><dt>Connection</dt><dd>Local computer only</dd></div><div><dt>Saved state</dt><dd>Redraft isolated</dd></div><div><dt>Cloud dependency</dt><dd>None</dd></div><div><dt>Streamlit fallback</dt><dd>Preserved</dd></div></dl></Panel></div>{data.notices.map((notice, index) => <div className={`alert-strip alert-strip--${notice.tone}`} key={`${notice.title}-${index}`}><strong>{notice.title}</strong><span>{notice.message}</span></div>)}{health.messages.map((message, index) => <div className="alert-strip" key={`health-${index}-${message}`}>{message}</div>)}</>;
}

const STREAMER_HORIZON_OPTIONS = ["This Week", "Next 2", "Next 3"] as const;
type StreamerHorizon = (typeof STREAMER_HORIZON_OPTIONS)[number];
const STREAMER_HORIZON_WEEKS: Record<StreamerHorizon, number> = { "This Week": 1, "Next 2": 2, "Next 3": 3 };

export function WeeklyToolsPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const [week, setWeek] = useState(1);
  const [horizon, setHorizon] = useState<StreamerHorizon>("This Week");
  const [results, setResults] = useState<KdstStreamerResult[]>([]);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [working, setWorking] = useState(false);
  const provider = data.externalConsensus;
  useEffect(() => {
    setResults([]);
    setError(null);
  }, [data.activeProfileId]);
  const load = async () => {
    if (working || !provider?.configured) return;
    setWorking(true); setError(null); setResults([]);
    const weekCount = STREAMER_HORIZON_WEEKS[horizon];
    const loaded: KdstStreamerResult[] = [];
    try {
      // Sequential, not parallel -- STREAMER_HORIZON_WEEKS caps this at 3
      // real FantasyPros ECR reads, never a burst against the provider.
      for (let offset = 0; offset < weekCount; offset += 1) {
        const targetWeek = Math.min(18, week + offset);
        loaded.push(await client.kdstStreamer(targetWeek));
      }
      setResults(loaded);
    } catch (reason) {
      setError(reason instanceof NwrApiError ? reason : new NwrApiError("K/DST Streamer could not read its sources."));
    } finally {
      setWorking(false);
    }
  };
  const columns: TableColumn[] = [
    { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span> },
    { key: "ecr", label: "FantasyPros ECR", sort: "number", align: "right" },
    { key: "tier", label: "Tier", sort: "number" },
    { key: "rosterStatus", label: "Sleeper status", sort: "text" },
    { key: "recommendation", label: "Action", sort: "text", render: (row) => <StatusBadge tone={String(row.recommendation) === "ADD" || String(row.recommendation) === "START" ? "safe" : "review"} label={String(row.recommendation)} /> },
  ];
  return <>
    <PageHeader eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a Sleeper league"} title={`${data.activeProfile?.leagueName ?? "Redraft"} — Weekly Tools`} description="External K/DST consensus from FantasyPros, filtered against the active Sleeper roster. NWR does not calculate a K/DST score or combine ECR with Redraft projections -- provider-scored data only." status={<StatusBadge tone={provider?.configured ? "review" : "blocked"} label={provider?.configured ? "Provider configured" : "Provider key required"} />} />
    <Panel title="External consensus authority" eyebrow={provider?.authority ?? "EXTERNAL CONSENSUS — FANTASYPROS"}>
      <p>{provider?.message ?? "Provider status is unavailable."}</p>
      <p className="copy-muted">Use a FantasyPros API key authorized for your account in the local Desktop environment, then restart. No API key is shown, stored in a profile, or sent to Sleeper.</p>
      <div className="profile-edit-actions">
        <label className="form-field"><span>NFL week</span><input min={1} max={18} type="number" value={week} onChange={(event) => setWeek(Number(event.target.value))} /></label>
        <SegmentedControl label="Horizon" options={STREAMER_HORIZON_OPTIONS as unknown as string[]} value={horizon} onChange={(value) => setHorizon(value as StreamerHorizon)} />
        <Button disabled={!provider?.configured || working || !data.activeProfile} icon="activity" onClick={() => void load()}>{working ? "Reading…" : `Refresh K/DST ECR (${horizon})`}</Button>
      </div>
    </Panel>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {results.map((result) => <div key={result.week}>
      <p className="draft-feedback">Week {result.week} · {result.writeBehavior.replaceAll("_", " ")} · provider-scored ECR only; schedule, betting, weather, and hidden weights are not used.</p>
      {(["K", "DST"] as const).map((position) => <Panel key={`${result.week}-${position}`} title={`Week ${result.week} · ${position} streamer actions`} eyebrow="FantasyPros ECR (provider-scored) · Sleeper availability"><DataTable columns={columns} rows={result.positions.filter((row) => row.position === position) as unknown as Array<Record<string, unknown>>} rowKey={(row) => `${position}-${String(row.playerName)}-${String(row.ecr)}`} /></Panel>)}
    </div>)}
  </>;
}

export function FreeAgentsPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const { result, error, working } = useFreeAgents(client, data.activeProfile?.provider === "sleeper" ? data.activeProfileId : null);
  const isSleeper = data.activeProfile?.provider === "sleeper";
  return <>
    <PageHeader eyebrow="Live Sleeper league state" title="Free Agents" description="Players currently on no roster in this league. Existing NWR season rank/value is shown when an exact identity match exists; unmatched players stay explicitly unranked." status={<StatusBadge tone={isSleeper ? "safe" : "blocked"} label={isSleeper ? "Live read-only" : "Sleeper profile required"} />} />
    {!isSleeper ? <EmptyState title="Sleeper league required" message="ESPN and local profiles have no live roster source, so NWR will not fabricate availability." /> : null}
    {working ? <p className="draft-feedback">Reading current Sleeper rosters…</p> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result?.rankingWarning ? <div className="alert-strip"><strong>Ranking unavailable</strong><span>{result.rankingWarning}</span></div> : null}
    {result ? <Panel title={`${result.freeAgents.length} unrostered players`} eyebrow="AVAILABLE · all fantasy positions" action={isSleeper ? <div className="profile-edit-actions"><Link to="/waivers">Open Waiver analysis</Link><Link to="/compare">Open Compare</Link></div> : undefined}><DataTable columns={FREE_AGENT_COLUMNS} rows={result.freeAgents as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.sleeperPlayerId)} /></Panel> : null}
  </>;
}

export function OpponentRostersPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const [result, setResult] = useState<RedraftOpponentRostersResult | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  useEffect(() => {
    let active = true;
    setResult(null); setError(null);
    if (!data.activeProfileId || data.activeProfile?.provider !== "sleeper") return undefined;
    void client.redraftOpponentRosters().then((value) => { if (active) setResult(value); }).catch((reason) => {
      if (active) setError(reason instanceof NwrApiError ? reason : new NwrApiError("Opponent rosters could not be read."));
    });
    return () => { active = false; };
  }, [client, data.activeProfileId, data.activeProfile?.provider]);
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const columns: TableColumn[] = [
    {
      key: "playerName",
      label: "Player",
      sort: "text",
      render: (row) => isSleeper
        ? <Link
            className="opponent-roster-trade-link"
            title={`Add ${String(row.playerName)} to a Trade Analysis "I receive" side`}
            to={`/trade-analysis?receiveSleeperId=${encodeURIComponent(String(row.sleeperPlayerId))}&receiveName=${encodeURIComponent(String(row.playerName))}`}
          >
            {String(row.playerName)}
          </Link>
        : String(row.playerName),
    },
    { key: "position", label: "Position", sort: "text" },
    { key: "team", label: "NFL team", sort: "text" },
    { key: "starter", label: "Lineup", sort: "text", render: (row) => row.starter ? <StatusBadge tone="safe" label="Starter" /> : "Bench" },
  ];
  return <>
    <PageHeader eyebrow="Live Sleeper league state" title="Opponent Rosters" description="Every non-owner team and its current Sleeper roster. This view is read-only and contains no projection or trade recommendation. Click a player to start a Trade Analysis for them." status={<StatusBadge tone={result ? "safe" : data.activeProfile?.provider === "sleeper" ? "review" : "blocked"} label={result ? `${result.opponents.length} opponents` : "Live source"} />} />
    {data.activeProfile?.provider !== "sleeper" ? <EmptyState title="Sleeper league required" message="ESPN and local profiles have no live opponent-roster source." /> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {isSleeper ? <div className="profile-edit-actions"><Link to="/trade-finder">Open Trade Finder (auto-search all opponents)</Link></div> : null}
    {result?.opponents.map((opponent) => <Panel key={opponent.rosterId} title={opponent.teamName} eyebrow={`${opponent.players.length} players · roster ${opponent.rosterId}`}><DataTable columns={columns} rows={opponent.players as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.sleeperPlayerId)} />{opponent.unresolvedSleeperPlayerIds.length ? <p className="copy-muted">Unresolved Sleeper IDs: {opponent.unresolvedSleeperPlayerIds.join(", ")}</p> : null}</Panel>)}
  </>;
}

// NWR in-season UI pass (2026-09-10): the old "coming soon, blocked on a
// governed weekly-projection model" LeagueHomePage is retired -- Start/Sit,
// Waivers, and Trade are now real, live capabilities. See WeeklyHomePage in
// ./in-season.tsx, which composes redraftWeeklyHomeActions with this same
// free-agent read.
