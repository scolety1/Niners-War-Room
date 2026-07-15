# Player Board Label Contract Review

## Route and implementation

- Primary route: `/rankings`
- Compatibility alias: `/player-board`
- Canonical implementation: `app/pages/20_final_board_v1.py`
- Thin app-shell wrapper inspected by the stale test: `app/pages/05_rankings.py`

`app/navigation.py` maps both the visible Dynasty Rankings route and the Player Board legacy alias to the canonical implementation.

## Label decision

- Stale expected page label: `Player Board`
- Current accepted page label: `Dynasty Rankings`
- Current accepted controls: `Dynasty Review`, `Market Context`, `Data Review`, `Search player`, `Position`, `Player type`, `Sort by`, `Advanced filters`, and `Review needed`

The page-title label is a surface identity, not a model field. The controls map to existing filters/presets only. Changing the application back to the June 5 wording would misstate the accepted current route and could imply that old Model v4 review controls still own the page.

## References

- Navigation: `app/navigation.py`
- Product acceptance: `docs/hq/parallel_lanes/NWR_DYNASTY_RANKINGS_PAGE_LANE_20260623.md`
- Current surface authority: `docs/hq/master/post_rookie_registry_roadmap_reassessment_v1_20260711/CURRENT_SURFACE_STATE_MAP.csv`
- Current page regression contract: `tests/test_dynasty_rankings_page_v1.py`

## Accessibility and responsive behavior

No label or UI markup changed. The repaired test now validates the implementation users actually reach. Live compact and desktop checks show the accurate title and named controls; the accessibility tree exposes names for `View preset`, `Search player`, `Player type`, `Sort by`, and the navigation controls. Root horizontal overflow is absent at both required sizes.

No ranking, data, sorting, filtering, recommendation, source, or freshness behavior changed.

Classification: `STALE_TEST_EXPECTATION`. Confidence: `HIGH`. Unresolved ambiguity: none.
