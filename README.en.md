<p align="center"><img src="docs/assets/agent-ecosystem-banner.svg" alt=".agents architecture" width="100%"></p>

# .agents

<p align="center">
  <a href="https://github.com/bearatol/.agents/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/bearatol/.agents/actions/workflows/test.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
</p>

<p align="center"><strong>Use the same rules, skills, and work with any AI tool.</strong></p>

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

`.agents` is a workspace for your AI work. It keeps rules, skills, prompts,
specialists, and other material you want to reuse. Codex, Claude, Gemini, Kimi,
and other tools can use the same workspace, one at a time or together.

It is not another model or account. Your material stays in your Git repository,
separate from any one AI service. Change computers, accounts, or providers and
keep what you built.

## Why use it

| Situation | What `.agents` gives you |
| --- | --- |
| Claude is unavailable or out of quota | Connect Codex, Gemini, or Kimi and keep using the same skills and rules |
| You bought a new computer | Clone your `.agents` repository and run setup. Your workspace comes back |
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

Setup asks what you need help with and which AI applications you use. Choose one
or more options, enter several applications with commas, then review the change
before it is made. Select `generic` only for a tool without its own adapter.

### 2. Verify the installation

```bash
./scripts/agents.sh doctor
```

On Windows:

```powershell
.\scripts\agents.ps1 doctor
```

`doctor` checks the installed environment and host connections. Resolve any
conflict or modified-file report before continuing.

### 3. Restart the selected AI tool and give it a normal task

The AI tool can now see the shared material it supports.

> Review this project for bugs. Start with a short plan, make the changes, and show the test results.

After that check, normal daily work does not require more terminal commands.

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

Add another AI later without reinstalling everything:

```bash
./scripts/agents.sh connect kimi
```

## What is stored

Your `.agents` Git repository can contain rules, prompts, skills, specialists,
model settings, connection descriptions, shared AI tasks, and new types of
material. It does not contain passwords, API keys, login sessions, installed
applications, or model weights. Keep those out of Git.

## Save your own reusable work

For a personal skill:

```bash
./scripts/agents.sh library add skill my-skill ./my-skill
./scripts/agents.sh library trust skill my-skill
./scripts/agents.sh library activate skill my-skill
./scripts/agents.sh connect codex claude gemini kimi
```

The skill is stored first. You review it, mark it as trusted, and then activate
it for connected tools. This prevents instructions from Git from turning on by
themselves. You can also store `rule`, `prompt`, `agent`, `mcp`, `model`, or a
new type. An adapter can activate a type when it learns how to use it.

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

Git brings back your files and setup reconnects the applications. Each personal
skill must be activated again with `library activate skill NAME`. Instructions
cloned from Git are never enabled without your decision.

## Several AI hosts as one team

Everyone uses the same `.agents`, but their answers do not overwrite one
another. For example, Claude can implement, Gemini and Kimi can review, and
Codex can accept the outcome:

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

The files under `workspace/projects/release/` can be read by any connected AI
tool and synchronized through Git. See the full flow in [personal workspace and
AI teams](docs/WORKSPACE.md).

## What does `export` mean?

Most people do not need this command.

`export` creates a small installation receipt. It records the selected work
areas, connected AI applications, and exact `.agents` version. It does **not**
contain prompts, skills, projects, passwords, or personal files. Git moves
those files.

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

The lock contains only a schema version, ecosystem version, full commit SHA,
profiles, components, and hosts. It contains no paths, commands, URLs,
environment variables, credentials, or file contents. Local modifications and
unmanaged files stay in place. A conflict requires your decision.

Learn more: [personal workspace and AI teams](docs/WORKSPACE.md) · [hosts](docs/HOSTS.md) · [architecture](docs/ARCHITECTURE.md) · [roadmap](docs/ROADMAP.md) · [security](SECURITY.md) · [contributing](CONTRIBUTING.md).

Licensed under the [MIT License](LICENSE).
