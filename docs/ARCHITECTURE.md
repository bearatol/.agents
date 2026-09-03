# Architecture

.agents separates user-owned data from host-specific execution.

```text
Git-backed .agents workspace
   |
   +---- personal library: <any-type>/<name>
   |
   +---- neutral tasks, results, reviews, decisions
   |
   v
Stable CLI facade
   |
   +---- Codex adapter
   +---- Claude adapter
   +---- Gemini adapter
   +---- Kimi adapter
   +---- generic/future adapter
            |
            v
        host-specific execution
```

## Three layers

A normal installation keeps three ownership layers distinct:

- **System source** is the versioned project checkout. `catalog/catalog.json`,
  `catalog/catalog.schema.json`, `library/`, `profiles/`, and `scripts/` are
  canonical here.
- **Managed runtime** is `AGENTS_HOME`. Its top-level `skills/`, `agents/`,
  `orchestration/`, `tools/`, `catalog.json`, and `catalog.schema.json` are
  installed projections for hosts. Do not edit them directly; `status` and
  `doctor` report drift so it can be reviewed before an update.
- **Personal workspace** is `workspace/`. It contains user-owned reusable
  material and neutral team records, and should be kept in private Git when it
  contains private work.

Developers may use the project checkout itself as `AGENTS_HOME`. In that mode
the source and managed runtime share one directory, but their ownership remains
the same: `library/` and `catalog/` are canonical, while the generated
top-level runtime paths are ignored by Git.

## Activation registry

Hashes alone cannot say who is entitled to write a path, so a runtime that
several tools install into ends up with drift nobody can safely resolve. The
activation registry attributes every activated path to one owner, using records
that already exist: the canonical catalog, the personal workspace index, and
third-party lock files found inside `AGENTS_HOME`. Anything no record claims
stays `unknown` and untouched.

`scripts/registry.py` derives the registry on every run and writes nothing.
Its three commands are read operations. `report` lists ownership, trust, and
state. `plan` shows what an installation would change. `reconcile` shows the
paths that need a human decision, including names claimed by two records and
links that leave the runtime. Reasoning and trade-offs are recorded in
`docs/adr/0001-ownership-layers-and-activation-registry.md`.

`~/.agents` is a shared runtime with several writers, not this project's
private destination. The tool matches the community directory layout where
that is free, writes only paths it owns, and reports the rest.
`docs/adr/0002-shared-directory-sources-and-attested-packages.md` records the
decisions that follow from that: content moves to its own package repository,
sources become data with pinned and linked modes, identifiers are qualified
while installed names stay flat, removal and deactivation act only on owned
paths, and packages carry scan evidence bound to a content hash.

## Sources of truth

- `catalog/catalog.json` describes every component, agent capability, access
  level, skill policy, and advisory skill set. Its local
  `catalog/catalog.schema.json` constrains the catalog structure.
- `library/agents/` contains vendor-neutral canonical specialist prompts.
- `library/skills/` contains reusable methods loaded by CEO and subagents.
- `library/orchestration/` defines task, result, and state contracts.
- `profiles/` groups components for selective installation.
- `.ecosystem-profiles`, `.ecosystem-components`, and `.ecosystem-hosts` record
  the logical selection on one machine; they never contain credentials.
- The runtime `catalog.json` and sibling `catalog.schema.json` are managed
  copies for installed tools. Repository checks always use the canonical pair
  under `catalog/`.
- A user-exported environment lock is the portable, versioned description of
  that selection: schema version, ecosystem version, full commit SHA, profiles,
  explicit components, and hosts.
- Host adapters render small wrappers that point back to canonical prompts.
- `catalog/migrations.json` records canonical replacements for merged roles.
- `workspace/library/<type>/<name>/` is the open-ended personal data store.
  Storage accepts future types without assigning them executable meaning.
- `workspace/projects/` is the vendor-neutral collaboration log. Each task
  attempt, worker result, peer review, and coordinator decision is immutable.

## Facade and adapters

The human interface expresses intent: set up one or more applications, connect
them, store reusable material, or coordinate a team. A host adapter translates
only the connection step into paths and wrapper formats documented by that
host. The library and team records do not depend on those formats.

Adapter descriptions are declarative. They cannot contain commands, URLs,
environment variables, or filesystem destinations. Only trusted adapter code
may activate a built-in ID. An unknown future host can still read the generic
files and neutral task packets without changing the storage layer.

This is the Facade pattern: callers use one stable interface while adapters may
evolve independently behind it.

## Multi-host collaboration

A specialist role and an AI host are different identities. For example,
`engineer` may be performed by Claude today and Codex tomorrow. The task record
therefore stores both the role and the worker host. Reviewers write separate
files, and only the recorded coordinator writes the final decision.

Attempt numbers prevent stale work from being accepted after a retry. Exclusive
creation and atomic replacement prevent partial JSON and silent overwrite.
Host names provide attribution, not authentication; operating-system and Git
permissions enforce access.

## Why skills remain autonomous

The CEO knows project dependencies but a specialist knows its own method. The
CEO therefore recommends skills while each subagent makes the final selection.
The result packet makes that choice observable without centralizing expertise.

Progressive disclosure keeps the context small: agents scan IDs, descriptions,
tags, and capabilities first; they read complete `SKILL.md` files only after
selection, and task-relevant references only when required by that skill.

Skills never change the task's scope or permissions. Subagents cannot spawn
other subagents; additional expertise returns to the CEO for a new assignment.
Independent security controls may deliberately disable optional skills to keep
their review boundary stable.

## Trust boundary

The catalog and prompts express policy but cannot grant host permissions. The
host sandbox, tool allowlist, user approvals, and project rules remain the
enforcement layer. Generated wrappers use the access level declared for each
agent and preserve conflicting user configuration.

Environment locks are untrusted declarative input. They cannot specify paths,
repositories, URLs, commands, environment variables, overwrite behavior, or
network destinations. Restore validates logical IDs and provenance, preflights
managed and host targets, and derives all destinations from trusted code. Git
fetch, checkout, downgrade, credentials, host applications, plugins, and model
weights remain outside the restore boundary.

Personal imports are untrusted instructions. The importer rejects common
secret and model artifacts, unsafe paths, links, special files, excessive size,
and overwrites. New items remain inactive until an explicit checksum-based trust
decision. Trust never grants permission to execute code or use the network.
