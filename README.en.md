# Agent Ecosystem

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

An original toolkit of skills, subagents, shared rules, and scripts managed
through one global `~/.agents` directory. Select only the profiles you need and
connect them to Codex, Claude Code, Gemini, or another AI agent.

The repository contains no model weights, secrets, virtual environments,
caches, or republished skills with unclear licensing.

## What you get

- 23 marketing skills covering research, positioning, copy, email, ads,
  content, CRO, and campaign launches;
- a natural-writing workflow that removes bureaucratic and canned language;
- a UI/UX process from user flow to design system;
- video planning and implementation with React and Remotion;
- context engineering for compact prompts and reliable handoffs;
- CEO, marketer, design reviewer, video producer, and context engineer
  subagents, plus engineer, QA reviewer, and product editor;
- a conflict-safe selective installer, diagnostics, and host adapters;
- local MLX documentation and setup helpers without model weights.

## Install on a new computer

You need Git, Bash, Python 3, and macOS or Linux.

```bash
git clone https://github.com/bearatol/agent-ecosystem.git
cd agent-ecosystem
./scripts/bootstrap.sh
```

The interactive bootstrap lists available profiles, asks what to install, and
offers to connect selected AI tools. Files are installed into `~/.agents` by
default.

For a non-interactive installation:

```bash
./scripts/install.sh \
  --profile core \
  --profile marketing \
  --host codex \
  --host claude
```

Verify the result:

```bash
./scripts/doctor.sh
```

## Let an agent install it

After cloning, send this request to any agent:

```text
Read CONNECT.md in this repository. Help me choose the smallest profiles for
my work, install them into ~/.agents, connect my agent hosts, and run doctor.
Do not overwrite existing files without asking.
```

The agent should inspect the catalog, recommend the smallest useful set, and
show the exact command before running it.

## Profiles

| Profile | Contents |
| --- | --- |
| `core` | CEO, routing, skill discovery, shared rules, and natural writing |
| `marketing` | 23 marketing skills and the marketer subagent |
| `design` | UI/UX skill and design reviewer |
| `video` | Remotion skill and video producer |
| `context` | Context engineering skill and subagent |
| `software` | Engineer, QA reviewer, software delivery, and quality review |
| `content` | Product editor and skills for documentation and content |
| `local-models` | Documentation and MLX helpers only; no models |
| `all` | Every maintained profile |

Inspect exact contents:

```bash
./scripts/list.sh
./scripts/list.sh --profile marketing
```

Install one component:

```bash
./scripts/install.sh --component skill:copywriting
```

## CEO and subagents

The CEO reads the catalog, applies its own skills, decomposes the goal, and
recommends specialists. Skill recommendations are advisory: every subagent
independently selects all useful skills within its task and permissions, then
reports what it considered and applied.

The security reviewer is deliberately isolated from optional skills so that a
reviewed component cannot weaken the control that evaluates it.

```bash
~/.agents/tools/team/team.sh list --type agent
~/.agents/tools/team/team.sh recommend --tags software,quality
~/.agents/tools/team/team.sh plan \
  --goal "Prepare a verified release" \
  --tags software,quality,release
```

The CEO dispatches tasks through the selected host's native subagent mechanism.
Subagents cannot create nested subagents; requests for another specialist return
to the CEO. See [Architecture](docs/ARCHITECTURE.md) and
[Orchestration](docs/ORCHESTRATION.md).

## Connect AI tools

```bash
./scripts/connect.sh --host codex
./scripts/connect.sh --host claude
./scripts/connect.sh --host gemini
```

Adapters create skill links and host-native subagent wrappers. They do not
overwrite a host's global instruction file. For another tool, point the agent
to `~/.agents/AGENTS.md` and `~/.agents/CONNECT.md`. See
[Host support](docs/HOSTS.md).

## Update

```bash
./scripts/update.sh
```

The installer never silently replaces a changed file. It reports a conflict.
Use `--force` only when you intentionally want replacement, preferably after
committing personal changes to Git.

During migration from an older installation, use `--preserve-agents-file` with
`--force` to update managed components and the catalog without replacing your
personal `~/.agents/AGENTS.md`.

## Local models

The `local-models` profile installs documentation and loopback-only helpers.
Weights and `.venv` directories are excluded.

```bash
./scripts/install.sh --profile local-models
cd ~/.agents/local-models/mlx-local-runtime
./setup.sh --version VERIFIED_VERSION
./run.sh --model /absolute/path/to/model --port 9944
```

The MLX helper supports Apple Silicon Macs. Python package installation and
model download remain separate, explicit user actions.

## Repository layout

```text
catalog/          component source of truth
library/skills/   original skills
library/agents/   subagent prompts
library/rules/    shared rules
library/models/   documentation and setup helpers
library/tools/    local catalog and coordination tools
library/orchestration/ task, result, and state contracts
profiles/         ready-made selections
docs/             architecture, orchestration, and host support
examples/         validated task and result packet examples
scripts/          install, connect, update, and doctor
tests/            isolated installation checks
```

## Security and licensing

Repository content was created for this project and is published under MIT.
Third-party material must not be added without verified redistribution rights.
Removing a license or making cosmetic edits does not create original work.

The installer does not download models, start network services automatically,
or overwrite conflicting user files without `--force`. See
[SECURITY.md](SECURITY.md) and [THIRD_PARTY.md](THIRD_PARTY.md).

## Contributing

A new component must use English, have a catalog entry, belong to a profile,
and pass:

```bash
./tests/test.sh
./scripts/doctor.sh
git diff --check
```

See [CONTRIBUTING.md](CONTRIBUTING.md). License: [MIT](LICENSE).
