# LVE Data Source, Confidence, and Manual Override Policy

## Core findings

For LVE, the safest source policy is **domain-specific, not globally hierarchical**. Direct exports from entity["company","Sleeper","fantasy sports app"] should be the canonical source for league state because the platform’s API is read-only, exposes leagues, drafts, rosters, users, and traded picks, and explicitly recommends storing stable `user_id` values because usernames can change. Its support docs also confirm that keeper and dynasty leagues allow future-pick trading and that the draftboard reflects current pick ownership. Official entity["sports_league","NFL","us football league"] injury reports and transaction logs should outrank every editorial source for current player availability, because the league publicly defines participation and game-status categories and still enforces the policy with fines for inaccurate reporting. citeturn6view0turn7view2turn7view3turn14view3turn6view2turn13view0turn13view1turn6view6turn12search1turn12search5

Public market and editorial sources are still useful, but only as **secondary evidence**. entity["company","FantasyPros","fantasy sports company"] states that ECR is a consensus constructed from tracked experts, that rankings and advice are updated daily with revision dates, that NFL weekly projections are aggregated from multiple sources, and that its fantasy depth charts are based on ECR and may not match team-announced depth charts. Just as important for LVE, its draft-accuracy methodology is evaluated in **half-PPR**, not in a 1QB, no-PPR, first-down-bonus format like yours. Contract databases such as entity["organization","Over the Cap","nfl contract site"] and entity["company","Spotrac","sports contracts site"] are useful for structure, security, and timing, but they are not official league-state truth and should not override direct role or availability evidence. citeturn6view1turn8view2turn8view3turn6view4turn6view5turn8view5turn8view6turn8view0turn14view0

A provenance layer is mandatory, not optional. entity["organization","W3C","web standards consortium"] defines provenance as information about entities, activities, and people involved in producing data, specifically so users can assess quality, reliability, and trustworthiness. entity["organization","National Institute of Standards and Technology","us standards agency"] identifies completeness, accuracy, integrity, consistency, and timeliness as key data-quality components. Missing-data guidance also warns that missing observations can bias estimates and weaken inference. For this app, every imported file, manual correction, and scoring run therefore needs source IDs, timestamps, effective dates, before/after values, and a reproducible run record. citeturn6view3turn10view2turn10view4

## Source hierarchy and required data

The source hierarchy should be applied **by question type**. The league-rank PDF is authoritative for forced-release logic but irrelevant to injury status. The official injury report is authoritative for availability but irrelevant to pick ownership. Market ranks help measure public liquidity, but they should never become the truth set for LVE scoring.

| Data domain | Canonical local source | Required or optional | LVE precedence | Freshness target | Allowed model use |
|---|---|---:|---|---|---|
| League rosters, franchises, roster IDs, users | Timestamped local export from Sleeper | Required | Highest for league state | Within 24h of declaration lock and within 24h of draft room open | Ownership, roster slots, roster comparison, pick mapping |
| Draft list, draft IDs, traded picks | Timestamped local Sleeper export plus offline draft reconciliation file when needed | Required | Highest for picks | Within 24h of draft; immediately after any trade | Pick ownership, rookie-slot mapping, draft-room board |
| League-rank top-five document | Commissioner-issued PDF/TXT/CSV snapshot | Required for forced-release tools; optional otherwise | Highest for summer forced-release logic only | Current summer issue only | Forced-release pressure, candidate selection, opponent-targeting |
| Official injury status | Local snapshot of official NFL practice/game-status reports | Required for veteran/free-agent evaluation inside final pre-draft window; recommended otherwise | Highest for availability | Same day if inside 72h of draft; otherwise within 3 days | Opportunity, review warnings, confidence, injury blocker checks |
| Official transactions | Local snapshot of NFL transaction wire | Required for veteran/free-agent and roster-eligibility views | Highest for signings, waivers, reserve moves, releases | Same day in final 72h before draft; otherwise within 7 days | Availability, team assignment, free-agent pool membership |
| Market ranks | Snapshot of FantasyPros ECR or equivalent market file with scoring context stored | Optional | Secondary | Within 7 days, preferably 72h | Trade-liquidity overlay, public-vs-private gap, tiebreakers |
| Projections | Imported local projection bundle with source names and timestamps | Optional but recommended for veteran/free-agent modules | Secondary | Within 7 days preseason; tighter if used in-season | Win-now overlays, range of outcomes, signal agreement |
| Depth charts | Imported depth chart or role snapshot with source label | Optional | Tertiary | Within 72h if used | Role tiebreaker, confidence, review warnings only |
| Contracts | OTC/Spotrac snapshot plus source label | Optional | Tertiary | Within 30 days in the offseason | Security/liquidity context, not base role truth |
| Manual typed notes | Curated local notes CSV | Optional | Low | No fixed window; must have author/date | Review context, override support, display notes |
| Handwritten league history | Image/PDF plus reviewed transcription file | Optional | Lowest until verified | No freshness rule | Historical audit only; never score directly until transcribed and verified |

