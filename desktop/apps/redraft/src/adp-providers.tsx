import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { PasteAdpPreview, RedraftBootstrap } from "@nwr/contracts";
import { Button, ErrorState, PageHeader, Panel, StatusBadge } from "@nwr/ui";
import { useState } from "react";

import { leagueFormat } from "./league-context";

function providerLabel(adp: NonNullable<RedraftBootstrap["draftBoard"]>["adp"] | undefined) {
  if (!adp?.available) return "ADP: unavailable";
  const source = adp.source.replace(/^Owner-imported /i, "Owner ");
  return `ADP: ${source} · ${adp.freshness ?? "cached"}`;
}

export function AdpProvidersPage({ client, data, onUpdate }: { client: NwrApiClient; data: RedraftBootstrap; onUpdate: (data: RedraftBootstrap) => void }) {
  const [working, setWorking] = useState("");
  const [error, setError] = useState<NwrApiError | null>(null);
  const [message, setMessage] = useState("");
  const [pasteText, setPasteText] = useState("");
  const [pasteSource, setPasteSource] = useState<PasteAdpPreview["selectedSource"]>("CONSENSUS");
  const [pasteLabel, setPasteLabel] = useState("Owner platform rankings");
  const [pastePreview, setPastePreview] = useState<PasteAdpPreview | null>(null);
  const activeProfile = data.activeProfile;
  const adp = data.draftBoard?.adp;
  const fail = (reason: unknown, fallback: string) => setError(reason instanceof NwrApiError ? reason : new NwrApiError(fallback));
  const run = async (key: string, action: () => Promise<RedraftBootstrap>, success: string) => {
    if (!activeProfile || working) return;
    setWorking(key); setError(null); setMessage("");
    try { const next = await action(); onUpdate(next); setMessage(next.draftBoard?.adp?.lastRefreshError ? "FFC refresh failed; the last known good cached ADP remains active." : success); }
    catch (reason) { fail(reason, "The ADP provider action could not be completed."); }
    finally { setWorking(""); }
  };
  const preview = async () => {
    if (!activeProfile || !pasteText.trim() || working) return;
    setWorking("paste-preview"); setError(null); setMessage("");
    try { const result = await client.previewRedraftPasteAdp(activeProfile.profileId, pasteText, pasteSource); setPastePreview(result.pastePreview); setMessage(`Parsed ${result.pastePreview.matchedRows}/${result.pastePreview.sourceRows} safe player matches.`); }
    catch (reason) { fail(reason, "The pasted platform table could not be parsed."); }
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
      <dl className="adp-details"><div><dt>Current source</dt><dd>{adp?.available ? adp.source : "No active ADP snapshot"}</dd></div><div><dt>Freshness</dt><dd>{adp?.freshness ?? "UNAVAILABLE"}</dd></div><div><dt>Source date</dt><dd>{adp?.dateWindow || adp?.sourceDate || "—"}</dd></div><div><dt>Player matches</dt><dd>{adp?.available ? `${adp.matchedPlayers}/${adp.sourcePlayers ?? adp.rankingPlayers}` : "—"}</dd></div><div><dt>Priority</dt><dd>Active owner import → FFC → owner CSV → disclosed fallback</dd></div><div><dt>Boundary</dt><dd>Market timing only; NWR value rank and projections remain authoritative.</dd></div></dl>
      {adp?.lastRefreshError ? <p className="boundary-note">Last FFC refresh: {adp.lastRefreshError}</p> : null}
      <div className="profile-edit-actions"><Button disabled={!activeProfile || Boolean(working)} icon="activity" onClick={() => void run("adp-refresh", () => client.refreshRedraftAdp(activeProfile!.profileId), "Fantasy Football Calculator ADP refreshed locally. NWR ranks did not change.")}>{working === "adp-refresh" ? "Refreshing…" : "Refresh FFC ADP"}</Button><Button disabled={!activeProfile || Boolean(working)} icon="undo" variant="secondary" onClick={() => void run("paste-clear", () => client.clearRedraftPasteAdp(activeProfile!.profileId), "Active imported ranking cleared. FFC remains the default when available.")}>Clear active provider</Button></div>
    </Panel>
    <div className="adp-provider-grid">
      <Panel title="Paste Rankings / ADP" eyebrow="Owner-imported market timing · local snapshot">
        <p>Paste rankings from your platform table. Choose which column is active: Consensus, Sleeper, ESPN, or FantasyPros. This changes draft-market timing only; NWR rankings and projections do not change.</p>
        <div className="form-grid"><label className="form-field"><span>Source label</span><input disabled={Boolean(working)} value={pasteLabel} onChange={(event) => setPasteLabel(event.target.value)} /></label><label className="form-field"><span>Active platform column</span><select disabled={Boolean(working)} value={pasteSource} onChange={(event) => setPasteSource(event.target.value as PasteAdpPreview["selectedSource"])}><option value="CONSENSUS">Consensus</option><option value="SLEEPER">Sleeper</option><option value="ESPN">ESPN</option><option value="FANTASYPROS">FantasyPros</option></select></label></div>
        <p className="boundary-note">Sleeper selection is labeled <strong>Owner-imported Sleeper ADP</strong>. It uses pasted owner data only; NWR does not call or write to a Sleeper ADP API.</p>
        <label className="form-field"><span>Markdown platform table</span><textarea disabled={Boolean(working)} rows={9} value={pasteText} onChange={(event) => { setPasteText(event.target.value); setPastePreview(null); }} placeholder="| Position | Player | Consensus | Sleeper | ESPN | FantasyPros |\n| --- | --- | ---: | ---: | ---: | ---: |\n| RB1 | Example Player | 3.2 | — | 4.1 | 3.7 |" /></label>
        <div className="profile-edit-actions"><Button disabled={!activeProfile || !pasteText.trim() || Boolean(working)} icon="activity" onClick={() => void preview()} variant="secondary">{working === "paste-preview" ? "Parsing…" : "Preview parse"}</Button><Button disabled={!activeProfile || !pasteText.trim() || Boolean(working)} icon="check" onClick={() => void run("paste-save", () => client.saveRedraftPasteAdp(activeProfile!.profileId, pasteText, pasteSource, pasteLabel), "Pasted platform ADP snapshot saved locally. Activate it to use it for timing.")}>{working === "paste-save" ? "Saving…" : "Save snapshot"}</Button><Button disabled={!activeProfile || Boolean(working)} icon="draft" onClick={() => void run("paste-activate", () => client.activateRedraftPasteAdp(activeProfile!.profileId), "Owner-imported platform ADP is active for market timing. NWR ranks did not change.")}>{working === "paste-activate" ? "Activating…" : "Activate for Fantasy Gamers"}</Button></div>
        {pastePreview ? <div className="copy-muted"><strong>Preview: {pastePreview.matchedRows}/{pastePreview.sourceRows} safely matched; {pastePreview.skippedRows} skipped.</strong>{[...pastePreview.warnings, ...pastePreview.unmatched].slice(0, 20).map((warning) => <small key={warning}>{warning}</small>)}</div> : null}
      </Panel>
      <Panel title="Import owner ADP CSV" eyebrow="Local file · explicit import">
        <p>Import a local owner-provided ADP CSV when a platform export is more convenient than a paste. It affects market timing only.</p>
        <label className="file-action">Choose owner ADP CSV<input accept=".csv,text/csv" disabled={!activeProfile || Boolean(working)} onChange={(event) => void importCsv(event.target.files?.[0])} type="file" /></label>
        <p className="boundary-note">The active-source priority is always visible above. No provider import changes rankings, projections, CPU strategy rules, or Sleeper data.</p>
      </Panel>
    </div>
  </div>;
}
