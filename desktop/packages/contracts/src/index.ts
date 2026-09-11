export const CONTRACT_VERSION = "1.0.0" as const;

export type DesktopMode = "dynasty" | "redraft";
export type HealthTone = "ready" | "review" | "blocked" | "offline";
export type JsonScalar = string | number | boolean | null;
export type JsonValue = JsonScalar | JsonValue[] | { [key: string]: JsonValue };

export interface RuntimeDescriptor {
  mode: DesktopMode;
  apiBaseUrl: string;
  token: string;
  contractVersion: typeof CONTRACT_VERSION | string;
}

export interface ApiEnvelope<T> {
  contractVersion: typeof CONTRACT_VERSION | string;
  mode: DesktopMode;
  data: T;
  warnings: string[];
  errors: ApiErrorBody[];
}

export interface ApiErrorBody {
  contractVersion?: string;
  code: string;
  message: string;
  recoveryAction?: string;
  fieldErrors?: Record<string, string[]>;
}

export interface SourceStatus {
  ready: boolean;
  tone: HealthTone;
  authority: string;
  sourceAsOf: string;
  freshness: string;
  summary: string;
  scheduledRefresh: string;
  errors: string[];
  warnings: string[];
  sourceHashes?: Record<string, string>;
}

export interface WorkspaceSummary {
  watchlist: number;
  targets: number;
  avoid: number;
  openDecisions: number;
  savedScenarios: number;
}

export type PlanningModuleId = "roster" | "picks" | "keeper" | "drop" | "trade" | "draft";

export interface PlanningModuleState {
  moduleId: PlanningModuleId;
  checks: boolean[];
  notes: string;
  saved: boolean;
  updatedAtUtc: string;
}

export interface PlanningWorkspace {
  storeStatus: "loaded" | "empty" | "blocked";
  updatedAtUtc: string;
  message: string;
  modules: PlanningModuleState[];
}

export interface PlanningModuleInput {
  checks: boolean[];
  notes: string;
}

export type WorkspaceTeamWindow =
  | "Contending"
  | "Balanced"
  | "Rebuilding"
  | "Custom/Unspecified";

export interface PersonalBoardEntry {
  assetId: string;
  name: string;
  assetType: string;
  watchlist: boolean;
  target: boolean;
  avoid: boolean;
  tags: string[];
  notes: string;
  teamWindow: WorkspaceTeamWindow;
  createdAtUtc: string;
  updatedAtUtc: string;
}

export interface PersonalBoardInput {
  assetId: string;
  watchlist: boolean;
  target: boolean;
  avoid: boolean;
  tags: string[];
  notes: string;
  teamWindow: WorkspaceTeamWindow;
}

export type OwnerDecisionType =
  | "player evaluation"
  | "draft target"
  | "roster cut"
  | "waiver target"
  | "custom note";

export interface OwnerDecisionRecord {
  decisionId: string;
  title: string;
  decisionType: OwnerDecisionType;
  status: string;
  assetIds: string[];
  assetNames: string[];
  rationale: string;
  createdAtUtc: string;
  updatedAtUtc: string;
}

export interface OwnerDecisionInput {
  title: string;
  decisionType: OwnerDecisionType;
  assetIds: string[];
  rationale: string;
}

export interface WorkspaceBackupStatus {
  status: "none" | "ready" | "blocked";
  backupId: string;
  fileCount: number;
  message: string;
}

export interface DynastyWorkspace {
  storeStatus: "loaded" | "empty" | "blocked";
  message: string;
  updatedAtUtc: string;
  personalBoard: PersonalBoardEntry[];
  decisions: OwnerDecisionRecord[];
  backup: WorkspaceBackupStatus;
}

export interface DynastySummary {
  rankedPlayers: number;
  marketMatched: number;
  rookieRows: number;
  blockedRookies: number;
  manualReviewRookies: number;
  outcomeRows: number;
  workspace: WorkspaceSummary;
}

export interface DynastyRanking {
  rank: number | null;
  player: string;
  position: string;
  team: string;
  age: number | null;
  positionRank: string;
  tier: string;
  nwrScore: number | null;
  nwrView: string;
  range: string;
  marketBand: string;
  marketRank: number | null;
  marketGap: number | null;
  marketValue: number | null;
  marketDate: string;
  confidence: string;
  risk: string;
  assetId: string;
}

export interface AssetOption {
  assetId: string;
  name: string;
  assetType: string;
  position: string;
  team: string;
  rank: number | null;
  authority: string;
  /** Compatibility-only selection block. Model evidence blocking is separate. */
  blocked: boolean;
  selectable: boolean;
  searchable: boolean;
  draftEligible: boolean;
  modelScoreEligible: boolean;
  evidenceBlocked: boolean;
  scoreStatus: string;
  identityStatus: string;
  playerId: string;
  draftRound: number | null;
  overallPick: number | null;
  refreshAvailable: boolean;
}

export interface RookieRanking {
  rank: number | null;
  assetId: string;
  playerId: string;
  player: string;
  position: string;
  team: string;
  evidenceBand: string;
  draftRange: string;
  nflDraftCapital: string;
  boardScore: number | null;
  reviewScore: number | null;
  authority: string;
  blockedReason: string;
  warnings: string;
  confidence: string;
  age: number | null;
  collegeProduction: string;
  marketShare: string;
  athleticContext: string;
  researchTier: string;
  researchNeighborhood: string;
  currentRole: string;
  whatNwrLikes: string;
  whatHoldsBack: string;
  biggestUncertainty: string;
  rankScoreExplanation: string;
  floor: string;
  expected: string;
  ceiling: string;
  identityStatus: string;
  draftEligibility: string;
  scoreStatus: string;
  modelScoreEligible: boolean;
  searchable: boolean;
  selectable: boolean;
  draftable: boolean;
  refreshAvailable: boolean;
  draftRound: number | null;
  overallPick: number | null;
  eligibilityReason: string;
}

export interface RookieIntelligence {
  nwrRookieScore: number | null;
  reviewScore: number | null;
  rawModelScore: number | null;
  collegeProduction: string;
  marketShare: string;
  athleticContext: string;
  currentRole: string;
  whatNwrLikes: string[];
  whatHoldsBack: string[];
  biggestUncertainty: string;
  rankScoreExplanation: string;
}

