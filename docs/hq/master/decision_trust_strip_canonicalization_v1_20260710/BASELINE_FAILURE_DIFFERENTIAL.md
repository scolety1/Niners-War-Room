# Baseline Failure Differential

Command on clean HQ and source implementation:

`python -m pytest tests/test_trust_banner_ui.py -q`

Both runs produced `2 failed, 3 passed` in 0.08 seconds.

Identical failing tests:

1. `test_decision_pages_render_one_primary_trust_banner`
2. `test_main_model_pages_show_required_review_only_banner`

Both stop at unchanged `app/pages/05_rankings.py`, whose complete content remains:

```python
from __future__ import annotations

from app.main import main

main()
```

The first assertion expects one literal `render_page_trust_banner(` call and finds zero. The second expects a literal banner call or banner text in the wrapper and finds neither. Stack location and assertion messages are materially identical.

`app/pages/05_rankings.py` has no source-commit diff. `tests/test_trust_banner_ui.py` is unchanged. No skip, xfail, assertion removal, or weakening occurred. The source adds no new failure.

Result: `ACCEPTED_IDENTICAL_PRE_EXISTING_BASELINE_FAILURES`.
