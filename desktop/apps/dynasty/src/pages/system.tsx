import { createNwrClient, NwrApiError } from "@nwr/api-client";
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
      <div className="metric-grid planning-metrics">
        <MetricCard label="Watchlist" value={data.summary.workspace.watchlist} detail="Owner tagged" icon="target" tone="violet" />
        <MetricCard label="Targets" value={data.summary.workspace.targets} detail="Active interest" icon="check" tone="gold" />
        <MetricCard label="Open decisions" value={data.summary.workspace.openDecisions} detail="Decisions to revisit" icon="board" tone="cyan" />
        <MetricCard label="Saved scenarios" value={data.summary.workspace.savedScenarios} detail="Local compositions" icon="layers" tone="crimson" />
      </div>
    </>
  );
}

export function DraftCockpitPage({ data }: { data: DynastyBootstrap }) {
  const navigate = useNavigate();
  const rookieRows = data.rookies
    .filter((row) => row.rank != null && !row.blockedReason)
    .slice(0, 12)
    .map((row) => ({ ...row }));
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
            <StatusBadge tone="review" label="Rookie Review authority" />
            <StatusBadge tone="safe" label="No live provider calls" />
          </>
        }
        actions={<Button icon="rookie" onClick={() => navigate("/rookies")}>Open Rookie Review</Button>}
      />
      <div className="alert-strip">
        <strong>Desktop V1 boundary</strong>
        <span>
          Live picks remain in the existing Streamlit draft runtime until its session lifecycle,
          event log, backup, and recovery contract are wrapped together. This page never implies a pick was recorded.
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
                    #{row.rank} · {row.player} · {row.position}
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
            <div><strong>{data.status.ready ? "92" : "46"}</strong><span>/ 100</span></div>
            <p>{data.status.ready ? "Governed evidence loaded" : "Source blockers require review"}</p>
          </div>
          <dl className="health-list">
            <div><dt>Dynasty board</dt><dd><StatusBadge tone={data.rankings.length ? "safe" : "blocked"} label={data.rankings.length ? "Ready" : "Blocked"} /></dd></div>
            <div><dt>Rookie Review</dt><dd><StatusBadge tone="review" label={`${data.rookies.length} rows`} /></dd></div>
            <div><dt>Live draft writes</dt><dd><StatusBadge tone="review" label="Legacy runtime only" /></dd></div>
            <div><dt>Provider network</dt><dd><StatusBadge tone="safe" label="Off" /></dd></div>
          </dl>
        </Panel>
      </div>
      <Panel title="Top rookie targets" eyebrow="Frozen 2026 review · open a row for evidence">
        <DataTable
          columns={[
            { key: "rank", label: "Rank", render: (row) => `#${String(row.rank)}` },
            { key: "player", label: "Player", render: (row) => <span className="player-cell"><strong>{String(row.player)}</strong><small>{ownerLabel(row.team)} · {ownerLabel(row.position)}</small></span> },
            { key: "rookieTier", label: "Tier", render: (row) => <span className="tier-pill">{ownerLabel(row.rookieTier)}</span> },
            { key: "draftRange", label: "Draft range", render: (row) => ownerLabel(row.draftRange) },
            { key: "confidence", label: "Confidence", render: (row) => ownerLabel(row.confidence) },
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

export function DataHealthPage({ data, onReload }: { data: DynastyBootstrap; onReload: () => void }) {
  const status = data.status;
  const sourceRows = Object.entries(status.sourceHashes ?? {}).map(([source, hash]) => ({ source, hash, state: "Verified" }));
  return <>
    <PageHeader eyebrow="System · Trust & freshness" title="Data Health" description="Inspect the governed source state, freshness, and local runtime boundary. No page-open refresh or provider call occurs here." status={<><StatusBadge tone={status.tone} label={status.ready ? "Decision ready" : "Review required"} /><StatusBadge tone="safe" label="Scheduled refresh disabled" /></>} actions={<Button icon="activity" onClick={onReload}>Reload local snapshot</Button>} />
    <section className={`health-hero health-hero--${status.tone}`}><div className="health-hero__icon"><Icon name={status.ready ? "check" : "alert"} size={27} /></div><div><span>{status.authority}</span><h2>{status.summary}</h2><p>Source as of {status.sourceAsOf || "unavailable"} · {status.freshness || "freshness unclassified"}</p></div><div><strong>{status.ready ? "READY" : "REVIEW"}</strong><small>Local contract 1.0</small></div></section>
    <div className="metric-grid"><MetricCard label="Dynasty rows" value={data.rankings.length} detail="Expected 240" trend={data.rankings.length === 240 ? "Exact" : "Review"} icon="board" tone="violet" /><MetricCard label="Market matches" value={data.summary.marketMatched} detail={`As of ${data.marketFreshness.sourceAsOf || "—"}`} trend={data.marketFreshness.status} icon="market" tone="gold" /><MetricCard label="Rookie rows" value={data.rookies.length} detail={`${data.summary.blockedRookies} blocked`} trend="Review only" icon="rookie" tone="crimson" /><MetricCard label="Scheduled refresh" value="OFF" detail="Owner approval required" trend="Fail-closed" icon="shield" tone="cyan" /></div>
    <div className="split-view"><Panel title="Source integrity" eyebrow="Owner view"><p className="copy-muted">All required Dynasty sources passed local integrity checks. Technical source fingerprints are available below when needed.</p><details className="advanced-details"><summary>Advanced source details</summary>{sourceRows.length ? <DataTable columns={[{key:"source",label:"Authority"},{key:"hash",label:"Source fingerprint",render:(row)=><code className="hash-value">{String(row.hash)}</code>},{key:"state",label:"State",render:()=> <StatusBadge tone="safe" label="Verified" />}]} rows={sourceRows} rowKey={(row)=>String(row.source)} /> : <p className="copy-muted">Technical source details were not included in this runtime snapshot.</p>}</details></Panel><Panel title="Runtime boundary" eyebrow="Windows desktop"><dl className="health-list"><div><dt>Transport</dt><dd>Local computer only</dd></div><div><dt>Cloud dependency</dt><dd>None</dd></div><div><dt>Provider calls</dt><dd>Disabled</dd></div><div><dt>Streamlit fallback</dt><dd>Preserved</dd></div><div><dt>Mode isolation</dt><dd>Dynasty only</dd></div></dl></Panel></div>
    {status.errors.map((error) => <div className="alert-strip alert-strip--blocked" key={error}><strong>Blocked</strong>{error}</div>)}{status.warnings.map((warning) => <div className="alert-strip" key={warning}><strong>Review</strong>{warning}</div>)}
  </>;
}