export interface RookieDraftReadiness {
  verdict: string;
  ready: boolean;
  officialDrafted: number;
  positionCounts: Record<string, number>;
  exactIdentity: number;
  scored: number;
  manualReview: number;
  unresolved: number;
  missingFromRegistry: number;
  missingFromDraftablePool: number;
  duplicateAssetIds: number;
  refreshAvailable: number;
  reviewAssetIds: string[];
  missingAssetIds: string[];
  surfaceGapAssetIds: string[];
  nonselectableAssetIds: string[];
  draftableAssetIds: string[];
  missingBySurface: Record<string, string[]>;
  duplicateBySurface: Record<string, string[]>;
  validatedSurfaces: string[];
  alertCode: string;
  alertTitle: string;
  alertMessage: string;
}

export interface MarketFreshness {
  sourceAsOf: string;
  status: string;
  message: string;
}

export interface Notice {
  tone: Exclude<HealthTone, "offline">;
  title: string;
  message: string;
}

export interface DynastyBootstrap {
  product: {
    title: string;
    contextLabel: string;
    leagueLabel: string;
    authority: string;
  };
  status: SourceStatus;
  summary: DynastySummary;
  rankings: DynastyRanking[];
  rookies: RookieRanking[];
  assetOptions: AssetOption[];
  rookieReadiness: RookieDraftReadiness;
  marketFreshness: MarketFreshness;
  planning: PlanningWorkspace;
  notices: Notice[];
}

export interface PlayerDetail {
  assetId: string;
  name: string;
  assetType: string;
  position: string;
  team: string;
  rank: number | null;
  positionRank: string;
  nwrScore: number | null;
  age: number | null;
  confidence: string;
  authority: string;
  range: {
    floor: string;
    expected: string;
    ceiling: string;
    method: string;
    authority: string;
  };
  market: {
    band: string;
    gap: number | null;
    rank: number | null;
    value: number | null;
    sourceAsOf: string;
    status: string;
  };
  risk: string;
  reasons: string[];
  outcomes: Array<Record<string, JsonValue>>;
  research: Record<string, JsonValue>;
  caveats: string[];
  playerId: string;
  identityStatus: string;
  officialDraftAssetId: string;
  nflDraftCapital: string;
  draftRound: number | null;
  overallPick: number | null;
  draftEligibility: string;
  modelScoreEligible: boolean;
  scoreStatus: string;
  selectable: boolean;
  refreshAvailable: boolean;
  rookieIntelligence: RookieIntelligence | null;
  immediateProduction?: ImmediateProduction;
}

export interface ImmediateProduction {
  assetId: string;
  player: string;
  available: boolean;
  projectedPoints: number | null;
  overallRank: number | null;
  positionRank: number | null;
  replacementPoints: number | null;
  replacementAdjustedValue: number | null;
  confidence: string;
  rookie: boolean | null;
  authority: string;
  sourceAsOf: string;
  uncertainty: string;
}

export interface BridgeDecision {
  key: string;
  label: string;
  preferred: string;
  badge: "PRODUCTION" | "REVIEW" | "RESEARCH ONLY" | "INSUFFICIENT EVIDENCE";
  authority: string;
  reason: string;
  evidence: string[];
}

export interface RookieVeteranBridge {
  mode: "ROOKIE_VETERAN";
  players: string[];
  decisions: BridgeDecision[];
  immediateProduction: ImmediateProduction[];
  why: string[];
  warnings: string[];
}

export interface CompareLean {
  horizon: string;
  preferred: string;
  reason: string;
  authority: string;
}

export interface ComparePlayer {
  assetId: string;
  player: string;
  dimensions: Record<string, JsonScalar>;
  advantages: string[];
  risks: string[];
}

export interface CompareRange {
  assetId: string;
  player: string;
  floor: string;
  expected: string;
  ceiling: string;
  ageWindow: string;
  risk: string;
  authority: string;
  method: string;
}

export interface DynastyComparison {
  leans: CompareLean[];
  ranges: CompareRange[];
  players: ComparePlayer[];
  warnings: string[];
  bridge?: RookieVeteranBridge | null;
}

export type TeamWindow = "Contending" | "Balanced" | "Rebuilding";

export interface TradeDimension {
  code: string;
  label: string;
  outcome: string;
  confidence: string;
  evidence: string[];
  explanation: string;
}

export interface TradeDecision {
  authority: string;
  recommendation: string;
  preferredSide: string;
  confidence: string;
  teamWindow: TeamWindow;
  summary: string;
  reasons: string[];
  mainUncertainty: string;
  whatWouldChange: string[];
  synthesisTrace: string[];
  dimensions: TradeDimension[];
  counterStatus: "available" | "blocked";
  counterMessage: string;
}

export interface SavedTradeScenario {
  scenarioId: string;
  title: string;
  give: string[];
  receive: string[];
  teamWindow: TeamWindow;
  notes: string;
  createdAtUtc: string;
  updatedAtUtc: string;
  sourceStatus: "CURRENT" | "STALE_SOURCE_VERSION";
}

export interface TradeWorkspace {
  storeStatus: "loaded" | "empty" | "blocked";
  updatedAtUtc: string;
  message: string;
  scenarios: SavedTradeScenario[];
}

export interface TradeScenarioInput {
  scenarioId: string | null;
  title: string;
  give: string[];
  receive: string[];
  teamWindow: TeamWindow;
  notes: string;
}

export interface TradeSaveResult {
  scenarioId: string;
  workspace: TradeWorkspace;
}

export interface TradeBriefInput {
  title: string;
  give: string[];
  receive: string[];
  teamWindow: TeamWindow;
  notes: string;
}

export interface TradeBriefExport {
  fileName: string;
  markdown: string;
  missingData: string[];
}

export interface RosterSettings {
  qb: number;
  rb: number;
  wr: number;
  te: number;
  flex: number;
  superflex: number;
  k: number;
  dst: number;
  benchSize: number;
}

export interface ScoringSettings {
  passingYards: number;
  passingTd: number;
  interception: number;
  rushingYards: number;
  rushingTd: number;
  receivingYards: number;
  reception: number;
  receivingTd: number;
  passingFirstDown: number;
  rushingFirstDown: number;
  receivingFirstDown: number;
  returnYards: number;
  returnTd: number;
  fumbleLost: number;
  tePremium: number;
  bonuses: Record<string, number>;
}

