#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

agents_home() {
  printf '%s\n' "${AGENTS_HOME:-$HOME/.agents}"
}

validate_agents_home() {
  local value="$1"
  [[ "$value" == /* ]] || fail "AGENTS_HOME must be an absolute path"
  case "$value" in
    /|/Users|/home|"$HOME"|"$HOME"/)
      fail "refusing unsafe AGENTS_HOME: $value"
      ;;
  esac
}

fail() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

validate_name() {
  local value="$1"
  [[ "$value" =~ ^[a-z0-9][a-z0-9-]*$ ]] || fail "invalid component name: $value"
}

component_source() {
  local root="$1"
  local kind="$2"
  local name="$3"
  case "$kind" in
    skill) printf '%s/library/skills/%s\n' "$root" "$name" ;;
    agent) printf '%s/library/agents/%s.md\n' "$root" "$name" ;;
    rule) printf '%s/library/rules/%s.md\n' "$root" "$name" ;;
    model) printf '%s/library/models/%s\n' "$root" "$name" ;;
    *) fail "unknown component kind: $kind" ;;
  esac
}

component_destination() {
  local home="$1"
  local kind="$2"
  local name="$3"
  case "$kind" in
    skill) printf '%s/skills/%s\n' "$home" "$name" ;;
    agent) printf '%s/agents/%s.md\n' "$home" "$name" ;;
    rule) printf '%s/rules/%s.md\n' "$home" "$name" ;;
    model) printf '%s/local-models/%s\n' "$home" "$name" ;;
    *) fail "unknown component kind: $kind" ;;
  esac
}

expand_profile() {
  local root="$1"
  local profile="$2"
  local file="$root/profiles/$profile.profile"
  validate_name "$profile"
  [[ -f "$file" ]] || fail "unknown profile: $profile"

  local line nested
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    if [[ "$line" == profile:* ]]; then
      nested="${line#profile:}"
      expand_profile "$root" "$nested"
    else
      printf '%s\n' "$line"
    fi
  done < "$file"
}
