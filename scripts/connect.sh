#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
DEST_HOME="$(agents_home)"
validate_agents_home "$DEST_HOME"
declare -a HOSTS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host)
      [[ $# -ge 2 ]] || fail "--host requires a name"
      HOSTS+=("$2")
      shift 2
      ;;
    -h|--help)
      printf 'Usage: %s --host codex|claude|gemini|generic [--host ...]\n' "$0"
      exit 0
      ;;
    *) fail "unknown argument: $1" ;;
  esac
done

[[ ${#HOSTS[@]} -gt 0 ]] || fail "select at least one host"
[[ -d "$DEST_HOME/skills" ]] || fail "install a profile before connecting hosts"

link_skills() {
  local target_root="$1"
  mkdir -p "$target_root"
  local skill name target
  for skill in "$DEST_HOME"/skills/*; do
    [[ -d "$skill" && -f "$skill/SKILL.md" ]] || continue
    name="$(basename "$skill")"
    target="$target_root/$name"
    [[ "$target" == "$target_root"/* ]] || fail "host link escaped target directory"
    if [[ -L "$target" && "$(readlink "$target")" == "$skill" ]]; then
      continue
    fi
    if [[ -e "$target" || -L "$target" ]]; then
      printf 'host conflict: %s\n' "$target" >&2
      continue
    fi
    ln -s "$skill" "$target"
    printf 'linked %s\n' "$target"
  done
}

render_agents() {
  local host="$1"
  local target_root="$2"
  local team_tool="$DEST_HOME/tools/team/team.sh"
  [[ -x "$team_tool" ]] || fail "install the core profile before connecting subagents"
  "$team_tool" --home "$DEST_HOME" render-host --host "$host" --target "$target_root"
}

for host in "${HOSTS[@]}"; do
  case "$host" in
    codex)
      link_skills "$HOME/.codex/skills"
      render_agents codex "$HOME/.codex/agents"
      ;;
    claude)
      link_skills "$HOME/.claude/skills"
      render_agents claude "$HOME/.claude/agents"
      ;;
    gemini)
      link_skills "$HOME/.gemini/skills"
      render_agents gemini "$HOME/.gemini/agents"
      ;;
    generic)
      printf 'generic host: point the agent to %s/AGENTS.md and %s/CONNECT.md\n' "$DEST_HOME" "$DEST_HOME"
      ;;
    *) fail "unsupported host: $host" ;;
  esac
done
