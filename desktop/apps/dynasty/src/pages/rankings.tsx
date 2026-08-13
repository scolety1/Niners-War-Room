import type { AssetOption, DynastyBootstrap, DynastyRanking } from "@nwr/contracts";
import { Button, DataTable, PageHeader, Panel, SearchInput, SegmentedControl, SelectField, StatusBadge, formatNumber, stableSortRows } from "@nwr/ui";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ownerDisplay, ownerLabel } from "../lib/owner-copy";

function OwnerValue({ value }: { value: unknown }) {
  const display = ownerDisplay(value);
  return <span title={display.title}>{display.label}</span>;
}

function marketClass(value: unknown) {
  const signal = String(value).toLowerCase();
  return signal.includes("buy") || signal.includes("nwr higher") ? "buy" : signal.includes("sell") || signal.includes("market higher") ? "sell" : "aligned";
}

function rankingRecords(rows: DynastyRanking[]) { return rows.map((row) => ({ ...row })); }

export function assetExplorerRows(
  rows: AssetOption[],
  query: string,
  assetType: string,
  evidence: string,
) {
  const needle = query.trim().toLowerCase();
  return rows.filter((row) => {
    if (assetType !== "All" && row.assetType !== assetType) return false;
    if (evidence === "Available" && row.blocked) return false;
    if (evidence === "Blocked" && !row.blocked) return false;
    return !needle || `${row.name} ${row.team} ${row.position} ${row.authority} ${row.assetType}`.toLowerCase().includes(needle);
  });
}

export function AssetExplorerPage({ data }: { data: DynastyBootstrap }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [assetType, setAssetType] = useState("All");
  const [evidence, setEvidence] = useState("All");
  const [tableResetKey, setTableResetKey] = useState(0);
  const assetTypes = ["All", ...new Set(data.assetOptions.map((row) => row.assetType).filter(Boolean))];
  const rows = useMemo(
    () => assetExplorerRows(data.assetOptions, query, assetType, evidence),
    [assetType, data.assetOptions, evidence, query],
  );
  const blockedCount = data.assetOptions.filter((row) => row.blocked).length;
  const reset = () => {
    setQuery("");
    setAssetType("All");
    setEvidence("All");
    setTableResetKey((value) => value + 1);
  };

  return <>
    <PageHeader
      eyebrow="Players · governed registry"
      title="Asset Explorer"
      description="Browse current players, Rookie Review assets, and future picks without merging their source scales or changing NWR authority."
      status={<><StatusBadge tone="safe" label={`${data.assetOptions.length} governed assets`} /><StatusBadge tone={blockedCount ? "review" : "safe"} label={`${blockedCount} evidence blocked`} /></>}
      actions={<Button icon="compare" onClick={() => navigate("/compare")}>Compare assets</Button>}
    />
    <div className="alert-strip"><strong>Read-only registry</strong><span>Ranks remain source-native. Missing evidence stays unavailable, never zero, and blocked assets remain visible.</span></div>
    <Panel title="Governed asset registry" eyebrow="Current players · rookies · picks">
      <div className="toolbar">
        <SearchInput value={query} onChange={setQuery} placeholder="Find an asset, team, position, or authority…" />
        <SelectField label="Asset type" value={assetType} onChange={setAssetType} options={assetTypes.map((value) => ({ value, label: value }))} />
        <SelectField label="Evidence" value={evidence} onChange={setEvidence} options={["All", "Available", "Blocked"].map((value) => ({ value, label: value }))} />
        <Button icon="undo" onClick={reset} variant="ghost">Reset</Button>
      </div>
      <DataTable columns={[
        { key: "rank", label: "Source rank", sort: "number", width: "90px", render: (row) => row.rank == null ? "—" : `#${String(row.rank)}` },
        { key: "name", label: "Asset", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.name)}</strong><small>{ownerLabel(row.team)} · {ownerLabel(row.position)}</small></span> },
        { key: "assetType", label: "Asset type", sort: "text", render: (row) => ownerLabel(row.assetType) },
        { key: "authority", label: "Source authority", sort: "text", render: (row) => ownerLabel(row.authority) },
        { key: "blocked", label: "Evidence", sort: "text", render: (row) => <StatusBadge tone={row.blocked ? "blocked" : "safe"} label={row.blocked ? "Blocked" : "Available"} /> },
      ]} resetKey={tableResetKey} rows={rows.map((row) => ({ ...row }))} rowKey={(row) => String(row.assetId)} onRowClick={(row) => navigate(`/players/${encodeURIComponent(String(row.assetId))}`)} />
    </Panel>
  </>;
}