That hierarchy follows the actual structure of the available source systems. Sleeper is the best source for league-state objects and pick ownership; the NFL’s own reporting rules and transactions are the most authoritative public availability sources; FantasyPros is explicit that its ranks are consensus opinion, its revisions are date-stamped, its weekly projections are aggregated from several sources, and its fantasy depth charts are not necessarily the same as team-announced charts. citeturn6view0turn7view2turn7view3turn14view3turn6view2turn13view0turn13view1turn6view6turn6view1turn8view2turn8view3turn6view4turn6view5

The minimum required data should also be **run-mode dependent**, because the app has multiple jobs. A compact rookie board can tolerate optional-market gaps; a forced-release board cannot tolerate missing league-rank data; and a draft-room veteran-versus-rookie comparison cannot tolerate unresolved pick ownership or player team status.

| Run mode | Required inputs | Review-only inputs | Hard block if missing |
|---|---|---|---|
| Core rookie board | Player identity, position, season, rookie-model features, current pick ownership file | Market ranks, projections, manual notes | Duplicate asset keys, unresolved pick ownership, missing model version |
| Veteran board | Player identity, position, current team/status, transaction snapshot, core veteran features | Projections, contracts, market ranks, notes | Unknown roster status, conflicting team assignment, missing transaction snapshot inside final draft window |
| Forced-release planner | League-rank top-five file, declaration roster snapshot, team rosters | Market ranks, contracts, notes | Missing current league-rank file, missing declaration snapshot |
| Draft-room unified board | Current rosters, current pick ownership, rookie outputs, veteran outputs, free-agent pool, veteran-opportunity layer | Market ranks, optional projections, depth charts | Any unresolved pick owner, duplicate player IDs, stale draft-state snapshot after a known trade |
| Historical study | Transcribed league history, mapped identities, season tags | Photos/scans of handwritten notes | Unverified transcription used as scored input |

## Missing-data and confidence policy

The app should treat missingness as a **data-quality problem**, not as a hidden football opinion. Because data quality is commonly evaluated through completeness, accuracy, integrity, consistency, and timeliness, and because missing data can bias inference, the safest local-first rule is: **neutral imputation for score stability, visible confidence penalties for trust, and hard blocks when identity or ownership is unresolved**. Forecast-combination research also supports using agreement across multiple independent sources as a confidence input, because combining forecasts often improves accuracy and simple averages are hard to beat. citeturn10view2turn10view4turn8view4

### Missing-data policy

| Missingness class | Rule | Score effect | Confidence effect | UI outcome |
|---|---|---|---|---|
| Identity-critical | Do not impute | No score produced | Confidence not computed | Blocking warning |
| Ownership-critical | Do not impute | No score produced | Confidence not computed | Blocking warning |
| Core scored feature | Impute neutral `50` on normalized 0-100 scale | Keeps formulas deterministic | Apply core-feature confidence penalty | Review-needed warning |
| Secondary scored feature | Impute neutral `50` | Small effect only | Smaller confidence penalty | Data warning |
| Overlay-only feature | Leave blank or impute neutral `50` depending on formula design | Must not move main talent score materially | Small or zero penalty | Data warning |
| Display-only feature | Leave blank | None | None | No score effect; optional note |

