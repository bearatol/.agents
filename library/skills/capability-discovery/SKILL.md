---
name: capability-discovery
description: Discover an installed, cataloged, or safely obtainable capability.
---

# Capability Discovery

Use when the requested capability is not already known.

Search in this order:

1. Installed entries in `~/.agents/catalog.json` and `~/.agents/skills`.
2. Profiles and original components in the Agent Ecosystem repository.
3. Official registries or upstream repositories, only with user-approved
   network access.

For every candidate report its purpose, source, version or commit, license,
required tools, network behavior, compatible hosts, and maintenance status.
Reject packages with unclear provenance, hidden executables, credential
requests unrelated to function, or no permission to redistribute.

Prefer referencing and pinned installation over copying. If no safe candidate
exists, propose an original minimal skill based on functional requirements.

A subagent may use an already installed safe candidate without asking the CEO.
It must not install, download, publish, or enable network access unless the task
and user approvals already permit that action. Report missing capabilities and
approval needs through `skill_gaps`; do not expand the task to obtain them.
