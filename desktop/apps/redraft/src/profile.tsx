import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type {
  LeagueProfile,
  PasteAdpPreview,
  RedraftBootstrap,
  RedraftProfileUpdateInput,
} from "@nwr/contracts";
import { Button, ErrorState, Icon, PageHeader, Panel, StatusBadge } from "@nwr/ui";
import { useEffect, useState } from "react";

import { leagueFormat, leagueIdentityFormat } from "./league-context";

function editableProfile(profile: LeagueProfile): RedraftProfileUpdateInput {
  return {
    leagueName: profile.leagueName,
    teamCount: profile.teamCount,
    roster: {
      qb: profile.roster.qb,
      rb: profile.roster.rb,
      wr: profile.roster.wr,
      te: profile.roster.te,
      flex: profile.roster.flex,
      superflex: profile.roster.superflex,
      k: profile.roster.k,
      dst: profile.roster.dst,
      benchSize: profile.roster.benchSize,
    },
    scoring: {
      reception: profile.scoring.reception,
      passingTd: profile.scoring.passingTd,
      interception: profile.scoring.interception,
      tePremium: profile.scoring.tePremium,
    },
    draft: {
      rounds: profile.draft.rounds,
      draftSlot: profile.draft.draftSlot,
      replacementMethod: profile.draft.replacementMethod,
    },
  };
}

