import { describe, expect, it } from "vitest";

import { detectedPlatform, platformCoverageText } from "./adp-providers";

describe("owner platform ADP provider display", () => {
  it("shows stable lower-case contract coverage keys with owner-facing labels", () => {
    expect(platformCoverageText({
      consensus: { available: 4, total: 4 }, sleeper: { available: 2, total: 4 },
      espn: { available: 3, total: 4 }, fantasypros: { available: 1, total: 4 },
    })).toBe("Consensus: 4/4 · Sleeper: 2/4 · ESPN: 3/4 · FantasyPros: 1/4");
  });

  it("detects Fantasy Gamers' persisted Sleeper provider before a snapshot exists", () => {
    expect(detectedPlatform({ provider: "sleeper" } as never)).toBe("Sleeper");
    expect(detectedPlatform({ provider: "espn" } as never)).toBe("ESPN");
    expect(detectedPlatform({ provider: "local" } as never)).toBe("Consensus");
  });
});
