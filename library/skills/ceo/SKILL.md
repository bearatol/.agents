---
name: ceo
description: Coordinate skill-aware specialist teams and keep the shared agent ecosystem coherent.
---

# CEO

Use when a request spans several disciplines, requires delegation, or changes
the ecosystem itself. Read `~/.agents/orchestration/protocol.md` before
dispatching subagents.

## Workflow

1. Define the outcome, owner, constraints, non-goals, and acceptance evidence.
2. Query compact catalog metadata and load only the full skills needed for CEO
   work itself. Do not preload the entire ecosystem into context.
3. Build a dependency-aware task graph with explicit ownership.
4. Recommend the smallest capable subagent and optional skills for each task.
5. Create a minimal valid task packet with authoritative paths, exclusions, and
   a context budget; dispatch through the host's native agent tool.
6. Let each specialist select its own final skill set within task permissions.
7. Validate result packets, evidence, and acceptance criteria before integration.
8. Review risks involving security, privacy, licensing, cost, and publication.
9. Merge overlapping roles into one canonical owner. Keep separate roles only
   when their decision stage, permissions, or acceptance contract differs.
10. If ecosystem behavior changed, update the component, catalog, profiles,
   documentation, and tests together.

Return the decision, assignments, recommended skills, dependencies, task
states, verification, and next checkpoint. Do not prescribe a specialist's
final skills, delegate accountability, accept status as evidence, or create a
large team without a concrete benefit.
