#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

declare -a PROFILES=()
declare -a COMPONENTS=()
declare -a HOSTS=()
declare -a INSTALL_OPTIONS=()
declare -a SELECTION_NAMES=()

usage() {
  printf '%s\n' 'Usage: agents.sh setup'
  printf '%s\n' '       agents.sh setup --work NAME [--work NAME ...] --app NAME'
  printf '%s\n' 'Work names: code, research, writing, design, video, complex, local-ai, all'
  printf '%s\n' 'Apps: codex, claude, gemini, kimi, koda, sourcecraft, generic'
}

contains() {
  local value="$1"
  shift
  local current
  for current in "$@"; do [[ "$current" == "$value" ]] && return 0; done
  return 1
}

add_profile() {
  local profile="$1"
  if [[ ${#PROFILES[@]} -eq 0 ]] || ! contains "$profile" "${PROFILES[@]}"; then
    PROFILES+=("$profile")
  fi
}

add_host() {
  local host="$1"
  case "$host" in
    codex|claude|gemini|kimi|koda|sourcecraft|generic) ;;
    *) printf 'error: unsupported AI application: %s\n' "$host" >&2; exit 1 ;;
  esac
  if [[ ${#HOSTS[@]} -eq 0 ]] || ! contains "$host" "${HOSTS[@]}"; then
    HOSTS+=("$host")
  fi
}

add_selection_name() {
  local name="$1"
  if [[ ${#SELECTION_NAMES[@]} -eq 0 ]] || ! contains "$name" "${SELECTION_NAMES[@]}"; then
    SELECTION_NAMES+=("$name")
  fi
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

add_work() {
  local work="$1"
  if [[ "$work" != all && ${#PROFILES[@]} -gt 0 ]] && contains all "${PROFILES[@]}"; then
    printf 'error: "all" cannot be combined with another work choice\n' >&2
    exit 1
  fi
  case "$work" in
    code) add_profile software; add_selection_name 'Write and test code' ;;
    research) add_profile marketing; add_selection_name 'Research and marketing' ;;
    writing) add_profile content; add_selection_name 'Write documents and texts' ;;
    design) add_profile design; add_selection_name 'Design interfaces' ;;
    video) add_profile video; add_selection_name 'Make videos' ;;
    complex) add_profile context; add_selection_name 'Organize complex tasks' ;;
    local-ai) add_profile local-models; add_selection_name 'Use a local AI helper' ;;
    all)
      if [[ ${#PROFILES[@]} -gt 0 ]] && contains all "${PROFILES[@]}"; then return; fi
      [[ ${#PROFILES[@]} -eq 0 ]] || { printf 'error: "all" cannot be combined with another work choice\n' >&2; exit 1; }
      add_profile all
      add_selection_name 'Everything'
      ;;
    *) printf 'error: unsupported work choice: %s\n' "$work" >&2; exit 1 ;;
  esac
}

add_work_list() {
  local input="$1" item
  local old_ifs="$IFS"
  IFS=',' read -r -a work_items <<< "$input"
  IFS="$old_ifs"
  [[ ${#work_items[@]} -gt 0 ]] || { printf 'error: choose at least one work area\n' >&2; exit 1; }
  for item in "${work_items[@]}"; do
    item="$(trim "$item")"
    [[ -n "$item" ]] || { printf 'error: empty work choice\n' >&2; exit 1; }
    add_work "$item"
  done
}

add_interactive_choices() {
  local input="$1" item work
  local old_ifs="$IFS"
  IFS=',' read -r -a choice_items <<< "$input"
  IFS="$old_ifs"
  [[ ${#choice_items[@]} -gt 0 ]] || { printf 'error: choose at least one number\n' >&2; exit 1; }
  for item in "${choice_items[@]}"; do
    item="$(trim "$item")"
    case "$item" in
      1) work=code ;;
      2) work=research ;;
      3) work=writing ;;
      4) work=design ;;
      5) work=video ;;
      6) work=complex ;;
      7) work=local-ai ;;
      8) work=all ;;
      *) printf 'error: unsupported choice: %s\n' "$item" >&2; exit 1 ;;
    esac
    add_work "$work"
  done
}

interactive=0
human_work_selected=0
if [[ $# -eq 0 ]]; then
  interactive=1
else
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --work)
        [[ $# -ge 2 ]] || { printf 'error: --work requires a name\n' >&2; exit 1; }
        human_work_selected=1
        add_work_list "$2"; shift 2 ;;
      --app|--host)
        [[ $# -ge 2 ]] || { printf 'error: %s requires a name\n' "$1" >&2; exit 1; }
        add_host "$2"; shift 2 ;;
      --profile)
        [[ $# -ge 2 ]] || { printf 'error: --profile requires a name\n' >&2; exit 1; }
        add_profile "$2"; shift 2 ;;
      --component)
        [[ $# -ge 2 ]] || { printf 'error: --component requires a name\n' >&2; exit 1; }
        COMPONENTS+=("$2"); shift 2 ;;
      --force|--dry-run|--no-root-files|--preserve-agents-file)
        INSTALL_OPTIONS+=("$1"); shift ;;
      -h|--help) usage; exit 0 ;;
      *) printf 'error: unknown setup option: %s\n' "$1" >&2; usage >&2; exit 1 ;;
    esac
  done
fi

if [[ $interactive -eq 1 ]]; then
  printf '.agents setup\n\n'
  printf '%s\n' 'Choose one or more areas. Common checks and helpers are added automatically.'
  printf '%s\n' '  1) Write and test code'
  printf '%s\n' '  2) Research and marketing'
  printf '%s\n' '  3) Write documents and texts'
  printf '%s\n' '  4) Design interfaces'
  printf '%s\n' '  5) Make videos'
  printf '%s\n' '  6) Organize complex tasks'
  printf '%s\n' '  7) Use a local AI helper'
  printf '%s\n' '  8) Everything'
  printf 'Your choices (for example 1,5) [1]: '
  IFS= read -r choices
  choices="${choices:-1}"
  add_interactive_choices "$choices"
  printf 'AI application (codex, claude, gemini, kimi, koda, sourcecraft, generic) [generic]: '
  IFS= read -r app
  add_host "${app:-generic}"
fi

[[ ${#PROFILES[@]} -gt 0 || ${#COMPONENTS[@]} -gt 0 ]] || {
  printf 'error: choose at least one work area\n' >&2
  exit 1
}
if [[ ${#HOSTS[@]} -eq 0 && ( $interactive -eq 1 || $human_work_selected -eq 1 ) ]]; then
  add_host generic
fi
add_profile core

args=()
for profile in "${PROFILES[@]}"; do args+=(--profile "$profile"); done
if [[ ${#COMPONENTS[@]} -gt 0 ]]; then
  for component in "${COMPONENTS[@]}"; do args+=(--component "$component"); done
fi
if [[ ${#HOSTS[@]} -gt 0 ]]; then
  for host in "${HOSTS[@]}"; do args+=(--host "$host"); done
fi
if [[ ${#INSTALL_OPTIONS[@]} -gt 0 ]]; then
  args+=("${INSTALL_OPTIONS[@]}")
fi

if [[ $interactive -eq 1 ]]; then
  printf '\nYou selected: '
  separator=''
  if [[ ${#SELECTION_NAMES[@]} -gt 0 ]]; then
    for selection in "${SELECTION_NAMES[@]}"; do
      printf '%s%s' "$separator" "$selection"
      separator=', '
    done
  fi
  printf '\nAI application: %s\n' "${HOSTS[*]}"
  printf 'Continue? [y/N] '
  IFS= read -r answer
  [[ "$answer" == 'y' || "$answer" == 'Y' ]] || exit 0
fi

exec "$SCRIPT_DIR/install.sh" "${args[@]}"