export interface DraftContext {
  draftType: "snake" | "auction";
  draftSlot: number | null;
  rounds: number;
  keeperCount: number;
  auctionBudget: number | null;
  // A LIST of {position, maximum} pairs -- never an object keyed by the
  // literal position code ("QB", "WR", ...). NWR Overnight V3 retry-queue
  // follow-up: a real, live-reproduced bug -- the shared desktop API
  // camelCase key transform (`public_json_value`) mangles an all-uppercase
  // single-word dict key ("WR" -> "wR"), the exact same class of bug
  // already documented and worked around this way for UDK position rankings
  // (`redraft_draft_room_v1_service.load_udk_rankings`'s own docstring).
  // The `RedraftProfileUpdateInput.draft.rosterLimits` REQUEST shape below
  // is unaffected (plain JSON parse, no camelCase transform applied to
  // request bodies) and deliberately stays `Record<string, number>`.
  rosterLimits: { position: string; maximum: number }[];
  adpContextEnabled: boolean;
  replacementMethod: "starter_cutoff" | "expected_available";
}

export interface LeagueProfile {
  profileId: string;
  leagueName: string;
  season: number;
  teamCount: number;
  roster: RosterSettings;
  scoring: ScoringSettings;
  draft: DraftContext;
  presetKey: string | null;
  archived: boolean;
  createdAtUtc: string;
  updatedAtUtc: string;
  practicalMode: boolean;
  nwrPureExperimental: boolean;
  provider: "local" | "sleeper" | "espn" | "fantasypros";
  providerLeagueId: string | null;
}

export interface RedraftProfileUpdateInput {
  leagueName: string;
  teamCount: number;
  roster: Pick<
    RosterSettings,
    "qb" | "rb" | "wr" | "te" | "flex" | "superflex" | "k" | "dst" | "benchSize"
  >;
  scoring: Pick<ScoringSettings, "reception" | "passingTd" | "interception" | "tePremium">;
  draft: Pick<DraftContext, "rounds" | "draftSlot" | "replacementMethod"> & {
    /** League/platform position maxima. Empty means the rule is unknown,
     * never that the UI should invent a strategy cap. */
    rosterLimits?: Record<string, number>;
  };
  // NWR FINAL PRE-DRAFT GAP CLOSURE: optional and omittable -- omitting
  // preserves the profile's existing value (the real backend semantics,
  // unchanged). When set, enables/disables Practical Mode, which is what
  // ranking generation needs to stop expecting ranked K/DST rows (they
  // have none by design) and treat K/DST as manual-only. Previously the
  // ONLY caller that could ever set this was the Sleeper-import path --
  // a manually-configured league with real K/DST roster slots (e.g. an
  // ESPN league) had no owner-facing way to enable it at all.
  practicalMode?: boolean;
}

export interface RedraftRanking {
  overallRank: number;
  positionRank: number;
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  projectedPoints: number;
  replacementPoints: number;
  replacementAdjustedValue: number;
  starterGap: number;
  confidence: string;
  tier: number;
  positionTier: number;
  overallTierLabel: string;
  positionTierLabel: string;
  sourceAsOf: string;
  rookie: boolean;
  overallAdp: number | null;
  expectedPick: number | null;
  expectedRound?: number | null;
  nwrAdpGap?: number | null;
  valueLabel?: string;
  timingLabel?: string;
  makeItBack?: string;
  adpSource: string;
  drafted: boolean;
  draftedBy: string;
  pickNumber: number | null;
  /** Canonical backend result for the team currently on the clock. */
  rosterLegal: boolean;
  legalityCode: string;
  legalityReason: string;
}

export interface ReplacementLevel {
  position: string;
  starterCount: number;
  rosteredCount: number;
  starterCutoffPoints: number;
  replacementPoints: number;
}

export interface RedraftHealth {
  status: string;
  playerUniverseAvailable: boolean;
  currentSeasonForecastAvailable: boolean;
  scoringProfileValid: boolean;
  replacementCalculationValid: boolean;
  rankedPlayers: number;
  blockedPlayers: number;
  lastGeneratedTimestamp: string;
  messages: string[];
}

export interface DraftBoard {
  schemaVersion: number;
  profileId: string;
  drafted: string[];
  updatedAtUtc?: string;
  recoveredFromBackup?: boolean;
  configured?: boolean;
  ownerSlot?: number | null;
  seed?: number;
  speed?: "FAST" | "NORMAL" | "STEP";
  mode?: "MOCK" | "LIVE_READ_ONLY";
  picks?: DraftPick[];
  boardCells?: DraftBoardCell[];
  teams?: DraftTeam[];
  recentPicks?: DraftPick[];
  draftLog?: DraftPick[];
  myRoster?: DraftRosterPlayer[];
  currentPick?: number | null;
  currentTeamSlot?: number | null;
  nextOwnerPick?: number | null;
  isOwnerTurn?: boolean;
  complete?: boolean;
  availableCount?: number;
  canUndo?: boolean;
  adp?: AdpStatus;
  beatAdpPool?: BeatAdpRow[];
  decisionRows?: BeatAdpRow[];
  recommendations?: DraftRecommendation[];
  positionRun?: Array<{ position: string; count: number }>;
  fallbackDisclosure?: string;
  sleeperCompatibility?: {
    mode: string;
    pollingDefault: string;
    writes: string;
  };
}

export interface DraftPick {
  pickNumber: number;
  round: number;
  teamSlot: number;
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  actor: string;
  selectionBehavior: string;
  status?: "OPEN" | "RESOLVED" | "UNRESOLVED";
}

export interface DraftBoardCell extends DraftPick {
  ownerPick: boolean;
  current: boolean;
}

export interface DraftRosterPlayer {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  pickNumber: number;
}

export interface DraftTeam {
  teamSlot: number;
  name: string;
  owner: boolean;
  roster: DraftRosterPlayer[];
  picks: Array<Record<string, unknown>>;
}

export interface AdpStatus {
  available: boolean;
  provider?: string;
  source: string;
  // The ADP source's OWN team count -- may differ from the active room's
  // team count. A round.pick display is only computed against this, not
  // silently against the room's own team count.
  teamCount?: number;
  sourceDate: string;
  dateWindow?: string;
  importedAtUtc: string;
  retrievedAtUtc?: string;
  matchedPlayers: number;
  sourcePlayers?: number;
  sourceCoverage?: number;
  rankingPlayers: number;
  coverage: number;
  unmatched: string[];
  sourceSha256: string;
  authority: string;
  endpoint?: string;
  providerVersion?: string;
  positionFilter?: string;
  sampleSize?: number | null;
  freshness?: "FRESH" | "RECENT" | "STALE" | "UNAVAILABLE";
  lastRefreshError?: string;
  attributionUrl?: string;
  message: string;
}

