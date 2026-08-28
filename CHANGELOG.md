# Changelog

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