export function RankingsPage({ data }: { data: DynastyBootstrap }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState("ALL");
  const [team, setTeam] = useState("ALL");
  const [market, setMarket] = useState("All");
  const [limit, setLimit] = useState("50");
  const [tableResetKey, setTableResetKey] = useState(0);
  const filtered = useMemo(() => data.rankings.filter((row) => {
    if (position !== "ALL" && row.position !== position) return false;
    if (team !== "ALL" && row.team !== team) return false;
    if (market !== "All" && row.marketBand !== market) return false;
    return !query.trim() || `${row.player} ${row.team}`.toLowerCase().includes(query.trim().toLowerCase());
  }).slice(0, Number(limit)), [data.rankings, limit, market, position, query, team]);
  const positions = ["ALL", ...new Set(data.rankings.map((row) => row.position).filter(Boolean))];
  const teams = ["ALL", ...new Set(data.rankings.map((row) => row.team).filter(Boolean))].sort();
  const markets = ["All", ...new Set(data.rankings.map((row) => row.marketBand).filter(Boolean))];
  const reset = () => {
    setQuery("");
    setPosition("ALL");
    setTeam("ALL");
    setMarket("All");
    setLimit("50");
    setTableResetKey((value) => value + 1);
  };
  return <>
    <PageHeader eyebrow="Players · Finished V1 order" title="Dynasty Rankings" description="The accepted long-term board, translated for owner decisions without changing its authority." status={<><StatusBadge tone="safe" label={`${data.rankings.length} ranked players`} /><StatusBadge tone="review" label={`Market ${data.marketFreshness.sourceAsOf || "date unavailable"}`} /></>} actions={<Button icon="compare" onClick={() => navigate("/compare")}>Open Compare</Button>} />
    <Panel title="Full player board" eyebrow="Rank · range · market · risk">
      <div className="toolbar"><SearchInput value={query} onChange={setQuery} placeholder="Find a player or team…" /><SegmentedControl label="Position" options={positions} value={position} onChange={setPosition} /><SelectField label="Team" value={team} onChange={setTeam} options={teams.map((value) => ({ value, label: value === "ALL" ? "All teams" : value }))} /><SelectField label="Market view" value={market} onChange={setMarket} options={markets.map((value) => ({ value, label: ownerLabel(value) }))} /><SelectField label="Show" value={limit} onChange={setLimit} options={[25,50,100,data.rankings.length].map((value) => ({ value: String(value), label: `${value} rows` }))} /><Button icon="undo" onClick={reset} variant="ghost">Reset</Button></div>
      <DataTable columns={[
        { key: "rank", label: "Rank", sort: "number", width: "65px", render: (row) => <span className="rank-cell"><i /><b>#{String(row.rank ?? "—")}</b></span> },
        { key: "player", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.player)}</strong><small>{ownerLabel(row.team)} · Age {String(row.age ?? "—")}</small></span> },
        { key: "position", label: "Pos", sort: "text", align: "center", render: (row) => <span className="position-pill">{String(row.position)}</span> },
        { key: "positionRank", label: "Pos rank", sort: "text", render: (row) => <OwnerValue value={row.positionRank} /> },
        { key: "nwrScore", label: "NWR score", sort: "number", align: "right", render: (row) => formatNumber(row.nwrScore as number, 2) },
        { key: "range", label: "Expected window", sort: "text", render: (row) => <OwnerValue value={row.range} /> },
        { key: "marketBand", label: "Market", sort: "text", render: (row) => <span className={`market-signal market-signal--${marketClass(row.marketBand)}`}><i />{ownerLabel(row.marketBand)}</span> },
        { key: "marketGap", label: "Gap", sort: "number", align: "right", render: (row) => row.marketGap == null ? "—" : `${(row.marketGap as number) > 0 ? "+" : ""}${formatNumber(row.marketGap as number, 0)}` },
        { key: "confidence", label: "Confidence", sort: "text", render: (row) => <OwnerValue value={row.confidence} /> },
        { key: "risk", label: "Risk", sort: "text", render: (row) => <OwnerValue value={row.risk} /> },
      ]} resetKey={tableResetKey} rows={rankingRecords(filtered)} rowKey={(row) => String(row.assetId)} onRowClick={(row) => navigate(`/players/${encodeURIComponent(String(row.assetId))}`)} />
    </Panel>
  </>;
}

