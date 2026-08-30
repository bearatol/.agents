#!/usr/bin/env python3

"""Safe, dependency-free storage and collaboration commands for .agents."""

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import sys
import tempfile
from datetime import datetime, timezone


SCHEMA_VERSION = 1
KIND_RE = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
MAX_FILES = 1000
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 25 * 1024 * 1024
MAX_DEPTH = 12
FORBIDDEN_NAMES = {
    ".env", "credentials", "credentials.json", "id_dsa", "id_ecdsa",
    "id_ed25519", "id_rsa", "secrets.json",
}
FORBIDDEN_SUFFIXES = {
    ".bin", ".ckpt", ".gguf", ".key", ".p12", ".pem", ".pfx",
    ".pt", ".pth", ".safetensors",
}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
)


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_token(value, label, pattern=NAME_RE):
    if not pattern.fullmatch(value):
        fail(f"invalid {label}: use lowercase letters, numbers, dots, dashes, or underscores")
    return value


def validate_text(value, label):
    if not isinstance(value, str) or not value.strip() or "\0" in value or len(value) > 10000:
        fail(f"invalid {label}: provide 1 to 10000 visible characters")
    encoded = value.encode("utf-8")
    if any(pattern.search(encoded) for pattern in SECRET_PATTERNS):
        fail(f"secret-like content is not allowed in {label}")
    return value


def validate_text_list(values, label):
    return [validate_text(value, label) for value in values or []]


def workspace_root(repo):
    return repo / "workspace"


def require_workspace(repo):
    root = workspace_root(repo)
    manifest = root / "workspace.json"
    if not manifest.is_file():
        fail("personal workspace is not initialized; run 'agents library init'")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read workspace manifest: {exc}")
    if data != {"schema_version": SCHEMA_VERSION}:
        fail("unsupported or invalid workspace manifest")
    return root


def ensure_contained(path, root):
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        fail(f"path leaves its safety root: {path}")


