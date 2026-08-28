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
STATE_FILE="$DEST_HOME/.ecosystem-state.json"
STATE_TOOL="$ROOT/scripts/state.py"

declare -a PROFILES=()
declare -a COMPONENTS=()
declare -a HOSTS=()
DRY_RUN=0
ROOT_FILES=1
PRESERVE_AGENTS_FILE=0

usage() {
  printf '%s\n' "Usage: $0 --profile NAME [--profile NAME ...] [options]"
  printf '%s\n' "       $0 --component KIND:NAME [--component KIND:NAME ...] [options]"
  printf '%s\n' "Options: --host codex|claude|gemini|koda|sourcecraft|generic  --force  --dry-run"
  printf '%s\n' "         --no-root-files  --preserve-agents-file"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      [[ $# -ge 2 ]] || fail "--profile requires a name"
      PROFILES+=("$2")
      shift 2
      ;;
    --component)
      [[ $# -ge 2 ]] || fail "--component requires KIND:NAME"
      COMPONENTS+=("$2")
      shift 2
      ;;
    --host)
      [[ $# -ge 2 ]] || fail "--host requires a name"
      HOSTS+=("$2")
      shift 2
      ;;
    --force) shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --no-root-files) ROOT_FILES=0; shift ;;
    --preserve-agents-file) PRESERVE_AGENTS_FILE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage; fail "unknown argument: $1" ;;
  esac
done

[[ ${#PROFILES[@]} -gt 0 || ${#COMPONENTS[@]} -gt 0 ]] || fail "select at least one profile or component"

preflight_hosts() {
  local preflight_root preflight_home
  local -a selection_args host_args
  selection_args=()
  host_args=()
  local profile component host
  for profile in "${PROFILES[@]}"; do selection_args+=(--profile "$profile"); done
  for component in "${COMPONENTS[@]}"; do selection_args+=(--component "$component"); done
  for host in "${HOSTS[@]}"; do host_args+=(--host "$host"); done
  [[ $ROOT_FILES -eq 1 ]] || selection_args+=(--no-root-files)
  [[ $PRESERVE_AGENTS_FILE -eq 0 ]] || selection_args+=(--preserve-agents-file)

  # Check the real installation first, then build an isolated copy for host checks.
  "$SCRIPT_DIR/install.sh" "${selection_args[@]}" --dry-run >/dev/null
  preflight_root="$(mktemp -d)"
  preflight_home="$preflight_root/agents"
  if ! AGENTS_HOME="$preflight_home" "$SCRIPT_DIR/install.sh" "${selection_args[@]}" >/dev/null; then
    rm -rf "$preflight_root"
    return 1
  fi
  if [[ -f "$STATE_FILE" && ! -L "$STATE_FILE" ]]; then
    cp "$STATE_FILE" "$preflight_home/.ecosystem-state.json"
  fi
  if ! AGENTS_HOME="$preflight_home" AE_MANAGED_HOME="$DEST_HOME" \
    "$SCRIPT_DIR/connect.sh" --dry-run "${host_args[@]}"; then
    rm -rf "$preflight_root"
    return 1
  fi
  rm -rf "$preflight_root"
}

if [[ ${#HOSTS[@]} -gt 0 && $DRY_RUN -eq 0 ]]; then
  preflight_hosts
fi

state_matches() {
  local component_id="$1"
  local path="$2"
  command -v python3 >/dev/null 2>&1 || return 1
  python3 "$STATE_TOOL" matches --state "$STATE_FILE" --id "$component_id" \
    --path "$path" >/dev/null 2>&1
}

state_record() {
  local component_id="$1"
  local source_path="$2"
  local installed_path="$3"
  command -v python3 >/dev/null 2>&1 || return 0
  python3 "$STATE_TOOL" set --state "$STATE_FILE" --id "$component_id" \
    --source "$source_path" --installed "$installed_path"
}

TEMP_COMPONENTS="$(mktemp)"
TEMP_INSTALLED="$(mktemp)"
TEMP_MERGED="$(mktemp)"
TEMP_EXPLICIT="$(mktemp)"
trap 'rm -f "$TEMP_COMPONENTS" "$TEMP_INSTALLED" "$TEMP_MERGED" "$TEMP_EXPLICIT"' EXIT
if [[ ${#PROFILES[@]} -gt 0 ]]; then
  for profile in "${PROFILES[@]}"; do
    expand_profile "$ROOT" "$profile" >> "$TEMP_COMPONENTS"
  done
fi
if [[ ${#COMPONENTS[@]} -gt 0 ]]; then
  for component in "${COMPONENTS[@]}"; do
    printf '%s\n' "$component" >> "$TEMP_COMPONENTS"
  done
fi

mapfile_compat() {
  local line
  while IFS= read -r line; do
    [[ -n "$line" ]] && printf '%s\0' "$line"
  done
}

declare -a UNIQUE_COMPONENTS=()
while IFS= read -r -d '' component; do
  UNIQUE_COMPONENTS+=("$component")
done < <(awk '!seen[$0]++' "$TEMP_COMPONENTS" | mapfile_compat)

if [[ $DRY_RUN -eq 0 && $ROOT_FILES -eq 1 ]]; then
  mkdir -p "$DEST_HOME/skills" "$DEST_HOME/agents" "$DEST_HOME/rules" \
    "$DEST_HOME/local-models" "$DEST_HOME/tools"
fi

CONFLICTS=0
INSTALLED=0
for component in "${UNIQUE_COMPONENTS[@]}"; do
  [[ "$component" == *:* ]] || fail "invalid component entry: $component"
  kind="${component%%:*}"
  name="${component#*:}"
  validate_name "$name"
  source_path="$(component_source "$ROOT" "$kind" "$name")"
  destination_path="$(component_destination "$DEST_HOME" "$kind" "$name")"
  [[ -e "$source_path" ]] || fail "catalog points to missing source: $source_path"
  [[ "$destination_path" == "$DEST_HOME"/* ]] || fail "destination escaped AGENTS_HOME"
  assert_no_symlink_traversal "$destination_path" "$DEST_HOME"

  if [[ -e "$destination_path" || -L "$destination_path" ]]; then
    if diff -qr "$source_path" "$destination_path" >/dev/null 2>&1; then
      printf 'unchanged  %s\n' "$component"
      printf '%s\n' "$component" >> "$TEMP_INSTALLED"
      [[ $DRY_RUN -eq 1 ]] || state_record "$component" "$source_path" "$destination_path"
      continue
    fi
    if state_matches "$component" "$destination_path"; then
      printf 'updating   %s\n' "$component"
    else
      printf 'conflict   %s (%s)\n' "$component" "$destination_path" >&2
      CONFLICTS=$((CONFLICTS + 1))
      continue
    fi
  fi

  if [[ $DRY_RUN -eq 1 ]]; then
    printf 'would-install  %s -> %s\n' "$component" "$destination_path"
    continue
  fi

  parent="$(dirname "$destination_path")"
  mkdir -p "$parent"
  assert_no_symlink_traversal "$destination_path" "$DEST_HOME"
  if [[ -d "$source_path" ]]; then
    rm -rf "$destination_path"
    cp -R "$source_path" "$destination_path"
  else
    cp "$source_path" "$destination_path"
  fi
  printf 'installed  %s\n' "$component"
  printf '%s\n' "$component" >> "$TEMP_INSTALLED"
  state_record "$component" "$source_path" "$destination_path"
  INSTALLED=$((INSTALLED + 1))
done

if [[ $ROOT_FILES -eq 1 ]]; then
  install_root_file() {
    local source_file="$1"
    local destination_file="$2"
    local state_id="root:$(basename "$destination_file")"
    assert_no_symlink_traversal "$destination_file" "$DEST_HOME"
    if [[ $DRY_RUN -eq 1 ]]; then
      if [[ -e "$destination_file" ]]; then
        if diff -q "$source_file" "$destination_file" >/dev/null 2>&1 || state_matches "$state_id" "$destination_file"; then
          return
        fi
        printf 'conflict   managed file (%s)\n' "$destination_file" >&2
        CONFLICTS=$((CONFLICTS + 1))
      else
        printf 'would-install  %s -> %s\n' "$state_id" "$destination_file"
      fi
      return
    fi
    if [[ -e "$destination_file" ]] && ! diff -q "$source_file" "$destination_file" >/dev/null 2>&1; then
      if state_matches "$state_id" "$destination_file"; then
        printf 'updating   managed file (%s)\n' "$destination_file"
      else
        printf 'conflict   managed file (%s)\n' "$destination_file" >&2
        CONFLICTS=$((CONFLICTS + 1))
        return
      fi
    elif [[ -e "$destination_file" ]]; then
      state_record "$state_id" "$source_file" "$destination_file"
      return
    fi
    cp "$source_file" "$destination_file"
    state_record "$state_id" "$source_file" "$destination_file"
  }

  install_root_file "$ROOT/CONNECT.md" "$DEST_HOME/CONNECT.md"
  if [[ $PRESERVE_AGENTS_FILE -eq 0 ]]; then
    install_root_file "$ROOT/AGENTS.md" "$DEST_HOME/AGENTS.md"
  fi
  install_root_file "$ROOT/catalog/catalog.json" "$DEST_HOME/catalog.json"
  install_root_file "$ROOT/catalog/migrations.json" "$DEST_HOME/migrations.json"
fi

if [[ $DRY_RUN -eq 0 ]]; then
  if [[ ${#COMPONENTS[@]} -gt 0 ]]; then
    for component in "${COMPONENTS[@]}"; do
      if grep -Fxq "$component" "$TEMP_INSTALLED"; then
        printf '%s\n' "$component" >> "$TEMP_EXPLICIT"
      fi
    done
  fi

  merge_selection_file() {
    local destination_file="$1"
    local additions_file="$2"
    assert_no_symlink_traversal "$destination_file" "$DEST_HOME"
    : > "$TEMP_MERGED"
    if [[ -f "$destination_file" ]]; then
      cat "$destination_file" > "$TEMP_MERGED"
    fi
    cat "$additions_file" >> "$TEMP_MERGED"
    local staged_file
    staged_file="$(mktemp "$DEST_HOME/.ecosystem-selection.XXXXXX")"
    awk 'NF && !seen[$0]++' "$TEMP_MERGED" > "$staged_file"
    assert_no_symlink_traversal "$destination_file" "$DEST_HOME"
    mv "$staged_file" "$destination_file"
  }

  if [[ -f "$DEST_HOME/.ecosystem-installed" ]]; then
    cat "$DEST_HOME/.ecosystem-installed" > "$TEMP_MERGED"
  fi
  cat "$TEMP_INSTALLED" >> "$TEMP_MERGED"
  staged_installed="$(mktemp "$DEST_HOME/.ecosystem-installed.XXXXXX")"
  awk 'NF && !seen[$0]++' "$TEMP_MERGED" > "$staged_installed"
  assert_no_symlink_traversal "$DEST_HOME/.ecosystem-installed" "$DEST_HOME"
  mv "$staged_installed" "$DEST_HOME/.ecosystem-installed"

  if [[ $CONFLICTS -eq 0 ]]; then
    : > "$TEMP_COMPONENTS"
    if [[ ${#PROFILES[@]} -gt 0 ]]; then
      printf '%s\n' "${PROFILES[@]}" > "$TEMP_COMPONENTS"
    fi
    merge_selection_file "$DEST_HOME/.ecosystem-profiles" "$TEMP_COMPONENTS"
  fi
  merge_selection_file "$DEST_HOME/.ecosystem-components" "$TEMP_EXPLICIT"
fi

if [[ ${#HOSTS[@]} -gt 0 && $DRY_RUN -eq 0 && $CONFLICTS -eq 0 ]]; then
  host_args=()
  for host in "${HOSTS[@]}"; do
    host_args+=(--host "$host")
  done
  "$SCRIPT_DIR/connect.sh" "${host_args[@]}"
fi

printf 'Finished: %d installed, %d conflicts.\n' "$INSTALLED" "$CONFLICTS"
[[ $CONFLICTS -eq 0 ]] || exit 2
