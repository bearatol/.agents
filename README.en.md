<p align="center"><img src="docs/assets/agent-ecosystem-banner.svg" alt=".agents architecture" width="100%"></p>

# .agents

<p align="center">
  <a href="https://github.com/bearatol/.agents/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/bearatol/.agents/actions/workflows/test.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
</p>

<p align="center"><strong>Connect any AI tool to your settings and reusable work—then get to work.</strong></p>

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

`.agents` is your shared workspace for AI. It keeps rules, skills, prompts, specialists, and other reusable work. Codex, Claude, Gemini, Kimi, and future tools can use the same workspace separately or together.

It is not another model. It is an independent layer between your work and AI tools: change computer, account, or provider without losing what you built.

## Why use it

| Situation | What `.agents` gives you |
| --- | --- |
| Claude is unavailable or out of quota | Connect Codex, Gemini, or Kimi and keep using the same skills and rules |
| You bought a new computer | Clone your `.agents` repository, run setup, and rebuild the workspace |
| One AI implements while another reviews better | Give them separate tasks and keep results and reviews together |
| You collected useful prompts and processes | Keep them in your Git repository instead of one vendor account |
| A new AI artifact appears tomorrow | Add a new folder type without migrating old data |

## Quick start: three steps

### 1. Install

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

Setup asks what you do and which AI applications you use. Select one or several choices, then confirm the change.

### 2. Restart the selected AI tool

The AI tool can now see the shared skills and settings that it supports.

### 3. Give it a normal task

> Review this project for bugs. Start with a short plan, make the changes, and show the test results.

Done. Normal daily work does not require more terminal commands.

## Connect everything at once

Install every work area and connect several AI tools with one command:

```bash
./scripts/agents.sh setup --work all \
  --app codex --app claude --app gemini --app kimi
```

On Windows:

```powershell
.\scripts\agents.ps1 setup -Work all -App codex,claude,gemini,kimi
```

Connect another AI later without reinstalling everything:

```bash
./scripts/agents.sh connect kimi
```

## What is stored

Your `.agents` Git repository may contain rules, prompts, skills, specialists,
model settings, connection descriptions, shared AI tasks, and future artifact
types. Passwords, API keys, login sessions, installed applications, and model
weights are deliberately excluded.

## Save your own reusable work

For a personal skill:

```bash
./scripts/agents.sh library add skill my-skill ./my-skill
./scripts/agents.sh library trust skill my-skill
./scripts/agents.sh library activate skill my-skill
./scripts/agents.sh connect codex claude gemini kimi
```

The skill is stored first, reviewed and trusted explicitly, then activated for connected tools. You can already store `rule`, `prompt`, `agent`, `mcp`, `model`, or any future type; matching adapters can add activation later.

## Move to a new computer

If you did not add personal material, clone `.agents` again and run `setup`.

For personal work, use your own private Git repository. On the new computer:

```bash
git clone YOUR_PRIVATE_REPOSITORY .agents
cd .agents
./scripts/agents.sh setup
./scripts/agents.sh library check
./scripts/agents.sh doctor
```

Git moves your files. Setup restores the shared environment and connections.
This version requires each personal skill to be activated again with
`library activate skill NAME`: instructions cloned from Git are never enabled
without an explicit decision.

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

## What does `export` mean?

Most people do not need this command.

`export` creates a small installation receipt for reproducing the exact setup. It records the selected work areas, connected AI applications, and exact `.agents` version. It does **not** contain prompts, skills, projects, passwords, or personal files. Git moves those files.

Use it only when another computer must reproduce the same version and connections:

```bash
./scripts/agents.sh status
./scripts/agents.sh export ./agents.lock.json
```

The resulting `agents.lock.json` is that receipt. After cloning the same repository version on another computer:

```bash
./scripts/agents.sh restore ./agents.lock.json
./scripts/agents.sh doctor
```

See [exact setup recovery](docs/PORTABILITY.md) for technical guarantees and limitations.

## Status vocabulary

This section is only for troubleshooting. Normal daily work does not require
checking `status`.

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
