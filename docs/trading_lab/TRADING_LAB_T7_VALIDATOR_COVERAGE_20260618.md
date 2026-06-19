# Trading Lab T7 Validator Coverage

Date: 2026-06-18

| artifact | ACCEPT coverage | REJECT coverage | HOLD coverage |
| --- | --- | --- | --- |
| Source inventory | Public source metadata | Prohibited source categories, broker/API text, secret config | Terms/storage uncertainty remains manual |
| Research intake | Required fake paper fields | Advice, execution, broker, secret, private account, data workflow text | Incomplete source review remains manual |
| Manual lifecycle | Required fake lifecycle fields | Invalid text implying execution, broker, private account, data workflow | Transition-policy uncertainty remains manual |
| Watchlist note | Required paper-only fields | Advice/execution/broker/private-account text | Missing public sources can remain manual HOLD by status |
| Strategy note | Required fake strategy fields | Advice/execution/broker/secret/data workflow text | Evidence uncertainty remains manual |
| Risk journal | Required fake risk fields | Real account, broker, execution, advice text | Severity/probability uncertainty remains manual |
| Paper journal | Required fake paper fields | Execution, private account, secret-like values | Review-status detail remains manual |
| Manual review packet | Required review fields | Advice, execution, broker, secret, private account, data workflow text | Source terms uncertainty remains manual |

T7 validators are pure in-memory checks. They do not create data files,
generated outputs, orders, signals, app wiring, or deployment paths.
