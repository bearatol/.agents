# CEO and Subagent Orchestration

There are two compatible levels:

- A host-native CEO works inside one AI host and can use that host's native
  specialist wrappers.
- Several independent AI applications can exchange neutral records through
  `scripts/agents.sh team` and `workspace/projects/`.

The second level separates the specialist role from the vendor. Claude may act
as the engineer, Gemini and Kimi as reviewers, and Codex as coordinator. See
[personal workspace and AI teams](WORKSPACE.md) for the complete CLI flow.
`agents.sh team` creates and validates files. It never launches an AI
application, spends tokens, or sends network requests.

## Inspect the available team

```bash
~/.agents/tools/team/team.sh list --type agent
~/.agents/tools/team/team.sh show agent:engineer
```

## Get deterministic recommendations

```bash
~/.agents/tools/team/team.sh recommend \
  --tags software,quality,release
```

Recommendations are a starting point. The CEO chooses assignments; each
subagent chooses its own final skills.

## Create a task packet

```bash
~/.agents/tools/team/team.sh task \
  --task-id installer-001 \
  --agent engineer \
  --title "Improve installer updates" \
  --objective "Update managed components without overwriting user edits" \
  --scope scripts/install.sh \
  --scope scripts/state.py \
  --authoritative-input catalog/catalog.json \
  --exclude "unrelated build logs" \
  --context-budget focused \
  --recommend-skill software-delivery \
  --accept "Existing user modifications remain unchanged" \
  --accept "All installer tests pass" \
  --output task.json
```

The CEO dispatches `task.json` through the host's native subagent tool. The
specialist queries compact catalog metadata, considers every relevant skill,
loads full instructions only for selected skills, and reports its actual choices
in a result packet. The context budget is soft: evidence and safety take priority
over token reduction.

## Validate returned evidence

```bash
~/.agents/tools/team/team.sh validate task task.json
~/.agents/tools/team/team.sh validate result result.json
```

Schema validity does not prove correctness. The CEO must still inspect
artifacts, evidence, test output, and acceptance criteria.
