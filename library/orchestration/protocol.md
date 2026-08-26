# Skill-aware Orchestration Protocol

This protocol defines how a CEO coordinates specialist subagents without
removing their professional autonomy.

## Roles

- The user owns goals, approvals, and irreversible decisions.
- The CEO owns decomposition, agent recommendations, dispatch, integration,
  verification, and project state.
- A subagent owns its bounded specialist task and independently selects the
  skills needed to complete it.
- A skill supplies method or knowledge. It never grants permissions, expands
  scope, or changes ownership.

## CEO loop

1. Read the catalog and current project state.
2. Define the outcome, acceptance evidence, constraints, and non-goals.
3. Build a dependency-aware task graph.
4. Recommend the smallest capable subagent for each task. Recommend skills as
   non-binding hints, not mandatory selections.
5. Create a task packet and dispatch it through the host's native subagent
   mechanism.
6. Track task state as `ready`, `running`, `review`, `complete`, or `blocked`.
7. Validate every result packet, evidence item, and acceptance criterion.
8. Integrate accepted results and record decisions or reusable improvements.

The CEO must not fabricate work, report a task as complete from a status
message alone, or delegate the final acceptance decision.

## Subagent skill selection

Before specialist work, every subagent must:

1. Read the installed catalog and the assigned task packet.
2. Identify every skill that could materially improve the result.
3. Select all relevant skills that fit the task scope and available context.
4. Load and follow each selected `SKILL.md` completely.
5. Resolve conflicting skill instructions by preserving the task packet,
   permissions, repository rules, and user decisions in that order.
6. Record `skills_considered`, `skills_applied`, and `skill_gaps` in the result.

The CEO's skill recommendations are advisory. A subagent may add or omit a
skill when it explains the reason. A subagent may not use a skill to access
new data, tools, paths, networks, or permissions that the task did not grant.
Independent control-plane reviewers may use a stricter fixed method and no
optional skills when their canonical prompt requires that isolation.

## Delegation boundary

Subagents do not delegate to other subagents. If additional expertise is
needed, the subagent returns a `blocked` or `needs_specialist` result to the
CEO with a precise recommendation. This prevents recursive teams, duplicated
work, and unclear ownership.

## Minimum evidence

A completed result must contain the outcome, artifacts, verification evidence,
skills applied, residual risks, and any assumptions that remain unverified.
