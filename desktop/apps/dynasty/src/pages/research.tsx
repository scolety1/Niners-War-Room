import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { DynastyBootstrap, PlayerDetail, RookieRanking } from "@nwr/contracts";
import {
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  MetricCard,
  PageHeader,
  Panel,
  SearchInput,
  SelectField,
  StatusBadge,
  formatNumber,
} from "@nwr/ui";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ownerAge,
  ownerDisplay,
  ownerFieldLabel,
  ownerLabel,
  ownerResearchValue,
} from "../lib/owner-copy";
import { matchesPlayerSearch } from "../lib/search";

function OwnerValue({ value, fallback }: { value: unknown; fallback?: string }) {
  const display = ownerDisplay(value, fallback);
  return <span title={display.title}>{display.label}</span>;
}

function decodeAssetId(value: string | undefined) {
  if (!value) return "";
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export function PlayerDetailPage({ client, data }: { client: NwrApiClient; data: DynastyBootstrap }) {
  const params = useParams();
  const navigate = useNavigate();
  const defaultId =
    data.assetOptions.find((asset) => asset.assetType === "Current Player")?.assetId ??
    data.assetOptions[0]?.assetId ??
    "";
  const selectedId = decodeAssetId(params.assetId) || defaultId;
  const [detail, setDetail] = useState<PlayerDetail | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);

  useEffect(() => {
    if (!selectedId) return;
    let active = true;
    setDetail(null);
    setError(null);
    void client
      .dynastyPlayer(selectedId)
      .then((value) => {
        if (active) setDetail(value);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(
            reason instanceof NwrApiError
              ? reason
              : new NwrApiError("Player evidence is unavailable."),
          );
        }
      });
    return () => {
      active = false;
    };
  }, [client, selectedId]);

  const options = data.assetOptions.slice().sort((left, right) => left.name.localeCompare(right.name));
  return (
    <>
      <PageHeader
        eyebrow="Players · One decision hub"
        title="Player Detail"
        description="Identity, rank, evidence, research, and uncertainty in one source-separated view."
        actions={
          <label className="player-jump">
            <span>Jump to player</span>
            <select
              value={selectedId}
              onChange={(event) => navigate(`/players/${encodeURIComponent(event.target.value)}`)}
            >
              {options.map((asset) => (
                <option key={asset.assetId} value={asset.assetId}>
                  {asset.name} · {asset.assetType}
                </option>
              ))}
            </select>
          </label>
        }
        status={
          <>
            <StatusBadge tone="safe" label="Governed identity" />
            <StatusBadge tone="safe" label="Source separated" />
          </>
        }
      />
      {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
      {!detail && !error ? (
        <div className="detail-skeleton">
          <i />
          <i />
          <i />
        </div>
      ) : null}
      {detail ? (
        <PlayerDetailBody
          detail={detail}
          onCompare={() => navigate(`/compare?assets=${encodeURIComponent(detail.assetId)}`)}
          onPersonal={() => navigate(`/workspace?asset=${encodeURIComponent(detail.assetId)}`)}
          onTrade={() => navigate(`/trades?asset=${encodeURIComponent(detail.assetId)}`)}
        />
      ) : null}
    </>
  );
}

