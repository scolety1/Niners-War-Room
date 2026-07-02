# Sample Export Request Email

To: `info@trumedianetworks.com`

Subject: NFL Advanced Analytics / API sample export request for private source evaluation

Dear TruMedia team,

I am evaluating whether TruMedia can serve as a rights-cleared NFL source for a private football research workflow. I am not seeking public redistribution, a consumer-facing product, or immediate production integration. The first goal is source admission: confirm rights, schema, coverage, zero/missing semantics, and whether the data can be used for private fantasy/dynasty formula research.

Could you advise whether the right product path is NFL Advanced Analytics, NFL API, a data warehouse export, or a partner export?

For an initial evaluation, I would prefer a vendor-generated sample export rather than API credentials. The most useful sample would include:

- Player identifiers: GSIS ID, PFF ID if available, TruMedia player ID if applicable, player name, team, position.
- Season/week/game/play identifiers.
- Routes run and route type if available.
- Targets, receptions if available, receiving yards, air yards/depth, and yards after catch.
- Alignment: wide, slot, backfield, in-line, or your available alignment taxonomy.
- Snap participation and route participation.
- Coverage type, defender/matchup fields, and coverage/matchup IDs if available.
- Separation or other tracking-derived fields if available.
- Red-zone, inside-10, and inside-5 context.
- Explicit zero/missing semantics for every requested field.
- Export timestamp, as-of/correction timestamp if available, schema version, and data license/use note.

Requested grains:

- Player-week receiving/route usage for recent regular seasons, ideally 2024 and 2025.
- Player-game receiving/route usage for the same period if available.
- Player-play route/target/coverage/tracking rows for a small representative game sample.
- Identity crosswalk and schema/data dictionary.

Rights questions:

- May the sample export be stored locally for private evaluation?
- May compact schema, source-admission receipts, and aggregate coverage matrices be stored in a private repository?
- May derived artifacts be used for private fantasy/dynasty formula research, with no public redistribution?
- Which fields are TruMedia-owned versus third-party licensed, and which fields are not exportable?
- Can GSIS/PFF IDs be included, and is any Sleeper ID crosswalk available or permitted through local joining?
- If API access is necessary later, are credentials provided by TruMedia, and what handling/rotation requirements apply?

I will not attempt to access any TruMedia systems, create API keys, or use credentials unless TruMedia approves an evaluation path in writing. If a call is easier, I am happy to schedule a demo or product-fit discussion.

Thank you,

NWR source evaluation

