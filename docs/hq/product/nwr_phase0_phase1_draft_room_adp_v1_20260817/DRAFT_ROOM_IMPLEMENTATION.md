# Draft Room Implementation

The Redraft desktop now renders a 10-column by 15-round snake board. Every cell retains pick number, player, NFL team, position, drafting team, actor, and selection basis.

Owner controls provide slots 1–10, Fast/Normal/Step modes, restart, undo, one CPU pick, and advance-to-owner. Clicking a team header changes the roster panel; the owner team is labeled `My Roster`. Drafted players leave the Available Players panel but remain on the board, in Recent Picks, team rosters, and the full Draft Log.

State remains local under the active Redraft profile. Writes are atomic and accompanied by a backup document. Legacy drafted-only boards are read compatibly and upgraded in memory without changing player identity.
