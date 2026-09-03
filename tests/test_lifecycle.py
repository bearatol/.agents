#!/usr/bin/env python3
"""Regression tests for ownership-driven removal and deactivation."""

import contextlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
# Neither this process nor the commands it starts may leave bytecode caches
# in the source tree; installers copy component directories verbatim.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, str(ROOT / "scripts"))
import lifecycle  # noqa: E402
import registry  # noqa: E402


def canonical_catalog():
    return json.loads((ROOT / "catalog" / "catalog.json").read_text(encoding="utf-8"))


def first_skill():
    for component in canonical_catalog()["components"]:
        if isinstance(component, dict) and str(component.get("id", "")).startswith("skill:"):
            return component["id"].split(":", 1)[1], ROOT / component["path"]
    raise AssertionError("the canonical catalog declares no skill")


class LifecycleFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self.temporary.name) / "agents"
        (self.home / "skills").mkdir(parents=True)
        self.skill_name, self.skill_source = first_skill()
        self.skill_path = self.home / "skills" / self.skill_name
        shutil.copytree(self.skill_source, self.skill_path)
        (self.home / ".ecosystem-installed").write_text(
            f"skill:{self.skill_name}\n", encoding="utf-8"
        )
        self.addCleanup(self.temporary.cleanup)

    def run_command(self, *arguments):
        stream = io.StringIO()
        errors = io.StringIO()
        argv = [
            "--repo", str(ROOT),
            "--home", str(self.home),
            "--user-home", str(self.home),
            *arguments,
        ]
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(errors):
            code = lifecycle.main(argv)
        return code, stream.getvalue() + errors.getvalue()

    def add_foreign_skill(self, name):
        path = self.home / "skills" / name
        path.mkdir(parents=True, exist_ok=True)
        (path / "SKILL.md").write_text("# foreign\n", encoding="utf-8")
        (self.home / ".skill-lock.json").write_text(
            json.dumps({"version": 3, "skills": {name: {"source": "someone/skills"}}}),
            encoding="utf-8",
        )
        return path

    def registry_state(self, component_id):
        entries, _ = registry.build_entries(ROOT, self.home, self.home)
        for entry in entries:
            if entry["id"] == component_id:
                return entry
        return None


class RemoveTests(LifecycleFixture):
    def test_removes_a_component_this_project_owns(self):
        code, output = self.run_command("remove", f"skill:{self.skill_name}")
        self.assertEqual(code, 0, output)
        self.assertFalse(self.skill_path.exists())
        self.assertNotIn(self.skill_name, (self.home / ".ecosystem-installed").read_text(encoding="utf-8"))

    def test_refuses_a_component_owned_by_another_tool(self):
        self.add_foreign_skill("frontend-design")
        code, output = self.run_command("remove", "frontend-design")
        self.assertEqual(code, 1)
        self.assertIn("owned by foreign", output)
        self.assertTrue((self.home / "skills" / "frontend-design").is_dir())

    def test_refuses_a_component_claimed_twice(self):
        (self.home / ".skill-lock.json").write_text(
            json.dumps({"version": 3, "skills": {self.skill_name: {"source": "someone/skills"}}}),
            encoding="utf-8",
        )
        code, output = self.run_command("remove", f"skill:{self.skill_name}")
        self.assertEqual(code, 1)
        self.assertIn("also claimed by", output)
        self.assertTrue(self.skill_path.is_dir())

    def test_refuses_a_link_that_leaves_the_runtime(self):
        outside = pathlib.Path(self.temporary.name) / "elsewhere"
        outside.mkdir()
        (outside / "SKILL.md").write_text("# elsewhere\n", encoding="utf-8")
        os.symlink(outside, self.home / "skills" / "linked-skill")
        code, output = self.run_command("remove", "linked-skill")
        self.assertEqual(code, 1)
        self.assertTrue((self.home / "skills" / "linked-skill").is_symlink())

    def test_dry_run_changes_nothing(self):
        code, output = self.run_command("remove", f"skill:{self.skill_name}", "--dry-run")
        self.assertEqual(code, 0, output)
        self.assertIn("would-remove", output)
        self.assertTrue(self.skill_path.is_dir())

    def test_unknown_name_is_an_error(self):
        code, output = self.run_command("remove", "no-such-skill")
        self.assertEqual(code, 1)
        self.assertIn("no activated component matches", output)


