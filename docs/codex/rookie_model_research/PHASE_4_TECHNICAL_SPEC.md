# Niners Dynasty War Room Phase 4 Technical Specification

This Phase 4 spec turns the prior rookie-indicator research, audit thinking, and scoring formulas into an implementation contract for a fully local-first build. The technical stack implied by your requirements is a good fit for RFC-4180-style CSV fixtures, Python stdlib CSV I/O, typed dataclasses for row-level validation, `pytest` fixtures plus parametrized regression tests, and a table-first app in entity["company","Streamlit","python app framework"] using interactive dataframes, editable override tables, column configuration, row selection, and link columns. citeturn4search0turn3search0turn0search2turn0search3turn0search15turn5search1turn5search6turn1search1turn5search9turn1search14

This specification assumes the league rules and football conclusions from Phases 1–3 are already accepted as your model-policy layer. What follows is the implementation layer: file shapes, registry metadata, formulas, fixtures, UI contracts, validation rules, and migration order.

## CSV Schemas

All CSVs should be UTF-8, comma-delimited, headered, and compatible with the common CSV conventions documented in RFC 4180 by the entity["organization","IETF","internet standards body"]. Python’s `csv` module supports dictionary-shaped row I/O and recommends opening files with `newline=''`, which is the right default for deterministic local fixture loading and export. citeturn4search0turn3search0

### Global CSV conventions

| item | value |
|---|---|
| encoding | `utf-8` |
| delimiter | `,` |
| header row | required |
| quoting | RFC-4180 compatible; quote fields containing commas, quotes, or newlines |
| booleans | lowercase `true` / `false` |
| missing values | empty string, never literal `NULL` |
| score precision | store as decimal with up to 1 decimal place in CSV; keep full float precision in memory |
| multi-value fields | pipe-delimited slugs, sorted lexicographically |
| date format | `YYYY-MM-DD` |
| datetime format | ISO 8601 UTC or local-offset timestamp |

### `rookie_prospect_inputs.csv`

One row per rookie prospect. This file stores identity, stable biographical fields, and pre-normalization metadata that is not naturally expressed as long-form feature rows.

| column name | type | required/optional | allowed values or enum | description | example value | validation rule |
|---|---|---|---|---|---|---|
| season | int | required | `2000-2100` | season of the rookie board | `2026` | must be integer; same season used across all related files |
| prospect_id | string | required | slug | stable local primary key | `tet_mc_millan_wr_2025` | regex `^[a-z0-9_]+$`; unique within season |
| player_name | string | required | free text | display name | `Tetairoa McMillan` | non-empty |
| position | enum | required | `QB`, `RB`, `WR`, `TE` | model position | `WR` | must match feature rows and output rows |
| school | string | optional | free text | college program | `Arizona` | blank allowed |
| nfl_team | string | optional | team code or blank | post-draft NFL team | `CAR` | blank allowed pre-draft; if `draft_status=post_draft`, not blank |
| draft_status | enum | required | `pre_draft`, `post_draft`, `undrafted` | whether draft context exists | `post_draft` | governs whether draft/team fields may be blank |
| draft_round | int | optional | `1-7` or blank | NFL draft round | `1` | blank only if `pre_draft` or `undrafted` |
| draft_pick | int | optional | `1-300` or blank | overall NFL draft pick | `8` | blank only if `pre_draft`; if populated, round must also be populated |
| age_on_sept_1 | float | required | `18.0-26.0` | age anchor for age trajectory normalization | `21.4` | must be numeric in range |
| early_declare_status | enum | required | `early`, `senior`, `graduate`, `unknown` | early declare metadata | `early` | non-empty enum |
| height_in | float | optional | `65-82` | height in inches | `76.0` | blank allowed; numeric if present |
| weight_lb | float | optional | `170-285` | weight in pounds | `219.0` | blank allowed; numeric if present |
| bmi | float | optional | `20-40` | convenience field; can be derived | `26.6` | if blank and height+weight present, derive in code |
| forty_time | float | optional | `4.20-5.40` | combine/pro day forty | `4.48` | numeric if present |
| ras | float | optional | `0.0-10.0` | Relative Athletic Score or local equivalent | `9.71` | numeric if present |
| film_grade | float | optional | `0.0-100.0` | manual film rubric output | `82.0` | must be normalized if present |
| injury_durability_score | float | optional | `0.0-100.0` | normalized durability input | `78.0` | must be normalized if present |
| data_quality_tier | enum | required | `verified`, `partial`, `estimated`, `hand_entered` | provenance quality marker | `verified` | non-empty enum |

### `rookie_feature_registry.csv`

One row per supported feature definition. This file is metadata, not player data. It tells validators and the UI what a feature is, how it behaves, and whether it should affect scoring.

| column name | type | required/optional | allowed values or enum | description | example value | validation rule |
|---|---|---|---|---|---|---|
| position | enum | required | `QB`, `RB`, `WR`, `TE` | position namespace for feature | `WR` | unique with `feature_name` |
| feature_name | string | required | slug | stable code-friendly feature key | `target_earning` | regex `^[a-z0-9_]+$`; unique within position |
| feature_category | enum | required | `core`, `secondary`, `post_draft`, `league_overlay`, `confidence_modifier`, `risk_flag`, `upside_flag`, `floor_flag`, `display_only`, `rejected` | feature role | `core` | non-empty enum |
| parent_score_component | enum | required | `main_prospect_score`, `league_fit_score`, `rookie_opportunity_score`, `long_term_dynasty_score`, `trade_insulation_score`, `display_only` | primary home component | `main_prospect_score` | non-empty enum |
| evidence_strength | enum | required | `high`, `medium`, `low`, `speculative` | carried forward from Phases 1–3 | `high` | non-empty enum |
| expected_direction | enum | required | `higher_better`, `lower_better_after_transform`, `contextual_overlay`, `display_only` | how normalized value should be interpreted | `higher_better` | non-empty enum |
| default_weight | float | required | `0.0-100.0` | default registry weight | `22.0` | `min_weight <= default_weight <= max_weight` |
| min_weight | float | required | `0.0-100.0` | lower bound for tuning | `16.0` | `min_weight <= max_weight` |
| max_weight | float | required | `0.0-100.0` | upper bound for tuning | `28.0` | `max_weight >= min_weight` |
| missing_data_penalty | float | required | `0.0-10.0` | feature-specific missing-data severity | `6.0` | display-only/rejected rows should usually be `0.0` |
| is_core_feature | bool | required | `true`, `false` | whether absence materially harms model certainty | `true` | if `true`, category cannot be `display_only` or `rejected` |
| is_league_overlay | bool | required | `true`, `false` | whether feature exists because of LVE scoring/roster context | `false` | if `true`, weight should not feed `main_prospect_score` |
| is_post_draft_feature | bool | required | `true`, `false` | whether feature requires NFL-team context | `false` | if `true`, blank values are valid pre-draft |
| is_rejected_or_display_only | bool | required | `true`, `false` | whether feature must not affect score directly | `false` | if `true`, `default_weight` should be `0.0` |
| implementation_notes | string | required | free text | execution notes for code and UI | `Reuse in trade score; never let this alter main score through landing spot.` | non-empty |

### `rookie_feature_scores.csv`

One row per `season + prospect_id + feature_name`. This is the main long-form scoring input file. It should be the primary source for the huge audit table.

| column name | type | required/optional | allowed values or enum | description | example value | validation rule |
|---|---|---|---|---|---|---|
| season | int | required | `2000-2100` | season key | `2026` | FK-compatible with prospect inputs |
| prospect_id | string | required | slug | prospect foreign key | `tet_mc_millan_wr_2025` | must exist in `rookie_prospect_inputs.csv` |
| position | enum | required | `QB`, `RB`, `WR`, `TE` | copied for convenience | `WR` | must equal prospect position |
| feature_name | string | required | slug | feature foreign key | `target_earning` | must exist in registry for same position |
| raw_value_text | string | optional | free text | unparsed or human-readable source value | `31.4 percent target share` | blank allowed |
| raw_value_numeric | float | optional | free numeric | numeric raw value before normalization | `31.4` | blank allowed |
| raw_unit | enum | optional | `score`, `percent`, `years`, `pick`, `yards`, `rate`, `boolean`, `text`, `index`, `none` | raw value unit | `percent` | blank allowed if no raw value |
| normalized_score | float | optional | `0.0-100.0` | normalized scoring input | `92.0` | required if feature is scored; blank allowed only for display-only/rejected rows |
| source_summary | string | required | free text | concise provenance description | `manual normalization from 2026 pre-draft workbook` | non-empty |
| citation_links | string | optional | pipe-delimited source keys | local source keys or resolvable link keys | `wr_research_phase1|source_catalog_wr_01` | regex `^[a-z0-9_]+(\|[a-z0-9_]+)*$` or blank |
| source_confidence | enum | required | `verified`, `derived`, `manual`, `handwritten`, `estimated` | confidence in this row’s provenance | `verified` | non-empty enum |
| is_missing | bool | required | `true`, `false` | whether value is intentionally missing | `false` | if `true`, `normalized_score` may be blank and `missing_reason` should be filled |
| missing_reason | string | optional | free text | reason for missing or neutralized input | `pre_draft_unavailable` | required when `is_missing=true` |
| is_user_override | bool | required | `true`, `false` | whether user manually overrode this feature | `false` | if `true`, `override_reason` required |
| override_reason | string | optional | free text | explanation for manual adjustment | `handwritten notes suggest earlier route role than source file` | required when `is_user_override=true` |
| updated_at | datetime | required | ISO 8601 | last modification timestamp | `2026-05-05T20:14:00-06:00` | valid ISO timestamp |
| unique_key | string | optional | derived slug | optional baked key for external tools | `2026|tet_mc_millan_wr_2025|target_earning` | if present, must be unique |

