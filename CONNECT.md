# Connect This Ecosystem

This file is the entry point for humans and AI agents.

## Instructions for an AI agent

1. Read `catalog/catalog.json` and the requested profile files.
2. Ask what kind of work the user does and which hosts they use.
3. Recommend the smallest sufficient set of profiles and components.
4. Show the exact install command before running it.
5. Run `scripts/install.sh` only with the user's selected profiles.
6. Run `scripts/connect.sh` for explicitly selected hosts.
7. Run `scripts/doctor.sh` and report conflicts or missing dependencies.
8. Never install model weights, packages, or network services implicitly.
9. Never overwrite an existing file unless the user approves `--force`.
10. After changing the ecosystem, update the catalog, profile membership,
    documentation, and tests in the same change.

## Human commands

```bash
./scripts/list.sh
./scripts/install.sh --profile core --profile marketing
./scripts/connect.sh --host codex --host claude
./scripts/doctor.sh
```

The default destination is `${AGENTS_HOME:-$HOME/.agents}`. Override it for a
test or isolated installation:

```bash
AGENTS_HOME=/tmp/agent-ecosystem-test ./scripts/install.sh --profile core
```

## Supported host adapters

- `codex`: links installed skills into `~/.codex/skills`.
- `claude`: links installed skills into `~/.claude/skills`.
- `gemini`: links installed skills into `~/.gemini/skills`.
- `generic`: uses `~/.agents` directly; tell the host to read its `AGENTS.md`.

Adapters create only managed skill links. They do not overwrite a host's
global instruction file. This avoids silently replacing personal rules.
