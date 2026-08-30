#!/usr/bin/env python3

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "workspace.py"


def run(*args, check=True):
    return subprocess.run(
        [sys.executable, str(CLI), *map(str, args)],
        text=True,
        capture_output=True,
        check=check,
    )


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="agents-workspace-")
        self.repo = pathlib.Path(self.temporary.name)
        run("--repo", self.repo, "library", "init")

    def tearDown(self):
        self.temporary.cleanup()

    def command(self, *args, check=True):
        return run("--repo", self.repo, *args, check=check)

    def make_skill(self, name="source"):
        source = self.repo.parent / f"{self.repo.name}-{name}"
        source.mkdir()
        (source / "SKILL.md").write_text("# Safe skill\n", encoding="utf-8")
        self.addCleanup(lambda: __import__("shutil").rmtree(source, ignore_errors=True))
        return source

    def test_add_list_trust_and_detect_modification(self):
        source = self.make_skill()
        self.command("library", "add", "skill", "my-skill", source)
        listing = json.loads(self.command("library", "list", "--json").stdout)
        self.assertEqual(listing[0]["status"], "inactive")
        self.command("library", "trust", "skill", "my-skill")
        listing = json.loads(self.command("library", "list", "--json").stdout)
        self.assertEqual(listing[0]["status"], "trusted")
        self.command("library", "check")
        installed = self.repo.parent / f"{self.repo.name}-home"
        self.addCleanup(lambda: __import__("shutil").rmtree(installed, ignore_errors=True))
        run("--repo", self.repo, "--home", installed, "library", "activate", "skill", "my-skill")
        self.assertTrue((installed / "skills/my-skill/SKILL.md").is_file())
        duplicate = run(
            "--repo", self.repo, "--home", installed, "library", "activate", "skill", "my-skill",
            check=False,
        )
        self.assertNotEqual(duplicate.returncode, 0)
        item = self.repo / "workspace/library/skill/my-skill/SKILL.md"
        item.write_text("changed\n", encoding="utf-8")
        self.assertNotEqual(self.command("library", "check", check=False).returncode, 0)

    def test_unknown_type_is_stored_but_duplicate_and_traversal_fail(self):
        source = self.make_skill("future")
        self.command("library", "add", "future-format", "example", source)
        self.assertTrue((self.repo / "workspace/library/future-format/example/SKILL.md").is_file())
        self.assertNotEqual(self.command("library", "add", "future-format", "example", source, check=False).returncode, 0)
        self.assertNotEqual(self.command("library", "add", "../bad", "example", source, check=False).returncode, 0)

    def test_concurrent_add_has_one_winner_and_no_partial_item(self):
        source = self.make_skill("concurrent")
        command = [
            sys.executable, str(CLI), "--repo", str(self.repo), "library", "add",
            "skill", "shared", str(source),
        ]
        first = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        second = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        first.communicate()
        second.communicate()
        self.assertEqual(sorted([first.returncode, second.returncode]), [0, 1])
        self.assertTrue((self.repo / "workspace/library/skill/shared/SKILL.md").is_file())
        self.command("library", "check")

    def test_secret_weight_and_symlink_imports_fail(self):
        secret = self.repo.parent / f"{self.repo.name}-secret"
        secret.mkdir()
        (secret / ".env").write_text("PASSWORD=value\n", encoding="utf-8")
        self.addCleanup(lambda: __import__("shutil").rmtree(secret, ignore_errors=True))
        self.assertNotEqual(self.command("library", "add", "prompt", "secret", secret, check=False).returncode, 0)

        weight = self.repo.parent / f"{self.repo.name}-weight.gguf"
        weight.write_bytes(b"weight")
        self.addCleanup(lambda: weight.unlink(missing_ok=True))
        self.assertNotEqual(self.command("library", "add", "model", "weight", weight, check=False).returncode, 0)

        linked = self.repo.parent / f"{self.repo.name}-linked"
        linked.mkdir()
        os.symlink(weight, linked / "file")
        self.addCleanup(lambda: __import__("shutil").rmtree(linked, ignore_errors=True))
        self.assertNotEqual(self.command("library", "add", "prompt", "linked", linked, check=False).returncode, 0)

    def test_multi_host_task_result_review_and_decision(self):
        self.command(
            "team", "init", "release", "--objective", "Ship safely",
            "--coordinator", "codex", "--member", "claude", "--member", "gemini", "--member", "kimi",
        )
        self.command(
            "team", "task", "release", "implementation", "--title", "Implement feature",
            "--objective", "Produce a tested change", "--role", "engineer", "--worker", "claude",
            "--reviewer", "gemini", "--reviewer", "kimi", "--scope", "scripts",
            "--accept", "Tests pass",
        )
        self.command(
            "team", "result", "release", "implementation", "--worker", "claude",
            "--status", "complete", "--summary", "Implemented", "--evidence", "Tests pass",
        )
        duplicate = self.command(
            "team", "result", "release", "implementation", "--worker", "claude",
            "--status", "complete", "--summary", "Overwrite", check=False,
        )
        self.assertNotEqual(duplicate.returncode, 0)
        for reviewer in ("gemini", "kimi"):
            self.command(
                "team", "review", "release", "implementation", "--reviewer", reviewer,
                "--verdict", "approve", "--summary", "Verified",
            )
        self.command(
            "team", "decide", "release", "implementation", "--coordinator", "codex",
            "--decision", "accept", "--summary", "Accepted after peer review",
        )
        status = self.command("team", "status", "release").stdout
        self.assertIn("decided", status)
        self.assertIn("2/2 reviews", status)

    def test_stale_results_and_self_review_fail(self):
        self.command(
            "team", "init", "audit", "--objective", "Audit",
            "--coordinator", "codex", "--member", "claude",
        )
        bad = self.command(
            "team", "task", "audit", "check", "--title", "Check", "--objective", "Check",
            "--role", "reviewer", "--worker", "claude", "--reviewer", "claude",
            "--scope", "docs", "--accept", "Reviewed", check=False,
        )
        self.assertNotEqual(bad.returncode, 0)
        for attempt in (1, 2):
            self.command(
                "team", "task", "audit", "check", "--attempt", str(attempt), "--title", "Check",
                "--objective", "Check", "--role", "reviewer", "--worker", "claude",
                "--reviewer", "codex", "--scope", "docs", "--accept", "Reviewed",
            )
        stale = self.command(
            "team", "result", "audit", "check", "--attempt", "1", "--worker", "claude",
            "--status", "complete", "--summary", "Old", check=False,
        )
        self.assertNotEqual(stale.returncode, 0)
        secret = self.command(
            "team", "result", "audit", "check", "--attempt", "2", "--worker", "claude",
            "--status", "complete", "--summary", "sk-" + ("a" * 26), check=False,
        )
        self.assertNotEqual(secret.returncode, 0)


if __name__ == "__main__":
    unittest.main()
