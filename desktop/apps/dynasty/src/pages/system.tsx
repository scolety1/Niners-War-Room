import { createNwrClient, NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type {
  DynastyBootstrap,
  PlanningModuleId,
  PlanningModuleState,
  PlanningWorkspace,
} from "@nwr/contracts";
import {
  Button,
  DataTable,
  ErrorState,
  Icon,
  MetricCard,
  PageHeader,
  Panel,
  StatusBadge,
} from "@nwr/ui";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ownerLabel } from "../lib/owner-copy";

const PLANNING_TOOLS = [
  {
    id: "roster",
    title: "Roster architecture",
    icon: "players",
    horizon: "Now → 3 years",
    description:
      "Map positional pressure and manual succession notes without automated roster hydration.",
  },
  {
    id: "picks",
    title: "Future pick ledger",
    icon: "draft",
    horizon: "2027 → 2029",
    description: "Track owned capital and uncertainty. Unknown slots stay unknown.",
  },
  {
    id: "keeper",
    title: "Keeper deadline",
    icon: "shield",
    horizon: "Next deadline",
    description: "Review protected core, pressure candidates, and explicit rule configuration.",
  },
  {
    id: "drop",
    title: "Drop deadline",
    icon: "target",
    horizon: "Next deadline",
    description: "Separate roster pressure from long-term asset authority.",
  },
  {
    id: "trade",
    title: "Trade deadline",
    icon: "trade",
    horizon: "Season calendar",
    description: "Queue decisions by team window and evidence readiness.",
  },
  {
    id: "draft",
    title: "Upcoming draft prep",
    icon: "rookie",
    horizon: "2027 class",
    description: "Capture manual pick needs and draft-class watch points.",
  },
] as const;

const CHECK_LABELS = [
  "Confirm current owner-entered roster state",
  "Review identity or ownership gaps",
  "Capture the decision window",
  "Save evidence needed before action",
] as const;

type PlanningStateMap = Record<PlanningModuleId, PlanningModuleState>;

function planningStateMap(workspace: PlanningWorkspace): PlanningStateMap {
  const defaults = Object.fromEntries(
    PLANNING_TOOLS.map((tool) => [
      tool.id,
      {
        moduleId: tool.id,
        checks: [false, false, false, false],
        notes: "",
        saved: false,
        updatedAtUtc: "",
      },
    ]),
  ) as PlanningStateMap;
  for (const module of workspace.modules) defaults[module.moduleId] = { ...module };
  return defaults;
}

