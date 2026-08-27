#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -gt 0 ]]; then
  exec "$SCRIPT_DIR/install.sh" "$@"
fi

printf '.agents bootstrap\n\n'
"$SCRIPT_DIR/list.sh"
printf '\nSelect comma-separated profiles [core]: '
IFS= read -r profile_input
profile_input="${profile_input:-core}"

args=()
old_ifs="$IFS"
IFS=','
for profile in $profile_input; do
  profile="${profile//[[:space:]]/}"
  [[ -n "$profile" ]] && args+=(--profile "$profile")
done
IFS="$old_ifs"

printf 'Connect hosts, comma-separated (codex,claude,gemini,koda,sourcecraft,generic) [generic]: '
IFS= read -r host_input
host_input="${host_input:-generic}"
IFS=','
for host in $host_input; do
  host="${host//[[:space:]]/}"
  [[ -n "$host" ]] && args+=(--host "$host")
done
IFS="$old_ifs"

printf '\nPlanned command:\n  %q' "$SCRIPT_DIR/install.sh"
printf ' %q' "${args[@]}"
printf '\nContinue? [y/N] '
IFS= read -r answer
[[ "$answer" == "y" || "$answer" == "Y" ]] || exit 0
exec "$SCRIPT_DIR/install.sh" "${args[@]}"
