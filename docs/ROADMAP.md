# Roadmap

The current milestone is a dependable CLI, portable library, multi-host
adapters, and neutral team records. The next layers should preserve those file
contracts rather than replace them.

## Next

- Explicit activation and adapter capability mapping for personal rules,
  prompts, skills, specialists, model settings, and MCP descriptions.
- Import previews, safer update workflows, history, provenance, and migrations.
- Easier Git synchronization and conflict guidance without storing credentials.
- More trusted adapters implemented behind the same facade.

## Later

- A local browser UI for setup, library browsing, trust review, adapter status,
  team boards, and recovery. The CLI remains the automation API underneath it.
- A desktop application for people who do not want to use a terminal.
- A graph of artifacts, tasks, evidence, decisions, and dependencies.
- Context packs and graph-based retrieval that reduce repeated tokens while
  preserving authoritative sources and review evidence.
- Optional local orchestration that launches several approved hosts, observes
  budgets, and requires explicit permissions for writes or network use.

No roadmap item may turn declarative adapter data into arbitrary commands,
store account secrets in Git, or silently activate imported instructions.