### `rookie_model_outputs.csv`

One row per computed prospect per model version. This file is the compact board source.

#### Identity and metadata columns

| column name | type | required/optional | allowed values or enum | description | example value | validation rule |
|---|---|---|---|---|---|---|
| season | int | required | `2000-2100` | season key | `2026` | required |
| model_version | string | required | semantic-ish version string | scoring version | `lve_v4_0_0` | regex `^[a-z0-9_\.]+$` |
| board_rank | int | required | `1-1000` | final deterministic rank | `3` | unique within `season + model_version` |
| prospect_id | string | required | slug | FK to prospect | `tet_mc_millan_wr_2025` | must exist in prospect inputs |
| player_name | string | required | free text | display name | `Tetairoa McMillan` | non-empty |
| position | enum | required | `QB`, `RB`, `WR`, `TE` | display position | `WR` | must match prospect inputs |
| nfl_team | string | optional | team code or blank | current NFL team | `CAR` | may be blank pre-draft |
| veteran_benchmark_id | string | optional | slug | chosen comparison benchmark | `wr_best_available_release_2026_01` | blank allowed pre-benchmark |
| computed_at | datetime | required | ISO 8601 | score snapshot timestamp | `2026-05-05T20:30:00-06:00` | valid ISO timestamp |

#### Score, flag, and recommendation columns

| column name | type | required/optional | allowed values or enum | description | example value | validation rule |
|---|---|---|---|---|---|---|
| main_prospect_score | float | required | `0.0-100.0` | core talent score | `89.8` | bounds check |
| league_fit_score | float | required | `0.0-100.0` | LVE scoring/roster adjustment score | `87.6` | bounds check |
| rookie_opportunity_score | float | required | `0.0-100.0` | post-draft rookie-year path score | `83.6` | bounds check |
| long_term_dynasty_score | float | required | `0.0-100.0` | long-run keeper value score | `89.1` | bounds check |
| trade_insulation_score | float | required | `0.0-100.0` | market insulation score | `89.6` | bounds check |
| veteran_benchmark_score | float | optional | `0.0-100.0` | selected benchmark’s score | `72.0` | blank allowed if no benchmark layer loaded |
| veteran_opportunity_adjustment | float | required | `-20.0 to 10.0` | signed veteran comparison adjustment | `5.0` | must respect per-position cap |
| missing_data_penalty | float | required | `0.0-15.0` | signed subtraction magnitude | `0.0` | non-negative |
| confidence_score | float | required | `0.0-100.0` | data coverage/provenance score | `91.0` | bounds check |
| pre_gate_score | float | required | `0.0-100.0` | weighted sum before gate | `88.6` | bounds check |
| gate_adjustment | float | required | `-25.0 to 5.0` | structural gate adjustment | `0.0` | must follow QB/TE gate rules |
| position_gate_status | enum | required | `none`, `qb_elite_exempt`, `qb_structural_penalty`, `qb_low_capital_penalty`, `te_elite_exempt`, `te_structural_penalty`, `te_day3_penalty` | audit-friendly gate label | `none` | non-empty enum |
| final_decision_score | float | required | `0.0-100.0` | final board score | `93.6` | bounds check |
| recommended_range | string | required | round-pick range string | suggested pick window | `1.01-1.03` | regex `^[1-5]\.(0[1-9]|10)-((([1-5]\.(0[1-9]|10))|UDFA))$` |
| do_not_draft_before_pick | int | required | `1-50` | earliest acceptable pick | `1` | integer bounds check |
| risk_flags | string | optional | pipe-delimited slugs | risk markers | `weak_target_earning|veteran_opportunity_drag` | sorted unique slugs or blank |
| upside_flags | string | optional | pipe-delimited slugs | upside markers | `alpha_target_earner|beats_veteran_market` | sorted unique slugs or blank |
| floor_flags | string | optional | pipe-delimited slugs | floor markers | `day1_or_day2_capital|trade_insulation` | sorted unique slugs or blank |
| short_explanation | string | required | free text | deterministic summary string | `Elite target earning, strong route path, no veteran drag.` | non-empty |

### `veteran_opportunity_benchmarks.csv`

One row per released veteran, free agent, or local benchmark row considered in rookie opportunity cost. Because your draft happens after roster declaration, this file should be refreshed after official releases and before the offline draft.

| column name | type | required/optional | allowed values or enum | description | example value | validation rule |
|---|---|---|---|---|---|---|
| season | int | required | `2000-2100` | season key | `2026` | required |
| benchmark_id | string | required | slug | primary key | `wr_best_available_release_2026_01` | regex `^[a-z0-9_]+$`; unique within season |
| asset_name | string | required | free text | veteran or free-agent name | `Veteran WR Example` | non-empty |
| asset_type | enum | required | `released_veteran`, `free_agent`, `benchmark_only` | source of opportunity benchmark | `released_veteran` | non-empty enum |
| benchmark_scope | enum | required | `same_position`, `flex_pool`, `league_global` | comparison bucket | `same_position` | non-empty enum |
| position | enum | required | `QB`, `RB`, `WR`, `TE` | position | `WR` | required |
| nfl_team | string | optional | team code, `FA`, or blank | current affiliation | `FA` | blank allowed |
| availability_status | enum | required | `available`, `possibly_available`, `protected`, `uncertain` | roster declaration result | `available` | non-empty enum |
| role_tier | enum | required | `starter`, `committee`, `depth`, `stash` | expected role | `starter` | non-empty enum |
| benchmark_score | float | required | `0.0-100.0` | score used for veteran comparison | `72.0` | bounds check |
| win_now_score | float | required | `0.0-100.0` | immediate-season utility | `78.0` | bounds check |
| hold_value_score | float | required | `0.0-100.0` | short-to-medium hold value | `64.0` | bounds check |
| trade_liquidity_score | float | required | `0.0-100.0` | likely tradability | `61.0` | bounds check |
| recommended_pick_equivalent | int | optional | `1-50` or blank | rough rookie-pick equivalent | `24` | numeric if present |
| source_summary | string | required | free text | provenance summary | `post-roster-declaration local benchmark sheet` | non-empty |
| citation_links | string | optional | pipe-delimited source keys | local source keys | `release_sheet_2026|benchmark_notes_01` | regex key list or blank |
| is_active_benchmark | bool | required | `true`, `false` | whether row is active in current run | `true` | non-empty |
| notes | string | optional | free text | optional benchmark commentary | `Use for WR same-position comparison only.` | blank allowed |

### `rookie_audit_notes.csv`

One row per note. This is the provenance and manual-review file. It is where handwritten league records, scouting interpretations, override explanations, and validation comments should live.

| column name | type | required/optional | allowed values or enum | description | example value | validation rule |
|---|---|---|---|---|---|---|
| season | int | required | `2000-2100` | season key | `2026` | required |
| note_id | string | required | slug | note primary key | `note_wr_tet_mc_millan_target_earning_01` | regex `^[a-z0-9_]+$`; unique within season |
| prospect_id | string | optional | slug or blank | prospect foreign key | `tet_mc_millan_wr_2025` | blank allowed for league-level notes |
| position | enum | optional | `QB`, `RB`, `WR`, `TE` or blank | position scope | `WR` | if `prospect_id` present, should match prospect |
| feature_name | string | optional | slug or blank | feature-specific note scope | `target_earning` | blank allowed |
| note_scope | enum | required | `league_context`, `prospect`, `feature`, `component`, `benchmark`, `override`, `validation` | note grouping | `feature` | non-empty enum |
| note_type | enum | required | `source`, `scouting`, `handwritten_history`, `override_reason`, `validation_warning`, `normalization_note`, `league_rule` | note subtype | `override_reason` | non-empty enum |
| note_text | string | required | free text | full note body | `Local handwritten record suggests stronger outside route role than imported sheet.` | non-empty |
| source_summary | string | optional | free text | concise provenance line | `commissioner notebook transcription` | blank allowed |
| citation_links | string | optional | pipe-delimited source keys | local source keys | `scan_2025_notebook_p03` | regex key list or blank |
| provenance | enum | required | `manual`, `research_phase`, `imported_csv`, `handwritten_record`, `commissioner_rule` | provenance class | `handwritten_record` | non-empty enum |
| author | string | required | free text | note author or reviewer | `lsmith` | non-empty |
| affects_score | bool | required | `true`, `false` | whether note drives an actual override | `true` | if `true`, override fields required |
| override_target | string | optional | slug or blank | field affected by override | `normalized_score` | required if `affects_score=true` |
| override_value | string | optional | free text | override payload | `78.0` | required if `affects_score=true` |
| created_at | datetime | required | ISO 8601 | creation timestamp | `2026-05-05T19:25:00-06:00` | valid ISO timestamp |

