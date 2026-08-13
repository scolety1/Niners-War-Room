import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type {
  DynastyBootstrap,
  DynastyWorkspace,
  OwnerDecisionType,
  PersonalBoardInput,
  WorkspaceTeamWindow,
} from "@nwr/contracts";
import { Button, EmptyState, ErrorState, PageHeader, Panel, StatusBadge } from "@nwr/ui";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

const TEAM_WINDOWS: WorkspaceTeamWindow[] = [
  "Contending",
  "Balanced",
  "Rebuilding",
  "Custom/Unspecified",
];
const DECISION_TYPES: Array<{ value: OwnerDecisionType; label: string }> = [
  { value: "player evaluation", label: "Player evaluation" },
  { value: "draft target", label: "Draft target" },
  { value: "roster cut", label: "Roster cut" },
  { value: "waiver target", label: "Waiver target" },
  { value: "custom note", label: "Custom note" },
];

function boardDraft(assetId: string, workspace: DynastyWorkspace | null): PersonalBoardInput {
  const prior = workspace?.personalBoard.find((row) => row.assetId === assetId);
  return {
    assetId,
    watchlist: prior?.watchlist ?? false,
    target: prior?.target ?? false,
    avoid: prior?.avoid ?? false,
    tags: prior?.tags ?? [],
    notes: prior?.notes ?? "",
    teamWindow: prior?.teamWindow ?? "Custom/Unspecified",
  };
}

