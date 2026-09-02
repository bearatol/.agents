# ADR 0001: Ownership layers and the activation registry

- Status: accepted
- Date: 2026-09-02
- Supersedes: nothing
- Related: `docs/ARCHITECTURE.md`, `CONNECT.md`, `scripts/registry.py`

## Context

`docs/ARCHITECTURE.md` already names three ownership layers: the project
checkout, the managed runtime under `AGENTS_HOME`, and the personal workspace.
The code does not enforce that split, and a real installation shows what the
gap costs.

Measured on one machine:

- The canonical catalog is at ecosystem version 0.6.0 while the installed
  runtime `catalog.json` is still at 0.3.1.
- `AGENTS_HOME/skills` holds 170 directories. The canonical catalog declares
  34 of them. A third-party skill installer records 116 in its own lock file.
  Nothing at all records the remaining 26.
- Six names are claimed twice, by the catalog and by that third-party tool.
- `doctor` reports four diverged targets and cannot say more than "this
  differs", because it compares hashes and has no notion of who owns a path.

Two failure modes follow from this. An installer that treats every runtime
path as its own would overwrite skills the user deliberately installed. An
installer that refuses to touch anything it did not write can never repair
its own drift. Today the project avoids the first by refusing conflicts, which
leaves drift permanent and makes `doctor` fail with no route forward.

The development layout makes it harder still: a contributor may point
`AGENTS_HOME` at the checkout itself, so canonical sources and generated
projections share one directory.

## Decision

### 1. Three owners, one owner per path

- **Source** is the versioned checkout. `catalog/`, `library/`, `profiles/`
  and `scripts/` are canonical there and are never written by runtime commands.
- **Managed runtime** is `AGENTS_HOME`. Its top-level `skills/`, `agents/`,
  `rules/`, `tools/`, `orchestration/`, `local-models/`, `catalog.json` and
  `catalog.schema.json` are projections of the source.
- **Personal workspace** is `workspace/`. It holds user material and neutral
  team records, and no install step writes there.

Every activated path belongs to exactly one owner. Ownership decides who may
write, and nothing else. It does not grant permissions to a host.

### 2. Ownership is derived from evidence, not assumed

A path is attributed by the records that already exist, in this order:

1. Declared by the canonical catalog, so the owner is `catalog`.
2. Recorded in the personal workspace index, so the owner is `workspace`.
3. Recorded in a third-party lock file inside `AGENTS_HOME`, so the owner is
   `foreign`.
4. Recorded by nothing, so the owner is `unknown`.

A path claimed by more than one record is a collision. A collision is reported
and never resolved silently, because both claimants may be right about intent
and only the user knows which content should survive.

### 3. The registry is derived before it is stored

The activation registry answers, for each activated path: who owns it, where
it came from, what its content hash is, how far it was reviewed, which hosts
publish it, and how it stands against its source.

It is computed from evidence on every run. No new state file is written in
this step. Persisting the registry becomes useful only when it must hold a
decision that cannot be derived, which is a review decision about a foreign or
unknown path, and that arrives with `apply`.

Deriving first has a practical benefit: the registry cannot itself go stale,
so it can be trusted while the drift it describes is being resolved.

### 4. plan, apply, reconcile

- `plan` computes what an installation would change and writes nothing.
- `apply` writes only paths whose owner is `catalog`, and only when the current
  content matches either the canonical source or the hash this project last
  installed. Any other path is skipped and reported.
- `reconcile` reports divergence and conflict. It is a read operation. It never
  deletes, moves, or overwrites, and it never repairs a path on its own.

`reconcile` staying read-only is the load-bearing rule here. The word invites
an automatic fix, and an automatic fix over a foreign or unknown path is data
loss.

### 5. Compatibility mode stays, and stays explicit

Using the checkout as `AGENTS_HOME` remains supported. It is a development
convenience, not the normal layout. Commands may warn that owners share one
directory. They must not migrate that directory, because the same paths carry
both canonical sources and generated copies.

### 6. Migration is opt-in and additive

When a separate runtime is introduced later, it follows this order: report the
current state, run a dry run, create a new clean runtime directory, then copy
only material the user has explicitly trusted. Existing directories are left
as they are. No command rewrites a user's runtime in place.

## Registry model

One entry per activated path.

| Field | Meaning |
| --- | --- |
| `id` | `kind:name`, matching catalog component identifiers |
| `kind` | `skill`, `agent`, `rule`, `tool`, `orchestration`, `model` |
| `name` | directory or file name inside the runtime |
| `path` | path relative to `AGENTS_HOME` |
| `owner` | `catalog`, `workspace`, `foreign`, or `unknown` |
| `provenance` | the record that attributes the path, with its reference |
| `hash` | content digest of the installed path |
| `trust` | `managed`, `trusted`, `declared`, or `unreviewed` |
| `targets` | connected hosts that publish this path |
| `state` | `current`, `managed-stale`, `locally-modified`, `missing`, `present` |
| `collisions` | other records claiming the same path |

Trust values mean:

- `managed`: content matches its canonical source.
- `trusted`: a personal workspace item the user marked as trusted.
- `declared`: a third-party tool records where it came from, and no review by
  this project happened.
- `unreviewed`: nothing records it.

Trust never implies permission to run code or reach the network. It only
answers whether an owner may write the path.

## Consequences

Good:

- `doctor` gains a route forward. Each diverged path now carries an owner and
  a named decision instead of a bare mismatch.
- The 136 skills that no project record claims stop being invisible, and stay
  untouched.
- `plan` and `reconcile` are safe to run anywhere, including CI, because they
  cannot write.
- Windows and POSIX installers can share one Python planner, with the shells
  reduced to thin wrappers.

Costs:

- Every run recomputes hashes for the activated tree. Measured at roughly one
  second for 170 skills, which is acceptable for a command a person runs by
  hand and worth revisiting if the tree grows much larger.
- Reading a third-party lock file couples this project to a format it does not
  control. The reader treats the file as untrusted input, tolerates a missing
  or invalid file, and never executes anything from it.
- Users with existing collisions must make a decision the tool will not make
  for them.

## Alternatives considered

**Let the installer own every path under the runtime.** Simple, and it would
clear all current drift in one run. Rejected: it would delete 136 skills the
user installed on purpose.

**Keep only content hashes, as the state file does today.** Already
implemented and cheap. Rejected: a hash says a path differs, not who is
entitled to change it, so the tool can only ever refuse.

**Migrate automatically to a clean runtime directory.** It would resolve the
mixed layout at once. Rejected: it moves user data without a decision, and the
value is small next to that risk.

**Persist the registry immediately.** Rejected for this step: a stored registry
adds a file that can itself drift, before there is any decision worth storing.