export interface MarketProviderAdp {
  consensus: number | null;
  sleeper: number | null;
  espn: number | null;
  fantasypros: number | null;
}

export interface PasteAdpPreview {
  selectedSource: "CONSENSUS" | "SLEEPER" | "ESPN" | "FANTASYPROS";
  sourceRows: number;
  matchedRows: number;
  skippedRows: number;
  unmatched: string[];
  warnings: string[];
  rows: Array<Record<string, unknown>>;
  parserMode?: "MARKDOWN_TABLE" | "PLAIN_TEXT_BLOCK" | "RESPONSIVE_PLATFORM_CLIPBOARD";
  platformCoverage?: Record<string, { available: number; total: number }>;
}

export interface OwnerPlatformSnapshotStatus {
  available: boolean;
  active: boolean;
  parserMode: string;
  rowCount: number;
  matchedRows?: number;
  platformCoverage: Record<string, { available: number; total: number }>;
  sourceLabel: string;
  rawHash: string;
  importedAtUtc: string;
  leagueSelection: string;
  detectedPlatform: string;
  activeColumn?: string;
}

export interface BeatAdpRow {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  nwrRank: number;
  expectedPick: number | null;
  expectedRound?: number | null;
  overallAdp?: number | null;
  nwrEdge: number | null;
  nwrView: string;
  draftTiming: string;
  makeItBackProbability: number | null;
  makeItBackMethod: string;
  confidence: string;
  adpSource?: string;
  adpExplanation?: string;
  adpUnavailableReason?: string;
}

export interface DraftRecommendation {
  label: "Best Available" | "Best Fit" | "Value vs ADP" | "Upside" | "Safer";
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  nwrRank: number;
  nwrView: string;
  draftTiming: string;
  makeItBack: string;
  overallTierLabel: string;
  positionTierLabel: string;
  rosterFit: string;
  overallAdp?: number | null;
  adpSource?: string;
  adpExplanation?: string;
  adpUnavailableReason?: string;
  note: string;
}

export interface ManualDraftAsset {
  playerId: string;
  playerName: string;
  position: "K" | "DST";
  team: string;
  authority: "MANUAL — NOT MODELED BY NWR";
  overallAdp?: number | null;
  expectedPick?: number | null;
  expectedRound?: number | null;
  adpSource?: string;
  rosterLegal: boolean;
  legalityCode: string;
  legalityReason: string;
}

export interface ExternalConsensusStatus {
  authority: string;
  configured: boolean;
  manualFallback: string;
  message: string;
}

export interface KdstStreamerRow {
  playerName: string;
  position: "K" | "DST";
  team: string;
  ecr: number;
  tier: number | null;
  week: number;
  authority: string;
  rosterStatus: string;
  recommendation: "START" | "HOLD" | "ROSTERED_ELSEWHERE" | "ADD" | "ALTERNATIVE";
}

export interface KdstStreamerUnmatchedEntry {
  position: "K" | "DST";
  sleeperPlayerId: string;
}

export interface KdstStreamerResult {
  authority: string;
  week: number;
  leagueId: string;
  // Flat list, not a dict keyed by "K"/"DST" -- the desktop API's generic
  // camelCase JSON-key transform mangles literal data keys like "K"/"DST"
  // (e.g. "DST" -> "dST"). Each row carries its own `position` field.
  positions: KdstStreamerRow[];
  unmatchedSleeperPlayerIds: KdstStreamerUnmatchedEntry[];
  writeBehavior: string;
  // NWR pre-UI architecture pass (2026-09-10, directive section 3/C):
  // identification fields, additive. Flat list for the same reason as
  // `positions` above -- never a dict keyed by "K"/"DST".
  leagueSnapshotId?: string;
  traceIds?: Array<{ position: "K" | "DST"; traceId: string }>;
}

export interface RedraftFreeAgent {
  sleeperPlayerId: string;
  playerId: string;
  playerName: string;
  position: "QB" | "RB" | "WR" | "TE" | "K" | "DST";
  team: string;
  overallRank: number | null;
  positionRank: number | null;
  projectedPoints: number | null;
  replacementAdjustedValue: number | null;
  valueLabel: string;
  rankingAuthority: "NWR REDRAFT RANKING" | "UNRANKED";
  rosterStatus: "AVAILABLE";
}

export interface RedraftFreeAgentsResult {
  leagueId: string;
  freeAgents: RedraftFreeAgent[];
  rankingWarning: string;
  writeBehavior: string;
}

export interface RedraftOpponentPlayer {
  sleeperPlayerId: string;
  playerName: string;
  position: string;
  team: string;
  starter: boolean;
}

export interface RedraftOpponentRoster {
  rosterId: string;
  ownerUserId: string;
  teamName: string;
  players: RedraftOpponentPlayer[];
  unresolvedSleeperPlayerIds: string[];
}

export interface RedraftOpponentRostersResult {
  leagueId: string;
  opponents: RedraftOpponentRoster[];
  writeBehavior: string;
}

// ---------------------------------------------------------------------------
// In-season UI pass (2026-09-10): Start/Sit, Waivers/Add-Drop/FAAB, Redraft
// Trade Analysis, Trade Finder, and the canonical weekly-projection
// provider-health block every one of them now carries. These mirror the
// exact facade payload shapes in src/application/desktop_facade.py
// (redraft_weekly_projections / redraft_weekly_lineup / redraft_waivers /
// redraft_trade_analysis / redraft_trade_finder / redraft_weekly_home_
// actions) field-for-field -- no client-side renaming.
// ---------------------------------------------------------------------------

export interface WeeklyProjectionProviderHealth {
  schemaVersion: number;
  provider: string;
  sourceEndpoint: string;
  integrationStatus: string;
  season: number;
  week: number;
  seasonType: string;
  leagueId: string;
  retrievedAt: string;
  schemaFingerprint: string;
  payloadHash: string;
  totalRows: number;
  nonzeroProjectionRows: number;
  status: "OK" | "DEGRADED" | "UNAVAILABLE";
  freshness: "LIVE" | "STALE";
  servedFromCache: boolean;
  issues: string[];
}

