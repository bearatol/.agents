#!/usr/bin/env python3

import argparse
import pathlib
import re
import subprocess
import sys


CYRILLIC = re.compile(r"[\u0400-\u04ff]")
PERSONAL_PATH = re.compile(r"/(?:Users|home)/[^/\s]+")


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
        if path.name != "doctor.sh" and not path.name.startswith("README") and CYRILLIC.search(text):
            errors.append(f"Cyrillic text in machine-facing file: {relative}")
        if path.name != "check_repository.py" and PERSONAL_PATH.search(text):
            errors.append(f"machine-specific home path in: {relative}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
