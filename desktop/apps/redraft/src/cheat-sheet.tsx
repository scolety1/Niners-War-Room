import type { ManualDraftAsset, RedraftBootstrap, RedraftRanking, UdkPlayerEntry } from "@nwr/contracts";
import { Button, DataTable, EmptyState, PageHeader, Panel, SegmentedControl, StatusBadge, type TableColumn, formatNumber } from "@nwr/ui";
import { useMemo, useState } from "react";
import { formatAdpRoundPick } from "./adp-format";
import { buildUdkEntryById } from "./ballers-shared";

// Owner feedback closure, section 8/9: positional lanes now include K/DST
// (previously Overall/QB/RB/WR/TE/Tiers only -- K/DST are real, legal,
// draftable positions the owner asked to keep findable and draftable
// everywhere). K/DST are NOT part of NWR's scored `rankings` (they are
// separately-sourced manual assets, unmodeled by NWR) -- shown here from
// the exact same `manualAssets` list Suggestions' position filter and
// search already use, never a fabricated advanced score.
// NWR FINAL OWNER-FEEDBACK CLOSURE (section A, "FLEX = actual RB/WR/TE
// eligibility... Superflex only where configured"): FLEX and Superflex
// lanes were entirely absent from Cheat Sheets (present on Suggestions,
// missing here) -- added using the same real position-eligibility rule
// Suggestions already uses, never a new/different definition.
const BASE_SHEETS = ["Overall", "QB", "RB", "WR", "TE", "FLEX", "K", "DST", "Tiers"];
const FLEX_ELIGIBLE = new Set(["RB", "WR", "TE"]);
const SUPERFLEX_ELIGIBLE = new Set(["QB", "RB", "WR", "TE"]);
const MANUAL_POSITIONS = new Set(["K", "DST"]);

