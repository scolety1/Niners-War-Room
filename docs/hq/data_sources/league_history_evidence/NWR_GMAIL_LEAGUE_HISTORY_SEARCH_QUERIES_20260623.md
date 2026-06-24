# NWR Gmail League History Search Queries - 2026-06-23

## Privacy Boundary

This query pack is for league-history evidence recovery only. Raw email bodies, raw Gmail exports, unrelated private content, and full personal messages must not be committed. Repo-tracked evidence should be limited to message metadata, short subject/date pointers, parsed league entities, and review notes.

## Core Queries

```text
in:anywhere -in:spam -in:trash "Las Vegas Enginerds"
in:anywhere -in:spam -in:trash LVE (draft OR keeper OR trade OR roster OR unprotected OR cuts OR drops)
in:anywhere -in:spam -in:trash "Las Vegas Enginerds" (draft OR keeper OR trade OR roster OR unprotected OR cuts OR drops)
in:anywhere -in:spam -in:trash (keeper OR keepers OR draft OR trade OR traded OR drop OR drops OR cut OR cuts OR unprotected OR roster OR round OR pick)
```

## Team Queries

```text
in:anywhere -in:spam -in:trash (Niners OR WhoDat OR "Rabid Monkeys" OR "Golden Boy Productions") (draft OR trade OR keeper OR roster)
in:anywhere -in:spam -in:trash ("Dirt Devils" OR "Super Chargers" OR "Mighty Canucks" OR "Rocky Mountain High" OR "Practice Squad" OR "Precise Guesswork") (draft OR trade OR keeper OR roster)
in:anywhere -in:spam -in:trash Niners (draft OR trade OR keeper OR roster OR pick)
in:anywhere -in:spam -in:trash WhoDat (draft OR trade OR keeper OR roster OR pick)
in:anywhere -in:spam -in:trash "Rabid Monkeys" (draft OR trade OR keeper OR roster OR pick)
in:anywhere -in:spam -in:trash "Golden Boy Productions" (draft OR trade OR keeper OR roster OR pick)
in:anywhere -in:spam -in:trash "Dirt Devils" (draft OR trade OR keeper OR roster OR pick)
in:anywhere -in:spam -in:trash "Super Chargers" (draft OR trade OR keeper OR roster OR pick)
in:anywhere -in:spam -in:trash "Mighty Canucks" (draft OR trade OR keeper OR roster OR pick)
in:anywhere -in:spam -in:trash "Rocky Mountain High" (draft OR trade OR keeper OR roster OR pick)
in:anywhere -in:spam -in:trash "Practice Squad" (draft OR trade OR keeper OR roster OR pick)
in:anywhere -in:spam -in:trash "Precise Guesswork" (draft OR trade OR keeper OR roster OR pick)
```

## Review Notes

- Use Gmail search results to identify candidate messages and attachments.
- Read full message bodies only with explicit review intent.
- Normalize actual evidence into CSV rows instead of storing raw email text.
- Treat trade/draft/Gmail evidence as review evidence until promoted by a separate model/backtest lane.
