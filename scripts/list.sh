#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
ROOT="$(repo_root)"

if [[ $# -eq 0 ]]; then
  printf 'Available profiles:\n'
  for file in "$ROOT"/profiles/*.profile; do
    name="$(basename "$file" .profile)"
    printf '  %s\n' "$name"
  done
  printf '\nUse: %s --profile NAME\n' "$0"
  exit 0
fi

[[ $# -eq 2 && "$1" == "--profile" ]] || fail "usage: $0 [--profile NAME]"
printf 'Components in profile %s:\n' "$2"
expand_profile "$ROOT" "$2" | awk '!seen[$0]++ { print "  " $0 }'
