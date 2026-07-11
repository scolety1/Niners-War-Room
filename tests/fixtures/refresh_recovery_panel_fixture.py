from app.components.refresh_recovery_panel import render_refresh_recovery_panel
from src.services.refresh_recovery_presentation_service import build_refresh_recovery_presentations

FIXTURES = (
    {"source_name": "Success", "action_type": "REFRESHED", "refreshed": True},
    {"source_name": "Partial", "headline_status": "partial_success"},
    {"source_name": "Stale", "freshness_status": "stale"},
    {"source_name": "Skipped", "action_type": "SKIPPED_BY_POLICY"},
    {"source_name": "Unavailable", "execution_status": "blocked_config"},
    {"source_name": "Gated", "execution_status": "blocked_policy"},
    {"source_name": "Failed", "action_type": "FAILED", "runner_path": "diagnostic.txt"},
    {"source_name": "Unknown"},
)

render_refresh_recovery_panel(build_refresh_recovery_presentations(FIXTURES))
