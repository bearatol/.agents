#!/usr/bin/env python3
"""Read-only activation registry and planner for the agent ecosystem.

Every command here is a read operation. It answers who owns each activated
path, how far that path was reviewed, and what a future apply step would
change. It never creates, moves, overwrites, or deletes anything, so it is
safe to run against a live installation and inside CI. The design is recorded
in docs/adr/0001-ownership-layers-and-activation-registry.md.
"""

import argparse
import json
import os
import pathlib
import sys

from environment import (
    EnvironmentError as EcosystemError,
    HOSTS,
    catalog_data,
    classify,
    component_paths,
    environment_state,
    host_target,
    read_json_file,
    read_lines,
)
from state import digest_path

FOREIGN_RECORDS = (".skill-lock.json",)
NATIVE_DISCOVERY_HOSTS = {"generic", "kimi", "koda"}
LINKING_HOSTS = {"codex", "claude", "gemini", "sourcecraft"}
DIRECTORY_KINDS = {"skill": "skills", "tool": "tools", "model": "local-models"}
FILE_KINDS = {"agent": "agents", "rule": "rules"}
RUNTIME_KINDS = {**DIRECTORY_KINDS, **FILE_KINDS}
GENERATED_NAMES = {"INDEX.md", "README.md"}
ROOT_SOURCES = {
    "AGENTS.md": ("AGENTS.md",),
    "CONNECT.md": ("CONNECT.md",),
    "catalog.json": ("catalog", "catalog.json"),
    "catalog.schema.json": ("catalog", "catalog.schema.json"),
    "migrations.json": ("catalog", "migrations.json"),
}
MAX_FOREIGN_ENTRIES = 4096

OWNER_ORDER = {"catalog": 0, "workspace": 1, "foreign": 2, "unknown": 3}
STATE_ORDER = {"missing": 0, "locally-modified": 1, "managed-stale": 2, "present": 3, "current": 4}
ALL_KINDS = sorted(set(RUNTIME_KINDS) | {"orchestration", "root"})


def relative_to_home(path, home):
    try:
        return pathlib.Path(path).relative_to(home).as_posix()
    except ValueError:
        return str(path)


def content_hash(path):
    try:
        return digest_path(path)
    except (OSError, FileNotFoundError):
        return None


def escapes_home(path, home):
    """Report whether a path leads outside the managed runtime."""
    if not path.is_symlink():
        return False
    try:
        path.resolve(strict=False).relative_to(pathlib.Path(home).resolve(strict=False))
    except (OSError, ValueError):
        return True
    return False


def link_target(path):
    if not path.is_symlink():
        return None
    try:
        return os.readlink(path)
    except OSError:
        return None


def catalog_claims(repo, home):
    """Map each runtime path to the canonical component that declares it."""
    repo = pathlib.Path(repo)
    home = pathlib.Path(home)
    claims = {}
    for component_id, (source, installed) in component_paths(repo, home).items():
        claims[installed] = {
            "id": component_id,
            "kind": component_id.split(":", 1)[0],
            "source": source,
            "record": "catalog/catalog.json",
            "reference": component_id,
        }
    for name, parts in ROOT_SOURCES.items():
        claims[home / name] = {
            "id": f"root:{name}",
            "kind": "root",
            "source": repo.joinpath(*parts),
            "record": "catalog/catalog.json",
            "reference": f"root:{name}",
        }
    return claims


