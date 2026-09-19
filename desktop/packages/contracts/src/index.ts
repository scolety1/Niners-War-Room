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
  ownership?: AssetOwnership;
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

// Dynasty League Import V1 (Worker 3): real Sleeper ownership annotation,
// additive on top of every already-governed row -- see
// `dynasty_sleeper_league_service.annotate_ownership`'s own docstring for
// the exact honesty contract (never guessed, `UNRESOLVED` disclosed for
// rookies rather than silently omitted).
export type OwnershipStatus = "OWNED" | "FREE_AGENT" | "UNRESOLVED";

export interface AssetOwnership {
  ownershipStatus: OwnershipStatus;
  rosterId: number | null;
  rosterTeamName: string | null;
  rosterSlotStatus: string | null;
  isMyTeam: boolean;
  reason: string;
}

/** Present on `DynastyBootstrap`/`DynastyWorkspace` only once a league has
 * been connected (`league_profile_id` was resolved server-side from the
 * persisted "active league" marker) -- absent entirely otherwise, matching
 * the byte-identical-when-not-connected guarantee the backend facade
 * tests. */
export interface DynastyLeagueContext {
  profileId: string;
  leagueName: string;
  myRosterId: number | null;
  fetchedAtUtc: string;
  // D1 fix (NWR Sunday Readiness overnight cycle, Worker 4): additive --
  // lets the frontend offer a real "Refresh from Sleeper" action on an
  // already-connected league by resubmitting the same real league id (and
  // owner id, when known) instead of requiring disconnect -> reconnect.
  leagueId: string;
  myOwnerId: string | null;
}

export interface DynastyLeagueImportInput {
  leagueId: string;
  myOwnerId?: string;
  profileId?: string;
}

export interface DynastyLeagueRosterSummary {
  rosterId: number;
  ownerId: string;
  teamName: string;
  isMyTeam: boolean;
  playerCount: number;
  wins: number;
  losses: number;
  ties: number;
}

/** The full response of `load_dynasty_league_profile` -- what the "already
 * connected" state can look like when the owner revisits the Connect
 * League screen. */
export interface DynastyLeagueProfileSummary {
  profileId: string;
  leagueId: string;
  leagueName: string;
  season: string;
  numTeams: number;
  myOwnerId: string | null;
  myRosterId: number | null;
  scoringSettings: Record<string, number>;
  rosterPositions: string[];
  taxiSlots: number;
  reserveSlots: number;
  rosters: DynastyLeagueRosterSummary[];
  myPickCapitalBySeason: Record<string, number>;
  fetchedAtUtc: string;
  updatedAtUtc: string;
}

