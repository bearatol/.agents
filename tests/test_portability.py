#!/usr/bin/env python3

import json
import hashlib
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "agents.sh"
ENVIRONMENT = ROOT / "scripts" / "environment.py"


def run(*args, env=None, check=True):
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=ROOT,
        env=merged,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


class PortableWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repository_temporary = tempfile.TemporaryDirectory(prefix="ae-clean-repo-")
        cls.clean_root = pathlib.Path(cls.repository_temporary.name) / "repo"
        run("git", "clone", "--quiet", ROOT, cls.clean_root)
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--modified", "--others", "--exclude-standard", "-z"],
            stdout=subprocess.PIPE,
            check=True,
        ).stdout
        for raw in listed.split(b"\0"):
            if not raw:
                continue
            relative = pathlib.Path(os.fsdecode(raw))
            source = ROOT / relative
            destination = cls.clean_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.is_symlink():
                destination.symlink_to(os.readlink(source))
            else:
                shutil.copy2(source, destination)
        run("git", "-C", cls.clean_root, "config", "user.email", "test@example.invalid")
        run("git", "-C", cls.clean_root, "config", "user.name", "Portability Test")
        run("git", "-C", cls.clean_root, "add", ".")
        staged = run("git", "-C", cls.clean_root, "diff", "--cached", "--quiet", check=False)
        if staged.returncode == 1:
            run("git", "-C", cls.clean_root, "commit", "--no-verify", "-m", "test snapshot")
        elif staged.returncode != 0:
            raise RuntimeError("could not inspect the temporary fixture index")
        run("git", "-C", cls.clean_root, "branch", "-M", "main")
        commit = run("git", "-C", cls.clean_root, "rev-parse", "HEAD").stdout.strip()
        run("git", "-C", cls.clean_root, "update-ref", "refs/remotes/origin/main", commit)
        run(
            "git",
            "-C",
            cls.clean_root,
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            "refs/remotes/origin/main",
        )
        cls.clean_cli = cls.clean_root / "scripts" / "agents.sh"

    @classmethod
    def tearDownClass(cls):
        cls.repository_temporary.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ae-portability-")
        self.addCleanup(self.temporary.cleanup)
        self.base = pathlib.Path(self.temporary.name)
        self.home = self.base / "agents"
        self.user = self.base / "user"
        self.env = {"AGENTS_HOME": str(self.home), "HOME": str(self.user)}

    def test_setup_export_restore_round_trip(self):
        run(
            self.clean_cli,
            "setup",
            "--profile",
            "core",
            "--component",
            "skill:software-delivery",
            "--host",
            "codex",
            env=self.env,
        )
        lock = self.base / "environment.lock.json"
        run(self.clean_cli, "export", str(lock), env=self.env)
        document = json.loads(lock.read_text(encoding="utf-8"))
        self.assertEqual(
            set(document),
            {"schema_version", "ecosystem_version", "commit", "profiles", "components", "hosts"},
        )
        self.assertEqual(document["schema_version"], 1)
        self.assertEqual(document["profiles"], ["core"])
        self.assertEqual(document["components"], ["skill:software-delivery"])
        self.assertEqual(document["hosts"], ["codex"])
        self.assertRegex(document["commit"], r"^[0-9a-f]{40}$")

        second_home = self.base / "restored-agents"
        second_user = self.base / "restored-user"
        restored_env = {"AGENTS_HOME": str(second_home), "HOME": str(second_user)}
        unrelated = second_user / ".codex" / "skills" / "ui-ux-design"
        unrelated.mkdir(parents=True)
        marker = unrelated / "personal.txt"
        marker.write_text("keep\n", encoding="utf-8")
        run(self.clean_cli, "restore", str(lock), env=restored_env)
        self.assertTrue((second_home / "skills" / "software-delivery" / "SKILL.md").is_file())
        self.assertEqual((second_home / ".ecosystem-profiles").read_text().splitlines(), ["core"])
        self.assertEqual((second_home / ".ecosystem-components").read_text().splitlines(), ["skill:software-delivery"])
        self.assertEqual((second_home / ".ecosystem-hosts").read_text().splitlines(), ["codex"])
        self.assertTrue((second_user / ".codex" / "agents" / "ceo.toml").is_file())
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")

    def test_export_refuses_to_overwrite(self):
        run(self.clean_cli, "setup", "--profile", "core", env=self.env)
        lock = self.base / "environment.lock.json"
        lock.write_text("keep me\n", encoding="utf-8")
        result = run(self.clean_cli, "export", str(lock), env=self.env, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(lock.read_text(encoding="utf-8"), "keep me\n")

    def test_export_rejects_dirty_source_and_installed_drift(self):
        run(self.clean_cli, "setup", "--profile", "core", env=self.env)
        marker = self.clean_root / "untracked-export-test.txt"
        marker.write_text("dirty\n", encoding="utf-8")
        self.addCleanup(lambda: marker.unlink(missing_ok=True))
        lock = self.base / "dirty.lock.json"
        result = run(self.clean_cli, "export", str(lock), env=self.env, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("clean reviewed checkout", result.stderr)
        self.assertFalse(lock.exists())
        marker.unlink()
        with (self.home / "AGENTS.md").open("a", encoding="utf-8") as handle:
            handle.write("\nlocal change\n")
        drift_lock = self.base / "drift.lock.json"
        drift = run(self.clean_cli, "export", str(drift_lock), env=self.env, check=False)
        self.assertNotEqual(drift.returncode, 0)
        self.assertIn("installed environment is not current", drift.stderr)
        self.assertFalse(drift_lock.exists())

    def test_status_and_export_fail_before_setup(self):
        status = run(CLI, "status", env=self.env, check=False)
        self.assertNotEqual(status.returncode, 0)
        self.assertIn("environment:not-installed", status.stdout)
        lock = self.base / "empty.lock.json"
        exported = run(CLI, "export", str(lock), env=self.env, check=False)
        self.assertNotEqual(exported.returncode, 0)
        self.assertFalse(lock.exists())

    def test_status_reads_windows_copy_state(self):
        repo = self.base / "windows-repo"
        source = repo / "library" / "skills" / "sample"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("sample\n", encoding="utf-8")
        (repo / "catalog").mkdir()
        (repo / "catalog" / "catalog.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "ecosystem_version": "1.0.0",
                    "components": [
                        {"id": "skill:sample", "type": "skill", "name": "sample", "path": "library/skills/sample"}
                    ],
                }
            ),
            encoding="utf-8",
        )
        installed = self.home / "skills" / "sample"
        installed.mkdir(parents=True)
        (installed / "SKILL.md").write_text("sample\n", encoding="utf-8")
        host_copy = self.user / ".codex" / "skills" / "sample"
        host_copy.mkdir(parents=True)
        (host_copy / "SKILL.md").write_text("sample\n", encoding="utf-8")

        def powershell_directory_hash(path):
            records = []
            root = path.resolve()
            for item in sorted(path.rglob("*"), key=lambda entry: str(entry.resolve())):
                if item.is_file():
                    relative = item.resolve().relative_to(root).as_posix()
                    digest = hashlib.sha256(item.read_bytes()).hexdigest()
                    records.append(f"{relative}\0{digest}\n")
            return hashlib.sha256("".join(records).encode()).hexdigest()

        state = {
            "version": 1,
            "entries": [
                {"id": "skill:sample", "hash": powershell_directory_hash(installed)},
                {"id": "host:codex:skill:sample", "hash": powershell_directory_hash(host_copy)},
            ],
        }
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / ".ecosystem-state-windows.json").write_text(json.dumps(state), encoding="utf-8")
        (self.home / ".ecosystem-installed").write_text("skill:sample\n", encoding="utf-8")
        (self.home / ".ecosystem-hosts").write_text("codex\n", encoding="utf-8")
        result = run(
            ENVIRONMENT,
            "status",
            "--repo",
            repo,
            "--home",
            self.home,
            "--user-home",
            self.user,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("current        host:codex:skill:sample", result.stdout)

    def test_restore_rejects_untrusted_manifests_before_writes(self):
        commit = run("git", "rev-parse", "HEAD").stdout.strip()
        catalog = json.loads((ROOT / "catalog" / "catalog.json").read_text(encoding="utf-8"))
        valid = {
            "schema_version": 1,
            "ecosystem_version": catalog["ecosystem_version"],
            "commit": commit,
            "profiles": ["core"],
            "components": [],
            "hosts": [],
        }
        cases = {
            "unknown-field": dict(valid, path="/tmp/escape"),
            "unknown-component": dict(valid, components=["skill:not-in-catalog"]),
            "bad-commit": dict(valid, commit="0" * 40),
            "path-profile": dict(valid, profiles=["../core"]),
        }
        for name, document in cases.items():
            with self.subTest(name=name):
                manifest = self.base / f"{name}.json"
                manifest.write_text(json.dumps(document), encoding="utf-8")
                target = self.base / f"target-{name}"
                result = run(
                    CLI,
                    "restore",
                    str(manifest),
                    env={"AGENTS_HOME": str(target), "HOME": str(self.user)},
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(target.exists())

        duplicate = self.base / "duplicate.json"
        duplicate.write_text(
            '{"schema_version":1,"schema_version":1,"ecosystem_version":"0.4.0",'
            f'"commit":"{commit}","profiles":[],"components":[],"hosts":[]}}',
            encoding="utf-8",
        )
        result = run(CLI, "restore", str(duplicate), env=self.env, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.home.exists())

        oversized = self.base / "oversized.json"
        oversized.write_bytes(b" " * (1024 * 1024 + 1))
        result = run(CLI, "restore", str(oversized), env=self.env, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.home.exists())

        linked = self.base / "linked.json"
        linked.symlink_to(duplicate)
        result = run(CLI, "restore", str(linked), env=self.env, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.home.exists())

    def test_host_conflicts_fail_preflight_without_partial_writes(self):
        run(CLI, "setup", "--profile", "core", "--no-root-files", env=self.env)
        skills = sorted(path.name for path in (self.home / "skills").iterdir() if (path / "SKILL.md").is_file())
        for index in (0, len(skills) // 2, len(skills) - 1):
            with self.subTest(conflict=skills[index]):
                user = self.base / f"conflict-user-{index}"
                conflict = user / ".codex" / "skills" / skills[index]
                conflict.mkdir(parents=True)
                marker = conflict / "personal.txt"
                marker.write_text("keep\n", encoding="utf-8")
                result = run(
                    ROOT / "scripts" / "connect.sh",
                    "--host",
                    "codex",
                    env={"AGENTS_HOME": str(self.home), "HOME": str(user)},
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")
                linked = user / ".codex" / "skills"
                self.assertEqual([path.name for path in linked.iterdir()], [skills[index]])
                self.assertFalse((self.home / ".ecosystem-hosts").exists())

    def test_repeated_host_connect_accepts_managed_symlinks(self):
        run(CLI, "setup", "--profile", "core", "--host", "codex", env=self.env)
        result = run(ROOT / "scripts" / "connect.sh", "--host", "codex", env=self.env, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_status_and_doctor_detect_managed_root_drift(self):
        run(CLI, "setup", "--profile", "core", "--host", "generic", env=self.env)
        with (self.home / "AGENTS.md").open("a", encoding="utf-8") as handle:
            handle.write("\nlocal change\n")
        status = run(CLI, "status", env=self.env, check=False)
        self.assertNotEqual(status.returncode, 0)
        self.assertIn("locally-modified root:AGENTS.md", status.stdout)
        doctor = run(CLI, "doctor", env=self.env, check=False)
        self.assertNotEqual(doctor.returncode, 0)

    def test_symlinked_host_parent_is_rejected_without_touching_target(self):
        run(CLI, "setup", "--profile", "core", "--no-root-files", env=self.env)
        outside = self.base / "outside"
        outside.mkdir()
        codex = self.user / ".codex"
        codex.mkdir(parents=True)
        (codex / "skills").symlink_to(outside)
        result = run(
            ROOT / "scripts" / "connect.sh",
            "--host",
            "codex",
            env=self.env,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.home / ".ecosystem-hosts").exists())

    def test_status_classifies_component_and_host_drift(self):
        repo = self.base / "repo"
        source = repo / "library" / "skills" / "sample"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("version one\n", encoding="utf-8")
        (repo / "profiles").mkdir()
        (repo / "profiles" / "sample.profile").write_text("skill:sample\n", encoding="utf-8")
        (repo / "catalog").mkdir()
        (repo / "catalog" / "catalog.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "ecosystem_version": "1.0.0",
                    "components": [
                        {"id": "skill:sample", "type": "skill", "name": "sample", "path": "library/skills/sample"}
                    ],
                }
            ),
            encoding="utf-8",
        )
        installed = self.home / "skills" / "sample"
        installed.mkdir(parents=True)
        (installed / "SKILL.md").write_text("version one\n", encoding="utf-8")
        state = self.home / ".ecosystem-state.json"
        run(
            ENVIRONMENT,
            "record",
            "--state",
            state,
            "--id",
            "skill:sample",
            "--source",
            source,
            "--installed",
            installed,
        )
        (self.home / ".ecosystem-installed").write_text("skill:sample\n", encoding="utf-8")
        (self.home / ".ecosystem-hosts").write_text("codex\n", encoding="utf-8")
        host_skill = self.user / ".codex" / "skills" / "sample"
        host_skill.mkdir(parents=True)
        (host_skill / "SKILL.md").write_text("unmanaged\n", encoding="utf-8")

        current = run(
            ENVIRONMENT,
            "status",
            "--repo",
            repo,
            "--home",
            self.home,
            "--user-home",
            self.user,
            check=False,
        )
        self.assertNotEqual(current.returncode, 0)
        self.assertIn("current        skill:sample", current.stdout)
        self.assertIn("host-conflicting host:codex:skill:sample", current.stdout)

        (source / "SKILL.md").write_text("version two\n", encoding="utf-8")
        stale = run(
            ENVIRONMENT,
            "status",
            "--repo",
            repo,
            "--home",
            self.home,
            "--user-home",
            self.user,
            check=False,
        )
        self.assertIn("managed-stale  skill:sample", stale.stdout)

        (installed / "SKILL.md").write_text("local change\n", encoding="utf-8")
        modified = run(
            ENVIRONMENT,
            "status",
            "--repo",
            repo,
            "--home",
            self.home,
            "--user-home",
            self.user,
            check=False,
        )
        self.assertIn("locally-modified skill:sample", modified.stdout)

        for child in installed.iterdir():
            child.unlink()
        installed.rmdir()
        missing = run(
            ENVIRONMENT,
            "status",
            "--repo",
            repo,
            "--home",
            self.home,
            "--user-home",
            self.user,
            check=False,
        )
        self.assertIn("missing        skill:sample", missing.stdout)

    def test_restore_provenance_accepts_detached_head_with_local_origin_head(self):
        origin = self.base / "origin.git"
        checkout = self.base / "checkout"
        run("git", "init", "--bare", origin)
        run("git", "clone", origin, checkout)
        run("git", "-C", checkout, "config", "user.email", "test@example.invalid")
        run("git", "-C", checkout, "config", "user.name", "Portability Test")
        (checkout / "catalog").mkdir()
        (checkout / "profiles").mkdir()
        (checkout / "catalog" / "catalog.json").write_text(
            json.dumps({"schema_version": 2, "ecosystem_version": "1.0.0", "components": []}),
            encoding="utf-8",
        )
        run("git", "-C", checkout, "add", ".")
        run("git", "-C", checkout, "commit", "-m", "fixture")
        run("git", "-C", checkout, "branch", "-M", "main")
        run("git", "-C", checkout, "push", "-u", "origin", "main")
        run("git", "-C", origin, "symbolic-ref", "HEAD", "refs/heads/main")
        run("git", "-C", checkout, "remote", "set-head", "origin", "-a")
        commit = run("git", "-C", checkout, "rev-parse", "HEAD").stdout.strip()
        run("git", "-C", checkout, "checkout", "--detach", commit)
        manifest = self.base / "detached.json"
        manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "ecosystem_version": "1.0.0",
                    "commit": commit,
                    "profiles": [],
                    "components": [],
                    "hosts": [],
                }
            ),
            encoding="utf-8",
        )
        result = run(
            ENVIRONMENT,
            "restore-plan",
            "--repo",
            checkout,
            "--manifest",
            manifest,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        in_checkout = checkout / "agents.lock.json"
        in_checkout.write_text(manifest.read_text(encoding="utf-8"), encoding="utf-8")
        allowed = run(
            ENVIRONMENT,
            "restore-plan",
            "--repo",
            checkout,
            "--manifest",
            in_checkout,
            check=False,
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)

        (checkout / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        dirty = run(
            ENVIRONMENT,
            "restore-plan",
            "--repo",
            checkout,
            "--manifest",
            manifest,
            check=False,
        )
        self.assertNotEqual(dirty.returncode, 0)
        self.assertIn("clean reviewed checkout", dirty.stderr)


if __name__ == "__main__":
    unittest.main()