**Model-design policy:**  
Use neutral `50`, not `0`, for any missing normalized feature that is still allowed into formulas. Zero implies a bad football signal; `50` explicitly means unknown.

**Hard block conditions:**  
A run should be blocked if any of the following are unresolved:
- duplicate or ambiguous `asset_key`
- missing `asset_type`, `position`, or `season`
- missing current owner for any pick asset in a draft-room comparison
- missing current team or roster-status source for a veteran/free agent inside the final draft window
- missing current league-rank file when the forced-release module is active
- any override touching a blocked field without evidence, author, and timestamp

### Confidence score formula

The exact weights below are **model-design choices**, not externally validated football coefficients. They are recommended because they line up with the strongest evidence available on data quality, provenance, and forecast combination without pretending to be a learned model.

**Recommended formula**

\[
\text{confidence\_score} =
\mathrm{clamp}\Big(
0.40 \cdot \text{completeness} +
0.25 \cdot \text{source\_reliability} +
0.20 \cdot \text{freshness} +
0.15 \cdot \text{signal\_agreement} +
\text{override\_adjustment},
0, 100
\Big)
\]

**Component definitions**

| Component | Definition | Recommended implementation |
|---|---|---|
| `completeness` | Weighted coverage of expected fields for the current run mode | `100 * present_weight / expected_weight`, where critical fields carry larger weights than optional overlays |
| `source_reliability` | Weighted average of source-tier scores for populated fields | Tier A local canonical or official = 100; Tier B official public = 90; Tier C structured market = 75; Tier D editorial estimate = 60; Tier E unverified manual/history = 35 |
| `freshness` | Weighted average of freshness scores by domain | Use domain windows below |
| `signal_agreement` | Agreement among comparable external signals | If 3+ external signals exist, convert each to a percentile, compute average pairwise spread, then `100 - min(100, spread*125)`; if only one external signal exists, default to `50` |
| `override_adjustment` | Bonus or penalty tied to manual intervention quality | `+0` to `+5` if an override resolves a verified source error using a stronger source; `0` if no override; `-5` to `-20` for opinion-driven or poorly documented overrides |

**Freshness windows**

| Domain | `100` | `70` | `40` | `10` | Block threshold |
|---|---|---|---|---|---|
| League state / picks | ≤24h | 25–72h | 4–7d | >7d | If a known trade/declaration occurred after snapshot |
| Injury reports | Same day | 1 day old | 2–3 days old | >3 days | If inside final 72h before draft and no current report exists |
| Transactions | Same day | 1–2 days old | 3–7 days old | >7 days | If veteran/free-agent board is active inside final draft window |
| Market ranks / projections | ≤72h | 4–7d | 8–21d | >21d | Never block by themselves |
| Depth charts | ≤72h | 4–7d | 8–14d | >14d | Never block by themselves |
| Contracts | ≤30d | 31–60d | 61–120d | >120d | Never block by themselves |

**Do not double-penalize missingness.** If completeness already captures the absence of a field, the app should not also subtract an additional global penalty unless the field is in a specific “critical feature missing” exception list.

## Manual overrides and provenance

The override policy should preserve the model’s two core promises: **determinism** and **explainability**. That means the user is allowed to correct bad data, resolve conflicts, and document league-specific facts, but not to silently rewrite outputs. A strong provenance chain is what keeps a local-first app trustworthy after multiple manual edits. That recommendation is directly aligned with W3C’s provenance model and the standard data-quality dimensions emphasized by NIST. citeturn6view3turn10view2

### What can and cannot be overridden

