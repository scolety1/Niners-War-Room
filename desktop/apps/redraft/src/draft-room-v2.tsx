/**
 * Draft Room V2 -- an ISOLATED candidate (sections 3-6 of the remaining-
 * overnight-runway directive). Reachable at /draft-room-v2, a distinct
 * route from the production Draft Room at "/" (pages.tsx#DraftRoomPage)
 * -- nothing here replaces it automatically.
 *
 * Every real data field used below already exists in the production
 * RedraftBootstrap/DraftBoard payload (board.beatAdpPool, board.recommendations,
 * board.myRoster, externalIntelligence) -- no new backend endpoint was
 * required to build this tab structure. The SHADOW/RESEARCH numeric
 * authorities (Team Score, Championship Equity, Pick Score --
 * src/services/shadow_numeric_authorities_service.py) are NOT wired to
 * any HTTP route or consumed here: those columns render an explicit
 * "not connected" placeholder rather than a fabricated number, per this
 * session's own isolation rule (SHADOW never appears production-
 * authoritative) and the section 3/10 instruction that research labels
 * must stay visible and unvalidated values must never look authoritative.
 */
import type {
  DraftBoard,
  DraftRosterPlayer,
  RedraftBootstrap,
  RedraftExternalIntelligence,
  RedraftExternalIntelligenceEntry,
} from "@nwr/contracts";
import {
  Button,
  DataTable,
  EmptyState,
  PageHeader,
  Panel,
  StatusBadge,
  type TableColumn,
  formatNumber,
} from "@nwr/ui";
import type { NwrApiClient } from "@nwr/api-client";
import { useEffect, useMemo, useState } from "react";

export const DRAFT_ROOM_V2_TABS = ["SUGGESTIONS", "PLAYERS", "BOARD", "MY_TEAM", "COMPARE"] as const;
export type DraftRoomV2Tab = (typeof DRAFT_ROOM_V2_TABS)[number];

export function tabLabel(tab: DraftRoomV2Tab): string {
  return tab === "MY_TEAM" ? "My Team" : tab.charAt(0) + tab.slice(1).toLowerCase();
}

export const RESEARCH_NOT_CONNECTED = "Not connected — SHADOW/RESEARCH backend";
export const COMPARE_MAX_PLAYERS = 4;

// --- Pure data-preparation functions (unit-tested in draft-room-v2.test.ts) --

export interface SuggestionRow {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  nwrRank: number;
  marketExpectedPick: number | null;
  nwrEdge: number | null;
  nwrView: string;
  draftTiming: string;
  makeItBack: string;
  alertSeverity: string | null;
  alertText: string | null;
  // SHADOW/RESEARCH columns -- always this exact placeholder, never a number.
  pickScore: typeof RESEARCH_NOT_CONNECTED;
  teamScoreAfter: typeof RESEARCH_NOT_CONNECTED;
  championshipEquityAfter: typeof RESEARCH_NOT_CONNECTED;
  equityGain: typeof RESEARCH_NOT_CONNECTED;
  waitCost: typeof RESEARCH_NOT_CONNECTED;
}

export function buildSuggestionsRows(
  board: DraftBoard | null | undefined,
  intelById: Map<string, RedraftExternalIntelligenceEntry>,
  limit = 10,
): SuggestionRow[] {
  const pool = board?.beatAdpPool ?? board?.decisionRows ?? [];
  return pool.slice(0, limit).map((row) => {
    const intel = intelById.get(row.playerId);
    return {
      playerId: row.playerId,
      playerName: row.playerName,
      position: row.position,
      team: row.team,
      nwrRank: row.nwrRank,
      marketExpectedPick: row.expectedPick ?? row.overallAdp ?? null,
      nwrEdge: row.nwrEdge ?? null,
      nwrView: row.nwrView,
      draftTiming: row.draftTiming,
      makeItBack: row.makeItBackProbability != null ? formatNumber(row.makeItBackProbability, 2) : row.makeItBackMethod,
      alertSeverity: intel?.currentAlertSeverity ?? null,
      alertText: intel?.currentAlert ?? null,
      pickScore: RESEARCH_NOT_CONNECTED,
      teamScoreAfter: RESEARCH_NOT_CONNECTED,
      championshipEquityAfter: RESEARCH_NOT_CONNECTED,
      equityGain: RESEARCH_NOT_CONNECTED,
      waitCost: RESEARCH_NOT_CONNECTED,
    };
  });
}

