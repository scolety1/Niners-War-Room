import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { RedraftBootstrap, RedraftRanking } from "@nwr/contracts";
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
} from "@nwr/ui";
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

const POSITION_OPTIONS = ["ALL", "QB", "RB", "WR", "TE", "K", "DST"];
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

function rankingColumns(compact = false): TableColumn[] {
  const base: TableColumn[] = [
    { key: "overallRank", label: "Rank", sort: "number", width: "60px", render: (row) => <span className="rank-cell"><i /><b>#{String(row.overallRank)}</b></span> },
    { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}{String(row.positionRank)}</small></span> },
    { key: "position", label: "Pos", sort: "text", align: "center", render: (row) => <span className="position-pill">{String(row.position)}</span> },
    { key: "tier", label: "Tier", sort: "number", render: (row) => <span className="tier-pill">Tier {String(row.tier)}</span> },
    { key: "projectedPoints", label: "Proj pts", sort: "number", align: "right", render: (row) => formatNumber(row.projectedPoints as number, 1) },
    { key: "replacementAdjustedValue", label: "Value over replacement", sort: "number", align: "right", render: (row) => <span className="vor-cell"><strong>{formatNumber(row.replacementAdjustedValue as number, 1)}</strong><ProgressBar value={Number(row.replacementAdjustedValue ?? 0)} max={250} tone="gold" /></span> },
    { key: "confidence", label: "Confidence", sort: "text" },
  ];
  return compact ? base.slice(0, 6) : [...base, { key: "sourceAsOf", label: "Source as of", sort: "text" }];
}