| Override target | Allowed | Conditions | Direct score impact |
|---|---:|---|---:|
| Raw imported field | Yes | Must capture old value, new value, reason, evidence source, author, timestamp | Indirect only, via recalculation |
| Source conflict resolution | Yes | Must state why one source outranks another for this field | Indirect only |
| Handwritten transcription correction | Yes | Must link to scan/photo and transcription reviewer | Indirect only |
| League-rank mapping | Yes | Must link to the actual issued league-rank source | Indirect only |
| Pick ownership correction after offline event | Yes | Must cite commissioner note or reconciled draft sheet | Indirect only |
| Injury/availability correction | Yes, cautiously | Must prefer official report or official transaction evidence | Indirect only |
| Normalization thresholds / feature weights | Yes, but as model-version change, not ad hoc player edit | Requires new model version and run metadata | Indirect only |
| `final_decision_score` | **No** | Never directly editable | None |
| `confidence_score` | **No** | Must be recomputed from the formula | None |
| `recommended_range` | **No** | Derived output only | None |
| `do_not_draft_before_pick` | **No** | Derived output only | None |
| Derived flags | **No direct editing** | Change inputs or add review note instead | None |

### Required explanation fields for every override

Every override row should include:
- `override_id`
- `entity_type`
- `entity_key`
- `field_name`
- `old_value`
- `new_value`
- `reason_code`
- `explanation_text`
- `evidence_source_id`
- `author`
- `applied_at_local`
- `review_status`

**Strong policy recommendation:** if the app is single-user, the same user may approve their own override, but the record should still explicitly say `self_approved=true`. If the app ever becomes multi-user, critical overrides should require a second reviewer.

### Audit trail requirements

The audit system should be append-only at the row level:
- Never edit an old override row in place; supersede it with a new row.
- Every run stores the exact input snapshot IDs and hashes it used.
- Every note can link to both the source row and the override row it motivated.
- Every scored output row should be traceable back to a `run_id`, a `model_version`, and a set of source snapshots.

That is the simplest practical version of provenance for a local CSV app: **entity** = source file or player row, **activity** = import/override/run, **agent** = user who did it. citeturn6view3

## CSV schemas

Below are the recommended Phase 9 governance files. The first three are **curated inputs** and may be committed if you want versioned audit history. The last one is a **generated run artifact** and should normally be ignored by version control.

**`source_catalog.csv`**

| Column | Type | Required | Description |
|---|---|---:|---|
| `source_id` | string | Yes | Stable unique ID for a source snapshot or local document |
| `source_family` | enum | Yes | `league_platform`, `league_rank_doc`, `market_rank`, `projection`, `injury_report`, `transaction_wire`, `depth_chart`, `contract_db`, `manual_note`, `handwritten_history` |
| `source_name` | string | Yes | Human-readable display name |
| `source_domain` | enum | Yes | `league_state`, `league_rank`, `market`, `projection`, `injury`, `transaction`, `depth_chart`, `contract`, `note`, `history` |
| `authority_tier` | enum | Yes | `tier_a_local_canonical`, `tier_b_official_public`, `tier_c_structured_market`, `tier_d_editorial_estimate`, `tier_e_manual_unverified` |
| `priority_rank` | integer | Yes | Lower number means higher precedence within the same domain |
| `required_for_modes` | string | Yes | Pipe-delimited run modes, e.g. `draft_room|forced_release` |
| `freshness_window_hours` | integer | No | Domain freshness SLA for confidence scoring |
| `source_format` | enum | Yes | `csv`, `json`, `pdf`, `txt`, `md`, `xlsx`, `jpg`, `png` |
| `local_path` | string | Yes | Workspace-relative local file path |
| `source_url` | string | No | Original external URL if applicable |
| `captured_at_local` | datetime | Yes | When the local copy was captured |
| `effective_date` | date | No | Date the source became operative |
| `season` | integer | No | Relevant NFL/LVE season |
| `scoring_context` | string | No | Examples: `half_ppr`, `standard`, `custom_lve`, `n/a` |
| `checksum_sha256` | string | No | File checksum for reproducibility |
| `parser_version` | string | No | Import/parser version used |
| `source_notes` | string | No | Freeform provenance note |
| `is_active` | boolean | Yes | Whether source should currently be considered in precedence resolution |

**Validation rules**
- `source_id` must be unique.
- `priority_rank` must be unique within `source_domain` for `is_active=true`.
- `scoring_context` is mandatory for all market-rank and projection sources.
- `checksum_sha256` is strongly recommended for file-based sources and required for any source that can affect a money-decision run.

**`audit_notes.csv`**

