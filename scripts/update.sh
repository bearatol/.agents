#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"
ROOT="$(repo_root)"
DEST_HOME="$(agents_home)"

[[ $# -eq 1 ]] || fail "usage: $0 APPROVED_40_CHARACTER_COMMIT"
APPROVED_COMMIT="$1"
[[ "$APPROVED_COMMIT" =~ ^[0-9a-fA-F]{40}$ ]] || fail "approved commit must be a full 40-character SHA"

[[ -d "$ROOT/.git" ]] || fail "update requires a Git clone"
[[ -f "$DEST_HOME/.ecosystem-profiles" ]] || fail "no installed profile manifest found"

git -C "$ROOT" fetch --prune origin
UPSTREAM="$(git -C "$ROOT" rev-parse '@{u}')"
REMOTE_COMMIT="$(git -C "$ROOT" rev-parse "$UPSTREAM")"
RESOLVED_APPROVAL="$(git -C "$ROOT" rev-parse "$APPROVED_COMMIT^{commit}")"
[[ "$RESOLVED_APPROVAL" == "$REMOTE_COMMIT" ]] || \
  fail "approved commit does not match upstream HEAD: $REMOTE_COMMIT"
git -C "$ROOT" merge --ff-only "$RESOLVED_APPROVAL"
args=()
while IFS= read -r profile; do
  [[ -n "$profile" ]] && args+=(--profile "$profile")
done < "$DEST_HOME/.ecosystem-profiles"
"$SCRIPT_DIR/install.sh" "${args[@]}"
"$SCRIPT_DIR/doctor.sh"
