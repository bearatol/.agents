# Security Policy

## Supported versions

Security fixes are applied to the latest commit on the default branch.

## Reporting

Do not open a public issue for a suspected credential leak or exploitable
installer vulnerability. Contact the repository owner privately through the
security reporting method configured on GitHub.

## Installer guarantees

- Installation is local and defaults to `~/.agents`.
- Existing files are not replaced unless `--force` is supplied.
- Host adapters create symbolic links only for selected installed skills.
- No script downloads model weights or starts a model automatically.
- Package installation occurs only when a user explicitly runs a model setup
  script.

Before publishing, run:

```bash
./tests/test.sh
./scripts/doctor.sh
git diff --check
```

Also inspect the staged file list and search for secrets, private paths, model
artifacts, and unexpected executable files.
