# TSF build blueprint

| Task | Branch | Tests/gate | Build |
| --- | --- | --- | --- |
| 2A snapshots/availability | `feature/phase2a-sleeper-substrate-v1` | fixture + cache/failure/privacy tests; owner read-only check | No |
| 2B Redraft ROS/weekly | `feature/phase2b-redraft-ros-weekly-v1` | retrospective/stale/sample tests; owner evidence review | No |
| 2C waiver/lineup/streamers | `feature/phase2c-redraft-weekly-actions-v1` | legal-slot/property/add-drop/availability tests; weekly walkthrough | No |
| 2D Dynasty movement | `feature/phase2d-dynasty-inseason-v1` | authority-drift and scenario tests; owner review | No |
| 3 Trade Finder | `feature/trade-finder-v1` | bounded search/pick ownership/two-team evidence tests | No |
| 4 acceptance | `release/nwr-complete-product-v1` | full smoke/install/state-receipt gates | Yes, serialized |

Stop on missing provider terms, stale inputs without fallback, identity collision, authority drift, illegal roster result, owner-state mismatch, or unapproved source. Use high reasoning for architecture/calibration and normal implementation models for deterministic code.
