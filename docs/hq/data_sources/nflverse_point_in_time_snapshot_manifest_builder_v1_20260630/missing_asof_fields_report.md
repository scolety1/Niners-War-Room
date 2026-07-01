# Missing As-Of Fields Report

- `rosters`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Current roster status in display artifact lacks roster event/as-of timestamp.
- `weekly_rosters`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Weekly roster status lacks frozen season-week extraction/as-of proof.
- `injuries`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Injury report publication/as-of timing is not proven; missing injury is not healthy.
- `practice_status`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Practice status can leak late-week health/role information without publication timing.
- `depth_charts`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Depth chart publication timestamp and team/week context are not tracked.
- `schedules`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Schedule release/update timestamp and reschedule history are not tracked.
- `snap_counts`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Completed-game cutoff and lag policy are not tracked; missing snaps are not zero.
- `player_stats`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Player stats can overlap labels; sidecar/replay exclusion rules are not proven.
- `draft_picks`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Draft event/publication timestamp and post-draft anchor split are not tracked here.
- `combine`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Dataset health exists, but no row-level combine as-of manifest exists here.
- `contracts`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Contract context is display-only and cannot become value/trade/model input.
- `availability_denominator_artifact`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, point_in_time_snapshot_id; blocker: Denominator artifact is display-only; active/inactive hierarchy and games_missed remain blocked.
- `player_context_display_artifact`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Current display artifact is not historical replay proof.
- `identity_bridge_artifacts`: missing source_extraction_timestamp, publication_time_or_source_release_timestamp, feature_as_of_timestamp, point_in_time_snapshot_id; blocker: Identity bridge is prerequisite gating evidence, not a predictive feature.

No missing field is inferred from current display data. Missing as-of evidence remains blocked for replay.
