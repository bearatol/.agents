<p align="center"><img src="docs/assets/agent-ecosystem-banner.svg" alt=".agents architecture banner" width="100%"></p>

# .agents

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

One portable layer for AI-agent work. It keeps shared rules, useful skills, and specialists available where they help, without rebuilding the context from scratch for every task.

Start with one work pack. Foundation is installed with it and connects it to the AI tool you choose.

## Quick start

You need Git and Python 3. On macOS, Linux, or WSL:

```bash
git clone https://github.com/bearatol/.agents.git
cd .agents
./scripts/bootstrap.sh
```

The installer asks for just two decisions: a work pack and a host. It adds Foundation (whose technical profile name is `core`), installs the pack, and offers the connection. Then verify the installation:

```bash
./scripts/doctor.sh
```

On Windows, use PowerShell:

```powershell
git clone https://github.com/bearatol/.agents.git
Set-Location .agents
.\scripts\install.ps1 -Profile core,software -HostName codex
.\scripts\doctor.ps1
```

## Choose a work pack

Foundation is the shared base: rules, CEO, routing, skill discovery, context engineering, natural writing, and quality review. `core` remains its technical name for command compatibility.

| If you want to… | Choose |
| --- | --- |
| Build and review software | `software` |
| Research markets, market, and launch | `marketing` |
| Write documentation, articles, and product copy | `content` |
| Design interfaces | `design` |
| Plan and make video | `video` |
| Handle large tasks and context handoffs | `context` |
| Set up the local MLX helper without model weights | `local-models` |

Inspect exact contents before installing:

```bash
./scripts/list.sh --profile software
```

## Connect and verify

Codex, Claude Code, Gemini, Koda, Yandex SourceCraft, and a generic mode are supported. Quick start connects the selected host; add another later:

```bash
./scripts/connect.sh --host claude
./scripts/doctor.sh
```

Adapters create managed links to installed skills and do not replace your existing user instructions. See [host support](docs/HOSTS.md) for details, including Windows and WSL.

## Keeping context focused

Foundation keeps concise shared rules in one place. A work pack adds only domain-specific instructions, while the CEO can split a complex goal into verifiable specialist tasks. Each result should return the work completed, verification, skills used, and remaining risks.

This is an operating approach, not a promise of a fixed token reduction or universal quality: results still depend on the task, model, and review.

## When you need more control

<details>
<summary>Non-interactive installation and individual components</summary>

```bash
./scripts/install.sh --profile core --profile marketing --host codex
./scripts/install.sh --component skill:copywriting
```

Run `./scripts/list.sh` to see every maintained profile. The `all` profile is for cases that genuinely need the whole collection.
</details>

<details>
<summary>CEO and subagents</summary>

The CEO decomposes a goal and recommends specialists; every specialist chooses skills within its task and permissions. The security reviewer is isolated from optional skills. See [Architecture](docs/ARCHITECTURE.md) and [Orchestration](docs/ORCHESTRATION.md).

```bash
~/.agents/tools/team/team.sh recommend --tags software,quality
```
</details>

<details>
<summary>Updates, local models, and contributing</summary>

Review the exact upstream commit before updating, then run:

```bash
./scripts/update.sh APPROVED_40_CHARACTER_COMMIT
```

`local-models` installs documentation and loopback-only helpers, not model weights or a virtual environment. See [CONNECT.md](CONNECT.md), [SECURITY.md](SECURITY.md), [THIRD_PARTY.md](THIRD_PARTY.md), and [CONTRIBUTING.md](CONTRIBUTING.md) for updates, safety, licensing, and contribution rules.
</details>

Repository components are original project work and licensed under [MIT](LICENSE).
