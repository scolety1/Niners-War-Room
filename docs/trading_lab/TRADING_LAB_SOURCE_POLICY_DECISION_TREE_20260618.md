# Trading Lab Source Policy Decision Tree

Date: 2026-06-18

## Decision Tree

1. Is the source a public manual reference?
   - Yes: continue to attribution and storage review.
   - No: continue to private/paid review.

2. Are terms, license, attribution, and storage expectations clear?
   - Yes: ACCEPT for manual paper/research use.
   - No: HOLD for manual review.

3. Is the source paid, private, or a data dump?
   - Yes: HOLD unless a future explicit approval exists.
   - No: continue.

4. Does the source include broker credentials, account keys, secrets, private
   brokerage exports, private account balances, or real-money execution data?
   - Yes: REJECT.
   - No: continue manual source review.

## Outcomes

- ACCEPT public manual reference.
- HOLD terms unclear.
- REJECT private broker/account source.
- REJECT credential/secret source.
- HOLD paid/private data source unless future explicit approval exists.

## Boundary

This decision tree does not approve data ingestion, market-data fetching,
redistribution, generated outputs, legal conclusions, or trading execution.
