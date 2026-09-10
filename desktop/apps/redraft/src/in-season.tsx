import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type {
  RedraftBootstrap,
  TradeAnalysisResult,
  TradeFinderCandidate,
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

import { leagueFormat } from "./league-context";
import {
  ACTION_CATEGORY_LABEL,
  ACTION_CATEGORY_LINK,
  FAAB_URGENCY_TONE,
  FREE_AGENT_COLUMNS,
  ProviderStatusLine,
  RefreshProjectionsButton,
  WeekControl,
  statusTone,
  useAsync,
  useFreeAgents,
} from "./weekly-shared";

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

// ---------------------------------------------------------------------------
// Weekly Home
// ---------------------------------------------------------------------------

export function WeeklyHomePage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const profileId = isSleeper ? data.activeProfileId : null;
  const [week, setWeek] = useState(1);

  const actionsLoader = useCallback(
    () => (profileId ? client.redraftWeeklyHomeActions(week) : null),
    [client, profileId, week],
  );
  const { result: actions, error: actionsError, working: actionsWorking } = useAsync(actionsLoader, [profileId, week]);

  const lineupLoader = useCallback(() => (profileId ? client.redraftWeeklyLineup(week) : null), [client, profileId, week]);
  const { result: lineup } = useAsync(lineupLoader, [profileId, week]);

  const { result: freeAgents, error: freeAgentError, working: freeAgentsWorking } = useFreeAgents(client, profileId);

  const activeName = data.activeProfile?.leagueName ?? "Choose a league";

  return <>
    <PageHeader
      eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"}
      title={`${activeName} · Week ${week}`}
      description="Real, ranked in-season actions NWR can support honestly this week for YOUR roster -- never a filled quota. Opponent matchup scoring is not part of the current Sleeper integration, so this view does not claim a live head-to-head score."
      status={<StatusBadge tone={data.status.tone} label={data.health.status || "Review"} />}
      actions={<WeekControl week={week} onChange={setWeek} />}
    />
    {!isSleeper ? <EmptyState title="Sleeper league required" message="Weekly in-season tools (Start/Sit, Waivers, Trade, streamers) require an active Sleeper-imported league. Choose or import one." action={<Link to="/leagues">Open league chooser</Link>} /> : null}
    {isSleeper ? <>
      <Panel title="NWR Actions" eyebrow={actionsWorking ? "Reading live data…" : actions ? `${actions.actions.length} ranked action${actions.actions.length === 1 ? "" : "s"}` : "—"}>
        {actionsError ? <ErrorState message={actionsError.message} recovery={actionsError.recoveryAction} /> : null}
        {actions && actions.actions.length === 0 ? <EmptyState title="No high-priority actions right now" message="Lineup, waivers, trades, and streamers were all checked live -- none returned anything worth flagging this week." /> : null}
        {actions && actions.actions.length > 0 ? (
          <ol className="nwr-actions-list">
            {actions.actions.map((action, index) => {
              const link = ACTION_CATEGORY_LINK[action.category];
              return (
                <li key={`${action.category}-${index}`}>
                  <span className="nwr-actions-list__index">{index + 1}</span>
                  <div><strong>{action.summary}</strong><small>{ACTION_CATEGORY_LABEL[action.category] ?? action.category}</small></div>
                  {link ? <Link to={link}>Open</Link> : null}
                </li>
              );
            })}
          </ol>
        ) : null}
        {actions?.unavailableSections.length ? (
          <div className="alert-strip">
            <strong>Some sections unavailable</strong>
            <span>{actions.unavailableSections.map((section) => `${section.section}: ${section.reason}`).join(" · ")}</span>
          </div>
        ) : null}
      </Panel>
      <div className="split-view">
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
          {freeAgents ? <DataTable columns={FREE_AGENT_COLUMNS} rows={freeAgents.freeAgents.slice(0, 8) as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.sleeperPlayerId)} /> : freeAgentsWorking ? <p className="draft-feedback">Reading…</p> : null}
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
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const [week, setWeek] = useState(1);
  const loader = useCallback(() => (isSleeper ? client.redraftWeeklyLineup(week) : null), [client, isSleeper, week]);
  const { result, error, working, reload } = useAsync(loader, [isSleeper, week]);

  const benchColumns: TableColumn[] = [
    { key: "playerName", label: "Player", sort: "text" },
    { key: "position", label: "Pos", sort: "text" },
    { key: "projectedPoints", label: "Proj pts", sort: "number", align: "right", render: (row) => row.projectedPoints == null ? "—" : formatNumber(Number(row.projectedPoints), 1) },
  ];

  return <>
    <PageHeader
      eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"}
      title={`Start / Sit — THIS WEEK (Week ${week})`}
      description="NWR's recommended legal lineup for this week only -- never confused with rest-of-season rankings. Recommendation-only: NWR never writes a lineup to Sleeper."
      status={result ? <StatusBadge tone={result.providerHealth.freshness === "STALE" ? "review" : "safe"} label={`${result.matched} matched · ${result.unmatched} unmatched`} /> : undefined}
      actions={<div className="profile-edit-actions"><WeekControl week={week} onChange={setWeek} /><RefreshProjectionsButton onRefresh={reload} working={working} /></div>}
    />
    {!isSleeper ? <EmptyState title="Sleeper league required" message="Start/Sit needs a live Sleeper roster and the real weekly-projection source." /> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result ? <>
      <ProviderStatusLine health={result.providerHealth} />
      {result.swaps.length ? (
        <Panel title="Recommended changes" eyebrow={`${result.swaps.length} change${result.swaps.length === 1 ? "" : "s"} vs. Sleeper's current starters`}>
          <ol className="nwr-actions-list">{result.swaps.map((swap, index) => <li key={index}><span className="nwr-actions-list__index">{index + 1}</span><div><strong>{swap.summary}</strong><small>{SLOT_LABEL[swap.slotType] ?? swap.slotType}</small></div></li>)}</ol>
        </Panel>
      ) : (
        <Panel title="Recommended changes" eyebrow="0 changes"><EmptyState title="Already optimal" message="Sleeper's current starters already match NWR's optimal lineup for this week." /></Panel>
      )}
      <Panel title="Starting lineup" eyebrow={`Projected total ${formatNumber(result.projectedTotal, 1)} pts`}>
        <div className="tier-player-grid">
          {result.starters.map((slot, index) => (
            <article key={index}>
              <span>{SLOT_LABEL[slot.slotType] ?? slot.slotType}</span>
              <div>
                <strong>{slot.player?.playerName ?? "Empty slot"}</strong>
                <small>{slot.player ? `${slot.player.team} · ${slot.player.position}` : "No eligible player"}</small>
              </div>
              <b>{slot.player?.projectedPoints == null ? "—" : formatNumber(slot.player.projectedPoints, 1)}</b>
              <StatusBadge
                tone={slot.closeCall ? "review" : statusTone(slot.status)}
                label={slot.closeCall ? `CLOSE CALL vs ${slot.closeCallAlternative ?? "alt"} (${formatNumber(slot.closeCallMargin ?? 0, 1)})` : slot.status}
              />
            </article>
          ))}
        </div>
      </Panel>
      <Panel title="Bench" eyebrow={`${result.bench.length} players`}>
        <DataTable columns={benchColumns} rows={result.bench as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.sleeperPlayerId)} />
      </Panel>
      {result.excluded.length ? (
        <Panel title="Not included this week" eyebrow={`${result.excluded.length} player(s)`}>
          <p className="copy-muted">{result.excluded.map((player) => player.playerName).join(", ")} -- no roster slot they're eligible for, or no usable projection.</p>
        </Panel>
      ) : null}
    </> : null}
  </>;
}

