# Known Caveat Differential

Result: no source-introduced semantic, accessibility, or viewport blocker.

## Streamlit deprecation warnings

Existing use_container_width calls can emit Streamlit deprecation warnings. The new helper contains no use_container_width call, and the page diff does not add or alter one. No new deprecation warning is attributable to this source commit. Unrelated warning repair is outside this lane.

## Direct-route startup notice

The brief Page not found notice reproduced while launching the real /player-compare route directly and the page then rendered normally. app/navigation.py is byte-identical between baseline and source, so the notice is unrelated to this commit. It was dismissed for measurement; no navigation repair was attempted.

## Synthetic states

Partial/empty and exception states that cannot be reached through the production minimum-two-player contract use test-only fixtures. Each rendered fixture has a prominent non-production warning. Unit coverage also verifies only Player B, neither selected, duplicate exclusion, stale, gated, unavailable, identity exception, source exception, long labels, and dense content without altering production data.

## Desktop JPEG storage

The real desktop JPEG is stored as 914x1000 even though the browser was set to a true 1440x1000 CSS viewport. This capture-backend limitation was reported by the source packet. Independent DOM readings prove document 1440/1440, main 1430/1430, two 627px selector outers at x80 and x723, and no page overflow. The JPEG dimension is not used as viewport proof.

## Keyboard automation

Native details/summary semantics, focusability, expansion by native click, visible 3px focus, and absence of keyboard interception passed. Synthesized Enter/Space events did not yield a reliable backend toggle trace. No programmatic focus-restoration claim is made; a manual screen-reader/physical-keyboard check remains recommended.

## Manifest checkout line endings

On this Windows checkout, Git materializes text packet files with CRLF while the repository blobs and source manifest were authored with canonical LF bytes. Raw worktree hashing therefore differs for 17 text entries. Hashing the source commit's Git blobs against MANIFEST.json passes all 26 entries; all binary JPEG worktree bytes also pass. The source packet commit/tree is unchanged.
