---
name: find-skills
description: Discover an installed, cataloged, or safely obtainable capability.
---

# Find Skills

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
