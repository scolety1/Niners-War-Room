import { afterEach, describe, expect, it, vi } from "vitest";

import { NwrApiClient, NwrApiError, assertLocalApiBase, buildLocalApiUrl } from "./index";

afterEach(() => vi.unstubAllGlobals());

describe("assertLocalApiBase", () => {
  it("accepts only HTTP loopback endpoints", () => {
    expect(assertLocalApiBase("http://127.0.0.1:18741").hostname).toBe("127.0.0.1");
    expect(assertLocalApiBase("http://localhost:18742").hostname).toBe("localhost");
  });

  it.each([
    "https://127.0.0.1:18741",
    "http://0.0.0.0:18741",
    "http://example.com:18741",
    "file:///C:/NWR",
    "not-a-url",
  ])("rejects non-local endpoint %s", (value) => {
    expect(() => assertLocalApiBase(value)).toThrow(NwrApiError);
  });
});

describe("buildLocalApiUrl", () => {
  it("keeps root-relative API routes on the authenticated loopback origin", () => {
    expect(buildLocalApiUrl("http://127.0.0.1:18741", "/api/v1/bootstrap").href).toBe(
      "http://127.0.0.1:18741/api/v1/bootstrap",
    );
  });

  it.each(["api/v1/bootstrap", "//external.example/bootstrap"])(
    "rejects non-root-relative path %s",
    (path) => expect(() => buildLocalApiUrl("http://127.0.0.1:18741", path)).toThrow(NwrApiError),
  );
});

describe("NwrApiClient planning persistence", () => {
  it("sends a typed module payload only to the authenticated Dynasty loopback route", async () => {
    vi.stubGlobal("window", globalThis);
    const response = {
      contractVersion: "1.0.0",
      mode: "dynasty",
      data: {
        storeStatus: "loaded",
        updatedAtUtc: "2026-08-11T12:00:00Z",
        message: "Local workspace data loaded.",
        modules: [],
      },
      warnings: [],
      errors: [],
    };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(response), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new NwrApiClient("dynasty", {
      mode: "dynasty",
      apiBaseUrl: "http://127.0.0.1:18741",
      token: "nwr-desktop-test-token-0123456789-abcdef",
      contractVersion: "1.0.0",
    });

    await client.savePlanningModule("draft", {
      checks: [true, false, true, false],
      notes: "Verify the pick ledger.",
    });

    expect(fetchMock).toHaveBeenCalledOnce();
    const [target, init] = fetchMock.mock.calls[0] as [URL, RequestInit];
    expect(target.href).toBe("http://127.0.0.1:18741/api/v1/dynasty/planning/modules/draft");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({
      checks: [true, false, true, false],
      notes: "Verify the pick ledger.",
    });
    expect((init.headers as Record<string, string>)["X-NWR-Desktop-Token"]).toContain("test-token");
  });
});

describe("NwrApiClient trade workspace", () => {
  it("uses the typed list, atomic save, and governed Markdown export routes", async () => {
    vi.stubGlobal("window", globalThis);
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            contractVersion: "1.0.0",
            mode: "dynasty",
            data: {},
            warnings: [],
            errors: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new NwrApiClient("dynasty", {
      mode: "dynasty",
      apiBaseUrl: "http://127.0.0.1:18741",
      token: "nwr-desktop-test-token-0123456789-abcdef",
      contractVersion: "1.0.0",
    });
    const trade = {
      title: "Contender window",
      give: ["current:a"],
      receive: ["pick:2027:1"],
      teamWindow: "Contending" as const,
      notes: "Review the exact governed assets.",
    };

    await client.listSavedTrades();
    await client.saveTradeScenario({ scenarioId: null, ...trade });
    await client.exportTradeBrief(trade);

    const requests = fetchMock.mock.calls as [URL, RequestInit][];
    expect(requests.map(([target]) => target.pathname)).toEqual([
      "/api/v1/dynasty/trades",
      "/api/v1/dynasty/trades",
      "/api/v1/dynasty/trades/export",
    ]);
    expect(requests.map(([, init]) => init.method ?? "GET")).toEqual([
      "GET",
      "POST",
      "POST",
    ]);
    expect(JSON.parse(String(requests[1]?.[1].body))).toEqual({
      scenarioId: null,
      ...trade,
    });
    expect(JSON.parse(String(requests[2]?.[1].body))).toEqual(trade);
  });
});