export function DraftRoomPage({ client, data, onUpdate }: { client: NwrApiClient; data: RedraftBootstrap; onUpdate: (data: RedraftBootstrap) => void }) {
  const [position, setPosition] = useState("ALL");
  const [query, setQuery] = useState("");
  const [depth, setDepth] = useState("25");
  const [working, setWorking] = useState("");
  const [error, setError] = useState<NwrApiError | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const mutationInFlight = useRef(false);
  const focusAfterMutation = useRef(false);
  const drafted = draftedIds(data);
  const filteredRows = rankingRows(data).filter((row) => !row.drafted && (position === "ALL" || row.position === position) && (!query || String(row.playerName).toLowerCase().includes(query.toLowerCase())));
  const rows = withDepth(filteredRows, depth);

  useEffect(() => {
    if (!focusAfterMutation.current) return;
    focusAfterMutation.current = false;
    window.requestAnimationFrame(() => {
      const nextAction = document.querySelector<HTMLButtonElement>("[data-draft-action]:not(:disabled)");
      const undoAction = document.querySelector<HTMLButtonElement>("[data-draft-undo]:not(:disabled)");
      (nextAction ?? undoAction)?.focus();
    });
  }, [drafted.length]);

  const mark = async (playerId: string) => {
    if (!data.activeProfileId || mutationInFlight.current) return;
    mutationInFlight.current = true;
    setWorking(playerId);
    setError(null);
    setAnnouncement("");
    const playerName = data.rankings.find((row) => row.playerId === playerId)?.playerName ?? "Player";
    try {
      const next = await client.markDrafted(data.activeProfileId, playerId);
      focusAfterMutation.current = true;
      onUpdate(next);
      setAnnouncement(`Recorded ${playerName} at pick ${drafted.length + 1}.`);
    } catch (reason) {
      const nextError = reason instanceof NwrApiError ? reason : new NwrApiError("Draft pick could not be recorded.");
      setError(nextError);
      setAnnouncement(`Draft update failed: ${nextError.message}`);
    } finally {
      mutationInFlight.current = false;
      setWorking("");
    }
  };

  const undo = async () => {
    if (!data.activeProfileId || mutationInFlight.current) return;
    mutationInFlight.current = true;
    setWorking("undo");
    setError(null);
    setAnnouncement("");
    const restoredId = drafted.at(-1);
    const restoredName = data.rankings.find((row) => row.playerId === restoredId)?.playerName ?? "the last player";
    try {
      const next = await client.undoDraftPick(data.activeProfileId);
      focusAfterMutation.current = true;
      onUpdate(next);
      setAnnouncement(`Restored ${restoredName} to the available board.`);
    } catch (reason) {
      const nextError = reason instanceof NwrApiError ? reason : new NwrApiError("Last pick could not be undone.");
      setError(nextError);
      setAnnouncement(`Undo failed: ${nextError.message}`);
    } finally {
      mutationInFlight.current = false;
      setWorking("");
    }
  };

  if (!data.activeProfile) {
    return <><PageHeader eyebrow="Draft command center" title="Redraft Draft Room" description="Choose or create a league profile to build a current-season board." /><EmptyState icon="profile" title="No active league profile" message="Profiles are isolated inside Redraft and never touch Dynasty settings." action={<Button onClick={() => { window.location.hash = "#/profile"; }}>Open profile manager</Button>} /></>;
  }

  return <div aria-busy={Boolean(working)} className="draft-room-page">
    {data.draftBoard?.recoveredFromBackup ? <div className="alert-strip" role="status"><strong>Draft board recovered</strong><span>NWR restored the last verified local backup before opening this board.</span></div> : null}
    <PageHeader eyebrow="Live draft · Current season" title={`${data.activeProfile.leagueName} Draft Room`} description="A fast current-season board built from this league's scoring, roster demand, and governed projections." status={<><StatusBadge tone="safe" label={`${data.rankings.length} ranked`} /><StatusBadge tone="review" label={`${drafted.length} drafted`} /></>} actions={<><Button data-draft-undo disabled={!drafted.length || Boolean(working)} icon="undo" variant="secondary" onClick={() => void undo()}>{working === "undo" ? "Restoring…" : "Undo last pick"}</Button><Button disabled={Boolean(working)} icon="profile" variant="ghost" onClick={() => { window.location.hash = "#/profile"; }}>League profile</Button></>} />
    <p aria-atomic="true" aria-live={error ? "assertive" : "polite"} className={`draft-feedback ${error ? "draft-feedback--error" : ""}`} role="status">{announcement || "Draft board ready."}</p>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    <section className="on-clock"><div><span>On the clock</span><strong>Pick {drafted.length + 1}</strong><small>{data.activeProfile.draft.draftType} · Slot {data.activeProfile.draft.draftSlot ?? "—"}</small></div><div className="clock-ring"><strong>∞</strong><span>Offline</span></div><div><span>Top available</span><strong>{filteredRows[0]?.playerName ? String(filteredRows[0].playerName) : "No admitted player"}</strong><small>{filteredRows[0]?.position ? `${String(filteredRows[0].position)}${String(filteredRows[0].positionRank)} · Tier ${String(filteredRows[0].tier)}` : "Projection evidence required"}</small></div></section>
    <div className="metric-grid"><MetricCard label="Available players" value={Math.max(0, data.rankings.length - drafted.length)} detail="Current board" icon="players" tone="gold" /><MetricCard label="Drafted" value={drafted.length} detail={`Next pick ${drafted.length + 1}`} icon="check" tone="crimson" /><MetricCard label="League teams" value={data.activeProfile.teamCount} detail={data.activeProfile.roster.superflex ? "Superflex" : "1QB"} icon="profile" tone="violet" /><MetricCard label="Scoring" value={data.activeProfile.scoring.reception === 1 ? "PPR" : data.activeProfile.scoring.reception === .5 ? "Half" : "Std"} detail={`${data.activeProfile.draft.rounds} rounds`} icon="settings" tone="cyan" /></div>
    <Panel title="Best available" eyebrow={`Profile-adjusted · ${filteredRows.length} matches`}><div className="toolbar"><SearchInput value={query} onChange={setQuery} /><SegmentedControl label="Position" options={POSITION_OPTIONS} value={position} onChange={setPosition} /><SelectField label="Show" value={depth} onChange={setDepth} options={DRAFT_DEPTH_OPTIONS} /></div><DataTable columns={[...rankingColumns(), { key: "action", label: "", align: "right", render: (row) => <Button data-draft-action disabled={Boolean(working)} variant="secondary" onClick={() => void mark(String(row.playerId))}>{working === String(row.playerId) ? "Saving…" : "Draft"}</Button> }]} rows={rows} rowKey={(row) => String(row.playerId)} /></Panel>
  </div>;
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
  const rows = useMemo(() => withDepth(filteredRows, depth), [depth, filteredRows]);
  const reset = () => {
    setQuery("");
    setPosition("ALL");
    setTeam("ALL");
    setAvailability("Available");
    setDepth("100");
    setTableResetKey((value) => value + 1);
  };
  return <><PageHeader eyebrow="Player board · League specific" title="Redraft Rankings" description="Current-season projection value, dynamic replacement level, confidence, and tiers for the active league profile." status={<><StatusBadge tone={data.rankings.length ? "safe" : "blocked"} label={`${data.rankings.length} ranked players`} /><StatusBadge tone="safe" label="Dynasty independent" /></>} /><Panel title="Current-season board" eyebrow={`Showing ${rows.length} of ${filteredRows.length} matches`}><div className="toolbar"><SearchInput value={query} onChange={setQuery} /><SegmentedControl label="Position" options={POSITION_OPTIONS} value={position} onChange={setPosition} /><SelectField label="Team" value={team} onChange={setTeam} options={teams.map((value) => ({ value, label: value === "ALL" ? "All teams" : value }))} /><SelectField label="Availability" value={availability} onChange={setAvailability} options={["Available", "Drafted", "All"].map((value) => ({ value, label: value }))} /><SelectField label="Board depth" value={depth} onChange={setDepth} options={BOARD_DEPTH_OPTIONS} /><Button icon="undo" onClick={reset} variant="ghost">Reset</Button></div><DataTable columns={rankingColumns()} resetKey={tableResetKey} rows={rows} rowKey={(row) => String(row.playerId)} /></Panel></>;
}

