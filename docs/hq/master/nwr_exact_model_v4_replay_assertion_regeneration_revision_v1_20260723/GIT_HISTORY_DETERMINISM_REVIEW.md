# Git history determinism review

Canonical Git evidence uses only history reachable from fixed source commit
`0929ce6ec058a698efeee10fe5770f56047bab21`. Pickaxe hits are sorted and record
exact commit IDs. Source commits are resolved with `git log -1 <fixed> --
<path>`.

`git log --all`, `git rev-list --all`, local branch enumeration, active branch
names, remote-tracking labels, mutable remotes, usernames, and absolute
worktree paths are excluded from canonical output. A non-authoritative branch
metadata probe changes no governed byte.
