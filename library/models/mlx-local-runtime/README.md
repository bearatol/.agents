# MLX Local Runtime

Optional helper for running a compatible text model locally on Apple Silicon.
No weights or Python environment are included in this repository.

## Requirements

- macOS on Apple Silicon
- Python 3.10 or newer
- Enough memory for the selected model and context size
- A model that the user is permitted to download and use

## Setup

Choose a verified `mlx-lm` release and install it into an isolated environment:

```bash
./setup.sh --version VERSION
```

Run a local model in the foreground, bound to loopback only:

```bash
./run.sh --model /absolute/path/to/model --port 9944
```

Press `Ctrl-C` to stop it. Never expose an unauthenticated inference server to
a LAN or the public internet. Record measured behavior in a copy of
`spec-template.md` before delegating real work to the model.
