from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main(argv: list[str] | None = None) -> int:
    from src.services.mock_draft_operator_session import (
        create_practice_session,
        draft_history,
        list_available_assets,
        load_session_state,
        mark_asset_drafted,
        render_operator_status,
        save_session_state,
        undo_last_pick,
        upcoming_my_picks,
        validate_operator_session,
    )

    parser = argparse.ArgumentParser(description="Fixture-only Mock Draft operator practice.")
    parser.add_argument(
        "command",
        choices=("status", "available", "draft", "undo", "history", "upcoming", "validate", "demo"),
    )
    parser.add_argument("--asset-id", default="")
    parser.add_argument("--state-path", default="")
    args = parser.parse_args(argv)

    session = (
        load_session_state(args.state_path)
        if args.state_path and Path(args.state_path).exists()
        else create_practice_session()
    )

    print("Mock Draft fixture-only practice operator")
    print("No real inputs read. No real simulation run.")

    if args.command == "status":
        print(render_operator_status(session))
    elif args.command == "available":
        for row in list_available_assets(session):
            print(
                f"{row['display_order']}. "
                f"{row['asset_id']} | {row['player']} | {row['position']}"
            )
    elif args.command == "draft":
        if not args.asset_id:
            parser.error("draft requires --asset-id")
        session = mark_asset_drafted(session, args.asset_id)
        print(f"Drafted fixture asset: {args.asset_id}")
        print(render_operator_status(session))
    elif args.command == "undo":
        session = undo_last_pick(session)
        print("Undid last fixture pick.")
        print(render_operator_status(session))
    elif args.command == "history":
        rows = draft_history(session)
        if not rows:
            print("History: none")
        for row in rows:
            print(f"{row['pick_label']} | {row['asset_id']} | {row['player']}")
    elif args.command == "upcoming":
        for row in upcoming_my_picks(session):
            marker = "NEXT" if row["is_next"] else "LATER"
            print(f"{marker}: {row['pick_label']} | {row['owner']}")
    elif args.command == "validate":
        validate_operator_session(session)
        print("Operator session validation: GREEN")
    elif args.command == "demo":
        print(render_operator_status(session))
        print("Available before pick:")
        for row in list_available_assets(session, limit=2):
            print(f"- {row['asset_id']} | {row['player']}")
        session = mark_asset_drafted(session, "fixture:rookie_a")
        print("Manual fixture draft: fixture:rookie_a")
        print("History after pick:")
        for row in draft_history(session):
            print(f"- {row['pick_label']} | {row['player']}")
        session = undo_last_pick(session)
        print("Undo complete.")
        validate_operator_session(session)
        print("Operator session validation: GREEN")

    if args.state_path:
        save_session_state(session, args.state_path)
        print(f"Saved fixture-only state: {args.state_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
