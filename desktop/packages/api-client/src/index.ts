import { invoke } from "@tauri-apps/api/core";
import {
  CONTRACT_VERSION,
  type ApiEnvelope,
  type ApiErrorBody,
  type DesktopMode,
  type DynastyBootstrap,
  type DynastyComparison,
  type DynastyWorkspace,
  type KdstStreamerResult,
  type MetricStatus,
  type OwnerDecisionInput,
  type PersonalBoardInput,
  type PlayerDetail,
  type PlanningModuleId,
  type PlanningModuleInput,
  type PlanningWorkspace,
  type PasteAdpPreview,
  type RedraftBootstrap,
  type RedraftCatchUpApplyResponse,
  type RedraftCatchUpPreviewResponse,
  type RedraftDecisionBundleResponse,
  type RedraftHistoricalReplayPreviewResponse,
  type RedraftExternalIntelligenceResponse,
  type RedraftProfileUpdateInput,
  type RedraftSleeperSyncResult,
  type RuntimeDescriptor,
  type TradeBriefExport,
  type TradeBriefInput,
  type TeamWindow,
  type TradeDecision,
  type TradeSaveResult,
  type TradeScenarioInput,
  type TradeWorkspace,
} from "@nwr/contracts";

const REQUEST_TIMEOUT_MS = 20_000;
const STARTUP_RETRY_DELAYS_MS = [0, 160, 320, 640, 1_000, 1_600] as const;

// NWR Big-Draft Readiness Overnight V1: declared locally (not yet added to
// @nwr/contracts) to keep this an additive, low-risk client change. The
// full `v1` field is the exact same shape as `RedraftDecisionBundleResponse`
// (imported above) minus its own `available`/`speed` wrapper.
export interface RedraftRawActionValueResponse {
  expectedTerminalValue: number;
  terminalValueStdev: number;
  terminalObjectiveName: string;
  lookaheadDepth: number;
  rolloutCount: number;
  modelVersion: string;
}

export interface RedraftDecisionBundleV2CandidateResponse {
  playerId: string;
  v2Status: string;
  teamScoreV2: Record<string, unknown> | null;
  championshipEquityV2: Record<string, unknown> | null;
  pickScore: number | null;
  // The real, historically-validated fix for the Fantasy Gamers candidate-
  // collapse bug (TEAM_SCORE_SATURATION -- see raw_action_value_live_service.py):
  // rawActionValue/expectedRegret/decisionQualityPercentile differentiate
  // candidates even when Pick Score itself legitimately ties. Declared here
  // (previously missing from this client type even though the backend
  // already returned them) so the consolidated Draft Room can surface them.
  rawActionValue: RedraftRawActionValueResponse | null;
  expectedRegret: number | null;
  decisionQualityPercentile: number | null;
  rawActionValueStatus: string;
  // NWR FINAL PRE-DRAFT GAP CLOSURE (section 2, "Metric Status
  // Consistency"): the same shared EVALUATED/BUDGET_LIMITED/UNSUPPORTED/...
  // taxonomy every other metric (Player Score, Team Score, Championship
  // Equity, Cost of Waiting, Make-It-Back, Pick Score) already carries --
  // previously RAV/DQ had only the bare `rawActionValueStatus` string
  // above, handled by ad hoc frontend string-matching. Additive only:
  // `rawActionValueStatus`/`decisionQualityPercentile` above are
  // unchanged.
  decisionQualityStatus: MetricStatus;
}

export interface RedraftDecisionBundleV2Response {
  decisionBundleV2: {
    available: boolean;
    speed: "FAST" | "STANDARD" | "DEEP";
    reason?: string;
    version?: string;
    v2Status?: string;
    teamCount?: number;
    evidenceContext?: Record<string, unknown>;
    currentTeamScoreV2?: Record<string, unknown> | null;
    candidates?: RedraftDecisionBundleV2CandidateResponse[];
    warnings?: string[];
    v1?: RedraftDecisionBundleResponse["decisionBundle"];
  };
}

export class NwrApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly recoveryAction: string;
  readonly fieldErrors: Record<string, string[]>;

  constructor(
    message: string,
    options: {
      status?: number | undefined;
      code?: string | undefined;
      recoveryAction?: string | undefined;
      fieldErrors?: Record<string, string[]> | undefined;
    } = {},
  ) {
    super(message);
    this.name = "NwrApiError";
    this.status = options.status ?? 0;
    this.code = options.code ?? "DESKTOP_API_ERROR";
    this.recoveryAction = options.recoveryAction ?? "Retry after checking Data Health.";
    this.fieldErrors = options.fieldErrors ?? {};
  }
}

