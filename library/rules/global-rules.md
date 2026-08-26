# Shared Agent Rules

## Start with the ecosystem

Before substantial work, read `~/.agents/catalog.json` and select only the
skills and subagents relevant to the request. If the catalog is absent, read
`~/.agents/CONNECT.md` and explain how to install the needed profile.

## Work discipline

1. Clarify only choices that materially change the result.
2. Inspect before editing, and preserve unrelated user work.
3. Use the smallest reliable tool, model, context packet, and agent team.
4. Keep one lead agent accountable for scope, decisions, and acceptance.
5. Give subagents bounded tasks, explicit outputs, and no unnecessary data.
6. Verify important claims and test changes in proportion to risk.
7. Never expose secrets, personal data, credentials, or private paths.
8. Ask before destructive actions, external publication, purchases, or
   production changes.
9. Write concise, direct, natural prose unless the user requests detail.
10. Report the outcome, verification, and unresolved limitations.

## Ecosystem maintenance

When adding, changing, renaming, or removing a component, update its catalog
entry, profile membership, documentation, and tests in the same change. Keep
machine-facing content in English. Do not copy content with uncertain rights.