function csvCell(value: unknown): string {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function buildCheatSheetCsv(data: RedraftBootstrap, rows: RedraftRanking[]): string {
  const profile = data.activeProfile;
  if (!profile) return "";
  const headers = ["League Profile", "Season", "Teams", "Scoring", "Rank", "Pos Rank", "Player", "Team", "Position", "Tier", "Projected Points", "Replacement Value", "Confidence", "Rookie", "Source As Of"];
  const scoring = `${profile.scoring.reception} PPR; ${profile.scoring.tePremium} TE premium`;
  const records = rows.map((row) => [profile.leagueName, profile.season, profile.teamCount, scoring, row.overallRank, `${row.position}${row.positionRank}`, row.playerName, row.team, row.position, row.tier, row.projectedPoints, row.replacementAdjustedValue, row.confidence, row.rookie ? "Yes" : "No", row.sourceAsOf]);
  return [headers, ...records].map((record) => record.map(csvCell).join(",")).join("\r\n") + "\r\n";
}

// NWR PRE-DRAFT MARKET DATA / ADP UX CLEANUP (2026-09-08, directive section
// 11): a compact, real, read-only status line -- Cheat Sheets consumes the
// active global Ballers/market data, it never manages the source.
export function ballersStatusText(data: RedraftBootstrap): string {
  const positions = data.udkRankings?.positions ?? [];
  if (positions.length === 0) return "Ballers: not imported";
  const rows = positions.reduce((sum, position) => sum + position.entries.length, 0);
  const latest = positions.reduce((latestTime, position) => position.importedAtUtc > latestTime ? position.importedAtUtc : latestTime, "");
  const date = latest ? new Date(latest).toLocaleDateString() : "—";
  return `Ballers: ${date} · ${rows} rows`;
}

export function marketStatusText(data: RedraftBootstrap): string {
  const adp = data.draftBoard?.adp;
  if (!adp?.available) return "Market: unavailable";
  const provider = data.ownerPlatformSnapshot?.activeColumn || adp.source.replace(/^Owner-imported /i, "").replace(/ ADP.*$/i, "");
  const date = adp.sourceDate ? new Date(adp.sourceDate).toLocaleDateString() : adp.dateWindow || "—";
  return `Market: ${provider} · ${date}`;
}

// NWR CHEAT SHEET -- COMBINED NWR + MARKET + BALLERS VIEW (2026-09-08,
// directive sections 4-6): the Combined table's compact "Ballers Rank" /
// "Ballers Tier" cells stay narrow on purpose (section 9, "the owner
// should not have to scroll sideways") -- every OTHER real field the
// active Ballers row actually carries (its own Ballers ADP, distinct from
// active-league Market ADP; Risk/Upside already have dedicated columns so
// are omitted here to avoid repeating them; projected points; bye week;
// outlook) goes into this hover tooltip instead of a wider table, and the
// full detail is always one click away in the Player Drawer's own
// "Ballers" section. Never invents a field the source file didn't have.
function ballersDetailTitle(entry: UdkPlayerEntry | undefined): string {
  if (!entry) return "No Ballers/Fantasy Footballers row for this player in the imported file.";
  return [
    entry.adpRaw ? `Ballers ADP ${entry.adpRaw}` : null,
    entry.points != null ? `Proj ${formatNumber(entry.points, 1)}` : null,
    entry.byeWeek ? `Bye ${entry.byeWeek}` : null,
    entry.dynastyLocked ? "Dynasty: locked (UDK+ upsell)" : null,
    entry.outlook ? `Outlook: ${entry.outlook}` : null,
  ].filter(Boolean).join(" · ") || "Ballers/Fantasy Footballers data";
}

export function CheatSheetPage({
  data,
  // Optional, defaulted: the standalone "#/cheat-sheet" browse/export
  // route (RedraftApp.tsx) has no live draft-turn context to record a
  // pick against. Draft Room V2's embedded Cheat Sheets tab passes the
  // real values so Draft/Queue genuinely work there (owner feedback
  // section 9: "positional Cheat Sheets support Draft/Queue/Details").
  canRecordPick = false,
  working = "",
  queuedIds = [],
  onDraft = () => {},
  onQueue = () => {},
  onPlayerClick = () => {},
}: {
  data: RedraftBootstrap;
  canRecordPick?: boolean;
  working?: string;
  queuedIds?: string[];
  onDraft?: (playerId: string) => void;
  onQueue?: (playerId: string) => void;
  onPlayerClick?: (playerId: string, event: React.MouseEvent) => void;
}) {
  const [sheet, setSheet] = useState("Overall");
  // NWR CHEAT SHEET -- COMBINED NWR + MARKET + BALLERS VIEW (2026-09-08,
  // directive section 1): Combined is now the default -- NWR rank, the
  // active league's own routed market ADP, and the owner's imported
  // Ballers/UDK data side by side in one row, so the owner never has to
  // switch tabs mid-draft just to compare sources. "Ballers" (previously
  // "UDK") only ever offers data for a position the owner has actually
  // imported real Ballers rows for -- never fabricated from nothing.
  const [source, setSource] = useState<"COMBINED" | "NWR" | "BALLERS">("COMBINED");
  // Owner feedback closure, section 8: drafted players disappear
  // immediately by default from every lane here too (Cheat Sheets was a
  // real, disclosed gap -- previously showed every player regardless of
  // draft state). Uses the canonical player-ID drafted list
  // (board.drafted), never a display-name comparison; a "Show Drafted"
  // toggle stays available for the owner to review history.
  const [showDrafted, setShowDrafted] = useState(false);
  const draftedIds = useMemo(() => new Set(data.draftBoard?.drafted ?? []), [data.draftBoard?.drafted]);
  const udkForSheet = data.udkRankings?.positions?.find((row) => row.position === sheet);
  const manualRows = useMemo(
    () => (data.manualAssets ?? []).filter((row) => row.position === sheet && (showDrafted || !draftedIds.has(row.playerId))),
    [data.manualAssets, sheet, showDrafted, draftedIds],
  );
  const rows = useMemo(
    () => (sheet === "Overall" || sheet === "Tiers" || MANUAL_POSITIONS.has(sheet)
      ? data.rankings
      : sheet === "FLEX"
        ? data.rankings.filter((row) => FLEX_ELIGIBLE.has(row.position))
        : sheet === "SFLX"
          ? data.rankings.filter((row) => SUPERFLEX_ELIGIBLE.has(row.position))
          : data.rankings.filter((row) => row.position === sheet)
    ).filter((row) => showDrafted || !row.drafted),
    [data.rankings, sheet, showDrafted],
  );
  // Superflex lane only where the active league is actually configured
  // for it -- never shown for a 1QB league (matches the exact real
  // Suggestions position-filter behavior, not a separate new rule).
  const SHEETS = (data.activeProfile?.roster.superflex ?? 0) > 0
    ? [...BASE_SHEETS.slice(0, 6), "SFLX", ...BASE_SHEETS.slice(6)]
    : BASE_SHEETS;
  const udkVisibleEntries = useMemo(
    () => (udkForSheet?.entries ?? []).filter((row) => showDrafted || !row.playerId || !draftedIds.has(row.playerId)),
    [udkForSheet, showDrafted, draftedIds],
  );
  if (!data.activeProfile) return <><PageHeader eyebrow="Draft prep · Current season" title="Cheat Sheet" description="Activate a league profile to build its printable current-season board." /><EmptyState icon="profile" title="No active league profile" message="Cheat sheets are profile-specific and stay inside Redraft." action={<Button onClick={() => { window.location.hash = "#/profile"; }}>Open profile manager</Button>} /></>;
  const exportCsv = () => {
    const blob = new Blob([buildCheatSheetCsv(data, rows)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeName = data.activeProfile!.leagueName.replace(/[^A-Za-z0-9._-]+/g, "_").replace(/^[._]+|[._]+$/g, "") || "redraft";
    link.href = url; link.download = `${safeName}_${data.activeProfile!.season}_${sheet}.csv`; document.body.append(link); link.click(); link.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 0);
  };
  const draftActionColumn: TableColumn = {
    key: "cheatSheetActions", label: "", align: "right",
    render: (row) => {
      const playerId = String(row.playerId ?? "");
      if (!playerId) {
        // UDK-specific: a real source row the importer could not safely
        // match to a canonical NWR player ID (e.g. not in NWR's admitted
        // ranking pool at all) -- preserved and shown with the exact
        // reason, never silently dropped and never force-matched.
        if (row.matchStatus === "UNMATCHED") {
          return (
            <span title="This UDK row could not be safely matched to a real NWR-ranked player (not present in NWR's admitted current-season ranking pool) -- shown for reference only, not draftable from here.">
              <StatusBadge tone="review" label="Not in NWR pool" />
            </span>
          );
        }
        return null;
      }
      const isDrafted = draftedIds.has(playerId) || Boolean(row.drafted);
      if (isDrafted) return <StatusBadge tone="review" label="Drafted" />;
      const isQueued = queuedIds.includes(playerId);
      return (
        <span className="draft-room-v2-pick-actions">
          <Button data-draft-action disabled={!canRecordPick || Boolean(working)} variant="primary" onClick={() => onDraft(playerId)}>
            {working === playerId ? "Saving…" : "Draft"}
          </Button>
          <Button variant="ghost" onClick={() => onQueue(playerId)}>{isQueued ? "Queued" : "Queue"}</Button>
        </span>
      );
    },
  };
  const isManual = MANUAL_POSITIONS.has(sheet);
  const visible = isManual ? [] : sheet === "Tiers" ? rows.slice().sort((left, right) => left.tier - right.tier || left.overallRank - right.overallRank) : rows;
  // NWR CHEAT SHEET -- COMBINED NWR + MARKET + BALLERS VIEW (2026-09-08):
  // the ONE shared Ballers/UDK lookup, same real source and values every
  // other surface (Suggestions' "Show Ballers" column, the Player Drawer)
  // already resolves through -- never a second, divergently-built map.
  const udkById = useMemo(() => buildUdkEntryById(data.udkRankings), [data.udkRankings]);
  // The ADP source's OWN team count (may differ from the room's) -- the
  // exact guard formatAdpRoundPick already uses everywhere else, so a
  // different-sized source's pick numbers are never silently reinterpreted
  // as this league's own rounds.
  const adpTeamCount = data.draftBoard?.adp?.teamCount ?? null;
  const roomTeamCount = data.activeProfile.teamCount ?? null;
  return (
    <>
      <PageHeader
        eyebrow="Draft prep · Profile specific"
        title="Cheat Sheet"
        description="A printable and exportable board built from the active league's governed current-season rankings."
        status={<><StatusBadge tone="safe" label={data.activeProfile.leagueName} /><StatusBadge tone="safe" label={`${isManual ? manualRows.length : udkForSheet && source === "BALLERS" ? udkVisibleEntries.length : visible.length} players`} /></>}
        actions={<Button icon="board" onClick={exportCsv}>Export NWR Cheat Sheet CSV</Button>}
      />
      {/* NWR PRE-DRAFT MARKET DATA / ADP UX CLEANUP (2026-09-08): Cheat
          Sheets consumes active data, it does not manage the source --
          Import UDK CSV/rollback moved to Market Data / ADP (single
          control-center, directive section 2). This status line links
          there instead of duplicating any import control here. */}
      <p className="boundary-note">
        {ballersStatusText(data)} · {marketStatusText(data)} ·{" "}
        <a href="#/adp">Manage in Market Data / ADP</a>
      </p>
      <Panel title={`${data.activeProfile.leagueName} · ${data.activeProfile.season}`} eyebrow={`${data.activeProfile.teamCount} teams · ${data.activeProfile.scoring.reception} PPR · ${data.activeProfile.scoring.tePremium} TE premium`}>
        <div className="toolbar">
          <SegmentedControl label="Sheet" options={SHEETS} value={sheet} onChange={(value) => { setSheet(value); setSource("COMBINED"); }} />
          {/* NWR CHEAT SHEET -- COMBINED NWR + MARKET + BALLERS VIEW
              (2026-09-08, directive section 1): Combined is the default
              side-by-side reference; NWR/Ballers stay available as focused
              single-source modes. Hidden for K/DST -- NWR has no score for
              those positions (unmodeled), so there is only one honest table
              for them (below), not three source variants of the same data. */}
          {!isManual ? (
            <SegmentedControl
              label="Source"
              options={udkForSheet ? ["COMBINED", "NWR", "BALLERS"] : ["COMBINED", "NWR"]}
              value={source}
              onChange={(value) => setSource(value as "COMBINED" | "NWR" | "BALLERS")}
            />
          ) : null}
          <label className="toolbar__toggle">
            <input type="checkbox" checked={showDrafted} onChange={(event) => setShowDrafted(event.target.checked)} />
            Show Drafted
          </label>
        </div>
        {isManual ? (
          <>
            {/* NWR CHEAT SHEET -- COMBINED NWR + MARKET + BALLERS VIEW
                (2026-09-08, directive section 7): K/DST are real, legal,
                draftable positions NWR does not score (unmodeled, not a
                bug) -- an honest layout leads with the real Ballers
                reference ranking when the owner's imported file covers it,
                names the active source plainly, and never fabricates an
                NWR Player Score for these rows. */}
            <p className="boundary-note">
              NWR does not score K/DST — never blended into NWR rank/score. Ballers/Fantasy Footballers
              rankings are shown as the reference when the owner's imported file covers this position;
              otherwise these are manual, unranked reference rows.
            </p>
            <DataTable
              columns={[
                {
                  key: "ballersRank", label: "Ballers Rank", sort: "number", width: "96px",
                  sortValue: (row) => udkById.get(String(row.playerId))?.rank ?? null,
                  render: (row) => {
                    const entry = udkById.get(String(row.playerId));
                    return <span title={ballersDetailTitle(entry)}>{entry?.rank ?? "—"}</span>;
                  },
                },
                { key: "playerName", label: "Team / Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span> },
                {
                  key: "activeSource", label: "Active Source",
                  render: (row) => udkById.get(String(row.playerId))
                    ? <StatusBadge tone="safe" label="Ballers rankings" />
                    : <StatusBadge tone="review" label="Manual · not modeled by NWR" />,
                },
                {
                  key: "overallAdp", label: "ADP", sort: "number",
                  render: (row) => {
                    const adp = formatAdpRoundPick(row.overallAdp as number | null, adpTeamCount, roomTeamCount);
                    return <span title={adp.title}>{adp.text}</span>;
                  },
                },
                draftActionColumn,
              ]}
              rows={manualRows.map((row: ManualDraftAsset) => ({ ...row }))}
              rowKey={(row) => String(row.playerId)}
            />
          </>
        ) : udkForSheet && source === "BALLERS" ? (
          <>
            <p className="boundary-note">
              {udkForSheet.provider} · imported {udkForSheet.importedAtUtc} · {udkForSheet.sourceRows} rows.
              Ballers' own position rank/tier — NOT NWR's overall rank, and its Risk/Upside/ADP are provider
              context, not NWR calibrated confidence. ADP is shown exactly as Ballers printed it (source team
              count unknown) — never reinterpreted as this league's own round.pick.
              {" "}Rollback moved to <a href="#/adp">Market Data / ADP</a>.
            </p>
            <DataTable
              columns={[
                { key: "rank", label: "Ballers Rank", sort: "number", width: "72px" },
                { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · Bye {String((row as unknown as UdkPlayerEntry).byeWeek || "—")}</small></span> },
                { key: "tier", label: "Tier", sort: "number", render: (row) => row.tier == null ? "—" : String(row.tier) },
                { key: "adpRaw", label: "Ballers ADP", sort: "text", render: (row) => (row.adpRaw as string) || "—" },
                { key: "points", label: "Proj pts", align: "right", sort: "number", render: (row) => row.points == null ? "—" : formatNumber(row.points as number, 1) },
                { key: "riskUpside", label: "Ballers Risk / Upside", align: "right", render: (row) => `${row.risk == null ? "—" : formatNumber(row.risk as number, 1)} / ${row.upside == null ? "—" : formatNumber(row.upside as number, 1)}` },
                { key: "outlook", label: "Outlook", render: (row) => <span title={String(row.outlook || "")}>{String(row.outlook || "").slice(0, 80)}{String(row.outlook || "").length > 80 ? "…" : ""}</span> },
                draftActionColumn,
              ]}
              rows={udkVisibleEntries.map((row) => ({ ...row, playerId: row.playerId ?? "" }))}
              rowKey={(row) => String(row.playerId || `unmatched-${String(row.playerName)}-${String(row.rank)}`)}
            />
          </>
        ) : source === "COMBINED" ? (
          <>
            {/* NWR CHEAT SHEET -- COMBINED NWR + MARKET + BALLERS VIEW
                (2026-09-08, directive sections 2/9): the owner's requested
                default -- NWR rank, this league's own routed market ADP
                (the exact same `overallAdp` field Suggestions/Compare/the
                Player Drawer already read, never a second computation),
                and the owner's imported Ballers row side by side. Kept to
                8 visible columns at normal desktop width per the owner's
                own "no horizontal hunting" instruction; NWR Tier rides
                inline in the Player cell, and every other real Ballers
                field (its own ADP, projected points, bye, outlook) is one
                hover or one Player Drawer click away -- never invented
                when the source file doesn't have it. */}
            <p className="boundary-note">
              Ballers Risk/Upside and Ballers ADP are the Fantasy Footballers Podcast UDK's own values —
              provider context, not NWR calibrated confidence, and never blended into NWR rank/score.
            </p>
            <DataTable
              columns={[
                {
                  key: "overallRank", label: "NWR Rank", width: "64px", sort: "number",
                  render: (row) => (
                    <span title={`Proj ${formatNumber(row.projectedPoints as number, 1)} pts · Value over replacement ${formatNumber(row.replacementAdjustedValue as number, 1)} · Confidence ${String(row.confidence)}`}>
                      {String(row.overallRank)}
                    </span>
                  ),
                },
                {
                  key: "playerName", label: "Player", sort: "text",
                  render: (row) => (
                    <span
                      className="player-cell player-cell--clickable"
                      onClick={(event) => onPlayerClick(String(row.playerId), event as unknown as React.MouseEvent)}
                    >
                      <strong>{String(row.playerName)}</strong>
                      <small>{String(row.team)} · {String(row.position)}{String(row.positionRank)} · Tier {String(row.tier)}</small>
                    </span>
                  ),
                },
                {
                  key: "overallAdp", label: "Market ADP", sort: "number",
                  render: (row) => {
                    const adp = formatAdpRoundPick(row.overallAdp as number | null, adpTeamCount, roomTeamCount);
                    return <span title={adp.title}>{adp.text}</span>;
                  },
                },
                {
                  key: "ballersRank", label: "Ballers Rank", sort: "number",
                  sortValue: (row) => udkById.get(String(row.playerId))?.rank ?? null,
                  render: (row) => {
                    const entry = udkById.get(String(row.playerId));
                    return <span title={ballersDetailTitle(entry)}>{entry?.rank ?? "—"}</span>;
                  },
                },
                {
                  key: "ballersTier", label: "Ballers Tier", sort: "number",
                  sortValue: (row) => udkById.get(String(row.playerId))?.tier ?? null,
                  render: (row) => {
                    const entry = udkById.get(String(row.playerId));
                    return <span title={ballersDetailTitle(entry)}>{entry?.tier ?? "—"}</span>;
                  },
                },
                {
                  key: "ballersRisk", label: "Ballers Risk", align: "right", sort: "number",
                  sortValue: (row) => udkById.get(String(row.playerId))?.risk ?? null,
                  render: (row) => {
                    const entry = udkById.get(String(row.playerId));
                    return entry?.risk == null ? "—" : formatNumber(entry.risk, 1);
                  },
                },
                {
                  key: "ballersUpside", label: "Ballers Upside", align: "right", sort: "number",
                  sortValue: (row) => udkById.get(String(row.playerId))?.upside ?? null,
                  render: (row) => {
                    const entry = udkById.get(String(row.playerId));
                    return entry?.upside == null ? "—" : formatNumber(entry.upside, 1);
                  },
                },
                draftActionColumn,
              ]}
              rows={visible.map((row) => ({ ...row }))}
              rowKey={(row) => String(row.playerId)}
            />
          </>
        ) : (
          <DataTable
            columns={[
              { key: "overallRank", label: "Rank", width: "64px" },
              {
                key: "playerName", label: "Player",
                render: (row) => (
                  <span
                    className="player-cell player-cell--clickable"
                    onClick={(event) => onPlayerClick(String(row.playerId), event as unknown as React.MouseEvent)}
                  >
                    <strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}{String(row.positionRank)}</small>
                  </span>
                ),
              },
              { key: "position", label: "Pos", align: "center" },
              { key: "tier", label: "Tier" },
              { key: "projectedPoints", label: "Proj pts", align: "right", render: (row) => formatNumber(row.projectedPoints as number, 1) },
              { key: "replacementAdjustedValue", label: "Value over replacement", align: "right", render: (row) => formatNumber(row.replacementAdjustedValue as number, 1) },
              { key: "confidence", label: "Confidence" },
              draftActionColumn,
            ]}
            rows={visible.map((row) => ({ ...row }))}
            rowKey={(row) => String(row.playerId)}
          />
        )}
      </Panel>
    </>
  );
}