function isTauriRuntime(): boolean {
  return "__TAURI_INTERNALS__" in window;
}

function browserRuntime(mode: DesktopMode): RuntimeDescriptor {
  const defaultPort = mode === "dynasty" ? "18741" : "18742";
  return {
    mode,
    apiBaseUrl:
      import.meta.env.VITE_NWR_API_BASE_URL ?? `http://127.0.0.1:${defaultPort}`,
    token:
      import.meta.env.VITE_NWR_API_TOKEN ??
      "nwr-desktop-development-token-only-000000000000",
    contractVersion: CONTRACT_VERSION,
  };
}

export function assertLocalApiBase(apiBaseUrl: string): URL {
  let value: URL;
  try {
    value = new URL(apiBaseUrl);
  } catch {
    throw new NwrApiError("The desktop service returned an invalid local address.", {
      code: "INVALID_API_ADDRESS",
    });
  }
  const localHost = value.hostname === "127.0.0.1" || value.hostname === "localhost";
  if (value.protocol !== "http:" || !localHost || value.username || value.password) {
    throw new NwrApiError("NWR Desktop only accepts an unauthenticated loopback URL.", {
      code: "NON_LOCAL_API_ADDRESS",
    });
  }
  value.pathname = value.pathname.replace(/\/$/, "");
  value.search = "";
  value.hash = "";
  return value;
}

export function buildLocalApiUrl(apiBaseUrl: string, path: string): URL {
  if (!path.startsWith("/") || path.startsWith("//")) {
    throw new NwrApiError("The desktop API path must be root-relative.", {
      code: "INVALID_API_PATH",
    });
  }
  const base = assertLocalApiBase(apiBaseUrl);
  return new URL(path, base);
}

