import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { KdstStreamerResult, RedraftBootstrap, RedraftRanking } from "@nwr/contracts";
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

import { draftFormat, leagueFormat } from "./league-context";

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

export function DraftRoomPage({ client, data, onUpdate }: { client: NwrApiClient; data: RedraftBootstrap; onUpdate: (data: RedraftBootstrap) => void }) {
  const [position, setPosition] = useState("ALL");
  const [query, setQuery] = useState("");
  const [depth, setDepth] = useState("25");
  const [working, setWorking] = useState("");
  const [error, setError] = useState<NwrApiError | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const [ownerSlot, setOwnerSlot] = useState(String(data.activeProfile?.draft.draftSlot ?? 9));
  const [speed, setSpeed] = useState<"FAST" | "NORMAL" | "STEP">("NORMAL");
  const [selectedTeam, setSelectedTeam] = useState(data.draftBoard?.ownerSlot ?? 9);
  const mutationInFlight = useRef(false);
  const focusAfterMutation = useRef(false);
  const drafted = draftedIds(data);
  const board = data.draftBoard;
  const ownerTurn = Boolean(board?.isOwnerTurn);
  const manualPosition = position === "K" || position === "DST";
  const filteredRows = rankingRows(data).filter((row) => !row.drafted && (position === "ALL" || row.position === position) && (!query || String(row.playerName).toLowerCase().includes(query.toLowerCase())));
  const manualRows = (data.manualAssets ?? []).filter((row) => !drafted.includes(row.playerId) && row.position === position && (!query || `${row.playerName} ${row.team}`.toLowerCase().includes(query.toLowerCase())));
  const rows = withDepth(filteredRows, depth);
  const team = board?.teams?.find((value) => value.teamSlot === selectedTeam);

  useEffect(() => {
    if (!focusAfterMutation.current) return;
    focusAfterMutation.current = false;
    window.requestAnimationFrame(() => {
      const nextAction = document.querySelector<HTMLButtonElement>("[data-draft-action]:not(:disabled)");
      const undoAction = document.querySelector<HTMLButtonElement>("[data-draft-undo]:not(:disabled)");
      (nextAction ?? undoAction)?.focus();
    });
  }, [drafted.length]);

  const mutate = async (key: string, action: () => Promise<RedraftBootstrap>, success: string) => {
    if (!data.activeProfileId || mutationInFlight.current) return;
    mutationInFlight.current = true;
    setWorking(key);
    setError(null);
    setAnnouncement("");
    try {
      const next = await action();
      focusAfterMutation.current = true;
      onUpdate(next);
      setAnnouncement(key === "adp-refresh" && next.draftBoard?.adp?.lastRefreshError ? "FFC refresh failed; the last known good cached ADP remains active." : success);
    } catch (reason) {
      const nextError = reason instanceof NwrApiError ? reason : new NwrApiError("Draft pick could not be recorded.");
      setError(nextError);
      setAnnouncement(`Draft update failed: ${nextError.message}`);
    } finally {
      mutationInFlight.current = false;
      setWorking("");
    }
  };

  const mark = async (playerId: string) => {
    if (!data.activeProfileId) return;
    const playerName = data.rankings.find((row) => row.playerId === playerId)?.playerName ?? data.manualAssets?.find((row) => row.playerId === playerId)?.playerName ?? "Player";
    await mutate(playerId, () => client.markDrafted(data.activeProfileId!, playerId), `Drafted ${playerName}; CPU selections advanced to your next turn.`);
  };

  const undo = async () => {
    if (!data.activeProfileId) return;
    await mutate("undo", () => client.undoDraftPick(data.activeProfileId!), "Restored the last recorded pick.");
  };

  const start = async () => {
    if (!data.activeProfileId) return;
    const slot = Number(ownerSlot);
    setSelectedTeam(slot);
    await mutate("start", () => client.startDraftRoom(data.activeProfileId!, slot, speed), `Draft Room started from slot ${slot}.`);
  };

  const advance = async (onePick: boolean) => {
    if (!data.activeProfileId) return;
    await mutate(onePick ? "one" : "advance", () => client.advanceDraftRoom(data.activeProfileId!, onePick), onePick ? "Recorded one CPU pick." : "CPU teams advanced to your next pick.");
  };

  const importAdp = async (file: File | undefined) => {
    if (!file || !data.activeProfileId) return;
    await mutate("adp", () => file.text().then((csvText) => client.importRedraftAdp(data.activeProfileId!, csvText)), `Imported owner ADP from ${file.name}; NWR ranks did not change.`);
  };

  const refreshAdp = async () => {
    if (!data.activeProfileId) return;
    await mutate("adp-refresh", () => client.refreshRedraftAdp(data.activeProfileId!), "Refreshed Fantasy Football Calculator ADP; NWR ranks did not change.");
  };

  if (!data.activeProfile) {
    return <><PageHeader eyebrow="Draft command center" title="Redraft Draft Room" description="Choose or create a league profile to build a current-season board." /><EmptyState icon="profile" title="No active league profile" message="Profiles are isolated inside Redraft and never touch Dynasty settings." action={<Button onClick={() => { window.location.hash = "#/profile"; }}>Open profile manager</Button>} /></>;
  }

  const manualColumns: TableColumn[] = [
    { key: "playerName", label: "Manual asset", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span> },
    { key: "authority", label: "Status", sort: "text", render: () => <StatusBadge tone="review" label="Manual · not modeled" /> },
    { key: "overallAdp", label: "ADP", sort: "number", render: (row) => row.overallAdp == null ? "—" : formatNumber(row.overallAdp as number, 1) },
    { key: "action", label: "", align: "right", render: (row) => <Button data-draft-action disabled={!ownerTurn || Boolean(working)} variant="secondary" onClick={() => void mark(String(row.playerId))}>{working === String(row.playerId) ? "Saving…" : "Draft"}</Button> },
  ];
  return <div aria-busy={Boolean(working)} className="draft-room-page">
    {board?.recoveredFromBackup ? <div className="alert-strip" role="status"><strong>Draft board recovered</strong><span>NWR restored the last verified local backup before opening this board.</span></div> : null}
    <PageHeader eyebrow={draftFormat(data.activeProfile)} title={`${data.activeProfile.leagueName} — Draft Room`} description="A persistent 10-team snake room with roster-aware CPU opponents, explicit ADP timing context, and no platform writes." status={<><StatusBadge tone="safe" label={`${data.rankings.length} ranked`} /><StatusBadge tone={board?.adp?.available ? "safe" : "review"} label={board?.adp?.available ? `ADP ${board.adp.freshness ?? "cached"}: ${board.adp.source}` : "ADP unavailable"} /><StatusBadge tone="review" label={`${drafted.length} / ${data.activeProfile.teamCount * data.activeProfile.draft.rounds} picks`} /></>} actions={<><Button data-draft-undo disabled={!board?.canUndo || Boolean(working)} icon="undo" variant="secondary" onClick={() => void undo()}>{working === "undo" ? "Restoring…" : "Undo"}</Button><Button disabled={Boolean(working)} icon="profile" variant="ghost" onClick={() => { window.location.hash = "#/profile"; }}>League profile</Button></>} />
    <p aria-atomic="true" aria-live={error ? "assertive" : "polite"} className={`draft-feedback ${error ? "draft-feedback--error" : ""}`} role="status">{announcement || "Draft board ready. Projection evidence strength is separate from readiness."}</p>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    <Panel title={board?.configured ? "Room controls" : "Set your draft slot"} eyebrow="Deterministic local mock"><div className="draft-setup"><SelectField label="My slot" value={ownerSlot} onChange={setOwnerSlot} options={Array.from({ length: data.activeProfile.teamCount }, (_, index) => ({ value: String(index + 1), label: `Slot ${index + 1}` }))} /><SelectField label="CPU speed" value={speed} onChange={(value) => setSpeed(value as "FAST" | "NORMAL" | "STEP")} options={[{ value: "FAST", label: "Fast" }, { value: "NORMAL", label: "Normal" }, { value: "STEP", label: "Step" }]} /><Button disabled={Boolean(working)} onClick={() => void start()}>{board?.configured ? "Restart draft" : "Start draft"}</Button>{board?.configured ? <><Button disabled={Boolean(working) || ownerTurn || board.complete} variant="secondary" onClick={() => void advance(false)}>Advance to my pick</Button><Button disabled={Boolean(working) || ownerTurn || board.complete} variant="ghost" onClick={() => void advance(true)}>One CPU pick</Button></> : null}<Button disabled={Boolean(working)} variant="secondary" onClick={() => void refreshAdp()}>{working === "adp-refresh" ? "Refreshing…" : "Refresh FFC ADP"}</Button><label className="file-action">Import owner ADP CSV<input accept=".csv,text/csv" disabled={Boolean(working)} onChange={(event) => void importAdp(event.target.files?.[0])} type="file" /></label></div><p className="boundary-note">{board?.fallbackDisclosure ?? "ADP is optional market-timing context and never changes NWR value rank."}{board?.adp?.available ? ` ${board.adp.dateWindow || board.adp.sourceDate}${board.adp.sampleSize ? ` · ${board.adp.sampleSize.toLocaleString()} drafts` : ""}. Fantasy Football Calculator attribution: ${board.adp.attributionUrl || "owner import"}.` : ""}</p></Panel>
    {board?.configured ? <>
      <section className="on-clock"><div><span>{board.complete ? "Draft complete" : board.isOwnerTurn ? "You are on the clock" : `Team ${board.currentTeamSlot} is on the clock`}</span><strong>{board.currentPick ? `Pick ${board.currentPick}` : "150 picks recorded"}</strong><small>{draftFormat(data.activeProfile)}</small></div><div className="clock-ring"><strong>{board.isOwnerTurn ? "YOU" : "CPU"}</strong><span>{board.speed}</span></div><div><span>Next owner pick</span><strong>{board.nextOwnerPick ?? "—"}</strong><small>{board.positionRun?.length ? `Run: ${board.positionRun.map((run) => `${run.position} ×${run.count}`).join(", ")}` : "No active position run"}</small></div></section>
      <Panel title="Draft board" eyebrow="15 rounds · click a team to inspect its roster"><div className="draft-board-scroll"><div className="draft-board-grid"><div className="draft-board-corner">Rd</div>{Array.from({ length: data.activeProfile.teamCount }, (_, index) => index + 1).map((slot) => <button className={slot === board.ownerSlot ? "owner-team" : ""} key={`head-${slot}`} onClick={() => setSelectedTeam(slot)}>T{slot}{slot === board.ownerSlot ? " · YOU" : ""}</button>)}{Array.from({ length: data.activeProfile.draft.rounds }, (_, index) => index + 1).flatMap((round) => [<b className="round-label" key={`round-${round}`}>{round}</b>, ...Array.from({ length: data.activeProfile!.teamCount }, (_, column) => { const slot = column + 1; const cell = board.boardCells?.find((item) => item.round === round && item.teamSlot === slot); return <article className={`${cell?.ownerPick ? "owner-pick" : ""} ${cell?.current ? "current-pick" : ""}`} key={`${round}-${slot}`}><small>{cell?.pickNumber}</small>{cell?.playerName ? <><strong>{cell.playerName}</strong><span>{cell.position} · {cell.team}</span></> : <em>Open</em>}</article>; })])}</div></div></Panel>
      <div className="draft-room-split"><Panel title="Recent picks" eyebrow="Latest eight selections"><div className="recent-picks">{board.recentPicks?.length ? board.recentPicks.slice().reverse().map((pick) => <article key={pick.pickNumber}><b>{pick.pickNumber}</b><span><strong>{pick.playerName}</strong><small>T{pick.teamSlot} · {pick.position} · {pick.actor}</small></span></article>) : <p>No picks yet.</p>}</div></Panel><Panel title={team?.owner ? "My Roster" : team?.name ?? `Team ${selectedTeam}`} eyebrow={`Team ${selectedTeam} roster`}><div className="roster-list">{team?.roster.length ? team.roster.map((player) => <article key={player.playerId}><span className="position-pill">{player.position}</span><strong>{player.playerName}</strong><small>{player.team} · #{player.pickNumber}</small></article>) : <p>No players drafted.</p>}</div></Panel></div>
      <Panel title="Draft recommendations" eyebrow="Five distinct decision lenses"><div className="recommendation-grid">{board.recommendations?.map((card) => <article key={card.label}><span>{card.label}</span><strong>{card.playerName}</strong><small>{card.position} · NWR #{card.nwrRank} · {card.rosterFit}</small><b>{card.nwrView} · {card.draftTiming}</b><p>{card.note}</p><Button data-draft-action disabled={!ownerTurn || Boolean(working)} variant="secondary" onClick={() => void mark(card.playerId)}>Draft</Button></article>)}</div></Panel>
    </> : null}
    <div className="metric-grid"><MetricCard label="Available players" value={Math.max(0, data.rankings.length - drafted.length)} detail="Current board" icon="players" tone="gold" /><MetricCard label="Drafted" value={drafted.length} detail={`Next pick ${drafted.length + 1}`} icon="check" tone="crimson" /><MetricCard label="League teams" value={data.activeProfile.teamCount} detail={data.activeProfile.roster.superflex ? "Superflex" : "1QB"} icon="profile" tone="violet" /><MetricCard label="Scoring" value={data.activeProfile.scoring.reception === 1 ? "PPR" : data.activeProfile.scoring.reception === .5 ? "Half" : "Std"} detail={`${data.activeProfile.draft.rounds} rounds`} icon="settings" tone="cyan" /></div>
    <Panel title={manualPosition ? "Manual position" : "Available player panel"} eyebrow={manualPosition ? "NWR does not currently model K/DST" : `NWR rank remains authoritative · ${filteredRows.length} matches`}><div className="toolbar"><SearchInput value={query} onChange={setQuery} /><SegmentedControl label="Position" options={POSITION_OPTIONS} value={position} onChange={setPosition} />{!manualPosition ? <SelectField label="Show" value={depth} onChange={setDepth} options={DRAFT_DEPTH_OPTIONS} /> : null}</div>{manualPosition ? <DataTable columns={manualColumns} rows={manualRows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.playerId)} /> : <DataTable columns={[{ key: "overallRank", label: "NWR", sort: "number" }, { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)} · {String(row.positionTierLabel)}</small></span> }, { key: "overallAdp", label: "ADP", sort: "number", render: (row) => row.overallAdp == null ? "—" : formatNumber(row.overallAdp as number, 1) }, { key: "expectedRound", label: "Exp rd", sort: "number", render: (row) => row.expectedRound == null ? "—" : `R${String(row.expectedRound)}` }, { key: "nwrAdpGap", label: "Gap", sort: "number", render: (row) => row.nwrAdpGap == null ? "—" : formatNumber(row.nwrAdpGap as number, 1) }, { key: "valueLabel", label: "NWR view", sort: "text" }, { key: "timingLabel", label: "Timing", sort: "text" }, { key: "makeItBack", label: "Make it back", sort: "text" }, { key: "action", label: "", align: "right", render: (row) => <Button data-draft-action disabled={!ownerTurn || Boolean(working)} variant="secondary" onClick={() => void mark(String(row.playerId))}>{working === String(row.playerId) ? "Saving…" : "Draft"}</Button> }]} rows={rows} rowKey={(row) => String(row.playerId)} />}</Panel>
    {board?.configured ? <><Panel title="Beat ADP pool" eyebrow="NWR value view and draft timing are separate"><DataTable columns={[{ key: "nwrRank", label: "NWR", sort: "number" }, { key: "playerName", label: "Player", sort: "text" }, { key: "expectedPick", label: "Expected pick", sort: "number" }, { key: "nwrEdge", label: "NWR edge", sort: "number" }, { key: "nwrView", label: "NWR view", sort: "text" }, { key: "draftTiming", label: "Timing", sort: "text" }, { key: "makeItBack", label: "Make it back", sort: "text" }]} rows={(board.beatAdpPool ?? []) as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.playerId)} /></Panel><Panel title="Full draft log" eyebrow={`${board.draftLog?.length ?? 0} immutable local events`}><DataTable columns={[{ key: "pickNumber", label: "Pick", sort: "number" }, { key: "round", label: "Round", sort: "number" }, { key: "teamSlot", label: "Team", sort: "number" }, { key: "playerName", label: "Player", sort: "text" }, { key: "position", label: "Pos", sort: "text" }, { key: "actor", label: "Actor", sort: "text" }, { key: "selectionBehavior", label: "Selection basis", sort: "text" }]} rows={(board.draftLog ?? []) as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.pickNumber)} /></Panel></> : null}
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
