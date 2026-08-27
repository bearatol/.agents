# Security Policy

## Supported versions

Security fixes are applied to the latest commit on the default branch.

## Reporting

Do not open a public issue for a suspected credential leak or exploitable
installer vulnerability. Contact the repository owner privately through the
security reporting method configured on GitHub.

## Installer guarantees

- Installation is local and defaults to `~/.agents`.
- Existing files are replaced automatically only when their recorded managed
  hash proves they have not been changed by the user. `--force` is retained for
  command compatibility but never overrides a user-modified or unmanaged path.
- Native Windows operations reject junctions, symbolic links, and other reparse
  points anywhere along a managed destination path.
- Bash host adapters create symbolic links only for installed skills. Native
  Windows adapters use managed copies. Both preserve conflicting host agent
  definitions.
- Generated subagent wrappers inherit the catalog access boundary. Skill
  selection cannot grant broader tools, paths, networking, or permissions.
- Subagents cannot create nested subagents; additional expertise returns to the
  accountable CEO.
- No script downloads model weights or starts a model automatically.
- Package installation occurs only when a user explicitly runs a model setup
  script.
- Update scripts fetch first, require the user to approve the exact 40-character
  upstream commit, and only then fast-forward and reinstall managed components.

Before publishing, run:

```bash
./tests/test.sh
./scripts/doctor.sh
git diff --check
```

Also inspect the staged file list and search for secrets, private paths, model
artifacts, and unexpected executable files.

Repository CI runs isolated test suites on Linux, macOS, and Windows with
read-only repository permissions.
