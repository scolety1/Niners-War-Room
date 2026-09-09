import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { LeagueProfile, RedraftBootstrap, RedraftProfileUpdateInput } from "@nwr/contracts";
import { Button, ErrorState, Icon, PageHeader, Panel, StatusBadge } from "@nwr/ui";
import { useEffect, useState } from "react";

import { leagueFormat, leagueIdentityFormat } from "./league-context";

type EditableProfile = Omit<RedraftProfileUpdateInput, "draft"> & {
  draft: RedraftProfileUpdateInput["draft"] & { rosterLimits?: Record<string, number> };
};

function editableProfile(profile: LeagueProfile): EditableProfile {
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
      // The wire shape is a LIST of {position, maximum} (never an object
      // keyed by the literal position code -- see DraftContext.rosterLimits'
      // own comment in @nwr/contracts for the real camelCase-key
      // serialization bug this avoids). Converted to a Record here purely
      // for this editor's own convenient internal state; the save call
      // below sends the Record form straight back, which the update
      // REQUEST body already expects unchanged.
      rosterLimits: Object.fromEntries(profile.draft.rosterLimits.map((entry) => [entry.position, entry.maximum])),
    },
    practicalMode: profile.practicalMode,
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
  const [edit, setEdit] = useState<EditableProfile | null>(
    data.activeProfile ? editableProfile(data.activeProfile) : null,
  );
  const [working, setWorking] = useState("");
  const [error, setError] = useState<NwrApiError | null>(null);
  const [message, setMessage] = useState("");
  const [sleeperLeagueId, setSleeperLeagueId] = useState("1312983576827920384");
  const [sleeperUsername, setSleeperUsername] = useState("scolety");

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
  const refreshSleeper = async () => {
    if (!data.activeProfile || data.activeProfile.provider !== "sleeper" || working) return;
    setWorking("sleeper-resync"); setError(null); setMessage("");
    try {
      onUpdate(await client.resyncSleeperRedraftProfile(data.activeProfile.profileId));
      setMessage("Sleeper league settings and your current roster were refreshed locally. No Sleeper data was changed.");
    } catch (reason) { fail(reason, "Sleeper league could not be refreshed."); }
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
        {data.activeProfile?.provider === "sleeper" ? <div className="profile-create-footer"><p>Refresh league settings and your stored roster from Sleeper's read-only API.</p><Button disabled={Boolean(working)} icon="activity" onClick={() => void refreshSleeper()}>{working === "sleeper-resync" ? "Refreshing…" : "Refresh from Sleeper"}</Button></div> : null}
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
    </div>
    {data.activeProfile && edit ? <ProfileEditor edit={edit} disabled={Boolean(working)} onChange={setEdit} onDuplicate={() => void duplicate()} onSave={() => void save()} working={working} /> : null}
  </>;
}

function ProfileEditor({ edit, disabled, onChange, onDuplicate, onSave, working }: { edit: EditableProfile; disabled: boolean; onChange: (value: EditableProfile) => void; onDuplicate: () => void; onSave: () => void; working: string }) {
  const number = (value: string) => Number(value);
  const rosterField = (key: keyof RedraftProfileUpdateInput["roster"], label: string) => <label className="form-field"><span>{label}</span><input disabled={disabled} min={0} max={40} type="number" value={edit.roster[key]} onChange={(event) => onChange({ ...edit, roster: { ...edit.roster, [key]: number(event.target.value) } })} /></label>;
  const scoringField = (key: keyof RedraftProfileUpdateInput["scoring"], label: string, step = 0.5) => <label className="form-field"><span>{label}</span><input disabled={disabled} step={step} type="number" value={edit.scoring[key]} onChange={(event) => onChange({ ...edit, scoring: { ...edit.scoring, [key]: number(event.target.value) } })} /></label>;
  const rosterLimitField = (position: string) => <label className="form-field" key={`max-${position}`}><span>{position} maximum</span><input disabled={disabled} min={0} max={40} placeholder="Not configured" type="number" value={edit.draft.rosterLimits?.[position] ?? ""} onChange={(event) => {
    const limits = { ...(edit.draft.rosterLimits ?? {}) };
    if (event.target.value === "") delete limits[position];
    else limits[position] = number(event.target.value);
    onChange({ ...edit, draft: { ...edit.draft, rosterLimits: limits } });
  }} /></label>;
  return <Panel title="Edit active profile" eyebrow="Validated scoring · roster · draft settings">
    <div className="profile-edit-grid">
      <label className="form-field"><span>League name</span><input disabled={disabled} maxLength={120} value={edit.leagueName} onChange={(event) => onChange({ ...edit, leagueName: event.target.value })} /></label>
      <label className="form-field"><span>Teams</span><input disabled={disabled} min={2} max={32} type="number" value={edit.teamCount} onChange={(event) => onChange({ ...edit, teamCount: number(event.target.value) })} /></label>
      {rosterField("qb", "QB")}{rosterField("rb", "RB")}{rosterField("wr", "WR")}{rosterField("te", "TE")}{rosterField("flex", "Flex")}{rosterField("superflex", "Superflex")}{rosterField("k", "K")}{rosterField("dst", "DST")}{rosterField("benchSize", "Bench")}
      {(edit.roster.k > 0 || edit.roster.dst > 0) ? (
        // NWR LAST PRE-DRAFT BLOCKER CLOSURE (section 1, "remove the
        // owner Practical Mode footgun"): a K/DST roster slot now works
        // automatically -- ranking generation no longer requires this
        // flag at all (see the real fix in redraft_engine_v1_service.py:
        // K/DST are structurally exempt from the ranked-coverage check
        // whenever the roster configures them, unconditionally). This
        // toggle keeps its own real, separate, narrower meaning (gates
        // the standalone "Start Practical Mock" QA simulator below, and
        // the "PRACTICAL SCORING" disclosure notice) -- moved into a
        // details disclosure, off the primary form, since normal draft
        // setup no longer depends on it.
        <details className="form-field form-field--details">
          <summary>Advanced: Practical Mock settings</summary>
          <label className="form-field form-field--checkbox" title="K/DST roster slots already work without this. This only affects the separate 'Start Practical Mock' QA simulator below and its scoring disclosure -- not live Draft Room ranking or Suggestions.">
            <input disabled={disabled} type="checkbox" checked={edit.practicalMode ?? false} onChange={(event) => onChange({ ...edit, practicalMode: event.target.checked })} />
            <span>Practical Mode (only affects the separate Practical Mock QA simulator -- K/DST already draft normally without this)</span>
          </label>
        </details>
      ) : null}
      {scoringField("reception", "Reception")}{scoringField("passingTd", "Passing TD")}{scoringField("interception", "Interception")}{scoringField("tePremium", "TE premium")}
      <label className="form-field"><span>Draft rounds</span><input disabled={disabled} min={1} max={40} type="number" value={edit.draft.rounds} onChange={(event) => onChange({ ...edit, draft: { ...edit.draft, rounds: number(event.target.value) } })} /></label>
      <label className="form-field"><span>Draft slot</span><input disabled={disabled} min={1} max={edit.teamCount} placeholder="Optional" type="number" value={edit.draft.draftSlot ?? ""} onChange={(event) => onChange({ ...edit, draft: { ...edit.draft, draftSlot: event.target.value ? number(event.target.value) : null } })} /></label>
      <label className="form-field"><span>Replacement method</span><select disabled={disabled} value={edit.draft.replacementMethod} onChange={(event) => onChange({ ...edit, draft: { ...edit.draft, replacementMethod: event.target.value as RedraftProfileUpdateInput["draft"]["replacementMethod"] } })}><option value="expected_available">Expected available</option><option value="starter_cutoff">Starter cutoff</option></select></label>
      {(() => {
        const positions = ["QB", "RB", "WR", "TE", "K", "DST"];
        const unsupplied = positions.filter((position) => edit.draft.rosterLimits?.[position] === undefined);
        // Visible without expanding the details below -- an unconfigured
        // position has NO invented hard maximum; legality falls back to
        // total roster capacity and required-slot feasibility only, and
        // NWR's strategic marginal-value signal (not a fabricated legal
        // cap) is what actually discourages over-drafting that position.
        return (
          <div className="form-field form-field--full">
            <StatusBadge
              tone={unsupplied.length ? "review" : "safe"}
              label={unsupplied.length ? `Position maximums: Not supplied (${unsupplied.join(", ")})` : "Position maximums: All supplied"}
            />
          </div>
        );
      })()}
      <details className="form-field form-field--details">
        <summary>League position maxima</summary>
        <p>Enter the draft platform's actual limits. Blank means unknown; NWR will not invent one.</p>
        <div className="profile-edit-grid">
          {["QB", "RB", "WR", "TE", "K", "DST"].map(rosterLimitField)}
        </div>
      </details>
    </div>
    <div className="profile-edit-actions"><Button disabled={disabled || !edit.leagueName.trim()} icon="check" onClick={onSave}>{working === "save" ? "Saving…" : "Save & refresh rankings"}</Button><Button disabled={disabled} icon="layers" onClick={onDuplicate} variant="secondary">{working === "duplicate" ? "Duplicating…" : "Duplicate profile"}</Button></div>
  </Panel>;
}