export function ProfilePage({
  client,
  data,
  onUpdate,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
}) {
  const [preset, setPreset] = useState(data.presets[0]?.presetKey ?? "");
  const [name, setName] = useState(data.presets[0]?.leagueName ?? "My Redraft League");
  const [edit, setEdit] = useState<RedraftProfileUpdateInput | null>(
    data.activeProfile ? editableProfile(data.activeProfile) : null,
  );
  const [working, setWorking] = useState("");
  const [error, setError] = useState<NwrApiError | null>(null);
  const [message, setMessage] = useState("");
  const [sleeperLeagueId, setSleeperLeagueId] = useState("1312983576827920384");
  const [sleeperUsername, setSleeperUsername] = useState("scolety");
  const [pasteText, setPasteText] = useState("");
  const [pasteSource, setPasteSource] = useState<PasteAdpPreview["selectedSource"]>("CONSENSUS");
  const [pasteLabel, setPasteLabel] = useState("Owner platform rankings");
  const [pastePreview, setPastePreview] = useState<PasteAdpPreview | null>(null);

  useEffect(() => {
    setEdit(data.activeProfile ? editableProfile(data.activeProfile) : null);
  }, [data.activeProfile]);

  const fail = (reason: unknown, fallback: string) => {
    setError(reason instanceof NwrApiError ? reason : new NwrApiError(fallback));
  };
  const create = async () => {
    if (!preset || !name.trim() || working) return;
    setWorking("create"); setError(null); setMessage("");
    try {
      onUpdate(await client.createRedraftProfile(preset, name));
      setMessage("Profile created and activated.");
    } catch (reason) { fail(reason, "Profile could not be created."); }
    finally { setWorking(""); }
  };
  const activate = async (profile: LeagueProfile) => {
    if (working) return;
    setWorking(`activate:${profile.profileId}`); setError(null); setMessage("");
    try {
      onUpdate(await client.activateRedraftProfile(profile.profileId));
      setMessage(`${profile.leagueName} is active.`);
    } catch (reason) { fail(reason, "Profile could not be activated."); }
    finally { setWorking(""); }
  };
  const duplicate = async () => {
    if (!data.activeProfile || working) return;
    setWorking("duplicate"); setError(null); setMessage("");
    try {
      onUpdate(await client.duplicateRedraftProfile(data.activeProfile.profileId));
      setMessage("Profile duplicated and activated. Its draft board starts empty.");
    } catch (reason) { fail(reason, "Profile could not be duplicated."); }
    finally { setWorking(""); }
  };
  const importSleeper = async () => {
    if (!sleeperLeagueId.trim() || !sleeperUsername.trim() || working) return;
    setWorking("sleeper-import"); setError(null); setMessage("");
    try {
      onUpdate(await client.importSleeperRedraftProfile(sleeperLeagueId.trim(), sleeperUsername.trim()));
      setMessage("Sleeper league imported locally. Any unsupported scoring fields are shown in the data-health notices; no Sleeper data was changed.");
    } catch (reason) { fail(reason, "Sleeper league could not be imported."); }
    finally { setWorking(""); }
  };
  const save = async () => {
    if (!data.activeProfile || !edit || working) return;
    setWorking("save"); setError(null); setMessage("");
    try {
      onUpdate(await client.updateRedraftProfile(data.activeProfile.profileId, edit));
      setMessage("Scoring, roster, and draft settings saved. Rankings were refreshed.");
    } catch (reason) { fail(reason, "Profile settings could not be saved."); }
    finally { setWorking(""); }
  };
  const startPracticalMock = async () => {
    if (!data.activeProfile || working) return;
    setWorking("practical"); setError(null); setMessage("");
    try {
      onUpdate(await client.startPracticalMock(data.activeProfile.profileId));
      setMessage("Practical Mock is ready. Five uncommon scoring events remain omitted; K/DST are manual and unmodeled.");
    } catch (reason) { fail(reason, "Practical Mock could not start."); }
    finally { setWorking(""); }
  };
  const refreshAdp = async () => {
    if (!data.activeProfile || working) return;
    setWorking("adp-refresh"); setError(null); setMessage("");
    try {
      const next = await client.refreshRedraftAdp(data.activeProfile.profileId);
      onUpdate(next);
      setMessage(next.draftBoard?.adp?.lastRefreshError ? "FFC refresh failed; the last known good cached ADP remains active." : "Fantasy Football Calculator ADP refreshed locally. NWR rankings were not changed.");
    } catch (reason) { fail(reason, "Fantasy Football Calculator ADP could not be refreshed."); }
    finally { setWorking(""); }
  };
  const previewPasteAdp = async () => {
    if (!data.activeProfile || !pasteText.trim() || working) return;
    setWorking("paste-preview"); setError(null); setMessage("");
    try {
      const result = await client.previewRedraftPasteAdp(data.activeProfile.profileId, pasteText, pasteSource);
      setPastePreview(result.pastePreview);
      setMessage(`Parsed ${result.pastePreview.matchedRows} safe player matches. Review warnings before saving.`);
    } catch (reason) { fail(reason, "The pasted platform ADP table could not be parsed."); }
    finally { setWorking(""); }
  };
  const savePasteAdp = async () => {
    if (!data.activeProfile || !pasteText.trim() || working) return;
    setWorking("paste-save"); setError(null); setMessage("");
    try {
      onUpdate(await client.saveRedraftPasteAdp(data.activeProfile.profileId, pasteText, pasteSource, pasteLabel));
      setMessage("Pasted platform ADP snapshot saved locally. Activate it to override FFC timing.");
    } catch (reason) { fail(reason, "The pasted platform ADP snapshot could not be saved."); }
    finally { setWorking(""); }
  };
  const activatePasteAdp = async () => {
    if (!data.activeProfile || working) return;
    setWorking("paste-activate"); setError(null); setMessage("");
    try { onUpdate(await client.activateRedraftPasteAdp(data.activeProfile.profileId)); setMessage("Owner-imported platform ADP is active for market timing. NWR ranks did not change."); }
    catch (reason) { fail(reason, "The pasted platform ADP snapshot could not be activated."); }
    finally { setWorking(""); }
  };
  const clearPasteAdp = async () => {
    if (!data.activeProfile || working) return;
    setWorking("paste-clear"); setError(null); setMessage("");
    try { onUpdate(await client.clearRedraftPasteAdp(data.activeProfile.profileId)); setMessage("Active pasted platform ADP cleared. FFC remains the default when available."); }
    catch (reason) { fail(reason, "The active pasted platform ADP snapshot could not be cleared."); }
    finally { setWorking(""); }
  };

  const profileCount = data.profiles.length;
  const profileLabel = `${profileCount} profile${profileCount === 1 ? "" : "s"} · ${data.activeProfileId ? "active" : "none active"}`;
  return <>
    <PageHeader eyebrow={data.activeProfile ? `Active League · ${leagueFormat(data.activeProfile)}` : "League management · Local and isolated"} title="League Profiles & Scoring" description="Switch, import, and inspect each Redraft league. Scoring, roster demand, Sleeper context, and draft state remain isolated." status={<><StatusBadge tone="safe" label={profileLabel} /><StatusBadge tone="safe" label="Redraft only" /></>} />
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    <p aria-live="polite" className="profile-feedback">{message}</p>
    <div className="profile-layout">
      <Panel title="Your leagues" eyebrow="Current-season profiles">
        <div className="profile-list">
          {data.profiles.map((profile) => <button className={profile.profileId === data.activeProfileId ? "active" : ""} disabled={Boolean(working)} key={profile.profileId} onClick={() => void activate(profile)}><span><Icon name="trophy" /></span><div><strong>{profile.leagueName}</strong><small>{leagueFormat(profile)}</small><small>{leagueIdentityFormat(profile)}</small></div>{profile.profileId === data.activeProfileId ? <em>Active</em> : <Icon name="chevron" size={13} />}</button>)}
          {!data.profiles.length ? <p className="copy-muted">No profile exists yet. Create one from a validated preset.</p> : null}
        </div>
      </Panel>
      <Panel title="Create from preset" eyebrow="Fast setup">
        <div className="form-grid">
          <label className="form-field"><span>Preset</span><select disabled={Boolean(working)} value={preset ?? ""} onChange={(event) => { setPreset(event.target.value); const match = data.presets.find((item) => item.presetKey === event.target.value); if (match) setName(match.leagueName); }}>{data.presets.map((item) => <option key={item.presetKey} value={item.presetKey ?? ""}>{item.leagueName}</option>)}</select></label>
          <label className="form-field"><span>League name</span><input disabled={Boolean(working)} maxLength={120} value={name} onChange={(event) => setName(event.target.value)} /></label>
        </div>
        <div className="profile-create-footer"><p>Creates a separate profile and makes it active.</p><Button disabled={!preset || !name.trim() || Boolean(working)} icon="profile" onClick={() => void create()}>{working === "create" ? "Saving…" : "Create & activate"}</Button></div>
      </Panel>
      <Panel title="Import from Sleeper" eyebrow="Read-only league profile">
        <div className="form-grid">
          <label className="form-field"><span>League ID</span><input disabled={Boolean(working)} value={sleeperLeagueId} onChange={(event) => setSleeperLeagueId(event.target.value)} /></label>
          <label className="form-field"><span>Sleeper username</span><input disabled={Boolean(working)} value={sleeperUsername} onChange={(event) => setSleeperUsername(event.target.value)} /></label>
        </div>
        <div className="profile-create-footer"><p>Reads league settings once, creates an isolated local Redraft profile, and never makes a Sleeper pick or roster change.</p><Button disabled={!sleeperLeagueId.trim() || !sleeperUsername.trim() || Boolean(working)} icon="profile" onClick={() => void importSleeper()}>{working === "sleeper-import" ? "Importing…" : "Import & activate"}</Button></div>
      </Panel>
      <Panel title="Practical Mock Mode" eyebrow="Owner-authorized · Fantasy Gamers">
        <p>NWR models the major QB/RB/WR/TE scoring rules for Fantasy Gamers. Five uncommon scoring events are not included. Kicker and DST are manual/unmodeled.</p>
        <div className="profile-create-footer"><p>{data.activeProfile?.practicalMode ? "Practical Mode is active. Use Draft Room to search and draft manual K/DST assets." : "Refreshes public Sleeper K/DST identities locally and enables this approximate profile."}</p><Button disabled={!data.activeProfile || data.activeProfile.practicalMode || Boolean(working)} icon="draft" onClick={() => void startPracticalMock()}>{working === "practical" ? "Starting…" : "Start Practical Mock"}</Button></div>
      </Panel>
      <Panel title="ADP Provider" eyebrow="External market timing · local cache">
        <p>Fantasy Football Calculator ADP is the default external 10-team PPR timing source. It never changes NWR rank or projections.</p>
        <div className="profile-create-footer"><p>{data.draftBoard?.adp?.available ? `${data.draftBoard.adp.freshness ?? "CACHED"} · ${data.draftBoard.adp.dateWindow || data.draftBoard.adp.sourceDate}${data.draftBoard.adp.sampleSize ? ` · ${data.draftBoard.adp.sampleSize.toLocaleString()} drafts` : ""}` : "No cached ADP snapshot. Draft Room remains usable with disclosed fallback behavior."}</p><Button disabled={!data.activeProfile || Boolean(working)} icon="activity" onClick={() => void refreshAdp()}>{working === "adp-refresh" ? "Refreshing…" : "Refresh FFC ADP"}</Button></div>
      </Panel>
      <Panel title="Paste Rankings / Platform ADP" eyebrow="Owner-imported market timing · local snapshot">
        <p>Paste a stable markdown pipe table. This is market timing only: it never changes NWR rankings, projections, or Sleeper data.</p>
        <div className="form-grid">
          <label className="form-field"><span>Source label</span><input disabled={Boolean(working)} value={pasteLabel} onChange={(event) => setPasteLabel(event.target.value)} /></label>
          <label className="form-field"><span>Selected ADP column</span><select disabled={Boolean(working)} value={pasteSource} onChange={(event) => setPasteSource(event.target.value as PasteAdpPreview["selectedSource"])}><option value="CONSENSUS">Consensus</option><option value="SLEEPER">Sleeper</option><option value="ESPN">ESPN</option><option value="FANTASYPROS">FantasyPros</option></select></label>
          <label className="form-field"><span>League context</span><input disabled value="PPR · 10 teams · 2026" /></label>
        </div>
        <label className="form-field"><span>Markdown table</span><textarea disabled={Boolean(working)} rows={9} value={pasteText} onChange={(event) => { setPasteText(event.target.value); setPastePreview(null); }} placeholder="| Position | Player | Consensus | Sleeper | ESPN | FantasyPros |\n| --- | --- | ---: | ---: | ---: | ---: |\n| RB1 | Example Player | 3.2 | — | 4.1 | 3.7 |" /></label>
        <div className="profile-create-footer"><p>Unknown, blank, dash, or em dash values are never treated as zero. Save keeps the original text locally; activation is explicit.</p><span><Button disabled={!data.activeProfile || !pasteText.trim() || Boolean(working)} icon="activity" onClick={() => void previewPasteAdp()} variant="secondary">{working === "paste-preview" ? "Parsing…" : "Preview parse"}</Button><Button disabled={!data.activeProfile || !pasteText.trim() || Boolean(working)} icon="check" onClick={() => void savePasteAdp()}>{working === "paste-save" ? "Saving…" : "Save snapshot"}</Button><Button disabled={!data.activeProfile || Boolean(working)} icon="draft" onClick={() => void activatePasteAdp()}>{working === "paste-activate" ? "Activating…" : "Activate for Fantasy Gamers"}</Button><Button disabled={!data.activeProfile || Boolean(working)} icon="undo" onClick={() => void clearPasteAdp()} variant="secondary">Clear active imported ranking</Button></span></div>
        {pastePreview ? <div className="copy-muted"><strong>Preview: {pastePreview.matchedRows}/{pastePreview.sourceRows} safely matched; {pastePreview.skippedRows} skipped.</strong>{[...pastePreview.warnings, ...pastePreview.unmatched].slice(0, 20).map((warning) => <small key={warning}>{warning}</small>)}</div> : null}
      </Panel>
    </div>
    {data.activeProfile && edit ? <ProfileEditor edit={edit} disabled={Boolean(working)} onChange={setEdit} onDuplicate={() => void duplicate()} onSave={() => void save()} working={working} /> : null}
  </>;
}

