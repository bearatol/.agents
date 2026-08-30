<p align="center"><img src="docs/assets/agent-ecosystem-banner.svg" alt=".agents architecture" width="100%"></p>

# .agents

<p align="center">
  <a href="https://github.com/bearatol/.agents/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/bearatol/.agents/actions/workflows/test.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
</p>

<p align="center"><strong>Keep your AI work in one portable place. Use it from Codex, Claude, Gemini, Kimi, and other tools separately or together.</strong></p>

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

`.agents` is a Git-backed home for shared rules, skills, specialists, prompts, model settings, and team tasks. AI applications attach through replaceable adapters, so one tool can be replaced or several can work together. Existing user files are never silently overwritten.

## Quick start

Git and Python 3 are required. On macOS, Linux, or WSL:

```bash
git clone https://github.com/bearatol/.agents.git
cd .agents
./scripts/agents.sh setup
```

On Windows:

```powershell
git clone https://github.com/bearatol/.agents.git
Set-Location .agents
.\scripts\agents.ps1 setup
```

Setup asks what you want help with and which AI application you use. You can choose several areas, such as code and video. It shows a plain-language confirmation before changing anything.

## Combine work areas or install everything

If you prefer not to answer questions, name the work directly. For example, code and video:

```bash
./scripts/agents.sh setup --work code --work video --app codex
```

On Windows:

```powershell
.\scripts\agents.ps1 setup -Work code,video -App codex
```

To install everything:

```bash
./scripts/agents.sh setup --work all --app codex
```

To let Codex, Claude, Gemini, and Kimi use the same workspace at once:

```bash
./scripts/agents.sh setup --work all \
  --app codex --app claude --app gemini --app kimi
```

On Windows, pass `-App codex,claude,gemini,kimi`.

## Main commands

| Goal | macOS / Linux / WSL | Windows |
| --- | --- | --- |
| Install or extend the workspace | `./scripts/agents.sh setup` | `.\scripts\agents.ps1 setup` |
| Inspect the current state | `./scripts/agents.sh status` | `.\scripts\agents.ps1 status` |
| Export portable configuration | `./scripts/agents.sh export ./agents.lock.json` | `.\scripts\agents.ps1 export .\agents.lock.json` |
| Restore on a new computer | `./scripts/agents.sh restore ./agents.lock.json` | `.\scripts\agents.ps1 restore .\agents.lock.json` |
| Run the complete health check | `./scripts/agents.sh doctor` | `.\scripts\agents.ps1 doctor` |

Add personal work to the portable library:

```bash
./scripts/agents.sh library add skill my-skill ./my-skill
./scripts/agents.sh library list
./scripts/agents.sh library trust skill my-skill
./scripts/agents.sh library activate skill my-skill
./scripts/agents.sh connect codex claude gemini kimi
./scripts/agents.sh library check
```

The type may be `skill`, `rule`, `prompt`, `agent`, `mcp`, `model`, or a future name that does not exist yet. A new type is just a new folder. Imports remain inactive until reviewed and explicitly trusted. This version activates skills; other types are preserved safely until a matching adapter exists.

## Several AI hosts as one team

Shared settings stay in `.agents`, while each host writes a separate immutable result. For example, Claude can implement, Gemini and Kimi can review, and Codex can accept the outcome:

```bash
./scripts/agents.sh team init release \
  --objective "Prepare the release" --coordinator codex \
  --member claude --member gemini --member kimi

./scripts/agents.sh team task release implementation \
  --title "Implement the change" --objective "Produce a verified result" \
  --role engineer --worker claude --reviewer gemini --reviewer kimi \
  --scope scripts --accept "All tests pass"

./scripts/agents.sh team status release
```

The neutral files under `workspace/projects/release/` can be read by any AI host and synchronized through Git. See the complete result, review, and decision flow in [personal workspace and AI teams](docs/WORKSPACE.md).

The existing install, connect, update, and list scripts remain available for automation and advanced control.

## First useful request

Open or restart the selected AI host after setup, then give it a normal task:

> Review this project for bugs. Start with a short plan, make only approved changes, and show the test evidence.

For a multi-disciplinary task:

> Run a complete product audit with the CEO. Use specialists only where they add concrete value and return evidence for every conclusion.

## Move to a new computer

On the old computer:

Export from a trusted checkout with no uncommitted changes so its contents exactly match the commit recorded in the lock.

```bash
./scripts/agents.sh status
./scripts/agents.sh export ./agents.lock.json
```

Copy `agents.lock.json`, clone the repository on the new computer, and independently review the full commit SHA recorded in the lock. Switch a clean checkout with no local changes to that reviewed commit, then run:

```bash
./scripts/agents.sh restore ./agents.lock.json
./scripts/agents.sh doctor
```

Restore never performs fetch, checkout, downgrade, deletion, or forced overwrite. It validates the lock and preflights destinations before persistent writes. See [portability and recovery](docs/PORTABILITY.md).

| Moves | Does not move |
| --- | --- |
| Selected profiles and explicit components | Accounts and authentication |
| Supported host connections | API keys and other secrets |
| Exact repository commit and ecosystem version | AI applications and CLI packages |
| Personal library and shared AI-team projects | Model weights, plugins, and unrelated dotfiles |

The Git repository moves the personal library; the lock restores the installed environment and connections. Use your own private repository for personal material. Never store passwords, keys, or account sessions: automated checks help, but cannot replace reviewing the diff before a push.

## Status vocabulary

- `current`: installed content matches its source;
- `missing`: a managed target is absent;
- `managed-stale`: the source changed while the installed copy stayed managed;
- `locally-modified`: installed content was changed locally;
- `host-conflicting`: a host connection is missing or occupied by unmanaged content.

`status` inspects the installed workspace. `doctor` also validates the catalog, profiles, repository text, forbidden artifacts, and host integration. Unsafe or incomplete state returns a non-zero exit code.

## Choose what you need help with

| Goal | Choose during setup |
| --- | --- |
| Software development and review | Code |
| Research, marketing, and launches | Research and marketing |
| Documentation and product content | Writing |
| Interface design | Design |
| Video planning and production | Video |
| Long tasks and context handoffs | Complex tasks |
| A local AI helper | Local AI |

Shared safety rules, quality checks, and basic helpers are added automatically. You do not need to learn their internal names.

## Trust boundary

The lock contains only schema version, ecosystem version, full commit SHA, profiles, components, and hosts. It contains no paths, commands, URLs, environment variables, credentials, or file contents. Local modifications and unmanaged files are preserved; conflicts require an explicit decision.

Learn more: [personal workspace and AI teams](docs/WORKSPACE.md) · [hosts](docs/HOSTS.md) · [architecture](docs/ARCHITECTURE.md) · [roadmap](docs/ROADMAP.md) · [security](SECURITY.md) · [contributing](CONTRIBUTING.md).

Licensed under the [MIT License](LICENSE).