// ---------------------------------------------------------------------------
// Waivers + Add/Drop + FAAB
// ---------------------------------------------------------------------------

function AddDropDetail({
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
  // dropCandidates IS the full current roster (rank_drop_candidates ranks
  // every rostered player, weakest first) -- the only real source this app
  // has for a position-depth breakdown, so it's reused rather than
  // re-derived some other way.
  const depthBefore = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const drop of waivers.dropCandidates) counts[drop.position] = (counts[drop.position] ?? 0) + 1;
    return counts;
  }, [waivers.dropCandidates]);
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
            <p>{add.becomesStarter ? `Projected to become a starter this week (${formatNumber(add.weeklyProjectedPoints ?? 0, 1)} pts).` : "Would not become a starter this week under NWR's lineup optimizer."}</p>
          ) : <p className="copy-muted">Switch to THIS WEEK mode above for a weekly-lineup estimate.</p>}
          <h3>Rest-of-season impact</h3>
          <p>
            Replacement value {formatNumber(add.rosReplacementValue ?? 0, 1)} · Marginal utility {formatNumber(add.marginalUtility ?? 0, 1)}
            {suggestedDrop ? <> vs. dropping {suggestedDrop.playerName} ({formatNumber(suggestedDrop.marginalUtility ?? 0, 1)}) — net {formatNumber(pairing?.netMarginalUtility ?? 0, 1)}</> : null}
          </p>
          <h3>Status / risk</h3>
          <p>{add.marginalUtilityExplanation}{suggestedDrop ? <><br /><span className="copy-muted">Drop rationale: {suggestedDrop.explanation}</span></> : null}</p>
          <h3>FAAB recommendation</h3>
          {add.faabBidLowDollars == null ? <p className="copy-muted">No FAAB estimate available for this candidate.</p> : (
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
          {!suggestedDrop ? <p className="copy-muted">NWR did not suggest a drop pairing for this add -- pick one from the candidates below, or add without dropping if you have an open bench slot.</p> : null}
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
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const [mode, setMode] = useState<"THIS_WEEK" | "REST_OF_SEASON">("REST_OF_SEASON");
  const [week, setWeek] = useState(1);
  const [position, setPosition] = useState("ALL");
  const [view, setView] = useState("Available to add");
  const [remainingBudget, setRemainingBudget] = useState(100);
  const [weeksRemaining, setWeeksRemaining] = useState(14);
  const [totalBudget, setTotalBudget] = useState(100);
  const [selectedAddId, setSelectedAddId] = useState<string | null>(null);

  const loader = useCallback(
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
  const { result, error, working, reload } = useAsync(loader, [isSleeper, mode, week, remainingBudget, weeksRemaining, totalBudget]);

  const positions = ["ALL", ...new Set((result?.addCandidates ?? []).map((row) => row.position))];
  const addRows = useMemo(() => (result?.addCandidates ?? []).filter((row) => position === "ALL" || row.position === position), [result, position]);
  const dropRows = useMemo(() => (result?.dropCandidates ?? []).filter((row) => position === "ALL" || row.position === position), [result, position]);
  const pairingRows = useMemo(() => (result?.addDropPairings ?? []).filter((row) => position === "ALL" || row.add.position === position), [result, position]);
  const selectedAdd = result?.addCandidates.find((row) => row.canonicalPlayerId === selectedAddId) ?? null;

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
    {!isSleeper ? <EmptyState title="Sleeper league required" message="Waivers needs a live Sleeper roster and the governed NWR ranking." /> : null}
    <div className="toolbar">
      <SegmentedControl label="Mode" options={["REST_OF_SEASON", "THIS_WEEK"]} value={mode} onChange={(value) => setMode(value as "THIS_WEEK" | "REST_OF_SEASON")} />
      {mode === "THIS_WEEK" ? <WeekControl week={week} onChange={setWeek} /> : null}
      <SelectField label="Position" value={position} onChange={setPosition} options={positions.map((value) => ({ value, label: value }))} />
      <SegmentedControl label="View" options={["Available to add", "Add/Drop pairings", "Consider dropping"]} value={view} onChange={setView} />
      <Button icon="activity" variant="secondary" onClick={reload} disabled={working}>{working ? "Reading…" : "Refresh"}</Button>
    </div>
    <Panel title="FAAB settings" eyebrow="Used to compute the suggested bid range below">
      <div className="profile-edit-actions">
        <label className="form-field"><span>Remaining budget ($)</span><input type="number" min={0} value={remainingBudget} onChange={(event) => setRemainingBudget(Math.max(0, Number(event.target.value) || 0))} /></label>
        <label className="form-field"><span>Total season budget ($)</span><input type="number" min={1} value={totalBudget} onChange={(event) => setTotalBudget(Math.max(1, Number(event.target.value) || 1))} /></label>
        <label className="form-field"><span>Weeks remaining</span><input type="number" min={1} max={18} value={weeksRemaining} onChange={(event) => setWeeksRemaining(Math.min(18, Math.max(1, Number(event.target.value) || 1)))} /></label>
      </div>
    </Panel>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result?.rankingWarning ? <div className="alert-strip"><strong>Ranking unavailable</strong><span>{result.rankingWarning}</span></div> : null}
    {mode === "THIS_WEEK" ? <ProviderStatusLine health={result?.weeklyProviderHealth ?? null} /> : null}
    {result ? <>
      {view === "Available to add" ? <Panel title="Available to add" eyebrow={`${addRows.length} shown`}><DataTable columns={addColumns} rows={addRows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.canonicalPlayerId)} /></Panel> : null}
      {view === "Add/Drop pairings" ? <Panel title="Suggested add/drop pairings" eyebrow={`${pairingRows.length} shown`}><DataTable columns={pairingColumns} rows={pairingRows as unknown as Array<Record<string, unknown>>} rowKey={(row) => (row as unknown as (typeof pairingRows)[number]).add.canonicalPlayerId} /></Panel> : null}
      {view === "Consider dropping" ? <Panel title="Weakest current roster players" eyebrow={`${dropRows.length} shown, weakest first`}><DataTable columns={dropColumns} rows={dropRows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.canonicalPlayerId)} /></Panel> : null}
      {selectedAdd ? <AddDropDetail add={selectedAdd} waivers={result} mode={mode} onClose={() => setSelectedAddId(null)} /> : null}
      {result.unmatchedRosterSleeperPlayerIds.length ? <p className="copy-muted">Unresolved roster Sleeper IDs: {result.unmatchedRosterSleeperPlayerIds.join(", ")}</p> : null}
    </> : null}
  </>;
}