| Column | Type | Required | Description |
|---|---|---:|---|
| `note_id` | string | Yes | Stable note ID |
| `entity_type` | enum | Yes | `player`, `pick`, `team`, `league`, `source`, `run` |
| `entity_key` | string | Yes | Key of the affected object |
| `season` | integer | No | Relevant season |
| `note_scope` | enum | Yes | `data`, `model`, `decision`, `forced_release`, `history` |
| `severity` | enum | Yes | `info`, `data_warning`, `model_warning`, `review_needed`, `blocking` |
| `note_text` | string | Yes | Human-readable note |
| `linked_source_id` | string | No | Optional foreign key to `source_catalog.csv` |
| `linked_override_id` | string | No | Optional foreign key to `manual_overrides.csv` |
| `author` | string | Yes | Who wrote the note |
| `created_at_local` | datetime | Yes | Creation time |
| `expires_at_local` | datetime | No | Optional expiry time |
| `review_status` | enum | Yes | `open`, `reviewed`, `resolved`, `archived` |
| `reviewed_by` | string | No | Reviewer identity |
| `reviewed_at_local` | datetime | No | Review timestamp |

**Validation rules**
- `severity=blocking` notes must either link to an active source issue or explicitly state the blocking reason.
- Notes tied to handwritten history should include either a linked scan source or a transcription source.

**`manual_overrides.csv`**

| Column | Type | Required | Description |
|---|---|---:|---|
| `override_id` | string | Yes | Stable override ID |
| `entity_type` | enum | Yes | `player`, `pick`, `team`, `league`, `source`, `model` |
| `entity_key` | string | Yes | Affected object |
| `season` | integer | No | Relevant season |
| `field_name` | string | Yes | Exact overridden field |
| `old_value` | string | No | Prior value, serialized |
| `new_value` | string | Yes | New value, serialized |
| `override_type` | enum | Yes | `data_correction`, `source_resolution`, `manual_entry`, `transcription_fix`, `league_rule_fix`, `parser_fix` |
| `reason_code` | enum | Yes | `official_error`, `parser_error`, `transcription_error`, `commissioner_ruling`, `ownership_reconciliation`, `injury_clarification`, `other` |
| `explanation_text` | string | Yes | Plain-language rationale |
| `evidence_source_id` | string | No | Supporting source link to `source_catalog.csv` |
| `requested_by` | string | Yes | Override author |
| `approved_by` | string | Yes | Approver; may equal requester in single-user mode |
| `self_approved` | boolean | Yes | Explicit self-approval marker |
| `applied_at_local` | datetime | Yes | Application time |
| `expires_at_local` | datetime | No | Optional expiration |
| `affects_scoring` | boolean | Yes | Whether score can change after recalculation |
| `review_status` | enum | Yes | `pending`, `approved`, `rejected`, `expired` |

**Validation rules**
- `field_name` must not target derived output columns such as `final_decision_score`, `confidence_score`, `recommended_range`, or `do_not_draft_before_pick`.
- `approved_by`, `explanation_text`, and either `evidence_source_id` or an explicit `reason_code=other` explanation are mandatory.
- Any approved override on an identity-critical field must trigger a rerun before the board is considered current.

**`model_run_metadata.csv`**

| Column | Type | Required | Description |
|---|---|---:|---|
| `run_id` | string | Yes | Stable run identifier |
| `run_mode` | enum | Yes | `rookie_board`, `veteran_board`, `draft_room`, `forced_release`, `trade_review`, `keeper_review`, `historical_audit` |
| `season` | integer | Yes | Relevant season |
| `league_id` | string | No | Local league identifier if present |
| `model_version` | string | Yes | Semantic model version |
| `scoring_profile_id` | string | Yes | e.g. `lve_1qb_noppr_fd04_v1` |
| `source_catalog_hash` | string | Yes | Hash of source catalog used |
| `input_bundle_hash` | string | Yes | Hash of input fixtures bundle |
| `overrides_hash` | string | Yes | Hash of active override set |
| `notes_hash` | string | No | Hash of active notes relevant to run |
| `executed_at_local` | datetime | Yes | Run time |
| `app_version` | string | Yes | App build/version |
| `git_commit` | string | No | Optional repo revision |
| `asset_count` | integer | Yes | Number of scored assets |
| `warning_count` | integer | Yes | Total warnings |
| `blocking_warning_count` | integer | Yes | Count of blockers |
| `run_status` | enum | Yes | `success`, `blocked`, `partial` |
| `blocked_reason` | string | No | Reason if blocked |
| `output_path` | string | No | Local path to generated output artifact |
| `runtime_notes` | string | No | Freeform run note |