## Feature Registry

Treat the registry as model metadata, not as the only formula source of truth. The exact component formulas in the next section are authoritative for scoring. The registry’s `default_weight` is the feature’s primary “home” weight for UI, validation severity, and human audit context. Features marked display-only or rejected stay in the audit table but contribute `0` to scoring.

### QB feature registry

| position | feature_name | feature_category | parent_score_component | evidence_strength | expected_direction | default_weight | min_weight | max_weight | missing_data_penalty | is_core_feature | is_league_overlay | is_post_draft_feature | is_rejected_or_display_only | implementation_notes |
|---|---|---|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| QB | draft_capital | core | main_prospect_score | high | higher_better | 26 | 20 | 32 | 7 | true | false | false | false | Reuse in long-term and trade formulas; never let landing spot mutate this score. |
| QB | passing_efficiency | core | main_prospect_score | high | higher_better | 24 | 18 | 30 | 6 | true | false | false | false | Composite of AYA/attempt efficiency and stability metrics. |
| QB | rushing_profile | core | main_prospect_score | high | higher_better | 18 | 12 | 24 | 6 | true | true | false | false | Key LVE overlay because 1QB plus 3-point pass TD boosts dual-threat separation. |
| QB | sack_avoidance | secondary | main_prospect_score | medium | higher_better | 12 | 8 | 18 | 4 | true | false | false | false | Normalize so lower pressure-to-sack becomes higher score. |
| QB | accuracy_decision | secondary | main_prospect_score | medium | higher_better | 12 | 8 | 18 | 4 | true | false | false | false | Should capture accuracy plus turnover-worthy-play avoidance. |
| QB | age_trajectory | secondary | long_term_dynasty_score | medium | higher_better | 8 | 4 | 12 | 3 | false | false | false | false | Younger, earlier, faster-development profiles score better. |
| QB | starting_path | post_draft | rookie_opportunity_score | medium | higher_better | 50 | 35 | 60 | 5 | true | false | true | false | Post-draft opening-year path; use neutral 50 pre-draft. |
| QB | team_environment | post_draft | rookie_opportunity_score | medium | higher_better | 30 | 20 | 40 | 3 | false | true | true | false | Decompose landing spot into OL/coaching/weapons; do not use raw “good landing spot” labels. |
| QB | developmental_stability | secondary | long_term_dynasty_score | low | higher_better | 10 | 4 | 16 | 2 | false | false | true | false | Multi-year starter runway and organizational stability. |
| QB | injury_durability | risk_flag | long_term_dynasty_score | medium | higher_better | 5 | 0 | 10 | 2 | false | false | false | false | Use as floor/risk input, never as dominant core driver. |
| QB | film_grade | display_only | display_only | medium | display_only | 0 | 0 | 5 | 0 | false | false | false | true | Tiebreaker and disagreement detector only. |
| QB | competition_adjustment | confidence_modifier | display_only | low | contextual_overlay | 0 | 0 | 5 | 0 | false | false | false | true | Display/context only unless you later add explicit normalization tables. |
| QB | landing_spot_overlay | league_overlay | display_only | low | contextual_overlay | 0 | 0 | 8 | 0 | false | true | true | true | Show in UI, but scoring must flow through starting_path/team_environment instead. |
| QB | return_game_value | rejected | display_only | speculative | display_only | 0 | 0 | 0 | 0 | false | false | true | true | Ignore for QB scoring. |

### RB feature registry

| position | feature_name | feature_category | parent_score_component | evidence_strength | expected_direction | default_weight | min_weight | max_weight | missing_data_penalty | is_core_feature | is_league_overlay | is_post_draft_feature | is_rejected_or_display_only | implementation_notes |
|---|---|---|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| RB | draft_capital | core | main_prospect_score | high | higher_better | 28 | 22 | 34 | 7 | true | false | false | false | Core prior for hit rate, role access, and trade insulation. |
| RB | workload_earning | core | main_prospect_score | high | higher_better | 22 | 16 | 28 | 6 | true | false | false | false | Must reflect carries, route participation, target earning, and touch share. |
| RB | rush_efficiency | core | main_prospect_score | medium | higher_better | 18 | 12 | 24 | 5 | true | false | false | false | Use efficiency that is resilient to environment, not raw yards only. |
| RB | receiving_impact | secondary | main_prospect_score | medium | higher_better | 12 | 6 | 18 | 4 | true | false | false | false | Important, but clearly de-weighted versus PPR formats. |
| RB | age_trajectory | secondary | long_term_dynasty_score | medium | higher_better | 10 | 4 | 14 | 3 | false | false | false | false | Younger and earlier-declare profiles score better. |
| RB | goal_line_power | core | league_fit_score | medium | higher_better | 20 | 12 | 28 | 4 | true | true | false | false | LVE-specific plus because receptions alone do less work here. |
| RB | chain_moving | core | league_fit_score | medium | higher_better | 30 | 20 | 36 | 5 | true | true | false | false | First-down rate, success rate, short-yardage conversion, and stay-on-field value. |
| RB | athleticism | secondary | long_term_dynasty_score | medium | higher_better | 10 | 4 | 16 | 2 | false | false | false | false | Keep below capital and workload inputs. |
| RB | projected_touch_path | post_draft | rookie_opportunity_score | medium | higher_better | 40 | 28 | 48 | 5 | true | false | true | false | Post-draft touch path; default to 50 before draft. |
| RB | offensive_line_environment | post_draft | rookie_opportunity_score | low | higher_better | 25 | 15 | 32 | 2 | false | true | true | false | Important but should remain overlay, not talent proxy. |
| RB | injury_durability | risk_flag | long_term_dynasty_score | medium | higher_better | 5 | 0 | 10 | 2 | false | false | false | false | Floor/risk input only. |
| RB | film_grade | display_only | display_only | medium | display_only | 0 | 0 | 5 | 0 | false | false | false | true | Use only as tiebreaker or disagreement detector. |
| RB | competition_adjustment | confidence_modifier | display_only | low | contextual_overlay | 0 | 0 | 5 | 0 | false | false | false | true | Conference/context display only by default. |
| RB | landing_spot_overlay | league_overlay | display_only | low | contextual_overlay | 0 | 0 | 8 | 0 | false | true | true | true | Decompose into touch path and OL instead of raw score. |
| RB | return_game_value | upside_flag | display_only | low | contextual_overlay | 0 | 0 | 3 | 0 | false | true | true | true | Surface as upside note only because return scoring exists but should not reshape core profiles. |

### WR feature registry

| position | feature_name | feature_category | parent_score_component | evidence_strength | expected_direction | default_weight | min_weight | max_weight | missing_data_penalty | is_core_feature | is_league_overlay | is_post_draft_feature | is_rejected_or_display_only | implementation_notes |
|---|---|---|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| WR | draft_capital | core | main_prospect_score | high | higher_better | 24 | 18 | 30 | 7 | true | false | false | false | Core prior and trade insulation anchor. |
| WR | target_earning | core | main_prospect_score | high | higher_better | 22 | 16 | 28 | 6 | true | false | false | false | Includes target share and targets per route run logic. |
| WR | efficiency_dominance | core | main_prospect_score | high | higher_better | 22 | 16 | 28 | 6 | true | false | false | false | Should capture YPRR, YPTPA, and market-share dominance. |
| WR | age_trajectory | secondary | long_term_dynasty_score | medium | higher_better | 12 | 6 | 18 | 4 | true | false | false | false | Breakout age and age-adjusted production live here. |
| WR | role_robustness | secondary | league_fit_score | medium | higher_better | 10 | 4 | 16 | 3 | false | true | false | false | Outside/slot flexibility, route-tree robustness, and non-gimmick role value. |
| WR | chain_moving | core | league_fit_score | medium | higher_better | 10 | 4 | 16 | 4 | true | true | false | false | LVE-specific boost because first downs and weekly startable volume matter. |
| WR | athleticism | secondary | trade_insulation_score | low | higher_better | 10 | 0 | 16 | 2 | false | false | false | false | Keep below earning and efficiency. |
| WR | projected_route_share | post_draft | rookie_opportunity_score | medium | higher_better | 40 | 28 | 48 | 5 | true | false | true | false | Route path matters more than vague landing-spot sentiment. |
| WR | quarterback_environment | post_draft | rookie_opportunity_score | low | higher_better | 25 | 15 | 32 | 2 | false | true | true | false | Overlay only; do not let it drown out talent. |
| WR | injury_durability | risk_flag | long_term_dynasty_score | medium | higher_better | 10 | 0 | 14 | 2 | false | false | false | false | Floor/risk only. |
| WR | film_quality | display_only | display_only | medium | display_only | 0 | 0 | 5 | 0 | false | false | false | true | Tiebreaker and disagreement detector. |
| WR | competition_adjustment | confidence_modifier | display_only | low | contextual_overlay | 0 | 0 | 5 | 0 | false | false | false | true | No direct score effect in v1. |
| WR | landing_spot_overlay | league_overlay | display_only | low | contextual_overlay | 0 | 0 | 8 | 0 | false | true | true | true | Show only through explanation layer. |
| WR | return_game_value | upside_flag | display_only | low | contextual_overlay | 0 | 0 | 3 | 0 | false | true | true | true | Useful as tie-breaker/upside note, not core rank driver. |