// ---------------------------------------------------------------------------
// My Roster (needed for Trade Analysis's "I give" picker; also a real,
// useful standalone read -- no existing page showed the owner's own roster
// with live Sleeper identity).
// ---------------------------------------------------------------------------

export function MyRosterPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const loader = useCallback(() => (isSleeper ? client.redraftMyRoster() : null), [client, isSleeper]);
  const { result, error, working } = useAsync(loader, [isSleeper]);
  const columns: TableColumn[] = [
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
  ];
  return <>
    <PageHeader eyebrow="Live Sleeper league state" title="My Roster" description="Your current live Sleeper roster. Read-only." status={<StatusBadge tone={isSleeper ? "safe" : "blocked"} label={isSleeper ? "Live read-only" : "Sleeper profile required"} />} />
    {!isSleeper ? <EmptyState title="Sleeper league required" message="ESPN and local profiles have no live roster source." /> : null}
    {working ? <p className="draft-feedback">Reading current Sleeper roster…</p> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result?.rankingWarning ? <div className="alert-strip"><strong>Ranking unavailable</strong><span>{result.rankingWarning}</span></div> : null}
    {result ? <Panel title={`${result.roster.length} rostered players`} eyebrow="Read-only"><DataTable columns={columns} rows={result.roster as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.sleeperPlayerId)} /></Panel> : null}
  </>;
}