export interface WeeklyProjectionRow {
  canonicalPlayerId: string;
  sleeperPlayerId: string;
  playerName: string;
  position: string;
  team: string;
  projectedPoints: number | null;
  scoringContext: "NWR_LEAGUE_SCORING" | "SLEEPER_PROVIDER_SCORING";
  identityMatch: "MATCHED" | "UNMATCHED" | "AMBIGUOUS";
  gp: number | null;
  sourceAsOf: string;
}

export interface WeeklyProjectionsResult {
  season: number;
  week: number;
  leagueId: string;
  source: string;
  sourceStatus: "OK" | "UNAVAILABLE";
  sourceAsOf: string;
  matched: number;
  unmatched: number;
  ambiguous: number;
  totalPlayersInSource: number;
  providerHealth: WeeklyProjectionProviderHealth;
  rows: WeeklyProjectionRow[];
  writeBehavior: string;
}

export interface WeeklyLineupSlotPlayer {
  sleeperPlayerId: string;
  playerName: string;
  position: string;
  team: string;
  projectedPoints: number | null;
}

export interface WeeklyLineupSlot {
  slotType: string;
  player: WeeklyLineupSlotPlayer | null;
  status: string;
  closeCall: boolean;
  closeCallAlternative: string | null;
  closeCallMargin: number | null;
}

export interface WeeklyLineupBenchPlayer {
  sleeperPlayerId: string;
  playerName: string;
  position: string;
  projectedPoints: number | null;
}

export interface WeeklyLineupSwap {
  slotType: string;
  startPlayer: string;
  benchPlayer: string;
  projectedDelta: number;
  summary: string;
}

// NWR pre-UI architecture pass (2026-09-10, directive section 4): the
// owner-facing DecisionResultEnvelope contract. Additive on top of each
// tool's own real response shape -- never a replacement for it. Migrated
// this pass: Start/Sit (WeeklyLineupResult), Waivers (WaiversResult).
// Trade Analysis/Trade Finder/K-DST Streamer carry `traceId`/
// `leagueSnapshotId` this same pass but not yet this full envelope; Draft
// is untouched. See DECISION_CONTRACTS.md.
export type DecisionConfidenceState = "HIGH" | "NOMINAL" | "LOW" | "UNAVAILABLE";

export interface DecisionResultEnvelope {
  task: string;
  profileId: string;
  leagueSnapshotId: string | null;
  generatedAtUtc: string;
  primaryRecommendation: Record<string, unknown> | null;
  alternatives: Array<Record<string, unknown>>;
  rationale: string;
  confidenceState: DecisionConfidenceState;
  confidenceBasis: string;
  dataHealth: Record<string, unknown> | null;
  traceId: string | null;
  issues: string[];
}

export interface WeeklyLineupResult {
  season: number;
  week: number;
  leagueId: string;
  sourceStatus: "OK" | "UNAVAILABLE";
  sourceAsOf: string;
  matched: number;
  unmatched: number;
  ambiguous: number;
  providerHealth: WeeklyProjectionProviderHealth;
  traceId?: string | null;
  leagueSnapshotId?: string;
  decisionEnvelope?: DecisionResultEnvelope;
  projectedTotal: number;
  unprojectedStarterCount: number;
  starters: WeeklyLineupSlot[];
  bench: WeeklyLineupBenchPlayer[];
  excluded: Array<{ sleeperPlayerId: string; playerName: string; position: string }>;
  swaps: WeeklyLineupSwap[];
  writeBehavior: string;
}

export interface WaiverAddCandidate {
  sleeperPlayerId: string;
  canonicalPlayerId: string;
  playerName: string;
  position: string;
  team: string;
  rosReplacementValue: number | null;
  rosOverallRank: number | null;
  weeklyProjectedPoints: number | null;
  marginalUtility: number | null;
  becomesStarter: boolean;
  marginalUtilityExplanation: string;
  identityStatus: string;
  faabBidLowDollars: number | null;
  faabBidHighDollars: number | null;
  faabUrgency: "HIGH" | "MEDIUM" | "LOW" | null;
  faabRationale: string | null;
}

export interface WaiverDropCandidate {
  canonicalPlayerId: string;
  playerName: string;
  position: string;
  marginalUtility: number | null;
  explanation: string;
}

export interface WaiverAddDropPairing {
  add: WaiverAddCandidate;
  drop: WaiverDropCandidate | null;
  netMarginalUtility: number | null;
}

export interface WaiversResult {
  leagueId: string;
  mode: "THIS_WEEK" | "REST_OF_SEASON";
  week: number | null;
  weeklySourceStatus: string | null;
  weeklyProviderHealth: WeeklyProjectionProviderHealth | null;
  rankingWarning: string;
  traceId?: string | null;
  leagueSnapshotId?: string;
  decisionEnvelope?: DecisionResultEnvelope;
  unmatchedRosterSleeperPlayerIds: string[];
  addCandidates: WaiverAddCandidate[];
  dropCandidates: WaiverDropCandidate[];
  addDropPairings: WaiverAddDropPairing[];
  writeBehavior: string;
}

export interface TradePlayerImpact {
  playerId: string;
  playerName: string;
  position: string;
  rosReplacementValue: number | null;
  marginalUtility: number | null;
  becomesStarter: boolean;
  statusFlag: string | null;
}

export interface TradeAnalysisResult {
  leagueId: string;
  traceId?: string | null;
  leagueSnapshotId?: string;
  gives: TradePlayerImpact[];
  receives: TradePlayerImpact[];
  rosValueDelta: number;
  netMarginalUtility: number;
  startingLineupValueBefore: number;
  startingLineupValueAfter: number;
  startingLineupValueDelta: number;
  benchContingencyValueBefore: number;
  benchContingencyValueAfter: number;
  starterHolesBefore: string[];
  starterHolesAfter: string[];
  positionRedundancyBefore: Record<string, number>;
  positionRedundancyAfter: Record<string, number>;
  riskFlags: string[];
  championshipEquityNote: string | null;
  writeBehavior: string;
}

export interface TradeFinderCandidate {
  myGivePlayerId: string;
  myGivePlayerName: string;
  opponentGivePlayerId: string;
  opponentGivePlayerName: string;
  opponentRosterId: string;
  opponentTeamName: string;
  myNetMarginalUtility: number;
  opponentNetMarginalUtility: number;
  myRosValueDelta: number;
}

