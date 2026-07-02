# Screenshots Or Route Smoke Report

## Focused Checks Completed

Command:

```powershell
uv run --with pytest --with ruff python -m pytest tests/test_evidence_review_hub_page.py tests/test_navigation_compression.py tests/test_evidence_integration_review_page.py
```

Result: `25 passed`

Command:

```powershell
uv run --with pytest --with ruff python -m ruff check src/services/evidence_review_hub_service.py app/pages/45_evidence_review_hub_v1.py app/navigation.py tests/test_evidence_review_hub_page.py tests/test_navigation_compression.py
```

Result: `All checks passed`

## Route Smoke

Command:

```powershell
uv run --with pytest --with ruff python -c "from streamlit.testing.v1 import AppTest; at = AppTest.from_file('app/pages/45_evidence_review_hub_v1.py'); at.run(timeout=20); print('exceptions=' + str(len(at.exception))); [print(e) for e in at.exception]"
```

Result: `exceptions=0`

Route covered:

- `/evidence-review-hub`

Observed warnings: existing Streamlit `use_container_width` deprecation warnings only.

## Additional Validation

Command:

```powershell
uv run --with pytest --with ruff python -m compileall app src tests
```

Result: passed

Command:

```powershell
git diff --check
```

Result: passed; only Git line-ending warnings for existing Windows behavior.

Command:

```powershell
git diff --cached --check
```

Result: passed with nothing staged.

Command:

```powershell
protected path/source-truth scan
```

Result: `PROTECTED_SCAN_CLEAN`

Command:

```powershell
forbidden raw/shared/cache/local/secrets tracked-path scan
```

Result: `FORBIDDEN_TRACKED_PATH_SCAN_CLEAN`

Command:

```powershell
banned active-language scan over touched app/service files
```

Result: `BANNED_ACTIVE_LANGUAGE_SCAN_CLEAN`

Command:

```powershell
approval/non-promotion scan over touched app/service/test files
```

Result: `APPROVAL_NON_PROMOTION_SCAN_CLEAN`

## Notes

No screenshots were required by the lane.