export function PlayerDetailBody({
  detail: sourceDetail,
  onCompare,
  onPersonal,
  onTrade,
}: {
  detail: PlayerDetail;
  onCompare: () => void;
  onPersonal: () => void;
  onTrade: () => void;
}) {
  const detail = {
    ...sourceDetail,
    research: Object.fromEntries(
      Object.entries(sourceDetail.research).map(([key, value]) => [
        key,
        ownerResearchValue(key, value),
      ]),
    ),
  };
  const outcomeRows = detail.outcomes.map((row, index) => ({ row: index + 1, ...row }));
  const outcomeColumns = outcomeRows.length
    ? Object.keys(outcomeRows[0]!)
        .filter((key) => key !== "row")
        .slice(0, 8)
        .map((key) => ({
          key,
          label: ownerFieldLabel(key),
          render: (row: Record<string, unknown>) => <OwnerValue value={row[key]} />,
        }))
    : [];
  const decisionBlocked = !detail.selectable;
  const isRookieDraftAsset = Boolean(detail.officialDraftAssetId && detail.rookieIntelligence);
  const rookie = detail.rookieIntelligence!;

  return (
    <>
      <section className="player-identity">
        <div className="player-identity__mark">{detail.position || "NWR"}</div>
        <div>
          <span>
            {ownerLabel(detail.assetType)} · {ownerLabel(detail.team, "Team unavailable")}
          </span>
          <h2>{detail.name}</h2>
          <p>{ownerLabel(detail.authority)}</p>
        </div>
        <div className="player-identity__actions">
          <Button disabled={decisionBlocked} icon="compare" onClick={onCompare} title={decisionBlocked ? "A unique governed selection identity is required." : undefined}>
            Compare
          </Button>
          <Button disabled={decisionBlocked} icon="trade" variant="secondary" onClick={onTrade} title={decisionBlocked ? "A unique governed selection identity is required." : undefined}>
            Trade lab
          </Button>
          <Button icon="board" variant="ghost" onClick={onPersonal}>
            Personal context
          </Button>
        </div>
      </section>
      {detail.refreshAvailable ? (
        <div className="alert-strip">
          <strong>Updated identity available</strong>
          <span>
            Draft eligibility uses newer factual information; the frozen Rookie Review score was
            not rebuilt.
          </span>
        </div>
      ) : null}
      <div className="metric-grid">
        <MetricCard
          label="NWR rank"
          value={detail.rank == null ? (isRookieDraftAsset ? "Manual Review" : "—") : `#${detail.rank}`}
          detail={ownerLabel(detail.positionRank || detail.position)}
          icon="trophy"
          tone="violet"
        />
        <MetricCard
          label={isRookieDraftAsset ? "NWR rookie score" : "NWR score"}
          value={
            isRookieDraftAsset && !detail.modelScoreEligible
              ? "Unavailable"
              : formatNumber(isRookieDraftAsset ? rookie.nwrRookieScore : detail.nwrScore, 2)
          }
          detail={isRookieDraftAsset ? "Evidence-adjusted score used for rank" : "Finished V1 authority"}
          icon="activity"
          tone="crimson"
        />
        {isRookieDraftAsset ? (
          <>
            <MetricCard
              label="NFL draft"
              value={detail.overallPick == null ? "—" : `#${detail.overallPick}`}
              detail={detail.draftRound == null ? "Draft capital unavailable" : `Round ${detail.draftRound}`}
              icon="players"
              tone="gold"
            />
            <MetricCard
              label="Draft status"
              value={detail.draftEligibility}
              detail={detail.identityStatus}
              icon="shield"
              tone="cyan"
            />
          </>
        ) : (
          <>
            <MetricCard label="Age" value={formatNumber(detail.age, 1)} detail="Lifecycle context" icon="players" tone="gold" />
            <MetricCard label="Confidence" value={ownerLabel(detail.confidence)} detail={ownerLabel(detail.risk, "No risk label")} icon="shield" tone="cyan" />
          </>
        )}
      </div>
      <div className="split-view">
        <div className="stack">
          <Panel title="Owner outlook" eyebrow={ownerLabel(detail.range.authority, "Source-separated range")}>
            <div className="range-grid">
              <RangeCell label="Floor" value={detail.range.floor} tone="floor" />
              <RangeCell label="NWR expected" value={detail.range.expected} tone="expected" />
              <RangeCell label="Ceiling" value={detail.range.ceiling} tone="ceiling" />
            </div>
            <p className="copy-muted">{ownerLabel(detail.range.method)}</p>
          </Panel>
          {isRookieDraftAsset ? (
            <>
              <Panel title="What NWR likes" eyebrow="Admitted rookie evidence">
                <ul className="compact-list">{rookie.whatNwrLikes.map((item) => <li key={item}>{item}</li>)}</ul>
              </Panel>
              <Panel title="What holds them back" eyebrow="Admitted rookie evidence">
                <ul className="compact-list">{rookie.whatHoldsBack.map((item) => <li key={item}>{item}</li>)}</ul>
              </Panel>
              <Panel title="Why this rank differs from raw score" eyebrow="Rank contract">
                <p>{rookie.rankScoreExplanation}</p>
              </Panel>
            </>
          ) : (
            <Panel title="Why NWR has them here" eyebrow="Admitted reasons">
              {detail.reasons.length ? (
                <ol className="reason-list">{detail.reasons.map((reason) => <li key={reason}>{ownerLabel(reason)}</li>)}</ol>
              ) : (
                <EmptyState title="No Finished V1 explanation" message="This asset authority does not support a production-rank explanation." />
              )}
            </Panel>
          )}
          {outcomeRows.length ? (
            <Panel title="Outcome V3 matrix" eyebrow="Applicable evidence only">
              <DataTable columns={outcomeColumns} rows={outcomeRows} rowKey={(row) => String(row.row)} />
            </Panel>
          ) : null}
        </div>
        <div className="stack">
          {isRookieDraftAsset ? (
            <>
              <Panel title="Draft & identity" eyebrow="Live factual overlay">
                <dl className="detail-list">
                  <div><dt>Governed player ID</dt><dd>{detail.playerId || "Unavailable"}</dd></div>
                  <div><dt>NFL draft capital</dt><dd>{detail.nflDraftCapital || "Unavailable"}</dd></div>
                  <div><dt>Draft eligibility</dt><dd>{detail.draftEligibility}</dd></div>
                  <div><dt>Score status</dt><dd>{detail.scoreStatus}</dd></div>
                </dl>
              </Panel>
              <Panel title="College & athletic context" eyebrow="Governed components">
                <dl className="detail-list">
                  <div><dt>College production</dt><dd>{rookie.collegeProduction}</dd></div>
                  <div><dt>Market share</dt><dd>{rookie.marketShare}</dd></div>
                  <div><dt>Athletic context</dt><dd>{rookie.athleticContext}</dd></div>
                </dl>
              </Panel>
              <Panel title="Current NFL role context" eyebrow="Factual · excluded from rookie score">
                <p>{rookie.currentRole}</p>
              </Panel>
            </>
          ) : null}
          <Panel title="Risk & uncertainty" eyebrow="Decision guardrail">
            <div className="risk-callout">
              {isRookieDraftAsset ? rookie.biggestUncertainty : ownerLabel(detail.risk, "Not enough information")}
            </div>
            {detail.caveats.length ? <ul className="compact-list">{detail.caveats.map((item) => <li key={item}>{ownerLabel(item)}</li>)}</ul> : null}
          </Panel>
          <Panel title="Research context" eyebrow="Frozen research · display only">
            {Object.keys(detail.research).length ? (
              <dl className="detail-list">
                {Object.entries(detail.research).slice(0, 8).map(([key, value]) => (
                  <div key={key}><dt>{ownerFieldLabel(key)}</dt><dd><OwnerValue value={value} /></dd></div>
                ))}
              </dl>
            ) : (
              <p className="copy-muted">No applicable research context.</p>
            )}
          </Panel>
          {!isRookieDraftAsset ? (
            <Panel title="Market read" eyebrow="Display only">
              <div className={`market-call market-call--${detail.market.band.toLowerCase().includes("buy") ? "buy" : detail.market.band.toLowerCase().includes("sell") ? "sell" : "neutral"}`}>
                <span>{ownerLabel(detail.market.band, "Unavailable")}</span>
                <strong>{detail.market.gap == null ? "—" : `${detail.market.gap > 0 ? "+" : ""}${formatNumber(detail.market.gap, 0)} ranks`}</strong>
                <small>Market #{detail.market.rank ?? "—"} · {detail.market.sourceAsOf || "No date"}</small>
              </div>
              <p className="copy-muted">External comparison never changes NWR authority.</p>
            </Panel>
          ) : null}
        </div>
      </div>
    </>
  );
}

