#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_HOME="$(mktemp -d)"
PORTABILITY_PID=""
cleanup() {
  if [[ -n "$PORTABILITY_PID" ]] && kill -0 "$PORTABILITY_PID" >/dev/null 2>&1; then
    kill "$PORTABILITY_PID" >/dev/null 2>&1 || true
    wait "$PORTABILITY_PID" >/dev/null 2>&1 || true
  fi
  rm -rf "$TEST_HOME"
}
trap cleanup EXIT

export AGENTS_HOME="$TEST_HOME/.agents"
TEST_USER_HOME="$TEST_HOME/user"
mkdir -p "$TEST_USER_HOME"

python3 "$ROOT/tests/test_portability.py" > "$TEST_HOME/portability.log" 2>&1 &
PORTABILITY_PID=$!

PREFLIGHT_AGENTS_HOME="$TEST_HOME/preflight-agents"
PREFLIGHT_USER_HOME="$TEST_HOME/preflight-user"
AGENTS_HOME="$PREFLIGHT_AGENTS_HOME" "$ROOT/scripts/install.sh" \
  --profile software --no-root-files >/dev/null
if HOME="$PREFLIGHT_USER_HOME" AGENTS_HOME="$PREFLIGHT_AGENTS_HOME" \
  "$ROOT/scripts/connect.sh" --host codex --host claude --host gemini --host sourcecraft \
  >/dev/null 2>&1; then
  printf 'missing Foundation preflight unexpectedly succeeded\n' >&2
  exit 1
fi
[[ ! -e "$PREFLIGHT_USER_HOME/.codex" ]]
[[ ! -e "$PREFLIGHT_USER_HOME/.claude" ]]
[[ ! -e "$PREFLIGHT_USER_HOME/.gemini" ]]
[[ ! -e "$PREFLIGHT_USER_HOME/.config" ]]
[[ ! -e "$PREFLIGHT_USER_HOME/.codeassistant" ]]

QUICK_START_AGENTS_HOME="$TEST_HOME/quick-start-agents"
QUICK_START_USER_HOME="$TEST_HOME/quick-start-user"
printf 'software\ncodex\ny\n' | \
  HOME="$QUICK_START_USER_HOME" AGENTS_HOME="$QUICK_START_AGENTS_HOME" \
  "$ROOT/scripts/bootstrap.sh" >/dev/null
grep -qx 'core' "$QUICK_START_AGENTS_HOME/.ecosystem-profiles"
grep -qx 'software' "$QUICK_START_AGENTS_HOME/.ecosystem-profiles"
[[ -f "$QUICK_START_USER_HOME/.codex/agents/engineer.toml" ]]

BASH32_AGENTS_HOME="$TEST_HOME/bash32-profile-only-agents"
BASH32_USER_HOME="$TEST_HOME/bash32-profile-only-user"
HOME="$BASH32_USER_HOME" AGENTS_HOME="$BASH32_AGENTS_HOME" \
  /bin/bash "$ROOT/scripts/install.sh" --profile software --no-root-files >/dev/null
grep -qx 'software' "$BASH32_AGENTS_HOME/.ecosystem-profiles"

INVALID_INPUT_AGENTS_HOME="$TEST_HOME/invalid-input-agents"
INVALID_INPUT_USER_HOME="$TEST_HOME/invalid-input-user"
for invalid_host in invalid-host ../codex 'codex;touch' --host; do
  if printf 'software\n%s\ny\n' "$invalid_host" | \
    HOME="$INVALID_INPUT_USER_HOME" AGENTS_HOME="$INVALID_INPUT_AGENTS_HOME" \
    "$ROOT/scripts/bootstrap.sh" >/dev/null 2>&1; then
    printf 'unsupported host unexpectedly succeeded: %s\n' "$invalid_host" >&2
    exit 1
  fi
done
[[ ! -e "$INVALID_INPUT_AGENTS_HOME" ]]
[[ ! -e "$INVALID_INPUT_USER_HOME/.codex" ]]

if HOME="$INVALID_INPUT_USER_HOME" AGENTS_HOME="$PREFLIGHT_AGENTS_HOME" \
  "$ROOT/scripts/connect.sh" --host invalid-host --host codex >/dev/null 2>&1; then
  printf 'unsupported direct host unexpectedly succeeded\n' >&2
  exit 1
