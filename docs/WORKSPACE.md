# Personal workspace and AI teams

## The simple model

`.agents` has three layers:

1. The personal library stores reusable work.
2. Adapters let AI applications read the shared environment.
3. Team projects let several applications exchange tasks, results, reviews,
   and decisions without depending on one vendor.

Git moves these files between computers. It does not move accounts, API keys,
applications, or model weights.

## Store any kind of reusable work

Initialize once, then add a file or directory:

```bash
./scripts/agents.sh library init
./scripts/agents.sh library add skill release-check ./release-check
./scripts/agents.sh library list
./scripts/agents.sh library trust skill release-check
./scripts/agents.sh library activate skill release-check
./scripts/agents.sh connect codex claude gemini kimi
./scripts/agents.sh library check
```

Windows uses the same words:

```powershell
.\scripts\agents.ps1 library init
.\scripts\agents.ps1 library add skill release-check .\release-check
.\scripts\agents.ps1 library list
```

Data lives at `workspace/library/<type>/<name>/`. The storage contract does not
enumerate types. If a future AI ecosystem introduces a new artifact, use a new
lowercase type such as `memory`, `workflow`, or `evaluation`; old versions can
still preserve and inventory it.

An import starts as `inactive`. Review its files before running `trust`. Trust
records the reviewed checksum; it does not execute scripts or automatically
grant an adapter access. If trusted content changes outside the CLI, `check`
fails and asks for a new reviewed import.

`activate skill` copies a reviewed skill into the installed shared skill
directory without overwriting anything. Run `connect` afterward so every
selected host sees it. This first version activates skills only. Rules, prompts,
specialists, MCP descriptions, model settings, and unknown future types are
already portable data, but remain inactive until a trusted adapter supports
their semantics.

The importer rejects path traversal, links, special files, nested Git
repositories, likely credentials, private keys, model weights, oversized
files, and overwrite attempts. Detection cannot find every secret. Review
`git diff --staged` before publishing and use a private repository for personal
work.

## Connect several AI applications

One setup command may select several adapters:

```bash
./scripts/agents.sh setup --work all \
  --app codex --app claude --app gemini --app kimi
```

Or connect already installed content later:

```bash
./scripts/agents.sh connect codex claude gemini kimi
```

The facade is stable; adapters translate it to host conventions. Codex,
Claude, and Gemini receive host-native skills and specialist wrappers. Kimi
uses its documented native discovery of `~/.agents/skills`. A future or custom
host can always use the `generic` adapter and read `AGENTS.md`, `CONNECT.md`,
and neutral team files. Unknown library types remain data until a trusted
adapter explicitly supports their meaning.

## Coordinate a team without vendor lock-in

Create a project and name every participating host:

```bash
./scripts/agents.sh team init release \
  --objective "Prepare a safe release" \
  --coordinator codex \
  --member claude --member gemini --member kimi
```

Assign a specialist role to one host and independent review to others:

```bash
./scripts/agents.sh team task release implementation \
  --title "Implement the release change" \
  --objective "Return a tested implementation" \
  --role engineer --worker claude \
  --reviewer gemini --reviewer kimi \
  --scope scripts --accept "All tests pass"
```

The worker records a result:

```bash
./scripts/agents.sh team result release implementation \
  --worker claude --status complete --summary "Change implemented" \
  --evidence "Tests pass"
```

Each reviewer writes its own file:

```bash
./scripts/agents.sh team review release implementation \
  --reviewer gemini --verdict approve --summary "Tests and diff verified"

./scripts/agents.sh team review release implementation \
  --reviewer kimi --verdict approve --summary "Independent review passed"
```

The recorded coordinator makes the final decision only after every assigned
review exists:

```bash
./scripts/agents.sh team decide release implementation \
  --coordinator codex --decision accept --summary "Accepted after two reviews"

./scripts/agents.sh team status release
```

Every task has an attempt number. A retry creates the next immutable attempt;
stale results from an older attempt are rejected. Results are separated by
worker and reviews by reviewer, so simultaneous writers do not overwrite each
other. Host names are attribution, not authentication: operating-system and
Git permissions remain the enforcement boundary.

The CLI coordinates files; it does not launch AI applications, spend tokens,
or use the network. A human, a host-native coordinator, or future UI may
dispatch the neutral task files.
