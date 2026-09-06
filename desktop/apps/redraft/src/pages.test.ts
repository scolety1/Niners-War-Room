import { describe, expect, it } from "vitest";

import {
  DRAFT_ROOM_ACCEPTANCE_LABELS,
  globalPickSearchRows,
  nextRapidCaptureIndex,
  type PickSearchAsset,
  rankingSearchRows,
} from "./pages";

// The exact 23 real KHA 2026 draft picks the live NWR capture misrecorded
// because the correct player was ranked in NWR but wasn't the one selected
// under clock pressure -- see
// sample_data/kha_real_draft_2026/RECONCILIATION_LEDGER.md /
// RECONCILIATION_LEDGER.csv (classification SEARCH_FAILURE). These are real
// production incident data, not synthetic examples.
const KHA_SEARCH_FAILURE_PLAYERS: PickSearchAsset[] = [
  { playerId: "p-brian-thomas-jr", playerName: "Brian Thomas Jr.", team: "JAX", position: "WR" },
  { playerId: "p-jordan-mason", playerName: "Jordan Mason", team: "MIN", position: "RB" },
  { playerId: "p-chuba-hubbard", playerName: "Chuba Hubbard", team: "CAR", position: "RB" },
  { playerId: "p-chris-godwin-jr", playerName: "Chris Godwin Jr.", team: "TB", position: "WR" },
  { playerId: "p-travis-kelce", playerName: "Travis Kelce", team: "KC", position: "TE" },
  { playerId: "p-dallas-goedert", playerName: "Dallas Goedert", team: "PHI", position: "TE" },
  { playerId: "p-quentin-johnston", playerName: "Quentin Johnston", team: "LAC", position: "WR" },
  { playerId: "p-josh-jacobs", playerName: "Josh Jacobs", team: "GB", position: "RB" },
  { playerId: "p-xavier-worthy", playerName: "Xavier Worthy", team: "KC", position: "WR" },
  { playerId: "p-blake-corum", playerName: "Blake Corum", team: "LAR", position: "RB" },
  { playerId: "p-jakobi-meyers", playerName: "Jakobi Meyers", team: "JAX", position: "WR" },
  { playerId: "p-josh-downs", playerName: "Josh Downs", team: "IND", position: "WR" },
  { playerId: "p-kyle-monangai", playerName: "Kyle Monangai", team: "CHI", position: "RB" },
  { playerId: "p-makai-lemon", playerName: "Makai Lemon", team: "PHI", position: "WR" },
  { playerId: "p-jacory-croskey-merritt", playerName: "Jacory Croskey-Merritt", team: "WSH", position: "RB" },
  { playerId: "p-tyler-shough", playerName: "Tyler Shough", team: "NO", position: "QB" },
  { playerId: "p-jordyn-tyson", playerName: "Jordyn Tyson", team: "NO", position: "WR" },
  { playerId: "p-tj-hockenson", playerName: "T.J. Hockenson", team: "MIN", position: "TE" },
  { playerId: "p-zach-charbonnet", playerName: "Zach Charbonnet", team: "SEA", position: "RB" },
  { playerId: "p-jayden-reed", playerName: "Jayden Reed", team: "GB", position: "WR" },
  { playerId: "p-woody-marks", playerName: "Woody Marks", team: "HOU", position: "RB" },
  { playerId: "p-mike-washington-jr", playerName: "Mike Washington Jr.", team: "LV", position: "RB" },
  { playerId: "p-tre-tucker", playerName: "Tre Tucker", team: "LV", position: "WR" },
];

// A sample of the 14 real KHA_UDK_KDST_2026_SNAPSHOT.csv-backed K/DST manual
// assets from the same historical ledger (classification
// K_DST_UNREPRESENTABLE) -- these live only in the manual asset pool, never
// in ranked rows, and historically required first switching the position
// filter to K or DST to find at all.
const KHA_KDST_MANUAL_ASSETS: PickSearchAsset[] = [
  { playerId: "MANUAL_K_DAL", playerName: "Brandon Aubrey", team: "DAL", position: "K" },
  { playerId: "MANUAL_DST_HOU", playerName: "Texans D/ST", team: "HOU", position: "DST" },
  { playerId: "MANUAL_K_LAR", playerName: "Harrison Mevis", team: "LAR", position: "K" },
  { playerId: "MANUAL_DST_PHI", playerName: "Eagles D/ST", team: "PHI", position: "DST" },
];

