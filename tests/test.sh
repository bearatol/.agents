#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_HOME="$(mktemp -d)"
trap 'rm -rf "$TEST_HOME"' EXIT

export AGENTS_HOME="$TEST_HOME/.agents"

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
[[ -f "$AGENTS_HOME/local-models/mlx-local-runtime/README.md" ]]

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

printf 'All tests passed.\n'
