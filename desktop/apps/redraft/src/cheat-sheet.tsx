import type { ManualDraftAsset, RedraftBootstrap, RedraftRanking, UdkPlayerEntry } from "@nwr/contracts";
import { Button, DataTable, EmptyState, PageHeader, Panel, SegmentedControl, StatusBadge, type TableColumn, formatNumber } from "@nwr/ui";
import { useMemo, useState } from "react";

// Owner feedback closure, section 8/9: positional lanes now include K/DST
// (previously Overall/QB/RB/WR/TE/Tiers only -- K/DST are real, legal,
// draftable positions the owner asked to keep findable and draftable
// everywhere). K/DST are NOT part of NWR's scored `rankings` (they are
// separately-sourced manual assets, unmodeled by NWR) -- shown here from
// the exact same `manualAssets` list Suggestions' position filter and
// search already use, never a fabricated advanced score.
const SHEETS = ["Overall", "QB", "RB", "WR", "TE", "K", "DST", "Tiers"];
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
  onImportUdk,
}: {
  data: RedraftBootstrap;
  canRecordPick?: boolean;
  working?: string;
  queuedIds?: string[];
  onDraft?: (playerId: string) => void;
  onQueue?: (playerId: string) => void;
  onPlayerClick?: (playerId: string, event: React.MouseEvent) => void;
  onImportUdk: (file: File | undefined) => void;
}) {
  const [sheet, setSheet] = useState("Overall");
  // "Source" only ever offers UDK for a position the owner has actually
  // imported real UDK data for (the owner's real file is QB-only) --
  // never fabricated for RB/WR/TE/K/DST from nothing.
  const [source, setSource] = useState<"NWR" | "UDK">("NWR");
  // Owner feedback closure, section 8: drafted players disappear
  // immediately by default from every lane here too (Cheat Sheets was a
  // real, disclosed gap -- previously showed every player regardless of
  // draft state). Uses the canonical player-ID drafted list
  // (board.drafted), never a display-name comparison; a "Show Drafted"
  // toggle stays available for the owner to review history.
  const [showDrafted, setShowDrafted] = useState(false);
  const draftedIds = useMemo(() => new Set(data.draftBoard?.drafted ?? []), [data.draftBoard?.drafted]);
  const udkForSheet = data.udkRankings?.positions?.[sheet];
  const manualRows = useMemo(
    () => (data.manualAssets ?? []).filter((row) => row.position === sheet && (showDrafted || !draftedIds.has(row.playerId))),
    [data.manualAssets, sheet, showDrafted, draftedIds],
  );
  const rows = useMemo(
    () => (sheet === "Overall" || sheet === "Tiers" || MANUAL_POSITIONS.has(sheet)
      ? data.rankings
      : data.rankings.filter((row) => row.position === sheet)
    ).filter((row) => showDrafted || !row.drafted),
    [data.rankings, sheet, showDrafted],
  );
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
      if (!playerId) return null;
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
  return (
    <>
      <PageHeader
        eyebrow="Draft prep · Profile specific"
        title="Cheat Sheet"
        description="A printable and exportable board built from the active league's governed current-season rankings."
        status={<><StatusBadge tone="safe" label={data.activeProfile.leagueName} /><StatusBadge tone="safe" label={`${isManual ? manualRows.length : udkForSheet && source === "UDK" ? udkVisibleEntries.length : visible.length} players`} /></>}
        actions={
          <>
            <label className="file-action">
              Import UDK CSV
              <input accept=".csv,text/csv" disabled={Boolean(working)} onChange={(event) => onImportUdk(event.target.files?.[0])} type="file" />
            </label>
            <Button icon="board" onClick={exportCsv}>Export CSV</Button>
          </>
        }
      />
      <Panel title={`${data.activeProfile.leagueName} · ${data.activeProfile.season}`} eyebrow={`${data.activeProfile.teamCount} teams · ${data.activeProfile.scoring.reception} PPR · ${data.activeProfile.scoring.tePremium} TE premium`}>
        <div className="toolbar">
          <SegmentedControl label="Sheet" options={SHEETS} value={sheet} onChange={(value) => { setSheet(value); setSource("NWR"); }} />
          {udkForSheet ? (
            <SegmentedControl
              label="Source"
              options={["NWR", "UDK"]}
              value={source}
              onChange={(value) => setSource(value as "NWR" | "UDK")}
            />
          ) : null}
          <label className="toolbar__toggle">
            <input type="checkbox" checked={showDrafted} onChange={(event) => setShowDrafted(event.target.checked)} />
            Show Drafted
          </label>
        </div>
        {isManual ? (
          <DataTable
            columns={[
              { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span> },
              { key: "authority", label: "Status", sort: "text", render: () => <StatusBadge tone="review" label="Manual · not modeled by NWR" /> },
              draftActionColumn,
            ]}
            rows={manualRows.map((row: ManualDraftAsset) => ({ ...row }))}
            rowKey={(row) => String(row.playerId)}
          />
        ) : udkForSheet && source === "UDK" ? (
          <>
            <p className="boundary-note">
              {udkForSheet.provider} · imported {udkForSheet.importedAtUtc} · {udkForSheet.sourceRows} rows.
              UDK's own position rank/tier — NOT NWR's overall rank, and its Risk/Upside/ADP are provider
              context, not NWR calibrated confidence. ADP is shown exactly as UDK printed it (source team
              count unknown) — never reinterpreted as this league's own round.pick.
            </p>
            <DataTable
              columns={[
                { key: "rank", label: "UDK Rank", sort: "number", width: "72px" },
                { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · Bye {String((row as unknown as UdkPlayerEntry).byeWeek || "—")}</small></span> },
                { key: "tier", label: "Tier", sort: "number", render: (row) => row.tier == null ? "—" : String(row.tier) },
                { key: "adpRaw", label: "UDK ADP", sort: "text", render: (row) => (row.adpRaw as string) || "—" },
                { key: "points", label: "Proj pts", align: "right", sort: "number", render: (row) => row.points == null ? "—" : formatNumber(row.points as number, 1) },
                { key: "riskUpside", label: "Risk / Upside", align: "right", render: (row) => `${row.risk == null ? "—" : formatNumber(row.risk as number, 1)} / ${row.upside == null ? "—" : formatNumber(row.upside as number, 1)}` },
                { key: "outlook", label: "Outlook", render: (row) => <span title={String(row.outlook || "")}>{String(row.outlook || "").slice(0, 80)}{String(row.outlook || "").length > 80 ? "…" : ""}</span> },
                draftActionColumn,
              ]}
              rows={udkVisibleEntries.map((row) => ({ ...row, playerId: row.playerId ?? "" }))}
              rowKey={(row) => String(row.playerId || `unmatched-${String(row.playerName)}-${String(row.rank)}`)}
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
