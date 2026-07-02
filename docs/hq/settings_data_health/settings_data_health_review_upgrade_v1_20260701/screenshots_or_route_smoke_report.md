# Screenshots Or Route Smoke Report

Route smoke target:

- `/settings-data-health`
- Source page: `app/pages/28_settings_data_health_v1.py`

Expected route checks:

- Page imports without exception.
- AppTest renders the existing Settings / Data Health page.
- New review-only section labels are visible:
  - Artifact Health Board
  - Source Contract Summary
  - Dataset Availability
  - Guardrail Status
  - What Can Safely Be Used Today?
  - What Is Still Blocked?

Screenshot capture is not required for this docs/service lane; AppTest route smoke is sufficient.
