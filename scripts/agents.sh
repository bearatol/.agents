#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
ROOT="$(repo_root)"
DEST_HOME="$(agents_home)"

usage() {
  printf '%s\n' 'Usage: agents.sh setup [--work NAME ...] [--app NAME]'
  printf '%s\n' '       agents.sh status'
  printf '%s\n' '       agents.sh export OUTPUT.json'
  printf '%s\n' '       agents.sh restore MANIFEST.json'
  printf '%s\n' '       agents.sh doctor'
}

[[ $# -gt 0 ]] || { usage; exit 1; }
command_name="$1"
shift

case "$command_name" in
  setup)
    exec "$SCRIPT_DIR/bootstrap.sh" "$@"
    ;;
  status)
    [[ $# -eq 0 ]] || fail 'status takes no arguments'
    validate_agents_home "$DEST_HOME"
    exec python3 "$SCRIPT_DIR/environment.py" status \
      --repo "$ROOT" --home "$DEST_HOME" --user-home "$HOME"
    ;;
  export)
    [[ $# -eq 1 ]] || fail 'usage: agents.sh export OUTPUT.json'
    validate_agents_home "$DEST_HOME"
    exec python3 "$SCRIPT_DIR/environment.py" export \
      --repo "$ROOT" --home "$DEST_HOME" --user-home "$HOME" --output "$1"
    ;;
  restore)
    [[ $# -eq 1 ]] || fail 'usage: agents.sh restore MANIFEST.json'
    validate_agents_home "$DEST_HOME"
    manifest="$1"
    plan_file="$(mktemp)"
    preflight_root="$(mktemp -d)"
    trap 'rm -f "$plan_file"; rm -rf "$preflight_root"' EXIT
    python3 "$SCRIPT_DIR/environment.py" restore-plan \
      --repo "$ROOT" --manifest "$manifest" > "$plan_file"
    profiles=()
    components=()
    hosts=()
    while IFS=$'\t' read -r kind value; do
      case "$kind" in
        profile) profiles+=(--profile "$value") ;;
        component) components+=(--component "$value") ;;
        host) hosts+=(--host "$value") ;;
        *) fail 'invalid internal restore plan' ;;
      esac
    done < "$plan_file"
    [[ ${#profiles[@]} -gt 0 || ${#components[@]} -gt 0 ]] || \
      fail 'manifest selects no profiles or components'

    "$SCRIPT_DIR/install.sh" "${profiles[@]}" "${components[@]}" --dry-run
    if [[ ${#hosts[@]} -gt 0 ]]; then
      preflight_home="$preflight_root/agents"
      AGENTS_HOME="$preflight_home" "$SCRIPT_DIR/install.sh" \
        "${profiles[@]}" "${components[@]}" >/dev/null
      if [[ -f "$DEST_HOME/.ecosystem-state.json" ]]; then
        cp "$DEST_HOME/.ecosystem-state.json" "$preflight_home/.ecosystem-state.json"
      fi
      AGENTS_HOME="$preflight_home" "$SCRIPT_DIR/connect.sh" --dry-run "${hosts[@]}"
    fi

    if ! "$SCRIPT_DIR/install.sh" "${profiles[@]}" "${components[@]}"; then
      fail 'restore partially applied; resolve the reported error and rerun the same command'
    fi
    if [[ ${#hosts[@]} -gt 0 ]] && ! "$SCRIPT_DIR/connect.sh" "${hosts[@]}"; then
      fail 'restore partially applied; installed components are recorded and rerunning is safe'
    fi
    "$SCRIPT_DIR/doctor.sh"
    ;;
  doctor)
    [[ $# -eq 0 ]] || fail 'doctor takes no arguments'
    exec "$SCRIPT_DIR/doctor.sh"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    fail "unknown command: $command_name"
    ;;
esac