export function MarketPage({ data }: { data: DynastyBootstrap }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [signal, setSignal] = useState("All");
  const [sort, setSort] = useState("nwr");
  const signals = ["All", ...new Set(data.rankings.map((row) => row.marketBand).filter(Boolean))];
  const rows = useMemo(() => {
    const result = data.rankings.filter((row) => row.marketRank != null && (signal === "All" || row.marketBand === signal) && (!query || row.player.toLowerCase().includes(query.toLowerCase())));
    if (sort === "market") return stableSortRows(result, (row) => row.marketGap, "number", "ascending");
    if (sort === "rank") return stableSortRows(result, (row) => row.rank, "number", "ascending");
    return stableSortRows(result, (row) => row.marketGap, "number", "descending");
  }, [data.rankings, query, signal, sort]);
  const count = (needle: string) => data.rankings.filter((row) => row.marketBand === needle).length;
  return <>
    <PageHeader eyebrow="NWR analysis · Display only" title="Market Disagreement Radar" description="External consensus is a comparison lens. It never changes NWR rank, score, or trade authority." status={<><StatusBadge tone="review" label={ownerLabel(data.marketFreshness.status, "Freshness review")} /><StatusBadge tone="safe" label={`${data.summary.marketMatched} exact matches`} /></>} />
    <div className="alert-strip"><strong>Snapshot {data.marketFreshness.sourceAsOf || "unknown"}</strong><span>{ownerLabel(data.marketFreshness.message, "Treat disagreement as a prompt to investigate, not an automatic transaction.")}</span></div>
    <div className="metric-grid market-metrics"><div className="signal-metric signal-metric--buy"><strong>{count("Potential Buy")}</strong><span>Potential buy</span></div><div className="signal-metric"><strong>{count("NWR Higher")}</strong><span>NWR higher</span></div><div className="signal-metric signal-metric--neutral"><strong>{count("Aligned")}</strong><span>Aligned</span></div><div className="signal-metric signal-metric--sell"><strong>{count("Market Higher") + count("Potential Sell / Caution")}</strong><span>Market higher</span></div></div>
    <Panel title="Disagreement worklist" eyebrow="Exact player identity · rank gap">
      <div className="toolbar"><SearchInput value={query} onChange={setQuery} /><SelectField label="Signal" value={signal} onChange={setSignal} options={signals.map((value) => ({ value, label: ownerLabel(value) }))} /><SelectField label="Sort" value={sort} onChange={setSort} options={[{value:"nwr",label:"Biggest NWR edge"},{value:"market",label:"Biggest market edge"},{value:"rank",label:"NWR rank"}]} /></div>
      <DataTable columns={[
        { key: "rank", label: "NWR", render: (row) => `#${String(row.rank ?? "—")}` },
        { key: "player", label: "Player", render: (row) => <span className="player-cell"><strong>{String(row.player)}</strong><small>{ownerLabel(row.team)} · {ownerLabel(row.positionRank)}</small></span> },
        { key: "marketBand", label: "Signal", render: (row) => <span className={`market-signal market-signal--${marketClass(row.marketBand)}`}><i />{ownerLabel(row.marketBand)}</span> },
        { key: "marketRank", label: "Market rank", align: "right", render: (row) => `#${String(row.marketRank ?? "—")}` },
        { key: "marketGap", label: "NWR vs market", align: "right", render: (row) => `${(row.marketGap as number) > 0 ? "+" : ""}${formatNumber(row.marketGap as number, 0)}` },
        { key: "nwrView", label: "NWR view", render: (row) => <OwnerValue value={row.nwrView} /> }, { key: "confidence", label: "Confidence", render: (row) => <OwnerValue value={row.confidence} /> }, { key: "risk", label: "Risk", render: (row) => <OwnerValue value={row.risk} /> },
      ]} rows={rankingRecords(rows)} rowKey={(row) => String(row.assetId)} onRowClick={(row) => navigate(`/players/${encodeURIComponent(String(row.assetId))}`)} />
    </Panel>
  </>;
}