// ---------------------------------------------------------------------------
// Redraft Trade Analysis
// ---------------------------------------------------------------------------

type TradeSide = { sleeperPlayerId: string; name: string };

function verdictFor(result: TradeAnalysisResult): { label: string; tone: "safe" | "review" | "blocked" } {
  const netUtility = result.netMarginalUtility;
  const rosValue = result.rosValueDelta;
  if (netUtility > 0 && rosValue >= 0) return { label: "Improves my roster", tone: "safe" };
  if (netUtility < 0 && rosValue <= 0) return { label: "Hurts my roster", tone: "blocked" };
  return { label: "Close", tone: "review" };
}

function TradeSidePicker({
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
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const [searchParams] = useSearchParams();
  const [gives, setGives] = useState<TradeSide[]>([]);
  const [receives, setReceives] = useState<TradeSide[]>([]);
  const [result, setResult] = useState<TradeAnalysisResult | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [working, setWorking] = useState(false);

  const myRosterLoader = useCallback(() => (isSleeper ? client.redraftMyRoster() : null), [client, isSleeper]);
  const { result: myRoster } = useAsync(myRosterLoader, [isSleeper]);
  const opponentsLoader = useCallback(() => (isSleeper ? client.redraftOpponentRosters() : null), [client, isSleeper]);
  const { result: opponents } = useAsync(opponentsLoader, [isSleeper]);

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
  ];

  const verdict = result ? verdictFor(result) : null;

  return <>
    <PageHeader eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"} title="Redraft Trade Analysis" description="I-give / I-receive. Real, structured before/after impact -- never a single opaque trade score. NWR never proposes or accepts a trade on Sleeper." status={isSleeper ? undefined : <StatusBadge tone="blocked" label="Sleeper profile required" />} />
    {!isSleeper ? <EmptyState title="Sleeper league required" message="Trade Analysis needs your live Sleeper roster and a live opponent roster." /> : null}
    {isSleeper ? <>
      <Panel title="Build a trade">
        <div className="split-view">
          <TradeSidePicker label="I give" side={gives} candidates={giveCandidates} onAdd={(candidate) => setGives((current) => [...current, candidate])} onRemove={(id) => setGives((current) => current.filter((p) => p.sleeperPlayerId !== id))} />
          <TradeSidePicker label="I receive" side={receives} candidates={receiveCandidates} onAdd={(candidate) => setReceives((current) => [...current, candidate])} onRemove={(id) => setReceives((current) => current.filter((p) => p.sleeperPlayerId !== id))} />
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

function TradeFinderCard({ candidate }: { candidate: TradeFinderCandidate }) {
  const fits = candidate.myNetMarginalUtility > 0 && candidate.opponentNetMarginalUtility > 0;
  return (
    <article className="trade-finder-card">
      <header>
        <strong>vs. {candidate.opponentTeamName}</strong>
        <StatusBadge tone={fits ? "safe" : "review"} label={fits ? "Mutual improvement" : "One-sided"} />
      </header>
      <p>You send: <strong>{candidate.myGivePlayerName}</strong></p>
      <p>You receive: <strong>{candidate.opponentGivePlayerName}</strong></p>
      <p className="copy-muted">
        Why it may fit: {fits
          ? "both sides' real marginal roster utility improves under NWR's evaluator."
          : "only one side's marginal utility improves under NWR's evaluator -- the other team may not agree."}
      </p>
      <p>NWR impact: your net marginal utility {formatNumber(candidate.myNetMarginalUtility, 1)} · ROS value delta {formatNumber(candidate.myRosValueDelta, 1)} · their net marginal utility {formatNumber(candidate.opponentNetMarginalUtility, 1)}</p>
      <Link to={`/trade-analysis?giveSleeperId=${encodeURIComponent(candidate.myGivePlayerId)}&giveName=${encodeURIComponent(candidate.myGivePlayerName)}&receiveSleeperId=${encodeURIComponent(candidate.opponentGivePlayerId)}&receiveName=${encodeURIComponent(candidate.opponentGivePlayerName)}`}>
        Open in Trade Analysis
      </Link>
    </article>
  );
}

export function TradeFinderPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const isSleeper = data.activeProfile?.provider === "sleeper";
  const loader = useCallback(() => (isSleeper ? client.redraftTradeFinder() : null), [client, isSleeper]);
  const { result, error, working, reload } = useAsync(loader, [isSleeper]);
  return <>
    <PageHeader
      eyebrow={data.activeProfile ? leagueFormat(data.activeProfile) : "Choose a league"}
      title="Trade Finder"
      description="Real win-win candidates evaluated against every live opponent roster. NWR never claims an opponent will accept -- no acceptance model exists."
      status={result ? <StatusBadge tone="safe" label={`${result.candidates.length} candidates`} /> : undefined}
      actions={<Button icon="activity" onClick={reload} disabled={working} variant="secondary">{working ? "Searching…" : "Refresh"}</Button>}
    />
    {!isSleeper ? <EmptyState title="Sleeper league required" message="Trade Finder needs your live roster and every live opponent roster." /> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {result && result.candidates.length === 0 ? <EmptyState title="No win-win candidates found" message="NWR's evaluator did not find any 1-for-1 package where both sides' real marginal utility improves right now." /> : null}
    {result && result.candidates.length ? <div className="trade-finder-grid">{result.candidates.map((candidate, index) => <TradeFinderCard key={`${candidate.opponentRosterId}-${candidate.myGivePlayerId}-${index}`} candidate={candidate} />)}</div> : null}
  </>;
}
