#!/usr/bin/env python3

import argparse
import pathlib
import re
import subprocess
import sys


CYRILLIC = re.compile(r"[\u0400-\u04ff]")
PERSONAL_PATH = re.compile(r"/(?:Users|home)/[^/\s]+")
USER_FACING_NON_ENGLISH = {pathlib.Path("docs/HOW_IT_WORKS.md")}

# PowerShell refuses to assign these, and the failure only appears on Windows.
# Checking here means a Linux run catches it before the Windows job does.
POWERSHELL_RESERVED = {
    "host", "pid", "pshome", "shellid", "executioncontext", "home",
    "psversiontable", "psculture", "psuiculture", "true", "false", "null",
    "myinvocation", "psscriptroot", "pscommandpath", "psedition",
    "iswindows", "islinux", "ismacos",
}
POWERSHELL_ASSIGNMENT = re.compile(r"\$(\w+)\s*=(?!=)")
POWERSHELL_LOOP = re.compile(r"\bforeach\s*\(\s*\$(\w+)\s+in\b", re.IGNORECASE)
POWERSHELL_SUFFIXES = {".ps1", ".psm1"}


def powershell_reserved_writes(text):
    """Report line numbers that assign a read-only PowerShell variable."""
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        code = line.split("#", 1)[0]
        for pattern in (POWERSHELL_ASSIGNMENT, POWERSHELL_LOOP):
            for match in pattern.finditer(code):
                if match.group(1).lower() in POWERSHELL_RESERVED:
                    found.append((number, match.group(1)))
    return found


def repository_files(root):
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
        capture_output=True,
    )
    if result.returncode != 0:
        return root.rglob("*")
    return (root / pathlib.Path(path.decode()) for path in result.stdout.split(b"\0") if path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()
    errors = []
    for path in repository_files(root):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in (".git", "__pycache__") for part in relative.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if (path.name != "doctor.sh" and not path.name.startswith("README") and
                relative not in USER_FACING_NON_ENGLISH and CYRILLIC.search(text)):
            errors.append(f"Cyrillic text in machine-facing file: {relative}")
        if path.name != "check_repository.py" and PERSONAL_PATH.search(text):
            errors.append(f"machine-specific home path in: {relative}")
        if path.suffix in POWERSHELL_SUFFIXES:
            for number, name in powershell_reserved_writes(text):
                errors.append(
                    f"{relative}:{number} assigns ${name}, "
                    "which PowerShell keeps read-only"
                )
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