export interface MyTeamSummary {
  roster: DraftRosterPlayer[];
  strengths: string[];
  holes: string[];
}

export function buildMyTeamSummary(data: RedraftBootstrap): MyTeamSummary {
  const board = data.draftBoard;
  const roster = board?.myRoster ?? [];
  const req = data.activeProfile?.roster;
  if (!req) return { roster, strengths: [], holes: [] };
  const counts: Record<string, number> = {};
  for (const player of roster) counts[player.position] = (counts[player.position] ?? 0) + 1;
  const strengths: string[] = [];
  const holes: string[] = [];
  for (const [position, need] of [
    ["QB", req.qb], ["RB", req.rb], ["WR", req.wr], ["TE", req.te], ["K", req.k], ["DST", req.dst],
  ] as Array<[string, number]>) {
    if (need <= 0) continue;
    const have = counts[position] ?? 0;
    if (have >= need) strengths.push(`${position} (${have}/${need})`);
    else holes.push(`${position} (${have}/${need})`);
  }
  return { roster, strengths, holes };
}

// StatusBadge's own tone union (packages/ui) -- "safe" plus the shared
// HealthTone set. Reused directly rather than inventing a parallel tone
// vocabulary.
export type BadgeTone = "safe" | "review" | "blocked" | "ready" | "offline";

export interface UdkBadge {
  key: string;
  label: string;
  tone: BadgeTone;
  title?: string;
}

export function severityToBadgeTone(severity: string | null | undefined): BadgeTone {
  const normalized = (severity ?? "").toUpperCase();
  if (normalized === "HIGH") return "blocked";
  if (normalized === "MEDIUM") return "review";
  return "safe";
}

export function buildUdkBadges(entry: RedraftExternalIntelligenceEntry | undefined): UdkBadge[] {
  if (!entry) return [];
  const badges: UdkBadge[] = [];
  if (entry.udkPositionRank) badges.push({ key: "udk-rank", label: `UDK #${entry.udkPositionRank}`, tone: "ready" });
  if (entry.udkTier) badges.push({ key: "udk-tier", label: `Tier ${entry.udkTier}`, tone: "ready" });
  if (entry.currentAlert) {
    badges.push({
      key: "alert",
      label: entry.currentAlertSeverity || "Alert",
      tone: severityToBadgeTone(entry.currentAlertSeverity),
      title: entry.currentAlert,
    });
  }
  return badges;
}

export function toggleCompareSelection(
  current: string[],
  playerId: string,
  max: number = COMPARE_MAX_PLAYERS,
): string[] {
  if (current.includes(playerId)) return current.filter((id) => id !== playerId);
  if (current.length >= max) return current;
  return [...current, playerId];
}

export interface CompareRow {
  playerId: string;
  playerName: string;
  position: string;
  nwrRank: number | null;
  overallAdp: number | null;
  tier: string | null;
  status: string;
}

export function buildCompareRows(
  playerIds: string[],
  data: RedraftBootstrap,
  intelById: Map<string, RedraftExternalIntelligenceEntry>,
): CompareRow[] {
  return playerIds
    .map((playerId) => {
      const ranked = data.rankings.find((row) => row.playerId === playerId);
      const manual = data.manualAssets?.find((row) => row.playerId === playerId);
      const intel = intelById.get(playerId);
      if (!ranked && !manual) return null;
      return {
        playerId,
        playerName: ranked?.playerName ?? manual?.playerName ?? playerId,
        position: ranked?.position ?? manual?.position ?? "?",
        nwrRank: ranked?.overallRank ?? null,
        overallAdp: ranked?.overallAdp ?? manual?.overallAdp ?? null,
        tier: ranked?.overallTierLabel ?? null,
        status: intel?.currentAlert ? `Alert: ${intel.currentAlertSeverity ?? "flagged"}` : "No current alert",
      };
    })
    .filter((row): row is CompareRow => row !== null);
}

