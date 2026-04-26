# Maintenance Windows

Fleet may perform low-risk maintenance during unattended runs.

- Window: local development only
- Allowed lanes: bugs, tests, docs, performance, debt, validation hardening
- Disallowed without human approval: package changes, production deploys, auth, payments, secrets, migrations beyond local SQLite, external APIs, scraping
