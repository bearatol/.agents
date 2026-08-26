# Repository Rules for AI Agents

## Purpose

Maintain a portable ecosystem of original skills, subagent prompts, shared
rules, adapters, and optional local-model helpers.

## Required workflow

1. Read `CONNECT.md`, `catalog/catalog.json`, and relevant profiles first.
2. Select the smallest components that satisfy the task.
3. Preserve existing user files and unrelated changes.
4. Use English for every machine-facing rule, skill, prompt, manifest, and
   script message. User-facing articles may use another language.
5. Update catalog and profile metadata whenever components change.
6. Run `tests/test.sh` and `scripts/doctor.sh` before completion.
7. Review the final diff for secrets, personal paths, model weights, license
   violations, unsafe shell expansion, and unexpected network access.

## Publication boundary

Only original repository content may be committed. A third-party component
may be referenced in the catalog, but it must not be vendored unless its
license explicitly permits redistribution and all required notices are kept.
Never remove or rewrite a third-party license to make publication appear
permitted.

## Generated and private data

Do not commit credentials, `.env` files, private keys, logs, caches, virtual
environments, model weights, user backups, or machine-specific absolute paths.
