import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { BallersPreview, PasteAdpPreview, RedraftBootstrap } from "@nwr/contracts";
import { Button, ErrorState, PageHeader, Panel, StatusBadge } from "@nwr/ui";
import { useEffect, useMemo, useState } from "react";

import { leagueFormat } from "./league-context";
import { usePlayerDetailOpener } from "./player-detail-context";

type LeagueSelection = "AUTO" | "CONSENSUS" | "SLEEPER" | "ESPN" | "FANTASYPROS" | "DISABLED";

function providerLabel(adp: NonNullable<RedraftBootstrap["draftBoard"]>["adp"] | undefined) {
  if (!adp?.available) return "ADP: unavailable";
  return `ADP: ${adp.source.replace(/^Owner-imported /i, "Owner ")} · ${adp.freshness ?? "cached"}`;
}

type PlatformCoverage = Record<string, { available: number; total: number }> | undefined;

export function platformCoverageText(platformCoverage: PlatformCoverage) {
  if (!platformCoverage) return "Preview to inspect platform-column coverage.";
  return [{ label: "Consensus", key: "consensus" }, { label: "Sleeper", key: "sleeper" }, { label: "ESPN", key: "espn" }, { label: "FantasyPros", key: "fantasypros" }].map(({ label, key }) => {
    const coverage = platformCoverage[key] ?? platformCoverage[key.toUpperCase()];
    return `${label}: ${coverage?.available ?? 0}/${coverage?.total ?? 0}`;
  }).join(" · ");
}

