# Reproduce the same setup on another computer

Most users do not need `export` or `restore`. Clone your repository on the new
computer and run `setup` again.

The commands in this document are for people who must reproduce the exact same
`.agents` version, selected work areas, and AI connections. The exported
`agents.lock.json` is an installation receipt. It is not a backup and contains
none of the user's prompts, skills, projects, or files.

`.agents` can reproduce its managed workspace on another computer. It is not a
whole-machine backup and does not move accounts, credentials, applications,
plugins, model weights, or unrelated dotfiles.

The repository itself also carries `workspace/library/` and
`workspace/projects/`: personal reusable material and neutral collaboration
history. Put personal work in a private repository. A public fork makes those
files public as well.

## Export on the old computer

First resolve any state reported by `status`. Use a trusted checkout with no
uncommitted changes so its contents match the recorded commit, then export to a
new file:

```bash
./scripts/agents.sh status
./scripts/agents.sh export ./agents.lock.json
```

PowerShell uses the same command names through `scripts/agents.ps1`. Export
refuses a dirty checkout, any installed drift, and an existing output path. The
JSON file contains exactly six fields: schema version, ecosystem version, full
Git commit, selected profiles, explicit components, and hosts.

The lock intentionally does not duplicate personal library content. Git moves
that content; the lock reproduces the installed selection and adapter choices.

## Prepare the new computer

Install Git, Python 3, and the AI host applications you intend to use. Clone the
repository, open the lock as text, and review its full commit SHA. Select that
commit through a separate, explicit Git action and keep the checkout free of
local and untracked changes. Restore itself never fetches or changes the
checkout, and refuses to run from a dirty worktree.

## Restore

With the reviewed commit already checked out:

```bash
./scripts/agents.sh restore ./agents.lock.json
./scripts/agents.sh library check
./scripts/agents.sh doctor
```

Restore rejects malformed, oversized, duplicate-key, future-schema, unknown
profile/component/host, version-mismatched, foreign-history, and checkout-
mismatched manifests. Values select logical IDs only; they cannot control paths,
commands, remotes, environment variables, deletion, or overwrite behavior.

Before persistent writes, restore preflights the selected components, managed
root files, and host destinations. Unmanaged or locally modified targets are
preserved and reported as conflicts. If an operating-system I/O error interrupts
the apply phase, completed targets remain recorded and the same restore command
is designed to converge safely after the underlying error is fixed.

## Resolve status results

- `missing`: rerun setup or restore after confirming why the target disappeared.
- `managed-stale`: run the approved update or reinstall the recorded selection.
- `locally-modified`: keep and back up the local version, or remove it manually
  only after deciding to accept the managed source.
- `host-conflicting`: inspect the exact host path, preserve the existing file,
  and reconnect only after resolving ownership.

There is deliberately no force flag in the portable manifest and no automatic
cleanup. These boundaries keep a copied lock from gaining filesystem, network,
or destructive authority.