export interface DynastyWorkspace {
  storeStatus: "loaded" | "empty" | "blocked";
  message: string;
  updatedAtUtc: string;
  personalBoard: PersonalBoardEntry[];
  decisions: OwnerDecisionRecord[];
  backup: WorkspaceBackupStatus;
  dynastyLeague?: DynastyLeagueContext;
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
  ownership?: AssetOwnership;
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
  ownership?: AssetOwnership;
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
  ownership?: AssetOwnership;
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
  dynastyLeague?: DynastyLeagueContext;
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
  ownership?: AssetOwnership;
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

/** Dynasty League Import V1 (Worker 4): one entry per asset id the backend
 * could make an honest ownership determination for -- a flat LIST, never a
 * dict keyed by the literal asset id (that shape hits the shared camelCase
 * JSON-key transform, which mangles any dict key it treats as a schema
 * field name; see `desktop_facade.compare_dynasty_assets`'s own comment).
 * Present only once a Dynasty league is connected, exactly like
 * `AssetOption.ownership`/`DynastyBootstrap.dynastyLeague`. */
export interface AssetOwnershipEntry {
  assetId: string;
  ownership: AssetOwnership;
}

export interface DynastyComparison {
  leans: CompareLean[];
  ranges: CompareRange[];
  players: ComparePlayer[];
  warnings: string[];
  bridge?: RookieVeteranBridge | null;
  ownership?: AssetOwnershipEntry[];
  dynastyLeague?: DynastyLeagueContext;
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
  ownership?: AssetOwnershipEntry[];
  dynastyLeague?: DynastyLeagueContext;
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
  // NWR pre-UI architecture CLOSURE pass (directive section 4): one
  // DecisionResultEnvelope PER POSITION -- same flat-list reasoning as
  // `positions`/`traceIds` above.
  decisionEnvelopes?: Array<{ position: "K" | "DST"; decisionEnvelope: DecisionResultEnvelope }>;
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
  /** NWR Post-UI closure pass (bug 2): the same canonical-identity boundary
   * `RedraftMyRosterPlayer.canonicalPlayerId` already exposes for the
   * owner's own roster -- `null` when this opponent player could not be
   * identity-matched to NWR's governed ranking pool (see
   * `identityStatus`). Any UI action that hands a player id to a
   * canonical-id-based endpoint (e.g. `redraftTradeAnalysis`'s "gives"/
   * "receives" side) must resolve through THIS field, never
   * `sleeperPlayerId` directly -- `sleeperPlayerId` is the raw provider id,
   * only valid at an actual Sleeper-facing boundary. */
  canonicalPlayerId: string | null;
  identityStatus: "MATCHED" | "UNMATCHED_IDENTITY";
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
  rankingWarning: string;
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
  canonicalPlayerId: string | null;
  playerName: string;
  position: string;
  team: string;
  projectedPoints: number | null;
  /** NWR Sunday Readiness overnight cycle, Worker 3 (W7 fix): the real
   * scoring basis `projectedPoints` was computed under --
   * "NWR_LEAGUE_SCORING" / "NWR_LEAGUE_SCORING_KDST_WEEKLY" (exact) /
   * "NWR_LEAGUE_SCORING_KDST_WEEKLY_PARTIAL" (some real league scoring
   * category could not be mapped from the provider's raw stats) /
   * "SLEEPER_PROVIDER_SCORING" (generic provider passthrough, not this
   * league's own scoring). `null` only for a player with no real
   * projection row at all. */
  scoringContext?: string | null;
  /** Real, named league scoring categories (nonzero weight) this player's
   * raw stats could not support -- e.g. a 50+ yard field-goal tier the
   * provider never breaks out. Empty unless `scoringContext` is the
   * PARTIAL label above. */
  unsupportedScoringCategories?: string[];
  /** NWR pre-UI architecture CLOSURE pass (directive section 2): the
   * canonical PlayerAvailabilityStatus authority, `null` when this player
   * carries no known status issue -- see DATA_AUTHORITY.md. */
  playerAvailabilityStatus: PlayerAvailabilityStatus | null;
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
  canonicalPlayerId: string | null;
  playerName: string;
  position: string;
  projectedPoints: number | null;
  /** See `WeeklyLineupSlotPlayer.scoringContext`. */
  scoringContext?: string | null;
  unsupportedScoringCategories?: string[];
  playerAvailabilityStatus: PlayerAvailabilityStatus | null;
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

// NWR Sunday Readiness overnight cycle, Worker 2 (W2/W3): real reserve/taxi
// and locked-bench coverage -- kept distinct from `excluded` (a real
// status-override exclusion) and from a genuinely available `bench`
// player. Neither bucket is ever selectable as an unconditional START.
export interface WeeklyLineupCoverageEntry {
  sleeperPlayerId: string;
  canonicalPlayerId: string | null;
  playerName: string;
  position: string;
  projectedPoints?: number | null;
  isTaxi?: boolean;
  playerAvailabilityStatus: PlayerAvailabilityStatus | null;
}

export interface WeeklyGameLockInfo {
  season: number;
  week: number;
  seasonType: string;
  source: string;
  sourceStatus: "OK" | "UNAVAILABLE";
  fetchedAt: string;
  lockedTeams: string[];
  // A flat list, not a dict keyed by team code -- the shared desktop API
  // camelCase JSON-key transform mangles arbitrary data-dict keys (e.g.
  // "BUF" -> "bUF"); see `weekly_game_lock_service.py`'s `to_dict()`.
  kickoffUtcByTeam: Array<{ team: string; kickoffUtc: string }>;
  unknownTeams: string[];
  issues: string[];
  error: string | null;
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
  /** A starter whose provider identity was never confirmed against NWR's
   * canonical mapping -- may still carry a real point value, but that
   * value is not the same confidence as a confirmed identity. */
  unresolvedIdentityStarterCount?: number;
  /** NWR Sunday Readiness overnight cycle, Worker 3 (W7 fix): `true` when
   * at least one starter that actually contributed to `projectedTotal` was
   * scored under a non-exact context (generic provider points, or a
   * partial league-exact K/DST match) -- so the UI can disclose that the
   * total is not uniformly exact-league-scored rather than implying it is.
   */
  nonExactScoringInTotal?: boolean;
  starters: WeeklyLineupSlot[];
  bench: WeeklyLineupBenchPlayer[];
  excluded: Array<{
    sleeperPlayerId: string;
    canonicalPlayerId: string | null;
    playerName: string;
    position: string;
    playerAvailabilityStatus: PlayerAvailabilityStatus | null;
  }>;
  reserve?: WeeklyLineupCoverageEntry[];
  lockedUnavailable?: WeeklyLineupCoverageEntry[];
  gameLock?: WeeklyGameLockInfo;
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
  /** NWR Sunday Readiness overnight cycle, Worker 3 (W5 fix): in
   * THIS_WEEK mode, this now reflects a real, independently-recomputed
   * weekly-lineup evaluation (`null` when not evaluated this pass --
   * NEVER silently defaulted to the season-long flag). In REST_OF_SEASON
   * mode, unchanged: the season-long `marginal_roster_utility_v2` flag.
   * See `becomesStarterBasis`. */
  becomesStarter: boolean | null;
  /** "THIS_WEEK_LINEUP_EVALUATION" | "UNAVAILABLE_NOT_EVALUATED_THIS_PASS"
   * | "SEASON_MARGINAL_UTILITY" -- which of the two meanings above
   * `becomesStarter` actually carries for this row. */
  becomesStarterBasis?: string;
  /** The real, legal-lineup usable gain THIS_WEEK mode ranks by (see
   * `rank_waiver_candidates`'s W5 fix) -- `null` for REST_OF_SEASON or a
   * candidate this pass did not evaluate. */
  thisWeekLineupGain?: number | null;
  thisWeekEvaluated?: boolean;
  marginalUtilityExplanation: string;
  identityStatus: string;
  faabBidLowDollars: number | null;
  faabBidHighDollars: number | null;
  faabUrgency: "HIGH" | "MEDIUM" | "LOW" | null;
  faabRationale: string | null;
  playerAvailabilityStatus: PlayerAvailabilityStatus | null;
}

export interface WaiverDropCandidate {
  canonicalPlayerId: string;
  playerName: string;
  position: string;
  marginalUtility: number | null;
  explanation: string;
  playerAvailabilityStatus: PlayerAvailabilityStatus | null;
}

/**
 * Waiver Night V1 (Section 4, Add/Drop context repair): before this fix,
 * `netMarginalUtility` subtracted the add's value against the owner's
 * ORIGINAL roster (`add.marginalUtility`) from the drop's value against the
 * roster WITH the drop already removed -- two different reference rosters
 * for one number. Fixed: `add`/`drop` are now both evaluated against the
 * SAME post-drop roster before the difference is taken (via NWR's
 * unchanged, closed `marginal_roster_utility_v2` authority). This is a
 * real, same-context marginal comparison -- NOT an authoritative
 * "total-roster" or "completed-transaction" utility; no such objective is
 * defined anywhere else in this codebase.
 */
export interface WaiverAddDropPairing {
  add: WaiverAddCandidate;
  drop: WaiverDropCandidate | null;
  /** `false` only for a real, verified open non-reserve roster slot
   * (`contextLabel === "OPEN_ROSTER_SLOT_ADD_ONLY"`) or when this roster
   * genuinely has no drop candidates at all -- never inferred from
   * anything else. When `false`, `drop` is `null`: this add is legal on
   * its own, never a fabricated forced pairing. */
  dropRequired: boolean;
  /** The add's own marginal value against the roster exactly as it stands
   * today -- identical to `add.marginalUtility`, kept here too so both
   * reference points sit side by side. */
  addUtilityVsOriginalRoster: number | null;
  /** The add's own marginal value recomputed against the SAME roster
   * `drop`'s own value was computed against (the roster with `drop`
   * already removed). `null` when `drop` is `null` or either side's value
   * could not be computed. */
  addUtilityVsPostDropRoster: number | null;
  /** The drop's own marginal value against the post-drop roster -- equal to
   * `drop.marginalUtility` when `drop` is not `null` (already computed
   * against that same roster; no recomputation needed on this side). */
  dropUtilityVsPostDropRoster: number | null;
  /** The same-context difference (`addUtilityVsPostDropRoster -
   * dropUtilityVsPostDropRoster`) when a drop is paired, or the add's own
   * unchanged-roster value when no drop is needed. */
  netMarginalUtility: number | null;
  /** "SAME_CONTEXT_MARGINAL_COMPARISON" | "OPEN_ROSTER_SLOT_ADD_ONLY" |
   * "NO_DROP_CANDIDATE_AVAILABLE" -- see the field docs above for what
   * each one means. */
  contextLabel: string;
}

/**
 * Waiver Night V1 (Section 4, open-slot handling): whether the owner has a
 * real, verified open non-reserve roster slot this request, derived from
 * the league's own real `roster_positions` array (Sleeper's real per-slot
 * contract) compared against the RAW roster player-id count -- never from
 * how many roster ids happened to resolve to a canonical NWR identity
 * (conflating "could not identity-match" with "this slot is empty" would be
 * a real, different bug). `openSlotAvailable`/`rosterSlotsTotal`/
 * `rosterSlotsOccupied` are all `null` together when `roster_positions`
 * could not be read this request (`status ===
 * "UNVERIFIED_ROSTER_SLOTS"`) -- never a silent guess either way.
 */
export interface WaiverRosterSlotContext {
  openSlotAvailable: boolean | null;
  status: "OPEN_SLOT_AVAILABLE" | "NO_OPEN_SLOT" | "UNVERIFIED_ROSTER_SLOTS";
  rosterSlotsTotal: number | null;
  rosterSlotsOccupied: number | null;
}

/**
 * NWR Waiver Night V1 (Worker 3, Work Unit 6; extended by Worker 4,
 * LIVE/SCENARIO budget separation): the FAAB/waiver-priority context this
 * response's bid ranges were actually priced from -- read-only ground truth
 * (`league.settings.waiver_type`/`waiver_budget` + the owner's own
 * `roster.settings.waiver_budget_used`/`waiver_position`, and, for weeks
 * remaining, `settings.playoff_week_start` vs the real current NFL week),
 * never a fabricated/static value.
 *
 * `isFaabLeague: null` means Sleeper's own league settings could not be
 * read this request -- an honest UNAVAILABLE state (`source ===
 * "UNAVAILABLE"`), never silently treated as a $100 default. `isFaabLeague
 * === false` is a real rolling-waiver-priority league -- never show a
 * dollar bid range; show `waiverPosition` instead.
 *
 * `budgetMode` says which budget this specific response actually used:
 * `"LIVE"` (derived entirely from this same request's own real Sleeper
 * reads, no caller input) or `"SCENARIO"` (the owner's own explicit,
 * complete hypothetical, echoed back verbatim in `scenario` so a scenario
 * result can never be mistaken for a live one anywhere downstream).
 */
export interface WaiverFaabContext {
  isFaabLeague: boolean | null;
  budgetMode: "LIVE" | "SCENARIO";
  totalBudgetDollars: number | null;
  remainingBudgetDollars: number | null;
  weeksRemaining: number | null;
  weeksRemainingSource: "LIVE" | "DEFAULTED" | "SCENARIO_INPUT" | null;
  waiverPosition: number | null;
  source: "SLEEPER_LIVE" | "UNAVAILABLE";
  scenario: {
    remainingBudgetDollars: number;
    totalBudgetDollars: number;
    weeksRemaining: number;
  } | null;
}

/** The owner's explicit, complete "what if my budget were different"
 * hypothetical for `redraftWaivers` -- all three fields required together
 * (no partial override of the real live budget). Sending this at all is the
 * explicit opt-in the owner must take; omitting it means LIVE. */
export interface WaiverBudgetScenarioInput {
  remainingBudgetDollars: number;
  totalBudgetDollars: number;
  weeksRemaining: number;
}

/**
 * Waiver Night V1 (Section 5, THIS_WEEK honesty): `mode` does NOT change
 * the ranking signal `addCandidates`/`dropCandidates`/`addDropPairings`
 * are sorted by -- both modes rank by the real, closed
 * `marginal_roster_utility_v2` marginal-roster-utility (rest-of-season
 * oriented), unchanged. `THIS_WEEK` additionally computes/surfaces the
 * real weekly-projected points (`weeklyProjectedPoints`, `becomesStarter`
 * for THIS week's lineup) and uses them ONLY as a secondary tie-break when
 * two candidates' marginal utility is equal -- never as the primary sort
 * key. Render this honestly (see `TargetsTab`'s Mode caption in
 * `improve-team.tsx`) rather than implying THIS_WEEK reorders by weekly
 * value.
 */
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
  faabContext: WaiverFaabContext;
  rosterSlotContext: WaiverRosterSlotContext;
  unmatchedRosterSleeperPlayerIds: string[];
  /**
   * NWR Full Cycle V1 (Worker 7): a readable label/reason per entry in
   * `unmatchedRosterSleeperPlayerIds`, distinguishing two genuinely
   * different situations the flat raw-id list conflates -- a real,
   * catalog-known player/team-defense whose position (K/DST) simply has no
   * rows in NWR's governed ranking by design ("OUT_OF_RANKED_MODEL_SCOPE",
   * not a bug) vs. a genuinely unresolved Sleeper id ("UNKNOWN_TO_CATALOG",
   * worth investigating). Optional for backward compatibility with any
   * cached/older response shape; render `unmatchedRosterSleeperPlayerIds`
   * as a fallback when absent.
   */
  unmatchedRosterSleeperPlayers?: Array<{
    sleeperId: string;
    label: string;
    reason: string;
    category: "OUT_OF_RANKED_MODEL_SCOPE" | "UNKNOWN_TO_CATALOG";
  }>;
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
  playerAvailabilityStatus: PlayerAvailabilityStatus | null;
}

export interface TradeAnalysisResult {
  leagueId: string;
  traceId?: string | null;
  leagueSnapshotId?: string;
  decisionEnvelope?: DecisionResultEnvelope;
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
  /** NWR canonical player id (GSIS-style). Internal use only -- e.g. the
   * global Player Drawer, which is canonical-id-based everywhere. Do NOT
   * pass this to any endpoint that expects a raw Sleeper id (e.g.
   * `redraftTradeAnalysis`'s gives/receives) -- use `mySleeperPlayerId`
   * for that provider boundary instead (NWR Post-UI closure pass, bug 2:
   * this exact confusion is what broke the old "Open in Analyze" button). */
  myGivePlayerId: string;
  /** The real raw Sleeper id for the SAME player as `myGivePlayerId` --
   * the correct id to use at an actual Sleeper-facing boundary. `null`
   * only if this player could not be resolved back to a raw roster id
   * (should not happen in practice; never fabricated if it did). */
  mySleeperPlayerId: string | null;
  myGivePlayerName: string;
  myGivePlayerAvailabilityStatus: PlayerAvailabilityStatus | null;
  opponentGivePlayerId: string;
  /** Same boundary distinction as `mySleeperPlayerId`, for the opponent
   * side. */
  opponentSleeperPlayerId: string | null;
  opponentGivePlayerName: string;
  opponentGivePlayerAvailabilityStatus: PlayerAvailabilityStatus | null;
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
  decisionEnvelope?: DecisionResultEnvelope;
  candidates: TradeFinderCandidate[];
  writeBehavior: string;
}

/**
 * NWR Post-UI Product V1, P1-3 (Rich Trade Package Generator -- Worker 7,
 * UI half). Mirrors `DesktopBackendFacade.redraft_trade_package_search`'s
 * real response (`src/application/desktop_facade.py`), verified against a
 * real, live-computed payload (not just the ledger's prose description --
 * see `TradePackageEvaluation` below for the one place the ledger's own
 * "byte-for-byte the same shape as `TradeAnalysisResult`" claim was
 * slightly imprecise).
 */
export type TradePackageSearchMode = "FIND_WIN_WIN" | "TARGET_PLAYER" | "IMPROVE_POSITION";
export type TradePackageShape = "1-for-1" | "2-for-1" | "1-for-2" | "2-for-2";

/**
 * The per-side (owner or opponent) before/after evaluation nested inside a
 * `TradePackageCandidate`. Field names are identical to
 * `TradeAnalysisResult`'s own -- EXCEPT this nested shape carries no
 * `leagueId`/`traceId`/`leagueSnapshotId`/`decisionEnvelope`/
 * `championshipEquityNote`/`writeBehavior` (those are response-envelope-level
 * concerns that only exist once, at the top of `TradePackageSearchResult`,
 * not per side per candidate) -- confirmed directly against the facade's
 * own `_evaluation_payload()` serializer, not assumed from the ledger's
 * doc, which described it as "byte-for-byte the same" a little too
 * strongly.
 */
export interface TradePackageEvaluation {
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
}

export interface TradePackageCandidate {
  opponentRosterId: string;
  opponentTeamName: string;
  packageShape: TradePackageShape;
  /** Canonical NWR player ids (NOT raw Sleeper ids) -- same identity space
   * `TradeAnalysisResult.gives[].playerId` already uses. */
  youSend: string[];
  youSendNames: string[];
  youReceive: string[];
  youReceiveNames: string[];
  ownerEvaluation: TradePackageEvaluation;
  opponentEvaluation: TradePackageEvaluation;
  /** Structured, real-delta sentences computed by the backend from
   * `ownerEvaluation`. Never an acceptance probability -- the backend
   * computes none, in any mode. */
  whyItHelpsYou: string[];
  /** Same, computed from `opponentEvaluation`. Never an acceptance
   * probability. */
  whyItMayFitThem: string[];
}

export interface TradePackageSearchResult {
  leagueId: string;
  mode: TradePackageSearchMode;
  traceId?: string | null;
  leagueSnapshotId?: string;
  decisionEnvelope?: DecisionResultEnvelope;
  candidates: TradePackageCandidate[];
  /** Real `evaluate_trade` call count for this search (respects the
   * backend's documented hard caps). */
  packagesEvaluated: number;
  opponentsSearched: number;
  /** True when a hard search cap was hit before the space was exhausted --
   * render honestly; never imply the candidate list is complete when this
   * is true. */
  truncated: boolean;
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
  // NWR pre-UI architecture CLOSURE pass (directive section 2): the
  // canonical PlayerAvailabilityStatus authority, null when this player
  // carries no known status issue -- see DATA_AUTHORITY.md.
  playerAvailabilityStatus: PlayerAvailabilityStatus | null;
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

// P1-1 (2026-09-12): raw, directly-sourced Sleeper matchup/standings/
// playoff context -- additive-only fields on LeagueWorkspaceContext below.
// Every field is null/empty when Sleeper doesn't directly provide the
// fact (no provider, a failed read, an unresolvable opponent); nothing
// here is inferred, estimated, or simulated. `inPlayoffs` is a plain
// currentWeek >= playoffWeekStart comparison over two raw provider
// integers, not a prediction.
export interface LeagueWeekMatchupContext {
  week: number;
  hasOpponent: boolean;
  ownerPoints: number | null;
  opponentRosterId: number | string | null;
  opponentTeamName: string | null;
  opponentPoints: number | null;
  note: string | null;
}

export interface LeagueStandingsRow {
  rosterId: number | string | null;
  teamName: string;
  wins: number;
  losses: number;
  ties: number;
  pointsFor: number;
  pointsAgainst: number;
  isOwner: boolean;
}

export interface LeagueStandingsContext {
  rows: LeagueStandingsRow[];
  ownerRank: number | null;
}

export interface LeaguePlayoffBracketEntry {
  round: number | null;
  team1RosterId: number | string | null;
  team1TeamName: string | null;
  team2RosterId: number | string | null;
  team2TeamName: string | null;
  winnerRosterId: number | string | null;
  winnerTeamName: string | null;
  involvesOwner: boolean;
}

export interface LeaguePlayoffContext {
  leagueStatus: string | null;
  playoffWeekStart: number | null;
  inPlayoffs: boolean;
  bracketAvailable: boolean;
  bracket: LeaguePlayoffBracketEntry[];
}

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
  matchup: LeagueWeekMatchupContext | null;
  standings: LeagueStandingsContext | null;
  playoff: LeaguePlayoffContext | null;
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

// P1-4 (2026-09-12, Prospective Recommendation Ledger): the existing
// append-only in-season decision-trace ledger's owner-facing shape --
// TRADE_FINDER/TRADE_PACKAGE_SEARCH/DRAFT joined the tool-type set this
// pass (see in_season_decision_trace_service.py); DRAFT has no live call
// site yet (draft recommendation logic is out of this pass's scope).
export type DecisionTraceToolType =
  | "START_SIT"
  | "WAIVER"
  | "ADD_DROP"
  | "FAAB"
  | "TRADE"
  | "K_STREAMER"
  | "DST_STREAMER"
  | "TRADE_FINDER"
  | "TRADE_PACKAGE_SEARCH"
  | "DRAFT";

export type DecisionTraceStatus = "RECOMMENDED" | "OWNER_ACTION_RECORDED" | "OUTCOME_RECORDED";

export interface DecisionTraceOwnerAction {
  action: string;
  notes: string;
}

// History UI V2 (Live Player Intelligence V1, Worker 6): the real,
// decision-type-specific outcome detail schemas built by
// `prospective_outcome_schema_v1_service.py`'s `to_detail_dict()` methods.
// Field names and the `kind` discriminant literals here are a literal,
// intentionally-1:1 mirror of that Python module's own camelCase output --
// see `docs/codex/prospective_outcome_v1/PROSPECTIVE_OUTCOME_V1.md`. This
// is exactly the "backend enum -> API -> TS contract" boundary Work Unit
// 15's round-trip test checks (every real `KIND` string used on the Python
// side must appear, correctly spelled, as a TS union member here).
export interface OutcomePlayerPoints {
  playerId: string;
  points: number | null;
}

export interface StartSitOutcomeDetail {
  kind: "START_SIT_LINEUP_V1";
  week: number | null;
  recommendedStarterIds: string[];
  actualStarterIds: string[];
  eligibleAlternativeIdsAtLock: string[];
  recommendedOnlyIds: string[];
  actualOnlyIds: string[];
  recommendedProjectedTotal: number | null;
  actualPointsTotal: number | null;
  // A LIST, never a dict keyed by player id -- a real player id (e.g. a
  // Sleeper DST team code like "NE") passed as a JSON dict KEY gets
  // mangled by the backend's generic camelCase key transform ("NE" ->
  // "nE"), a real bug class this contract shape was fixed to avoid (see
  // `_points_by_player_list` in prospective_outcome_schema_v1_service.py).
  actualPointsByPlayer: OutcomePlayerPoints[];
  lineupOpportunityCost: number | null;
}

export interface WaiverOutcomeDetail {
  kind: "WAIVER_V1";
  recommendedPlayerId: string | null;
  claimSubmitted: boolean | null;
  claimWon: boolean | null;
  faabPaid: number | null;
  horizonWeeks: number;
  subsequentRosterUsageWeeks: number | null;
  subsequentTotalPoints: number | null;
}

export interface AddDropOutcomeDetail {
  kind: "ADD_DROP_V1";
  addedPlayerId: string | null;
  droppedPlayerId: string | null;
  horizonWeeks: number;
  addedPlayerSubsequentPoints: number | null;
  addedPlayerSubsequentRosterUsageWeeks: number | null;
  droppedPlayerSubsequentPoints: number | null;
  droppedPlayerReversed: boolean | null;
}

// FAAB deliberately keeps these two axes structurally separate -- "was the
// pickup good" is never conflated with "was the suggested $ range accurate".
export interface FaabPlayerDecisionQuality {
  subsequentPoints: number | null;
  subsequentRosterUsageWeeks: number | null;
  horizonWeeks: number;
}

export interface FaabBidRangeCalibration {
  suggestedBidLow: number | null;
  suggestedBidHigh: number | null;
  amountBid: number | null;
  won: boolean | null;
  actualWinningBid: number | null;
  bidWithinSuggestedRange: boolean | null;
  marginVsActualWinningBid: number | null;
}

export interface FaabOutcomeDetail {
  kind: "FAAB_V1";
  recommendedPlayerId: string | null;
  playerDecisionQuality: FaabPlayerDecisionQuality;
  bidRangeCalibration: FaabBidRangeCalibration;
}

export type TradeAcceptanceStatus = "ACCEPTED" | "REJECTED" | "UNKNOWN";

export interface TradeRealizedRosterOutcome {
  horizonWeeks: number;
  // LISTS, never dicts keyed by player id -- see `OutcomePlayerPoints`'s
  // own comment above for the real bug class this shape avoids.
  givesSubsequentPointsByPlayer: OutcomePlayerPoints[];
  receivesSubsequentPointsByPlayer: OutcomePlayerPoints[];
  netSubsequentPointsDelta: number | null;
}

export interface TradeOutcomeDetail {
  kind: "TRADE_V1";
  acceptanceStatus: TradeAcceptanceStatus;
  tradeAccepted: boolean | null;
  // Only ever populated when tradeAccepted === true -- a rejected/unknown
  // trade is never scored against an unobserved counterfactual (enforced
  // structurally on the Python side by TradeOutcomeDetail.__post_init__).
  realizedRosterOutcome: TradeRealizedRosterOutcome | null;
}

export type TradePackageDisposition = "IGNORED" | "CONSIDERED" | "SENT" | "ACCEPTED" | "UNKNOWN";

export interface TradeFinderOutcomeDetail {
  kind: "TRADE_FINDER_V1";
  packageDisposition: TradePackageDisposition;
  // Only ever populated when packageDisposition === "ACCEPTED".
  linkedTradeOutcome: TradeOutcomeDetail | null;
}

export interface StreamerOutcomeDetail {
  kind: "STREAMER_V1";
  position: string; // "K" | "DST"
  week: number | null;
  recommendedPlayerId: string | null;
  recommendedPlayerActualPoints: number | null;
  actualStarterPlayerId: string | null;
  actualStarterActualPoints: number | null;
  priorRosterOptionPlayerId: string | null;
  priorRosterOptionActualPoints: number | null;
  availableAlternativeIdsAtRecommendation: string[];
  bestAvailableAlternativeId: string | null;
  bestAvailableAlternativeActualPoints: number | null;
}

export interface DraftOutcomeDetail {
  kind: "DRAFT_V1";
  evaluationMethod: string;
  seasonLongRosterUtility: number | null;
  injuryLuckAdjustment: number | null;
  notes: string;
}

export type DecisionTraceOutcomeDetail =
  | StartSitOutcomeDetail
  | WaiverOutcomeDetail
  | AddDropOutcomeDetail
  | FaabOutcomeDetail
  | TradeOutcomeDetail
  | TradeFinderOutcomeDetail
  | StreamerOutcomeDetail
  | DraftOutcomeDetail;

export interface DecisionTraceOutcome {
  outcome: string;
  notes: string;
  // Additive (NWR Prospective Outcome V1 -> History UI V2): absent/`null`
  // for every outcome recorded before this pass, and for any decision type
  // this pass's ingestion mechanism has no real data to populate yet --
  // never fabricated when missing.
  detail?: DecisionTraceOutcomeDetail | null;
}

// ---------------------------------------------------------------------------
// History UI V3 (NWR Prospective Outcomes V1, Work Unit 13): the real
// `OutcomeEvaluation` contract (`prospective_outcome_evaluation_v1_service.
// py`) and the 8 real per-class evaluator `to_dict()` shapes
// (`prospective_outcome_*_evaluator_v1_service.py`, Workers 2/3) that back
// the new `evaluationDetail` field on `DecisionTraceHistoryEvent` below.
// Field names and the `evaluationStatus` union here are a literal,
// intentionally-1:1 mirror of those Python modules' own camelCase output --
// exactly the same "backend enum -> API -> TS contract" discipline
// `DecisionTraceOutcomeDetail` above already established.
// ---------------------------------------------------------------------------

// The real, closed 5-member set (`EVALUATION_STATUSES`,
// prospective_outcome_evaluation_v1_service.py). Never a parallel/invented
// set -- these are the exact strings the backend emits.
export type OutcomeEvaluationStatus =
  | "PENDING_OUTCOME"
  | "PENDING_WINDOW"
  | "EVALUATED"
  | "INSUFFICIENT_DECISION_CONTEXT"
  | "NOT_APPLICABLE";

export interface OutcomeEvaluationWindow {
  label: string;
  horizonWeeks: number | null;
}

export interface OutcomeEvaluation {
  schemaVersion: string;
  traceId: string;
  decisionType: string;
  leagueKey: string;
  leagueId: string;
  leagueSnapshotId: string | null;
  recommendationGeneratedAt: string;
  outcomeObservedAt: string | null;
  outcomeWindow: OutcomeEvaluationWindow;
  outcomeSource: string | null;
  outcomeSourceAsOf: string | null;
  ownerAction: Record<string, unknown> | null;
  factualOutcome: Record<string, unknown> | null;
  evaluationStatus: OutcomeEvaluationStatus | string;
  evaluationMetrics: Record<string, unknown>;
  issues: string[];
}

// The base fallback envelope -- used verbatim for DRAFT (no real evaluator
// this cycle, contract Section 2/hard boundary) and any tool this frontend
// build doesn't recognize.
export interface BaseEvaluationPayload {
  traceId: string;
  evaluation: OutcomeEvaluation;
}

export interface StartSitEvaluatorPayload {
  traceId: string;
  evaluation: OutcomeEvaluation;
  recommendedPlayerRealizedPoints: number | null;
  ownerSelectedPlayerRealizedPoints: number | null;
  lineupOpportunityCostPoints: number | null;
  bestLegalAlternativePlayerId: string | null;
  bestLegalAlternativeActualPoints: number | null;
  ownerActionObserved: boolean;
  issues: string[];
}

export interface WaiverEvaluatorPayload {
  traceId: string;
  evaluation: OutcomeEvaluation;
  recommendedPlayerId: string | null;
  recommendedDropPlayerId: string | null;
  claimableAtRecommendationTime: boolean | null;
  claimSubmitted: boolean | null;
  claimWon: boolean | null;
  faabPaid: number | null;
  horizonWeeks: number | null;
  subsequentTotalPoints: number | null;
  subsequentRosterUsageWeeks: number | null;
  issues: string[];
}

export interface AddDropEvaluatorPayload {
  traceId: string;
  evaluation: OutcomeEvaluation;
  addedPlayerId: string | null;
  droppedPlayerId: string | null;
  horizonWeeks: number | null;
  addedPlayerSubsequentPoints: number | null;
  addedPlayerSubsequentRosterUsageWeeks: number | null;
  droppedPlayerSubsequentPoints: number | null;
  droppedPlayerReversed: boolean | null;
  netRosterValuePoints: number | null;
  issues: string[];
}

export interface FaabEvaluatorPayload {
  traceId: string;
  evaluation: OutcomeEvaluation;
  recommendedPlayerId: string | null;
  // Deliberately TWO SEPARATE keys, never merged (contract Section 2).
  playerDecisionQuality: {
    subsequentPoints: number | null;
    subsequentRosterUsageWeeks: number | null;
    horizonWeeks: number;
  } | null;
  bidRangeCalibration: {
    suggestedBidLow: number | null;
    suggestedBidHigh: number | null;
    amountBid: number | null;
    won: boolean | null;
    actualWinningBid: number | null;
    bidWithinSuggestedRange: boolean | null;
    marginVsActualWinningBid: number | null;
  } | null;
  issues: string[];
}

export interface TradeEvaluatorPayload {
  traceId: string;
  evaluation: OutcomeEvaluation;
  ownerActionRaw: string | null;
  recommendedGivesIds: string[];
  recommendedReceivesIds: string[];
  acceptanceStatus: TradeAcceptanceStatus | string | null;
  tradeAccepted: boolean | null;
  horizonWeeks: number | null;
  netSubsequentPointsDeltaPoints: number | null;
  givesSubsequentPointsByPlayer: OutcomePlayerPoints[] | null;
  receivesSubsequentPointsByPlayer: OutcomePlayerPoints[] | null;
  issues: string[];
}

export interface TradeFinderEvaluatorPayload {
  traceId: string;
  decisionType: string;
  evaluation: OutcomeEvaluation;
  ownerActionRaw: string | null;
  recommendedGivesIds: string[];
  recommendedReceivesIds: string[];
  packageDisposition: TradePackageDisposition | string | null;
  tradeAccepted: boolean | null;
  horizonWeeks: number | null;
  netSubsequentPointsDeltaPoints: number | null;
  givesSubsequentPointsByPlayer: OutcomePlayerPoints[] | null;
  receivesSubsequentPointsByPlayer: OutcomePlayerPoints[] | null;
  issues: string[];
}

export interface StreamerEvaluatorPayload {
  traceId: string;
  evaluation: OutcomeEvaluation;
  position: string; // "K" | "DST"
  recommendedPlayerId: string | null;
  recommendedPlayerActualPoints: number | null;
  actualStarterPlayerId: string | null;
  actualStarterActualPoints: number | null;
  currentOptionPlayerId: string | null;
  currentOptionActualPoints: number | null;
  availableAlternativeIdsAtRecommendation: string[];
  bestAvailableAlternativeId: string | null;
  bestAvailableAlternativeActualPoints: number | null;
  regretVsActualStarterPoints: number | null;
  replacementLevelDeltaPoints: number | null;
  issues: string[];
}

export type DecisionTraceEvaluationDetail =
  | StartSitEvaluatorPayload
  | WaiverEvaluatorPayload
  | AddDropEvaluatorPayload
  | FaabEvaluatorPayload
  | TradeEvaluatorPayload
  | TradeFinderEvaluatorPayload
  | StreamerEvaluatorPayload
  | BaseEvaluationPayload;

export interface DecisionTraceHistoryEvent {
  traceId: string;
  league: string;
  leagueSnapshotId: string | null;
  season: number;
  week: number | null;
  decisionType: DecisionTraceToolType | string;
  recommendation: Record<string, unknown>;
  alternatives: Record<string, unknown>[];
  engineVersion: string;
  dataVersions: Record<string, string>;
  statusVersions: Record<string, string>;
  generatedAt: string;
  status: DecisionTraceStatus | string;
  ownerAction: DecisionTraceOwnerAction | null;
  ownerActionRecordedAt: string | null;
  outcome: DecisionTraceOutcome | null;
  outcomeRecordedAt: string | null;
  // History UI V3 (Work Unit 13): the real per-class `OutcomeEvaluation`
  // presentation for this row -- see
  // `prospective_outcome_history_presentation_v1_service.py`. Optional (not
  // `| null`) so a fixture/event captured before this pass still type-checks
  // without modification -- absent means "this backend build predates
  // evaluationDetail," never "evaluated to nothing."
  evaluationDetail?: DecisionTraceEvaluationDetail;
}

export interface DecisionTraceHistoryResult {
  profileId: string;
  leagueName: string;
  totalCount: number;
  events: DecisionTraceHistoryEvent[];
}

// ---------------------------------------------------------------------------
// Class-specific summary (NWR Prospective Outcomes V1, Work Unit 14):
// `redraft_decision_trace_outcome_summary`'s real response shape. Every
// summary axis is `{summaryStatus, sampleSize}` plus real computed fields
// ONLY when `summaryStatus === "SUMMARIZED"` -- gated by the preregistered
// `MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY` (20) entirely on the backend; this
// contract never re-derives that gate.
// ---------------------------------------------------------------------------

export type DecisionClassSummaryStatus = "NOT_ENOUGH_DATA_YET" | "SUMMARIZED";

export interface DecisionClassSummaryAxis {
  summaryStatus: DecisionClassSummaryStatus | string;
  sampleSize: number;
  [computedField: string]: unknown;
}

// Real evaluationStatus/acceptanceStatus/packageDisposition COUNT pairs --
// deliberately a LIST, never a dict keyed by the enum string itself. A dict
// keyed by an arbitrary enum-like string (e.g. `{"EVALUATED": 24}`) gets
// mangled by the backend's own generic camelCase-key transform
// (`"EVALUATED"` -> `"eVALUATED"`) -- the exact same real bug class already
// disclosed for player-id dict keys (`OutcomePlayerPoints[]` above). Found
// and fixed live this pass (`prospective_outcome_history_presentation_v1_
// service.py`'s own `_as_count_pairs`).
export interface DecisionClassStatusCount {
  status: string;
  count: number;
}

export interface DecisionClassDispositionCount {
  disposition: string;
  count: number;
}

export interface DecisionClassSummary {
  decisionType: string;
  statusCounts: DecisionClassStatusCount[];
  // TRADE only.
  acceptanceStatusCounts?: DecisionClassStatusCount[];
  // TRADE_FINDER only.
  packageDispositionCounts?: DecisionClassDispositionCount[];
  [axisOrField: string]: unknown;
}

export interface DecisionTraceOutcomeSummaryResult {
  profileId: string;
  leagueName: string;
  totalTraceCount: number;
  // A LIST, not a dict keyed by decisionType -- same real reason as
  // `statusCounts` above (`"START_SIT"`/`"K_STREAMER"`/etc. are exactly the
  // kind of ENUM-like string this transform mangles). Each entry already
  // carries its own real `decisionType` field.
  summaries: DecisionClassSummary[];
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