describe("NwrApiClient Redraft profile management", () => {
  it("uses isolated duplicate and strict edit routes", async () => {
    vi.stubGlobal("window", globalThis);
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            contractVersion: "1.0.0",
            mode: "redraft",
            data: {},
            warnings: [],
            errors: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new NwrApiClient("redraft", {
      mode: "redraft",
      apiBaseUrl: "http://127.0.0.1:18742",
      token: "nwr-desktop-test-token-0123456789-abcdef",
      contractVersion: "1.0.0",
    });
    const update = {
      leagueName: "Sunday League",
      teamCount: 10,
      roster: {
        qb: 1,
        rb: 2,
        wr: 3,
        te: 1,
        flex: 1,
        superflex: 0,
        k: 0,
        dst: 0,
        benchSize: 7,
      },
      scoring: {
        reception: 1,
        passingTd: 4,
        interception: -2,
        tePremium: 0.5,
      },
      draft: {
        rounds: 16,
        draftSlot: 4,
        replacementMethod: "expected_available" as const,
      },
    };

    await client.duplicateRedraftProfile("profile/a", " Sunday Copy ");
    await client.updateRedraftProfile("profile/a", update);

    const requests = fetchMock.mock.calls as [URL, RequestInit][];
    expect(requests.map(([target]) => target.pathname)).toEqual([
      "/api/v1/redraft/profiles/profile%2Fa/duplicate",
      "/api/v1/redraft/profiles/profile%2Fa/edit",
    ]);
    expect(JSON.parse(String(requests[0]?.[1].body))).toEqual({
      leagueName: "Sunday Copy",
    });
    expect(JSON.parse(String(requests[1]?.[1].body))).toEqual(update);
  });
});

describe("NwrApiClient Redraft Draft Room", () => {
  it("uses only authenticated local start, advance, ADP refresh/import, and read-only Sleeper routes", async () => {
    vi.stubGlobal("window", globalThis);
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            contractVersion: "1.0.0",
            mode: "redraft",
            data: {},
            warnings: [],
            errors: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new NwrApiClient("redraft", {
      mode: "redraft",
      apiBaseUrl: "http://127.0.0.1:18742",
      token: "nwr-desktop-test-token-0123456789-abcdef",
      contractVersion: "1.0.0",
    });

    await client.startDraftRoom("fantasy-gamers", 9, "NORMAL", 20260817);
    await client.advanceDraftRoom("fantasy-gamers", false);
    await client.refreshRedraftAdp("fantasy-gamers");
    await client.importRedraftAdp("fantasy-gamers", "player,position\n");
    await client.ingestSleeperDraftPick("fantasy-gamers", "player-1", 1);

    const requests = fetchMock.mock.calls as [URL, RequestInit][];
    expect(requests.map(([target]) => target.pathname)).toEqual([
      "/api/v1/redraft/draft/fantasy-gamers/start",
      "/api/v1/redraft/draft/fantasy-gamers/advance",
      "/api/v1/redraft/adp/fantasy-gamers/refresh",
      "/api/v1/redraft/adp/fantasy-gamers/import",
      "/api/v1/redraft/draft/fantasy-gamers/sleeper-pick",
    ]);
    expect(JSON.parse(String(requests[0]?.[1].body))).toEqual({
      ownerSlot: 9,
      seed: 20260817,
      speed: "NORMAL",
      mode: "MOCK",
    });
    expect(JSON.parse(String(requests[4]?.[1].body))).toEqual({
      playerId: "player-1",
      pickNumber: 1,
    });
  });
});

describe("NwrApiClient Personal Workspace", () => {
  it("uses the bounded owner-board, decision, backup, and dry-run routes", async () => {
    vi.stubGlobal("window", globalThis);
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            contractVersion: "1.0.0",
            mode: "dynasty",
            data: {},
            warnings: [],
            errors: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new NwrApiClient("dynasty", {
      mode: "dynasty",
      apiBaseUrl: "http://127.0.0.1:18741",
      token: "nwr-desktop-test-token-0123456789-abcdef",
      contractVersion: "1.0.0",
    });

    await client.loadDynastyWorkspace();
    await client.savePersonalBoardEntry({
      assetId: "current:1",
      watchlist: true,
      target: false,
      avoid: false,
      tags: ["camp"],
      notes: "Revisit after camp.",
      teamWindow: "Contending",
    });
    await client.createOwnerDecision({
      title: "Camp checkpoint",
      decisionType: "player evaluation",
      assetIds: ["current:1"],
      rationale: "Role security needs another check.",
    });
    await client.backupDynastyWorkspace();
    await client.checkDynastyWorkspaceRestore();
    await client.adoptLegacyDynastyWorkspace();

    expect((fetchMock.mock.calls as [URL, RequestInit][]).map(([target]) => target.pathname)).toEqual([
      "/api/v1/dynasty/workspace",
      "/api/v1/dynasty/workspace/personal-board",
      "/api/v1/dynasty/workspace/decisions",
      "/api/v1/dynasty/workspace/backup",
      "/api/v1/dynasty/workspace/backup/check",
      "/api/v1/dynasty/workspace/adopt-legacy",
    ]);
    expect(JSON.parse(String((fetchMock.mock.calls as [URL, RequestInit][])[5]?.[1].body))).toEqual({
      confirmed: true,
    });
  });
});
