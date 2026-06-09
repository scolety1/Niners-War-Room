from __future__ import annotations

from pathlib import Path


def path_fingerprint(path: str | Path) -> tuple[str, int, int, int]:
    root = Path(path).resolve()
    if root.is_file():
        stat = root.stat()
        return (str(root), stat.st_mtime_ns, 1, stat.st_size)
    if not root.exists():
        return (str(root), 0, 0, 0)

    latest_mtime = 0
    file_count = 0
    total_size = 0
    for file_path in sorted(root.rglob("*")):
        if not file_path.is_file():
            continue
        stat = file_path.stat()
        latest_mtime = max(latest_mtime, stat.st_mtime_ns)
        file_count += 1
        total_size += stat.st_size
    return (str(root), latest_mtime, file_count, total_size)