/**
 * A real, deterministic, template-based summary from structured fields
 * only -- no invented reasoning, no LLM call. Reports the best NWR rank,
 * the largest ADP discount (NWR rank meaningfully earlier than market),
 * and the position with the most remaining depth among the compared
 * players, using only fields already on CompareRow/the ranking data
 * passed in.
 */
export function generateCompareSummary(rows: CompareRow[], positionDepth: Record<string, number>): string {
  if (rows.length < 2) return "Select at least two players to compare.";
  const ranked = rows.filter((row) => row.nwrRank != null);
  const parts: string[] = [];
  if (ranked.length > 0) {
    const best = ranked.reduce((a, b) => (a.nwrRank! < b.nwrRank! ? a : b));
    parts.push(`${best.playerName} has the best NWR rank (#${best.nwrRank}) in this comparison.`);
  }
  const withAdpGap = rows
    .filter((row) => row.nwrRank != null && row.overallAdp != null)
    .map((row) => ({ row, gap: row.overallAdp! - row.nwrRank! }))
    .filter((entry) => entry.gap > 0);
  if (withAdpGap.length > 0) {
    const biggest = withAdpGap.reduce((a, b) => (a.gap > b.gap ? a : b));
    parts.push(
      `${biggest.row.playerName} offers the largest market discount (NWR #${biggest.row.nwrRank} vs. ADP ${formatNumber(biggest.row.overallAdp!, 1)}, a ${formatNumber(biggest.gap, 1)}-spot gap).`,
    );
  }
  const positions = [...new Set(rows.map((row) => row.position))];
  if (positions.length > 1) {
    const deepest = positions.reduce((a, b) => ((positionDepth[a] ?? 0) >= (positionDepth[b] ?? 0) ? a : b));
    const count = positionDepth[deepest] ?? 0;
    parts.push(`${deepest} is the deepest position among these ${rows.length} players (${count} other ranked ${deepest}s remain).`);
  }
  return parts.join(" ") || "No structured comparison signal available for this selection.";
}

// --- Component -------------------------------------------------------------

