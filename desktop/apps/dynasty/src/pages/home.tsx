import type { DynastyBootstrap } from "@nwr/contracts";
import { ActionCard, Button, DataTable, MetricCard, PageHeader, Panel, StatusBadge, formatNumber } from "@nwr/ui";
import { useNavigate } from "react-router-dom";
import { ownerLabel } from "../lib/owner-copy";

export function HomePage({ data }: { data: DynastyBootstrap }) {
  const navigate = useNavigate();
  const summary = data.summary;
  const marketOpportunities = data.rankings
    .filter((row) => (row.marketGap ?? 0) >= 6)
    .sort((left, right) => (right.marketGap ?? 0) - (left.marketGap ?? 0))
    .slice(0, 7)
    .map((row) => ({ ...row }));

  return <>
    <PageHeader eyebrow="Owner command center" title="Your dynasty, in decision order." description="Rank, compare, pressure-test, and plan from one governed long-term view. Model operations stay behind the glass." status={<><StatusBadge tone="safe" label="Finished V1 authority" /><StatusBadge tone="review" label={ownerLabel(data.marketFreshness.status, "Market freshness review")} /></>} actions={<><Button icon="compare" onClick={() => navigate("/compare")}>Compare players</Button><Button icon="trade" variant="secondary" onClick={() => navigate("/trades")}>Analyze trade</Button></>} />
    {data.notices.map((notice) => <div className={`alert-strip ${notice.tone === "blocked" ? "alert-strip--blocked" : ""}`} key={notice.title}><strong>{notice.title}</strong><span>{notice.message}</span></div>)}
    <section className="decision-hero"><div><span className="decision-hero__eyebrow">Decision pulse · Long-term roster architecture</span><h2>What needs your attention?</h2><p>Market disagreement, rookie uncertainty, and open owner decisions are surfaced here. No outside signal can silently reorder the NWR board.</p></div><div className="decision-hero__actions"><Button icon="search" onClick={() => navigate("/players")}>Evaluate player</Button><Button icon="market" variant="secondary" onClick={() => navigate("/market")}>Scan market gaps</Button></div></section>
    <div className="metric-grid">
      <MetricCard label="Governed board" value={summary.rankedPlayers} detail="Finished V1 assets" trend="Board authority" icon="board" tone="violet" />
      <MetricCard label="Market coverage" value={summary.marketMatched} detail={`${Math.max(0, summary.rankedPlayers - summary.marketMatched)} unmatched`} trend={data.marketFreshness.sourceAsOf || "No date"} icon="market" tone="gold" />
      <MetricCard label="Rookie review" value={summary.rookieRows} detail={`${summary.manualReviewRookies} manual review`} trend={`${summary.blockedRookies} unresolved`} icon="rookie" tone="crimson" />
      <MetricCard label="Open decisions" value={summary.workspace.openDecisions} detail={`${summary.workspace.savedScenarios} saved scenarios`} trend={`${summary.workspace.targets} targets`} icon="target" tone="cyan" />
    </div>
    <div className="dashboard-grid">
      <Panel title="Highest-leverage market gaps" eyebrow="Investigate · never automatic" action={<Button variant="ghost" onClick={() => navigate("/market")}>Open full market</Button>}>
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