export interface TradeFinderResult {
  leagueId: string;
  traceId?: string | null;
  leagueSnapshotId?: string;
  candidates: TradeFinderCandidate[];
  writeBehavior: string;
}

export interface WeeklyHomeAction {
  category: "START_SIT" | "START_SIT_CLOSE_CALL" | "WAIVER" | "TRADE" | "STREAMER";
  priority: number;
  summary: string;
  detail: Record<string, unknown>;
}

export interface WeeklyHomeActionsResult {
  week: number;
  /**
   * NWR pre-UI architecture CLOSURE pass (directive section 3): the ONE
   * snapshot id `lineup` was computed from -- every child decision card on
   * a single Weekly Home render shares this exact value. `null` only when
   * the lineup sub-call itself failed (see `unavailableSections`), never a
   * fabricated placeholder.
   */
  leagueSnapshotId: string | null;
  actions: WeeklyHomeAction[];
  /** The SAME sub-call this endpoint already used to build `actions` above
   * -- render the "Projected lineup" panel from this, not a second,
   * separately-fetched `redraftWeeklyLineup` call. `null` when unavailable
   * (see `unavailableSections`). */
  lineup: WeeklyLineupResult | null;
  /** The SAME-request free-agent read -- render the "Top free agents"
   * panel from this, not a separate `redraftFreeAgents` call. `null` when
   * unavailable (see `unavailableSections`). */
  freeAgents: RedraftFreeAgentsResult | null;
  unavailableSections: Array<{ section: string; reason: string }>;
  writeBehavior: string;
}

export interface RedraftMyRosterPlayer {
  sleeperPlayerId: string;
  canonicalPlayerId: string | null;
  playerName: string;
  position: string;
  team: string;
  starter: boolean;
  identityStatus: "MATCHED" | "UNMATCHED_IDENTITY";
}

export interface RedraftMyRosterResult {
  leagueId: string;
  roster: RedraftMyRosterPlayer[];
  rankingWarning: string;
  writeBehavior: string;
}

export interface RedraftSleeperResyncResult {
  profile: LeagueProfile;
  rosterSnapshot: {
    syncedAtUtc: string;
    rosterId: string | number;
    playerCount: number;
    unresolvedSleeperPlayerIds: string[];
  };
  writeBehavior: "NO_SLEEPER_WRITES";
}

export interface SleeperAutoSyncConflict {
  pickNumber: number;
  reason: "OUT_OF_ORDER" | "UNKNOWN_SLEEPER_PLAYER" | "UNRESOLVED_LOCAL_IDENTITY";
  detail: string;
}

export interface SleeperAutoSyncApplied {
  pickNumber: number;
  playerId: string;
  playerName: string;
}

export interface SleeperAutoSyncSummary {
  applied: SleeperAutoSyncApplied[];
  conflicts: SleeperAutoSyncConflict[];
  nextExpectedPick: number;
  sleeperPickCount: number;
  boundedBatchHit: boolean;
}

export interface RedraftSleeperSyncResult {
  draftBoard: DraftBoard;
  sleeperSync: SleeperAutoSyncSummary;
}

export interface RedraftExternalIntelligenceEntry {
  playerId: string;
  espnAdp: string | null;
  nwrVsEspnGap: string | null;
  fantasyProsEcr: string | null;
  fantasyProsTier: string | null;
  fantasyProsProjectedPoints: string | null;
  nwrVsFantasyProsGap: string | null;
  udkPositionRank: string | null;
  udkTier: string | null;
  udkAdp: string | null;
  udkRisk: string | null;
  udkUpside: string | null;
  udkProjectedPoints: string | null;
  currentAlert: string | null;
  currentAlertSeverity: string | null;
  udkCurrentConflictFlag: string | null;
}

export interface RedraftExternalIntelligence {
  available: boolean;
  generatedNote: string;
  entries: RedraftExternalIntelligenceEntry[];
  hiddenByExperimentalMode?: boolean;
  // Snapshot-age context for the underlying local cheat-sheet file (see
  // src/services/redraft_external_intelligence_service.py) -- never
  // changes generatedNote/entries, only labels their age so the UI can
  // distinguish a genuinely quiet currentAlert from a stale snapshot.
  snapshotGeneratedAtUtc?: string | null;
  snapshotAgeHours?: number | null;
  stale?: boolean;
}

export interface RedraftExternalIntelligenceResponse {
  externalIntelligence: RedraftExternalIntelligence;
}

// Owner Test Candidate V1 -- real, backend-computed DecisionBundle
// (Player Score / Team Score Research / Simulated Championship Equity
// Research / Cost of Waiting V2 / Pick Score Experimental). The UI must
// render exactly these fields; it must never compute or fabricate one.
export interface DecisionBundleCandidate {
  playerId: string;
  playerName: string;
  position: string;
  playerScore: number | null;
  teamScoreAfter: number;
  teamScoreDelta: number;
  championshipEquityAfter: number;
  equityGain: number;
  costOfWaiting: number;
  makeItBackProbability: number | null;
  // Owner-test follow-up: the real trial count behind makeItBackProbability
  // -- a candidate showing 100% survival across a SMALL trial count is a
  // real, disclosed modeled estimate, never a guarantee. null exactly when
  // makeItBackProbability is null, or when the source is a non-Monte-Carlo
  // heuristic (e.g. historical replay) with no trial count to report.
  makeItBackTrials: number | null;
  rawDecisionUtility: number;
  teamScoreUtilityComponent: number;
  equityUtilityComponent: number;
  pickScore: number;
  // Owner feedback closure (result-status taxonomy): true exactly when
  // every candidate evaluated alongside this one shared the same
  // championship-equity win_probability -- pickScore is a genuine,
  // honest 50.0 because the frozen formula found no real spread to
  // work with, not because this candidate was skipped or unevaluated.
  // Never changes pickScore's own value.
  pickScoreTiedNoSpread: boolean;
  action: string;
  warnings: string[];
  uncertainty: string;
  // Owner feedback closure (shared cross-metric result-status contract):
  // one status per metric family, keyed exactly as this interface's own
  // field names (playerScore/teamScore/championshipEquity/costOfWaiting/
  // makeItBack/pickScore). Additive only -- the metric's own value above
  // never changes because of this; this only labels it.
  metricStatus: Record<string, MetricStatus>;
  // NWR next-draft final blocker closure, section 2: marginal_roster_utility
  // is the real, walk-forward-validated PRIMARY candidate-ordering signal
  // (see decision_bundle_service.py's _candidate_sort_key) -- these two
  // fields have existed on the real backend payload since that promotion
  // but were never declared here or rendered anywhere in the UI. Both null
  // exactly when the backend's own computation legitimately failed for this
  // candidate (never a fabricated fallback) or when the caller didn't
  // request the richer explanation.
  marginalUtility: number | null;
  marginalRosterUtility: MarginalRosterUtility | null;
}

