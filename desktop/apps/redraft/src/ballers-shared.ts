// NWR CHEAT SHEET -- COMBINED NWR + MARKET + BALLERS VIEW (2026-09-08):
// extracted from draft-room-v2.tsx, unchanged, so Cheat Sheets' new
// Combined view (which cannot import from draft-room-v2.tsx without a
// circular import, since draft-room-v2.tsx itself renders CheatSheetPage)
// resolves the owner's imported Ballers/UDK data the exact same way
// Suggestions' "Show Ballers" column and the Player Drawer already do --
// one shared map, never a second, divergently-built lookup.
import type { RedraftBootstrap, UdkPlayerEntry } from "@nwr/contracts";

export function buildUdkEntryById(
  udkRankings: RedraftBootstrap["udkRankings"],
): Map<string, UdkPlayerEntry> {
  const map = new Map<string, UdkPlayerEntry>();
  for (const position of udkRankings?.positions ?? []) {
    for (const entry of position.entries) {
      if (entry.playerId) map.set(entry.playerId, entry);
    }
  }
  return map;
}
