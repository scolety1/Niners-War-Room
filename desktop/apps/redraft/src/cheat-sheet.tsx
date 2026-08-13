import type { RedraftBootstrap, RedraftRanking } from "@nwr/contracts";
import { Button, DataTable, EmptyState, PageHeader, Panel, SegmentedControl, StatusBadge, formatNumber } from "@nwr/ui";
import { useMemo, useState } from "react";

const SHEETS = ["Overall", "QB", "RB", "WR", "TE", "Tiers"];

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

export function CheatSheetPage({ data }: { data: RedraftBootstrap }) {
  const [sheet, setSheet] = useState("Overall");
  const rows = useMemo(() => sheet === "Overall" || sheet === "Tiers" ? data.rankings : data.rankings.filter((row) => row.position === sheet), [data.rankings, sheet]);
  if (!data.activeProfile) return <><PageHeader eyebrow="Draft prep · Current season" title="Cheat Sheet" description="Activate a league profile to build its printable current-season board." /><EmptyState icon="profile" title="No active league profile" message="Cheat sheets are profile-specific and stay inside Redraft." action={<Button onClick={() => { window.location.hash = "#/profile"; }}>Open profile manager</Button>} /></>;
  const exportCsv = () => {
    const blob = new Blob([buildCheatSheetCsv(data, rows)], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeName = data.activeProfile!.leagueName.replace(/[^A-Za-z0-9._-]+/g, "_").replace(/^[._]+|[._]+$/g, "") || "redraft";
    link.href = url; link.download = `${safeName}_${data.activeProfile!.season}_${sheet}.csv`; document.body.append(link); link.click(); link.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 0);
  };
  const visible = sheet === "Tiers" ? rows.slice().sort((left, right) => left.tier - right.tier || left.overallRank - right.overallRank) : rows;
  return <><PageHeader eyebrow="Draft prep · Profile specific" title="Cheat Sheet" description="A printable and exportable board built from the active league's governed current-season rankings." status={<><StatusBadge tone="safe" label={data.activeProfile.leagueName} /><StatusBadge tone="safe" label={`${visible.length} players`} /></>} actions={<Button icon="board" onClick={exportCsv}>Export CSV</Button>} /><Panel title={`${data.activeProfile.leagueName} · ${data.activeProfile.season}`} eyebrow={`${data.activeProfile.teamCount} teams · ${data.activeProfile.scoring.reception} PPR · ${data.activeProfile.scoring.tePremium} TE premium`}><div className="toolbar"><SegmentedControl label="Sheet" options={SHEETS} value={sheet} onChange={setSheet} /></div><DataTable columns={[{ key: "overallRank", label: "Rank", width: "64px" },{ key: "playerName", label: "Player", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}{String(row.positionRank)}</small></span> },{ key: "position", label: "Pos", align: "center" },{ key: "tier", label: "Tier" },{ key: "projectedPoints", label: "Proj pts", align: "right", render: (row) => formatNumber(row.projectedPoints as number, 1) },{ key: "replacementAdjustedValue", label: "Value over replacement", align: "right", render: (row) => formatNumber(row.replacementAdjustedValue as number, 1) },{ key: "confidence", label: "Confidence" }]} rows={visible.map((row) => ({ ...row }))} rowKey={(row) => String(row.playerId)} /></Panel></>;
}