**Validation rules**
- Every scored output table must carry a valid `run_id`.
- `model_run_metadata.csv` should be generated, not hand-edited.
- This file should normally be ignored in version control, along with any generated caches or data packs.

## Warnings, acceptance checklist, and rejected shortcuts

The warning layer should distinguish between **data quality**, **model quality**, and **decision readiness**. Official injury reports are formal availability inputs; market ranks are consensus opinion with revision dates; depth charts are more speculative and, in FantasyPros’ own words, may not match announced team charts. That makes it possible to be precise about what should merely lower confidence and what should actually stop a money decision. citeturn6view2turn13view0turn13view1turn8view2turn8view3turn6view5

### Warning classes

| Warning class | Trigger examples | User-facing rule | Score behavior |
|---|---|---|---|
| `data_warning` | Optional source stale, secondary feature missing, contract source old, depth chart spread wide | Show score, badge the row, reduce confidence modestly | Score allowed |
| `model_warning` | High disagreement among market/projection sources, unsupported note attached, too many neutral imputations | Show score, highlight confidence drop, require user review before trade action | Score allowed |
| `review_needed` | Handwritten note not verified, manual override self-approved on key field, conflicting market vs role evidence | Show score but require drill-down before acting | Score allowed |
| `decision_blocking` | Missing league-rank file in forced-release mode, unresolved pick ownership, duplicate asset key, stale league-state snapshot after known trade, unsupported override on critical field | Prevent export of “final” board and disable “decision-ready” badge | Score not decision-eligible |

### Final acceptance checklist before money decisions

A board should only be treated as decision-ready if all of the following are true:

- the current league-state snapshot is loaded and no known trade or declaration change has occurred since capture
- pick ownership is fully reconciled
- the active model version and scoring profile are explicitly shown
- all approved overrides have evidence, author, timestamp, and rerun coverage
- there are no blocking warnings
- the forced-release module is using the current summer league-rank source if release logic is active
- veteran/free-agent evaluation has a current transactions snapshot
- injury-sensitive veteran/free-agent rows inside the final pre-draft window have current enough injury evidence
- every public market or projection file stores its scoring context
- any handwritten-history input used in analysis has been transcribed and marked reviewed
- the board’s run metadata is saved locally and linked to the current output

### Rejected shortcuts and dangerous assumptions

These should be explicitly banned from the first shipping version:

- **Using public rank as truth.** ECR is expert consensus, not LVE truth, and FantasyPros’ published draft-accuracy study is based on half-PPR settings rather than your exact league. citeturn6view1turn8view6
- **Treating depth charts as authoritative role files.** FantasyPros says its depth charts are ECR-based and may not match team-announced charts; preseason depth charts are often described as unofficial. citeturn6view5turn10view0
- **Directly overriding final scores or draft ranges.** That destroys determinism and provenance.
- **Using missing = zero.** Missing data is uncertainty, not necessarily negative football evidence, and the broader literature warns that missingness can bias inference. citeturn10view4
- **Letting contracts drive fantasy role by themselves.** Contract data is contextual, not a substitute for actual role and availability.
- **Mixing stale and fresh sources without recording timestamps.** Freshness is a core data-quality dimension. citeturn10view2
- **Allowing runtime scraping or live APIs in final scoring.** That would violate the local-first requirement and break reproducibility.
- **Using handwritten league history directly as scored input before transcription and review.** It can inform context, but it is too error-prone to score raw.
- **Committing generated run outputs by default.** Generated metadata is useful for audit, but it should not become a hand-edited canonical input.
- **Counting the same uncertainty twice.** If completeness already penalizes missingness, do not stack a second generic missing-data penalty on top of it without a specific exception.