// NWR next-draft final blocker closure, section 2: the real, additive
// explanation block behind marginalUtility above -- see
// _safe_marginal_utility/explain_marginal_roster_reason
// (shadow_numeric_authorities_service.py). `label` is the real, current
// disclosure string the backend sends (has read "PROMOTED..." since the
// walk-forward adoption); never hardcode or duplicate it client-side.
export interface MarginalRosterUtility {
  utility: number;
  becomesStarter: boolean;
  benchRedundancyBefore: number;
  explanation: string;
  label: string;
}

// NWR NEXT-DRAFT FINAL BLOCKER CLOSURE (section 8): the real status/risk
// intake contract (current_player_status_overrides_service.py) has only
// three real kinds -- no "end date" field exists in the real backend
// (a richer taxonomy was assumed in earlier planning but never actually
// built; see docs/codex/NWR_STATUS_RISK_INTAKE_PATH_V1_20260908.md).
// This mirrors the real backend shape exactly, not an aspirational one.
export interface PlayerStatusOverride {
  playerId: string;
  playerName: string;
  kind: "SEASON_OUT" | "NOT_WITH_TEAM" | "ADMINISTRATIVE_EXEMPT" | "TEAM_CORRECTION";
  reason: string;
  effectiveDate: string;
  verifiedAtUtc: string;
  sources: string[];
  correctedTeam: string;
}

export interface MetricStatus {
  computationState:
    | "EVALUATED"
    | "PENDING"
    | "BUDGET_LIMITED"
    | "UNSUPPORTED"
    | "MISSING_INPUT"
    | "ERROR";
  genuineZero: boolean;
  // null where a "tie" has no meaning for this metric (e.g. Player Score).
  tiedNoSpread: boolean | null;
  validationDomain: string;
  sourceFreshness: string;
  dataCoverage: string | null;
}

export interface DecisionBundleTeamScore {
  percentile: number;
  rosterValue: number;
  populationSize: number;
  label: string;
}

export interface DecisionBundleChampionshipEquity {
  winProbability: number;
  standardError: number;
  seasonsSimulated: number;
  assumedFormat: boolean;
  label: string;
}

export interface DecisionBundleProvenance {
  leagueProfileHash: string;
  rosterStateHash: string;
  availablePlayerHash: string;
  universeHash: string;
  projectionModelVersion: string;
  marketSnapshotHash: string;
  featureSetVersion: string;
  teamScoreVersion: string;
  championshipEquityVersion: string;
  pickScoreVersion: string;
  optimizerVersion: string;
  seed: number;
  simulationCount: number;
  timestampUtc: string;
  bundleHash: string;
}

export interface DecisionBundleAvailable {
  available: true;
  speed: "FAST" | "STANDARD" | "DEEP";
  version: string;
  currentTeamScore: DecisionBundleTeamScore;
  currentChampionshipEquity: DecisionBundleChampionshipEquity;
  candidates: DecisionBundleCandidate[];
  provenance: DecisionBundleProvenance;
  simulationMetadata: Record<string, unknown>;
  latencySeconds: number;
}

export interface DecisionBundleUnavailable {
  available: false;
  speed: "FAST" | "STANDARD" | "DEEP";
  reason: string;
}

export type DecisionBundle = DecisionBundleAvailable | DecisionBundleUnavailable;

export interface RedraftDecisionBundleResponse {
  decisionBundle: DecisionBundle;
}

// Owner Test Candidate V1, sections 12/13: KHA historical replay preview --
// a fixed, read-only, explicitly-labeled artifact, never a live DecisionBundle.
export interface KhaShadowReplayPick {
  pickNumber: number;
  round: number;
  playerName: string;
  position: string;
  team: string;
  realNwrRankAtTimeOfPick: number;
  valueProxy: string;
  teamScoreBefore: number | null;
  teamScoreAfter: number | null;
  champEquityBefore: number | null;
  champEquityAfter: number | null;
  starterHolesBefore: string;
  starterHolesAfter: string;
  startingLineupValueDelta: number | null;
  topCandidateAlternatives: string;
  costOfWaiting: string;
  marketStateAdp: string;
  productionNwrRecommendation: string;
}

export interface KhaHistoricalReplayPreview {
  label: string;
  sourceRelativePath: string;
  disclosedLimitations: string;
  picks: KhaShadowReplayPick[];
}

export interface RedraftHistoricalReplayPreviewResponse {
  historicalReplay: KhaHistoricalReplayPreview;
}

export interface CatchUpCandidate {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
}

export interface CatchUpPreviewRow {
  pastedName: string;
  status: "MATCHED" | "AMBIGUOUS" | "NO_MATCH";
  playerId: string | null;
  playerName: string | null;
  position: string | null;
  team: string | null;
  candidates: CatchUpCandidate[];
  pickNumber: number;
}

export interface CatchUpPreview {
  rows: CatchUpPreviewRow[];
  overflowNames: string[];
  readyToApply: boolean;
}

export interface RedraftCatchUpPreviewResponse {
  catchUpPreview: CatchUpPreview;
}

export interface CatchUpAppliedRow {
  pickNumber: number;
  playerId: string;
  playerName: string;
}

export interface RedraftCatchUpApplyResponse {
  draftBoard: DraftBoard;
  catchUpApplied: CatchUpAppliedRow[];
}

