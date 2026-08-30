# Repository Rules for AI Agents

## Purpose

Maintain a portable ecosystem of original skills, subagent prompts, shared
rules, adapters, and optional local-model helpers.

## Required workflow

1. Read `CONNECT.md`, `catalog/catalog.json`, and relevant profiles first.
2. Select the smallest components that satisfy the task.
3. When acting as CEO, recommend agents and skills through task packets.
4. When acting as a subagent, independently select all relevant installed
   skills, apply them completely, and report skills considered and applied.
5. Skills never expand task scope, tools, paths, networks, or permissions.
6. Subagents do not delegate; requests for another specialist return to CEO.
7. Preserve existing user files and unrelated changes.
8. Use English for every machine-facing rule, skill, prompt, manifest, and
   script message. User-facing articles may use another language.
9. Update catalog and profile metadata whenever components change.
10. Run `tests/test.sh` and `scripts/doctor.sh` before completion.
11. Review the final diff for secrets, personal paths, model weights, license
   violations, unsafe shell expansion, and unexpected network access.

## User-facing writing

Before writing or editing text meant for people, including README files,
documentation, guides, articles, release notes, website copy, and interface
text, apply the
`natural-writing` and `copy-editing` skills. For Russian text, also apply
`humanizer-ru` or the closest available equivalent. Use this pass to remove
template-like AI phrasing, bureaucracy, vague promises, and needless jargon.

Keep the writer's intended voice and all verified facts. Do not manufacture
personal anecdotes, certainty, or casualness just to make prose sound human.
Avoid em dashes in user-facing prose. Prefer a full stop, comma, colon, or a
shorter sentence instead.
Machine-facing files, schemas, manifests, commands, and error messages are
excluded unless they contain text shown directly to a person.

## Publication boundary

Only original repository content may be committed. A third-party component
may be referenced in the catalog, but it must not be vendored unless its
license explicitly permits redistribution and all required notices are kept.
Never remove or rewrite a third-party license to make publication appear
permitted.

## Generated and private data

Do not commit credentials, `.env` files, private keys, logs, caches, virtual
environments, model weights, user backups, or machine-specific absolute paths.
