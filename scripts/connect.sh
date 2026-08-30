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
MANAGED_HOME="${AE_MANAGED_HOME:-$DEST_HOME}"
STATE_FILE="$DEST_HOME/.ecosystem-state.json"
STATE_TOOL="$ROOT/scripts/state.py"
declare -a HOSTS=()
DRY_RUN=0
SOURCE_HOME=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) [[ $# -ge 2 ]] || fail "--host requires a name"; HOSTS+=("$2"); shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --source-home) [[ $# -ge 2 ]] || fail "--source-home requires a path"; SOURCE_HOME="$2"; shift 2 ;;
    -h|--help) printf 'Usage: %s --host codex|claude|gemini|kimi|koda|sourcecraft|generic [--host ...]\n' "$0"; exit 0 ;;
    *) fail "unknown argument: $1" ;;
  esac
done

[[ ${#HOSTS[@]} -gt 0 ]] || fail "select at least one host"
[[ "$MANAGED_HOME" == /* ]] || fail "managed home must be an absolute path"
if [[ "$MANAGED_HOME" != "$DEST_HOME" && $DRY_RUN -ne 1 ]]; then
  fail "managed home override is allowed only during preflight"
fi
REQUIRES_FOUNDATION=0
for host in "${HOSTS[@]}"; do
  case "$host" in
    codex|claude|gemini|sourcecraft) REQUIRES_FOUNDATION=1 ;;
    kimi|koda|generic) ;;
    *) fail "unsupported host: $host" ;;
  esac
done

SKILLS_ROOT="$DEST_HOME/skills"
TEAM_TOOL="$DEST_HOME/tools/team/team.sh"
if [[ ! -d "$SKILLS_ROOT" && -n "$SOURCE_HOME" && $DRY_RUN -eq 1 ]]; then
  [[ "$SOURCE_HOME" == "$ROOT" ]] || fail "untrusted internal source home"
  SKILLS_ROOT="$ROOT/library/skills"
fi
[[ -d "$SKILLS_ROOT" ]] || fail "install a profile before connecting hosts"
if [[ $REQUIRES_FOUNDATION -eq 1 && ! -x "$TEAM_TOOL" && ! ( $DRY_RUN -eq 1 && "$SOURCE_HOME" == "$ROOT" ) ]]; then
  fail "install Foundation (profile core) before connecting subagents"
fi

state_matches() {
  python3 "$STATE_TOOL" matches --state "$STATE_FILE" --id "$1" --path "$2" >/dev/null 2>&1
}

state_record() {
  python3 "$STATE_TOOL" set --state "$STATE_FILE" --id "$1" --source "$2" --installed "$3"
}

STAGE_ROOT="$(mktemp -d)"
trap 'rm -rf "$STAGE_ROOT"' EXIT
CONFLICTS=0

preflight_skills() {
  local host="$1" target_root="$2" skill name target expected
  assert_no_symlink_traversal "$target_root" "$HOME"
  for skill in "$SKILLS_ROOT"/*; do
    [[ -d "$skill" && -f "$skill/SKILL.md" ]] || continue
    name="$(basename "$skill")"
    target="$target_root/$name"
    expected="$MANAGED_HOME/skills/$name"
    if [[ -L "$target" ]]; then
      if [[ "$(readlink "$target")" == "$expected" ]]; then continue; fi
      printf 'host conflict: %s\n' "$target" >&2
      CONFLICTS=$((CONFLICTS + 1))
    elif [[ -e "$target" ]]; then
      assert_no_symlink_traversal "$target" "$HOME"
      printf 'host conflict: %s\n' "$target" >&2
      CONFLICTS=$((CONFLICTS + 1))
    elif [[ $DRY_RUN -eq 1 ]]; then
      assert_no_symlink_traversal "$target" "$HOME"
      printf 'would-link %s\n' "$target"
    fi
  done
}

prepare_agents() {
  local host="$1" target_root="$2" stage="$STAGE_ROOT/$1"
  mkdir -p "$stage"
  assert_no_symlink_traversal "$target_root" "$HOME"
  if [[ -x "$TEAM_TOOL" ]]; then
    "$TEAM_TOOL" --home "$DEST_HOME" render-host --host "$host" --target "$stage" >/dev/null
  else
    local canonical name extension
    case "$host" in codex) extension=.toml ;; *) extension=.md ;; esac
    for canonical in "$ROOT"/library/agents/*.md; do
      [[ -f "$canonical" ]] || continue
      name="$(basename "$canonical" .md)"
      : > "$stage/$name$extension"
    done
  fi
  local wrapper target state_id
  for wrapper in "$stage"/*; do
    [[ -f "$wrapper" ]] || continue
    target="$target_root/$(basename "$wrapper")"
    state_id="host:$host:agent:$(basename "${wrapper%.*}")"
    assert_no_symlink_traversal "$target" "$HOME"
    if [[ -e "$target" || -L "$target" ]]; then
      if [[ -s "$wrapper" ]] && diff -q "$wrapper" "$target" >/dev/null 2>&1; then continue; fi
      if [[ -s "$wrapper" ]] && state_matches "$state_id" "$target"; then continue; fi
      printf 'host conflict: %s\n' "$target" >&2
      CONFLICTS=$((CONFLICTS + 1))
    elif [[ $DRY_RUN -eq 1 ]]; then
      printf 'would-install %s\n' "$target"
    fi
  done
}

preflight_file() {
  local source_file="$1" target_file="$2" state_id="$3"
  assert_no_symlink_traversal "$target_file" "$HOME"
  if [[ -e "$target_file" || -L "$target_file" ]]; then
    if diff -q "$source_file" "$target_file" >/dev/null 2>&1 || state_matches "$state_id" "$target_file"; then return; fi
    printf 'host conflict: %s\n' "$target_file" >&2
    CONFLICTS=$((CONFLICTS + 1))
  elif [[ $DRY_RUN -eq 1 ]]; then
    printf 'would-install %s\n' "$target_file"
  fi
}

for host in "${HOSTS[@]}"; do
  case "$host" in
    codex) preflight_skills codex "$HOME/.codex/skills"; prepare_agents codex "$HOME/.codex/agents" ;;
    claude) preflight_skills claude "$HOME/.claude/skills"; prepare_agents claude "$HOME/.claude/agents" ;;
    gemini) preflight_skills gemini "$HOME/.gemini/skills"; prepare_agents gemini "$HOME/.gemini/agents" ;;
    sourcecraft)
      prepare_agents sourcecraft "$HOME/.config/opencode/agents"
      preflight_file "$ROOT/library/hosts/sourcecraft-global-rule.md" "$HOME/.codeassistant/rules/agent-ecosystem.md" 'host:sourcecraft:rule:agent-ecosystem'
      ;;
    kimi|koda|generic) ;;
  esac
done

[[ $CONFLICTS -eq 0 ]] || exit 2
if [[ $DRY_RUN -eq 1 ]]; then printf 'Host preflight passed.\n'; exit 0; fi

install_skills() {
  local host="$1" target_root="$2" skill name target expected state_id
  assert_no_symlink_traversal "$target_root" "$HOME"
  mkdir -p "$target_root"
  assert_no_symlink_traversal "$target_root" "$HOME"
  for skill in "$DEST_HOME"/skills/*; do
    [[ -d "$skill" && -f "$skill/SKILL.md" ]] || continue
    name="$(basename "$skill")"; target="$target_root/$name"; expected="$skill"; state_id="host:$host:skill:$name"
    if [[ -L "$target" && "$(readlink "$target")" == "$expected" ]]; then
      state_record "$state_id" "$skill" "$target"; continue
    fi
    assert_no_symlink_traversal "$target" "$HOME"
    [[ ! -e "$target" && ! -L "$target" ]] || fail "host changed after preflight: $target; partial apply is safely rerunnable"
    ln -s "$expected" "$target"
    state_record "$state_id" "$skill" "$target"
    printf 'linked %s\n' "$target"
  done
}

install_managed_file() {
  local source_file="$1" target_file="$2" state_id="$3" staged_file
  assert_no_symlink_traversal "$target_file" "$HOME"
  mkdir -p "$(dirname "$target_file")"
  assert_no_symlink_traversal "$target_file" "$HOME"
  if [[ -e "$target_file" || -L "$target_file" ]]; then
    if diff -q "$source_file" "$target_file" >/dev/null 2>&1; then state_record "$state_id" "$source_file" "$target_file"; return; fi
    state_matches "$state_id" "$target_file" || fail "host changed after preflight: $target_file; partial apply is safely rerunnable"
  fi
  staged_file="$(mktemp "$(dirname "$target_file")/.ae-host.XXXXXX")"
  cp "$source_file" "$staged_file"
  assert_no_symlink_traversal "$target_file" "$HOME"
  if [[ -e "$target_file" || -L "$target_file" ]]; then
    state_matches "$state_id" "$target_file" || fail "host changed during apply: $target_file; partial apply is safely rerunnable"
  fi
  mv "$staged_file" "$target_file"
  state_record "$state_id" "$source_file" "$target_file"
  printf 'installed %s\n' "$target_file"
}

install_agents() {
  local host="$1" target_root="$2" wrapper state_id
  for wrapper in "$STAGE_ROOT/$host"/*; do
    [[ -f "$wrapper" ]] || continue
    state_id="host:$host:agent:$(basename "${wrapper%.*}")"
    install_managed_file "$wrapper" "$target_root/$(basename "$wrapper")" "$state_id"
  done
}

for host in "${HOSTS[@]}"; do
  case "$host" in
    codex) install_skills codex "$HOME/.codex/skills"; install_agents codex "$HOME/.codex/agents" ;;
    claude) install_skills claude "$HOME/.claude/skills"; install_agents claude "$HOME/.claude/agents" ;;
    gemini) install_skills gemini "$HOME/.gemini/skills"; install_agents gemini "$HOME/.gemini/agents" ;;
    sourcecraft)
      install_agents sourcecraft "$HOME/.config/opencode/agents"
      install_managed_file "$ROOT/library/hosts/sourcecraft-global-rule.md" "$HOME/.codeassistant/rules/agent-ecosystem.md" 'host:sourcecraft:rule:agent-ecosystem'
      printf 'SourceCraft CLI/OpenCode discovers skills directly from %s/skills\n' "$DEST_HOME"
      ;;
    koda)
      if command -v koda >/dev/null 2>&1; then printf 'koda detected: skills are discovered directly from %s/skills\n' "$DEST_HOME"; else printf 'koda is not installed; see docs/HOSTS.md for installation instructions\n'; fi
      ;;
    kimi) printf 'Kimi Code discovers skills directly from %s/skills\n' "$DEST_HOME" ;;
    generic) printf 'generic host: point the agent to %s/AGENTS.md and %s/CONNECT.md\n' "$DEST_HOME" "$DEST_HOME" ;;
  esac
done

HOSTS_STAGE="$(mktemp "$DEST_HOME/.ecosystem-hosts.XXXXXX")"
if [[ -f "$DEST_HOME/.ecosystem-hosts" ]]; then cat "$DEST_HOME/.ecosystem-hosts" > "$HOSTS_STAGE"; fi
printf '%s\n' "${HOSTS[@]}" >> "$HOSTS_STAGE"
awk 'NF && !seen[$0]++' "$HOSTS_STAGE" > "$STAGE_ROOT/hosts"
assert_no_symlink_traversal "$DEST_HOME/.ecosystem-hosts" "$DEST_HOME"
mv "$STAGE_ROOT/hosts" "$DEST_HOME/.ecosystem-hosts"
