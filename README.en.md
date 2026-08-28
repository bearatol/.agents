<p align="center"><img src="docs/assets/agent-ecosystem-banner.svg" alt=".agents architecture" width="100%"></p>

# .agents

<p align="center">
  <a href="https://github.com/bearatol/.agents/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/bearatol/.agents/actions/workflows/test.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
</p>

<p align="center"><strong>Configure your AI-agent workspace once, then check, move, and restore it through five clear commands.</strong></p>

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

`.agents` keeps shared rules, skills, specialists, work profiles, and connections for Codex, Claude Code, Gemini CLI, Koda, and SourceCraft. Existing user files are never silently overwritten.

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

## Five commands

| Goal | macOS / Linux / WSL | Windows |
| --- | --- | --- |
| Install or extend the workspace | `./scripts/agents.sh setup` | `.\scripts\agents.ps1 setup` |
| Inspect the current state | `./scripts/agents.sh status` | `.\scripts\agents.ps1 status` |
| Export portable configuration | `./scripts/agents.sh export ./agents.lock.json` | `.\scripts\agents.ps1 export .\agents.lock.json` |
| Restore on a new computer | `./scripts/agents.sh restore ./agents.lock.json` | `.\scripts\agents.ps1 restore .\agents.lock.json` |
| Run the complete health check | `./scripts/agents.sh doctor` | `.\scripts\agents.ps1 doctor` |

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
| Managed rules, skills, and agents | Model weights, plugins, and unrelated dotfiles |

This restores the managed `.agents` workspace; it is not a whole-computer backup.

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

Learn more: [hosts](docs/HOSTS.md) · [architecture](docs/ARCHITECTURE.md) · [orchestration](docs/ORCHESTRATION.md) · [security](SECURITY.md) · [contributing](CONTRIBUTING.md).

Licensed under the [MIT License](LICENSE).
