# ADR 0002: A shared directory, external sources, and attested packages

- Status: accepted
- Date: 2026-09-02
- Extends: ADR 0001
- Related: `docs/ARCHITECTURE.md`, `scripts/registry.py`

## Context

ADR 0001 gave every activated path one owner and made ownership derivable.
That answered who may write a path. It left three questions open, and the
ecosystem has since answered parts of them for us.

`~/.agents` is no longer this project's private destination. Several hosts in
this project's own adapter set already discover skills there natively, a
third-party installer writes there, and a draft community specification
proposes it as the shared location for agent configuration at both the user
and workspace level. That specification is early and single-authored, so this
decision treats it as a convention worth matching rather than a standard to
depend on. The measured installation behind ADR 0001 shows the result of
shared use either way: 170 skill directories, of which this project declared
34 and a third-party lock file recorded 116.

So the project cannot keep treating that directory as its own. It also cannot
keep shipping its library inside itself. A repository that is at once the tool,
the content, and the destination gives a new user no way to take one without
the other two.

Packaging has also stopped being an open question. A vendor-neutral package
format now exists, supported by several major clients, and it deliberately
excludes trust, installation control, dependency resolution, and distribution.
The directory specification excludes ownership, installation, and removal.
Three specifications in a row describe where files sit and what they look
like. None describes who put them there, who may change them, or how to take
them away.

That is the space this project works in, and this ADR fixes the shape of it.

## Decision

### 1. The directory is shared, the tool is a tenant

`~/.agents` is a shared runtime with several writers. This project is one of
them. It matches the community directory layout where doing so is free, so
that other tools reading that location find what they expect, and it writes
only paths it owns under ADR 0001. Matching a layout is not the same as
depending on a specification: nothing in this tool may require that
specification to be correct, adopted, or maintained. Anything another writer put there is reported, never rewritten,
never deleted.

The repository that carries the tool is named for the tool. The directory
keeps its conventional name. Confusing the two is what made installing this
project feel like surrendering a shared directory.

A first run on an existing directory therefore starts by reporting what is
already installed rather than by changing anything.

### 2. Content leaves the tool

Skills, specialist prompts and rules move out of this repository into a
package repository of their own. The tool ships no content. Its own package
becomes the first row in the user's source list, added during setup and
removable like any other.

This is what makes the architecture honest: if the project's own library
cannot be expressed as an ordinary source, then no one else's can either.

### 3. Sources are data, not directories

A source is a record, not a reserved location. Each has an id, an address, a
pin, and a trust level. Addresses are a git URL, a local path, or a package
archive. Nothing about a source implies where it sits on disk; clones are
cached inside the runtime under a path the user never edits.

Two install modes:

- **Pinned.** The source is fetched at an exact revision, copied into the
  runtime, and hashed. This is how every consumer installs.
- **Linked.** A local path is used in place, for authoring. The working copy
  is the installed copy, so there is exactly one of it, and the registry
  records the source as linked rather than reporting perpetual drift.

Linked mode exists because the alternative is two copies of one skill, which
is the ownership confusion ADR 0001 removed, reintroduced by the author's own
workflow.

### 4. Identifiers are qualified, installed names stay flat

Hosts discover skills by scanning a flat directory, so the installed name must
be unique and unqualified. Internally every component is identified by its
source as well as its name.

When two sources claim one name, the tool does not choose. It reports the
collision and requires an explicit alias, recording the alias so the decision
survives updates. Renaming a component within a source is recorded as a
replacement, and installers apply those replacements when merging an installed
manifest.

### 5. Removal and deactivation are owned operations

`remove` deletes only the paths its target owns in the registry. A path
claimed by another source, aliased away, or written by hand is left alone and
reported. `disable` withdraws a component from the hosts without deleting it.

These are the operations that make the tool a package manager rather than an
installer, and they were impossible before ownership existed.

### 6. Packages carry evidence, and the tool is a witness

A source may publish an attestation: which scanner, at which version, examined
which content hash, and with what result. Attestations use existing supply
chain formats and signatures rather than a format invented here.

Rules that keep an attestation from becoming a decoration:

- A verdict binds to a content hash. When the content changes the verdict is
  void and the component returns to unreviewed.
