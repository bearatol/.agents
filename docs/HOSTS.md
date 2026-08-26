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

## Generic hosts

Tell the main agent to read `~/.agents/AGENTS.md`, `~/.agents/CONNECT.md`, and
the orchestration protocol. If the host has no native subagent mechanism, the
CEO must not pretend delegation occurred. It may produce task packets for a
human to dispatch or complete the work in one context.

## Conflict behavior

Host adapters do not overwrite an existing custom agent with different
content. Resolve the conflict manually or explicitly regenerate after saving
the user's version.
