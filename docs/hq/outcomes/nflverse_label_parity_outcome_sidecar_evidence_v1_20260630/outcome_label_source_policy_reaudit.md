# Outcome Label Source Policy Reaudit

Verdict: `NO_LABEL_PROMOTION`

## Existing Outcome Labels

Existing Outcome V2 labels remain review/evaluation targets. They are not input features, rank drivers, source-truth gates, or app decision logic.

Outcome V2 first-down scoring status and label exactness remain governed by the existing Outcome V2 documentation. This packet does not alter those definitions.

## NFLVerse Player Stats

NFLVerse `player_stats` may be evaluated as a future sidecar comparison source. It is not currently approved as:

- label truth;
- training truth;
- model input;
- source truth;
- active app output;
- ranking logic.

A later label-parity gate must prove scoring parity, identity parity, season coverage, position coverage, and missingness behavior before any label-source change can be considered.

## Rookie Outcomes

Rookie Outcome remains blocked from active probability use. This packet does not approve Rookie Gate G, UDFA modeling, CFBD model input, or active rookie outcome columns.

Drafted-only review artifacts may remain review-only. NFLVerse `player_stats` can help a future sidecar audit for players with NFL seasons, but it does not make college-only or UDFA assumptions safe.

## Labels Are Not Features

Outcome labels, sidecar labels, and parity outcomes must not be used as model inputs. A future model feature gate would need to evaluate factual pre-outcome features separately from target labels.

## Missingness and Censoring

- Missing labels are `Not enough information`.
- Missing sidecar rows are `Not enough information`.
- Incomplete forward windows are right-censored.
- Censored windows are not misses.
- Missing data must never be converted to `0%`, false, healthy, clean, or low risk.

## Vendor and Local Labels

RotoWire, local, vendor-derived, or display-only artifacts remain local-review/display-only unless a separate explicit policy gate approves a different use. This packet does not approve any vendor-derived source for label truth, training, or model input.