- A verdict names the tool and version that produced it, so anyone can repeat
  the check and get the same answer.
- A verdict published by a source is a claim by that source. It is weighted by
  the trust the user granted that source, and may be recomputed locally.

Trust at the level of a source is what makes this usable. Reviewing 170
components by hand is not work anyone will do. Deciding about eight sources is.

When a scan finds a defect, the response depends on ownership. In a source we
publish, we fix it. In someone else's source we do not: the tool records the
verdict, withholds installation of critical findings, warns on the rest, and
leaves the decision with the user. The tool is a witness, not an editor of
other people's work. That is also the only role that scales.

### 7. Packages declare compatibility

A package declares its own version and the tool versions it works with. Until
that exists, moving the library out of this repository would produce a first
run that fetches a second repository of unknown compatibility, with nothing
able to detect the mismatch.

### 8. Reporting before serving

The first visual surface is a generated self-contained report file, produced
from the registry's existing output and opened directly from disk. It carries
no server and no listening port.

A local interface may follow once there are actions worth performing, and only
under fixed constraints: bound to the loopback interface, an ephemeral port
rather than a well-known one, a single-use token issued by the command line,
verification of request origin, no cross-origin access, and read-only unless
explicitly started otherwise.

The constraint is not decoration. A long-lived listener on a predictable port
that can read and modify this directory is reachable by any page the user
opens, and rebinding attacks defeat naive origin checks. A tool whose subject
is trust cannot ship that.

## Source record

| Field | Meaning |
| --- | --- |
| `id` | short stable name used to qualify component identifiers |
| `address` | git URL, local path, or package archive |
| `pin` | exact revision or version this source is installed at |
| `mode` | `pinned` or `linked` |
| `trust` | how far the user trusts what this source publishes |
| `attestation` | signature and scan evidence the source publishes, if any |
| `added_at` | when the user accepted this source |

## Order of work

Each step is usable on its own, and each is required by the next.

1. `remove` and `disable`, driven by ownership.
2. One real scanner integrated as a producer of verdicts, and the generated
   report file as the first visual surface.
3. Attestations and signing, first for the package we publish ourselves.
4. Package versions and compatibility declarations.
5. Sources as data, with pinned and linked modes.
6. The library moves to its own repository.
7. A local interface, under the constraints above, once actions exist.

Reordering steps 4 to 6 ahead of the rest produces a first run that cannot
work and cannot be diagnosed.

## Consequences

Good:

- Installing this tool onto a populated `~/.agents` becomes safe, and the
  first thing a user sees is an inventory of what they already have.
- The project's own content stops being privileged, which is what allows other
  people's libraries to be first-class.
- Scanner verdicts stop being single moments and become state that expires
  when content changes.
- Following the directory specification means other tools can read the same
  runtime without knowing about this one.

Costs:

- More concepts: source, pin, trust, alias, attestation. Every one of them has
  to earn its place in the command surface, and the surface is already wide.
- Splitting the library means the tool and its content can drift in version,
  which is why compatibility declarations come first.
- Reading a third-party record and a third-party scanner couples this project
  to formats it does not control. Both are treated as untrusted input.
- A draft specification may change under us, or be abandoned. Matching a layout
  is still cheaper than defining a competing one, and nothing depends on that
  specification surviving.

## Alternatives considered

**Keep the library in the tool.** One clone, no version skew, simplest first
run. Rejected: it makes the project a content bundle, and it gives no path for
anyone else's library to be treated the same way.

**Reserve a second directory in the user's home for packages.** Rejected: a
source with a reserved location is not one source among many, and a directory
that is both an editable checkout and an install source recreates the
ownership confusion ADR 0001 removed.

**Move off the shared directory to avoid conflicting with other tools.**
Rejected: that directory is where the ecosystem is converging, and the tool's
answer to shared use is ownership, not avoidance.

**Write our own scanner.** Rejected: several security vendors already publish
one, and the unclaimed work is keeping their verdicts attached to installed
state over time.

**Ship the local interface first, since navigating many components by hand is
the original problem.** Rejected for sequencing, not for merit: with no apply,
remove, or verdicts, it would present an empty surface, and it introduces a
listening service before there is anything for it to do.