describe("ranking search depth", () => {
  it("searches the full filtered universe even when the visible board is capped", () => {
    const rows = Array.from({ length: 608 }, (_, index) => index + 1);

    expect(rankingSearchRows(rows, "100", "")).toHaveLength(100);
    expect(rankingSearchRows(rows, "100", "Brock Purdy")).toHaveLength(608);
  });
});

describe("global pick search (KHA reconciliation-ledger regression)", () => {
  it("resolves every one of the 23 historical SEARCH_FAILURE picks by a realistic query fragment, ignoring position", () => {
    for (const target of KHA_SEARCH_FAILURE_PLAYERS) {
      const fragment = target.playerName.split(" ")[0]!.toLowerCase();
      const results = globalPickSearchRows(KHA_SEARCH_FAILURE_PLAYERS, [], [], fragment);
      expect(results.map((row) => row.playerId)).toContain(target.playerId);
    }
  });

  it("resolves every sampled historical K/DST manual asset without switching the position filter", () => {
    for (const target of KHA_KDST_MANUAL_ASSETS) {
      const fragment = target.playerName.split(" ")[0]!.toLowerCase();
      const results = globalPickSearchRows([], KHA_KDST_MANUAL_ASSETS, [], fragment);
      expect(results.map((row) => row.playerId)).toContain(target.playerId);
      expect(results.find((row) => row.playerId === target.playerId)?.source).toBe("MANUAL");
    }
  });

  it("finds an accented name from an unaccented query, and an unpunctuated query finds a punctuated name", () => {
    // Real gap found building the Saturday NWR PURE K/DST fixture: the
    // real Rams kicker is "Eddy Piñeiro" -- an operator typing the
    // ASCII "Pineiro" (no accent) must still find him.
    const kdstWithAccent = [
      { playerId: "MANUAL_K_LAR", playerName: "Eddy Piñeiro", team: "LAR", position: "K" },
    ];
    const accentResults = globalPickSearchRows([], kdstWithAccent, [], "pineiro");
    expect(accentResults.map((row) => row.playerId)).toContain("MANUAL_K_LAR");

    // A.J. Brown / AJ Brown (section 15's own named alias example) --
    // punctuation-insensitive for free from the same normalization.
    const punctuated = [
      { playerId: "p-aj-brown", playerName: "A.J. Brown", team: "PHI", position: "WR" },
    ];
    const punctuationResults = globalPickSearchRows(punctuated, [], [], "aj brown");
    expect(punctuationResults.map((row) => row.playerId)).toContain("p-aj-brown");
  });

  it("matches ranked players by team or position, not just name (owner-test follow-up: 'search QB' or 'search SF' must work)", () => {
    const byTeam = globalPickSearchRows(KHA_SEARCH_FAILURE_PLAYERS, [], [], "JAX");
    expect(byTeam.map((row) => row.playerId)).toEqual(
      expect.arrayContaining(["p-brian-thomas-jr", "p-jakobi-meyers"]),
    );
    const byPosition = globalPickSearchRows(KHA_SEARCH_FAILURE_PLAYERS, [], [], "TE");
    expect(byPosition.map((row) => row.playerId)).toEqual(
      expect.arrayContaining(["p-travis-kelce", "p-dallas-goedert"]),
    );
  });

  it("finds a match across ranked and manual assets in one query regardless of the other position's rows present", () => {
    const results = globalPickSearchRows(KHA_SEARCH_FAILURE_PLAYERS, KHA_KDST_MANUAL_ASSETS, [], "texans");
    expect(results).toHaveLength(1);
    expect(results[0]).toMatchObject({ playerName: "Texans D/ST", source: "MANUAL" });
  });

  it("excludes already-drafted players from both pools and returns nothing for an empty query", () => {
    expect(globalPickSearchRows(KHA_SEARCH_FAILURE_PLAYERS, KHA_KDST_MANUAL_ASSETS, [], "")).toHaveLength(0);
    const drafted = ["p-travis-kelce", "MANUAL_DST_HOU"];
    const results = globalPickSearchRows(KHA_SEARCH_FAILURE_PLAYERS, KHA_KDST_MANUAL_ASSETS, drafted, "e");
    expect(results.map((row) => row.playerId)).not.toContain("p-travis-kelce");
    expect(results.map((row) => row.playerId)).not.toContain("MANUAL_DST_HOU");
  });
});