// NWR PRE-DRAFT MARKET DATA / ADP UX CLEANUP (2026-09-08, directive
// section 10): explicit, honestly-named exports of already-loaded owner
// data -- never raw PDF content, only normalized CSV NWR already parsed.
function csvCell(value: unknown): string {
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function downloadCsv(filename: string, csv: string) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url; link.download = filename; document.body.append(link); link.click(); link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function exportBallersCsv(data: RedraftBootstrap) {
  const headers = ["Position", "Player", "Team", "Bye", "Rank", "Tier", "ADP", "Risk", "Upside", "Points", "Outlook"];
  const rows = (data.udkRankings?.positions ?? []).flatMap((position) =>
    position.entries.map((entry) => [entry.position, entry.playerName, entry.team, entry.byeWeek, entry.rank ?? "", entry.tier ?? "", entry.adpRaw, entry.risk ?? "", entry.upside ?? "", entry.points ?? "", entry.outlook]),
  );
  downloadCsv("nwr_ballers_udk_snapshot.csv", [headers, ...rows].map((record) => record.map(csvCell).join(",")).join("\r\n") + "\r\n");
}

function exportMarketAdpCsv(data: RedraftBootstrap) {
  const headers = ["PlayerId", "Player", "Position", "Team", "Consensus", "Sleeper", "ESPN", "FantasyPros"];
  const byId = new Map(data.rankings.map((row) => [row.playerId, row]));
  const rows = Object.entries(data.marketProviderAdp ?? {}).map(([playerId, values]) => {
    const ranking = byId.get(playerId);
    return [playerId, ranking?.playerName ?? "", ranking?.position ?? "", ranking?.team ?? "", values.consensus ?? "", values.sleeper ?? "", values.espn ?? "", values.fantasypros ?? ""];
  });
  downloadCsv("nwr_multiplatform_adp_snapshot.csv", [headers, ...rows].map((record) => record.map(csvCell).join(",")).join("\r\n") + "\r\n");
}

export function parserModeLabel(mode: string | undefined) {
  if (mode === "CSV_MULTI_PLATFORM") return "CSV";
  if (mode === "MARKDOWN_TABLE") return "Markdown table";
  if (mode === "RESPONSIVE_PLATFORM_CLIPBOARD") return "Plain-text";
  return "Platform table";
}

export function detectedPlatform(profile: RedraftBootstrap["activeProfile"]) {
  if (profile?.provider === "sleeper") return "Sleeper";
  if (profile?.provider === "espn") return "ESPN";
  if (profile?.provider === "fantasypros") return "FantasyPros";
  return "Consensus";
}

/**
 * NWR UI expansion pass (2026-09-12, Players surface): the Market Data
 * body itself, split out from its own `PageHeader` so the new unified
 * `PlayersPage` workspace (players.tsx) can render ONE shared header above
 * all four modes (Rankings/Tiers/Compare/Market) instead of repeating one
 * per tab -- same shape as `RankingsContent`/`TiersContent`/`CompareContent`
 * in pages.tsx. `AdpProvidersPage` below is kept as an unrouted legacy
 * fallback (same precedent as `WaiversPage` after the Improve Team pass)
 * -- no route in RedraftApp.tsx points to it any more; `/adp`'s scoped
 * route now renders `PlayersPage` with its Market tab selected.
 */
export function MarketDataContent({ client, data, onUpdate }: { client: NwrApiClient; data: RedraftBootstrap; onUpdate: (data: RedraftBootstrap) => void }) {
  const [working, setWorking] = useState("");
  const [error, setError] = useState<NwrApiError | null>(null);
  const [message, setMessage] = useState("");
  const [pasteText, setPasteText] = useState("");
  const [pasteLabel, setPasteLabel] = useState("Owner platform rankings");
  const [pastePreview, setPastePreview] = useState<PasteAdpPreview | null>(null);
  const [previewFilter, setPreviewFilter] = useState("ALL");
  const [previewLimit, setPreviewLimit] = useState(25);
  const activeProfile = data.activeProfile;
  const adp = data.draftBoard?.adp;
  const snapshot = data.ownerPlatformSnapshot;
  const detectedPlatformLabel = detectedPlatform(activeProfile);
  const activeColumn = snapshot?.activeColumn || detectedPlatformLabel.toUpperCase();
  const previewRows = (pastePreview?.rows ?? []).filter((row) => {
    const status = String(row.matchStatus || "");
    const reason = String(row.unmatchedReason || "");
    if (previewFilter === "MATCHED") return status === "MATCHED";
    if (previewFilter === "UNMATCHED") return status === "UNMATCHED";
    if (previewFilter === "AMBIGUOUS") return reason.includes("AMBIGUOUS") || reason.includes("COLLISION");
    if (previewFilter === "MISSING") return row[`${activeColumn.toLowerCase()}Adp`] == null;
    return true;
  });
  // NWR UI expansion pass (2026-09-12, Players surface): the ADP preview
  // table already shows a real matched NWR player per row -- the directive's
  // "all players clickable" requirement applies here too, not just to
  // Rankings/Tiers/Compare. `matchedNwrPlayerId` is a real backend field
  // (`matched_nwr_player_id`, camelCased at the API boundary -- confirmed
  // by reading `redraft_draft_room_v1_service.py`), so this is a real
  // identity, not a synthetic one. Position/team come from the already-
  // loaded governed rankings (the row itself does not always carry them),
  // same lookup shape as `exportMarketAdpCsv` above.
  const rankingById = useMemo(() => new Map(data.rankings.map((row) => [row.playerId, row])), [data.rankings]);
  const openPlayerDetail = usePlayerDetailOpener(data.activeProfileId, "PLAYERS_MARKET");
  const [leagueSelection, setLeagueSelection] = useState<LeagueSelection>("AUTO");
  useEffect(() => setLeagueSelection((snapshot?.leagueSelection || "AUTO") as LeagueSelection), [snapshot?.leagueSelection, activeProfile?.profileId]);
  const fail = (reason: unknown, fallback: string) => setError(reason instanceof NwrApiError ? reason : new NwrApiError(fallback));
  const run = async (key: string, action: () => Promise<RedraftBootstrap>, success: string) => {
    if (!activeProfile || working) return;
    setWorking(key); setError(null); setMessage("");
    try { const next = await action(); onUpdate(next); setMessage(next.draftBoard?.adp?.lastRefreshError ? "FFC refresh failed; the last known good cached ADP remains available." : success); }
    catch (reason) { fail(reason, "The ADP provider action could not be completed."); }
    finally { setWorking(""); }
  };
  const preview = async (overrideText?: string) => {
    const text = overrideText ?? pasteText;
    if (!activeProfile || !text.trim() || working) return;
    setWorking("paste-preview"); setError(null); setMessage("");
    try {
      const result = await client.previewRedraftPasteAdp(activeProfile.profileId, text, "CONSENSUS");
      setPastePreview(result.pastePreview);
      setMessage(`${parserModeLabel(result.pastePreview.parserMode)} parse: ${result.pastePreview.matchedRows}/${result.pastePreview.sourceRows} safe player matches.`);
    } catch (reason) { fail(reason, "The platform table could not be parsed."); }
    finally { setWorking(""); }
  };
  // NWR DATA-IMPORT UX FIX (2026-09-08): a real, multi-platform CSV export
  // (Name, Position, Team, ADP, Position Rank, Consensus ADP, Sleeper ADP,
  // ESPN ADP, FantasyPros ADP) now parses through the exact same backend
  // pipeline as a pasted table (_owner_platform_rows tries CSV first) --
  // no new route/client method, just a file-read into the same textarea +
  // preview flow so the owner sees the same match/coverage review before
  // saving, whether they pasted or uploaded.
  const importMultiPlatformCsv = async (file: File | undefined) => {
    if (!file || !activeProfile || working) return;
    setError(null); setMessage("");
    try {
      const text = await file.text();
      setPasteText(text);
      setPasteLabel(file.name.replace(/\.csv$/i, ""));
      await preview(text);
    } catch (reason) { fail(reason, `${file.name} could not be read.`); }
  };
  // NWR PRE-DRAFT MARKET DATA / ADP UX CLEANUP (2026-09-08, directive
  // sections 3 & 6): the old "Import owner ADP CSV" panel called
  // client.importRedraftAdp directly -- a rigid single-column importer with
  // no preview step, fully superseded by importMultiPlatformCsv above
  // (same file input, but routes through the real preview-before-activate
  // flow and already accepts the old simple Name/Position/ADP shape as well
  // as full multi-platform files). Removed to avoid a duplicate primary
  // control and a path that could silently activate a malformed file.
  const approveCandidate = async (row: Record<string, unknown>, candidate: Record<string, unknown>) => {
    if (!activeProfile || working) return;
    setWorking("manual-match"); setError(null); setMessage("");
    try {
      const next = await client.approveRedraftOwnerPlatformManualMatch(activeProfile.profileId, String(row.playerName || ""), String(row.position || ""), String(row.positionRank || ""), String(candidate.playerId || ""), snapshot?.rawHash || "");
      onUpdate(next);
      setMessage("Owner-approved ADP-only alias saved locally. Preview or save the snapshot again to apply it; rankings and identity data were not changed.");
    } catch (reason) { fail(reason, "The local ADP-only alias could not be saved."); }
    finally { setWorking(""); }
  };

  // NWR DATA-IMPORT UX FIX (2026-09-08, directive sections 1-4): the real
  // Ballers/UDK CSV+PDF parser/versioning pipeline already existed
  // (parse_udk_position_csv/parse_udk_position_pdf, save_udk_position_
  // *_rankings, rollback_udk_position_rankings) -- this closes the one
  // real owner-facing gap: no obvious import control, no preview-before-
  // activate step, and a PDF-only path with zero route/UI at all. One
  // control handles any position mix (QB/RB/WR/TE/K/DST) in one file --
  // positions actually present are read from the file itself.
  const ballersRankings = data.udkRankings;
  const [ballersPreview, setBallersPreview] = useState<BallersPreview | null>(null);
  const [ballersFileName, setBallersFileName] = useState("");
  const [ballersPayload, setBallersPayload] = useState<{ csvText?: string; pdfBase64?: string } | null>(null);
  const readFileAsBase64 = (file: File) => new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error);
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.slice(result.indexOf(",") + 1));
    };
    reader.readAsDataURL(file);
  });
  const previewBallers = async (file: File | undefined) => {
    if (!file || !activeProfile || working) return;
    setWorking("ballers-preview"); setError(null); setMessage(""); setBallersPreview(null); setBallersPayload(null);
    try {
      const isPdf = file.name.toLowerCase().endsWith(".pdf");
      const payload = isPdf ? { pdfBase64: await readFileAsBase64(file) } : { csvText: await file.text() };
      const result = await client.previewBallersImport(activeProfile.profileId, payload);
      setBallersPreview(result.ballersPreview);
      setBallersFileName(file.name);
      setBallersPayload(payload);
      setMessage(`Ballers preview: ${result.ballersPreview.matchedRows}/${result.ballersPreview.sourceRows} safe player matches across ${Object.keys(result.ballersPreview.perPositionCounts).length} position(s).`);
    } catch (reason) { fail(reason, `${file.name} could not be parsed as a Ballers cheat sheet.`); }
    finally { setWorking(""); }
  };
  const activateBallers = async () => {
    if (!activeProfile || !ballersPayload || working) return;
    setWorking("ballers-activate"); setError(null); setMessage("");
    try {
      const next = ballersPayload.pdfBase64
        ? await client.importUdkPdfRankings(activeProfile.profileId, ballersPayload.pdfBase64)
        : await client.importUdkRankings(activeProfile.profileId, ballersPayload.csvText || "");
      onUpdate(next);
      setMessage(`Ballers cheat sheet activated from ${ballersFileName}. This global snapshot now feeds every local Redraft league; NWR ranks/projections did not change.`);
      setBallersPreview(null); setBallersPayload(null); setBallersFileName("");
    } catch (reason) { fail(reason, "The Ballers cheat sheet could not be activated."); }
    finally { setWorking(""); }
  };
  const cancelBallersPreview = () => { setBallersPreview(null); setBallersPayload(null); setBallersFileName(""); setMessage(""); };
  const rollbackBallersPosition = async (position: string) => {
    if (!activeProfile || working) return;
    await run("ballers-rollback", () => client.rollbackUdkPositionRankings(activeProfile.profileId, position), `Rolled ${position} back to its previous Ballers import.`);
  };

  return <div className="adp-providers-page" aria-busy={Boolean(working)}>
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    <p aria-live="polite" className="profile-feedback">{message}</p>
    <h3 className="market-data-group-heading">Market / ADP</h3>
    <Panel title="Active ADP source" eyebrow="Compact in Draft Room · detail here">
      <dl className="adp-details"><div><dt>Current source</dt><dd>{adp?.available ? adp.source : "No active ADP snapshot"}</dd></div><div><dt>Freshness</dt><dd>{adp?.freshness ?? "UNAVAILABLE"}</dd></div><div><dt>Source date</dt><dd>{adp?.dateWindow || adp?.sourceDate || "—"}</dd></div><div><dt>Player matches</dt><dd>{adp?.available ? `${adp.matchedPlayers}/${adp.sourcePlayers ?? adp.rankingPlayers}` : "—"}</dd></div><div><dt>Priority</dt><dd>Active owner platform column → Consensus → FFC → owner CSV → disclosed fallback</dd></div><div><dt>Boundary</dt><dd>Market timing only; NWR value rank and projections remain authoritative.</dd></div></dl>
      {adp?.lastRefreshError ? <p className="boundary-note">Last FFC refresh: {adp.lastRefreshError}</p> : null}
      <div className="profile-edit-actions"><Button disabled={!activeProfile || Boolean(working)} icon="activity" onClick={() => void run("adp-refresh", () => client.refreshRedraftAdp(activeProfile!.profileId), "Fantasy Football Calculator ADP refreshed locally. NWR ranks did not change.")}>{working === "adp-refresh" ? "Refreshing…" : "Refresh FFC ADP"}</Button><Button disabled={!activeProfile || Boolean(working)} icon="undo" variant="secondary" onClick={() => void run("paste-clear", () => client.clearRedraftPasteAdp(activeProfile!.profileId), "This league now uses its automatic platform column again. FFC remains the fallback.")}>{working === "paste-clear" ? "Clearing…" : "Clear league override"}</Button></div>
    </Panel>
    <div className="adp-provider-grid">
      <Panel title="Import Multi-Platform ADP" eyebrow="Import once · use across every Redraft league">
        <p>Import one full platform ADP snapshot — CSV file, or paste a markdown table or plain-text clipboard block. NWR safely matches players once and stores the Consensus, Sleeper, ESPN, and FantasyPros columns together for every local Redraft league. It never changes rankings, projections, or Sleeper data.</p>
        {snapshot?.available ? <p className="boundary-note">Current snapshot: {snapshot.importedAtUtc ? new Date(snapshot.importedAtUtc).toLocaleDateString() : "—"} · {snapshot.rowCount} rows.</p> : null}
        <div className="form-grid">
          <label className="file-action">Choose multi-platform ADP CSV<input accept=".csv,text/csv" disabled={!activeProfile || Boolean(working)} onChange={(event) => void importMultiPlatformCsv(event.target.files?.[0])} type="file" /></label>
          <label className="form-field"><span>Source label</span><input disabled={Boolean(working)} value={pasteLabel} onChange={(event) => setPasteLabel(event.target.value)} /></label>
          <div className="form-field"><span>Parser modes</span><small>A real CSV file is recognized directly; markdown tables and plain-text player blocks are also accepted when pasted below.</small></div>
        </div>
        <label className="form-field"><span>Raw pasted text (or the file's own contents, once chosen above)</span><textarea disabled={Boolean(working)} rows={10} wrap="off" style={{ fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace", whiteSpace: "pre", overflowX: "auto" }} value={pasteText} onChange={(event) => { setPasteText(event.target.value); setPastePreview(null); setPreviewLimit(25); }} placeholder={"Name,Position,Team,ADP,Position Rank,Consensus ADP,Sleeper ADP,ESPN ADP,FantasyPros ADP\nExample Player,RB,KC,3.2,1,3.2,2.9,4.1,3.7\n\nor a markdown table:\n| Position | Player | Consensus | Sleeper | ESPN | FantasyPros |\n| --- | --- | ---: | ---: | ---: | ---: |\n| RB1 | Example Player | 3.2 | — | 4.1 | 3.7 |\n\nor plain text:\nWR13\nExample Player\n18.4 19.1 17.8 18.0"} /></label>
        <div className="profile-edit-actions"><Button disabled={!activeProfile || !pasteText.trim() || Boolean(working)} icon="activity" onClick={() => void preview()} variant="secondary">{working === "paste-preview" ? "Parsing…" : "Preview parse"}</Button><Button disabled={!activeProfile || !pasteText.trim() || Boolean(working)} icon="check" onClick={() => void run("paste-save", () => client.saveRedraftPasteAdp(activeProfile!.profileId, pasteText, "CONSENSUS", pasteLabel), "Global owner platform snapshot saved locally. Each league can now choose its column.")}>{working === "paste-save" ? "Saving…" : "Save global snapshot"}</Button><Button disabled={!snapshot?.available} variant="secondary" icon="board" onClick={() => exportMarketAdpCsv(data)}>Export Market ADP CSV</Button></div>
        {pastePreview ? <div className="copy-muted"><div className="metric-grid"><div><strong>{pastePreview.sourceRows}</strong><small>Parsed rows</small></div><div><strong>{pastePreview.matchedRows}</strong><small>Matched</small></div><div><strong>{pastePreview.unmatched.length}</strong><small>Unmatched</small></div><div><strong>{pastePreview.rows.filter((row) => String(row.matchSource || "") === "OWNER_APPROVED").length}</strong><small>Owner-approved</small></div><div><strong>{platformCoverageText(pastePreview.platformCoverage)}</strong><small>Platform coverage</small></div><div><strong>{activeColumn}</strong><small>{activeProfile?.leagueName || "—"} · {detectedPlatformLabel}</small></div></div><small>Fallback: {activeColumn} → Consensus → FFC → Unavailable · {parserModeLabel(pastePreview.parserMode)}</small><div className="profile-edit-actions"><Button variant={previewFilter === "ALL" ? "primary" : "secondary"} onClick={() => { setPreviewFilter("ALL"); setPreviewLimit(25); }}>All rows</Button><Button variant={previewFilter === "MATCHED" ? "primary" : "secondary"} onClick={() => { setPreviewFilter("MATCHED"); setPreviewLimit(25); }}>Matched</Button><Button variant={previewFilter === "UNMATCHED" ? "primary" : "secondary"} onClick={() => { setPreviewFilter("UNMATCHED"); setPreviewLimit(25); }}>Unmatched</Button><Button variant={previewFilter === "AMBIGUOUS" ? "primary" : "secondary"} onClick={() => { setPreviewFilter("AMBIGUOUS"); setPreviewLimit(25); }}>Ambiguous</Button><Button variant={previewFilter === "MISSING" ? "primary" : "secondary"} onClick={() => { setPreviewFilter("MISSING"); setPreviewLimit(25); }}>Missing active platform</Button></div><div className="draft-board-scroll"><table><thead><tr><th>Row</th><th>Pos rank</th><th>Player</th><th>Team</th><th>Consensus</th><th>Sleeper</th><th>ESPN</th><th>FantasyPros</th><th>Match status / source</th><th>Matched NWR player</th><th>Reason / review</th><th></th></tr></thead><tbody>{previewRows.slice(0, previewLimit).map((row) => { const matched = rankingById.get(String(row.matchedNwrPlayerId ?? "")); return <tr key={String(row.sourceRowIndex)}><td>{String(row.sourceRowIndex ?? "—")}</td><td>{String(row.positionRank ?? row.position ?? "—")}</td><td>{String(row.playerName ?? "—")}</td><td>{String(row.sourceTeam ?? "—")}</td><td>{String(row.consensusAdp ?? "—")}</td><td>{String(row.sleeperAdp ?? "—")}</td><td>{String(row.espnAdp ?? "—")}</td><td>{String(row.fantasyprosAdp ?? "—")}</td><td>{String(row.matchStatus ?? "—")} · {String(row.matchSource ?? "UNMATCHED")}</td><td>{String(row.matchedNwrPlayerName ?? "—")}</td><td>{String(row.unmatchedReason ?? (row[`${activeColumn.toLowerCase()}Adp`] == null ? "Selected column missing; Consensus/FFC fallback may apply" : "Matched"))}{Array.isArray(row.candidateSuggestions) ? row.candidateSuggestions.map((value) => { const candidate = value as Record<string, unknown>; return <div key={String(candidate.playerId)}><small>{String(candidate.playerName)} · {String(candidate.position)} · {String(candidate.team || "—")} · {String(candidate.confidence)}</small><Button disabled={Boolean(working) || String(candidate.position) !== String(row.position)} variant="secondary" onClick={() => void approveCandidate(row, candidate)}>Approve ADP-only match</Button></div>; }) : null}</td><td>{matched ? <Button variant="ghost" onClick={() => openPlayerDetail({ playerId: matched.playerId, playerName: matched.playerName, position: matched.position, team: matched.team })}>View</Button> : null}</td></tr>; })}</tbody></table></div>{previewRows.length > previewLimit ? <Button variant="secondary" onClick={() => setPreviewLimit((value) => value + 25)}>Show 25 more</Button> : null}{previewFilter === "UNMATCHED" ? pastePreview.unmatched.slice(0, 12).map((warning) => <small key={warning}>{warning}</small>) : null}</div> : null}
        {snapshot?.available ? <p className="boundary-note">Stored snapshot: {snapshot.rowCount} rows, {snapshot.matchedRows ?? "—"} safe matches, {parserModeLabel(snapshot.parserMode)} parser, hash {snapshot.rawHash.slice(0, 12)}… <small>{platformCoverageText(snapshot.platformCoverage)}</small></p> : null}
      </Panel>
      <Panel title="League Platform Selection" eyebrow="Per league · global snapshot remains unchanged">
        <p>This league is detected as <strong>{snapshot?.detectedPlatform || detectedPlatformLabel}</strong>. Auto follows the connected provider: Sleeper → Sleeper, ESPN → ESPN, FantasyPros → FantasyPros, otherwise Consensus.</p>
        <label className="form-field"><span>Use platform ADP for this league</span><select disabled={!snapshot?.available || Boolean(working)} value={leagueSelection} onChange={(event) => setLeagueSelection(event.target.value as LeagueSelection)}><option value="AUTO">Auto (detected platform)</option><option value="CONSENSUS">Consensus</option><option value="SLEEPER">Sleeper</option><option value="ESPN">ESPN</option><option value="FANTASYPROS">FantasyPros</option><option value="DISABLED">Disabled / use FFC fallback</option></select></label>
        <p className="boundary-note">Missing selected-column values use Consensus, then FFC, then show unavailable. Sleeper is always owner-imported and read-only.</p>
        <div className="profile-edit-actions"><Button disabled={!activeProfile || !snapshot?.available || Boolean(working)} icon="draft" onClick={() => void run("platform-selection", () => client.setRedraftOwnerPlatformSelection(activeProfile!.profileId, leagueSelection), `Active platform selection set to ${leagueSelection === "AUTO" ? "Auto" : leagueSelection}.`)}>{working === "platform-selection" ? "Activating…" : "Activate for this league"}</Button></div>
      </Panel>
    </div>
    <h3 className="market-data-group-heading">Ballers / UDK <small>(also feeds K/DST reference — see Draft Room · Market Data / ADP)</small></h3>
    <Panel title="Import Ballers Cheat Sheet" eyebrow="Import once · use across every Redraft league">
      <p>Import the owner's Fantasy Footballers Podcast UDK cheat sheet — CSV or PDF, any position mix (QB/RB/WR/TE/K/DST) in one file. NWR safely matches players once; the same active snapshot then feeds Suggestions, Cheat Sheets, Compare, and the Player Drawer for every local Redraft league. Ballers stays reference-only for QB/RB/WR/TE — it never changes NWR Rank, Player Score, Team Score, Championship Equity, RAV, or Pick Score. For K/DST it remains the explicit reference/fallback until NWR has a promoted direct K/DST model — no NWR Player Score is ever fabricated for K/DST.</p>
      {ballersRankings && ballersRankings.positions.length > 0 ? (
        <p className="boundary-note">
          Current Ballers snapshot: {ballersRankings.positions.map((p) => `${p.position} ${p.entries.length}`).join(" · ")}
          {" — "}imported {ballersRankings.positions[0]?.importedAtUtc ? new Date(ballersRankings.positions[0].importedAtUtc).toLocaleString() : "—"}
        </p>
      ) : <p className="boundary-note">No Ballers cheat sheet imported yet.</p>}
      <div className="profile-edit-actions">
        <label className="file-action">Choose Ballers cheat sheet (CSV or PDF)<input accept=".csv,text/csv,.pdf,application/pdf" disabled={!activeProfile || Boolean(working)} onChange={(event) => void previewBallers(event.target.files?.[0])} type="file" /></label>
        <Button disabled={!ballersRankings || ballersRankings.positions.length === 0} variant="secondary" icon="board" onClick={() => exportBallersCsv(data)}>Export Ballers / UDK CSV</Button>
      </div>
      {ballersPreview ? (
        <div className="copy-muted">
          <div className="metric-grid">
            <div><strong>{ballersFileName}</strong><small>Source file</small></div>
            <div><strong>{ballersPreview.sourceFormat}</strong><small>Format</small></div>
            <div><strong>{ballersPreview.sourceSha256.slice(0, 12)}…</strong><small>Source hash</small></div>
            <div><strong>{ballersPreview.sourceRows}</strong><small>Total rows</small></div>
            <div><strong>{ballersPreview.matchedRows}</strong><small>Matched</small></div>
            <div><strong>{ballersPreview.unmatched.length}</strong><small>Unmatched</small></div>
            <div><strong>{ballersPreview.duplicateRows.length}</strong><small>Duplicate</small></div>
          </div>
          <p>
            Position counts: {(["QB", "RB", "WR", "TE", "K", "DST"] as const).map((position) => `${position} ${ballersPreview.perPositionCounts[position] ?? 0}`).join(" · ")}
          </p>
          <p className="boundary-note">Fields detected: {Object.keys(ballersPreview.positions[Object.keys(ballersPreview.positions)[0] || ""]?.[0] ?? {}).length > 0 ? "Rank, Position Rank, Tier, ADP, Risk, Upside, Points, Outlook, Dynasty, Team, Bye" : "—"} — fields not present in the source file are never invented.</p>
          {ballersPreview.unmatched.length > 0 ? <details><summary>Unmatched rows ({ballersPreview.unmatched.length})</summary>{ballersPreview.unmatched.slice(0, 20).map((warning) => <small key={warning}>{warning}<br /></small>)}</details> : null}
          {ballersPreview.duplicateRows.length > 0 ? <details><summary>Duplicate rows ({ballersPreview.duplicateRows.length})</summary>{ballersPreview.duplicateRows.map((warning) => <small key={warning}>{warning}<br /></small>)}</details> : null}
          <div className="profile-edit-actions">
            <Button disabled={Boolean(working)} icon="check" onClick={() => void activateBallers()}>{working === "ballers-activate" ? "Activating…" : "Activate Ballers Cheat Sheet"}</Button>
            <Button disabled={Boolean(working)} variant="secondary" onClick={cancelBallersPreview}>Cancel</Button>
          </div>
        </div>
      ) : null}
      {ballersRankings && ballersRankings.positions.some((p) => (p.historyCount ?? 0) > 0) ? (
        <div className="profile-edit-actions">
          {ballersRankings.positions.filter((p) => (p.historyCount ?? 0) > 0).map((p) => (
            <Button key={p.position} disabled={Boolean(working)} variant="secondary" onClick={() => void rollbackBallersPosition(p.position)}>
              {working === "ballers-rollback" ? "Rolling back…" : `Roll back ${p.position}`}
            </Button>
          ))}
        </div>
      ) : null}
    </Panel>
  </div>;
}

export function AdpProvidersPage({ client, data, onUpdate }: { client: NwrApiClient; data: RedraftBootstrap; onUpdate: (data: RedraftBootstrap) => void }) {
  const activeProfile = data.activeProfile;
  const adp = data.draftBoard?.adp;
  return <>
    <PageHeader eyebrow={activeProfile ? `Active League · ${leagueFormat(activeProfile)}` : "Provider settings · local only"} title="Market Data" description="Manage draft-market timing (ADP) and Ballers/UDK reference rankings separately from NWR rankings and projections. Changes here never write to Sleeper." status={<><StatusBadge tone={adp?.available ? "safe" : "review"} label={providerLabel(adp)} /><StatusBadge tone="safe" label="NWR ranks unchanged" /></>} />
    <MarketDataContent client={client} data={data} onUpdate={onUpdate} />
  </>;
}