export function DraftRoomV2Page({
  client,
  data,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
}) {
  const [tab, setTab] = useState<DraftRoomV2Tab>("SUGGESTIONS");
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [drawerPlayerId, setDrawerPlayerId] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [externalIntel, setExternalIntel] = useState<RedraftExternalIntelligence | null>(null);
  const board = data.draftBoard;

  useEffect(() => {
    if (!data.activeProfileId) return;
    let cancelled = false;
    client
      .getRedraftExternalIntelligence(data.activeProfileId)
      .then((response) => {
        if (!cancelled) setExternalIntel(response.externalIntelligence);
      })
      .catch(() => {
        if (!cancelled) setExternalIntel({ available: false, generatedNote: "EXTERNAL INTEL UNAVAILABLE", entries: [] });
      });
    return () => {
      cancelled = true;
    };
  }, [client, data.activeProfileId]);

  const intelById = useMemo(() => {
    const map = new Map<string, RedraftExternalIntelligenceEntry>();
    for (const entry of externalIntel?.entries ?? []) map.set(entry.playerId, entry);
    return map;
  }, [externalIntel]);

  const positionDepth = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const row of data.rankings) {
      if (row.drafted) continue;
      counts[row.position] = (counts[row.position] ?? 0) + 1;
    }
    return counts;
  }, [data.rankings]);

  const suggestions = useMemo(() => buildSuggestionsRows(board, intelById), [board, intelById]);
  const myTeam = useMemo(() => buildMyTeamSummary(data), [data]);
  const compareRows = useMemo(() => buildCompareRows(compareIds, data, intelById), [compareIds, data, intelById]);
  const compareSummary = useMemo(() => generateCompareSummary(compareRows, positionDepth), [compareRows, positionDepth]);

  const onPlayerClick = (playerId: string, event: React.MouseEvent) => {
    if (event.altKey) {
      setCompareIds((current) => toggleCompareSelection(current, playerId));
      return;
    }
    setDrawerPlayerId(playerId);
  };

  if (!data.activeProfile) {
    return (
      <EmptyState
        icon="profile"
        title="No active league profile"
        message="Draft Room V2 needs an active Redraft profile -- set one up from the standard Draft Room first."
      />
    );
  }

  const drawerEntry = drawerPlayerId ? intelById.get(drawerPlayerId) : undefined;
  const drawerRanking = drawerPlayerId ? data.rankings.find((row) => row.playerId === drawerPlayerId) : undefined;

  return (
    <div className="draft-room-v2-page">
      <PageHeader
        eyebrow="Isolated preview — does not affect the production Draft Room"
        title={`${data.activeProfile.leagueName} — Draft Room V2`}
        description="Tabbed information architecture: Suggestions / Players / Board / My Team / Compare. Alt+click any player to add them to Compare."
        actions={
          <Button variant="ghost" onClick={() => setSidebarVisible((value) => !value)}>
            {sidebarVisible ? "Hide sidebar" : "Show sidebar"}
          </Button>
        }
      />
      <div className="draft-room-v2-layout">
        {sidebarVisible ? (
          <nav className="draft-room-v2-sidebar" aria-label="Draft Room V2 tabs">
            {DRAFT_ROOM_V2_TABS.map((value) => (
              <button
                key={value}
                type="button"
                aria-pressed={tab === value}
                className={tab === value ? "draft-room-v2-tab draft-room-v2-tab--active" : "draft-room-v2-tab"}
                onClick={() => setTab(value)}
              >
                {tabLabel(value)}
              </button>
            ))}
          </nav>
        ) : null}
        <div className="draft-room-v2-content">
          {tab === "SUGGESTIONS" ? <SuggestionsTab rows={suggestions} onPlayerClick={onPlayerClick} /> : null}
          {tab === "PLAYERS" ? (
            <PlayersTab data={data} intelById={intelById} onPlayerClick={onPlayerClick} />
          ) : null}
          {tab === "BOARD" ? <BoardTab board={board} onPlayerClick={onPlayerClick} /> : null}
          {tab === "MY_TEAM" ? <MyTeamTab summary={myTeam} /> : null}
          {tab === "COMPARE" ? (
            <CompareTab
              rows={compareRows}
              summary={compareSummary}
              onRemove={(playerId) => setCompareIds((current) => current.filter((id) => id !== playerId))}
            />
          ) : null}
        </div>
      </div>
      {compareIds.length > 0 && tab !== "COMPARE" ? (
        <div className="draft-room-v2-compare-tray" role="status">
          <span>{compareIds.length} selected for Compare</span>
          <Button variant="secondary" onClick={() => setTab("COMPARE")}>
            Open Compare
          </Button>
        </div>
      ) : null}
      {drawerPlayerId ? (
        <PlayerDrawer
          playerId={drawerPlayerId}
          ranking={drawerRanking}
          intel={drawerEntry}
          onClose={() => setDrawerPlayerId(null)}
        />
      ) : null}
    </div>
  );
}

function SuggestionsTab({
  rows,
  onPlayerClick,
}: {
  rows: SuggestionRow[];
  onPlayerClick: (playerId: string, event: React.MouseEvent) => void;
}) {
  const columns: TableColumn[] = [
    { key: "playerName", label: "Player", sort: "text", render: (row) => (
      <span
        className="player-cell player-cell--clickable"
        onClick={(event) => onPlayerClick(String(row.playerId), event as unknown as React.MouseEvent)}
      >
        <strong>{String(row.playerName)}</strong>
        <small>{String(row.team)} · {String(row.position)}</small>
      </span>
    ) },
    { key: "nwrRank", label: "NWR", sort: "number" },
    { key: "marketExpectedPick", label: "Market", sort: "number", render: (row) => row.marketExpectedPick == null ? "—" : formatNumber(row.marketExpectedPick as number, 1) },
    { key: "nwrEdge", label: "Edge", sort: "number", render: (row) => row.nwrEdge == null ? "—" : formatNumber(row.nwrEdge as number, 1) },
    { key: "pickScore", label: "Pick Score — EXPERIMENTAL", sort: "text" },
    { key: "teamScoreAfter", label: "Team Score After — RESEARCH", sort: "text" },
    { key: "championshipEquityAfter", label: "Champ Eq After — SIMULATED RESEARCH", sort: "text" },
    { key: "waitCost", label: "Wait Cost", sort: "text" },
    { key: "alertText", label: "Alert", sort: "text", render: (row) => row.alertText ? <span title={String(row.alertText)}><StatusBadge tone={severityToBadgeTone(row.alertSeverity as string | null)} label={String(row.alertSeverity ?? "Alert")} /></span> : "—" },
  ];
  return (
    <Panel title="Suggestions" eyebrow="Primary decision surface — top candidates by market-timed NWR view">
      {rows.length === 0 ? (
        <EmptyState icon="activity" title="No suggestions yet" message="Start the Draft Room and refresh ADP to populate this table." />
      ) : (
        <DataTable columns={columns} rows={rows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.playerId)} />
      )}
    </Panel>
  );
}

