import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type {
  AssetOption,
  AssetOwnership,
  AssetOwnershipEntry,
  DynastyBootstrap,
  DynastyComparison,
  TeamWindow,
  TradeDecision,
  TradeWorkspace,
} from "@nwr/contracts";
import {
  Button,
  ErrorState,
  Icon,
  PageHeader,
  Panel,
  SearchInput,
  SegmentedControl,
  StatusBadge,
  formatNumber,
} from "@nwr/ui";
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { matchesPlayerSearch } from "../lib/search";
import { ownershipLookup, resolveOwnershipDisplay } from "../lib/ownership";

const TRADE_SIDE_LIMIT = 6;

// ----------------------------------------------------------------------
// Dynasty League Import V1 (Worker 4): Compare + Trade Decision Lab
// ownership wiring. Every function below is a PURE, display-only layer on
// top of already-computed data -- none of it reads or writes any
// comparison score/verdict or trade-value field, satisfying the owner's
// explicit hard boundary ("ownership is a display/annotation/warning layer
// only"). See `desktop_facade.compare_dynasty_assets`/
// `evaluate_dynasty_trade`'s own comments for the backend half of the same
// guarantee.
// ----------------------------------------------------------------------

/** Real roster-owned asset ids from the already-annotated `assetOptions`
 * list (bootstrap-time truth) -- the "REAL default" the dispatch asked
 * for, used only to pre-fill the give side; the owner can always remove or
 * add manually afterward (see `fillTradeSideFromRoster`). */
export function rosterOwnedAssetIds(assets: readonly AssetOption[]): string[] {
  return assets
    .filter((asset) => asset.ownership?.ownershipStatus === "OWNED" && asset.ownership.isMyTeam)
    .map((asset) => asset.assetId);
}

/** Appends real roster asset ids onto an existing manual selection --
 * never removes or reorders what the owner already picked, skips anything
 * already selected on either side, and still respects the side limit. A
 * real default sourced from actual roster ownership, not a forced
 * constraint: every asset it adds remains individually removable exactly
 * like a manually added one. */
export function fillTradeSideFromRoster(
  current: readonly string[],
  other: readonly string[],
  rosterAssetIds: readonly string[],
  limit = TRADE_SIDE_LIMIT,
): string[] {
  const next = [...current];
  for (const assetId of rosterAssetIds) {
    if (next.length >= limit) break;
    if (next.includes(assetId) || other.includes(assetId)) continue;
    next.push(assetId);
  }
  return next;
}

export type TradeRosterWarningKind =
  | "GIVE_OWNED_BY_OPPONENT"
  | "GIVE_NOT_ON_ROSTER"
  | "GIVE_UNRESOLVED"
  | "RECEIVE_ALREADY_OWNED";

export interface TradeRosterWarning {
  assetId: string;
  kind: TradeRosterWarningKind;
  message: string;
}

/** The owner's explicit correctness requirement: flag (never block) a
 * "give" asset that real, live ownership data says is NOT actually on the
 * owner's roster -- an opponent's asset, a free agent, or (for a rookie
 * asset with no crosswalk yet) genuinely unconfirmable. Also flags the
 * mirror-image oddity on the receive side (already owned). An asset with
 * no ownership entry at all (no league connected, or an asset type with no
 * ownership concept such as a draft pick) produces no warning -- never
 * guessed. This never touches `give`/`receive` themselves or any trade
 * score -- it only classifies what is already selected. */
export function resolveTradeRosterWarnings(
  give: readonly string[],
  receive: readonly string[],
  ownership: ReadonlyMap<string, AssetOwnership>,
  nameForAsset: (assetId: string) => string,
): TradeRosterWarning[] {
  const warnings: TradeRosterWarning[] = [];
  for (const assetId of give) {
    const entry = ownership.get(assetId);
    if (!entry) continue;
    if (entry.ownershipStatus === "OWNED" && entry.isMyTeam) continue;
    const name = nameForAsset(assetId);
    if (entry.ownershipStatus === "OWNED") {
      warnings.push({
        assetId,
        kind: "GIVE_OWNED_BY_OPPONENT",
        message: `${name} is on your give side, but is currently owned by ${entry.rosterTeamName || "another team"} in your connected league, not your roster.`,
      });
    } else if (entry.ownershipStatus === "FREE_AGENT") {
      warnings.push({
        assetId,
        kind: "GIVE_NOT_ON_ROSTER",
        message: `${name} is on your give side, but is a free agent in your connected league, not on your roster.`,
      });
    } else if (entry.ownershipStatus === "UNRESOLVED") {
      warnings.push({
        assetId,
        kind: "GIVE_UNRESOLVED",
        message: `${name}'s real ownership could not be confirmed (${entry.reason || "no identity crosswalk yet"}) -- verify manually before trading it away.`,
      });
    }
  }
  for (const assetId of receive) {
    const entry = ownership.get(assetId);
    if (entry?.ownershipStatus === "OWNED" && entry.isMyTeam) {
      warnings.push({
        assetId,
        kind: "RECEIVE_ALREADY_OWNED",
        message: `${nameForAsset(assetId)} is on your receive side, but is already on your roster.`,
      });
    }
  }
  return warnings;
}