export function TiersPage({ data }: { data: RedraftBootstrap }) {
  const [position, setPosition] = useState("ALL");
  const [depth, setDepth] = useState("100");
  const filteredRows = useMemo(() => data.rankings.filter((row) => position === "ALL" || row.position === position), [data.rankings, position]);
  const visibleRows = useMemo(() => withDepth(filteredRows, depth), [depth, filteredRows]);
  const tiers = Array.from(new Set(visibleRows.map((row) => row.tier))).sort((a, b) => a - b);
  return <><PageHeader eyebrow="Draft board · Value cliffs" title="Tiers & Position Rooms" description="See where the active profile creates meaningful replacement-adjusted value breaks." status={<><StatusBadge tone={data.rankings.length ? "safe" : "blocked"} label={data.activeProfile?.leagueName ?? "No active profile"} /><StatusBadge tone="safe" label={`${visibleRows.length} of ${filteredRows.length} shown`} /></>} /><div className="toolbar"><SegmentedControl label="Position room" options={POSITION_OPTIONS} value={position} onChange={setPosition} /><SelectField label="Board depth" value={depth} onChange={setDepth} options={BOARD_DEPTH_OPTIONS} /></div><div className="tier-stack">{tiers.map((tier) => { const players = visibleRows.filter((row) => row.tier === tier); return <Panel key={tier} title={`Tier ${tier}`} eyebrow={`${players.length} shown`}><div className="tier-player-grid">{players.map((row) => <article key={row.playerId}><span>{row.overallRank}</span><div><strong>{row.playerName}</strong><small>{row.team} · {row.position}{row.positionRank}</small></div><b>{formatNumber(row.replacementAdjustedValue, 1)}</b></article>)}</div></Panel>; })}</div></>;
}

export function ComparePage({ data }: { data: RedraftBootstrap }) {
  const [left, setLeft] = useState(data.rankings[0]?.playerId ?? "");
  const [right, setRight] = useState(data.rankings[1]?.playerId ?? "");
  const a = data.rankings.find((row) => row.playerId === left);
  const b = data.rankings.find((row) => row.playerId === right);
  const options = data.rankings.map((row) => ({ value: row.playerId, label: `#${row.overallRank} ${row.playerName} · ${row.position}${row.positionRank}` }));
  return <><PageHeader eyebrow="Decision lab · Current season only" title="Redraft Player Compare" description="Compare projection, replacement value, tier, and confidence inside the active league. Dynasty authority is never consulted." status={<><StatusBadge tone="safe" label="Current season" /><StatusBadge tone="safe" label="Profile specific" /></>} /><Panel title="Choose two players" eyebrow="Admitted ranking universe"><div className="compare-selectors"><SelectField label="Player A" value={left} onChange={setLeft} options={options} /><span><Icon name="compare" /></span><SelectField label="Player B" value={right} onChange={setRight} options={options} /></div></Panel>{a && b ? <CompareCards players={[a, b]} /> : <EmptyState title="Two players required" message="Governed rankings must contain at least two players." />}</>;
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
