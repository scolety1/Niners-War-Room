import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { KdstStreamerResult, RedraftBootstrap, RedraftExternalIntelligence, RedraftExternalIntelligenceEntry, RedraftRanking } from "@nwr/contracts";
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
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { draftFormat, leagueFormat } from "./league-context";

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

export function ComparePage({ data }: { data: RedraftBootstrap }) {
  const [left, setLeft] = useState(data.rankings[0]?.playerId ?? "");
  const [right, setRight] = useState(data.rankings[1]?.playerId ?? "");
  useEffect(() => {
    setLeft(data.rankings[0]?.playerId ?? "");
    setRight(data.rankings[1]?.playerId ?? "");
  }, [data.activeProfileId, data.rankings]);
  const a = data.rankings.find((row) => row.playerId === left);
  const b = data.rankings.find((row) => row.playerId === right);
  const options = data.rankings.map((row) => ({ value: row.playerId, label: `#${row.overallRank} ${row.playerName} · ${row.position}${row.positionRank}` }));
  return <><PageHeader eyebrow={data.activeProfile ? leagueFormat(data.activeProfile, false) : "Choose a league profile"} title={`${data.activeProfile?.leagueName ?? "Redraft"} Player Compare`} description="Compare projection, replacement value, tier, and confidence inside the active league. Dynasty authority is never consulted." status={<><StatusBadge tone="safe" label="Current season" /><StatusBadge tone="safe" label="League specific" /></>} /><Panel title="Choose two players" eyebrow="Admitted ranking universe"><div className="compare-selectors"><SelectField label="Player A" value={left} onChange={setLeft} options={options} /><span><Icon name="compare" /></span><SelectField label="Player B" value={right} onChange={setRight} options={options} /></div></Panel>{a && b ? <CompareCards players={[a, b]} /> : <EmptyState title="Two players required" message="Governed rankings must contain at least two players." />}</>;
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

export function WeeklyToolsPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const [week, setWeek] = useState(1);
  const [result, setResult] = useState<KdstStreamerResult | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [working, setWorking] = useState(false);
  const provider = data.externalConsensus;
  useEffect(() => {
    setResult(null);
    setError(null);
  }, [data.activeProfileId]);
  const load = async () => {
    if (working || !provider?.configured) return;
    setWorking(true); setError(null);
    try { setResult(await client.kdstStreamer(week)); }
    catch (reason) { setError(reason instanceof NwrApiError ? reason : new NwrApiError("K/DST Streamer could not read its sources.")); }
    finally { setWorking(false); }
  };
  const columns: TableColumn[] = [
    { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span> },
    { key: "ecr", label: "FantasyPros ECR", sort: "number", align: "right" },
    { key: "tier", label: "Tier", sort: "number" },
    { key: "rosterStatus", label: "Sleeper status", sort: "text" },
    { key: "recommendation", label: "Action", sort: "text", render: (row) => <StatusBadge tone={String(row.recommendation) === "ADD" || String(row.recommendation) === "START" ? "safe" : "review"} label={String(row.recommendation)} /> },
  ];
  return <>
    <PageHeader eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a Sleeper league"} title={`${data.activeProfile?.leagueName ?? "Redraft"} — Weekly Tools`} description="External K/DST consensus from FantasyPros, filtered against the active Sleeper roster. NWR does not calculate a K/DST score or combine ECR with Redraft projections." status={<StatusBadge tone={provider?.configured ? "review" : "blocked"} label={provider?.configured ? "Provider configured" : "Provider key required"} />} />
    <Panel title="External consensus authority" eyebrow={provider?.authority ?? "EXTERNAL CONSENSUS — FANTASYPROS"}>
      <p>{provider?.message ?? "Provider status is unavailable."}</p>
      <p className="copy-muted">Use a FantasyPros API key authorized for your account in the local Desktop environment, then restart. No API key is shown, stored in a profile, or sent to Sleeper.</p>
      <div className="profile-edit-actions"><label className="form-field"><span>NFL week</span><input min={1} max={18} type="number" value={week} onChange={(event) => setWeek(Number(event.target.value))} /></label><Button disabled={!provider?.configured || working || !data.activeProfile} icon="activity" onClick={() => void load()}>{working ? "Reading…" : "Refresh K/DST ECR"}</Button></div>
    </Panel>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result ? <><p className="draft-feedback">Week {result.week} · {result.writeBehavior.replaceAll("_", " ")} · ECR only; schedule, betting, weather, and hidden weights are not used.</p>{(["K", "DST"] as const).map((position) => <Panel key={position} title={`${position} streamer actions`} eyebrow="FantasyPros ECR · Sleeper availability"><DataTable columns={columns} rows={result.positions[position] as unknown as Array<Record<string, unknown>>} rowKey={(row) => `${position}-${String(row.playerName)}-${String(row.ecr)}`} /></Panel>)}</> : null}
  </>;
}