export function TeamWorkspacePage({
  client,
  data,
}: {
  client: NwrApiClient;
  data: DynastyBootstrap;
}) {
  const [searchParams] = useSearchParams();
  const requestedAsset = searchParams.get("asset");
  const defaultAsset = data.assetOptions.some((row) => row.assetId === requestedAsset)
    ? requestedAsset!
    : data.assetOptions[0]?.assetId ?? "";
  const [workspace, setWorkspace] = useState<DynastyWorkspace | null>(null);
  const [assetId, setAssetId] = useState(defaultAsset);
  const [board, setBoard] = useState<PersonalBoardInput>(() => boardDraft(defaultAsset, null));
  const [tagsText, setTagsText] = useState("");
  const [decisionTitle, setDecisionTitle] = useState("");
  const [decisionType, setDecisionType] = useState<OwnerDecisionType>("player evaluation");
  const [decisionAsset, setDecisionAsset] = useState(defaultAsset);
  const [rationale, setRationale] = useState("");
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState<NwrApiError | null>(null);
  const options = useMemo(
    () => data.assetOptions.slice().sort((a, b) => a.name.localeCompare(b.name)),
    [data.assetOptions],
  );

  useEffect(() => {
    let active = true;
    setError(null);
    void client
      .loadDynastyWorkspace()
      .then((value) => { if (active) setWorkspace(value); })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof NwrApiError ? reason : new NwrApiError("Personal Workspace could not be loaded."));
      });
    return () => { active = false; };
  }, [client]);

  useEffect(() => {
    const next = boardDraft(assetId, workspace);
    setBoard(next);
    setTagsText(next.tags.join(", "));
  }, [assetId, workspace]);

  const fail = (reason: unknown, fallback: string) => {
    setError(reason instanceof NwrApiError ? reason : new NwrApiError(fallback));
  };
  const saveBoard = async () => {
    if (!assetId || busy) return;
    setBusy("board"); setError(null); setMessage("");
    try {
      const next = await client.savePersonalBoardEntry({
        ...board,
        assetId,
        tags: tagsText.split(",").map((value) => value.trim()).filter(Boolean),
      });
      setWorkspace(next);
      setMessage("Personal Board entry saved locally.");
    } catch (reason) { fail(reason, "Personal Board entry could not be saved."); }
    finally { setBusy(""); }
  };
  const saveDecision = async () => {
    if (!decisionTitle.trim() || !decisionAsset || !rationale.trim() || busy) return;
    setBusy("decision"); setError(null); setMessage("");
    try {
      const next = await client.createOwnerDecision({
        title: decisionTitle.trim(),
        decisionType,
        assetIds: [decisionAsset],
        rationale: rationale.trim(),
      });
      setWorkspace(next);
      setDecisionTitle(""); setRationale("");
      setMessage("Decision saved to the local journal.");
    } catch (reason) { fail(reason, "Decision could not be saved."); }
    finally { setBusy(""); }
  };
  const backup = async () => {
    if (busy) return;
    setBusy("backup"); setError(null); setMessage("");
    try {
      const next = await client.backupDynastyWorkspace();
      setWorkspace(next); setMessage("Verified local backup created.");
    } catch (reason) { fail(reason, "NWR could not create a local backup."); }
    finally { setBusy(""); }
  };
  const checkRestore = async () => {
    if (busy) return;
    setBusy("check"); setError(null); setMessage("");
    try {
      const next = await client.checkDynastyWorkspaceRestore();
      setWorkspace(next); setMessage(next.backup.message);
    } catch (reason) { fail(reason, "NWR could not verify the latest backup."); }
    finally { setBusy(""); }
  };
  const adoptLegacy = async () => {
    if (busy || workspace?.storeStatus !== "empty") return;
    setBusy("adopt"); setError(null); setMessage("");
    try {
      const next = await client.adoptLegacyDynastyWorkspace();
      setWorkspace(next); setMessage(next.message);
    } catch (reason) { fail(reason, "Established Streamlit workspace could not be imported."); }
    finally { setBusy(""); }
  };

  const blocked = workspace?.storeStatus === "blocked";
  return <>
    <PageHeader eyebrow="Team tools · Personal and local" title="My Board & Decision Tracker" description="Record your context around governed assets without changing NWR ranks, scores, outcomes, or market evidence." status={<><StatusBadge tone={blocked ? "blocked" : "safe"} label={blocked ? "Recovery required" : "Local workspace"} /><StatusBadge tone="review" label="Owner overlay only" /></>} />
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    <p aria-live="polite" className="workspace-feedback">{message || workspace?.message || "Loading your local workspace…"}</p>
    <div className="workspace-page-grid">
      <Panel title="My Board" eyebrow="Watch · target · avoid · notes">
        <div className="form-grid">
          <label className="form-field workspace-span"><span>Governed asset</span><select disabled={Boolean(busy)} value={assetId} onChange={(event) => setAssetId(event.target.value)}>{options.map((asset) => <option key={asset.assetId} value={asset.assetId}>{asset.name} · {asset.assetType}</option>)}</select></label>
          <label className="form-field"><span>Team window</span><select disabled={Boolean(busy)} value={board.teamWindow} onChange={(event) => setBoard((value) => ({ ...value, teamWindow: event.target.value as WorkspaceTeamWindow }))}>{TEAM_WINDOWS.map((value) => <option key={value}>{value}</option>)}</select></label>
          <label className="form-field"><span>Tags · comma separated</span><input disabled={Boolean(busy)} maxLength={500} value={tagsText} onChange={(event) => setTagsText(event.target.value)} /></label>
        </div>
        <fieldset className="workspace-flags" disabled={Boolean(busy)}><legend>Owner labels</legend>{(["watchlist", "target", "avoid"] as const).map((key) => <label key={key}><input checked={board[key]} onChange={(event) => setBoard((value) => ({ ...value, [key]: event.target.checked }))} type="checkbox" />{key[0]!.toUpperCase() + key.slice(1)}</label>)}</fieldset>
        <label className="form-field"><span>Personal context</span><textarea disabled={Boolean(busy)} maxLength={8000} value={board.notes} onChange={(event) => setBoard((value) => ({ ...value, notes: event.target.value }))} /><small>{board.notes.length.toLocaleString()} / 8,000 characters</small></label>
        <div className="workspace-actions"><Button disabled={blocked || Boolean(busy) || !assetId} icon="check" onClick={() => void saveBoard()}>{busy === "board" ? "Saving…" : "Save to My Board"}</Button></div>
      </Panel>
      <Panel title="Decision Tracker" eyebrow="Explicit journal · immutable source snapshot">
        <div className="form-grid">
          <label className="form-field"><span>Decision</span><input disabled={Boolean(busy)} maxLength={160} value={decisionTitle} onChange={(event) => setDecisionTitle(event.target.value)} placeholder="What are you deciding?" /></label>
          <label className="form-field"><span>Type</span><select disabled={Boolean(busy)} value={decisionType} onChange={(event) => setDecisionType(event.target.value as OwnerDecisionType)}>{DECISION_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
          <label className="form-field workspace-span"><span>Primary asset</span><select disabled={Boolean(busy)} value={decisionAsset} onChange={(event) => setDecisionAsset(event.target.value)}>{options.map((asset) => <option key={asset.assetId} value={asset.assetId}>{asset.name} · {asset.assetType}</option>)}</select></label>
        </div>
        <label className="form-field"><span>Decision context</span><textarea disabled={Boolean(busy)} maxLength={8000} value={rationale} onChange={(event) => setRationale(event.target.value)} /></label>
        <div className="workspace-actions"><Button disabled={blocked || Boolean(busy) || !decisionTitle.trim() || !rationale.trim()} icon="board" onClick={() => void saveDecision()} variant="secondary">{busy === "decision" ? "Saving…" : "Add decision"}</Button></div>
      </Panel>
    </div>
    <div className="workspace-page-grid">
      <Panel title="Personal Board entries" eyebrow={`${workspace?.personalBoard.length ?? 0} saved`}>
        {workspace?.personalBoard.length ? <div className="workspace-records">{workspace.personalBoard.map((entry) => <button disabled={Boolean(busy)} key={entry.assetId} onClick={() => setAssetId(entry.assetId)}><div><strong>{entry.name}</strong><small>{entry.assetType} · {entry.teamWindow}</small></div><span>{[entry.watchlist && "Watch", entry.target && "Target", entry.avoid && "Avoid"].filter(Boolean).join(" · ") || "Notes only"}</span></button>)}</div> : <EmptyState title="My Board is empty" message="Choose a governed asset, add your context, and save it locally." />}
      </Panel>
      <Panel title="Open decision journal" eyebrow={`${workspace?.decisions.length ?? 0} records`}>
        {workspace?.decisions.length ? <div className="workspace-records">{workspace.decisions.map((decision) => <article key={decision.decisionId}><div><strong>{decision.title}</strong><small>{decision.assetNames.join(", ")} · {decision.decisionType}</small></div><span>{decision.status}</span><p>{decision.rationale}</p></article>)}</div> : <EmptyState title="No decisions recorded" message="Add a decision when you want a durable local reminder and source snapshot." />}
      </Panel>
    </div>
    <Panel title="Backup & recovery check" eyebrow="Existing checksummed workspace service"><div className="workspace-recovery"><div><strong>{workspace?.backup.status === "ready" ? "Latest backup available" : workspace?.backup.status === "blocked" ? "Backup needs attention" : "No backup yet"}</strong><p>{workspace?.backup.message ?? "Create a local backup after saving owner context."}</p>{workspace?.backup.backupId ? <small>{workspace.backup.backupId} · {workspace.backup.fileCount || "unverified"} store files</small> : null}</div><div className="button-row"><Button disabled={Boolean(busy)} icon="shield" onClick={() => void backup()} variant="secondary">{busy === "backup" ? "Backing up…" : "Back up NWR"}</Button><Button disabled={Boolean(busy) || workspace?.backup.status === "none"} icon="activity" onClick={() => void checkRestore()} variant="ghost">{busy === "check" ? "Checking…" : "Check restore"}</Button><Button disabled={Boolean(busy) || workspace?.storeStatus !== "empty"} icon="layers" onClick={() => void adoptLegacy()} variant="ghost">{busy === "adopt" ? "Importing…" : "Import Streamlit workspace"}</Button></div></div></Panel>
  </>;
}
