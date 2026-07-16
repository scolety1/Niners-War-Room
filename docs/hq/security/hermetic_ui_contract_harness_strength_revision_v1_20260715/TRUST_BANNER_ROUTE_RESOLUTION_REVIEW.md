# Trust Banner Route Resolution Review

## Governed route types

The test resolves every route through `ALL_NAVIGATION_PAGES` before reading its
source.

- Decision Trust Strip: `/rankings`, `/player-board`, `/player-compare`, and
  `/trading-lab`.
- Legacy component banner: `/my-team`, `/war-board`, `/trade-lab`,
  `/league-targets`, and `/model-lab`.
- Legacy constant banner: `/legacy-decision-board`.
- Draft Prep scouting/legal-pool gate: `/legacy-draft-room`.

Each Decision Trust Strip route requires one exact structural call and its
route-specific heading. Each legacy component route requires one exact legacy
call. The legacy Decision Board requires its imported review-only constant in
one `st.warning` call. Draft Prep requires its gate in the routed `st.markdown`
call and planning-only text in the routed `st.info` call.

## Wrong-wrapper sensitivity

An injected `/rankings` route to the real bannerless app-shell wrapper fails.
An injected wrapper source containing only `render_page_trust_banner(...)` also
fails the Decision Trust Strip contract. A valid Decision Trust Strip call in
`/player-compare` cannot satisfy a broken `/rankings` source.

Result: route selection is live-registry-derived and fail-closed; no fixed
implementation file can mask a wrong route target.
