# Frozen comparator contract

The frozen 2026 comparator is governed by:

- exact tracked SHA-256
  `b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179`;
- exact 35-column schema;
- 924 rows;
- nonblank exact player IDs;
- governed score and ranking fields;
- target/feature season and freeze/as-of metadata;
- input source dates, hashes, and source status;
- tracked row order.

Score, rank, player ID, added row, removed row, governed reorder, and
source/as-of changes all fail. The canonical current board remains 240 rows at
SHA-256 `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`.

Production ranking change: `NONE`. Frozen 2026 change: `NONE`.