### TE feature registry

| position | feature_name | feature_category | parent_score_component | evidence_strength | expected_direction | default_weight | min_weight | max_weight | missing_data_penalty | is_core_feature | is_league_overlay | is_post_draft_feature | is_rejected_or_display_only | implementation_notes |
|---|---|---|---|---|---|---:|---:|---:|---:|---|---|---|---|---|
| TE | draft_capital | core | main_prospect_score | high | higher_better | 28 | 22 | 34 | 7 | true | false | false | false | Critical because no TE premium means weak-capital TE bets should be strongly discounted. |
| TE | receiving_efficiency | core | main_prospect_score | medium | higher_better | 22 | 16 | 28 | 6 | true | false | false | false | YPRR-style receiving efficiency is more important than raw catches alone. |
| TE | production_volume | secondary | main_prospect_score | medium | higher_better | 16 | 10 | 22 | 4 | true | false | false | false | Market share and volume still matter, but less than route/receiving quality. |
| TE | route_role | core | league_fit_score | medium | higher_better | 16 | 10 | 24 | 5 | true | true | false | false | Route participation and receiver-like deployment are essential in non-premium TE scoring. |
| TE | age_trajectory | secondary | long_term_dynasty_score | medium | higher_better | 8 | 4 | 12 | 3 | false | false | false | false | Younger developmental profiles score better. |
| TE | athletic_size | secondary | long_term_dynasty_score | medium | higher_better | 10 | 4 | 16 | 3 | false | false | false | false | Helpful when paired with route role and capital, not enough by itself. |
| TE | projected_route_share | post_draft | rookie_opportunity_score | medium | higher_better | 45 | 30 | 55 | 5 | true | false | true | false | Must be the main post-draft TE opportunity input. |
| TE | quarterback_environment | post_draft | rookie_opportunity_score | low | higher_better | 25 | 15 | 32 | 2 | false | true | true | false | Overlay only. |
| TE | blocking_dependency_risk | risk_flag | display_only | medium | lower_better_after_transform | 0 | 0 | 5 | 0 | false | false | true | true | Use as risk flag; do not give it direct positive weight. |
| TE | injury_durability | risk_flag | long_term_dynasty_score | medium | higher_better | 5 | 0 | 10 | 2 | false | false | false | false | Floor/risk input only. |
| TE | film_grade | display_only | display_only | medium | display_only | 0 | 0 | 5 | 0 | false | false | false | true | Tiebreaker only unless you later formalize TE film subgrades. |
| TE | competition_adjustment | confidence_modifier | display_only | low | contextual_overlay | 0 | 0 | 5 | 0 | false | false | false | true | Context display only. |
| TE | landing_spot_overlay | league_overlay | display_only | low | contextual_overlay | 0 | 0 | 8 | 0 | false | true | true | true | Do not score raw “good landing spot” beliefs directly. |
| TE | return_game_value | rejected | display_only | speculative | display_only | 0 | 0 | 0 | 0 | false | true | true | true | Ignore in TE scoring. |

## Formula Specification

All formula inputs are normalized `0-100`. Raw statistical normalization belongs upstream in local lookup tables or manually curated transforms. The scoring engine should never directly normalize raw yards, shares, or times during the final board pass. It should only consume already-normalized feature inputs from `rookie_feature_scores.csv`.

The league-specific changes from generic dynasty models are deliberate:

- QB is structurally pushed down because this is 1QB and passing TDs are only 3 points.
- TE is structurally pushed down because there is no TE premium.
- RB and WR league-fit scores emphasize chain moving, staying on the field, and goal-line or meaningful-touch roles.
- Pure reception volume matters less than in PPR.
- Landing spot is not a core talent signal; it only enters through post-draft opportunity and environment overlays.
- Released veterans and free agents matter because the rookie draft occurs after roster declaration, so rookie scores must be compared to current veteran alternatives.

### Helpers and global pipeline

```text
CONSTANT FINAL_WEIGHTS = {
  main_prospect_score: 0.52,
  league_fit_score: 0.10,
  rookie_opportunity_score: 0.14,
  long_term_dynasty_score: 0.14,
  trade_insulation_score: 0.10
}

CONSTANT EVIDENCE_TO_SCORE = {
  high: 100,
  medium: 75,
  low: 55,
  speculative: 35
}

CONSTANT SOURCE_TO_SCORE = {
  verified: 100,
  derived: 90,
  manual: 80,
  handwritten: 65,
  estimated: 50
}

CONSTANT VETERAN_CAPS = {
  QB: {neg: -14, pos: 3},
  RB: {neg: -10, pos: 5},
  WR: {neg: -10, pos: 5},
  TE: {neg: -12, pos: 3}
}

CONSTANT MISSING_CAPS = {
  QB: 10,
  RB: 8,
  WR: 8,
  TE: 10
}

function clamp(value, minValue = 0, maxValue = 100):
  if value < minValue: return minValue
  if value > maxValue: return maxValue
  return value

function weightedAverage(items):
  # items = [{score: 0-100, weight: number}, ...]
  numerator = 0
  denominator = 0
  for item in items:
    numerator += clamp(item.score) * item.weight
    denominator += item.weight
  if denominator == 0:
    return 50
  return clamp(numerator / denominator)

function getFeatureScore(prospectId, position, featureName):
  row = lookup rookies_feature_scores by (prospectId, featureName)
  if row does not exist or row.is_missing == true:
    return 50
  return clamp(row.normalized_score)

function missingDataPenalty(prospectId, position):
  total = 0
  for each scored feature row used by formulas:
    if row missing or row.is_missing == true:
      total += registry.missing_data_penalty
  penalty = total * 0.35
  return clamp(penalty, 0, MISSING_CAPS[position])

function confidenceScore(prospectId, position, dataCoreScore, filmGradeOptional):
  totalWeight = sum(default_weight for all scored features in registry for position)
  presentWeight = sum(default_weight where feature row exists and is_missing == false)
  coverageScore = 100 * presentWeight / totalWeight

  evidenceScore = weightedAverage(
    for each scored registry feature:
      {score: EVIDENCE_TO_SCORE[registry.evidence_strength], weight: registry.default_weight}
  )

  sourceScore = weightedAverage(
    for each scored feature row present:
      {score: SOURCE_TO_SCORE[row.source_confidence], weight: registry.default_weight}
  )

  disagreementPenalty = 0
  if filmGradeOptional exists:
    disagreementPenalty = min(15, abs(filmGradeOptional - dataCoreScore) * 0.25)

  missingPenalty = missingDataPenalty(prospectId, position)
  return clamp((coverageScore * 0.50) + (evidenceScore * 0.30) + (sourceScore * 0.20) - disagreementPenalty - (missingPenalty * 1.50))

function veteranOpportunityAdjustment(position, preGateScore, benchmarkScore):
  raw = (preGateScore - benchmarkScore) * 0.40
  return clamp(raw, VETERAN_CAPS[position].neg, VETERAN_CAPS[position].pos)

function finalDecisionScore(componentScores, veteranAdj, missingPenalty, gateAdjustment):
  preGate = (
    componentScores.main_prospect_score * 0.52 +
    componentScores.league_fit_score * 0.10 +
    componentScores.rookie_opportunity_score * 0.14 +
    componentScores.long_term_dynasty_score * 0.14 +
    componentScores.trade_insulation_score * 0.10
  )
  finalScore = clamp(preGate + veteranAdj + gateAdjustment - missingPenalty)
  return {
    pre_gate_score: clamp(preGate),
    final_decision_score: finalScore
  }
```

### Position formulas

#### QB