fi
[[ ! -e "$INVALID_INPUT_USER_HOME/.codex" ]]

HOME="$INVALID_INPUT_USER_HOME" AGENTS_HOME="$INVALID_INPUT_AGENTS_HOME" \
  "$ROOT/scripts/bootstrap.sh" --profile software --dry-run >/dev/null

for invalid_work_pack in invalid-pack ../software 'software;touch' --profile; do
  if printf '%s\ncodex\ny\n' "$invalid_work_pack" | \
    HOME="$INVALID_INPUT_USER_HOME" AGENTS_HOME="$INVALID_INPUT_AGENTS_HOME" \
    "$ROOT/scripts/bootstrap.sh" >/dev/null 2>&1; then
    printf 'unsupported work pack unexpectedly succeeded: %s\n' "$invalid_work_pack" >&2
    exit 1
  fi
done
[[ ! -e "$INVALID_INPUT_AGENTS_HOME" ]]

[[ -f "$ROOT/README.md" ]]
[[ -f "$ROOT/README.en.md" ]]
[[ -f "$ROOT/README.zh-CN.md" ]]

"$ROOT/scripts/install.sh" --profile all --host generic
"$ROOT/scripts/doctor.sh"

[[ -f "$AGENTS_HOME/skills/natural-writing/SKILL.md" ]]
[[ -f "$AGENTS_HOME/skills/ceo/SKILL.md" ]]
[[ -f "$AGENTS_HOME/skills/skill-authoring/SKILL.md" ]]
[[ -f "$AGENTS_HOME/skills/campaign-launch/SKILL.md" ]]
[[ -f "$AGENTS_HOME/skills/ui-ux-design/SKILL.md" ]]
[[ -f "$AGENTS_HOME/skills/remotion-video/SKILL.md" ]]
[[ -f "$AGENTS_HOME/skills/context-engineering/SKILL.md" ]]
[[ -f "$AGENTS_HOME/agents/ceo.md" ]]
[[ -f "$AGENTS_HOME/agents/engineer.md" ]]
[[ -f "$AGENTS_HOME/agents/qa-reviewer.md" ]]
[[ -f "$AGENTS_HOME/agents/product-editor.md" ]]
[[ -f "$AGENTS_HOME/agents/ai-vulnerability-monitor.md" ]]
[[ -f "$AGENTS_HOME/agents/legal-content-reviewer.md" ]]
[[ -f "$AGENTS_HOME/agents/sales.md" ]]
[[ -f "$AGENTS_HOME/agents/seo-researcher.md" ]]
[[ -f "$AGENTS_HOME/skills/security-gate/SKILL.md" ]]
[[ -f "$AGENTS_HOME/orchestration/protocol.md" ]]
[[ -x "$AGENTS_HOME/tools/team/team.sh" ]]
[[ -f "$AGENTS_HOME/.ecosystem-state.json" ]]
[[ -f "$AGENTS_HOME/local-models/mlx-local-runtime/README.md" ]]

"$AGENTS_HOME/tools/team/team.sh" --home "$AGENTS_HOME" validate-catalog
"$AGENTS_HOME/tools/team/team.sh" --home "$AGENTS_HOME" recommend \
  --tags software,quality --output "$TEST_HOME/recommendation.json"
"$AGENTS_HOME/tools/team/team.sh" --home "$AGENTS_HOME" plan \
  --goal "Ship a tested installer" --tags software,quality \
  --output "$TEST_HOME/plan.json"
"$AGENTS_HOME/tools/team/team.sh" --home "$AGENTS_HOME" task \
  --task-id task-001 --agent engineer --title "Improve installer" \
  --objective "Implement a bounded installer improvement" \
  --scope scripts/install.sh --recommend-skill software-delivery \
  --accept "Focused tests pass" --output "$TEST_HOME/task.json"
"$AGENTS_HOME/tools/team/team.sh" --home "$AGENTS_HOME" validate task "$TEST_HOME/task.json"
"$AGENTS_HOME/tools/team/team.sh" --home "$AGENTS_HOME" validate result \
  "$AGENTS_HOME/orchestration/templates/result.json"

