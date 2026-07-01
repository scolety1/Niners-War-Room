# Future Tuning Readiness Report V2

Future formula tuning remains not production-viable.

V2 is materially better than V1 because it restores the runtime path, expands the historical window, and null-fences optional source fields. It is sufficient for a future human-reviewed exploratory tuning substrate, but not for production formula changes.

Before formula search resumes:

- Review source zero semantics for core seasonal stat fields.
- Decide whether null-fenced optional fields should be used or excluded.
- Add typed historical red-zone sidecar only if source semantics are proven.
- Keep all candidate outputs review-only.
