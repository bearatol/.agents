# CEO and Subagent Orchestration

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
  --recommend-skill software-delivery \
  --accept "Existing user modifications remain unchanged" \
  --accept "All installer tests pass" \
  --output task.json
```

The CEO dispatches `task.json` through the host's native subagent tool. The
specialist reads the catalog, considers every relevant skill, and reports its
actual choices in a result packet.

## Validate returned evidence

```bash
~/.agents/tools/team/team.sh validate task task.json
~/.agents/tools/team/team.sh validate result result.json
```

Schema validity does not prove correctness. The CEO must still inspect
artifacts, evidence, test output, and acceptance criteria.
