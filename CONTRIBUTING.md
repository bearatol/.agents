# Contributing

Contributions must be original or clearly licensed for redistribution.

For a new component:

1. Create an English component under `library/`.
2. Add a catalog v2 entry to `catalog/catalog.json`.
3. For an agent, declare capabilities, access, skill policy, advisory skills,
   and whether it may delegate.
4. Add the component to one or more files in `profiles/`.
5. Document required tools, permissions, and network access explicitly.
6. Update orchestration schemas and examples when packet contracts change.
7. Add or update isolated tests.
8. Run `./tests/test.sh`, `./scripts/doctor.sh`, and `git diff --check`.

Agents must select their own relevant skills and report the decision. CEO skill
recommendations are advisory. A skill must never expand scope or permissions.

Do not submit copied prompt packs, cosmetically rewritten proprietary work,
model weights, credentials, generated caches, or undisclosed telemetry.