async function resolveRuntime(mode: DesktopMode): Promise<RuntimeDescriptor> {
  const descriptor = isTauriRuntime()
    ? await invoke<RuntimeDescriptor>("desktop_runtime")
    : browserRuntime(mode);
  if (descriptor.mode !== mode) {
    throw new NwrApiError(
      `The ${mode} interface refused a ${descriptor.mode} desktop service.`,
      { code: "MODE_MISMATCH" },
    );
  }
  if (!descriptor.token || descriptor.token.length < 32) {
    throw new NwrApiError("The desktop session token is missing or invalid.", {
      code: "INVALID_SESSION",
    });
  }
  assertLocalApiBase(descriptor.apiBaseUrl);
  return descriptor;
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

export class NwrApiClient {
  readonly mode: DesktopMode;
  private readonly runtime: RuntimeDescriptor;

  constructor(mode: DesktopMode, runtime: RuntimeDescriptor) {
    this.mode = mode;
    this.runtime = runtime;
  }

  async bootstrap<T extends DynastyBootstrap | RedraftBootstrap>(): Promise<T> {
    let lastError: unknown;
    for (const wait of STARTUP_RETRY_DELAYS_MS) {
      if (wait) await delay(wait);
      try {
        return await this.request<T>("/api/v1/bootstrap");
      } catch (error) {
        lastError = error;
        if (error instanceof NwrApiError && error.status > 0 && error.status < 500) break;
      }
    }
    throw lastError instanceof Error
      ? lastError
      : new NwrApiError("NWR Desktop could not start its local service.");
  }

  dynastyPlayer(assetId: string): Promise<PlayerDetail> {
    return this.request(`/api/v1/dynasty/assets/${encodeURIComponent(assetId)}`);
  }

  dynastyCompare(assetIds: string[]): Promise<DynastyComparison> {
    return this.request("/api/v1/dynasty/compare", {
      method: "POST",
      body: JSON.stringify({ assetIds }),
    });
  }

  evaluateTrade(
    give: string[],
    receive: string[],
    teamWindow: TeamWindow,
  ): Promise<TradeDecision> {
    return this.request("/api/v1/dynasty/trades/evaluate", {
      method: "POST",
      body: JSON.stringify({ give, receive, teamWindow }),
    });
  }

  listSavedTrades(): Promise<TradeWorkspace> {
    return this.request("/api/v1/dynasty/trades");
  }

  saveTradeScenario(input: TradeScenarioInput): Promise<TradeSaveResult> {
    return this.request("/api/v1/dynasty/trades", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  exportTradeBrief(input: TradeBriefInput): Promise<TradeBriefExport> {
    return this.request("/api/v1/dynasty/trades/export", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  savePlanningModule(
    moduleId: PlanningModuleId,
    input: PlanningModuleInput,
  ): Promise<PlanningWorkspace> {
    return this.request(`/api/v1/dynasty/planning/modules/${encodeURIComponent(moduleId)}`, {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  createRedraftProfile(presetKey: string, leagueName: string): Promise<RedraftBootstrap> {
    return this.request("/api/v1/redraft/profiles", {
      method: "POST",
      body: JSON.stringify({ presetKey, leagueName }),
    });
  }

  importSleeperRedraftProfile(leagueId: string, username: string): Promise<RedraftBootstrap> {
    return this.request("/api/v1/redraft/sleeper/import", {
      method: "POST",
      body: JSON.stringify({ leagueId, username }),
    });
  }

  activateRedraftProfile(profileId: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/profiles/${encodeURIComponent(profileId)}/activate`, {
      method: "POST",
      body: "{}",
    });
  }

  loadDynastyWorkspace(): Promise<DynastyWorkspace> {
    return this.request("/api/v1/dynasty/workspace");
  }

  savePersonalBoardEntry(input: PersonalBoardInput): Promise<DynastyWorkspace> {
    return this.request("/api/v1/dynasty/workspace/personal-board", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  createOwnerDecision(input: OwnerDecisionInput): Promise<DynastyWorkspace> {
    return this.request("/api/v1/dynasty/workspace/decisions", {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  backupDynastyWorkspace(): Promise<DynastyWorkspace> {
    return this.request("/api/v1/dynasty/workspace/backup", {
      method: "POST",
      body: "{}",
    });
  }

  checkDynastyWorkspaceRestore(): Promise<DynastyWorkspace> {
    return this.request("/api/v1/dynasty/workspace/backup/check", {
      method: "POST",
      body: "{}",
    });
  }

  adoptLegacyDynastyWorkspace(): Promise<DynastyWorkspace> {
    return this.request("/api/v1/dynasty/workspace/adopt-legacy", {
      method: "POST",
      body: JSON.stringify({ confirmed: true }),
    });
  }

  duplicateRedraftProfile(profileId: string, leagueName?: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/profiles/${encodeURIComponent(profileId)}/duplicate`, {
      method: "POST",
      body: JSON.stringify({ ...(leagueName?.trim() ? { leagueName: leagueName.trim() } : {}) }),
    });
  }

  updateRedraftProfile(
    profileId: string,
    input: RedraftProfileUpdateInput,
  ): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/profiles/${encodeURIComponent(profileId)}/edit`, {
      method: "POST",
      body: JSON.stringify(input),
    });
  }

  markDrafted(
    profileId: string,
    playerId: string,
    emergencyOverride?: boolean,
  ): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/pick`, {
      method: "POST",
      body: JSON.stringify({ playerId, ...(emergencyOverride ? { emergencyOverride } : {}) }),
    });
  }

  startDraftRoom(
    profileId: string,
    ownerSlot: number,
    speed: "FAST" | "NORMAL" | "STEP" = "NORMAL",
    seed = 20260817,
    mode: "MOCK" | "LIVE_READ_ONLY" = "MOCK",
  ): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/start`, {
      method: "POST",
      body: JSON.stringify({ ownerSlot, seed, speed, mode }),
    });
  }

  advanceDraftRoom(profileId: string, onePick = false): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/advance`, {
      method: "POST",
      body: JSON.stringify({ onePick }),
    });
  }

  importRedraftAdp(profileId: string, csvText: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/adp/${encodeURIComponent(profileId)}/import`, {
      method: "POST",
      body: JSON.stringify({ csvText }),
    });
  }

  refreshRedraftAdp(profileId: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/adp/${encodeURIComponent(profileId)}/refresh`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  importUdkRankings(profileId: string, csvText: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/udk/${encodeURIComponent(profileId)}/import`, {
      method: "POST",
      body: JSON.stringify({ csvText }),
    });
  }

  // NWR LAST PRE-DRAFT BLOCKER CLOSURE (section 2): the real "all 32
  // teams' current K/DST" UDK snapshot importer -- the only real, live
  // K/DST source that ever existed was hard-gated to the owner's one
  // Fantasy Gamers Sleeper league; a manually-configured league (e.g.
  // tonight's real ESPN league) had no path to a current K/DST pool at
  // all until this route was wired.
  importUdkKdstSnapshot(profileId: string, csvText: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/udk-kdst/${encodeURIComponent(profileId)}/import`, {
      method: "POST",
      body: JSON.stringify({ csvText }),
    });
  }

  previewRedraftPasteAdp(profileId: string, pasteText: string, selectedSource: PasteAdpPreview["selectedSource"]): Promise<{ pastePreview: PasteAdpPreview }> {
    return this.request(`/api/v1/redraft/adp/${encodeURIComponent(profileId)}/paste/preview`, {
      method: "POST", body: JSON.stringify({ pasteText, selectedSource }),
    });
  }

  saveRedraftPasteAdp(profileId: string, pasteText: string, selectedSource: PasteAdpPreview["selectedSource"], sourceLabel: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/adp/${encodeURIComponent(profileId)}/paste/save`, {
      method: "POST", body: JSON.stringify({ pasteText, selectedSource, sourceLabel }),
    });
  }

  activateRedraftPasteAdp(profileId: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/adp/${encodeURIComponent(profileId)}/paste/activate`, { method: "POST", body: "{}" });
  }

  clearRedraftPasteAdp(profileId: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/adp/${encodeURIComponent(profileId)}/paste/clear`, { method: "POST", body: "{}" });
  }

  setRedraftOwnerPlatformSelection(profileId: string, selection: "AUTO" | "CONSENSUS" | "SLEEPER" | "ESPN" | "FANTASYPROS" | "DISABLED"): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/adp/${encodeURIComponent(profileId)}/paste/selection`, {
      method: "POST", body: JSON.stringify({ selection }),
    });
  }

  approveRedraftOwnerPlatformManualMatch(profileId: string, pastedName: string, pastedPosition: string, pastedPositionRank: string, selectedNwrPlayerId: string, sourceSnapshotHash = ""): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/adp/${encodeURIComponent(profileId)}/paste/manual-match`, {
      method: "POST", body: JSON.stringify({ pastedName, pastedPosition, pastedPositionRank, selectedNwrPlayerId, sourceSnapshotHash }),
    });
  }

  ingestSleeperDraftPick(
    profileId: string,
    playerId: string,
    pickNumber: number,
  ): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/sleeper-pick`, {
      method: "POST",
      body: JSON.stringify({ playerId, pickNumber }),
    });
  }

  syncSleeperDraftPicks(profileId: string): Promise<RedraftSleeperSyncResult> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/sleeper-sync`, {
      method: "POST",
      body: "{}",
    });
  }

  previewCatchUpPaste(profileId: string, paste: string): Promise<RedraftCatchUpPreviewResponse> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/catch-up/preview`, {
      method: "POST",
      body: JSON.stringify({ paste }),
    });
  }

  applyCatchUpPaste(profileId: string, paste: string): Promise<RedraftCatchUpApplyResponse> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/catch-up/apply`, {
      method: "POST",
      body: JSON.stringify({ paste }),
    });
  }

  getRedraftDecisionBundle(
    profileId: string,
    speed: "FAST" | "STANDARD" | "DEEP" = "FAST",
    positionFilter?: string,
  ): Promise<RedraftDecisionBundleResponse> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/decision-bundle`, {
      method: "POST",
      body: JSON.stringify(positionFilter ? { speed, positionFilter } : { speed }),
    });
  }

  // NWR Big-Draft Readiness Overnight V1: the historically-validated
  // CHALLENGER DecisionBundle (Team Score V2 / Championship Equity V2 on
  // top of the exact same live state, unmodified V1 fields nested under
  // `v1`). Separate, additive endpoint -- calling this changes nothing
  // about `getRedraftDecisionBundle()` above. No UI currently calls this;
  // it exists so a future, explicit "VALIDATED ENGINE V2 -- SHADOW"
  // toggle can be wired in without any backend work remaining. NOT YET
  // build-verified against @nwr/contracts' real response typing in this
  // session (no network access to install this package's dependencies)
  // -- treat the return shape as unverified until a real `tsc`/build
  // pass confirms it, even though the backend route itself is real and
  // tested (see decision_bundle_service_v2.py).
  getRedraftDecisionBundleV2(
    profileId: string,
    speed: "FAST" | "STANDARD" | "DEEP" = "FAST",
  ): Promise<RedraftDecisionBundleV2Response> {
    return this.request(
      `/api/v1/redraft/draft/${encodeURIComponent(profileId)}/decision-bundle-v2`,
      { method: "POST", body: JSON.stringify({ speed }) },
    );
  }

  getKhaHistoricalReplayPreview(): Promise<RedraftHistoricalReplayPreviewResponse> {
    return this.request("/api/v1/redraft/historical-replay/kha-2026-09-02");
  }

  getRedraftExternalIntelligence(profileId: string): Promise<RedraftExternalIntelligenceResponse> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/external-intelligence`);
  }

  undoDraftPick(profileId: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/undo`, {
      method: "POST",
      body: "{}",
    });
  }

  replaceDraftPick(profileId: string, pickNumber: number, playerId: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/pick/replace`, {
      method: "POST",
      body: JSON.stringify({ pickNumber, playerId }),
    });
  }

  clearDraftPick(profileId: string, pickNumber: number): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/pick/clear`, {
      method: "POST",
      body: JSON.stringify({ pickNumber }),
    });
  }

  fillDraftPickGap(profileId: string, pickNumber: number, playerId: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/pick/fill-gap`, {
      method: "POST",
      body: JSON.stringify({ pickNumber, playerId }),
    });
  }

  undoDraftPickCorrection(profileId: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/draft/${encodeURIComponent(profileId)}/pick/undo-correction`, {
      method: "POST",
      body: "{}",
    });
  }

  startPracticalMock(profileId: string): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/profiles/${encodeURIComponent(profileId)}/practical-mock`, {
      method: "POST",
      body: "{}",
    });
  }

  setNwrPureMode(profileId: string, enabled: boolean): Promise<RedraftBootstrap> {
    return this.request(`/api/v1/redraft/profiles/${encodeURIComponent(profileId)}/nwr-pure-mode`, {
      method: "POST",
      body: JSON.stringify({ enabled }),
    });
  }

  kdstStreamer(week: number): Promise<KdstStreamerResult> {
    return this.request("/api/v1/redraft/kdst/streamer", {
      method: "POST",
      body: JSON.stringify({ week }),
    });
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const target = buildLocalApiUrl(this.runtime.apiBaseUrl, path);
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const response = await fetch(target, {
        ...init,
        cache: "no-store",
        credentials: "omit",
        redirect: "error",
        signal: controller.signal,
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-NWR-Desktop-Token": this.runtime.token,
          ...(init.headers ?? {}),
        },
      });
      const payload = (await response.json().catch(() => null)) as ApiEnvelope<T> | null;
      if (!response.ok) {
        const error = payload?.errors?.[0];
        throw new NwrApiError(error?.message ?? `Desktop request failed (${response.status}).`, {
          status: response.status,
          code: error?.code,
          recoveryAction: error?.recoveryAction,
          fieldErrors: error?.fieldErrors,
        });
      }
      if (!payload || !("data" in payload) || payload.mode !== this.mode) {
        throw new NwrApiError("The desktop service returned an invalid contract envelope.", {
          status: response.status,
          code: "INVALID_CONTRACT",
        });
      }
      if (!payload.contractVersion.startsWith("1.")) {
        throw new NwrApiError(
          `Desktop contract ${payload.contractVersion} is not supported by this app.`,
          { status: response.status, code: "CONTRACT_VERSION_MISMATCH" },
        );
      }
      return payload.data;
    } catch (error) {
      if (error instanceof NwrApiError) throw error;
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new NwrApiError("The local NWR service did not respond in time.", {
          code: "REQUEST_TIMEOUT",
        });
      }
      throw new NwrApiError("The local NWR service is not available yet.", {
        code: "SERVICE_UNAVAILABLE",
      });
    } finally {
      window.clearTimeout(timeout);
    }
  }
}

export async function createNwrClient(mode: DesktopMode): Promise<NwrApiClient> {
  return new NwrApiClient(mode, await resolveRuntime(mode));
}
