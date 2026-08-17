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
  provider: "local" | "sleeper";
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
  manualAssets?: ManualDraftAsset[];
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
