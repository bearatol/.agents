#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

RUNTIME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_PATH=""
PORT="9944"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      [[ $# -ge 2 ]] || { printf 'error: --model requires a path\n' >&2; exit 1; }
      MODEL_PATH="$2"
      shift 2
      ;;
    --port)
      [[ $# -ge 2 ]] || { printf 'error: --port requires a number\n' >&2; exit 1; }
      PORT="$2"
      shift 2
      ;;
    -h|--help)
      printf 'Usage: %s --model /absolute/model/path [--port 9944]\n' "$0"
      exit 0
      ;;
    *) printf 'error: unknown argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done

[[ -n "$MODEL_PATH" && "$MODEL_PATH" == /* && -d "$MODEL_PATH" ]] || {
  printf 'error: --model must be an existing absolute directory\n' >&2
  exit 1
}
[[ "$PORT" =~ ^[0-9]+$ && "$PORT" -ge 1024 && "$PORT" -le 65535 ]] || {
  printf 'error: port must be between 1024 and 65535\n' >&2
  exit 1
}
PYTHON="$RUNTIME_DIR/.venv/bin/python"
[[ -x "$PYTHON" ]] || { printf 'error: run setup.sh first\n' >&2; exit 1; }

printf 'Starting loopback-only MLX server on 127.0.0.1:%s\n' "$PORT"
exec "$PYTHON" -m mlx_lm.server --model "$MODEL_PATH" --host 127.0.0.1 --port "$PORT"
