# Rollback Plan

The revision is one local successor commit based directly on
`e94960fa81195e92b332db6beef3229056c7d968`. It is not merged and not pushed.

Before HQ adoption, rollback is simply abandoning the successor branch/worktree; the source
and blocked review evidence remain intact. If HQ later adopts the correction, revert the one
successor commit with a normal non-force revert. Do not delete or rewrite either historical
packet.

Receipt storage is ignored local runtime state. Code rollback must not copy, migrate, infer,
or promote any unsupported v1 receipt. Existing v1 bytes remain unsupported and require a
separate explicit maintenance decision. No production dataset rollback is needed because
this lane changes no source or production data.