class DisableTests(LifecycleFixture):
    def test_disable_moves_the_component_aside_and_records_it(self):
        code, output = self.run_command("disable", f"skill:{self.skill_name}")
        self.assertEqual(code, 0, output)
        self.assertFalse(self.skill_path.exists())
        self.assertTrue((self.home / registry.DISABLED_DIRECTORY / "skills" / self.skill_name).is_dir())
        record = json.loads((self.home / registry.DISABLED_RECORD).read_text(encoding="utf-8"))
        self.assertIn(f"skill:{self.skill_name}", record["entries"])

    def test_disabled_component_is_reported_as_disabled_not_missing(self):
        self.run_command("disable", f"skill:{self.skill_name}")
        entry = self.registry_state(f"skill:{self.skill_name}")
        self.assertIsNotNone(entry)
        self.assertEqual(entry["state"], "disabled")

    def test_an_install_would_not_recreate_a_disabled_component(self):
        self.run_command("disable", f"skill:{self.skill_name}")
        entry = self.registry_state(f"skill:{self.skill_name}")
        action, _ = registry.plan_action(entry)
        self.assertEqual(action, "keep")

    def test_a_component_owned_by_another_tool_can_be_disabled(self):
        self.add_foreign_skill("frontend-design")
        code, output = self.run_command("disable", "frontend-design")
        self.assertEqual(code, 0, output)
        self.assertFalse((self.home / "skills" / "frontend-design").exists())
        self.assertIn("may reinstall it", output)

    def test_enable_puts_it_back_and_clears_the_record(self):
        self.run_command("disable", f"skill:{self.skill_name}")
        code, output = self.run_command("enable", f"skill:{self.skill_name}")
        self.assertEqual(code, 0, output)
        self.assertTrue(self.skill_path.is_dir())
        record = json.loads((self.home / registry.DISABLED_RECORD).read_text(encoding="utf-8"))
        self.assertEqual(record["entries"], {})

    def test_enable_refuses_when_something_took_the_path(self):
        self.run_command("disable", f"skill:{self.skill_name}")
        self.skill_path.mkdir(parents=True)
        (self.skill_path / "SKILL.md").write_text("# someone else\n", encoding="utf-8")
        code, output = self.run_command("enable", f"skill:{self.skill_name}")
        self.assertEqual(code, 1)
        self.assertIn("already occupies", output)

    def test_a_link_pointing_outside_can_still_be_switched_off(self):
        outside = pathlib.Path(self.temporary.name) / "elsewhere"
        outside.mkdir()
        (outside / "SKILL.md").write_text("# elsewhere\n", encoding="utf-8")
        link = self.home / "skills" / "linked-skill"
        os.symlink(outside, link)
        code, output = self.run_command("disable", "linked-skill")
        self.assertEqual(code, 0, output)
        self.assertFalse(link.is_symlink())
        self.assertTrue((self.home / registry.DISABLED_DIRECTORY / "skills" / "linked-skill").is_symlink())
        self.assertTrue((outside / "SKILL.md").is_file())

    def test_disabling_twice_is_an_error(self):
        self.run_command("disable", f"skill:{self.skill_name}")
        code, output = self.run_command("disable", f"skill:{self.skill_name}")
        self.assertEqual(code, 1)
        self.assertIn("already disabled", output)

    def test_dry_run_changes_nothing(self):
        code, output = self.run_command("disable", f"skill:{self.skill_name}", "--dry-run")
        self.assertEqual(code, 0, output)
        self.assertIn("would-disable", output)
        self.assertTrue(self.skill_path.is_dir())
        self.assertFalse((self.home / registry.DISABLED_RECORD).exists())


class HostLinkTests(LifecycleFixture):
    def connect_codex(self):
        (self.home / ".ecosystem-hosts").write_text("codex\n", encoding="utf-8")
        target_root = self.home / ".codex" / "skills"
        target_root.mkdir(parents=True)
        link = target_root / self.skill_name
        os.symlink(self.skill_path, link)
        return link

    def test_disable_takes_the_published_link_down(self):
        link = self.connect_codex()
        code, output = self.run_command("disable", f"skill:{self.skill_name}")
        self.assertEqual(code, 0, output)
        self.assertFalse(link.is_symlink())

    def test_remove_takes_the_published_link_down(self):
        link = self.connect_codex()
        code, output = self.run_command("remove", f"skill:{self.skill_name}")
        self.assertEqual(code, 0, output)
        self.assertFalse(link.is_symlink())


if __name__ == "__main__":
    unittest.main()
