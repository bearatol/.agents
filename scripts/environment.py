#!/usr/bin/env python3
"""Portable manifest and drift operations for the agent ecosystem."""

import argparse
import contextlib
import errno
import hashlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

from state import digest_path, load_state, save_state


MAX_MANIFEST_BYTES = 1024 * 1024
MAX_ITEMS = 512
MAX_STRING = 256
FIELDS = {
    "schema_version",
    "ecosystem_version",
    "commit",
    "profiles",
    "components",
    "hosts",
}
HOSTS = {"codex", "claude", "gemini", "koda", "sourcecraft", "generic"}
NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
COMMIT = re.compile(r"^[0-9a-fA-F]{40}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")


class EnvironmentError(Exception):
    pass


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EnvironmentError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def read_json_file(path, *, limited=False, no_follow=False):
    path = pathlib.Path(path)
    flags = os.O_RDONLY
    if no_follow and hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise EnvironmentError(f"refusing symbolic-link input: {path}") from exc
        raise EnvironmentError(f"cannot read JSON file {path}: {exc}") from exc
    try:
        size = os.fstat(descriptor).st_size
        if limited and size > MAX_MANIFEST_BYTES:
            raise EnvironmentError("manifest exceeds 1 MiB")
        with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
            try:
                return json.load(handle, object_pairs_hook=reject_duplicates)
            except (json.JSONDecodeError, UnicodeError) as exc:
                raise EnvironmentError(f"invalid JSON: {exc}") from exc
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def catalog_data(repo):
    data = read_json_file(pathlib.Path(repo) / "catalog" / "catalog.json")
    if not isinstance(data, dict) or not isinstance(data.get("components"), list):
        raise EnvironmentError("invalid catalog")
    return data


def read_lines(path):
    path = pathlib.Path(path)
    if not path.is_file():
        return []
    values = []
    seen = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        value = raw.strip()
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return values


def validate_string_list(value, field, validator):
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        raise EnvironmentError(f"{field} must be an array with at most {MAX_ITEMS} items")
    seen = set()
    result = []
    for item in value:
        if not isinstance(item, str) or not item or len(item) > MAX_STRING:
            raise EnvironmentError(f"invalid {field} entry")
        if item in seen:
            raise EnvironmentError(f"duplicate {field} entry: {item}")
        if not validator(item):
            raise EnvironmentError(f"invalid {field} entry: {item}")
        seen.add(item)
        result.append(item)
    return result


def validate_manifest(path, repo, *, provenance):
    document = read_json_file(path, limited=True, no_follow=True)
    if not isinstance(document, dict) or set(document) != FIELDS:
        unknown = set(document) - FIELDS if isinstance(document, dict) else set()
        missing = FIELDS - set(document) if isinstance(document, dict) else FIELDS
        details = []
        if unknown:
            details.append("unknown fields: " + ", ".join(sorted(unknown)))
        if missing:
            details.append("missing fields: " + ", ".join(sorted(missing)))
        raise EnvironmentError("invalid manifest fields" + (": " + "; ".join(details) if details else ""))
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise EnvironmentError("schema_version must be 1")
    version = document["ecosystem_version"]
    if not isinstance(version, str) or len(version) > 64 or not VERSION.fullmatch(version):
        raise EnvironmentError("invalid ecosystem_version")
    commit = document["commit"]
    if not isinstance(commit, str) or not COMMIT.fullmatch(commit):
        raise EnvironmentError("commit must be a full 40-character SHA")

    repo = pathlib.Path(repo)
    catalog = catalog_data(repo)
    if version != catalog.get("ecosystem_version"):
        raise EnvironmentError(
            f"ecosystem version mismatch: manifest {version}, checkout {catalog.get('ecosystem_version')}"
        )
    catalog_ids = {item.get("id") for item in catalog["components"] if isinstance(item, dict)}
    profiles = validate_string_list(
        document["profiles"],
        "profiles",
        lambda name: bool(NAME.fullmatch(name)) and (repo / "profiles" / f"{name}.profile").is_file(),
    )
    components = validate_string_list(document["components"], "components", lambda item: item in catalog_ids)
    hosts = validate_string_list(document["hosts"], "hosts", lambda item: item in HOSTS)
    if provenance:
        check_provenance(repo, commit, path)
    document["profiles"] = profiles
    document["components"] = components
    document["hosts"] = hosts
    document["commit"] = commit.lower()
    return document


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise EnvironmentError(result.stderr.strip() or "Git provenance check failed")
    return result.stdout.strip()


