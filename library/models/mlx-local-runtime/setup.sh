#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

RUNTIME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      [[ $# -ge 2 ]] || { printf 'error: --version requires a value\n' >&2; exit 1; }
      VERSION="$2"
      shift 2
      ;;
    -h|--help)
      printf 'Usage: %s --version VERIFIED_MLX_LM_VERSION\n' "$0"
      exit 0
      ;;
    *) printf 'error: unknown argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done

[[ -n "$VERSION" ]] || { printf 'error: provide a verified mlx-lm version\n' >&2; exit 1; }
[[ "$VERSION" =~ ^[0-9][0-9A-Za-z.+-]*$ ]] || {
  printf 'error: version contains unsupported characters\n' >&2
  exit 1
}
[[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]] || {
  printf 'error: this helper supports macOS on Apple Silicon only\n' >&2
  exit 1
}
command -v python3 >/dev/null 2>&1 || { printf 'error: python3 is required\n' >&2; exit 1; }

python3 -m venv "$RUNTIME_DIR/.venv"
"$RUNTIME_DIR/.venv/bin/python" -m pip install --upgrade pip
"$RUNTIME_DIR/.venv/bin/python" -m pip install "mlx-lm==$VERSION"
printf 'Installed mlx-lm %s in %s/.venv\n' "$VERSION" "$RUNTIME_DIR"
