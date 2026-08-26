#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
ROOT="$(repo_root)"
DEST_HOME="$(agents_home)"

[[ -d "$ROOT/.git" ]] || fail "update requires a Git clone"
[[ -f "$DEST_HOME/.ecosystem-profiles" ]] || fail "no installed profile manifest found"

git -C "$ROOT" pull --ff-only
args=()
while IFS= read -r profile; do
  [[ -n "$profile" ]] && args+=(--profile "$profile")
done < "$DEST_HOME/.ecosystem-profiles"
"$SCRIPT_DIR/install.sh" "${args[@]}"
"$SCRIPT_DIR/doctor.sh"