def workspace_claims(repo, home):
    """Map each runtime path to an activated personal workspace item."""
    claims = {}
    index = pathlib.Path(repo) / "workspace" / ".index"
    if not index.is_dir():
        return claims
    for path in sorted(index.glob("*/*.json")):
        try:
            data = read_json_file(path, limited=True, no_follow=True)
        except (EcosystemError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        kind = data.get("type", path.parent.name)
        name = data.get("name", path.stem)
        directory = RUNTIME_KINDS.get(kind)
        if not directory or not isinstance(name, str) or "/" in name:
            continue
        target = name if kind in DIRECTORY_KINDS else f"{name}.md"
        claims[pathlib.Path(home) / directory / target] = {
            "record": "workspace/.index",
            "reference": f"{kind}/{name}",
            "trusted": bool(data.get("trusted")),
        }
    return claims


def foreign_claims(home):
    """Map each runtime path to a third-party record found inside AGENTS_HOME.

    The record is untrusted input. A missing, unreadable, or unexpected file
    yields no claims and never stops the command.
    """
    claims = {}
    warnings = []
    for filename in FOREIGN_RECORDS:
        path = pathlib.Path(home) / filename
        if not path.is_file():
            continue
        try:
            data = read_json_file(path, limited=True, no_follow=True)
        except (EcosystemError, OSError) as exc:
            warnings.append(f"cannot read {filename}: {exc}")
            continue
        skills = data.get("skills") if isinstance(data, dict) else None
        if not isinstance(skills, dict):
            warnings.append(f"{filename} holds no readable skill records")
            continue
        if len(skills) > MAX_FOREIGN_ENTRIES:
            warnings.append(f"{filename} declares too many entries to attribute")
            continue
        for name, entry in skills.items():
            if not isinstance(name, str) or "/" in name or os.sep in name or name in {".", ".."}:
                continue
            reference = None
            if isinstance(entry, dict) and isinstance(entry.get("source"), str):
                reference = entry["source"][:256]
            claims[pathlib.Path(home) / "skills" / name] = {
                "record": filename,
                "reference": reference,
            }
    return claims, warnings


def activated_paths(home, kinds):
    """List every path currently activated in the managed runtime."""
    home = pathlib.Path(home)
    paths = []
    skipped = 0
    for kind, directory in RUNTIME_KINDS.items():
        if kinds and kind not in kinds:
            continue
        root = home / directory
        if not root.is_dir():
            continue
        for entry in sorted(root.iterdir()):
            if entry.name.startswith("."):
                continue
            if entry.name in GENERATED_NAMES:
                skipped += 1
                continue
            if kind in DIRECTORY_KINDS and entry.is_file() and not entry.is_symlink():
                skipped += 1
                continue
            paths.append((kind, entry))
    if (not kinds or "orchestration" in kinds) and (home / "orchestration").is_dir():
        paths.append(("orchestration", home / "orchestration"))
    if not kinds or "root" in kinds:
        for name in sorted(ROOT_SOURCES):
            candidate = home / name
            if candidate.exists() or candidate.is_symlink():
                paths.append(("root", candidate))
    return paths, skipped


def component_name(kind, path):
    if kind in FILE_KINDS and path.suffix == ".md":
        return path.stem
    return path.name


def host_targets(user_home, connected, kind, name):
    targets = []
    for host in connected:
        if host not in HOSTS:
            continue
        if host in NATIVE_DISCOVERY_HOSTS:
            if kind == "skill":
                targets.append(f"{host}:native")
            continue
        if host not in LINKING_HOSTS:
            continue
        target = host_target(pathlib.Path(user_home), host, f"host:{host}:{kind}:{name}")
        if target is not None and (target.exists() or target.is_symlink()):
            targets.append(host)
    return targets


def describe(path, kind, context):
    name = component_name(kind, path)
    claims = []
    for owner, source in (("catalog", context["catalog"]), ("workspace", context["workspace"]), ("foreign", context["foreign"])):
        if path in source:
            claims.append((owner, source[path]))

    owner = claims[0][0] if claims else "unknown"
    primary = claims[0][1] if claims else {}
    exists = path.exists() or path.is_symlink()

    if owner == "catalog":
        component_id = primary["id"]
        kind = primary["kind"]
        state = classify(primary["source"], path, context["state"].get(component_id))
        if state == "current":
            trust = "managed"
        elif context["state"].get(component_id):
            trust = "declared"
        else:
            trust = "unreviewed"
    else:
        component_id = f"{kind}:{name}"
        state = "present" if exists else "missing"
        if owner == "workspace":
            trust = "trusted" if primary.get("trusted") else "unreviewed"
        elif owner == "foreign":
            trust = "declared"
        else:
            trust = "unreviewed"

    outside = escapes_home(path, context["home"]) if exists else False
    return {
        "id": component_id,
        "kind": kind,
        "name": name,
        "path": relative_to_home(path, context["home"]),
        "owner": owner,
        "provenance": {"record": primary.get("record"), "reference": primary.get("reference")},
        "hash": None if outside or not exists else content_hash(path),
        "trust": trust,
        "targets": host_targets(context["user_home"], context["connected"], kind, name) if exists else [],
        "state": state,
        "escapes_home": outside,
        "link": link_target(path) if outside else None,
        "collisions": [
            {"owner": other, "record": data.get("record"), "reference": data.get("reference")}
            for other, data in claims[1:]
        ],
    }


def build_entries(repo, home, user_home, *, kinds=None):
    repo = pathlib.Path(repo)
    home = pathlib.Path(home)
    kinds = set(kinds or [])
    foreign, warnings = foreign_claims(home)
    context = {
        "catalog": catalog_claims(repo, home),
        "workspace": workspace_claims(repo, home),
        "foreign": foreign,
        "state": environment_state(home),
        "connected": read_lines(home / ".ecosystem-hosts"),
        "home": home,
        "user_home": user_home,
    }

    paths, skipped = activated_paths(home, kinds)
    entries = []
    seen = set()
    for kind, path in paths:
        seen.add(path)
        entries.append(describe(path, kind, context))
    for path, claim in sorted(context["catalog"].items(), key=lambda item: str(item[0])):
        if path in seen:
            continue
        if kinds and claim["kind"] not in kinds:
            continue
        entries.append(describe(path, claim["kind"], context))

    if skipped:
        warnings.append(f"{skipped} generated index or plain file(s) in runtime directories were not attributed")
    entries.sort(key=lambda item: (OWNER_ORDER.get(item["owner"], 9), STATE_ORDER.get(item["state"], 9), item["id"]))
    return entries, warnings


def plan_action(entry):
    """Decide what an apply step would do, without doing any of it."""
    if entry["owner"] != "catalog":
        return "keep", f"owned by {entry['owner']}; the installer does not write this path"
    if entry["state"] == "current":
        if entry["collisions"]:
            return "skip", "matches its canonical source, but another record also claims this path"
        return "skip", "already matches its canonical source"
    if entry["collisions"]:
        return "conflict", "diverged and claimed by more than one record; choose which content stays"
    if entry["state"] == "missing":
        return "create", "declared by the catalog and not present"
    if entry["state"] == "managed-stale":
        return "update", "installed by this project and behind its canonical source"
    return "conflict", "differs from both the canonical source and the copy this project installed"


def render_table(rows, columns):
    widths = [max(len(str(row[index])) for row in [columns] + rows) for index in range(len(columns))]
    return [
        "  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)).rstrip()
        for row in [columns] + rows
    ]


def print_warnings(warnings):
    for warning in warnings:
        print(f"warning: {warning}")


def cmd_report(args, entries, warnings):
    if args.json:
        print(json.dumps({"schema_version": 1, "writes": False, "entries": entries, "warnings": warnings}, indent=2, ensure_ascii=False))
        return 0
    if not entries:
        print("No activated components found.")
        print_warnings(warnings)
        return 0
    rows = [
        [
            entry["owner"],
            entry["trust"],
            entry["state"],
            entry["id"],
            entry["provenance"]["reference"] or ("external link" if entry["escapes_home"] else "-"),
        ]
        for entry in entries
    ]
    for line in render_table(rows, ["OWNER", "TRUST", "STATE", "ID", "SOURCE"]):
        print(line)
    counts = {}
    for entry in entries:
        counts[entry["owner"]] = counts.get(entry["owner"], 0) + 1
    external = sum(1 for entry in entries if entry["escapes_home"])
    print()
    print("Totals: " + ", ".join(f"{owner} {count}" for owner, count in sorted(counts.items())))
    if external:
        print(f"{external} path(s) link outside the managed runtime and were not hashed.")
    print_warnings(warnings)
    return 0


def cmd_plan(args, entries, warnings):
    planned = [(entry, *plan_action(entry)) for entry in entries]
    if args.json:
        print(json.dumps({
            "schema_version": 1,
            "writes": False,
            "actions": [
                {"id": entry["id"], "path": entry["path"], "owner": entry["owner"], "action": action, "reason": reason}
                for entry, action, reason in planned
            ],
            "warnings": warnings,
        }, indent=2, ensure_ascii=False))
        return 0
    rows = [[action, entry["owner"], entry["id"], reason] for entry, action, reason in planned if action not in {"keep", "skip"}]
    kept = sum(1 for _, action, _ in planned if action == "keep")
    if rows:
        for line in render_table(rows, ["ACTION", "OWNER", "ID", "REASON"]):
            print(line)
        print()
    else:
        print("Nothing to change.")
    print(f"{kept} path(s) stay untouched because this project does not own them.")
    print("This command wrote nothing. Resolve every conflict before applying.")
    print_warnings(warnings)
    return 0


def cmd_reconcile(args, entries, warnings):
    divergent = []
    overlaps = []
    for entry in entries:
        action, reason = plan_action(entry)
        if action in {"conflict", "update", "create"}:
            divergent.append((entry, action, reason))
        elif entry["collisions"]:
            overlaps.append(entry)
    external = [entry for entry in entries if entry["escapes_home"]]

    if args.json:
        print(json.dumps({
            "schema_version": 1,
            "writes": False,
            "divergences": [
                {
                    "id": entry["id"],
                    "path": entry["path"],
                    "owner": entry["owner"],
                    "state": entry["state"],
                    "trust": entry["trust"],
                    "action": action,
                    "reason": reason,
                    "collisions": entry["collisions"],
                }
                for entry, action, reason in divergent
            ],
            "overlaps": [{"id": entry["id"], "path": entry["path"], "collisions": entry["collisions"]} for entry in overlaps],
            "external_links": [{"id": entry["id"], "path": entry["path"], "link": entry["link"]} for entry in external],
            "warnings": warnings,
        }, indent=2, ensure_ascii=False))
        return conflict_exit(args, divergent)

    if not divergent:
        print("Runtime and canonical sources agree.")
    for entry, action, reason in divergent:
        print(f"{action:<8} {entry['path']}")
        print(f"         owner: {entry['owner']}, state: {entry['state']}, trust: {entry['trust']}")
        print(f"         reason: {reason}")
        for collision in entry["collisions"]:
            print(f"         also claimed by {collision['owner']} via {collision['record']}")
    if overlaps:
        print()
        print("Claimed by more than one record while still matching the canonical source:")
        for entry in overlaps:
            print(f"  {entry['path']} ({', '.join(collision['owner'] for collision in entry['collisions'])})")
    if external:
        print()
        print("Activated paths that link outside the managed runtime:")
        for entry in external:
            print(f"  {entry['path']} -> {entry['link']}")
    print()
    print(f"{len(divergent)} path(s) need a decision. This command changed nothing.")
    print_warnings(warnings)
    return conflict_exit(args, divergent)


def conflict_exit(args, divergent):
    if args.fail_on_conflict and any(action == "conflict" for _, action, _ in divergent):
        return 1
    return 0


def parser():
    top = argparse.ArgumentParser(description=__doc__)
    top.add_argument("--repo", required=True)
    top.add_argument("--home", required=True)
    top.add_argument("--user-home", required=True)
    sub = top.add_subparsers(dest="command", required=True)
    for name, handler in (("report", cmd_report), ("plan", cmd_plan), ("reconcile", cmd_reconcile)):
        command = sub.add_parser(name)
        command.add_argument("--json", action="store_true")
        command.add_argument("--kind", action="append", choices=ALL_KINDS, help="limit the output to one runtime kind")
        if name == "reconcile":
            command.add_argument("--fail-on-conflict", action="store_true")
        command.set_defaults(handler=handler)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    if not hasattr(args, "fail_on_conflict"):
        args.fail_on_conflict = False
    try:
        catalog_data(args.repo)
        entries, warnings = build_entries(args.repo, args.home, args.user_home, kinds=args.kind)
    except (EcosystemError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return args.handler(args, entries, warnings)


if __name__ == "__main__":
    raise SystemExit(main())
