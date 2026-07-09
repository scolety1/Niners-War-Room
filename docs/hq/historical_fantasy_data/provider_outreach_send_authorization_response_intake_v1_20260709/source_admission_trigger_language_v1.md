# Source Admission Trigger Language V1

## Purpose

This document defines the exact provider response language or evidence required before NWR may open a future route-feed source-admission lane.

## Required Positive Language

A provider response may trigger source-admission review only if it clearly says all of the following, or provides equivalent contract language:

- The provider can supply actual player-level `routes_run`.
- WR, TE, and RB coverage is included, or omissions are explicitly documented.
- The feed can be used by NWR for internal historical fantasy research.
- NWR may store the feed internally under defined terms.
- NWR may compute derived internal metrics such as YPRR and TPRR under defined terms.
- A supported retrieval path exists, such as API, export, static file delivery, data room, or signed storage.
- Stable player identity fields are provided.
- Field dictionary and row-grain documentation are available.
- Historical coverage and missingness documentation are available.
- Provenance, checksum, schema version, or update timestamp support is available.

## Acceptable Trigger Phrases

Examples of language that may justify a source-admission lane:

- "We can license a routes-run feed for internal research use."
- "The feed includes player-level routes run for WR, TE, and RB."
- "The feed includes stable player identifiers and a field dictionary."
- "NWR may store the data internally and calculate derived metrics."
- "We provide a supported API/export with historical seasons and update timestamps."

## Insufficient Language

These are not enough:

- "The data is visible on our website."
- "You can look at the public page."
- "You may use it for personal reference."
- "We have route data, but no export."
- "You can copy it manually."
- "Names and teams are included."
- "We can send a sample spreadsheet" without terms.
- "No redistribution" without internal storage and derived-use rights.

## Red-Flag Language

These should keep the source blocked:

- "No scraping or automated use."
- "No data extraction or database creation."
- "No model, training, or derived metric use."
- "No storage or retention."
- "No export or API is available."
- "Routes are available only in the user interface."
- "Player names are the only identifier."
- "RB routes are not supported."

## Trigger Result

Even if trigger language is present, source status remains not admitted. The correct next action is a separate route-feed source-admission lane that verifies:

- permission
- reproducibility
- identity safety
- coverage
- missingness
- provenance
- row grain
- allowed use

True routes/YPRR/TPRR remain blocked until that later admission lane passes.