function ProfileEditor({ edit, disabled, onChange, onDuplicate, onSave, working }: { edit: RedraftProfileUpdateInput; disabled: boolean; onChange: (value: RedraftProfileUpdateInput) => void; onDuplicate: () => void; onSave: () => void; working: string }) {
  const number = (value: string) => Number(value);
  const rosterField = (key: keyof RedraftProfileUpdateInput["roster"], label: string) => <label className="form-field"><span>{label}</span><input disabled={disabled} min={0} max={40} type="number" value={edit.roster[key]} onChange={(event) => onChange({ ...edit, roster: { ...edit.roster, [key]: number(event.target.value) } })} /></label>;
  const scoringField = (key: keyof RedraftProfileUpdateInput["scoring"], label: string, step = 0.5) => <label className="form-field"><span>{label}</span><input disabled={disabled} step={step} type="number" value={edit.scoring[key]} onChange={(event) => onChange({ ...edit, scoring: { ...edit.scoring, [key]: number(event.target.value) } })} /></label>;
  return <Panel title="Edit active profile" eyebrow="Validated scoring · roster · draft settings">
    <div className="profile-edit-grid">
      <label className="form-field"><span>League name</span><input disabled={disabled} maxLength={120} value={edit.leagueName} onChange={(event) => onChange({ ...edit, leagueName: event.target.value })} /></label>
      <label className="form-field"><span>Teams</span><input disabled={disabled} min={2} max={32} type="number" value={edit.teamCount} onChange={(event) => onChange({ ...edit, teamCount: number(event.target.value) })} /></label>
      {rosterField("qb", "QB")}{rosterField("rb", "RB")}{rosterField("wr", "WR")}{rosterField("te", "TE")}{rosterField("flex", "Flex")}{rosterField("superflex", "Superflex")}{rosterField("k", "K")}{rosterField("dst", "DST")}{rosterField("benchSize", "Bench")}
      {scoringField("reception", "Reception")}{scoringField("passingTd", "Passing TD")}{scoringField("interception", "Interception")}{scoringField("tePremium", "TE premium")}
      <label className="form-field"><span>Draft rounds</span><input disabled={disabled} min={1} max={40} type="number" value={edit.draft.rounds} onChange={(event) => onChange({ ...edit, draft: { ...edit.draft, rounds: number(event.target.value) } })} /></label>
      <label className="form-field"><span>Draft slot</span><input disabled={disabled} min={1} max={edit.teamCount} placeholder="Optional" type="number" value={edit.draft.draftSlot ?? ""} onChange={(event) => onChange({ ...edit, draft: { ...edit.draft, draftSlot: event.target.value ? number(event.target.value) : null } })} /></label>
      <label className="form-field"><span>Replacement method</span><select disabled={disabled} value={edit.draft.replacementMethod} onChange={(event) => onChange({ ...edit, draft: { ...edit.draft, replacementMethod: event.target.value as RedraftProfileUpdateInput["draft"]["replacementMethod"] } })}><option value="expected_available">Expected available</option><option value="starter_cutoff">Starter cutoff</option></select></label>
    </div>
    <div className="profile-edit-actions"><Button disabled={disabled || !edit.leagueName.trim()} icon="check" onClick={onSave}>{working === "save" ? "Saving…" : "Save & refresh rankings"}</Button><Button disabled={disabled} icon="layers" onClick={onDuplicate} variant="secondary">{working === "duplicate" ? "Duplicating…" : "Duplicate profile"}</Button></div>
  </Panel>;
}
