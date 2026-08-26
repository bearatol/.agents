# Architecture

Agent Ecosystem separates portable expertise from host-specific execution.

```text
User goal
   |
   v
CEO agent ---- catalog v2 ---- skills
   |
   +---- task packet ---- specialist subagent
                              |
                              +---- self-selected skills
                              |
                              +---- result packet + evidence
   |
   v
Integration and acceptance
```

## Sources of truth

- `catalog/catalog.json` describes every component, agent capability, access
  level, skill policy, and advisory skill set.
- `library/agents/` contains vendor-neutral canonical specialist prompts.
- `library/skills/` contains reusable methods loaded by CEO and subagents.
- `library/orchestration/` defines task, result, and state contracts.
- `profiles/` groups components for selective installation.
- Host adapters render small wrappers that point back to canonical prompts.

## Why skills remain autonomous

The CEO knows project dependencies but a specialist knows its own method. The
CEO therefore recommends skills while each subagent makes the final selection.
The result packet makes that choice observable without centralizing expertise.

Skills never change the task's scope or permissions. Subagents cannot spawn
other subagents; additional expertise returns to the CEO for a new assignment.
Independent security controls may deliberately disable optional skills to keep
their review boundary stable.

## Trust boundary

The catalog and prompts express policy but cannot grant host permissions. The
host sandbox, tool allowlist, user approvals, and project rules remain the
enforcement layer. Generated wrappers use the access level declared for each
agent and preserve conflicting user configuration.