def check_clean_worktree(repo, allowed_untracked=None):
    status = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [entry for entry in status.split("\0") if entry]
    allowed_entry = None
    if allowed_untracked is not None:
        repo_path = pathlib.Path(repo).resolve()
        candidate = pathlib.Path(allowed_untracked).resolve()
        try:
            relative = candidate.relative_to(repo_path).as_posix()
        except ValueError:
            pass
        else:
            allowed_entry = f"?? {relative}"
    unexpected = [entry for entry in entries if entry != allowed_entry]
    if unexpected:
        raise EnvironmentError(
            "checkout has uncommitted or untracked changes; operation requires a clean reviewed checkout"
        )


def check_provenance(repo, commit, manifest):
    check_clean_worktree(repo, allowed_untracked=manifest)
    head = git(repo, "rev-parse", "HEAD")
    if head.lower() != commit.lower():
        raise EnvironmentError(
            f"checkout mismatch: manifest requires {commit.lower()}, current checkout is {head.lower()}; "
            "review and change the checkout separately"
        )
    upstream = None
    for candidate in ("@{u}", "refs/remotes/origin/HEAD"):
        try:
            upstream = git(repo, "rev-parse", candidate)
            break
        except EnvironmentError:
            continue
    if upstream is None:
        raise EnvironmentError("no configured local upstream history; configure an upstream before restore")
    result = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, upstream],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode:
        raise EnvironmentError("manifest commit is not in the configured upstream history")


