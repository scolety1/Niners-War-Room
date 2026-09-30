import type { AssetOwnership, DynastyBootstrap } from "@nwr/contracts";
import { ActionCard, Button, DataTable, MetricCard, PageHeader, Panel, StatusBadge, formatNumber } from "@nwr/ui";
import { useNavigate } from "react-router-dom";
import { ownerLabel } from "../lib/owner-copy";

export function HomePage({ data }: { data: DynastyBootstrap }) {
  const navigate = useNavigate();
  const summary = data.summary;
  // Dynasty League Import V1 (Worker 3): present ONLY once a real league is
  // connected -- `data.dynastyLeague` is entirely absent otherwise (the
  // backend facade's byte-identical-when-not-connected guarantee), so this
  // whole section renders nothing for anyone who hasn't connected a league,
  // exactly matching Home's pre-existing appearance.
  const dynastyLeague = data.dynastyLeague;
  const myRoster = dynastyLeague
    ? data.rankings.filter((row) => row.ownership?.isMyTeam).map((row) => ({ ...row }))
    : [];
  const myTeamName = dynastyLeague
    ? data.rankings.find((row) => row.ownership?.isMyTeam)?.ownership?.rosterTeamName || null
    : null;
  const injuryFindings = myRoster
    .filter((row) => row.currentStatusOverride)
    .sort((left, right) => {
      const leftStarter = left.ownership?.rosterSlotStatus === "starter" ? 1 : 0;
      const rightStarter = right.ownership?.rosterSlotStatus === "starter" ? 1 : 0;
      return rightStarter - leftStarter || (left.rank ?? 999) - (right.rank ?? 999);
    });
  const marketOpportunities = myRoster
    .filter((row) => Math.abs(row.marketGap ?? 0) >= 6)
    .sort((left, right) => Math.abs(right.marketGap ?? 0) - Math.abs(left.marketGap ?? 0))
    .slice(0, 5);
  const hasPriorityFindings = injuryFindings.length > 0 || marketOpportunities.length > 0;

  return <>
    <PageHeader eyebrow="Owner command center" title="Your dynasty, in decision order." description="Rank, compare, pressure-test, and plan from one governed long-term view. Model operations stay behind the glass." status={<><StatusBadge tone="safe" label="Finished V1 authority" /><StatusBadge tone="review" label={ownerLabel(data.marketFreshness.status, "Market freshness review")} />{dynastyLeague ? <StatusBadge tone="safe" label={`Connected: ${dynastyLeague.leagueName || dynastyLeague.profileId}`} /> : null}</>} actions={<><Button icon="compare" onClick={() => navigate("/compare")}>Compare players</Button><Button icon="trade" variant="secondary" onClick={() => navigate("/trades")}>Analyze trade</Button></>} />
    {!dynastyLeague ? (
      <div className="alert-strip">
        <strong>No Dynasty league connected</strong>
        <span>Connect your real Sleeper league to see your own roster, distinct from the market-wide board.</span>
        <Button icon="check" onClick={() => navigate("/data-health")} variant="secondary">Connect league</Button>
      </div>
    ) : null}
    <section className="decision-hero"><div><span className="decision-hero__eyebrow">Decision pulse · Your real roster</span><h2>What needs your attention?</h2><p>Only high-value owner-roster findings lead: verified status changes and large NWR-versus-market disagreements.</p></div><div className="decision-hero__actions"><Button icon="trade" onClick={() => navigate("/trades")}>Open Trade Lab</Button><Button icon="market" variant="secondary" onClick={() => navigate("/market")}>Scan market gaps</Button></div></section>
    {dynastyLeague ? <Panel title="Priority actions" eyebrow={`${data.lifecycleContext?.seasonPhase?.replaceAll("_", " ") ?? "Current season"} · owner roster only`}>
      {!hasPriorityFindings ? <p className="copy-muted">No verified major status change or large owner-roster market discrepancy needs action right now.</p> : null}
      <div className="action-grid">
        {injuryFindings.map((row) => <ActionCard
          key={`status-${row.assetId}`}
          icon="alert"
          title={`${row.player}: ${row.currentStatusOverride!.kind.replaceAll("_", " ")}`}
          description={row.currentStatusOverride!.reason}
          meta={`${ownerLabel(row.ownership?.rosterSlotStatus ?? "Rostered")} · verified ${row.currentStatusOverride!.effectiveDate}`}
          onClick={() => navigate(`/players/${encodeURIComponent(row.assetId)}`)}
        />)}
        {marketOpportunities.map((row) => <ActionCard
          key={`gap-${row.assetId}`}
          icon="market"
          title={`${row.player}: ${row.marketGap! > 0 ? "+" : ""}${formatNumber(row.marketGap!, 0)} rank gap`}
          description={`NWR #${row.rank ?? "—"} versus market #${row.marketRank ?? "—"}. Investigate before a trade decision; market evidence never reorders NWR.`}
          meta={`${ownerLabel(row.ownership?.rosterSlotStatus ?? "Rostered")} · ${ownerLabel(row.marketBand)}`}
          onClick={() => navigate(`/players/${encodeURIComponent(row.assetId)}`)}
        />)}
      </div>
    </Panel> : null}
    <div className="metric-grid">
      <MetricCard label="Governed board" value={summary.rankedPlayers} detail="Finished V1 assets" trend="Board authority" icon="board" tone="violet" />
      <MetricCard label="Market coverage" value={summary.marketMatched} detail={`${Math.max(0, summary.rankedPlayers - summary.marketMatched)} unmatched`} trend={data.marketFreshness.sourceAsOf || "No date"} icon="market" tone="gold" />
      <MetricCard label="Rookie review" value={summary.rookieRows} detail={`${summary.manualReviewRookies} manual review`} trend={`${summary.blockedRookies} unresolved`} icon="rookie" tone="crimson" />
      <MetricCard label="Open decisions" value={summary.workspace.openDecisions} detail={`${summary.workspace.savedScenarios} saved scenarios`} trend={`${summary.workspace.targets} targets`} icon="target" tone="cyan" />
    </div>
    {dynastyLeague ? (
      <Panel
        title={`Your roster${myTeamName ? ` — ${myTeamName}` : ""}`}
        eyebrow={`${dynastyLeague.leagueName || "Connected league"} · ${myRoster.length} of your players on the governed board`}
        action={<Button variant="ghost" onClick={() => navigate("/assets")}>Open Asset Explorer</Button>}
      >
        {myRoster.length ? (
          <DataTable
            columns={[
              { key: "rank", label: "NWR", width: "62px", render: (row) => <span className="rank-cell"><i /><b>#{String(row.rank ?? "—")}</b></span> },
              { key: "player", label: "Player", render: (row) => <span className="player-cell"><strong>{String(row.player)}</strong><small>{ownerLabel(row.team)} · {ownerLabel(row.positionRank)}</small></span> },
              { key: "position", label: "Pos", align: "center", render: (row) => <span className="position-pill">{String(row.position)}</span> },
              { key: "rosterSlot", label: "Slot", render: (row) => ownerLabel((row.ownership as AssetOwnership | undefined)?.rosterSlotStatus ?? "") },
              { key: "nwrScore", label: "NWR score", align: "right", render: (row) => formatNumber(row.nwrScore as number, 2) },
            ]}
            rows={myRoster}
            rowKey={(row) => String(row.assetId)}
            onRowClick={(row) => navigate(`/players/${encodeURIComponent(String(row.assetId))}`)}
          />
        ) : (
          <p className="copy-muted">
            None of your connected roster's current players matched the governed board yet --
            this can happen right after a fresh import. Reload Data Health to resync.
          </p>
        )}
      </Panel>
    ) : null}
    <div className="dashboard-grid">
      <Panel title="Your roster's market gaps" eyebrow="Investigate · never automatic" action={<Button variant="ghost" onClick={() => navigate("/market")}>Open full market</Button>}>
        <DataTable columns={[
          { key: "rank", label: "NWR", width: "62px", render: (row) => <span className="rank-cell"><i /><b>#{String(row.rank ?? "—")}</b></span> },
          { key: "player", label: "Player", render: (row) => <span className="player-cell"><strong>{String(row.player)}</strong><small>{ownerLabel(row.team)} · {ownerLabel(row.positionRank)}</small></span> },
          { key: "marketBand", label: "Signal", render: (row) => <span className="market-signal market-signal--buy"><i />{ownerLabel(row.marketBand)}</span> },
          { key: "marketRank", label: "Market", align: "right", render: (row) => `#${String(row.marketRank ?? "—")}` },
          { key: "marketGap", label: "Gap", align: "right", render: (row) => <strong className="positive-value">+{formatNumber(row.marketGap as number, 0)}</strong> },
          { key: "confidence", label: "Confidence", render: (row) => ownerLabel(row.confidence) },
        ]} rows={marketOpportunities} rowKey={(row) => String(row.assetId)} onRowClick={(row) => navigate(`/players/${encodeURIComponent(String(row.assetId))}`)} />
      </Panel>
      <div className="dashboard-stack">
        <Panel title="Most common jobs" eyebrow="Owner workflow">
          <div className="action-grid">
            <ActionCard icon="players" title="Evaluate player" description="Rank, range, outcomes, market." meta="One decision hub" onClick={() => navigate("/players")} />
            <ActionCard icon="compare" title="Compare options" description="Separate each decision horizon." meta="2–4 assets" onClick={() => navigate("/compare")} />
            <ActionCard icon="trade" title="Pressure-test trade" description="Ten transparent dimensions." meta="Advisory only" onClick={() => navigate("/trades")} />
            <ActionCard icon="rookie" title="Review rookies" description="Draft range and evidence gates." meta={`${summary.rookieRows} prospects`} onClick={() => navigate("/rookies")} />
          </div>
        </Panel>
        <Panel title="Decision workspace" eyebrow="Personal · local only" action={<Button variant="ghost" onClick={() => navigate("/workspace")}>Open My Board</Button>}>
          <div className="workspace-stats"><div><strong>{summary.workspace.watchlist}</strong><span>Watchlist</span></div><div><strong>{summary.workspace.targets}</strong><span>Targets</span></div><div><strong>{summary.workspace.avoid}</strong><span>Avoid</span></div><div><strong>{summary.workspace.openDecisions}</strong><span>Open</span></div></div>
        </Panel>
      </div>
    </div>
  </>;
}
