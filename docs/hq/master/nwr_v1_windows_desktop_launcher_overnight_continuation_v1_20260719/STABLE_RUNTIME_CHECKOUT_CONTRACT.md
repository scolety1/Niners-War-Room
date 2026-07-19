# Stable runtime checkout contract

Preferred location is `C:\NWR\Niners-War-Room-V1`. It is currently absent, so there is no path conflict. It was intentionally not created because canonical push/adoption and actual-user installation are blocked.

When authorized, the checkout must be a clean dedicated checkout of the final remote `work/hq-parallel-control`, contain no primary-worktree modifications or private LocalData, and have no sibling-worktree dependency. The shortcut must target its committed `scripts\nwr_desktop.py`; external state roots and validated ignored junctions must make checkout replacement data-neutral. Creation must stop with `BLOCKED_NWR_DESKTOP_LAUNCHER_STABLE_CHECKOUT_CONFLICT` if the location becomes populated or incompatible.
