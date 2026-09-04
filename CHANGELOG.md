# Changelog

## Unreleased

- Fixed the Windows setup and its test: both looped over `$Host`, which
  PowerShell keeps read-only, so a comma-separated application list failed on
  Windows only.
- Added a repository check for assignment to read-only PowerShell variables, so
  a POSIX run catches that class of defect before the Windows job does.
- Added `agents.sh remove`, `disable`, and `enable`. Removal deletes only a
  component this project owns in the registry and refuses anything claimed by
  another tool, claimed twice, or linking outside the runtime. Deactivation
  moves a component into a recorded holding area and takes its published host
  links down, so a component installed by another tool can be switched off
  without being destroyed, and put back later.
- Taught the registry about deactivated components, so a switched-off component
  reports as disabled instead of missing and an installation would not
  recreate it.
- Recorded the next architectural decision in
  `docs/adr/0002-shared-directory-sources-and-attested-packages.md`: `~/.agents`
  is a shared runtime this tool is a tenant of, content moves to its own
  package repository, sources become records with pinned and linked modes,
  removal and deactivation act only on owned paths, and packages carry scan
  evidence bound to a content hash. Scanning runs from the command line on the
  user's machine, not only in a publisher's pipeline, and a finding in someone
  else's component is answered by deriving an owned copy rather than by editing
  theirs.
- Recorded the ownership model in
  `docs/adr/0001-ownership-layers-and-activation-registry.md`: source, managed
  runtime, and personal workspace, with one owner per activated path.
- Added `agents.sh registry report|plan|reconcile`, a read-only view of who
  owns each activated path, how far it was reviewed, and what an installation
  would change. These commands never write.
- Reported names claimed by both the catalog and a third-party lock file, and
  activated paths that link outside the managed runtime.
- Pointed a failing `doctor` at `registry reconcile` instead of leaving a bare
  drift error.
- Added regression coverage for attribution, planning, untrusted third-party
  records, and the guarantee that no registry command writes.
- Renamed this project's own `skill:find-skills` to `skill:capability-discovery`
  and recorded the replacement, so the `find-skills` name belongs to the
  third-party CLI wrapper alone and the collision cannot come back.
- Made both installers read `catalog/migrations.json` when merging the
  installed manifest, so a renamed component stops being reported as drift.
- Stopped the test suites from leaving bytecode caches in the source tree,
  which installers copied verbatim into the managed runtime.
- Corrected the installer usage text: `--force` is accepted for compatibility
  and never overwrites a conflicting path.
- Ignored the generated runtime `catalog.schema.json` alongside the other
  managed copies, so a development checkout cannot commit it as source.

## 0.5.0 - 2026-08-29

- Reworked setup around plain-language work choices, including several choices
  at once or everything, while adding shared checks automatically.
- Added human-friendly noninteractive setup commands for Bash and PowerShell.
- Preflight host conflicts before persistent installation for Bash setup and
  direct installation, so a known conflict leaves the selected environment
  untouched.
- Added Bash and PowerShell regression coverage for multi-choice setup and
  expanded malicious-input and host-conflict checks.

## 0.4.0 - 2026-08-28

- Added one five-command workflow for setup, status, export, restore, and doctor.
- Added strict portable environment locks for profiles, explicit components,
  hosts, ecosystem version, and exact Git commit.
- Added drift-aware health checks and fail-closed host preflight on Bash and
  PowerShell.
- Made export fail closed on source or installed drift while allowing only the
  validated lock itself as untracked input during restore.
- Persisted host and explicit-component selections so updates can replay them.
- Added clean-machine restore, malicious-manifest, conflict, traversal,
  detached-HEAD, Windows-state, and idempotency coverage.
- Reworked onboarding around first use, daily health, and moving to a new
  computer.

## 0.3.1 - 2026-08-27

- Fixed Windows CI exit propagation after expected negative security tests.

## 0.3.0 - 2026-08-27

- Added native Windows PowerShell install, connect, update, doctor, and CI.
- Added Koda and Yandex SourceCraft host support.
- Merged design-master into design-reviewer and team-lead into CEO.
- Added sales, SEO, legal-content, and post-change security specialists.
- Expanded context engineering with metadata-first progressive disclosure.
- Added an original scalable SVG repository banner.

All notable changes to this project are documented here.

## 0.2.0 - 2026-08-26

- Add catalog v2 with agent capabilities, access levels, and skill policies.
- Add CEO task orchestration contracts and a local `team` CLI.
- Let every specialist autonomously select and report relevant skills while
  keeping CEO recommendations advisory; independent security review remains
  isolated from optional skills.
- Add engineer, QA reviewer, and product editor agents.
- Add software, quality, content, and orchestration components and profiles.
- Generate host-native subagent wrappers for Codex, Claude Code, and Gemini CLI.
- Add managed-content hashes so unchanged ecosystem files update safely while
  user-modified files remain protected.
- Add a migration option that preserves personal global agent rules.
- Add architecture, orchestration, host support, examples, and CI checks.

## 0.1.0 - 2026-08-25

- Publish the original portable skills, agents, profiles, installer, adapters,
  local-model helpers, and Russian, English, and Simplified Chinese guides.
