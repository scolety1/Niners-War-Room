# Streamer Findings

The current K/DST streamer boundary is correct but incomplete: optional FantasyPros consensus plus Sleeper availability, week-specific and read-only, with no hidden schedule/weather/injury weighting. Preserve it.

Build one shared streamer service over the Waiver pool with position plug-ins for QB, TE, K and DST. Inputs may include weekly projection/consensus, opponent, venue, weather, injury/usage, availability and owner horizon only after each source is admitted and fresh. Outputs must show Week 1, next 2-3 weeks, floor/ceiling where supported, roster replacement, source and freshness.

Do not train a new streamer model for completion. Start with licensed external consensus and deterministic rules. Missing schedule/weather/injury evidence remains unknown; it must not be silently imputed. The owner makes the platform transaction.
