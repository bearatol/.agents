#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -gt 0 ]]; then
  exec "$SCRIPT_DIR/install.sh" "$@"
fi

printf '.agents bootstrap\n\n'
printf '%s\n' 'Foundation is always included. Choose one work pack and one host.'
printf 'Work pack (software, marketing, content, design, video, context, local-models) [software]: '
IFS= read -r work_pack
work_pack="${work_pack:-software}"

case "$work_pack" in
  software|marketing|content|design|video|context|local-models) ;;
  *)
    printf 'error: unsupported work pack: %s\n' "$work_pack" >&2
    exit 1
    ;;
esac

printf 'Host (codex, claude, gemini, koda, sourcecraft, generic) [generic]: '
IFS= read -r host
host="${host:-generic}"

case "$host" in
  codex|claude|gemini|koda|sourcecraft|generic) ;;
  *)
    printf 'error: unsupported host: %s\n' "$host" >&2
    exit 1
    ;;
esac

args=(--profile core --profile "$work_pack" --host "$host")

printf '\nPlanned command:\n  %q' "$SCRIPT_DIR/install.sh"
printf ' %q' "${args[@]}"
printf '\nContinue? [y/N] '
IFS= read -r answer
[[ "$answer" == "y" || "$answer" == "Y" ]] || exit 0
exec "$SCRIPT_DIR/install.sh" "${args[@]}"