HOME="$TEST_USER_HOME" "$ROOT/scripts/connect.sh" --host codex --host claude --host gemini --host sourcecraft --host koda
[[ -f "$TEST_USER_HOME/.codex/agents/ceo.toml" ]]
[[ -f "$TEST_USER_HOME/.claude/agents/engineer.md" ]]
[[ -f "$TEST_USER_HOME/.gemini/agents/marketer.md" ]]
[[ -f "$TEST_USER_HOME/.config/opencode/agents/seo-researcher.md" ]]
[[ -f "$TEST_USER_HOME/.codeassistant/rules/agent-ecosystem.md" ]]
grep -q 'skill-router' "$TEST_USER_HOME/.claude/agents/engineer.md"
grep -q 'Independently select all relevant skills' "$TEST_USER_HOME/.gemini/agents/marketer.md"
grep -q 'scan compact' "$TEST_USER_HOME/.codex/agents/engineer.toml"
grep -q '^description: "' "$TEST_USER_HOME/.config/opencode/agents/seo-researcher.md"
if grep -q 'Read the installed catalog' "$TEST_USER_HOME/.claude/agents/engineer.md"; then
  printf 'specialist wrapper unexpectedly preloads the full catalog\n' >&2
  exit 1
fi
if grep -q 'skill-router' "$TEST_USER_HOME/.claude/agents/security-reviewer.md"; then
  printf 'security reviewer unexpectedly preloaded optional skills\n' >&2
  exit 1
fi
if grep -q 'activate_skill' "$TEST_USER_HOME/.gemini/agents/security-reviewer.md"; then
  printf 'security reviewer unexpectedly received skill activation\n' >&2
  exit 1
fi
if rg -q '"name":"(design-master|team-lead)"' "$ROOT/catalog/catalog.json"; then
  printf 'replaced agent remains in the canonical catalog\n' >&2
  exit 1
fi

if "$ROOT/scripts/install.sh" --profile core >/dev/null 2>&1; then
  :
else
  printf 'idempotent install failed\n' >&2
  exit 1
fi

printf 'personal rules\n' > "$AGENTS_HOME/AGENTS.md"
if "$ROOT/scripts/install.sh" --profile core >/dev/null 2>&1; then
  printf 'conflicting managed file was not reported\n' >&2
  exit 1
fi
grep -q '^personal rules$' "$AGENTS_HOME/AGENTS.md"

python3 "$ROOT/scripts/state.py" matches \
  --state "$AGENTS_HOME/.ecosystem-state.json" \
  --id skill:natural-writing \
  --path "$AGENTS_HOME/skills/natural-writing"

printf 'local customization\n' >> "$AGENTS_HOME/skills/natural-writing/SKILL.md"
if "$ROOT/scripts/install.sh" --profile core --no-root-files >/dev/null 2>&1; then
  printf 'modified managed skill was not reported as a conflict\n' >&2
  exit 1
fi
grep -q '^local customization$' "$AGENTS_HOME/skills/natural-writing/SKILL.md"
if "$ROOT/scripts/install.sh" --profile core --no-root-files --force >/dev/null 2>&1; then
  printf 'force overwrote or accepted a user-modified managed skill\n' >&2
  exit 1
fi
grep -q '^local customization$' "$AGENTS_HOME/skills/natural-writing/SKILL.md"

rm "$AGENTS_HOME/AGENTS.md"
"$ROOT/scripts/install.sh" --component skill:quality-review --no-root-files >/dev/null
[[ ! -e "$AGENTS_HOME/AGENTS.md" ]]

printf 'personal rules\n' > "$AGENTS_HOME/AGENTS.md"
"$ROOT/scripts/install.sh" --component skill:quality-review --force \
  --preserve-agents-file >/dev/null
grep -q '^personal rules$' "$AGENTS_HOME/AGENTS.md"

if ! wait "$PORTABILITY_PID"; then
  PORTABILITY_PID=""
  cat "$TEST_HOME/portability.log" >&2
  exit 1
fi
PORTABILITY_PID=""
cat "$TEST_HOME/portability.log"

printf 'All tests passed.\n'
