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
  rosterLimits: Record<string, number>;
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
  draft: Pick<DraftContext, "rounds" | "draftSlot" | "replacementMethod">;
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

export interface KdstStreamerResult {
  authority: string;
  week: number;
  leagueId: string;
  positions: Record<"K" | "DST", KdstStreamerRow[]>;
  unmatchedSleeperPlayerIds: Record<"K" | "DST", string[]>;
  writeBehavior: string;
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
}

export interface UdkRankings {
  // A LIST, never a dict keyed by position string -- a real position
  // code like "QB" used as a JSON object key gets silently mangled to
  // "qB" by the shared camelCase key transform every facade payload
  // passes through server-side. Verified live against the running
  // desktop API, not merely assumed.
  positions: UdkPositionSnapshot[];
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
  manualAssets?: ManualDraftAsset[];
  udkRankings?: UdkRankings;
  externalConsensus?: ExternalConsensusStatus;
  health: RedraftHealth;
  notices: Notice[];
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
