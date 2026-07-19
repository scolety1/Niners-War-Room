# Route registration and resolution review

Before: the same `NavigationPageSpec` represented both the default root and `/draft-cockpit-root`. Streamlit ignored the named URL of that default page, so a direct request displayed its active Page Not Found dialog and fell back to `/`.

After:

- `DEFAULT_ROOT_PAGE`: hidden, `default=True`, empty URL, physical wrapper `pages/46_draft_cockpit_default_root.py`.
- `/draft-cockpit-root`: hidden, `default=False`, physical wrapper `pages/44_draft_cockpit_root.py`.
- Both wrappers delegate to `pages/21_live_draft_room_v1.py`.
- `registered_route_spec()` requires exactly one named registration and rejects any named route that is also the default.

Browser result: `/draft-cockpit-root` stayed at `/draft-cockpit-root` at 375 x 812, 768 x 1024, and 1440 x 1000. It rendered one `Draft Cockpit` H1, no dialog, no Page Not Found, no traceback, and no root overflow. Root `/` continued to render the same owner. The pre-existing `/drafting-mode-root` compatibility redirect to `/draft-cockpit` is intentional and is the only route-agreement exception in the 180-case matrix.