```text
function scoreQB(prospectId, benchmarkScore):
  draft_capital = getFeatureScore(prospectId, "QB", "draft_capital")
  passing_efficiency = getFeatureScore(prospectId, "QB", "passing_efficiency")
  rushing_profile = getFeatureScore(prospectId, "QB", "rushing_profile")
  sack_avoidance = getFeatureScore(prospectId, "QB", "sack_avoidance")
  accuracy_decision = getFeatureScore(prospectId, "QB", "accuracy_decision")
  age_trajectory = getFeatureScore(prospectId, "QB", "age_trajectory")
  starting_path = getFeatureScore(prospectId, "QB", "starting_path")
  team_environment = getFeatureScore(prospectId, "QB", "team_environment")
  developmental_stability = getFeatureScore(prospectId, "QB", "developmental_stability")
  injury_durability = getFeatureScore(prospectId, "QB", "injury_durability")
  film_grade = optionalFeatureScore(prospectId, "QB", "film_grade")

  main_prospect_score = weightedAverage([
    {score: draft_capital, weight: 26},
    {score: passing_efficiency, weight: 24},
    {score: rushing_profile, weight: 18},
    {score: sack_avoidance, weight: 12},
    {score: accuracy_decision, weight: 12},
    {score: age_trajectory, weight: 8}
  ])

  league_fit_score = weightedAverage([
    {score: rushing_profile, weight: 45},
    {score: passing_efficiency, weight: 25},
    {score: sack_avoidance, weight: 15},
    {score: accuracy_decision, weight: 15}
  ])

  rookie_opportunity_score = weightedAverage([
    {score: starting_path, weight: 50},
    {score: team_environment, weight: 30},
    {score: draft_capital, weight: 20}
  ])

  long_term_dynasty_score = weightedAverage([
    {score: draft_capital, weight: 30},
    {score: age_trajectory, weight: 20},
    {score: passing_efficiency, weight: 20},
    {score: rushing_profile, weight: 15},
    {score: developmental_stability, weight: 10},
    {score: injury_durability, weight: 5}
  ])

  trade_insulation_score = weightedAverage([
    {score: draft_capital, weight: 45},
    {score: rushing_profile, weight: 25},
    {score: passing_efficiency, weight: 15},
    {score: age_trajectory, weight: 10},
    {score: team_environment, weight: 5}
  ])

  preGate = weighted sum with FINAL_WEIGHTS

  elite_qb_gate =
    draft_capital >= 85 and
    (
      rushing_profile >= 85 or
      (passing_efficiency >= 92 and sack_avoidance >= 75)
    ) and
    trade_insulation_score >= 78

  if elite_qb_gate:
    gate_adjustment = 0
    gate_status = "qb_elite_exempt"
  else if draft_capital < 55:
    gate_adjustment = -14
    gate_status = "qb_low_capital_penalty"
  else if rushing_profile < 45 and passing_efficiency < 90:
    gate_adjustment = -10
    gate_status = "qb_structural_penalty"
  else:
    gate_adjustment = -8
    gate_status = "qb_structural_penalty"

  veteran_adj = veteranOpportunityAdjustment("QB", preGate, benchmarkScore)
  missing_penalty = missingDataPenalty(prospectId, "QB")
  confidence_score = confidenceScore(prospectId, "QB", main_prospect_score, film_grade)

  return finalDecisionScore(components, veteran_adj, missing_penalty, gate_adjustment)
```

#### RB

```text
function scoreRB(prospectId, benchmarkScore):
  draft_capital = getFeatureScore(prospectId, "RB", "draft_capital")
  workload_earning = getFeatureScore(prospectId, "RB", "workload_earning")
  rush_efficiency = getFeatureScore(prospectId, "RB", "rush_efficiency")
  receiving_impact = getFeatureScore(prospectId, "RB", "receiving_impact")
  age_trajectory = getFeatureScore(prospectId, "RB", "age_trajectory")
  goal_line_power = getFeatureScore(prospectId, "RB", "goal_line_power")
  chain_moving = getFeatureScore(prospectId, "RB", "chain_moving")
  athleticism = getFeatureScore(prospectId, "RB", "athleticism")
  projected_touch_path = getFeatureScore(prospectId, "RB", "projected_touch_path")
  offensive_line_environment = getFeatureScore(prospectId, "RB", "offensive_line_environment")
  injury_durability = getFeatureScore(prospectId, "RB", "injury_durability")

  main_prospect_score = weightedAverage([
    {score: draft_capital, weight: 28},
    {score: workload_earning, weight: 22},
    {score: rush_efficiency, weight: 18},
    {score: receiving_impact, weight: 12},
    {score: age_trajectory, weight: 10},
    {score: goal_line_power, weight: 10}
  ])

  league_fit_score = weightedAverage([
    {score: workload_earning, weight: 30},
    {score: chain_moving, weight: 30},
    {score: goal_line_power, weight: 20},
    {score: rush_efficiency, weight: 15},
    {score: receiving_impact, weight: 5}
  ])

  rookie_opportunity_score = weightedAverage([
    {score: projected_touch_path, weight: 40},
    {score: offensive_line_environment, weight: 25},
    {score: goal_line_power, weight: 20},
    {score: draft_capital, weight: 15}
  ])

  long_term_dynasty_score = weightedAverage([
    {score: draft_capital, weight: 30},
    {score: age_trajectory, weight: 20},
    {score: workload_earning, weight: 20},
    {score: receiving_impact, weight: 15},
    {score: athleticism, weight: 10},
    {score: injury_durability, weight: 5}
  ])

  trade_insulation_score = weightedAverage([
    {score: draft_capital, weight: 45},
    {score: workload_earning, weight: 20},
    {score: receiving_impact, weight: 15},
    {score: athleticism, weight: 10},
    {score: age_trajectory, weight: 10}
  ])

  gate_adjustment = 0
  gate_status = "none"
  veteran_adj = veteranOpportunityAdjustment("RB", preGate, benchmarkScore)
  missing_penalty = missingDataPenalty(prospectId, "RB")
  confidence_score = confidenceScore(prospectId, "RB", main_prospect_score, optional film grade)

  return finalDecisionScore(components, veteran_adj, missing_penalty, gate_adjustment)
```

#### WR

```text
function scoreWR(prospectId, benchmarkScore):
  draft_capital = getFeatureScore(prospectId, "WR", "draft_capital")
  target_earning = getFeatureScore(prospectId, "WR", "target_earning")
  efficiency_dominance = getFeatureScore(prospectId, "WR", "efficiency_dominance")
  age_trajectory = getFeatureScore(prospectId, "WR", "age_trajectory")
  role_robustness = getFeatureScore(prospectId, "WR", "role_robustness")
  chain_moving = getFeatureScore(prospectId, "WR", "chain_moving")
  athleticism = getFeatureScore(prospectId, "WR", "athleticism")
  projected_route_share = getFeatureScore(prospectId, "WR", "projected_route_share")
  quarterback_environment = getFeatureScore(prospectId, "WR", "quarterback_environment")
  injury_durability = getFeatureScore(prospectId, "WR", "injury_durability")

  main_prospect_score = weightedAverage([
    {score: draft_capital, weight: 24},
    {score: target_earning, weight: 22},
    {score: efficiency_dominance, weight: 22},
    {score: age_trajectory, weight: 12},
    {score: role_robustness, weight: 10},
    {score: chain_moving, weight: 10}
  ])

  league_fit_score = weightedAverage([
    {score: chain_moving, weight: 30},
    {score: role_robustness, weight: 25},
    {score: target_earning, weight: 20},
    {score: efficiency_dominance, weight: 15},
    {score: athleticism, weight: 10}
  ])

  rookie_opportunity_score = weightedAverage([
    {score: projected_route_share, weight: 40},
    {score: quarterback_environment, weight: 25},
    {score: draft_capital, weight: 20},
    {score: role_robustness, weight: 15}
  ])

  long_term_dynasty_score = weightedAverage([
    {score: draft_capital, weight: 25},
    {score: age_trajectory, weight: 20},
    {score: target_earning, weight: 20},
    {score: efficiency_dominance, weight: 15},
    {score: role_robustness, weight: 10},
    {score: injury_durability, weight: 10}
  ])

  trade_insulation_score = weightedAverage([
    {score: draft_capital, weight: 40},
    {score: target_earning, weight: 20},
    {score: age_trajectory, weight: 15},
    {score: efficiency_dominance, weight: 15},
    {score: athleticism, weight: 10}
  ])

  gate_adjustment = 0
  gate_status = "none"
  veteran_adj = veteranOpportunityAdjustment("WR", preGate, benchmarkScore)
  missing_penalty = missingDataPenalty(prospectId, "WR")
  confidence_score = confidenceScore(prospectId, "WR", main_prospect_score, optional film grade)

  return finalDecisionScore(components, veteran_adj, missing_penalty, gate_adjustment)
```

#### TE

