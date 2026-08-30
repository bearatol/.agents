# Connect This Ecosystem

This file is the entry point for humans and AI agents.

The installer and host adapters require Git and Python 3. Use Bash on
macOS/Linux/WSL and PowerShell on native Windows.

## Instructions for an AI agent

1. Query `catalog/catalog.json` metadata and the requested profile files; do not
   preload every full skill.
2. Ask what kind of work the user does and which hosts they use. Several hosts
   may use the same environment simultaneously.
3. Recommend the smallest sufficient set of profiles and components.
4. Choose Bash or PowerShell for the current operating system and show the exact
   install command before running it.
5. Run `scripts/install.sh` only with the user's selected profiles.
6. Run `scripts/connect.sh` for explicitly selected hosts.
7. Run `scripts/doctor.sh` and report conflicts or missing dependencies.
8. Never install model weights, packages, or network services implicitly.
9. Never overwrite an unmanaged or user-modified file. Report the conflict and
   require the user to resolve that exact path manually.
10. After changing the ecosystem, update the catalog, profile membership,
    documentation, and tests in the same change.

## Instructions for a CEO agent

1. Read `~/.agents/orchestration/protocol.md` and query catalog metadata through
   `~/.agents/tools/team/team.sh`.
2. Apply the skills needed for coordination, planning, and verification.
3. Build a dependency-aware task graph and recommend specialist agents.
4. Create task packets with `~/.agents/tools/team/team.sh task`.
5. Recommend skills as hints. Each subagent selects its own final skill set.
6. Dispatch through the host's native subagent tool; never simulate a result.
7. Validate returned packets and evidence before marking a task complete.
8. Keep subagents from delegating further; additional expertise returns to CEO.

## Human commands

Use the human-friendly interface for normal work:

```bash
./scripts/agents.sh setup
./scripts/agents.sh connect codex claude gemini kimi
./scripts/agents.sh library list
./scripts/agents.sh team status PROJECT
./scripts/agents.sh status
./scripts/agents.sh export ./agents.lock.json
./scripts/agents.sh restore ./agents.lock.json
./scripts/agents.sh doctor
```

Native Windows:

```powershell
.\scripts\agents.ps1 setup
.\scripts\agents.ps1 connect -App codex,claude,gemini,kimi
.\scripts\agents.ps1 library list
.\scripts\agents.ps1 team status PROJECT
.\scripts\agents.ps1 status
.\scripts\agents.ps1 export .\agents.lock.json
.\scripts\agents.ps1 restore .\agents.lock.json
.\scripts\agents.ps1 doctor
```

`setup` accepts one or more work areas and one or more AI applications. `status` reports installed and host
drift. `export` refuses to overwrite an existing file. `restore` accepts only a
strict portable manifest and requires the current trusted checkout to match its
full commit SHA; it never fetches, changes Git state, deletes content, or enables
forced overwrite.

The lower-level commands remain available for automation:

```bash
./scripts/list.sh
./scripts/install.sh --profile core --profile marketing
./scripts/connect.sh --host codex --host claude
./scripts/doctor.sh
~/.agents/tools/team/team.sh list --type agent
~/.agents/tools/team/team.sh recommend --tags software,quality
```

Lower-level native Windows:

```powershell
.\scripts\install.ps1 -Profile core,marketing -HostName codex,koda,sourcecraft
.\scripts\doctor.ps1
```

The default destination is `${AGENTS_HOME:-$HOME/.agents}`. Override it for a
test or isolated installation:

```bash
AGENTS_HOME=/tmp/.agents-test ./scripts/install.sh --profile core
```

## Supported host adapters

- `codex`: links installed skills into `~/.codex/skills`.
- `claude`: links installed skills into `~/.claude/skills`.
- `gemini`: links installed skills into `~/.gemini/skills`.
- `kimi`: uses Kimi Code's native discovery of `~/.agents/skills`.
- `koda`: uses Koda's native discovery of `~/.agents/skills`.
- `sourcecraft`: uses native OpenCode skill discovery, renders OpenCode
  subagents, and adds a conflict-safe SourceCraft Code Assistant rule.
- `generic`: uses `~/.agents` directly; tell the host to read its `AGENTS.md`.

Adapters create managed skill links and host-native subagent wrappers. They do
not overwrite a host's global instruction file or conflicting custom agent.
The stable facade accepts only trusted built-in adapter IDs. Unknown names may
be stored as neutral library data but never become executable adapter commands.
