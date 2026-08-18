import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { PasteAdpPreview, RedraftBootstrap } from "@nwr/contracts";
import { Button, ErrorState, PageHeader, Panel, StatusBadge } from "@nwr/ui";
import { useEffect, useState } from "react";

import { leagueFormat } from "./league-context";

type LeagueSelection = "AUTO" | "CONSENSUS" | "SLEEPER" | "ESPN" | "FANTASYPROS" | "DISABLED";

function providerLabel(adp: NonNullable<RedraftBootstrap["draftBoard"]>["adp"] | undefined) {
  if (!adp?.available) return "ADP: unavailable";
  return `ADP: ${adp.source.replace(/^Owner-imported /i, "Owner ")} · ${adp.freshness ?? "cached"}`;
}

function coverageText(preview: PasteAdpPreview | null) {
  if (!preview?.platformCoverage) return "Preview to inspect platform-column coverage.";
  return ["CONSENSUS", "SLEEPER", "ESPN", "FANTASYPROS"].map((column) => {
    const coverage = preview.platformCoverage?.[column];
    return `${column}: ${coverage?.available ?? 0}/${coverage?.total ?? 0}`;
  }).join(" · ");
}

export function AdpProvidersPage({ client, data, onUpdate }: { client: NwrApiClient; data: RedraftBootstrap; onUpdate: (data: RedraftBootstrap) => void }) {
  const [working, setWorking] = useState("");
  const [error, setError] = useState<NwrApiError | null>(null);
  const [message, setMessage] = useState("");
  const [pasteText, setPasteText] = useState("");
  const [pasteLabel, setPasteLabel] = useState("Owner platform rankings");
  const [pastePreview, setPastePreview] = useState<PasteAdpPreview | null>(null);
  const activeProfile = data.activeProfile;
  const adp = data.draftBoard?.adp;
  const snapshot = data.ownerPlatformSnapshot;
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
  const preview = async () => {
    if (!activeProfile || !pasteText.trim() || working) return;
    setWorking("paste-preview"); setError(null); setMessage("");
    try {
      const result = await client.previewRedraftPasteAdp(activeProfile.profileId, pasteText, "CONSENSUS");
      setPastePreview(result.pastePreview);
      setMessage(`${result.pastePreview.parserMode === "PLAIN_TEXT_BLOCK" ? "Plain-text" : "Markdown"} parse: ${result.pastePreview.matchedRows}/${result.pastePreview.sourceRows} safe player matches.`);
    } catch (reason) { fail(reason, "The pasted platform table could not be parsed."); }
    finally { setWorking(""); }
  };
  const importCsv = async (file: File | undefined) => {
    if (!file || !activeProfile || working) return;
    await run("csv-import", () => file.text().then((csvText) => client.importRedraftAdp(activeProfile.profileId, csvText)), `Imported owner ADP from ${file.name}; NWR ranks did not change.`);
  };

  return <div className="adp-providers-page" aria-busy={Boolean(working)}>
    <PageHeader eyebrow={activeProfile ? `Active League · ${leagueFormat(activeProfile)}` : "Provider settings · local only"} title="ADP Providers" description="Manage draft-market timing separately from NWR rankings and projections. Changes here never write to Sleeper." status={<><StatusBadge tone={adp?.available ? "safe" : "review"} label={providerLabel(adp)} /><StatusBadge tone="safe" label="NWR ranks unchanged" /></>} />
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    <p aria-live="polite" className="profile-feedback">{message}</p>
    <Panel title="Active ADP source" eyebrow="Compact in Draft Room · detail here">
      <dl className="adp-details"><div><dt>Current source</dt><dd>{adp?.available ? adp.source : "No active ADP snapshot"}</dd></div><div><dt>Freshness</dt><dd>{adp?.freshness ?? "UNAVAILABLE"}</dd></div><div><dt>Source date</dt><dd>{adp?.dateWindow || adp?.sourceDate || "—"}</dd></div><div><dt>Player matches</dt><dd>{adp?.available ? `${adp.matchedPlayers}/${adp.sourcePlayers ?? adp.rankingPlayers}` : "—"}</dd></div><div><dt>Priority</dt><dd>Active owner platform column → Consensus → FFC → owner CSV → disclosed fallback</dd></div><div><dt>Boundary</dt><dd>Market timing only; NWR value rank and projections remain authoritative.</dd></div></dl>
      {adp?.lastRefreshError ? <p className="boundary-note">Last FFC refresh: {adp.lastRefreshError}</p> : null}
      <div className="profile-edit-actions"><Button disabled={!activeProfile || Boolean(working)} icon="activity" onClick={() => void run("adp-refresh", () => client.refreshRedraftAdp(activeProfile!.profileId), "Fantasy Football Calculator ADP refreshed locally. NWR ranks did not change.")}>{working === "adp-refresh" ? "Refreshing…" : "Refresh FFC ADP"}</Button><Button disabled={!activeProfile || Boolean(working)} icon="undo" variant="secondary" onClick={() => void run("paste-clear", () => client.clearRedraftPasteAdp(activeProfile!.profileId), "This league now uses its automatic platform column again. FFC remains the fallback.")}>{working === "paste-clear" ? "Clearing…" : "Clear league override"}</Button></div>
    </Panel>
    <div className="adp-provider-grid">
      <Panel title="Global Owner Platform Snapshot" eyebrow="Paste once · use across Redraft leagues">
        <p>Paste one full platform ADP table. NWR safely matches players once and stores the Consensus, Sleeper, ESPN, and FantasyPros columns together for every local Redraft league. It never changes rankings, projections, or Sleeper data.</p>
        <div className="form-grid"><label className="form-field"><span>Source label</span><input disabled={Boolean(working)} value={pasteLabel} onChange={(event) => setPasteLabel(event.target.value)} /></label><div className="form-field"><span>Parser modes</span><small>Markdown table first; plain-text player blocks are accepted when no table header is present.</small></div></div>
        <label className="form-field"><span>Platform rankings / ADP</span><textarea disabled={Boolean(working)} rows={10} value={pasteText} onChange={(event) => { setPasteText(event.target.value); setPastePreview(null); }} placeholder={"| Position | Player | Consensus | Sleeper | ESPN | FantasyPros |\n| --- | --- | ---: | ---: | ---: | ---: |\n| RB1 | Example Player | 3.2 | — | 4.1 | 3.7 |\n\nor plain text:\nWR13\nExample Player\n18.4 19.1 17.8 18.0"} /></label>
        <div className="profile-edit-actions"><Button disabled={!activeProfile || !pasteText.trim() || Boolean(working)} icon="activity" onClick={() => void preview()} variant="secondary">{working === "paste-preview" ? "Parsing…" : "Preview parse"}</Button><Button disabled={!activeProfile || !pasteText.trim() || Boolean(working)} icon="check" onClick={() => void run("paste-save", () => client.saveRedraftPasteAdp(activeProfile!.profileId, pasteText, "CONSENSUS", pasteLabel), "Global owner platform snapshot saved locally. Each league can now choose its column.")}>{working === "paste-save" ? "Saving…" : "Save global snapshot"}</Button></div>
        {pastePreview ? <div className="copy-muted"><strong>{pastePreview.parserMode === "PLAIN_TEXT_BLOCK" ? "Plain-text fallback" : "Markdown table"}: {pastePreview.matchedRows}/{pastePreview.sourceRows} safely matched; {pastePreview.skippedRows} skipped.</strong><small>{coverageText(pastePreview)}</small>{[...pastePreview.warnings, ...pastePreview.unmatched].slice(0, 12).map((warning) => <small key={warning}>{warning}</small>)}</div> : null}
        {snapshot?.available ? <p className="boundary-note">Stored snapshot: {snapshot.rowCount} rows, {snapshot.matchedRows ?? "—"} safe matches, {snapshot.parserMode || "unknown"} parser, hash {snapshot.rawHash.slice(0, 12)}…</p> : null}
      </Panel>
      <Panel title="League Platform Selection" eyebrow="Per league · global snapshot remains unchanged">
        <p>This league is detected as <strong>{snapshot?.detectedPlatform || "Consensus"}</strong>. Auto follows the connected provider: Sleeper → Sleeper, ESPN → ESPN, FantasyPros → FantasyPros, otherwise Consensus.</p>
        <label className="form-field"><span>Use platform ADP for this league</span><select disabled={!snapshot?.available || Boolean(working)} value={leagueSelection} onChange={(event) => setLeagueSelection(event.target.value as LeagueSelection)}><option value="AUTO">Auto (detected platform)</option><option value="CONSENSUS">Consensus</option><option value="SLEEPER">Sleeper</option><option value="ESPN">ESPN</option><option value="FANTASYPROS">FantasyPros</option><option value="DISABLED">Disabled / use FFC fallback</option></select></label>
        <p className="boundary-note">Missing selected-column values use Consensus, then FFC, then show unavailable. Sleeper is always owner-imported and read-only.</p>
        <div className="profile-edit-actions"><Button disabled={!activeProfile || !snapshot?.available || Boolean(working)} icon="draft" onClick={() => void run("platform-selection", () => client.setRedraftOwnerPlatformSelection(activeProfile!.profileId, leagueSelection), `Active platform selection set to ${leagueSelection === "AUTO" ? "Auto" : leagueSelection}.`)}>{working === "platform-selection" ? "Activating…" : "Activate for this league"}</Button></div>
      </Panel>
      <Panel title="Import owner ADP CSV" eyebrow="Local file · explicit import">
        <p>Import a local owner-provided ADP CSV when a platform export is more convenient than a paste. It affects market timing only.</p>
        <label className="file-action">Choose owner ADP CSV<input accept=".csv,text/csv" disabled={!activeProfile || Boolean(working)} onChange={(event) => void importCsv(event.target.files?.[0])} type="file" /></label>
        <p className="boundary-note">No provider import changes rankings, projections, CPU strategy rules, or Sleeper data.</p>
      </Panel>
    </div>
  </div>;
}