```text
function scoreTE(prospectId, benchmarkScore):
  draft_capital = getFeatureScore(prospectId, "TE", "draft_capital")
  receiving_efficiency = getFeatureScore(prospectId, "TE", "receiving_efficiency")
  production_volume = getFeatureScore(prospectId, "TE", "production_volume")
  route_role = getFeatureScore(prospectId, "TE", "route_role")
  age_trajectory = getFeatureScore(prospectId, "TE", "age_trajectory")
  athletic_size = getFeatureScore(prospectId, "TE", "athletic_size")
  projected_route_share = getFeatureScore(prospectId, "TE", "projected_route_share")
  quarterback_environment = getFeatureScore(prospectId, "TE", "quarterback_environment")
  injury_durability = getFeatureScore(prospectId, "TE", "injury_durability")
  film_grade = optionalFeatureScore(prospectId, "TE", "film_grade")

  main_prospect_score = weightedAverage([
    {score: draft_capital, weight: 28},
    {score: receiving_efficiency, weight: 22},
    {score: production_volume, weight: 16},
    {score: route_role, weight: 16},
    {score: age_trajectory, weight: 8},
    {score: athletic_size, weight: 10}
  ])

  league_fit_score = weightedAverage([
    {score: route_role, weight: 40},
    {score: receiving_efficiency, weight: 30},
    {score: production_volume, weight: 20},
    {score: athletic_size, weight: 10}
  ])

  rookie_opportunity_score = weightedAverage([
    {score: projected_route_share, weight: 45},
    {score: quarterback_environment, weight: 25},
    {score: draft_capital, weight: 20},
    {score: route_role, weight: 10}
  ])

  long_term_dynasty_score = weightedAverage([
    {score: draft_capital, weight: 30},
    {score: age_trajectory, weight: 20},
    {score: receiving_efficiency, weight: 20},
    {score: route_role, weight: 15},
    {score: athletic_size, weight: 10},
    {score: injury_durability, weight: 5}
  ])

  trade_insulation_score = weightedAverage([
    {score: draft_capital, weight: 50},
    {score: receiving_efficiency, weight: 20},
    {score: route_role, weight: 15},
    {score: athletic_size, weight: 10},
    {score: age_trajectory, weight: 5}
  ])

  elite_te_gate =
    draft_capital >= 85 and
    receiving_efficiency >= 85 and
    route_role >= 80 and
    athletic_size >= 75

  if elite_te_gate:
    gate_adjustment = 0
    gate_status = "te_elite_exempt"
  else if draft_capital < 50:
    gate_adjustment = -18
    gate_status = "te_day3_penalty"
  else:
    gate_adjustment = -12
    gate_status = "te_structural_penalty"

  veteran_adj = veteranOpportunityAdjustment("TE", preGate, benchmarkScore)
  missing_penalty = missingDataPenalty(prospectId, "TE")
  confidence_score = confidenceScore(prospectId, "TE", main_prospect_score, film_grade)

  return finalDecisionScore(components, veteran_adj, missing_penalty, gate_adjustment)
```

### Flags, recommended range, and draft floor logic

```text
function riskFlags(position, scores, features, confidence):
  flags = []
  if confidence < 60: flags.push("low_confidence")
  if scores.veteran_opportunity_adjustment <= -6: flags.push("loses_to_veteran_market")
  else if scores.veteran_opportunity_adjustment <= -3: flags.push("veteran_opportunity_drag")

  if position == "QB":
    if scores.gate_adjustment < 0: flags.push("qb_1qb_suppression")
    if features.draft_capital < 55: flags.push("low_capital_qb")
    if features.rushing_profile < 45: flags.push("pocket_qb_only")

  if position == "RB":
    if features.workload_earning < 55: flags.push("committee_risk")
    if features.goal_line_power < 40: flags.push("goal_line_fragility")
    if features.receiving_impact >= 70 and features.goal_line_power < 45: flags.push("no_ppr_satellite")

  if position == "WR":
    if features.target_earning < 45: flags.push("weak_target_earning")
    if features.role_robustness < 45: flags.push("role_fragility")
    if features.age_trajectory < 40: flags.push("old_for_class")

  if position == "TE":
    if scores.gate_adjustment < 0: flags.push("te_no_premium_suppression")
    if features.draft_capital < 50: flags.push("day3_te_suppression")
    if features.route_role < 55: flags.push("blocking_dependency_risk")

  return sorted unique flags

function upsideFlags(position, scores, features):
  flags = []
  if scores.veteran_opportunity_adjustment >= 3: flags.push("beats_veteran_market")

  if position == "QB":
    if features.rushing_profile >= 85 and scores.gate_adjustment == 0: flags.push("elite_dual_threat_qb")
    if features.rushing_profile >= 85: flags.push("weekly_ceiling")

  if position == "RB":
    if features.workload_earning >= 80 and features.goal_line_power >= 75: flags.push("three_down_goal_line_rb")
    if features.chain_moving >= 80: flags.push("chain_moving_back")

  if position == "WR":
    if features.target_earning >= 85 and features.efficiency_dominance >= 80: flags.push("alpha_target_earner")
    if features.chain_moving >= 80 and features.role_robustness >= 75: flags.push("chain_moving_xflx_fit")

  if position == "TE":
    if scores.gate_adjustment == 0: flags.push("exceptional_te_gate")
    if features.receiving_efficiency >= 85: flags.push("difference_making_receiver")

  return sorted unique flags

function floorFlags(position, scores, features):
  flags = []
  if features.draft_capital >= 70: flags.push("day1_or_day2_capital")
  if scores.rookie_opportunity_score >= 75:
    if position in {"WR", "TE"}: flags.push("immediate_route_path")
    else: flags.push("immediate_role_path")
  if scores.trade_insulation_score >= 75: flags.push("trade_insulation")
  return sorted unique flags

function scoreToBasePick(finalDecisionScore):
  if finalDecisionScore >= 90: return 1
  if finalDecisionScore >= 86: return 2
  if finalDecisionScore >= 82: return 4
  if finalDecisionScore >= 78: return 6
  if finalDecisionScore >= 74: return 8
  if finalDecisionScore >= 70: return 11
  if finalDecisionScore >= 66: return 14
  if finalDecisionScore >= 62: return 18
  if finalDecisionScore >= 58: return 22
  if finalDecisionScore >= 54: return 27
  if finalDecisionScore >= 50: return 31
  if finalDecisionScore >= 46: return 36
  if finalDecisionScore >= 42: return 41
  return 46

function doNotDraftBeforePick(position, finalDecisionScore, confidence, veteranAdj, features, gateStatus):
  basePick = scoreToBasePick(finalDecisionScore)

  positionFloor = 1
  if position == "QB":
    if gateStatus == "qb_elite_exempt": positionFloor = 4
    else if features.draft_capital < 55: positionFloor = 21
    else: positionFloor = 11

  if position == "TE":
    if gateStatus == "te_elite_exempt": positionFloor = 11
    else if features.draft_capital < 50: positionFloor = 31
    else: positionFloor = 16

  if veteranAdj <= -6: basePick += 4
  else if veteranAdj <= -3: basePick += 2

  if confidence < 60: basePick += 3
  else if confidence < 75: basePick += 1

  return clamp(max(basePick, positionFloor), 1, 50)

function pickToRoundString(pickNumber):
  if pickNumber > 50: return "UDFA"
  roundNum = floor((pickNumber - 1) / 10) + 1
  roundPick = ((pickNumber - 1) % 10) + 1
  return roundNum + "." + zeroPad2(roundPick)

function recommendedDraftRange(finalDecisionScore, confidence, doNotDraftBefore):
  startPick = max(scoreToBasePick(finalDecisionScore), doNotDraftBefore)
  width = 3 if confidence >= 85 else 5 if confidence >= 70 else 7
  endPick = min(50, startPick + width - 1)
  return pickToRoundString(startPick) + "-" + pickToRoundString(endPick)
```

## Test Fixtures

These fixtures are intended for deterministic regression tests. They assume:

- all listed feature values are already normalized `0-100`
- missing-data penalty is `0.0` unless otherwise stated
- benchmark scores are: `QB 72`, `RB 70`, `WR 72`, `TE 66`
- score comparisons in tests use tolerance `±0.05` for raw float outputs and `±0.1` for CSV-rounded display values