describe("rapid-capture keyboard navigation (pure step function)", () => {
  it("ArrowDown and Tab both step forward and wrap", () => {
    expect(nextRapidCaptureIndex("ArrowDown", false, 0, 3)).toBe(1);
    expect(nextRapidCaptureIndex("Tab", false, 0, 3)).toBe(1);
    expect(nextRapidCaptureIndex("ArrowDown", false, 2, 3)).toBe(0);
  });

  it("ArrowUp and Shift+Tab both step backward and wrap", () => {
    expect(nextRapidCaptureIndex("ArrowUp", false, 1, 3)).toBe(0);
    expect(nextRapidCaptureIndex("Tab", true, 0, 3)).toBe(2);
  });

  it("returns null (lets the key behave normally) for unrelated keys or an empty result list", () => {
    expect(nextRapidCaptureIndex("Enter", false, 0, 3)).toBeNull();
    expect(nextRapidCaptureIndex("Tab", false, 0, 0)).toBeNull();
    expect(nextRapidCaptureIndex("a", false, 0, 3)).toBeNull();
  });
});

describe("rapid capture end-to-end: exact 23 KHA SEARCH_FAILURE replay", () => {
  it("records all 23 historical picks via type + (arrow-nav if needed) + Enter, no mouse", () => {
    const drafted: string[] = [];
    let totalKeystrokes = 0;
    let arrowStepsUsed = 0;

    for (const target of KHA_SEARCH_FAILURE_PLAYERS) {
      const lastToken = target.playerName.split(" ").at(-1)!.replace(/\.$/, "");
      const fragment = lastToken.toLowerCase();
      let results = globalPickSearchRows(KHA_SEARCH_FAILURE_PLAYERS, [], drafted, fragment);
      // Simulate arrow-key stepping to the target if it isn't the first match.
      let index = 0;
      let stepsForThisPick = 0;
      const targetIndex = results.findIndex((row) => row.playerId === target.playerId);
      expect(targetIndex).toBeGreaterThanOrEqual(0); // must be findable at all
      while (index !== targetIndex) {
        const stepped = nextRapidCaptureIndex("ArrowDown", false, index, results.length);
        expect(stepped).not.toBeNull();
        index = stepped!;
        stepsForThisPick += 1;
      }
      // Enter records the highlighted candidate.
      const recorded = results[index]!;
      expect(recorded.playerId).toBe(target.playerId);
      drafted.push(recorded.playerId);
      arrowStepsUsed += stepsForThisPick;
      totalKeystrokes += fragment.length + stepsForThisPick + 1; // + Enter
      // Re-search after "clearing" (simulating the box reset for the next pick) --
      // the just-drafted player must no longer appear.
      results = globalPickSearchRows(KHA_SEARCH_FAILURE_PLAYERS, [], drafted, fragment);
      expect(results.some((row) => row.playerId === target.playerId)).toBe(false);
    }

    expect(drafted).toHaveLength(23);
    expect(new Set(drafted).size).toBe(23); // no duplicate recordings
    // Interaction-count measurement (directive section 2): mostly
    // type+Enter, arrow-nav only where a last-name fragment is ambiguous
    // within this 23-player pool (e.g. "josh" -> Josh Jacobs / Josh Downs).
    expect(arrowStepsUsed).toBeLessThan(23); // not every pick needs disambiguation
    expect(totalKeystrokes).toBeLessThan(23 * 12); // bounded, not a full-name-every-time cost
    console.info(
      `rapid-capture 23/23 replay: ${totalKeystrokes} total keystrokes, ${arrowStepsUsed} arrow-nav steps across 23 picks (avg ${(totalKeystrokes / 23).toFixed(1)} keystrokes/pick)`,
    );
  });

  it("K/DST manual assets are recordable the same way, no position-filter switch needed", () => {
    const drafted: string[] = [];
    for (const target of KHA_KDST_MANUAL_ASSETS) {
      const fragment = target.playerName.split(" ")[0]!.toLowerCase();
      const results = globalPickSearchRows([], KHA_KDST_MANUAL_ASSETS, drafted, fragment);
      const targetIndex = results.findIndex((row) => row.playerId === target.playerId);
      expect(targetIndex).toBeGreaterThanOrEqual(0);
      drafted.push(results[targetIndex]!.playerId);
    }
    expect(drafted).toHaveLength(KHA_KDST_MANUAL_ASSETS.length);
  });
});

describe("Draft Room owner acceptance surface", () => {
  it("keeps the board, roster, timing, log, and ADP boundary visible", () => {
    expect(DRAFT_ROOM_ACCEPTANCE_LABELS).toEqual([
      "Draft board",
      "My Roster",
      "Available player panel",
      "Recent picks",
      "Full draft log",
      "Beat ADP pool",
      "Draft recommendations",
      "Advance to my pick",
      "Refresh FFC ADP",
      "Paste Rankings / ADP",
      "ADP unavailable",
    ]);
  });
});