export function PlanningPage({ data }: { data: DynastyBootstrap }) {
  const navigate = useNavigate();
  const planningWorkspace = data.planning ?? {
    storeStatus: "empty" as const,
    updatedAtUtc: "",
    message: "No planning state was returned by the local service.",
    modules: [],
  };
  const initial = planningStateMap(planningWorkspace);
  const [active, setActive] = useState<PlanningModuleId>("roster");
  const [modules, setModules] = useState<PlanningStateMap>(initial);
  const [persisted, setPersisted] = useState<PlanningStateMap>(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string>("");
  const [statusMessage, setStatusMessage] = useState("");
  const selectableAssets = data.assetOptions.filter((asset) => asset.selectable);
  const [contextAssetId, setContextAssetId] = useState(selectableAssets[0]?.assetId ?? "");
  const contextAsset = selectableAssets.find((asset) => asset.assetId === contextAssetId);
  const tool = PLANNING_TOOLS.find((item) => item.id === active)!;
  const current = modules[active];
  const saved = persisted[active];
  const dirty =
    current.notes !== saved.notes || current.checks.some((value, index) => value !== saved.checks[index]);

  const updateCurrent = (changes: Partial<PlanningModuleState>) => {
    setModules((value) => ({ ...value, [active]: { ...value[active], ...changes } }));
    setStatusMessage("");
    setError("");
  };

  const save = async () => {
    const moduleId = active;
    const moduleTool = PLANNING_TOOLS.find((item) => item.id === moduleId)!;
    const draft = modules[moduleId];
    setSaving(true);
    setError("");
    setStatusMessage("");
    try {
      const client = await createNwrClient("dynasty");
      const workspace = await client.savePlanningModule(moduleId, {
        checks: draft.checks,
        notes: draft.notes,
      });
      const next = planningStateMap(workspace);
      setModules((value) => ({ ...value, [moduleId]: next[moduleId] }));
      setPersisted(next);
      setStatusMessage(`${moduleTool.title} saved to the Personal Workspace.`);
    } catch (reason) {
      setError(
        reason instanceof NwrApiError
          ? reason.message
          : "The planning module could not be saved locally.",
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <PageHeader
        eyebrow="Team · Manual planning"
        title="Dynasty Planning Console"
        description="Roster, picks, and deadlines stay connected to the long-term context without turning planning notes into hidden rankings."
        status={
          <>
            <StatusBadge tone="review" label="Manual descriptive only" />
            <StatusBadge
              tone={planningWorkspace.storeStatus === "blocked" ? "blocked" : "safe"}
              label={planningWorkspace.storeStatus === "blocked" ? "Workspace recovery required" : "Local persistence"}
            />
          </>
        }
      />
      <div className="planning-grid">
        <Panel title="Planning modules" eyebrow="Six graduated tools">
          <div className="planning-nav">
            {PLANNING_TOOLS.map((item) => {
              const module = modules[item.id];
              return (
                <button
                  aria-pressed={active === item.id}
                  className={active === item.id ? "active" : ""}
                  disabled={saving}
                  key={item.id}
                  onClick={() => {
                    setActive(item.id);
                    setError("");
                    setStatusMessage("");
                  }}
                >
                  <span><Icon name={item.icon} /></span>
                  <div>
                    <strong>{item.title}</strong>
                    <small>{module.saved ? `Saved · ${item.horizon}` : item.horizon}</small>
                  </div>
                  <Icon name="chevron" size={13} />
                </button>
              );
            })}
          </div>
        </Panel>
        <Panel title={tool.title} eyebrow={tool.horizon}>
          <section className="planning-canvas">
            <div className="planning-canvas__hero">
              <span><Icon name={tool.icon} size={26} /></span>
              <div><h3>{tool.title}</h3><p>{tool.description}</p></div>
            </div>
            <div className="planning-checks">
              {CHECK_LABELS.map((label, index) => (
                <label key={label}>
                  <input
                    checked={Boolean(current.checks[index])}
                    disabled={saving}
                    onChange={(event) =>
                      updateCurrent({
                        checks: current.checks.map((value, itemIndex) =>
                          itemIndex === index ? event.target.checked : value,
                        ),
                      })
                    }
                    type="checkbox"
                  />
                  {label}
                </label>
              ))}
            </div>
            <label className="form-field">
              <span>Owner notes</span>
              <textarea
                disabled={saving}
                maxLength={8000}
                onChange={(event) => updateCurrent({ notes: event.target.value })}
                placeholder="Record the football context, assumptions, and next check…"
                value={current.notes}
              />
              <small aria-live="polite">{current.notes.length.toLocaleString()} / 8,000 characters</small>
            </label>
            {error ? <ErrorState message={error} recovery="Your unsaved notes remain in this page. Retry after checking Data Health." /> : null}
            <div aria-live="polite" className="planning-canvas__footer">
              <span>
                {statusMessage ||
                  (current.saved && current.updatedAtUtc
                    ? `Last saved ${new Date(current.updatedAtUtc).toLocaleString()}`
                    : "Changes remain local and never alter governed source data.")}
              </span>
              <div className="button-row">
                <Button
                  disabled={!dirty || saving}
                  onClick={() => setModules((value) => ({ ...value, [active]: { ...saved } }))}
                  variant="ghost"
                >
                  Reset changes
                </Button>
                <Button
                  disabled={!dirty || saving || planningWorkspace.storeStatus === "blocked"}
                  icon="check"
                  onClick={() => void save()}
                  variant="secondary"
                >
                  {saving ? "Saving…" : "Save module"}
                </Button>
              </div>
            </div>
          </section>
        </Panel>
      </div>
      <Panel title="Governed asset context" eyebrow="Scenario Playground · no hidden value">
        <section className="planning-canvas">
          <label className="form-field">
            <span>Asset</span>
            <select value={contextAssetId} onChange={(event) => setContextAssetId(event.target.value)}>
              {selectableAssets.map((asset) => (
                <option key={asset.assetId} value={asset.assetId}>
                  {asset.name} · {asset.assetType} · {asset.evidenceBlocked ? "Manual review" : asset.rank == null ? "Context only" : `#${asset.rank}`}
                </option>
              ))}
            </select>
          </label>
          {contextAsset ? <div className="alert-strip"><strong>{contextAsset.name}</strong><span>{contextAsset.draftEligible ? "Draft eligible · " : ""}{contextAsset.scoreStatus}</span></div> : null}
          <div className="button-row">
            <Button disabled={!contextAssetId} onClick={() => navigate(`/players/${encodeURIComponent(contextAssetId)}`)} variant="secondary">Open detail</Button>
            <Button disabled={!contextAssetId} onClick={() => navigate(`/compare?assets=${encodeURIComponent(contextAssetId)}`)}>Add to Compare</Button>
            <Button disabled={!contextAssetId} onClick={() => navigate(`/trades?asset=${encodeURIComponent(contextAssetId)}`)} variant="ghost">Add to Trade Lab</Button>
          </div>
        </section>
      </Panel>
      <div className="metric-grid planning-metrics">
        <MetricCard label="Watchlist" value={data.summary.workspace.watchlist} detail="Owner tagged" icon="target" tone="violet" />
        <MetricCard label="Targets" value={data.summary.workspace.targets} detail="Active interest" icon="check" tone="gold" />
        <MetricCard label="Open decisions" value={data.summary.workspace.openDecisions} detail="Decisions to revisit" icon="board" tone="cyan" />
        <MetricCard label="Saved scenarios" value={data.summary.workspace.savedScenarios} detail="Local compositions" icon="layers" tone="crimson" />
      </div>
    </>
  );
}

export function draftCockpitRookieRows(data: Pick<DynastyBootstrap, "rookies" | "rookieReadiness">) {
  const admittedIds = new Set(data.rookieReadiness.draftableAssetIds);
  return data.rookies.filter((row) => admittedIds.has(row.assetId)).map((row) => ({ ...row }));
}

export function DraftCockpitPage({ data }: { data: DynastyBootstrap }) {
  const navigate = useNavigate();
  const rookieRows = draftCockpitRookieRows(data);
  const premium = data.rankings
    .filter((row) => (row.rank ?? 999) <= 24)
    .slice(0, 12)
    .map((row) => ({ ...row }));
  const [rookieId, setRookieId] = useState(rookieRows[0]?.assetId ?? "");
  const [anchorId, setAnchorId] = useState(premium[0]?.assetId ?? "");
  const selectedRookie = rookieRows.find((row) => row.assetId === rookieId);
  const selectedAnchor = premium.find((row) => row.assetId === anchorId);
  const comparisonIds = [rookieId, anchorId].filter(Boolean);

  return (
    <>
      <PageHeader
        eyebrow="Draft tools · Long-term context"
        title="Dynasty Draft Cockpit"
        description="A governed, read-only on-clock decision surface for rookie evidence, current-player anchors, and direct comparison."
        status={
          <>
            <StatusBadge tone="safe" label={`${data.rookieReadiness.officialDrafted} draftable rookies`} />
            <StatusBadge tone="review" label={`${data.rookieReadiness.manualReview} manual review`} />
            <StatusBadge tone="safe" label="No live provider calls" />
          </>
        }
        actions={<Button icon="rookie" onClick={() => navigate("/rookies")}>Open Rookie Review</Button>}
      />
      <div className="alert-strip">
        <strong>{data.rookieReadiness.alertTitle}</strong>
        <span>
          {data.rookieReadiness.alertMessage} Live pick writes remain in the existing Streamlit
          runtime; this page never implies a pick was recorded.
        </span>
      </div>
      <div className="dashboard-grid">
        <Panel title="On-clock decision focus" eyebrow="Choose two governed contexts">
          <section className="planning-canvas">
            <label className="form-field">
              <span>Rookie target</span>
              <select value={rookieId} onChange={(event) => setRookieId(event.target.value)}>
                {rookieRows.map((row) => (
                  <option key={row.assetId} value={row.assetId}>
                    {row.rank == null ? "Manual Review" : `#${row.rank}`} · {row.player} · {row.position} · Pick {row.overallPick ?? "—"}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span>Established anchor</span>
              <select value={anchorId} onChange={(event) => setAnchorId(event.target.value)}>
                {premium.map((row) => (
                  <option key={row.assetId} value={row.assetId}>
                    #{row.rank} · {row.player} · {row.positionRank}
                  </option>
                ))}
              </select>
            </label>
            <div className="planning-canvas__hero">
              <span><Icon name="compare" size={26} /></span>
              <div>
                <h3>{selectedRookie?.player ?? "Rookie unavailable"} vs {selectedAnchor?.player ?? "anchor unavailable"}</h3>
                <p>Compare source-separated horizons; Rookie Review and Finished V1 retain their own scales.</p>
              </div>
            </div>
            <div className="button-row">
              <Button
                disabled={!rookieId}
                onClick={() => navigate(`/players/${encodeURIComponent(rookieId)}`)}
                variant="secondary"
              >
                Open rookie evidence
              </Button>
              <Button
                disabled={comparisonIds.length < 2}
                icon="compare"
                onClick={() => navigate(`/compare?assets=${comparisonIds.map(encodeURIComponent).join(",")}`)}
              >
                Compare contexts
              </Button>
            </div>
          </section>
        </Panel>
        <Panel title="Evidence readiness" eyebrow="Local, read-only">
          <div className="readiness-ring">
            <div><strong>{data.rookieReadiness.missingFromDraftablePool === 0 ? "100" : "0"}</strong><span>/ 100</span></div>
            <p>{data.rookieReadiness.ready ? "Official draft class complete" : "Draft-class gaps require review"}</p>
          </div>
          <dl className="health-list">
            <div><dt>Dynasty board</dt><dd><StatusBadge tone={data.rankings.length ? "safe" : "blocked"} label={data.rankings.length ? "Ready" : "Blocked"} /></dd></div>
            <div><dt>Official QB/RB/WR/TE</dt><dd><StatusBadge tone="safe" label={`${data.rookieReadiness.officialDrafted} rows`} /></dd></div>
            <div><dt>Missing draftable</dt><dd><StatusBadge tone={data.rookieReadiness.missingFromDraftablePool ? "blocked" : "safe"} label={String(data.rookieReadiness.missingFromDraftablePool)} /></dd></div>
            <div><dt>Live draft writes</dt><dd><StatusBadge tone="review" label="Legacy runtime only" /></dd></div>
            <div><dt>Provider network</dt><dd><StatusBadge tone="safe" label="Off" /></dd></div>
          </dl>
        </Panel>
      </div>
      <Panel title="Complete rookie draft board" eyebrow="Ranked first · manual-review assets retained">
        <DataTable
          columns={[
            { key: "rank", label: "Rookie rank", render: (row) => row.rank == null ? "Manual Review" : `#${String(row.rank)}` },
            { key: "player", label: "Player", render: (row) => <span className="player-cell"><strong>{String(row.player)}</strong><small>{ownerLabel(row.team)} · {ownerLabel(row.position)}</small></span> },
            { key: "overallPick", label: "NFL pick", render: (row) => row.overallPick == null ? "—" : `R${String(row.draftRound)} · #${String(row.overallPick)}` },
            { key: "draftEligibility", label: "Draft eligibility", render: (row) => <StatusBadge tone={row.draftable ? "safe" : "blocked"} label={String(row.draftEligibility)} /> },
            { key: "scoreStatus", label: "Score status", render: (row) => <StatusBadge tone={row.modelScoreEligible ? "safe" : "review"} label={row.modelScoreEligible ? "Scored" : "Manual review"} /> },
          ]}
          rows={rookieRows}
          rowKey={(row) => String(row.assetId)}
          onRowClick={(row) => navigate(`/players/${encodeURIComponent(String(row.assetId))}`)}
        />
      </Panel>
      <Panel title="Premium established anchors" eyebrow="Finished V1 · Top 24">
        <DataTable
          columns={[
            { key: "rank", label: "Rank", render: (row) => `#${String(row.rank)}` },
            { key: "player", label: "Player", render: (row) => <span className="player-cell"><strong>{String(row.player)}</strong><small>{ownerLabel(row.team)} · {ownerLabel(row.positionRank)}</small></span> },
            { key: "nwrScore", label: "Score", align: "right" },
            { key: "range", label: "Expected window", render: (row) => ownerLabel(row.range) },
            { key: "marketBand", label: "Market context", render: (row) => ownerLabel(row.marketBand) },
          ]}
          rows={premium}
          rowKey={(row) => String(row.assetId)}
          onRowClick={(row) => navigate(`/players/${encodeURIComponent(String(row.assetId))}`)}
        />
      </Panel>
    </>
  );
}

// Dynasty League Import V1 (Worker 3): the real "Connect League" flow.
// Lives on Data Health because this is the page that already, honestly,
// discloses Dynasty's roster data as manual-only ("without automated
// roster hydration" -- see the Planning Console copy above) -- the
// natural place for the owner to change that. A GET-only Sleeper fetch
// underneath (`dynasty_sleeper_league_service`); no Sleeper writes ever.
// The connected league selection is persisted server-side
// (`local_exports/dynasty_v1/active_league_profile.json`, mirroring
// Redraft's own `active_profile.json` convention) -- it survives a full
// app/backend restart with no browser-local state needed at all.
function DynastyLeagueConnectionPanel({
  client,
  data,
  onReload,
}: {
  client: NwrApiClient;
  data: DynastyBootstrap;
  onReload: () => void;
}) {
  const connected = data.dynastyLeague;
  const [leagueId, setLeagueId] = useState("");
  const [myOwnerId, setMyOwnerId] = useState("");
  const [busy, setBusy] = useState<"connect" | "disconnect" | "refresh" | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const myTeamName = connected
    ? data.rankings.find((row) => row.ownership?.isMyTeam)?.ownership?.rosterTeamName || null
    : null;

  const connect = async () => {
    const trimmedLeagueId = leagueId.trim();
    if (!trimmedLeagueId) {
      setError("Enter your Sleeper league ID.");
      return;
    }
    setBusy("connect");
    setError("");
    setMessage("");
    try {
      await client.importDynastySleeperLeague({
        leagueId: trimmedLeagueId,
        ...(myOwnerId.trim() ? { myOwnerId: myOwnerId.trim() } : {}),
      });
      setMessage("League connected. Ownership context is now live across Home, Asset Explorer, and Player Detail.");
      onReload();
    } catch (reason) {
      setError(
        reason instanceof NwrApiError
          ? reason.message
          : "The Sleeper league could not be imported.",
      );
    } finally {
      setBusy(null);
    }
  };

  const disconnect = async () => {
    setBusy("disconnect");
    setError("");
    setMessage("");
    try {
      await client.disconnectDynastyLeague();
      setMessage("League disconnected. Ownership context is hidden again.");
      onReload();
    } catch (reason) {
      setError(
        reason instanceof NwrApiError
          ? reason.message
          : "The connected league could not be disconnected.",
      );
    } finally {
      setBusy(null);
    }
  };

  // D1 fix (NWR Sunday Readiness overnight cycle, Worker 4): before this,
  // an already-connected league had NO way to get a fresh Sleeper pull --
  // reloading the page only re-reads the latest already-SAVED local
  // snapshot (`load_dynasty_league_profile`), never fetches a new one, and
  // the only button offered while connected was "Disconnect league" (owner
  // would have to disconnect, re-type the league id, and reconnect just to
  // refresh). Reuses the SAME real, read-only `importDynastySleeperLeague`
  // GET-only import path Connect already uses -- resubmitting the SAME
  // real league id (and owner id, when known) the connected profile itself
  // now discloses (`connected.leagueId`/`myOwnerId`, both additive fields
  // this pass added to the contract). Every real import call already
  // writes a NEW, uniquely-timestamped snapshot file
  // (`save_league_snapshot`'s `utc_snapshot_stamp()` filename) and never
  // overwrites or discards a prior one, and a failed fetch raises before
  // any new file is written -- so the previous snapshot and connection
  // state are structurally preserved on a failed refresh with no extra
  // code needed here.
  const refresh = async () => {
    if (!connected) return;
    setBusy("refresh");
    setError("");
    setMessage("");
    try {
      await client.importDynastySleeperLeague({
        leagueId: connected.leagueId,
        ...(connected.myOwnerId ? { myOwnerId: connected.myOwnerId } : {}),
        profileId: connected.profileId,
      });
      setMessage("League refreshed from Sleeper. A new dated snapshot was saved.");
      onReload();
    } catch (reason) {
      setError(
        reason instanceof NwrApiError
          ? reason.message
          : "The league could not be refreshed from Sleeper. The previous snapshot is unchanged.",
      );
    } finally {
      setBusy(null);
    }
  };

  return (
    <Panel
      title="Dynasty League Connection"
      eyebrow="Sleeper · read-only import · GET requests only"
    >
      {connected ? (
        <>
          <div className="alert-strip">
            <strong>Connected: {connected.leagueName || connected.profileId}</strong>
            <span>
              {myTeamName ? `Your team: ${myTeamName} · ` : ""}
              Roster #{connected.myRosterId ?? "—"} · Imported {connected.fetchedAtUtc ? new Date(connected.fetchedAtUtc).toLocaleString() : "recently"}
            </span>
          </div>
          <p className="copy-muted">
            Ownership badges now appear on Home, Asset Explorer, and Player Detail. Rookie
            assets show as "Ownership unresolved" until a Sleeper identity crosswalk exists --
            this is disclosed on purpose, never silently guessed.
          </p>
          <div className="button-row">
            <Button
              disabled={busy !== null}
              icon="activity"
              onClick={() => void refresh()}
            >
              {busy === "refresh" ? "Refreshing…" : "Refresh from Sleeper"}
            </Button>
            <Button
              disabled={busy !== null}
              icon="undo"
              onClick={() => void disconnect()}
              variant="ghost"
            >
              {busy === "disconnect" ? "Disconnecting…" : "Disconnect league"}
            </Button>
          </div>
        </>
      ) : (
        <>
          <p className="copy-muted">
            No Dynasty league is connected. Roster data stays manual-only (Planning Console
            entries) until you connect a real Sleeper league below. This is a read-only import --
            it never writes to Sleeper.
          </p>
          <div className="planning-canvas">
            <label className="form-field">
              <span>Sleeper league ID</span>
              <input
                disabled={busy !== null}
                onChange={(event) => setLeagueId(event.target.value)}
                placeholder="e.g. 1344772855908290560"
                type="text"
                value={leagueId}
              />
            </label>
            <label className="form-field">
              <span>Your Sleeper user ID (optional)</span>
              <input
                disabled={busy !== null}
                onChange={(event) => setMyOwnerId(event.target.value)}
                placeholder="Identifies which roster is yours"
                type="text"
                value={myOwnerId}
              />
            </label>
            <div className="button-row">
              <Button disabled={busy !== null || !leagueId.trim()} icon="check" onClick={() => void connect()}>
                {busy === "connect" ? "Connecting…" : "Connect league"}
              </Button>
            </div>
          </div>
        </>
      )}
      {error ? <ErrorState message={error} recovery="Verify the league ID and try again." /> : null}
      {!error && message ? (
        <div aria-live="polite" className="alert-strip">
          <strong>{message}</strong>
        </div>
      ) : null}
    </Panel>
  );
}

export function DataHealthPage({
  client,
  data,
  onReload,
}: {
  client: NwrApiClient;
  data: DynastyBootstrap;
  onReload: () => void;
}) {
  const status = data.status;
  const sourceRows = Object.entries(status.sourceHashes ?? {}).map(([source, hash]) => ({ source, hash, state: "Verified" }));
  return <>
    <PageHeader eyebrow="System · Trust & freshness" title="Data Health" description="Inspect the governed source state, freshness, and local runtime boundary. No page-open refresh or provider call occurs here." status={<><StatusBadge tone={status.tone} label={status.ready ? "Decision ready" : "Review required"} /><StatusBadge tone="safe" label="Scheduled refresh disabled" /></>} actions={<Button icon="activity" onClick={onReload}>Reload local snapshot</Button>} />
    <section className={`health-hero health-hero--${status.tone}`}><div className="health-hero__icon"><Icon name={status.ready ? "check" : "alert"} size={27} /></div><div><span>{status.authority}</span><h2>{status.summary}</h2><p>Source as of {status.sourceAsOf || "unavailable"} · {status.freshness || "freshness unclassified"}</p></div><div><strong>{status.ready ? "READY" : "REVIEW"}</strong><small>Local contract 1.0</small></div></section>
    <div className="metric-grid"><MetricCard label="Dynasty rows" value={data.rankings.length} detail="Expected 240" trend={data.rankings.length === 240 ? "Exact" : "Review"} icon="board" tone="violet" /><MetricCard label="Market matches" value={data.summary.marketMatched} detail={`As of ${data.marketFreshness.sourceAsOf || "—"}`} trend={data.marketFreshness.status} icon="market" tone="gold" /><MetricCard label="Rookie rows" value={data.rookies.length} detail={`${data.summary.manualReviewRookies} manual review`} trend="Review only" icon="rookie" tone="crimson" /><MetricCard label="Scheduled refresh" value="OFF" detail="Owner approval required" trend="Fail-closed" icon="shield" tone="cyan" /></div>
    <DynastyLeagueConnectionPanel client={client} data={data} onReload={onReload} />
    <div className="split-view"><Panel title="Source integrity" eyebrow="Owner view"><p className="copy-muted">All required Dynasty sources passed local integrity checks. Technical source fingerprints are available below when needed.</p><details className="advanced-details"><summary>Advanced source details</summary>{sourceRows.length ? <DataTable columns={[{key:"source",label:"Authority"},{key:"hash",label:"Source fingerprint",render:(row)=><code className="hash-value">{String(row.hash)}</code>},{key:"state",label:"State",render:()=> <StatusBadge tone="safe" label="Verified" />}]} rows={sourceRows} rowKey={(row)=>String(row.source)} /> : <p className="copy-muted">Technical source details were not included in this runtime snapshot.</p>}</details></Panel><Panel title="Runtime boundary" eyebrow="Windows desktop"><dl className="health-list"><div><dt>Transport</dt><dd>Local computer only</dd></div><div><dt>Cloud dependency</dt><dd>None</dd></div><div><dt>Provider calls</dt><dd>Disabled</dd></div><div><dt>Streamlit fallback</dt><dd>Preserved</dd></div><div><dt>Mode isolation</dt><dd>Dynasty only</dd></div></dl></Panel></div>
    {status.errors.map((error) => <div className="alert-strip alert-strip--blocked" key={error}><strong>Blocked</strong>{error}</div>)}{status.warnings.map((warning) => <div className="alert-strip" key={warning}><strong>Review</strong>{warning}</div>)}
  </>;
}