```text
fixtures:
  - fixture_id: elite_rushing_qb
    position: QB
    confidence_assumption: 88
    benchmark_score: 72
    inputs:
      draft_capital: 92
      passing_efficiency: 86
      rushing_profile: 95
      sack_avoidance: 72
      accuracy_decision: 78
      age_trajectory: 82
      starting_path: 85
      team_environment: 74
      developmental_stability: 80
      injury_durability: 84
    expected_subscores:
      main_prospect_score: 86.2
      league_fit_score: 86.8
      rookie_opportunity_score: 83.1
      long_term_dynasty_score: 87.7
      trade_insulation_score: 90.0
      veteran_opportunity_adjustment: 3.0
      gate_adjustment: 0.0
    expected_final_score_range: [89.0, 90.0]
    expected_flags:
      risk: []
      upside: [beats_veteran_market, elite_dual_threat_qb, weekly_ceiling]
      floor: [day1_or_day2_capital, immediate_role_path, trade_insulation]
    expected_recommended_range: 1.04-1.06
    expected_do_not_draft_before_pick: 4

  - fixture_id: good_pocket_qb_suppressed
    position: QB
    confidence_assumption: 89
    benchmark_score: 72
    inputs:
      draft_capital: 88
      passing_efficiency: 84
      rushing_profile: 25
      sack_avoidance: 80
      accuracy_decision: 88
      age_trajectory: 75
      starting_path: 90
      team_environment: 80
      developmental_stability: 82
      injury_durability: 85
    expected_subscores:
      main_prospect_score: 73.7
      league_fit_score: 57.5
      rookie_opportunity_score: 86.6
      long_term_dynasty_score: 74.4
      trade_insulation_score: 73.1
      veteran_opportunity_adjustment: 0.6
      gate_adjustment: -10.0
    expected_final_score_range: [63.5, 65.0]
    expected_flags:
      risk: [pocket_qb_only, qb_1qb_suppression]
      upside: []
      floor: [day1_or_day2_capital, immediate_role_path]
    expected_recommended_range: 2.08-2.10
    expected_do_not_draft_before_pick: 18

  - fixture_id: high_capital_three_down_rb
    position: RB
    confidence_assumption: 90
    benchmark_score: 70
    inputs:
      draft_capital: 90
      workload_earning: 88
      rush_efficiency: 84
      receiving_impact: 76
      age_trajectory: 82
      goal_line_power: 85
      chain_moving: 86
      athleticism: 82
      projected_touch_path: 87
      offensive_line_environment: 78
      injury_durability: 85
    expected_subscores:
      main_prospect_score: 85.5
      league_fit_score: 85.6
      rookie_opportunity_score: 84.8
      long_term_dynasty_score: 84.9
      trade_insulation_score: 85.9
      veteran_opportunity_adjustment: 5.0
      gate_adjustment: 0.0
    expected_final_score_range: [90.0, 91.0]
    expected_flags:
      risk: []
      upside: [beats_veteran_market, chain_moving_back, three_down_goal_line_rb]
      floor: [day1_or_day2_capital, immediate_role_path, trade_insulation]
    expected_recommended_range: 1.01-1.03
    expected_do_not_draft_before_pick: 1

  - fixture_id: satellite_receiving_rb_no_ppr_downgrade
    position: RB
    confidence_assumption: 84
    benchmark_score: 70
    inputs:
      draft_capital: 62
      workload_earning: 54
      rush_efficiency: 62
      receiving_impact: 86
      age_trajectory: 76
      goal_line_power: 30
      chain_moving: 48
      athleticism: 74
      projected_touch_path: 50
      offensive_line_environment: 65
      injury_durability: 75
    expected_subscores:
      main_prospect_score: 61.3
      league_fit_score: 50.2
      rookie_opportunity_score: 51.6
      long_term_dynasty_score: 68.7
      trade_insulation_score: 66.6
      veteran_opportunity_adjustment: -3.8
      gate_adjustment: 0.0
    expected_final_score_range: [56.0, 57.0]
    expected_flags:
      risk: [committee_risk, goal_line_fragility, no_ppr_satellite, veteran_opportunity_drag]
      upside: []
      floor: []
    expected_recommended_range: 3.07-4.01
    expected_do_not_draft_before_pick: 27

  - fixture_id: elite_wr_profile
    position: WR
    confidence_assumption: 91
    benchmark_score: 72
    inputs:
      draft_capital: 93
      target_earning: 92
      efficiency_dominance: 90
      age_trajectory: 84
      role_robustness: 88
      chain_moving: 86
      athleticism: 79
      projected_route_share: 82
      quarterback_environment: 76
      injury_durability: 83
    expected_subscores:
      main_prospect_score: 89.8
      league_fit_score: 87.6
      rookie_opportunity_score: 83.6
      long_term_dynasty_score: 89.1
      trade_insulation_score: 89.6
      veteran_opportunity_adjustment: 5.0
      gate_adjustment: 0.0
    expected_final_score_range: [93.0, 94.0]
    expected_flags:
      risk: []
      upside: [alpha_target_earner, beats_veteran_market, chain_moving_xflx_fit]
      floor: [day1_or_day2_capital, immediate_route_path, trade_insulation]
    expected_recommended_range: 1.01-1.03
    expected_do_not_draft_before_pick: 1

  - fixture_id: older_raw_wr_weak_target_earning
    position: WR
    confidence_assumption: 78
    benchmark_score: 72
    inputs:
      draft_capital: 58
      target_earning: 38
      efficiency_dominance: 62
      age_trajectory: 32
      role_robustness: 46
      chain_moving: 44
      athleticism: 82
      projected_route_share: 55
      quarterback_environment: 72
      injury_durability: 78
    expected_subscores:
      main_prospect_score: 48.8
      league_fit_score: 49.8
      rookie_opportunity_score: 58.5
      long_term_dynasty_score: 50.2
      trade_insulation_score: 53.1
      veteran_opportunity_adjustment: -8.5
      gate_adjustment: 0.0
    expected_final_score_range: [42.0, 43.0]
    expected_flags:
      risk: [loses_to_veteran_market, old_for_class, veteran_opportunity_loss, weak_target_earning]
      upside: []
      floor: []
    expected_recommended_range: 5.01-5.07
    expected_do_not_draft_before_pick: 41

  - fixture_id: elite_te_exceptional_gate
    position: TE
    confidence_assumption: 88
    benchmark_score: 66
    inputs:
      draft_capital: 88
      receiving_efficiency: 90
      production_volume: 82
      route_role: 87
      age_trajectory: 80
      athletic_size: 81
      projected_route_share: 78
      quarterback_environment: 74
      injury_durability: 84
    expected_subscores:
      main_prospect_score: 86.0
      league_fit_score: 86.3
      rookie_opportunity_score: 79.9
      long_term_dynasty_score: 85.8
      trade_insulation_score: 87.9
      veteran_opportunity_adjustment: 3.0
      gate_adjustment: 0.0
    expected_final_score_range: [88.0, 89.0]
    expected_flags:
      risk: []
      upside: [beats_veteran_market, difference_making_receiver, exceptional_te_gate]
      floor: [day1_or_day2_capital, immediate_route_path, trade_insulation]
    expected_recommended_range: 2.01-2.03
    expected_do_not_draft_before_pick: 11

  - fixture_id: day3_te_heavily_suppressed
    position: TE
    confidence_assumption: 83
    benchmark_score: 66
    inputs:
      draft_capital: 38
      receiving_efficiency: 68
      production_volume: 62
      route_role: 55
      age_trajectory: 70
      athletic_size: 77
      projected_route_share: 42
      quarterback_environment: 68
      injury_durability: 82
    expected_subscores:
      main_prospect_score: 57.6
      league_fit_score: 62.5
      rookie_opportunity_score: 49.0
      long_term_dynasty_score: 59.1
      trade_insulation_score: 56.5
      veteran_opportunity_adjustment: -3.8
      gate_adjustment: -18.0
    expected_final_score_range: [34.0, 35.5]
    expected_flags:
      risk: [day3_te_suppression, te_no_premium_suppression, veteran_opportunity_drag]
      upside: []
      floor: []
    expected_recommended_range: 5.06-5.10
    expected_do_not_draft_before_pick: 46

  - fixture_id: rookie_loses_to_veteran_opportunity_cost
    position: WR
    confidence_assumption: 84
    benchmark_score: 72
    inputs:
      draft_capital: 66
      target_earning: 58
      efficiency_dominance: 64
      age_trajectory: 72
      role_robustness: 60
      chain_moving: 58
      athleticism: 70
      projected_route_share: 52
      quarterback_environment: 68
      injury_durability: 80
    expected_subscores:
      main_prospect_score: 63.1
      league_fit_score: 60.6
      rookie_opportunity_score: 60.0
      long_term_dynasty_score: 66.1
      trade_insulation_score: 65.4
      veteran_opportunity_adjustment: -3.6
      gate_adjustment: 0.0
    expected_final_score_range: [59.0, 60.0]
    expected_flags:
      risk: [veteran_opportunity_drag]
      upside: []
      floor: []
    expected_recommended_range: 3.02-3.06
    expected_do_not_draft_before_pick: 22

  - fixture_id: rookie_beats_veteran_opportunity_cost
    position: RB
    confidence_assumption: 88
    benchmark_score: 70
    inputs:
      draft_capital: 86
      workload_earning: 82
      rush_efficiency: 80
      receiving_impact: 68
      age_trajectory: 80
      goal_line_power: 78
      chain_moving: 81
      athleticism: 79
      projected_touch_path: 80
      offensive_line_environment: 76
      injury_durability: 82
    expected_subscores:
      main_prospect_score: 80.5
      league_fit_score: 79.9
      rookie_opportunity_score: 79.5
      long_term_dynasty_score: 80.4
      trade_insulation_score: 81.2
      veteran_opportunity_adjustment: 4.1
      gate_adjustment: 0.0
    expected_final_score_range: [84.0, 85.0]
    expected_flags:
      risk: []
      upside: [beats_veteran_market, chain_moving_back, three_down_goal_line_rb]
      floor: [day1_or_day2_capital, immediate_role_path, trade_insulation]
    expected_recommended_range: 1.04-1.06
    expected_do_not_draft_before_pick: 4
```

## UI and Table Design

A table-first UI is the correct fit here. `st.dataframe` provides interactive tables with sort/search/selection behavior, while `st.data_editor` supports controlled editing workflows. Streamlit’s column-configuration APIs and link columns are enough to build a compact rookie board, a huge audit table, and a manual-override view without needing a custom frontend. Optional local exports can be done with `st.download_button`. citeturn5search0turn5search1turn5search6turn1search1turn5search9turn1search14turn1search16turn5search8

### Compact rookie board

Use `rookie_model_outputs.csv` as the primary source. Sort by:

1. `final_decision_score` descending  
2. `confidence_score` descending  
3. `main_prospect_score` descending  
4. `trade_insulation_score` descending  
5. `prospect_id` ascending

Columns:

| column | source | behavior |
|---|---|---|
| rank | `board_rank` | integer, pinned left |
| player | `player_name` | display name |
| position | `position` | categorical |
| team | `nfl_team` | team code or blank |
| final_decision_score | `final_decision_score` | 1 decimal, sortable |
| confidence | `confidence_score` | 1 decimal, sortable |
| recommended_range | `recommended_range` | string like `1.04-1.06` |
| do_not_draft_before_pick | `do_not_draft_before_pick` | integer |
| top_flags | derived from `risk_flags`, `upside_flags`, `floor_flags` | show up to 3 slugs, then `+n` |
| veteran_opportunity_adjustment | `veteran_opportunity_adjustment` | signed decimal |
| short_explanation | `short_explanation` | deterministic summary string |

Deterministic `short_explanation` template:

```text
"{top_positive_reason}; {best_opportunity_reason}; {largest_drag_or_gate_reason}"
```

Examples:

- `Elite target earning; immediate route path; no veteran drag`
- `Three-down plus goal-line role; strong touch path; beats veteran market`
- `Pocket QB in 1QB; good starter path; structural QB suppression`

### Huge audit table

Build this by joining:

- `rookie_feature_scores.csv`
- `rookie_feature_registry.csv`
- `rookie_prospect_inputs.csv`
- `rookie_audit_notes.csv` as optional detail expander

Every registry feature should appear, including display-only and rejected rows. That is what makes the app explainable.

Columns:

| column | source | behavior |
|---|---|---|
| player | prospect inputs | pinned left |
| position | prospect inputs | categorical |
| feature_name | registry | slug |
| raw_value | feature scores | prefer `raw_value_numeric`, else `raw_value_text` |
| normalized_score | feature scores | 0-100 or blank |
| feature_weight | registry plus formula mapping | show the weight actually used in the active formula context |
| weighted_contribution | derived | contribution to final score, not just component score |
| evidence_strength | registry | enum |
| source | feature scores `source_summary` | short text |
| missing_flag | feature scores `is_missing` | boolean |
| risk_flag | derived | `true` if feature contributes to a triggered risk flag |
| upside_flag | derived | `true` if feature contributes to an upside flag |
| floor_flag | derived | `true` if feature contributes to a floor flag |
| implementation_note | registry `implementation_notes` | short summary |

Recommended derived formulas for the table:

```text
component_multiplier =
  0.52 for main_prospect_score
  0.10 for league_fit_score
  0.14 for rookie_opportunity_score
  0.14 for long_term_dynasty_score
  0.10 for trade_insulation_score
  0.00 for display_only

weighted_contribution =
  normalized_score * feature_weight * component_multiplier / 10000
```

UI behavior:

- default filter: `position in {QB,RB,WR,TE}` and `season = active season`
- expose toggles for `show_display_only`, `show_post_draft_only`, `show_missing_only`, `show_risk_only`
- allow row selection to open note details
- keep `citation_links` hidden in the grid or render as a linked expander field after resolving local source keys to URLs or file paths

## Validation and Guardrails

The validator should reject bad data before any score calculation. RFC-style CSV shape and Python CSV parsing are deterministic only if row counts, headers, and file-opening rules are consistent, so schema validation must happen at load time, not after scoring. citeturn4search0turn3search0

| rule | implementation check |
|---|---|
| every weighted feature must be `0-100` | reject any scored feature row outside bounds |
| missing core inputs default to `50` but reduce confidence | use `getFeatureScore -> 50`; apply `missingDataPenalty` and confidence deduction |
| rejected/display-only features must not affect score | if `is_rejected_or_display_only=true`, contribution must be `0` |
| landing spot must not affect `main_prospect_score` | forbid `landing_spot_overlay` from any main-component formula |
| veteran opportunity adjustment must be capped by position | enforce caps: QB `[-14,+3]`, RB `[-10,+5]`, WR `[-10,+5]`, TE `[-12,+3]` |
| QB and TE gates must be enforced | apply gate logic after pre-gate weighted sum, before final score output |
| all formulas must be deterministic | no randomness, no seeds, no external services, no time-based drift |
| no live APIs or scraping at runtime | all runtime reads come from checked-in CSV/JSON and local uploads only |
| no generated SQLite/data_pack output should be committed | add generated artifacts and caches to `.gitignore`; commit only source fixtures |
| foreign keys must be valid | feature scores require prospect + registry entries; outputs require prospect entries |
| row uniqueness must hold | enforce unique keys per schema contract |
| pre-draft mode must be valid | post-draft features can be missing and should neutralize to `50` rather than error |
| manual overrides must be auditable | any `is_user_override=true` row requires `override_reason` and matching audit note |
| flags must be stable | sort flag slugs lexicographically before persistence |
| board sort must be stable | use deterministic tie-breakers exactly as defined in UI section |
| rounding must be display-only | compute in float; round to 1 decimal only when persisting or rendering |
| benchmark freshness must match league workflow | only `is_active_benchmark=true` rows participate in veteran comparison |
| handwritten history must not silently become score input | handwritten notes go to `rookie_audit_notes.csv`; only explicit override rows may alter scoring |

Recommended load order:

```text
1. load rookie_feature_registry.csv
2. load rookie_prospect_inputs.csv
3. load rookie_feature_scores.csv
4. load veteran_opportunity_benchmarks.csv
5. load rookie_audit_notes.csv
6. validate FKs and enums
7. score prospects
8. write rookie_model_outputs.csv
```

## Migration Plan

A staged build is safer than trying to ship the whole war room at once. Python dataclasses are a good fit for mirroring CSV row contracts because they generate useful methods from type-annotated fields, and `pytest` fixtures plus parametrization are a natural match for deterministic score regression tests. The Streamlit app can remain a normal Python script run locally. citeturn0search2turn0search3turn0search15turn5search8

| step | deliverable | explicit output |
|---|---|---|
| Step 1: add CSV schema/docs only | commit schema docs and empty templates | add the six CSVs with headers only, plus README schema notes and validator stubs |
| Step 2: add model functions and deterministic tests | scoring engine with no UI | add `schema_models.py`, `csv_io.py`, `scoring.py`, `flags.py`, `ranges.py`, and `tests/test_model_regression.py` |
| Step 3: add sample rookie fixtures | reproducible fixture data | seed at least the ten fixtures above as prospect rows + long-form feature rows + benchmark rows |
| Step 4: add compact rookie board table | minimal decision UI | Streamlit page with outputs table, sorting, filters, and local CSV export |
| Step 5: add huge audit table view | explainability UI | joined long-form audit table with per-feature contributions, hidden source keys, and note expander |
| Step 6: add veteran/free-agent comparison layer | opportunity-cost logic | load active benchmarks after roster declaration and show signed veteran adjustment on board |
| Step 7: add manual override/provenance notes | controlled editorial layer | data-editor or local form for overrides that writes to `rookie_feature_scores.csv` and `rookie_audit_notes.csv` |

Recommended code-shape by the end of Step 2:

```text
app/
  app.py
  schema_models.py
  csv_io.py
  scoring.py
  flags.py
  ranges.py
  validators.py
  fixtures/
    rookie_prospect_inputs.csv
    rookie_feature_registry.csv
    rookie_feature_scores.csv
    rookie_model_outputs.csv
    veteran_opportunity_benchmarks.csv
    rookie_audit_notes.csv
tests/
  test_schema_validation.py
  test_scoring_regression.py
  test_position_gates.py
  test_veteran_adjustment.py
  test_missing_data.py
```

## Open Questions

These are the main decisions worth settling before coding begins.

| open question | current default | why it matters |
|---|---|---|
| Should RB/WR veteran opportunity use same-position only or a flex-pool benchmark? | same-position only in v1 | flex-heavy lineup makes cross-position opportunity cost relevant; same-position is simpler |
| Where should raw-to-normalized transforms live? | local JSON or Python constants, not runtime-generated | formulas assume normalized inputs already exist |
| Should film grades remain one number or become subgrades? | one normalized score, display-only in v1 | subgrades improve explainability but create more manual work |
| Should consensus trade value be fully internal or imported from outside rankings? | internal only in v1 | outside market signals help, but they add provenance complexity |
| How should handwritten historical league notes be used? | notes-only unless explicitly overridden | avoids accidental contamination from uncertain historical records |
| Should pre-NFL-draft mode be supported, or only post-draft boards? | support both | pre-draft mode requires neutral post-draft inputs and lower confidence |
| Should citations live inline in CSVs or in a separate local source catalog? | source-key fields in CSV, resolved via local map | better for local-first and friendlier than repeating long URLs |
| Should user overrides be limited to feature scores, or can they force final score outputs? | feature-score overrides only | preserves determinism and explainability |
| Should veterans eventually appear on the same board as rookies, or only as benchmark overlays? | benchmark overlay only in v1 | a unified board is useful later but broadens scope materially |
| Do you want a rookie-only board plus an all-asset board? | rookie-only board first | your draft decision already compares rookies to released veterans, so an all-asset board may become the real end state |

The fastest path to a trustworthy first version is to freeze the normalization tables, keep overrides auditable, score only from local fixtures, and treat the formulas above as the single scoring source of truth while letting the audit table expose every feature, every penalty, every gate, and every veteran comparison.