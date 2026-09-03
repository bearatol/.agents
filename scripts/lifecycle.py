#!/usr/bin/env python3
"""Removal and deactivation of activated components, driven by ownership.

These are the only write operations outside the installer. Both act on the
managed runtime and refuse anything the activation registry does not attribute
to this project, so a component installed by another tool is never destroyed by
accident. See docs/adr/0002-shared-directory-sources-and-attested-packages.md.
"""

import argparse
import json
import os
import pathlib
import shutil
import sys
import tempfile

# Importing sibling modules must not leave bytecode caches in the source
# tree; installers copy component directories verbatim.
sys.dont_write_bytecode = True

from environment import (
    EnvironmentError as EcosystemError,
    HOSTS,
    host_target,
    read_lines,
)
from registry import (
    DISABLED_DIRECTORY,
    DISABLED_RECORD,
    build_entries,
    load_disabled,
)
from state import load_state, save_state

MANIFEST = ".ecosystem-installed"
STATE_FILE = ".ecosystem-state.json"


def fail(message):
    raise EcosystemError(message)


def contained(path, root):
    """Refuse any path whose location leaves the managed runtime.

    The containing directory is resolved, not the path itself, so a symbolic
    link that sits inside the runtime and points outside it can still be moved
    or unlinked. What matters is where the entry lives, not where it leads.
    """
    path = pathlib.Path(path)
    try:
        parent = path.parent.resolve(strict=False)
        parent.relative_to(pathlib.Path(root).resolve(strict=False))
    except (OSError, ValueError):
        fail(f"path leaves the managed runtime: {path}")
    return parent / path.name


def write_json_replace(path, data):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_disabled(home, record):
    write_json_replace(pathlib.Path(home) / DISABLED_RECORD, record)


def find_entry(entries, target):
    """Resolve a user-supplied identifier or bare name to one entry."""
    matches = [entry for entry in entries if entry["id"] == target]
    if not matches:
        matches = [entry for entry in entries if entry["name"] == target]
    if not matches:
        fail(f"no activated component matches: {target}")
    if len(matches) > 1:
        names = ", ".join(sorted(entry["id"] for entry in matches))
        fail(f"several components match {target}; name one of: {names}")
    return matches[0]


def host_links(home, user_home, kind, name):
    """Managed links that publish this component to a connected host."""
    links = []
    for host in read_lines(pathlib.Path(home) / ".ecosystem-hosts"):
        if host not in HOSTS:
            continue
        state_id = f"host:{host}:{kind}:{name}"
        target = host_target(pathlib.Path(user_home), host, state_id)
        if target is None:
            continue
        if target.is_symlink() or target.exists():
            links.append((state_id, target))
    return links


def drop_state_entries(home, state_ids):
    path = pathlib.Path(home) / STATE_FILE
    if not path.is_file():
        return
    state = load_state(path)
    components = state.get("components", {})
    changed = False
    for state_id in state_ids:
        if components.pop(state_id, None) is not None:
            changed = True
    if changed:
        save_state(path, state)


def drop_manifest_entry(home, component_id):
    path = pathlib.Path(home) / MANIFEST
    if not path.is_file():
        return
    kept = [line for line in read_lines(path) if line != component_id]
    contained(path, home)
    write_lines(path, kept)


