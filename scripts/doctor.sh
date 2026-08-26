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
ERRORS=0
WARNINGS=0

error() { printf 'ERROR: %s\n' "$*" >&2; ERRORS=$((ERRORS + 1)); }
warn() { printf 'WARN: %s\n' "$*" >&2; WARNINGS=$((WARNINGS + 1)); }

for profile_file in "$ROOT"/profiles/*.profile; do
  while IFS= read -r component; do
    [[ -z "$component" || "$component" == \#* || "$component" == profile:* ]] && continue
    kind="${component%%:*}"
    name="${component#*:}"
    source_path="$(component_source "$ROOT" "$kind" "$name")"
    [[ -e "$source_path" ]] || error "missing source for $component"
  done < "$profile_file"
done

if ! command -v python3 >/dev/null 2>&1; then
  warn "python3 is unavailable; catalog JSON validation skipped"
else
  python3 -m json.tool "$ROOT/catalog/catalog.json" >/dev/null || error "invalid catalog JSON"
fi

if grep -R -n -E --exclude-dir=.git --exclude='doctor.sh' \
  --exclude='README*.md' --exclude='*.md.example' \
  '[А-Яа-яЁё]' "$ROOT" >/dev/null 2>&1; then
  error "Cyrillic text found in machine-facing repository content"
fi

if grep -R -n -E --exclude-dir=.git --exclude='doctor.sh' '/Users/[^/]+|/home/[^/]+' \
  "$ROOT" >/dev/null 2>&1; then
  error "machine-specific home path found"
fi

if find "$ROOT" -type f \( -name '*.safetensors' -o -name '*.gguf' -o -name '*.bin' \
  -o -name '*.pem' -o -name '*.key' -o -name '.env' \) -print -quit | grep -q .; then
  error "forbidden secret or model artifact found"
fi

if [[ -f "$DEST_HOME/.ecosystem-installed" ]]; then
  while IFS= read -r component; do
    [[ -z "$component" ]] && continue
    kind="${component%%:*}"
    name="${component#*:}"
    destination_path="$(component_destination "$DEST_HOME" "$kind" "$name")"
    [[ -e "$destination_path" ]] || warn "installed manifest entry is missing: $component"
  done < "$DEST_HOME/.ecosystem-installed"
else
  warn "no installation manifest at $DEST_HOME/.ecosystem-installed"
fi

printf 'Doctor finished: %d errors, %d warnings.\n' "$ERRORS" "$WARNINGS"
[[ $ERRORS -eq 0 ]]
