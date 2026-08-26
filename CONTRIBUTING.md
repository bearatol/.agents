# Contributing

Contributions must be original or clearly licensed for redistribution.

For a new component:

1. Create an English `SKILL.md` or agent prompt under `library/`.
2. Add an entry to `catalog/catalog.json`.
3. Add it to one or more files in `profiles/`.
4. Document required tools and network access explicitly.
5. Add or update tests.
6. Run `./tests/test.sh` and `./scripts/doctor.sh`.

Do not submit copied prompt packs, cosmetically rewritten proprietary work,
model weights, credentials, generated caches, or undisclosed telemetry.
