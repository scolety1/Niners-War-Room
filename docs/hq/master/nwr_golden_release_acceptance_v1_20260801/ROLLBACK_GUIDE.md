# Rollback Guide

The Golden Release is a normal fast-forward on `work/hq-parallel-control`.
Recovery uses the existing governed backup and restore contracts; perform a
restore dry-run before any real restore. Do not rewrite Git history, overwrite
canonical source files, or bypass hash validation. If application rollback is
needed, launch the last verified canonical commit in an isolated checkout and
preserve all user-state and receipt directories.
