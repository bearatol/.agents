# Personal workspace

This directory is the portable, Git-friendly data layer owned by the user.

- `library/<type>/<name>/` stores reusable material. A new data type needs only
  a new folder name; the storage layer does not need a code change.
- `.index/` records checksums and explicit trust decisions.
- `projects/` stores immutable tasks, results, peer reviews, and coordinator
  decisions for work shared by several AI hosts.

Use `scripts/agents.sh library ...` or `scripts/agents.ps1 library ...` instead
of editing `.index` and project records manually. Imported content is inactive
until it has been reviewed and explicitly trusted. Trust is provenance, not
permission to execute code. Never store credentials, private keys, account
sessions, or model weights here. Secret detection is a safety net, not a
guarantee; review every Git diff before publishing or pushing it.
