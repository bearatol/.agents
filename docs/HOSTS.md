# Host Support

## Codex

The adapter links skills into `~/.codex/skills` and renders agent wrappers into
`~/.codex/agents`. Wrappers reference the canonical prompts in `~/.agents` and
set a read-only or workspace-write sandbox from catalog metadata. Run
`codex doctor` after connecting when the command is available.

## Claude Code

The adapter links skills into `~/.claude/skills` and renders subagents into
`~/.claude/agents`. Each wrapper preloads `skill-router`; the specialist may
then invoke additional installed skills. Claude Code documents user-level
subagents, tool restrictions, and skill preloading in its
[subagent guide](https://code.claude.com/docs/en/sub-agents).

## Gemini CLI

Gemini CLI discovers user skills from `~/.gemini/skills` and also supports the
`~/.agents/skills` alias. User subagents live in `~/.gemini/agents`. The
adapter renders local agent definitions with isolated tool lists. See Gemini's
[skills guide](https://geminicli.com/docs/cli/using-agent-skills/) and
[subagent guide](https://geminicli.com/docs/core/subagents/).

## Koda CLI

Koda discovers global skills directly from `~/.agents/skills`; the adapter does
not create duplicate copies or invent an undocumented subagent format.

```bash
npm install --global @kodadev/koda-cli
koda --version
./scripts/connect.sh --host koda
koda skills list
```

Use Node.js 20 or newer. On Windows, run the same npm command and
`.\scripts\connect.ps1 -HostName koda`. The ecosystem references Koda but does
not vendor its package because the npm package does not currently declare a
redistribution license. See the [official npm page](https://www.npmjs.com/package/@kodadev/koda-cli).

## Yandex SourceCraft

SourceCraft CLI launches its bundled OpenCode agent. OpenCode natively discovers
skills from `~/.agents/skills`; the adapter renders subagents into
`~/.config/opencode/agents` and adds one conflict-safe global Code Assistant rule
under `~/.codeassistant/rules`.

```bash
./scripts/connect.sh --host sourcecraft
src init
src code
```

On Windows, run `.\scripts\connect.ps1 -HostName sourcecraft`. Authentication
remains an explicit SourceCraft step and should use the operating-system keyring
when available. SourceCraft web-interface skills are repository-scoped under
`.sourcecraft/skills`; a global `~/.agents` installation does not publish them
to the web catalog automatically. See the official [CLI quickstart](https://sourcecraft.dev/portal/docs/en/sourcecraft/operations/cli-quickstart),
[AI skills format](https://sourcecraft.dev/portal/docs/en/sourcecraft/concepts/ai-skills),
and [AGENTS.md support](https://sourcecraft.dev/portal/docs/en/sourcecraft/concepts/agentsmd).

## Windows and WSL

Native Windows uses the PowerShell scripts and copies skills into host-specific
directories, avoiding symlink privileges. The canonical directory is
`%USERPROFILE%\.agents` unless `AGENTS_HOME` is set.

```powershell
.\scripts\install.ps1 -Profile core,software -HostName codex,gemini
.\scripts\doctor.ps1
```

WSL is a separate Linux environment: use the Bash scripts and its Linux home
directory. Native Windows and WSL installations are not silently merged.

## Generic hosts

Tell the main agent to read `~/.agents/AGENTS.md`, `~/.agents/CONNECT.md`, and
the orchestration protocol. If the host has no native subagent mechanism, the
CEO must not pretend delegation occurred. It may produce task packets for a
human to dispatch or complete the work in one context.

## Conflict behavior

Host adapters do not overwrite an existing custom agent with different
content. Resolve the conflict manually or explicitly regenerate after saving
the user's version.