function PlayersTab({
  data,
  intelById,
  onPlayerClick,
}: {
  data: RedraftBootstrap;
  intelById: Map<string, RedraftExternalIntelligenceEntry>;
  onPlayerClick: (playerId: string, event: React.MouseEvent) => void;
}) {
  const rows = data.rankings.filter((row) => !row.drafted);
  const columns: TableColumn[] = [
    { key: "overallRank", label: "NWR", sort: "number" },
    { key: "playerName", label: "Player", sort: "text", render: (row) => (
      <span
        className="player-cell player-cell--clickable"
        onClick={(event) => onPlayerClick(String(row.playerId), event as unknown as React.MouseEvent)}
      >
        <strong>{String(row.playerName)}</strong>
        <small>{String(row.team)} · {String(row.position)}</small>
      </span>
    ) },
    { key: "overallAdp", label: "ADP", sort: "number", render: (row) => row.overallAdp == null ? "—" : formatNumber(row.overallAdp as number, 1) },
    { key: "badges", label: "UDK", sort: "text", render: (row) => (
      <span className="udk-badge-row">
        {buildUdkBadges(intelById.get(String(row.playerId))).map((badge) => (
          <span key={badge.key} title={badge.title}><StatusBadge tone={badge.tone} label={badge.label} /></span>
        ))}
      </span>
    ) },
  ];
  return (
    <Panel title="Players" eyebrow={`${rows.length} undrafted players`}>
      <DataTable columns={columns} rows={rows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.playerId)} />
    </Panel>
  );
}

function BoardTab({
  board,
  onPlayerClick,
}: {
  board: DraftBoard | null | undefined;
  onPlayerClick: (playerId: string, event: React.MouseEvent) => void;
}) {
  if (!board?.boardCells) {
    return <EmptyState icon="activity" title="No draft board yet" message="Start the Draft Room from the standard Draft Room page first." />;
  }
  return (
    <Panel title="Draft Board" eyebrow={`${board.boardCells.length} slots`}>
      <div className="draft-board-v2-grid">
        {board.boardCells.map((cell) => (
          <article
            key={cell.pickNumber}
            className={`draft-board-v2-cell ${cell.ownerPick ? "draft-board-v2-cell--owner" : ""} ${cell.current ? "draft-board-v2-cell--current" : ""}`}
            onClick={cell.playerId ? (event) => onPlayerClick(cell.playerId, event) : undefined}
          >
            <span className="draft-board-v2-cell__pick">#{cell.pickNumber}</span>
            <span className="draft-board-v2-cell__player">{cell.playerName || (cell.status === "UNRESOLVED" ? "Unresolved" : "Open")}</span>
          </article>
        ))}
      </div>
    </Panel>
  );
}

function MyTeamTab({ summary }: { summary: MyTeamSummary }) {
  return (
    <>
      <Panel title="My roster" eyebrow={`${summary.roster.length} players`}>
        <DataTable
          columns={[
            { key: "pickNumber", label: "Pick", sort: "number" },
            { key: "playerName", label: "Player", sort: "text" },
            { key: "position", label: "Pos", sort: "text" },
            { key: "team", label: "Team", sort: "text" },
          ]}
          rows={summary.roster as unknown as Array<Record<string, unknown>>}
          rowKey={(row) => String(row.playerId)}
        />
      </Panel>
      <Panel title="Strengths & holes" eyebrow="Filled vs. open roster slots">
        <div className="roster-strip">
          {summary.strengths.map((label) => (
            <span key={label} className="roster-slot roster-slot--full">{label}</span>
          ))}
          {summary.holes.map((label) => (
            <span key={label} className="roster-slot">{label}</span>
          ))}
        </div>
      </Panel>
      <Panel title="Team Score — RESEARCH" eyebrow="Not connected to this UI yet">
        <p className="boundary-note">{RESEARCH_NOT_CONNECTED}. See src/services/shadow_numeric_authorities_service.py.</p>
      </Panel>
      <Panel title="Simulated Championship Equity — RESEARCH" eyebrow="Not connected to this UI yet">
        <p className="boundary-note">{RESEARCH_NOT_CONNECTED}.</p>
      </Panel>
    </>
  );
}