// Owner feedback closure, section 7: the owner's real UDK ("Position
// Rankings -- Fantasy Footballers Podcast") CSV export -- a real
// subscriber source, distinct from NWR's own rankings, never a
// replacement for them. A single export may legitimately cover only one
// position (the owner's real file is 36 rows, all QB) -- `positions`
// only ever contains keys the owner has actually imported.
export interface UdkPlayerEntry {
  playerId: string | null;
  playerName: string;
  team: string;
  position: string;
  byeWeek: string;
  rank: number | null;
  points: number | null;
  risk: number | null;
  upside: number | null;
  // Preserved exactly as the source printed it (e.g. "2.06") -- UDK's
  // own round.pick-style notation from an unverified/unknown source
  // team count. Never parsed as a number, never reinterpreted as this
  // league's own round.pick.
  adpRaw: string;
  tier: number | null;
  outlook: string;
  // True when the Dynasty column is locked upsell text ("Unlock with
  // the 2026 UDK+..."), never a numeric rating invented from it.
  dynastyLocked: boolean;
  matchStatus: "MATCHED" | "UNMATCHED";
}

export interface UdkPositionSnapshot {
  position: string;
  entries: UdkPlayerEntry[];
  provider: string;
  importedAtUtc: string;
  sourceSha256: string;
  sourceRows: number;
  // NWR DATA-IMPORT UX FIX (2026-09-08): the real backend
  // (load_udk_rankings) already returns both of these; the TS contract
  // had been narrower than reality since this snapshot shape was
  // introduced.
  sourceFormat?: "CSV" | "PDF";
  historyCount?: number;
}

export interface UdkRankings {
  // A LIST, never a dict keyed by position string -- a real position
  // code like "QB" used as a JSON object key gets silently mangled to
  // "qB" by the shared camelCase key transform every facade payload
  // passes through server-side. Verified live against the running
  // desktop API, not merely assumed.
  positions: UdkPositionSnapshot[];
}

// NWR DATA-IMPORT UX FIX (2026-09-08, directive section 2): the real
// preview-before-activate response for a Ballers/UDK import (CSV or PDF).
export interface BallersPreview {
  sourceFormat: "CSV" | "PDF";
  sourceRows: number;
  matchedRows: number;
  unmatched: string[];
  warnings: string[];
  sourceSha256: string;
  perPositionCounts: Record<string, number>;
  duplicateRows: string[];
  // Capped sample per position (server-side) -- perPositionCounts above
  // carries the real, full counts.
  positions: Record<string, UdkPlayerEntry[]>;
}

export interface RedraftBootstrap {
  product: {
    title: string;
    contextLabel: string;
    authority: string;
  };
  status: SourceStatus;
  profiles: LeagueProfile[];
  presets: LeagueProfile[];
  activeProfileId: string | null;
  activeProfile: LeagueProfile | null;
  rankings: RedraftRanking[];
  replacementLevels: ReplacementLevel[];
  draftBoard: DraftBoard | null;
  ownerPlatformSnapshot?: OwnerPlatformSnapshotStatus;
  // NWR DATA-IMPORT UX FIX (2026-09-08, directive section 11): the real,
  // per-provider raw values behind the global owner platform snapshot,
  // keyed by NWR player id -- for a compact "Sleeper: 72.0, ESPN: 117.0..."
  // detail view (Compare/Player Drawer). The active league's own single
  // resolved column (source/overallAdp on rankings/DraftBoard) remains the
  // one real value used for Value/Reach/Cost-of-Waiting; this is read-only
  // supplementary detail, never a second source of truth.
  marketProviderAdp?: Record<string, MarketProviderAdp>;
  manualAssets?: ManualDraftAsset[];
  udkRankings?: UdkRankings;
  externalConsensus?: ExternalConsensusStatus;
  health: RedraftHealth;
  notices: Notice[];
}

// ---------------------------------------------------------------------------
// NWR pre-UI product-architecture hardening pass (2026-09-10): league
// identity/lifecycle/snapshot, player availability authority, and data
// health -- directive sections 1/2/3/5/6. See LEAGUE_CONTEXT.md,
// DATA_AUTHORITY.md.
// ---------------------------------------------------------------------------

export type LeagueLifecycle = "PRE_DRAFT" | "LIVE_DRAFT" | "IN_SEASON" | "OFFSEASON";

export interface LeagueWorkspaceContext {
  profileId: string;
  provider: "local" | "sleeper" | "espn" | "fantasypros";
  providerLeagueId: string | null;
  season: number;
  lifecycle: LeagueLifecycle;
  lifecycleBasis: string;
  currentWeek: number | null;
  scoringProfileHash: string;
  rosterStateHash: string | null;
  leagueSnapshotId: string;
  syncStatus: "LIVE" | "DEGRADED" | "NOT_APPLICABLE";
  syncAsOf: string | null;
  issues: string[];
}

export interface PlayerAvailabilityStatus {
  playerId: string;
  playerName: string;
  statusCategory: "OUT_FOR_SEASON" | "NOT_WITH_TEAM" | "ADMINISTRATIVE_EXEMPT" | "TEAM_CORRECTION";
  injuryDesignation: string | null;
  practiceState: string | null;
  irPupNfi: string | null;
  suspension: boolean;
  administrativeExempt: boolean;
  released: boolean;
  currentTeam: string | null;
  reason: string;
  source: string;
  sourceAsOf: string;
  overrideKind: string;
}

export interface PlayerAvailabilityStatusResult {
  statuses: PlayerAvailabilityStatus[];
  authorityHealth: {
    authority: string;
    automatedFeed: boolean;
    entryCount: number;
    issues: string[];
  };
}

export type DataHealthCategoryName =
  | "LEAGUE_SYNC"
  | "WEEKLY_PROJECTIONS"
  | "ROS_PROJECTIONS"
  | "MARKET_ADP"
  | "PLAYER_STATUS"
  | "DECISION_ENGINE"
  | "SNAPSHOT";

export interface DataHealthCategory {
  category: DataHealthCategoryName;
  status: "OK" | "DEGRADED" | "UNAVAILABLE" | "NOT_APPLICABLE" | "NO_ACTIVITY";
  source: string | null;
  lastUpdate: string | null;
  freshness: string;
  degradationReason: string | null;
  impactOnRecommendations: string;
}

export interface DataHealthReport {
  categories: DataHealthCategory[];
  generatedAtUtc: string;
}

export interface NavigationItem {
  label: string;
  path: string;
  icon: string;
  shortcut?: string;
}

export interface NavigationGroup {
  label: string;
  items: NavigationItem[];
}

export interface CommandItem {
  id: string;
  label: string;
  detail: string;
  path: string;
  icon: string;
  keywords?: string[];
}