class WorkspaceLock:
    def __init__(self, root):
        self.path = root / ".lock"
        self.fd = None

    def __enter__(self):
        try:
            self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(self.fd, f"pid={os.getpid()}\n".encode("ascii"))
            os.fsync(self.fd)
        except FileExistsError:
            fail("workspace is busy; wait for the other command to finish")
        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def write_json_exclusive(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            fail(f"already exists: {path}")
    except BaseException:
        pathlib.Path(temporary).unlink(missing_ok=True)
        raise
    pathlib.Path(temporary).unlink(missing_ok=True)


def write_json_replace(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        pathlib.Path(temporary).unlink(missing_ok=True)
        raise


def forbidden_file(path):
    lower = path.name.lower()
    return lower in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES


def scan_secret(path):
    if forbidden_file(path):
        return "forbidden secret or model filename"
    try:
        with path.open("rb") as stream:
            sample = stream.read(min(MAX_FILE_BYTES, 1024 * 1024) + 1)
    except OSError as exc:
        return f"cannot read file: {exc}"
    for pattern in SECRET_PATTERNS:
        if pattern.search(sample):
            return "secret-like content"
    return None


def source_files(source):
    source = source.absolute()
    try:
        source_mode = source.lstat().st_mode
    except OSError as exc:
        fail(f"cannot inspect source: {exc}")
    if stat.S_ISLNK(source_mode):
        fail("source cannot be a symbolic link")
    if stat.S_ISREG(source_mode):
        candidates = [(source, pathlib.Path(source.name))]
    elif stat.S_ISDIR(source_mode):
        candidates = []
        for current, dirs, files in os.walk(source, followlinks=False):
            current_path = pathlib.Path(current)
            relative_dir = current_path.relative_to(source)
            if len(relative_dir.parts) > MAX_DEPTH:
                fail(f"source is deeper than {MAX_DEPTH} directories")
            if ".git" in dirs:
                fail("source cannot contain a .git directory")
            for entry in list(dirs) + list(files):
                entry_path = current_path / entry
                try:
                    mode = entry_path.lstat().st_mode
                except OSError as exc:
                    fail(f"cannot inspect source entry: {exc}")
                if stat.S_ISLNK(mode):
                    fail(f"symbolic links are not allowed: {entry_path}")
                if entry in dirs and not stat.S_ISDIR(mode):
                    fail(f"unsupported directory entry: {entry_path}")
                if entry in files and not stat.S_ISREG(mode):
                    fail(f"special files are not allowed: {entry_path}")
            for filename in files:
                path = current_path / filename
                candidates.append((path, path.relative_to(source)))
    else:
        fail("source must be a regular file or directory")
    if not candidates:
        fail("source contains no files")
    if len(candidates) > MAX_FILES:
        fail(f"source contains more than {MAX_FILES} files")
    total = 0
    checked = []
    for path, relative in sorted(candidates, key=lambda pair: pair[1].as_posix()):
        if len(relative.parts) > MAX_DEPTH + 1:
            fail(f"source is deeper than {MAX_DEPTH} directories")
        size = path.stat(follow_symlinks=False).st_size
        if size > MAX_FILE_BYTES:
            fail(f"file is larger than {MAX_FILE_BYTES} bytes: {relative}")
        total += size
        if total > MAX_TOTAL_BYTES:
            fail(f"source is larger than {MAX_TOTAL_BYTES} bytes in total")
        issue = scan_secret(path)
        if issue:
            fail(f"{issue}: {relative}")
        checked.append((path, relative, size))
    return checked, total


def copy_regular_file(source, target, expected_size):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    source_fd = os.open(source, flags)
    try:
        mode = os.fstat(source_fd).st_mode
        if not stat.S_ISREG(mode) or os.fstat(source_fd).st_size != expected_size:
            fail(f"source changed during import: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target_fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            while True:
                chunk = os.read(source_fd, 1024 * 1024)
                if not chunk:
                    break
                os.write(target_fd, chunk)
            os.fsync(target_fd)
        finally:
            os.close(target_fd)
    finally:
        os.close(source_fd)


def tree_digest(root):
    digest = hashlib.sha256()
    file_count = 0
    total = 0
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                digest.update(chunk)
        file_count += 1
    return digest.hexdigest(), file_count, total


def validate_copied_tree(root):
    for path in root.rglob("*"):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or (not stat.S_ISDIR(mode) and not stat.S_ISREG(mode)):
            fail(f"unsafe file appeared during copy: {path.relative_to(root)}")
        if stat.S_ISREG(mode):
            issue = scan_secret(path)
            if issue:
                fail(f"{issue}: {path.relative_to(root)}")


def cmd_library_init(args):
    root = workspace_root(args.repo)
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "workspace.json"
    if manifest.exists():
        require_workspace(args.repo)
        print(f"Personal workspace is ready: {root}")
        return
    write_json_exclusive(manifest, {"schema_version": SCHEMA_VERSION})
    for directory in ("library", "projects", ".index", ".staging"):
        (root / directory).mkdir(exist_ok=True)
    print(f"Personal workspace created: {root}")


def item_paths(root, kind, name):
    validate_token(kind, "type", KIND_RE)
    validate_token(name, "name")
    item = root / "library" / kind / name
    metadata = root / ".index" / kind / f"{name}.json"
    ensure_contained(item, root)
    ensure_contained(metadata, root)
    return item, metadata


def cmd_library_add(args):
    root = require_workspace(args.repo)
    item, metadata = item_paths(root, args.kind, args.name)
    source = pathlib.Path(args.source).expanduser().absolute()
    ensure_contained(item, root)
    if source == root or root in source.parents or source in root.parents:
        fail("source and personal workspace must be separate")
    files, total = source_files(source)
    with WorkspaceLock(root):
        if item.exists() or metadata.exists():
            fail(f"library item already exists: {args.kind}/{args.name}")
        staging = root / ".staging" / f"{args.kind}-{args.name}-{os.getpid()}"
        try:
            staging.mkdir(parents=True, exist_ok=False)
            for source_file, relative, size in files:
                copy_regular_file(source_file, staging / relative, size)
            validate_copied_tree(staging)
            digest, file_count, copied_total = tree_digest(staging)
            if copied_total != total:
                fail("source changed during import")
            item.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging, item)
            write_json_exclusive(metadata, {
                "schema_version": SCHEMA_VERSION,
                "type": args.kind,
                "name": args.name,
                "sha256": digest,
                "files": file_count,
                "bytes": copied_total,
                "trusted": False,
                "added_at": utc_now(),
            })
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            if item.exists() and not metadata.exists():
                shutil.rmtree(item, ignore_errors=True)
            raise
    print(f"Added {args.kind}/{args.name} as inactive; review it, then run 'agents library trust {args.kind} {args.name}'")


def load_item_metadata(root, kind, name):
    item, metadata_path = item_paths(root, kind, name)
    if not item.is_dir() or not metadata_path.is_file():
        fail(f"unknown library item: {kind}/{name}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read item metadata: {exc}")
    return item, metadata_path, metadata


def cmd_library_trust(args):
    root = require_workspace(args.repo)
    with WorkspaceLock(root):
        item, metadata_path, metadata = load_item_metadata(root, args.kind, args.name)
        validate_copied_tree(item)
        digest, file_count, total = tree_digest(item)
        if (digest, file_count, total) != (metadata.get("sha256"), metadata.get("files"), metadata.get("bytes")):
            fail("library item changed after import; add it again under a new name")
        metadata["trusted"] = True
        metadata["trusted_at"] = utc_now()
        write_json_replace(metadata_path, metadata)
    print(f"Trusted {args.kind}/{args.name}; adapters still require explicit connection")


def cmd_library_activate(args):
    root = require_workspace(args.repo)
    if args.kind != "skill":
        fail("this version can activate only skills; other types remain safely stored")
    if args.home is None:
        fail("internal error: installed .agents home is required for activation")
    home = args.home
    home.mkdir(parents=True, exist_ok=True)
    item, _, metadata = load_item_metadata(root, args.kind, args.name)
    if not metadata.get("trusted"):
        fail("review and trust the library item before activation")
    validate_copied_tree(item)
    digest, file_count, total = tree_digest(item)
    if (digest, file_count, total) != (metadata.get("sha256"), metadata.get("files"), metadata.get("bytes")):
        fail("library item changed after review; add it again under a new name")
    if not (item / "SKILL.md").is_file():
        fail("a skill must contain SKILL.md at its root")
    destination = home / "skills" / args.name
    ensure_contained(destination, home)
    with WorkspaceLock(root):
        if destination.exists() or destination.is_symlink():
            fail(f"activation target already exists: {destination}")
        stage_root = home / ".workspace-staging"
        if stage_root.is_symlink():
            fail(f"activation staging path cannot be a symbolic link: {stage_root}")
        stage_root.mkdir(parents=True, exist_ok=True)
        ensure_contained(stage_root, home)
        staging = stage_root / f"skill-{args.name}-{os.getpid()}"
        try:
            staging.mkdir(parents=True, exist_ok=False)
            files, _ = source_files(item)
            for source_file, relative, size in files:
                copy_regular_file(source_file, staging / relative, size)
            validate_copied_tree(staging)
            digest_copy, count_copy, total_copy = tree_digest(staging)
            if (digest_copy, count_copy, total_copy) != (digest, file_count, total):
                fail("library item changed during activation")
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging, destination)
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            raise
    print(f"Activated skill {args.name} in {destination}; reconnect hosts to publish it")


def cmd_library_list(args):
    root = require_workspace(args.repo)
    index = root / ".index"
    rows = []
    for path in sorted(index.glob("*/*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            rows.append((path.parent.name, path.stem, "invalid", 0, 0))
            continue
        rows.append((data.get("type", path.parent.name), data.get("name", path.stem), "trusted" if data.get("trusted") else "inactive", data.get("files", 0), data.get("bytes", 0)))
    if args.json:
        print(json.dumps([
            {"type": kind, "name": name, "status": status, "files": files, "bytes": size}
            for kind, name, status, files, size in rows
        ], indent=2, ensure_ascii=False))
        return
    if not rows:
        print("Personal library is empty.")
        return
    for kind, name, status, files, size in rows:
        print(f"{status:<8} {kind}/{name} ({files} files, {size} bytes)")


def workspace_errors(root):
    errors = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == ".staging":
            continue
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            errors.append(f"cannot inspect {relative}: {exc}")
            continue
        if stat.S_ISLNK(mode):
            errors.append(f"symbolic link is not allowed: {relative}")
        elif path.is_file():
            issue = scan_secret(path)
            if issue:
                errors.append(f"{issue}: {relative}")
    for metadata_path in sorted((root / ".index").glob("*/*.json")):
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            item, _, _ = load_item_metadata(root, data["type"], data["name"])
            digest, files, total = tree_digest(item)
            if (digest, files, total) != (data.get("sha256"), data.get("files"), data.get("bytes")):
                errors.append(f"library item changed outside the CLI: {data.get('type')}/{data.get('name')}")
        except (KeyError, OSError, json.JSONDecodeError, SystemExit):
            errors.append(f"invalid library metadata: {metadata_path.relative_to(root)}")
    return errors


def cmd_library_check(args):
    root = require_workspace(args.repo)
    errors = workspace_errors(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("Personal workspace check passed.")


def project_paths(root, project):
    validate_token(project, "project")
    base = root / "projects" / project
    ensure_contained(base, root)
    return base, base / "project.json"


def load_project(root, project):
    base, manifest = project_paths(root, project)
    if not manifest.is_file():
        fail(f"unknown team project: {project}")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read team project: {exc}")
    return base, data


def normalized_many(values, label):
    result = []
    for value in values or []:
        validate_token(value, label)
        if value not in result:
            result.append(value)
    return result


def cmd_team_init(args):
    root = require_workspace(args.repo)
    base, manifest = project_paths(root, args.project)
    coordinator = validate_token(args.coordinator, "coordinator")
    members = normalized_many(args.member, "member")
    if coordinator not in members:
        members.insert(0, coordinator)
    objective = validate_text(args.objective, "objective")
    with WorkspaceLock(root):
        if base.exists():
            fail(f"team project already exists: {args.project}")
        for directory in ("tasks", "results", "reviews", "decisions"):
            (base / directory).mkdir(parents=True, exist_ok=True)
        write_json_exclusive(manifest, {
            "schema_version": SCHEMA_VERSION,
            "project": args.project,
            "objective": objective,
            "coordinator": coordinator,
            "members": members,
            "created_at": utc_now(),
        })
    print(f"Team project created: {args.project} ({', '.join(members)})")


def attempt_dir(base, section, task, attempt):
    validate_token(task, "task")
    if attempt < 1 or attempt > 999:
        fail("attempt must be between 1 and 999")
    path = base / section / task / f"attempt-{attempt:03d}"
    ensure_contained(path, base)
    return path


def cmd_team_task(args):
    root = require_workspace(args.repo)
    base, project = load_project(root, args.project)
    worker = validate_token(args.worker, "worker")
    role = validate_token(args.role, "role")
    reviewers = normalized_many(args.reviewer, "reviewer")
    if worker not in project["members"]:
        fail(f"worker is not a project member: {worker}")
    if any(reviewer not in project["members"] for reviewer in reviewers):
        fail("every reviewer must be a project member")
    if worker in reviewers:
        fail("worker cannot review its own task")
    directory = attempt_dir(base, "tasks", args.task, args.attempt)
    previous = attempt_dir(base, "tasks", args.task, args.attempt - 1) if args.attempt > 1 else None
    if previous and not (previous / "task.json").is_file():
        fail("create the previous attempt first")
    packet = {
        "schema_version": SCHEMA_VERSION,
        "project": args.project,
        "task_id": args.task,
        "attempt": args.attempt,
        "title": validate_text(args.title, "title"),
        "objective": validate_text(args.objective, "objective"),
        "assigned_role": role,
        "worker": worker,
        "reviewers": reviewers,
        "scope": validate_text_list(args.scope, "scope"),
        "acceptance_criteria": validate_text_list(args.accept, "acceptance criterion"),
        "inputs": validate_text_list(args.input, "input"),
        "created_at": utc_now(),
    }
    with WorkspaceLock(root):
        write_json_exclusive(directory / "task.json", packet)
    print(f"Task created: {args.project}/{args.task} attempt {args.attempt} -> {worker} ({role})")


def current_attempt(base, task):
    task_root = base / "tasks" / task
    attempts = sorted(path for path in task_root.glob("attempt-*") if (path / "task.json").is_file())
    if not attempts:
        fail(f"unknown task: {task}")
    return int(attempts[-1].name.removeprefix("attempt-"))


def load_task(base, task, attempt):
    path = attempt_dir(base, "tasks", task, attempt) / "task.json"
    if not path.is_file():
        fail(f"unknown task attempt: {task}/{attempt}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read task: {exc}")


def cmd_team_result(args):
    root = require_workspace(args.repo)
    base, _ = load_project(root, args.project)
    if current_attempt(base, args.task) != args.attempt:
        fail("stale result: use the current task attempt")
    task = load_task(base, args.task, args.attempt)
    worker = validate_token(args.worker, "worker")
    if worker != task["worker"]:
        fail("result worker does not match the task assignment")
    packet = {
        "schema_version": SCHEMA_VERSION,
        "project": args.project,
        "task_id": args.task,
        "attempt": args.attempt,
        "worker": worker,
        "status": args.status,
        "summary": validate_text(args.summary, "summary"),
        "evidence": validate_text_list(args.evidence, "evidence"),
        "created_at": utc_now(),
    }
    target = attempt_dir(base, "results", args.task, args.attempt) / f"{worker}.json"
    with WorkspaceLock(root):
        write_json_exclusive(target, packet)
    print(f"Result recorded: {args.project}/{args.task} attempt {args.attempt} by {worker}")


def cmd_team_review(args):
    root = require_workspace(args.repo)
    base, _ = load_project(root, args.project)
    if current_attempt(base, args.task) != args.attempt:
        fail("stale review: use the current task attempt")
    task = load_task(base, args.task, args.attempt)
    reviewer = validate_token(args.reviewer, "reviewer")
    if reviewer not in task["reviewers"]:
        fail("reviewer is not assigned to this task")
    result = attempt_dir(base, "results", args.task, args.attempt) / f"{task['worker']}.json"
    if not result.is_file():
        fail("record the worker result before a review")
    packet = {
        "schema_version": SCHEMA_VERSION,
        "project": args.project,
        "task_id": args.task,
        "attempt": args.attempt,
        "reviewer": reviewer,
        "verdict": args.verdict,
        "summary": validate_text(args.summary, "summary"),
        "created_at": utc_now(),
    }
    target = attempt_dir(base, "reviews", args.task, args.attempt) / f"{reviewer}.json"
    with WorkspaceLock(root):
        write_json_exclusive(target, packet)
    print(f"Review recorded: {args.verdict} by {reviewer}")


def cmd_team_decide(args):
    root = require_workspace(args.repo)
    base, project = load_project(root, args.project)
    coordinator = validate_token(args.coordinator, "coordinator")
    if coordinator != project["coordinator"]:
        fail("only the recorded coordinator may write the decision")
    if current_attempt(base, args.task) != args.attempt:
        fail("stale decision: use the current task attempt")
    task = load_task(base, args.task, args.attempt)
    result = attempt_dir(base, "results", args.task, args.attempt) / f"{task['worker']}.json"
    if not result.is_file():
        fail("record the worker result before a decision")
    review_root = attempt_dir(base, "reviews", args.task, args.attempt)
    missing = [reviewer for reviewer in task["reviewers"] if not (review_root / f"{reviewer}.json").is_file()]
    if missing:
        fail(f"missing assigned reviews: {', '.join(missing)}")
    packet = {
        "schema_version": SCHEMA_VERSION,
        "project": args.project,
        "task_id": args.task,
        "attempt": args.attempt,
        "coordinator": coordinator,
        "decision": args.decision,
        "summary": validate_text(args.summary, "summary"),
        "created_at": utc_now(),
    }
    target = attempt_dir(base, "decisions", args.task, args.attempt) / "decision.json"
    with WorkspaceLock(root):
        write_json_exclusive(target, packet)
    print(f"Decision recorded: {args.decision} by {coordinator}")


def cmd_team_status(args):
    root = require_workspace(args.repo)
    base, project = load_project(root, args.project)
    print(f"{project['project']}: {project['objective']}")
    print(f"team: {', '.join(project['members'])}; coordinator: {project['coordinator']}")
    task_root = base / "tasks"
    task_names = sorted(path.name for path in task_root.iterdir() if path.is_dir())
    if not task_names:
        print("No tasks yet.")
        return
    for task_name in task_names:
        attempt = current_attempt(base, task_name)
        task = load_task(base, task_name, attempt)
        result = attempt_dir(base, "results", task_name, attempt) / f"{task['worker']}.json"
        reviews = attempt_dir(base, "reviews", task_name, attempt)
        decision = attempt_dir(base, "decisions", task_name, attempt) / "decision.json"
        done_reviews = sum((reviews / f"{reviewer}.json").is_file() for reviewer in task["reviewers"])
        state = "decided" if decision.is_file() else "review" if result.is_file() else "ready"
        print(f"{state:<7} {task_name}#{attempt} -> {task['worker']} ({done_reviews}/{len(task['reviewers'])} reviews)")


def parser():
    result = argparse.ArgumentParser(description="Manage portable .agents data and multi-host work")
    result.add_argument("--repo", type=lambda value: pathlib.Path(value).expanduser().resolve(), required=True)
    result.add_argument("--home", type=lambda value: pathlib.Path(value).expanduser().resolve())
    top = result.add_subparsers(dest="area", required=True)

    library = top.add_parser("library", help="manage personal reusable data")
    library_sub = library.add_subparsers(dest="command", required=True)
    library_sub.add_parser("init").set_defaults(handler=cmd_library_init)
    add = library_sub.add_parser("add")
    add.add_argument("kind")
    add.add_argument("name")
    add.add_argument("source")
    add.set_defaults(handler=cmd_library_add)
    trust = library_sub.add_parser("trust")
    trust.add_argument("kind")
    trust.add_argument("name")
    trust.set_defaults(handler=cmd_library_trust)
    activate = library_sub.add_parser("activate")
    activate.add_argument("kind")
    activate.add_argument("name")
    activate.set_defaults(handler=cmd_library_activate)
    listing = library_sub.add_parser("list")
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(handler=cmd_library_list)
    library_sub.add_parser("check").set_defaults(handler=cmd_library_check)

    team = top.add_parser("team", help="coordinate several AI hosts through shared files")
    team_sub = team.add_subparsers(dest="command", required=True)
    init = team_sub.add_parser("init")
    init.add_argument("project")
    init.add_argument("--objective", required=True)
    init.add_argument("--coordinator", required=True)
    init.add_argument("--member", action="append", default=[])
    init.set_defaults(handler=cmd_team_init)
    task = team_sub.add_parser("task")
    task.add_argument("project")
    task.add_argument("task")
    task.add_argument("--attempt", type=int, default=1)
    task.add_argument("--title", required=True)
    task.add_argument("--objective", required=True)
    task.add_argument("--role", required=True)
    task.add_argument("--worker", required=True)
    task.add_argument("--reviewer", action="append", default=[])
    task.add_argument("--scope", action="append", required=True)
    task.add_argument("--accept", action="append", required=True)
    task.add_argument("--input", action="append", default=[])
    task.set_defaults(handler=cmd_team_task)
    result_cmd = team_sub.add_parser("result")
    result_cmd.add_argument("project")
    result_cmd.add_argument("task")
    result_cmd.add_argument("--attempt", type=int, default=1)
    result_cmd.add_argument("--worker", required=True)
    result_cmd.add_argument("--status", choices=["complete", "blocked", "failed"], required=True)
    result_cmd.add_argument("--summary", required=True)
    result_cmd.add_argument("--evidence", action="append", default=[])
    result_cmd.set_defaults(handler=cmd_team_result)
    review = team_sub.add_parser("review")
    review.add_argument("project")
    review.add_argument("task")
    review.add_argument("--attempt", type=int, default=1)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--verdict", choices=["approve", "changes-requested"], required=True)
    review.add_argument("--summary", required=True)
    review.set_defaults(handler=cmd_team_review)
    decide = team_sub.add_parser("decide")
    decide.add_argument("project")
    decide.add_argument("task")
    decide.add_argument("--attempt", type=int, default=1)
    decide.add_argument("--coordinator", required=True)
    decide.add_argument("--decision", choices=["accept", "retry", "reject"], required=True)
    decide.add_argument("--summary", required=True)
    decide.set_defaults(handler=cmd_team_decide)
    status_cmd = team_sub.add_parser("status")
    status_cmd.add_argument("project")
    status_cmd.set_defaults(handler=cmd_team_status)
    return result


def main():
    args = parser().parse_args()
    if not args.repo.is_dir():
        fail(f"repository does not exist: {args.repo}")
    args.handler(args)


if __name__ == "__main__":
    main()