function CompareTab({
  rows,
  summary,
  onRemove,
}: {
  rows: CompareRow[];
  summary: string;
  onRemove: (playerId: string) => void;
}) {
  if (rows.length === 0) {
    return <EmptyState icon="activity" title="Nothing selected" message="Alt+click a player anywhere in Draft Room V2 to add them here." />;
  }
  return (
    <>
      <Panel title="Compare" eyebrow={`${rows.length} of ${COMPARE_MAX_PLAYERS} players`}>
        <DataTable
          columns={[
            { key: "playerName", label: "Player", sort: "text" },
            { key: "position", label: "Pos", sort: "text" },
            { key: "nwrRank", label: "NWR", sort: "number", render: (row) => row.nwrRank == null ? "—" : String(row.nwrRank) },
            { key: "overallAdp", label: "Market", sort: "number", render: (row) => row.overallAdp == null ? "—" : formatNumber(row.overallAdp as number, 1) },
            { key: "tier", label: "Tier", sort: "text", render: (row) => String(row.tier ?? "—") },
            { key: "status", label: "Status", sort: "text" },
            { key: "action", label: "", align: "right", render: (row) => <Button variant="ghost" onClick={() => onRemove(String(row.playerId))}>Remove</Button> },
          ]}
          rows={rows as unknown as Array<Record<string, unknown>>}
          rowKey={(row) => String(row.playerId)}
        />
      </Panel>
      <Panel title="AI Compare Summary" eyebrow="Structured fields only — no invented reasoning">
        <p>{summary}</p>
      </Panel>
    </>
  );
}

function PlayerDrawer({
  playerId,
  ranking,
  intel,
  onClose,
}: {
  playerId: string;
  ranking: RedraftBootstrap["rankings"][number] | undefined;
  intel: RedraftExternalIntelligenceEntry | undefined;
  onClose: () => void;
}) {
  return (
    <aside className="player-drawer" role="dialog" aria-label={`${ranking?.playerName ?? playerId} detail`}>
      <div className="player-drawer__header">
        <strong>{ranking?.playerName ?? playerId}</strong>
        <Button variant="ghost" onClick={onClose}>Close</Button>
      </div>
      <section>
        <h3>NWR</h3>
        <p>Rank #{ranking?.overallRank ?? "—"} · {ranking?.overallTierLabel ?? "—"}</p>
        <p>Player Score (replacement-adjusted value): {ranking ? formatNumber(ranking.replacementAdjustedValue, 1) : "—"}</p>
      </section>
      <section>
        <h3>Draft</h3>
        <p>Market ADP: {ranking?.overallAdp != null ? formatNumber(ranking.overallAdp, 1) : "—"}</p>
        <p>Expected round: {ranking?.expectedRound ?? "—"}</p>
      </section>
      <section>
        <h3>SHADOW</h3>
        <p className="boundary-note">{RESEARCH_NOT_CONNECTED}.</p>
      </section>
      <section>
        <h3>Current</h3>
        {intel?.currentAlert ? (
          <p><StatusBadge tone={severityToBadgeTone(intel.currentAlertSeverity)} label={intel.currentAlertSeverity ?? "Alert"} /> {intel.currentAlert}</p>
        ) : (
          <p>No current alert on file.</p>
        )}
        {intel?.udkPositionRank ? <p>UDK position rank: {intel.udkPositionRank} (tier {intel.udkTier ?? "—"})</p> : null}
        {intel?.fantasyProsEcr ? <p>FantasyPros ECR: {intel.fantasyProsEcr}</p> : null}
      </section>
    </aside>
  );
}
