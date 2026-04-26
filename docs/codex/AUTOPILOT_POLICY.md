# Autopilot Policy

Status: APPROVED
Spending Limit: 0
Customer Data: no live customer data; local sample and user-provided league CSV snapshots only
Escalation: human review required for reputation, money, user trust, production deploys, auth, payments, secrets, migrations beyond local SQLite, legal text, mass email, data deletion, pricing changes, external APIs, scraping

## Safe Automatic Lanes

- deterministic model code
- local CSV validation
- local SQLite schema/test hardening
- Streamlit table UI
- docs updates
- test-backed bug fixes
- staging report generation

## Human Approval Required

- pricing changes
- production deploys
- payment behavior
- auth or permission changes
- mass emails
- deletion of user data
- legal or compliance text
- external runtime APIs
- web scraping
- package or dependency changes
