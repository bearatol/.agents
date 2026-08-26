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

declare -a PROFILES=()
declare -a COMPONENTS=()
declare -a HOSTS=()
FORCE=0
DRY_RUN=0
ROOT_FILES=1

usage() {
  printf '%s\n' "Usage: $0 --profile NAME [--profile NAME ...] [options]"
  printf '%s\n' "       $0 --component KIND:NAME [--component KIND:NAME ...] [options]"
  printf '%s\n' "Options: --host codex|claude|gemini|generic  --force  --dry-run  --no-root-files"
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
    --force) FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --no-root-files) ROOT_FILES=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage; fail "unknown argument: $1" ;;
  esac
done

[[ ${#PROFILES[@]} -gt 0 || ${#COMPONENTS[@]} -gt 0 ]] || fail "select at least one profile or component"

TEMP_COMPONENTS="$(mktemp)"
TEMP_INSTALLED="$(mktemp)"
TEMP_MERGED="$(mktemp)"
trap 'rm -f "$TEMP_COMPONENTS" "$TEMP_INSTALLED" "$TEMP_MERGED"' EXIT
for profile in "${PROFILES[@]}"; do
  expand_profile "$ROOT" "$profile" >> "$TEMP_COMPONENTS"
done
for component in "${COMPONENTS[@]}"; do
  printf '%s\n' "$component" >> "$TEMP_COMPONENTS"
done

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
  mkdir -p "$DEST_HOME/skills" "$DEST_HOME/agents" "$DEST_HOME/rules" "$DEST_HOME/local-models"
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

  if [[ -e "$destination_path" || -L "$destination_path" ]]; then
    if diff -qr "$source_path" "$destination_path" >/dev/null 2>&1; then
      printf 'unchanged  %s\n' "$component"
      printf '%s\n' "$component" >> "$TEMP_INSTALLED"
      continue
    fi
    if [[ $FORCE -ne 1 ]]; then
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
  if [[ -d "$source_path" ]]; then
    rm -rf "$destination_path"
    cp -R "$source_path" "$destination_path"
  else
    cp "$source_path" "$destination_path"
  fi
  printf 'installed  %s\n' "$component"
  printf '%s\n' "$component" >> "$TEMP_INSTALLED"
  INSTALLED=$((INSTALLED + 1))
done

if [[ $DRY_RUN -eq 0 ]]; then
  install_root_file() {
    local source_file="$1"
    local destination_file="$2"
    if [[ -e "$destination_file" ]] && ! diff -q "$source_file" "$destination_file" >/dev/null 2>&1; then
      if [[ $FORCE -ne 1 ]]; then
        printf 'conflict   managed file (%s)\n' "$destination_file" >&2
        CONFLICTS=$((CONFLICTS + 1))
        return
      fi
    elif [[ -e "$destination_file" ]]; then
      return
    fi
    cp "$source_file" "$destination_file"
  }

  install_root_file "$ROOT/CONNECT.md" "$DEST_HOME/CONNECT.md"
  install_root_file "$ROOT/AGENTS.md" "$DEST_HOME/AGENTS.md"
  install_root_file "$ROOT/catalog/catalog.json" "$DEST_HOME/catalog.json"
fi

if [[ $DRY_RUN -eq 0 ]]; then
  if [[ -f "$DEST_HOME/.ecosystem-installed" ]]; then
    cat "$DEST_HOME/.ecosystem-installed" > "$TEMP_MERGED"
  fi
  cat "$TEMP_INSTALLED" >> "$TEMP_MERGED"
  awk 'NF && !seen[$0]++' "$TEMP_MERGED" > "$DEST_HOME/.ecosystem-installed"

  : > "$TEMP_MERGED"
  if [[ -f "$DEST_HOME/.ecosystem-profiles" ]]; then
    cat "$DEST_HOME/.ecosystem-profiles" > "$TEMP_MERGED"
  fi
  printf '%s\n' "${PROFILES[@]}" >> "$TEMP_MERGED"
  awk 'NF && !seen[$0]++' "$TEMP_MERGED" > "$DEST_HOME/.ecosystem-profiles"
fi

if [[ ${#HOSTS[@]} -gt 0 && $DRY_RUN -eq 0 ]]; then
  host_args=()
  for host in "${HOSTS[@]}"; do
    host_args+=(--host "$host")
  done
  "$SCRIPT_DIR/connect.sh" "${host_args[@]}"
fi

printf 'Finished: %d installed, %d conflicts.\n' "$INSTALLED" "$CONFLICTS"
[[ $CONFLICTS -eq 0 ]] || exit 2
