# Agent Ecosystem

A portable, selective toolkit of original English-language skills, subagent
prompts, operating rules, and local-model setup helpers. It installs into the
shared `~/.agents` directory so multiple AI coding and writing tools can use
one source of truth.

The repository contains no model weights, credentials, virtual environments,
or republished unlicensed prompts.

## Quick start

```bash
git clone https://github.com/bearatol/agent-ecosystem.git
cd agent-ecosystem
./scripts/bootstrap.sh
```

For a non-interactive installation:

```bash
./scripts/install.sh --profile core --profile marketing --host codex --host claude
./scripts/doctor.sh
```

Ask any compatible agent:

```text
Read CONNECT.md in this repository. Help me choose the smallest profiles for
my work, install them into ~/.agents, connect my agent hosts, and run doctor.
Do not overwrite existing files without asking.
```

## Profiles

| Profile | Purpose |
| --- | --- |
| `core` | Governance, routing, discovery, and natural writing |
| `marketing` | 23 original marketing capabilities and a marketer subagent |
| `design` | Product UI/UX workflow and design reviewer |
| `video` | Remotion planning and implementation workflow |
| `context` | Context budgeting, compression, and handoff practices |
| `local-models` | Documentation and scripts; never model weights |
| `all` | Every maintained profile |

List exact contents with `./scripts/list.sh`.

## Design principles

- Install only what the user selects.
- Keep `~/.agents` vendor-neutral and portable.
- Prefer original skills over copied prompt collections.
- Preserve user files; conflicts require an explicit `--force`.
- Pin or document external dependencies rather than hiding them.
- Keep secrets, model weights, caches, and machine-specific paths out of Git.
- Treat catalog metadata as the source of truth and update it with every
  component change.

See [CONNECT.md](CONNECT.md), [SECURITY.md](SECURITY.md), and
[CONTRIBUTING.md](CONTRIBUTING.md).
