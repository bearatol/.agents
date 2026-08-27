#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
ROOT="$(repo_root)"
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
      printf 'Usage: %s --host codex|claude|gemini|koda|sourcecraft|generic [--host ...]\n' "$0"
      exit 0
      ;;
    *) fail "unknown argument: $1" ;;
  esac
done

[[ ${#HOSTS[@]} -gt 0 ]] || fail "select at least one host"
[[ -d "$DEST_HOME/skills" ]] || fail "install a profile before connecting hosts"

TEAM_TOOL="$DEST_HOME/tools/team/team.sh"
REQUIRES_FOUNDATION=0
for host in "${HOSTS[@]}"; do
  case "$host" in
    codex|claude|gemini|sourcecraft)
      REQUIRES_FOUNDATION=1
      ;;
    koda|generic)
      ;;
    *) fail "unsupported host: $host" ;;
  esac
done

if [[ $REQUIRES_FOUNDATION -eq 1 && ! -x "$TEAM_TOOL" ]]; then
  fail "install Foundation (profile core) before connecting subagents"
fi

link_skills() {
  local target_root="$1"
  assert_no_symlink_traversal "$target_root" "$HOME"
  mkdir -p "$target_root"
  assert_no_symlink_traversal "$target_root" "$HOME"
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
  assert_no_symlink_traversal "$target_root" "$HOME"
  "$TEAM_TOOL" --home "$DEST_HOME" render-host --host "$host" --target "$target_root"
}

install_file_if_free() {
  local source_file="$1"
  local target_file="$2"
  assert_no_symlink_traversal "$target_file" "$HOME"
  mkdir -p "$(dirname "$target_file")"
  assert_no_symlink_traversal "$target_file" "$HOME"
  if [[ -e "$target_file" ]]; then
    if diff -q "$source_file" "$target_file" >/dev/null 2>&1; then
      return
    fi
    printf 'host conflict: %s\n' "$target_file" >&2
    return
  fi
  cp "$source_file" "$target_file"
  printf 'installed %s\n' "$target_file"
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
    koda)
      if command -v koda >/dev/null 2>&1; then
        printf 'koda detected: skills are discovered directly from %s/skills\n' "$DEST_HOME"
      else
        printf 'koda is not installed; see docs/HOSTS.md for installation instructions\n'
      fi
      ;;
    sourcecraft)
      render_agents sourcecraft "$HOME/.config/opencode/agents"
      install_file_if_free "$ROOT/library/hosts/sourcecraft-global-rule.md" \
        "$HOME/.codeassistant/rules/agent-ecosystem.md"
      printf 'SourceCraft CLI/OpenCode discovers skills directly from %s/skills\n' "$DEST_HOME"
      ;;
    generic)
      printf 'generic host: point the agent to %s/AGENTS.md and %s/CONNECT.md\n' "$DEST_HOME" "$DEST_HOME"
      ;;
    *) fail "unsupported host: $host" ;;
  esac
done
