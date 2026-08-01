"""Create and verify the governed Personal Workspace pre-launch backup."""

from __future__ import annotations

import json

from src.services.personal_workspace_service import (
    create_workspace_backup,
    preview_workspace_restore,
)


def main() -> int:
    result = create_workspace_backup()
    preview = preview_workspace_restore(result.path) if result.path else None
    valid = bool(preview and preview.valid)
    print(
        json.dumps(
            {
                "status": "PRE_LAUNCH_BACKUP_VERIFIED" if valid else "PRE_LAUNCH_BACKUP_FAILED",
                "path": str(result.path or ""),
                "file_count": result.file_count,
                "manifest_sha256": result.manifest_sha256,
            },
            sort_keys=True,
        )
    )
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