function OwnershipTag({ ownership }: { ownership: AssetOwnership | undefined }) {
  const display = resolveOwnershipDisplay(ownership);
  if (!display) return null;
  return <StatusBadge tone={display.tone} label={display.label} />;
}

export function bridgeBadgeTone(badge: string): "safe" | "blocked" | "review" {
  if (badge === "PRODUCTION") return "safe";
  if (badge === "INSUFFICIENT EVIDENCE") return "blocked";
  return "review";
}

export function bridgeDecisionGroups(result: DynastyComparison) {
  return {
    horizons: result.bridge?.decisions.slice(0, 4) ?? [],
    traits: result.bridge?.decisions.slice(4) ?? [],
  };
}

export function ownerBridgePreference(preferred: string, badge: string): string {
  if (
    badge === "RESEARCH ONLY" &&
    preferred !== "TOO CLOSE" &&
    preferred !== "INSUFFICIENT EVIDENCE"
  ) {
    return `NWR research leans ${preferred}`;
  }
  return preferred;
}

export function nextTradeSide(
  current: readonly string[],
  other: readonly string[],
  assetId: string,
  limit = TRADE_SIDE_LIMIT,
): string[] {
  if (current.includes(assetId)) return current.filter((value) => value !== assetId);
  if (other.includes(assetId) || current.length >= limit) return [...current];
  return [...current, assetId];
}

export function isCurrentDecisionRequest(
  requestId: number,
  inputRevision: number,
  currentRequestId: number,
  currentInputRevision: number,
): boolean {
  return requestId === currentRequestId && inputRevision === currentInputRevision;
}

export function isSameTradePackage(
  give: readonly string[],
  receive: readonly string[],
  evaluatedGive: readonly string[],
  evaluatedReceive: readonly string[],
): boolean {
  return (
    give.length === evaluatedGive.length &&
    receive.length === evaluatedReceive.length &&
    give.every((assetId, index) => assetId === evaluatedGive[index]) &&
    receive.every((assetId, index) => assetId === evaluatedReceive[index])
  );
}

export function ownerDimensionLabel(value: string): string {
  const spaced = value
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replaceAll("_", " ")
    .trim();
  return spaced ? `${spaced.charAt(0).toUpperCase()}${spaced.slice(1)}` : "Evidence";
}

export function canSelectAsset(asset: AssetOption): boolean {
  return asset.selectable;
}