def atomic_export(document, output):
    output = pathlib.Path(output)
    parent = output.parent
    if not parent.is_dir():
        raise EnvironmentError(f"output directory does not exist: {parent}")
    if output.exists() or output.is_symlink():
        raise EnvironmentError(f"refusing to overwrite: {output}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=parent)
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            if os.name == "nt":
                os.rename(temporary, output)
            else:
                os.link(temporary, output)
        except FileExistsError as exc:
            raise EnvironmentError(f"refusing to overwrite: {output}") from exc
        if os.name != "nt":
            directory = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def component_paths(repo, home):
    catalog = catalog_data(repo)
    entries = {}
    for item in catalog["components"]:
        if not isinstance(item, dict) or not item.get("id") or not item.get("path"):
            continue
        component_id = item["id"]
        kind, name = component_id.split(":", 1)
        destinations = {
            "skill": home / "skills" / name,
            "agent": home / "agents" / f"{name}.md",
            "rule": home / "rules" / f"{name}.md",
            "model": home / "local-models" / name,
            "orchestration": home / "orchestration",
            "tool": home / "tools" / name,
        }
        if kind in destinations:
            entries[component_id] = (repo / item["path"], destinations[kind])
    return entries


def classify(source, installed, state_entry):
    if not installed.exists() and not installed.is_symlink():
        return "missing"
    try:
        installed_hash = digest_path(installed)
        source_hash = digest_path(source)
    except OSError:
        return "locally-modified"
    if installed_hash == source_hash:
        return "current"
    if state_entry:
        recorded_actual = powershell_hash_path(installed) if state_entry.get("hash_kind") == "powershell" else installed_hash
        if state_entry.get("installed_hash") == recorded_actual:
            return "managed-stale"
    return "locally-modified"


def powershell_hash_path(path):
    path = pathlib.Path(path)
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    records = []
    root = path.resolve()
    for item in sorted((entry for entry in path.rglob("*") if entry.is_file()), key=lambda entry: str(entry.resolve())):
        relative = item.resolve().relative_to(root).as_posix()
        records.append(f"{relative}\0{hashlib.sha256(item.read_bytes()).hexdigest()}\n")
    return hashlib.sha256("".join(records).encode()).hexdigest()


def environment_state(home):
    unix_path = home / ".ecosystem-state.json"
    if unix_path.is_file():
        return load_state(unix_path).get("components", {})
    windows_path = home / ".ecosystem-state-windows.json"
    if not windows_path.is_file():
        return {}
    data = read_json_file(windows_path)
    entries = {}
    for item in data.get("entries", []) if isinstance(data, dict) else []:
        if isinstance(item, dict) and isinstance(item.get("id"), str) and isinstance(item.get("hash"), str):
            entries[item["id"]] = {"installed_hash": item["hash"], "hash_kind": "powershell"}
    return entries


def host_target(user_home, host, state_id):
    parts = state_id.split(":", 3)
    if len(parts) != 4:
        return None
    _, state_host, kind, name = parts
    if state_host != host:
        return None
    roots = {
        "codex": user_home / ".codex",
        "claude": user_home / ".claude",
        "gemini": user_home / ".gemini",
        "sourcecraft": user_home / ".config" / "opencode",
    }
    root = roots.get(host)
    if root is None:
        return None
    if kind == "skill":
        return root / "skills" / name
    extensions = {"codex": ".toml", "claude": ".md", "gemini": ".md", "sourcecraft": ".md"}
    if kind == "agent":
        return root / "agents" / f"{name}{extensions[host]}"
    if host == "sourcecraft" and kind == "rule" and name == "agent-ecosystem":
        return user_home / ".codeassistant" / "rules" / "agent-ecosystem.md"
    return None


def run_status(repo, home, user_home):
    repo = pathlib.Path(repo)
    home = pathlib.Path(home)
    user_home = pathlib.Path(user_home)
    installed_components = read_lines(home / ".ecosystem-installed")
    if not installed_components:
        print("missing        environment:not-installed")
        return 1
    state_entries = environment_state(home)
    paths = component_paths(repo, home)
    unsafe = False
    for component_id in installed_components:
        if component_id not in paths:
            status = "locally-modified"
        else:
            source, installed = paths[component_id]
            status = classify(source, installed, state_entries.get(component_id))
        print(f"{status:<14} {component_id}")
        unsafe = unsafe or status != "current"

    root_paths = {
        "root:AGENTS.md": (repo / "AGENTS.md", home / "AGENTS.md"),
        "root:CONNECT.md": (repo / "CONNECT.md", home / "CONNECT.md"),
        "root:catalog.json": (repo / "catalog" / "catalog.json", home / "catalog.json"),
        "root:migrations.json": (repo / "catalog" / "migrations.json", home / "migrations.json"),
    }
    for state_id in sorted(key for key in state_entries if key.startswith("root:")):
        paths = root_paths.get(state_id)
        status = "locally-modified" if paths is None else classify(*paths, state_entries[state_id])
        print(f"{status:<14} {state_id}")
        unsafe = unsafe or status != "current"

    for host in read_lines(home / ".ecosystem-hosts"):
        if host not in HOSTS:
            print(f"host-conflicting host:{host}")
            unsafe = True
            continue
        if host in {"generic", "koda"}:
            print(f"current        host:{host}")
            continue
        host_entries = {key: value for key, value in state_entries.items() if key.startswith(f"host:{host}:")}
        if not host_entries:
            skills = home / "skills"
            for skill in sorted(skills.iterdir()) if skills.is_dir() else []:
                if not (skill / "SKILL.md").is_file():
                    continue
                target = {
                    "codex": user_home / ".codex" / "skills" / skill.name,
                    "claude": user_home / ".claude" / "skills" / skill.name,
                    "gemini": user_home / ".gemini" / "skills" / skill.name,
                }.get(host)
                if target is None:
                    continue
                state_id = f"host:{host}:skill:{skill.name}"
                if not target.is_symlink() or pathlib.Path(os.readlink(target)) != skill:
                    print(f"host-conflicting {state_id}")
                    unsafe = True
                else:
                    print(f"current        {state_id}")
            continue
        for state_id, entry in sorted(host_entries.items()):
            target = host_target(user_home, host, state_id)
            if target is None or (not target.exists() and not target.is_symlink()):
                status = "host-conflicting"
            else:
                try:
                    actual_hash = powershell_hash_path(target) if entry.get("hash_kind") == "powershell" else digest_path(target)
                    status = "current" if actual_hash == entry.get("installed_hash") else "host-conflicting"
                except OSError:
                    status = "host-conflicting"
            print(f"{status:<14} {state_id}")
            unsafe = unsafe or status != "current"
    return 1 if unsafe else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    export_parser = sub.add_parser("export")
    export_parser.add_argument("--repo", required=True)
    export_parser.add_argument("--home", required=True)
    export_parser.add_argument("--user-home", required=True)
    export_parser.add_argument("--output", required=True)

    plan_parser = sub.add_parser("restore-plan")
    plan_parser.add_argument("--repo", required=True)
    plan_parser.add_argument("--manifest", required=True)

    status_parser = sub.add_parser("status")
    status_parser.add_argument("--repo", required=True)
    status_parser.add_argument("--home", required=True)
    status_parser.add_argument("--user-home", required=True)

    record_parser = sub.add_parser("record")
    record_parser.add_argument("--state", required=True)
    record_parser.add_argument("--id", required=True)
    record_parser.add_argument("--source", required=True)
    record_parser.add_argument("--installed", required=True)

    args = parser.parse_args()
    try:
        if args.command == "export":
            repo = pathlib.Path(args.repo)
            home = pathlib.Path(args.home)
            check_clean_worktree(repo)
            with contextlib.redirect_stdout(io.StringIO()):
                status = run_status(repo, home, pathlib.Path(args.user_home))
            if status:
                raise EnvironmentError("installed environment is not current; run status and resolve all drift")
            catalog = catalog_data(repo)
            document = {
                "schema_version": 1,
                "ecosystem_version": catalog["ecosystem_version"],
                "commit": git(repo, "rev-parse", "HEAD").lower(),
                "profiles": read_lines(home / ".ecosystem-profiles"),
                "components": read_lines(home / ".ecosystem-components"),
                "hosts": read_lines(home / ".ecosystem-hosts"),
            }
            if not document["profiles"] and not document["components"]:
                raise EnvironmentError("no installed profile or explicit component selection to export")
            temporary = pathlib.Path(args.output).with_name(f".{pathlib.Path(args.output).name}.validate")
            # Validate the same shape without accepting arbitrary state values.
            for field, validator in (
                ("profiles", lambda item: bool(NAME.fullmatch(item)) and (repo / "profiles" / f"{item}.profile").is_file()),
                ("components", lambda item: item in {c.get("id") for c in catalog["components"] if isinstance(c, dict)}),
                ("hosts", lambda item: item in HOSTS),
            ):
                validate_string_list(document[field], field, validator)
            del temporary
            atomic_export(document, args.output)
            print(args.output)
            return 0
        if args.command == "restore-plan":
            document = validate_manifest(args.manifest, args.repo, provenance=True)
            for profile in document["profiles"]:
                print(f"profile\t{profile}")
            for component in document["components"]:
                print(f"component\t{component}")
            for host in document["hosts"]:
                print(f"host\t{host}")
            return 0
        if args.command == "status":
            return run_status(args.repo, args.home, args.user_home)
        state_path = pathlib.Path(args.state)
        state = load_state(state_path)
        state.setdefault("components", {})[args.id] = {
            "source_hash": digest_path(args.source),
            "installed_hash": digest_path(args.installed),
        }
        save_state(state_path, state)
        return 0
    except (EnvironmentError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
