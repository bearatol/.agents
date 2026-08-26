#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import pathlib
import stat
import sys
import tempfile
from datetime import datetime, timezone


def digest_path(path):
    path = pathlib.Path(path)
    if not path.exists() and not path.is_symlink():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    entries = [path]
    if path.is_dir() and not path.is_symlink():
        entries.extend(sorted(path.rglob("*"), key=lambda item: item.relative_to(path).as_posix()))
    for entry in entries:
        relative = "." if entry == path else entry.relative_to(path).as_posix()
        mode = stat.S_IMODE(entry.lstat().st_mode)
        digest.update(f"{relative}\0{mode:o}\0".encode())
        if entry.is_symlink():
            digest.update(b"link\0" + os.readlink(entry).encode())
        elif entry.is_file():
            digest.update(b"file\0")
            with entry.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        elif entry.is_dir():
            digest.update(b"dir\0")
    return digest.hexdigest()


def load_state(path):
    if not path.exists():
        return {"schema_version": 1, "components": {}}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".ecosystem-state.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    hash_parser = sub.add_parser("hash")
    hash_parser.add_argument("path")
    matches_parser = sub.add_parser("matches")
    matches_parser.add_argument("--state", required=True)
    matches_parser.add_argument("--id", required=True)
    matches_parser.add_argument("--path", required=True)
    set_parser = sub.add_parser("set")
    set_parser.add_argument("--state", required=True)
    set_parser.add_argument("--id", required=True)
    set_parser.add_argument("--source", required=True)
    set_parser.add_argument("--installed", required=True)
    args = parser.parse_args()

    try:
        if args.command == "hash":
            print(digest_path(args.path))
            return
        state_path = pathlib.Path(args.state)
        state = load_state(state_path)
        if args.command == "matches":
            expected = state.get("components", {}).get(args.id, {}).get("installed_hash")
            if not expected or expected != digest_path(args.path):
                raise SystemExit(1)
            return
        state.setdefault("components", {})[args.id] = {
            "source_hash": digest_path(args.source),
            "installed_hash": digest_path(args.installed),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        save_state(state_path, state)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