function AssetPicker({
  assets,
  selected,
  unavailable = new Set<string>(),
  onToggle,
  limit,
  label,
  disabled = false,
}: {
  assets: AssetOption[];
  selected: string[];
  unavailable?: ReadonlySet<string>;
  onToggle: (assetId: string) => void;
  limit: number;
  label: string;
  disabled?: boolean;
}) {
  const [query, setQuery] = useState("");
  const visible = useMemo(
    () =>
      assets
        .filter((asset) =>
          matchesPlayerSearch(
            [asset.name, asset.position, asset.team, asset.playerId, asset.scoreStatus],
            query,
          ),
        )
        .slice(0, 120),
    [assets, query],
  );
  return (
    <div aria-busy={disabled || undefined} className="picker-shell">
      <div className="picker-shell__header">
        <strong>{label}</strong>
        <span>
          {selected.length}/{limit}
        </span>
      </div>
      <SearchInput
        value={query}
        onChange={setQuery}
        placeholder="Search governed assets…"
      />
      <div className="asset-picker">
        {visible.map((asset) => {
          const selectedHere = selected.includes(asset.assetId);
          const selectedElsewhere = !selectedHere && unavailable.has(asset.assetId);
          const selectionBlocked = !canSelectAsset(asset) || selectedElsewhere;
          return (
            <button
              aria-disabled={selectionBlocked || disabled || undefined}
              className={selectedHere ? "selected" : ""}
              disabled={
                disabled ||
                selectionBlocked ||
                (!selectedHere && selected.length >= limit)
              }
              key={asset.assetId}
              onClick={() => onToggle(asset.assetId)}
              title={
                !asset.selectable
                  ? "This asset lacks a unique governed selection identity"
                  : selectedElsewhere
                    ? "Already selected on the other trade side"
                    : undefined
              }
              type="button"
            >
              <span>
                <strong>{asset.name}</strong>
                <small>
                  {asset.assetType} · {asset.position || "—"}{" "}
                  {asset.team ? `· ${asset.team}` : ""}
                </small>
              </span>
              {selectionBlocked ? (
                <em>{selectedElsewhere ? "Other side" : "Unavailable"}</em>
              ) : asset.evidenceBlocked ? (
                <em>Manual review</em>
              ) : (
                <b>{asset.rank == null ? "—" : `#${asset.rank}`}</b>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function SelectedChips({
  assets,
  selected,
  onRemove,
  disabled = false,
}: {
  assets: AssetOption[];
  selected: string[];
  onRemove: (assetId: string) => void;
  disabled?: boolean;
}) {
  const lookup = new Map(assets.map((asset) => [asset.assetId, asset]));
  return (
    <div className="chip-row selected-assets">
      {selected.map((assetId) => (
        <span className="chip" key={assetId}>
          {lookup.get(assetId)?.name ?? assetId}
          {lookup.get(assetId)?.ownership ? (
            <OwnershipTag ownership={lookup.get(assetId)?.ownership} />
          ) : null}
          <button
            aria-label={`Remove ${lookup.get(assetId)?.name ?? assetId}`}
            disabled={disabled}
            onClick={() => onRemove(assetId)}
            type="button"
          >
            <Icon name="close" size={11} />
          </button>
        </span>
      ))}
    </div>
  );
}

export function ComparePage({ client, data }: { client: NwrApiClient; data: DynastyBootstrap }) {
  const [search] = useSearchParams();
  const [selected, setSelected] = useState<string[]>(() => {
    const eligibleAssets = new Set(
      data.assetOptions.filter(canSelectAsset).map((asset) => asset.assetId),
    );
    const requestedAssets = search.get("assets")?.split(",").filter(Boolean);
    const initial = requestedAssets
      ? requestedAssets.filter((assetId) => eligibleAssets.has(assetId))
      : [...eligibleAssets].slice(0, 2);
    return [...new Set(initial)].slice(0, 4);
  });
  const [comparison, setComparison] = useState<DynastyComparison | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRevision = useRef(0);
  const requestSequence = useRef(0);

  const invalidate = () => {
    inputRevision.current += 1;
    requestSequence.current += 1;
    setComparison(null);
    setError(null);
    setLoading(false);
  };
  const toggle = (assetId: string) => {
    if (loading) return;
    invalidate();
    setSelected((current) =>
      current.includes(assetId)
        ? current.filter((value) => value !== assetId)
        : [...current, assetId].slice(0, 4),
    );
  };
  const run = async () => {
    if (selected.length < 2 || loading) return;
    const requestId = ++requestSequence.current;
    const revision = inputRevision.current;
    const requested = [...selected];
    setLoading(true);
    setError(null);
    try {
      const result = await client.dynastyCompare(requested);
      if (
        isCurrentDecisionRequest(
          requestId,
          revision,
          requestSequence.current,
          inputRevision.current,
        )
      ) {
        setComparison(result);
      }
    } catch (reason) {
      if (
        isCurrentDecisionRequest(
          requestId,
          revision,
          requestSequence.current,
          inputRevision.current,
        )
      ) {
        setError(
          reason instanceof NwrApiError
            ? reason
            : new NwrApiError("Comparison could not be built."),
        );
      }
    } finally {
      if (
        isCurrentDecisionRequest(
          requestId,
          revision,
          requestSequence.current,
          inputRevision.current,
        )
      ) {
        setLoading(false);
      }
    }
  };
  useEffect(() => {
    if (selected.length >= 2) void run();
  }, []);

  return (
    <>
      <PageHeader
        eyebrow="Decision lab · Source separated"
        title="Compare Players"
        description="See who NWR prefers by horizon before opening dense evidence. No common scale is invented across unsupported authorities."
        status={
          <>
            <StatusBadge tone="safe" label="2–4 governed assets" />
            <StatusBadge tone="safe" label="Horizon specific" />
          </>
        }
        actions={
          <Button
            disabled={selected.length < 2 || loading}
            icon="compare"
            onClick={() => void run()}
          >
            {loading ? "Building comparison…" : "Compare now"}
          </Button>
        }
      />
      <div className="split-view compare-builder">
        <Panel title="Select assets" eyebrow="Current players · rookies · picks">
          <AssetPicker
            assets={data.assetOptions}
            disabled={loading}
            selected={selected}
            onToggle={toggle}
            limit={4}
            label="Comparison set"
          />
          <SelectedChips
            assets={data.assetOptions}
            disabled={loading}
            selected={selected}
            onRemove={toggle}
          />
        </Panel>
        <Panel title="Comparison contract" eyebrow="Trust guardrails">
          <ul className="compact-list">
            <li>Short-, medium-, and long-term leans retain their own authority.</li>
            <li>Missing evidence stays unavailable, never zero.</li>
            <li>Market context cannot replace primary NWR evidence.</li>
          </ul>
        </Panel>
      </div>
      {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
      {comparison ? <ComparisonResult result={comparison} /> : null}
    </>
  );
}

function RangeCell({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className={`range-cell range-cell--${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <i />
    </div>
  );
}

function ComparisonResult({ result }: { result: DynastyComparison }) {
  const dimensions = Array.from(
    new Set(result.players.flatMap((player) => Object.keys(player.dimensions))),
  );
  const bridge = result.bridge;
  const { horizons: horizonDecisions, traits: traitDecisions } = bridgeDecisionGroups(result);
  // Dynasty League Import V1 (Worker 4): ownership is looked up from
  // `result.ownership` -- a real, separate annotation attached AFTER
  // `leans`/`ranges`/`players`/`bridge` were already fully computed on the
  // backend (see `desktop_facade.compare_dynasty_assets`). Rendered only
  // as extra display context next to each player's own panel; it never
  // feeds into any lean/range/dimension/advantage value above.
  const ownership = useMemo(() => ownershipLookup(result.ownership), [result.ownership]);
  return (
    <div className="comparison-result">
      <div className="section-title">
        <h2>{bridge ? `${bridge.players[0]} vs ${bridge.players[1]}` : "NWR preference by horizon"}</h2>
        <span>{bridge ? "Rookie ↔ Veteran mode" : "Decision first · evidence second"}</span>
      </div>
      {result.dynastyLeague ? (
        <p className="copy-muted">
          Ownership context: connected to {result.dynastyLeague.leagueName}. This label never
          changes a lean, range, dimension, or advantage above -- it is separate display context
          only.
        </p>
      ) : null}
      {bridge ? (
        <>
          <div className="bridge-horizon-grid">
            {horizonDecisions.map((decision) => (
              <article key={decision.key}>
                <header>
                  <span>{decision.label}</span>
                  <StatusBadge tone={bridgeBadgeTone(decision.badge)} label={decision.badge} />
                </header>
                <strong>{ownerBridgePreference(decision.preferred, decision.badge)}</strong>
                <p>{decision.reason}</p>
                <small>{decision.authority}</small>
              </article>
            ))}
          </div>
          <div className="bridge-trait-grid">
            {traitDecisions.map((decision) => (
              <article key={decision.key}>
                <span>{decision.label}</span>
                <strong>{ownerBridgePreference(decision.preferred, decision.badge)}</strong>
                <StatusBadge tone={bridgeBadgeTone(decision.badge)} label={decision.badge} />
                <p>{decision.reason}</p>
              </article>
            ))}
          </div>
          <Panel title="Immediate production context" eyebrow="Shared 2026 Redraft authority">
            <div className="bridge-production-grid">
              {bridge.immediateProduction.map((player) => (
                <article key={player.assetId || player.player}>
                  <strong>{player.player}</strong>
                  {player.available ? (
                    <dl>
                      <div><dt>Projected points</dt><dd>{formatNumber(player.projectedPoints, 1)}</dd></div>
                      <div><dt>Overall / position</dt><dd>#{player.overallRank} / #{player.positionRank}</dd></div>
                      <div><dt>Replacement-adjusted</dt><dd>{formatNumber(player.replacementAdjustedValue, 1)}</dd></div>
                      <div><dt>Confidence</dt><dd>{player.confidence}</dd></div>
                    </dl>
                  ) : <p>Exact-ID current-season evidence is unavailable.</p>}
                  <small>{player.uncertainty}</small>
                </article>
              ))}
            </div>
          </Panel>
          <Panel title="Why" eyebrow="Source-separated evidence">
            <ul className="compact-list">{bridge.why.map((item) => <li key={item}>{item}</li>)}</ul>
          </Panel>
          <p className="copy-muted">
            Rookie Review Score and veteran Finished V1 Score are not directly comparable. No shared 0–100 value or additive package score is shown.
          </p>
        </>
      ) : (
        <>
          <div className="horizon-grid">
            {result.leans.map((lean) => (
              <article key={lean.horizon}>
                <span>{lean.horizon}</span>
                <strong>{lean.preferred}</strong>
                <p>{lean.reason}</p>
                <small>{lean.authority}</small>
              </article>
            ))}
          </div>
          <p className="copy-muted">
            These are source-native research signals, not one shared numeric scale or a forecast interval.
          </p>
        </>
      )}
      <div className="advantage-grid">
        {result.ranges.map((range) => (
          <Panel key={range.assetId} title={range.player} eyebrow={range.ageWindow}>
            {ownership.get(range.assetId) ? (
              // Rendered in the panel BODY, never the header, to avoid a
              // real, reproduced-live overlap bug: `.panel__header` does
              // not wrap, and a wide ownership badge next to a long
              // multi-word eyebrow (e.g. "Advantages & uncertainty")
              // visually overlapped and clipped the eyebrow text.
              <div className="panel-ownership-line">
                <OwnershipTag ownership={ownership.get(range.assetId)} />
              </div>
            ) : null}
            <div className="range-grid">
              <RangeCell label="Downside signal" value={range.floor} tone="floor" />
              <RangeCell label="Research neighborhood" value={range.expected} tone="expected" />
              <RangeCell label="Upside signal" value={range.ceiling} tone="ceiling" />
            </div>
            <div className="risk-callout">{range.risk}</div>
            <p className="copy-muted">
              {[range.authority, range.method].filter(Boolean).join(" · ")}
            </p>
          </Panel>
        ))}
      </div>
      <Panel title="Decision matrix" eyebrow="Source-separated evidence">
        <div className="matrix">
          <div className="matrix__row matrix__head">
            <span>Dimension</span>
            {result.players.map((player) => (
              <strong key={player.assetId}>{player.player}</strong>
            ))}
          </div>
          {dimensions.map((dimension) => (
            <div className="matrix__row" key={dimension}>
              <span>{ownerDimensionLabel(dimension)}</span>
              {result.players.map((player) => (
                <b key={player.assetId}>{String(player.dimensions[dimension] ?? "—")}</b>
              ))}
            </div>
          ))}
        </div>
      </Panel>
      <div className="advantage-grid">
        {result.players.map((player) => (
          <Panel key={player.assetId} title={player.player} eyebrow="Advantages & uncertainty">
            {ownership.get(player.assetId) ? (
              <div className="panel-ownership-line">
                <OwnershipTag ownership={ownership.get(player.assetId)} />
              </div>
            ) : null}
            <div className="pros-cons">
              <div>
                <strong>Advantages</strong>
                <ul>
                  {player.advantages.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>Risks</strong>
                <ul>
                  {player.risks.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
          </Panel>
        ))}
      </div>
      {result.warnings.map((warning) => (
        <div className="alert-strip" key={warning}>
          {warning}
        </div>
      ))}
    </div>
  );
}

export function TradeLabPage({ client, data }: { client: NwrApiClient; data: DynastyBootstrap }) {
  const [search] = useSearchParams();
  const requestedAsset = search.get("asset") ?? "";
  const initialAsset = data.assetOptions.some(
    (asset) => asset.assetId === requestedAsset && canSelectAsset(asset),
  )
    ? requestedAsset
    : "";
  const [give, setGive] = useState<string[]>(initialAsset ? [initialAsset] : []);
  const [receive, setReceive] = useState<string[]>([]);
  const [teamWindow, setTeamWindow] = useState<TeamWindow>("Balanced");
  const [decision, setDecision] = useState<TradeDecision | null>(null);
  const [evaluatedPackage, setEvaluatedPackage] = useState<{
    give: string[];
    receive: string[];
  } | null>(null);
  const [workspace, setWorkspace] = useState<TradeWorkspace | null>(null);
  const [savedSelection, setSavedSelection] = useState("");
  const [scenarioId, setScenarioId] = useState<string | null>(null);
  const [title, setTitle] = useState("Trade scenario");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<NwrApiError | null>(null);
  const [statusMessage, setStatusMessage] = useState("");
  const [evaluating, setEvaluating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [workspaceLoading, setWorkspaceLoading] = useState(true);
  const inputRevision = useRef(0);
  const requestSequence = useRef(0);
  const decisionResult = useRef<HTMLDivElement>(null);
  const busy = evaluating || saving || exporting;

  // Dynasty League Import V1 (Worker 4): real ownership context for the
  // trade builder, sourced from the already-annotated `assetOptions` list
  // (bootstrap-time truth -- present only once a league is connected,
  // identical to Asset Explorer/Rankings' own convention). Purely a
  // display/warning layer: none of this is read by `evaluate()` above or
  // by the trade-value computation on the backend.
  const assetLookup = useMemo(
    () => new Map(data.assetOptions.map((asset) => [asset.assetId, asset])),
    [data.assetOptions],
  );
  const nameForAsset = (assetId: string) => assetLookup.get(assetId)?.name ?? assetId;
  const liveOwnership = useMemo(
    () =>
      new Map(
        data.assetOptions
          .filter((asset): asset is AssetOption & { ownership: AssetOwnership } =>
            Boolean(asset.ownership),
          )
          .map((asset) => [asset.assetId, asset.ownership]),
      ),
    [data.assetOptions],
  );
  const rosterAssetIds = useMemo(() => rosterOwnedAssetIds(data.assetOptions), [data.assetOptions]);
  const rosterWarnings = useMemo(
    () => resolveTradeRosterWarnings(give, receive, liveOwnership, nameForAsset),
    [give, receive, liveOwnership],
  );
  const fillFromRoster = () => {
    if (busy) return;
    const next = fillTradeSideFromRoster(give, receive, rosterAssetIds);
    if (next.length === give.length) return;
    invalidateDecision();
    setGive(next);
  };

  useEffect(() => {
    if (!decision) return;
    window.requestAnimationFrame(() => {
      decisionResult.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      decisionResult.current?.focus({ preventScroll: true });
    });
  }, [decision]);

  const invalidateDecision = () => {
    inputRevision.current += 1;
    requestSequence.current += 1;
    setDecision(null);
    setEvaluatedPackage(null);
    setError(null);
    setStatusMessage("");
    setEvaluating(false);
  };
  const toggleSide = (side: "give" | "receive", assetId: string) => {
    if (busy) return;
    const current = side === "give" ? give : receive;
    const other = side === "give" ? receive : give;
    const next = nextTradeSide(current, other, assetId);
    if (next.length === current.length && next.every((value, index) => value === current[index])) {
      return;
    }
    invalidateDecision();
    if (side === "give") setGive(next);
    else setReceive(next);
  };
  const changeTeamWindow = (value: string) => {
    if (busy || value === teamWindow) return;
    invalidateDecision();
    setTeamWindow(value as TeamWindow);
  };
  const evaluate = async () => {
    if (!give.length || !receive.length || evaluating) return;
    const requestId = ++requestSequence.current;
    const revision = inputRevision.current;
    const requestedGive = [...give];
    const requestedReceive = [...receive];
    const requestedWindow = teamWindow;
    setEvaluating(true);
    setError(null);
    try {
      const result = await client.evaluateTrade(
        requestedGive,
        requestedReceive,
        requestedWindow,
      );
      if (
        isCurrentDecisionRequest(
          requestId,
          revision,
          requestSequence.current,
          inputRevision.current,
        )
      ) {
        // Re-assert the exact request snapshot before exposing its decision. This also
        // protects save/export if an accessibility click is delivered twice at the
        // evaluation boundary.
        setGive(requestedGive);
        setReceive(requestedReceive);
        setEvaluatedPackage({ give: requestedGive, receive: requestedReceive });
        setDecision(result);
        setStatusMessage(
          `Evaluated the exact ${requestedGive.length}-for-${requestedReceive.length} selected package.`,
        );
      }
    } catch (reason) {
      if (
        isCurrentDecisionRequest(
          requestId,
          revision,
          requestSequence.current,
          inputRevision.current,
        )
      ) {
        setError(
          reason instanceof NwrApiError
            ? reason
            : new NwrApiError("Trade decision could not be evaluated."),
        );
      }
    } finally {
      if (
        isCurrentDecisionRequest(
          requestId,
          revision,
          requestSequence.current,
          inputRevision.current,
        )
      ) {
        setEvaluating(false);
      }
    }
  };

  useEffect(() => {
    let active = true;
    void client
      .listSavedTrades()
      .then((result) => {
        if (!active) return;
        setWorkspace(result);
        setSavedSelection((current) => current || result.scenarios[0]?.scenarioId || "");
      })
      .catch((reason) => {
        if (!active) return;
        setError(
          reason instanceof NwrApiError
            ? reason
            : new NwrApiError("Saved trades could not be loaded."),
        );
      })
      .finally(() => {
        if (active) setWorkspaceLoading(false);
      });
    return () => {
      active = false;
    };
  }, [client]);

  const save = async () => {
    if (busy || !give.length || !receive.length || !title.trim()) return;
    if (
      decision &&
      (!evaluatedPackage ||
        !isSameTradePackage(
          give,
          receive,
          evaluatedPackage.give,
          evaluatedPackage.receive,
        ))
    ) {
      setError(
        new NwrApiError("The selected package no longer matches the evaluated package.", {
          code: "TRADE_PACKAGE_CHANGED",
          recoveryAction: "Evaluate the exact selected package again before saving it.",
        }),
      );
      return;
    }
    setSaving(true);
    setError(null);
    setStatusMessage("");
    try {
      const result = await client.saveTradeScenario({
        scenarioId,
        title,
        give,
        receive,
        teamWindow,
        notes,
      });
      setWorkspace(result.workspace);
      setScenarioId(result.scenarioId);
      setSavedSelection(result.scenarioId);
      setStatusMessage("Trade saved atomically to the Personal Workspace.");
    } catch (reason) {
      setError(
        reason instanceof NwrApiError
          ? reason
          : new NwrApiError("The trade could not be saved locally."),
      );
    } finally {
      setSaving(false);
    }
  };

  const reopen = () => {
    if (busy) return;
    const scenario = workspace?.scenarios.find(
      (candidate) => candidate.scenarioId === savedSelection,
    );
    if (!scenario) return;
    const exactAssets = [...scenario.give, ...scenario.receive];
    if (new Set(exactAssets).size !== exactAssets.length) {
      setError(
        new NwrApiError("This saved trade contains a duplicate asset and cannot be reopened.", {
          code: "INVALID_SAVED_TRADE",
          recoveryAction: "Use a different saved trade or recover the Personal Workspace.",
        }),
      );
      return;
    }
    invalidateDecision();
    setGive([...scenario.give]);
    setReceive([...scenario.receive]);
    setTeamWindow(scenario.teamWindow);
    setTitle(scenario.title);
    setNotes(scenario.notes);
    setScenarioId(scenario.scenarioId);
    setStatusMessage(
      scenario.sourceStatus === "CURRENT"
        ? "Saved trade reopened. Evaluate it to refresh the decision."
        : "Saved trade reopened from older source versions. Evaluate it against current sources.",
    );
  };

  const startNew = () => {
    if (busy) return;
    invalidateDecision();
    setGive([]);
    setReceive([]);
    setTeamWindow("Balanced");
    setTitle("Trade scenario");
    setNotes("");
    setScenarioId(null);
    setStatusMessage("New unsaved trade started.");
  };

  const exportBrief = async () => {
    if (busy || !decision) return;
    if (
      !evaluatedPackage ||
      !isSameTradePackage(
        give,
        receive,
        evaluatedPackage.give,
        evaluatedPackage.receive,
      )
    ) {
      setError(
        new NwrApiError("The selected package no longer matches the evaluated package.", {
          code: "TRADE_PACKAGE_CHANGED",
          recoveryAction: "Evaluate the exact selected package again before exporting it.",
        }),
      );
      return;
    }
    setExporting(true);
    setError(null);
    setStatusMessage("");
    try {
      const result = await client.exportTradeBrief({
        title,
        give,
        receive,
        teamWindow,
        notes,
      });
      const blob = new Blob([result.markdown], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.fileName;
      document.body.append(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 0);
      setStatusMessage(
        result.missingData.length
          ? `Brief exported with ${result.missingData.length} documented missing-data item(s).`
          : "Markdown trade brief exported.",
      );
    } catch (reason) {
      setError(
        reason instanceof NwrApiError
          ? reason
          : new NwrApiError("The Markdown trade brief could not be exported."),
      );
    } finally {
      setExporting(false);
    }
  };

  const scenarios = workspace?.scenarios ?? [];
  const workspaceBlocked = workspace?.storeStatus === "blocked";
  return (
    <>
      <PageHeader
        eyebrow="Decision lab · Advisory only"
        title="Trade Decision Lab"
        description="Pressure-test the football decision across ten named dimensions. NWR never invents a hidden package score."
        status={
          <>
            <StatusBadge tone="safe" label="Exact governed assets" />
            <StatusBadge tone="review" label="No transaction execution" />
          </>
        }
        actions={
          <Button
            disabled={!give.length || !receive.length || busy}
            icon="trade"
            onClick={() => void evaluate()}
          >
            {evaluating ? "Evaluating…" : "Evaluate trade"}
          </Button>
        }
      />
      <div className="trade-window">
        <span>Team direction</span>
        <div
          aria-disabled={busy || undefined}
          style={busy ? { opacity: 0.65, pointerEvents: "none" } : undefined}
        >
          <SegmentedControl
            label=""
            options={["Contending", "Balanced", "Rebuilding"]}
            value={teamWindow}
            onChange={changeTeamWindow}
          />
        </div>
        <p>The team window changes fit—not source ranks, scores, or evidence.</p>
      </div>
      {rosterWarnings.length ? (
        <div className="trade-roster-warnings">
          {rosterWarnings.map((warning) => (
            <div className="alert-strip" key={`${warning.assetId}-${warning.kind}`}>
              {warning.message}
            </div>
          ))}
        </div>
      ) : null}
      <div className="trade-builder">
        <Panel
          action={
            data.dynastyLeague && rosterAssetIds.length ? (
              <Button
                disabled={busy}
                icon="layers"
                onClick={fillFromRoster}
                variant="ghost"
              >
                Fill from your roster
              </Button>
            ) : undefined
          }
          title="You give"
          eyebrow="Current roster side"
        >
          <AssetPicker
            assets={data.assetOptions}
            disabled={busy}
            selected={give}
            unavailable={new Set(receive)}
            onToggle={(id) => toggleSide("give", id)}
            limit={TRADE_SIDE_LIMIT}
            label="Outgoing assets"
          />
          <SelectedChips
            assets={data.assetOptions}
            disabled={busy}
            selected={give}
            onRemove={(id) => toggleSide("give", id)}
          />
        </Panel>
        <div className="trade-builder__versus">
          <span>
            <Icon name="trade" />
          </span>
          <strong>FOR</strong>
        </div>
        <Panel title="You receive" eyebrow="Incoming side">
          <AssetPicker
            assets={data.assetOptions}
            disabled={busy}
            selected={receive}
            unavailable={new Set(give)}
            onToggle={(id) => toggleSide("receive", id)}
            limit={TRADE_SIDE_LIMIT}
            label="Incoming assets"
          />
          <SelectedChips
            assets={data.assetOptions}
            disabled={busy}
            selected={receive}
            onRemove={(id) => toggleSide("receive", id)}
          />
        </Panel>
      </div>
      <Panel title="Saved trade workspace" eyebrow="Personal Workspace · Atomic local save">
        <div className="form-grid">
          <label className="form-field">
            <span>Scenario title</span>
            <input
              disabled={busy}
              maxLength={160}
              onChange={(event) => {
                setTitle(event.target.value);
                setError(null);
                setStatusMessage("");
              }}
              value={title}
            />
          </label>
          <label className="form-field">
            <span>Saved trade</span>
            <select
              disabled={busy || workspaceLoading || !scenarios.length}
              onChange={(event) => setSavedSelection(event.target.value)}
              value={savedSelection}
            >
              {!scenarios.length ? <option value="">No saved trades</option> : null}
              {scenarios.map((scenario) => (
                <option key={scenario.scenarioId} value={scenario.scenarioId}>
                  {scenario.title}
                  {scenario.sourceStatus === "CURRENT" ? "" : " · older sources"}
                </option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>Scenario notes</span>
            <textarea
              disabled={busy}
              maxLength={20_000}
              onChange={(event) => {
                setNotes(event.target.value);
                setError(null);
                setStatusMessage("");
              }}
              value={notes}
            />
          </label>
        </div>
        <div className="toolbar">
          <Button
            disabled={
              busy || workspaceBlocked || !give.length || !receive.length || !title.trim()
            }
            icon="check"
            onClick={() => void save()}
          >
            {saving ? "Saving…" : scenarioId ? "Update saved trade" : "Save current trade"}
          </Button>
          <Button
            disabled={busy || !savedSelection}
            icon="layers"
            onClick={reopen}
            variant="secondary"
          >
            Reopen selected
          </Button>
          <Button disabled={busy} icon="undo" onClick={startNew} variant="ghost">
            New trade
          </Button>
          <Button
            disabled={busy || !decision}
            icon="board"
            onClick={() => void exportBrief()}
            variant="secondary"
          >
            {exporting ? "Exporting…" : "Export Markdown"}
          </Button>
        </div>
        <p className="copy-muted">
          {statusMessage ||
            (workspaceLoading ? "Loading saved trades…" : workspace?.message || "Local only.")}
        </p>
      </Panel>
      {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
      {decision ? (
        <div aria-live="polite" ref={decisionResult} tabIndex={-1}>
          <TradeResult
            decision={decision}
            give={evaluatedPackage?.give ?? give}
            receive={evaluatedPackage?.receive ?? receive}
            nameForAsset={nameForAsset}
          />
        </div>
      ) : null}
    </>
  );
}

function TradeResult({
  decision,
  give,
  receive,
  nameForAsset,
}: {
  decision: TradeDecision;
  give: string[];
  receive: string[];
  nameForAsset: (assetId: string) => string;
}) {
  const tone = decision.recommendation.includes("ACCEPT")
    ? "accept"
    : decision.recommendation.includes("REJECT")
      ? "reject"
      : "counter";
  // Dynasty League Import V1 (Worker 4): the real ownership record AS OF
  // this specific evaluation (`decision.ownership`, attached strictly
  // after `evaluate_trade_decision` already computed everything else --
  // see `desktop_facade.evaluate_dynasty_trade`). Kept separate from the
  // live picker-time warnings above so a saved/exported trade brief always
  // carries the ownership snapshot that was true at the moment it was
  // evaluated.
  const evaluationOwnership = useMemo(
    () => ownershipLookup(decision.ownership),
    [decision.ownership],
  );
  return (
    <div className="trade-result">
      <section className={`trade-verdict trade-verdict--${tone}`}>
        <div>
          <span>{decision.authority}</span>
          <strong>{decision.recommendation.replaceAll("_", " ")}</strong>
          <p>{decision.summary}</p>
        </div>
        <div>
          <span>Confidence</span>
          <b>{decision.confidence}</b>
          <small>{decision.preferredSide}</small>
        </div>
      </section>
      {decision.dynastyLeague ? (
        <Panel title="Roster context at evaluation" eyebrow={`Connected to ${decision.dynastyLeague.leagueName} · display only`}>
          <div className="trade-roster-context">
            <div>
              <strong>You give</strong>
              <ul className="compact-list">
                {give.map((assetId) => (
                  <li key={assetId}>
                    {nameForAsset(assetId)} <OwnershipTag ownership={evaluationOwnership.get(assetId)} />
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <strong>You receive</strong>
              <ul className="compact-list">
                {receive.map((assetId) => (
                  <li key={assetId}>
                    {nameForAsset(assetId)} <OwnershipTag ownership={evaluationOwnership.get(assetId)} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <p className="copy-muted">
            This ownership record never changed the recommendation, confidence, or any dimension
            above -- it is the real roster state at the moment this trade was evaluated.
          </p>
        </Panel>
      ) : null}
      <div className="split-view">
        <Panel title="Why" eyebrow="Strongest independent dimensions">
          <ol className="reason-list">
            {decision.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ol>
        </Panel>
        <Panel title="Main uncertainty" eyebrow="What could change the call">
          <div className="risk-callout">{decision.mainUncertainty}</div>
          <ul className="compact-list">
            {decision.whatWouldChange.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Panel>
      </div>
      <div className="alert-strip">{decision.counterMessage}</div>
      <Panel title="Synthesis" eyebrow="Visible ordinal decision rule">
        <ul className="compact-list">
          {decision.synthesisTrace.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Panel>
      <Panel title="Decision trace" eyebrow="No package total · ten ordinal dimensions">
        <div className="dimension-grid">
          {decision.dimensions.map((dimension) => (
            <article key={dimension.code}>
              <header>
                <span>{dimension.code}</span>
                <strong>{dimension.label}</strong>
                <em>{dimension.outcome.replaceAll("_", " ")}</em>
              </header>
              <p>{dimension.explanation}</p>
              <small>{dimension.confidence} confidence</small>
            </article>
          ))}
        </div>
      </Panel>
    </div>
  );
}