function RangeCell({ label, value, tone }: { label: string; value: string; tone: string }) {
  const sourceNativeLabel =
    { Floor: "Downside signal", "NWR expected": "Research neighborhood", Ceiling: "Upside signal" }[label] ?? label;
  return <div className={`range-cell range-cell--${tone}`}><span>{sourceNativeLabel}</span><strong><OwnerValue value={value} fallback="Not enough information" /></strong><i /></div>;
}

function rookieRecords(rows: RookieRanking[]) {
  return rows.map((row) => ({ ...row }));
}

export function RookieReviewPage({ data }: { data: DynastyBootstrap }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState("ALL");
  const [scoreView, setScoreView] = useState("ALL");
  const rows = useMemo(
    () =>
      data.rookies.filter(
        (row) =>
          (position === "ALL" || row.position === position) &&
          (scoreView === "ALL" || row.modelScoreEligible) &&
          matchesPlayerSearch([row.player, row.team, row.playerId, row.scoreStatus], query),
      ),
    [data.rookies, position, query, scoreView],
  );
  const positions = ["ALL", ...new Set(data.rookies.map((row) => row.position).filter(Boolean))];
  return (
    <>
      <PageHeader
        eyebrow="2026 class · Review authority"
        title="Rookie Intelligence Board"
        description="The score shown is the evidence-adjusted score that actually orders the board. Manual-review assets stay draftable."
        status={
          <>
            <StatusBadge tone="safe" label={`${data.rookieReadiness.officialDrafted} official assets`} />
            <StatusBadge tone="review" label={`${data.rookieReadiness.manualReview} manual review`} />
          </>
        }
      />
      <div className="alert-strip"><strong>{data.rookieReadiness.alertTitle}</strong><span>{data.rookieReadiness.alertMessage} Missing evidence never becomes zero.</span></div>
      <Panel title="2026 prospect board" eyebrow="Score · evidence · research · current role">
        <div className="toolbar">
          <SearchInput value={query} onChange={setQuery} placeholder="Find a rookie…" />
          <div className="chip-row">{positions.map((value) => <button className={`filter-chip ${position === value ? "filter-chip--active" : ""}`} key={value} onClick={() => setPosition(value)}>{value}</button>)}</div>
          <SelectField label="Score coverage" value={scoreView} onChange={setScoreView} options={[{ value: "ALL", label: "All draftable rookies" }, { value: "SCORED", label: "Show scored only" }]} />
        </div>
        <DataTable
          columns={[
            { key: "rank", label: "Rookie rank", render: (row) => row.rank == null ? <span className="blocked-rank">Manual Review</span> : <span className="rank-cell"><i /><b>#{String(row.rank)}</b></span> },
            { key: "player", label: "Player", render: (row) => <span className="player-cell"><strong>{String(row.player)}</strong></span> },
            { key: "position", label: "Pos", align: "center", render: (row) => <span className="position-pill">{String(row.position)}</span> },
            { key: "team", label: "Team", render: (row) => <OwnerValue value={row.team} /> },
            { key: "nflDraftCapital", label: "NFL pick", render: (row) => <OwnerValue value={row.nflDraftCapital} /> },
            { key: "boardScore", label: "NWR rookie score", align: "right", render: (row) => row.modelScoreEligible ? formatNumber(row.boardScore as number, 2) : <span className="blocked-rank">Manual Review</span> },
            { key: "draftRange", label: "Draft range band", render: (row) => <OwnerValue value={row.draftRange} /> },
            { key: "evidenceBand", label: "Evidence band", render: (row) => <OwnerValue value={row.evidenceBand} /> },
            { key: "collegeProduction", label: "College production", render: (row) => <OwnerValue value={row.collegeProduction} /> },
            { key: "age", label: "Age", align: "right", render: (row) => ownerAge(row.age) },
            { key: "athleticContext", label: "Athletic context", render: (row) => <OwnerValue value={row.athleticContext} /> },
            { key: "researchNeighborhood", label: "Research neighborhood", render: (row) => <OwnerValue value={row.researchNeighborhood} /> },
            { key: "currentRole", label: "Current role", render: (row) => <OwnerValue value={row.currentRole} /> },
            { key: "confidence", label: "Confidence", render: (row) => <OwnerValue value={row.confidence} /> },
            { key: "warnings", label: "Warning", render: (row) => <OwnerValue value={row.warnings} /> },
          ]}
          rows={rookieRecords(rows)}
          rowKey={(row) => String(row.assetId)}
          onRowClick={(row) => navigate(`/players/${encodeURIComponent(String(row.assetId))}`)}
        />
      </Panel>
    </>
  );
}