def write_lines(path, values):
    path = pathlib.Path(path)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for value in values:
                handle.write(f"{value}\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def delete_path(path):
    path = pathlib.Path(path)
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def unlink_hosts(links, *, dry_run):
    for _, target in links:
        if dry_run:
            print(f"would-unlink   {target}")
            continue
        if target.is_symlink() or target.exists():
            delete_path(target)
            print(f"unlinked       {target}")


def cmd_disable(args, entries, home, user_home):
    entry = find_entry(entries, args.target)
    if entry["state"] == "disabled":
        fail(f"{entry['id']} is already disabled")
    if entry["state"] == "missing":
        fail(f"{entry['id']} is not present in the runtime")

    source = contained(pathlib.Path(home) / entry["path"], home)
    destination = contained(pathlib.Path(home) / DISABLED_DIRECTORY / entry["path"], home)
    if destination.exists() or destination.is_symlink():
        fail(f"a disabled copy already exists at {destination}")

    links = host_links(home, user_home, entry["kind"], entry["name"])
    if args.dry_run:
        print(f"would-disable  {entry['id']} ({entry['path']})")
        unlink_hosts(links, dry_run=True)
        return 0

    unlink_hosts(links, dry_run=False)
    drop_state_entries(home, [state_id for state_id, _ in links])
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)

    record = load_disabled(home)
    record.setdefault("entries", {})[entry["id"]] = {
        "kind": entry["kind"],
        "name": entry["name"],
        "path": entry["path"],
        "owner": entry["owner"],
    }
    save_disabled(home, record)
    print(f"disabled       {entry['id']}")
    if entry["owner"] == "foreign":
        print(f"note: {entry['provenance']['record']} still records this component and may reinstall it")
    return 0


def cmd_enable(args, entries, home, user_home):
    record = load_disabled(home)
    stored = record.get("entries", {})
    component_id = args.target
    if component_id not in stored:
        matches = [key for key, value in stored.items() if value.get("name") == args.target]
        if len(matches) > 1:
            fail(f"several disabled components match {args.target}; name one of: {', '.join(sorted(matches))}")
        if not matches:
            fail(f"no disabled component matches: {args.target}")
        component_id = matches[0]
    item = stored[component_id]

    source = contained(pathlib.Path(home) / DISABLED_DIRECTORY / item["path"], home)
    destination = contained(pathlib.Path(home) / item["path"], home)
    if not source.exists() and not source.is_symlink():
        fail(f"the disabled copy is gone: {source}")
    if destination.exists() or destination.is_symlink():
        fail(f"something already occupies {destination}; resolve that path first")
    if args.dry_run:
        print(f"would-enable   {component_id} ({item['path']})")
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)
    del stored[component_id]
    save_disabled(home, record)
    print(f"enabled        {component_id}")
    print("run connect to publish it to the hosts again")
    return 0


def cmd_remove(args, entries, home, user_home):
    entry = find_entry(entries, args.target)
    if entry["owner"] != "catalog":
        fail(
            f"{entry['id']} is owned by {entry['owner']}, so this tool does not delete it; "
            "disable it instead, or remove it with the tool that installed it"
        )
    if entry["collisions"]:
        owners = ", ".join(item["owner"] for item in entry["collisions"])
        fail(f"{entry['id']} is also claimed by {owners}; resolve that claim before removing it")
    if entry["escapes_home"]:
        fail(f"{entry['id']} links outside the managed runtime; remove it where it actually lives")
    if entry["state"] in {"missing", "disabled"}:
        fail(f"{entry['id']} is not currently installed")

    path = contained(pathlib.Path(home) / entry["path"], home)
    links = host_links(home, user_home, entry["kind"], entry["name"])
    if args.dry_run:
        print(f"would-remove   {entry['id']} ({entry['path']})")
        unlink_hosts(links, dry_run=True)
        return 0

    unlink_hosts(links, dry_run=False)
    delete_path(path)
    drop_state_entries(home, [entry["id"]] + [state_id for state_id, _ in links])
    drop_manifest_entry(home, entry["id"])
    print(f"removed        {entry['id']}")
    print("the catalog still declares it, so a later install will put it back")
    return 0


def parser():
    top = argparse.ArgumentParser(description=__doc__)
    top.add_argument("--repo", required=True)
    top.add_argument("--home", required=True)
    top.add_argument("--user-home", required=True)
    sub = top.add_subparsers(dest="command", required=True)
    for name, handler in (("remove", cmd_remove), ("disable", cmd_disable), ("enable", cmd_enable)):
        command = sub.add_parser(name)
        command.add_argument("target")
        command.add_argument("--dry-run", action="store_true")
        command.set_defaults(handler=handler)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        entries, _ = build_entries(args.repo, args.home, args.user_home)
        return args.handler(args, entries, pathlib.Path(args.home), pathlib.Path(args.user_home))
    except (EcosystemError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
