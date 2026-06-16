import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.preview_rookie_final_manual_draft_kit import BANNER, FILES, build_static_html  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_static_preview_builds_required_views() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        kit = root / "kit"
        preview = kit / "preview"
        rows = [
            {
                "rank": "1",
                "tier": "tier_1_priority_target",
                "player": "Target Player",
                "position": "WR",
                "draft_action": "target",
                "warning_severity": "none",
            }
        ]
        for filename in FILES.values():
            write_csv(kit / filename, rows)

        html_path = build_static_html(kit, preview)
        text = html_path.read_text(encoding="utf-8")

        assert html_path.exists()
        assert BANNER in text
        assert "Final board" in text
        assert "Draft-day quick sheet" in text
        assert "Warning-priority sheet" in text
        assert "positionFilter" in text
        assert "warningFilter" in text


if __name__ == "__main__":
    test_static_preview_builds_required_views()
    print("rookie_final_manual_draft_kit_preview direct harness passed")
