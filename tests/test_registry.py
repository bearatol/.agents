#!/usr/bin/env python3
"""Regression tests for the read-only activation registry and planner."""

import contextlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
# Neither this process nor the commands it starts may leave bytecode caches
# in the source tree; installers copy component directories verbatim.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.path.insert(0, str(ROOT / "scripts"))
import registry  # noqa: E402
from state import digest_path, save_state  # noqa: E402


def canonical_catalog():
    return json.loads((ROOT / "catalog" / "catalog.json").read_text(encoding="utf-8"))


def first_skill():
    for component in canonical_catalog()["components"]:
        if isinstance(component, dict) and str(component.get("id", "")).startswith("skill:"):
            return component["id"].split(":", 1)[1], ROOT / component["path"]
    raise AssertionError("the canonical catalog declares no skill")


def tree_digest(root):
    root = pathlib.Path(root)
    records = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            records.append(f"{relative}\0link\0{os.readlink(path)}")
        elif path.is_file():
            records.append(f"{relative}\0file\0{digest_path(path)}")
        else:
            records.append(f"{relative}\0dir")
    return "\n".join(records)


def run(home, *arguments, user_home=None):
    """Run one registry command in-process and capture its output."""
    stream = io.StringIO()
    argv = ["--repo", str(ROOT), "--home", str(home), "--user-home", str(user_home or home), *arguments]
    with contextlib.redirect_stdout(stream):
        code = registry.main(argv)
    return code, stream.getvalue()


def entries_by_id(home, **kwargs):
    code, output = run(home, "report", "--json", **kwargs)
    assert code == 0, output
    document = json.loads(output)
    return {entry["id"]: entry for entry in document["entries"]}, document["warnings"]


def actions_by_id(home, **kwargs):
    code, output = run(home, "plan", "--json", **kwargs)
    assert code == 0, output
    return {action["id"]: action for action in json.loads(output)["actions"]}


class RegistryFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self.temporary.name) / "agents"
        (self.home / "skills").mkdir(parents=True)
        self.skill_name, self.skill_source = first_skill()
        self.skill_path = self.home / "skills" / self.skill_name
        shutil.copytree(self.skill_source, self.skill_path)
        self.addCleanup(self.temporary.cleanup)

    def write_lock(self, skills):
        (self.home / ".skill-lock.json").write_text(
            json.dumps({"version": 3, "skills": skills}), encoding="utf-8"
        )

    def add_unmanaged_skill(self, name, text="# unmanaged\n"):
        path = self.home / "skills" / name
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(text, encoding="utf-8")
        return path

    def modify_installed_skill(self):
        (self.skill_path / "SKILL.md").write_text("# changed by someone else\n", encoding="utf-8")

    def record_installed_state(self):
        save_state(
            self.home / ".ecosystem-state.json",
            {
                "schema_version": 1,
                "components": {
                    f"skill:{self.skill_name}": {
                        "source_hash": digest_path(self.skill_source),
                        "installed_hash": digest_path(self.skill_path),
                    }
                },
            },
        )


class OwnershipTests(RegistryFixture):
    def test_catalog_skill_is_managed_and_current(self):
        entries, _ = entries_by_id(self.home)
        entry = entries[f"skill:{self.skill_name}"]
        self.assertEqual(entry["owner"], "catalog")
        self.assertEqual(entry["trust"], "managed")
        self.assertEqual(entry["state"], "current")
        self.assertEqual(entry["collisions"], [])

    def test_unrecorded_skill_is_unknown_and_unreviewed(self):
        self.add_unmanaged_skill("private-method")
        entries, _ = entries_by_id(self.home)
        entry = entries["skill:private-method"]
        self.assertEqual(entry["owner"], "unknown")
        self.assertEqual(entry["trust"], "unreviewed")
        self.assertEqual(entry["state"], "present")

    def test_third_party_record_attributes_its_own_skill(self):
        self.add_unmanaged_skill("frontend-design")
        self.write_lock({"frontend-design": {"source": "anthropics/skills"}})
        entries, _ = entries_by_id(self.home)
        entry = entries["skill:frontend-design"]
        self.assertEqual(entry["owner"], "foreign")
        self.assertEqual(entry["trust"], "declared")
        self.assertEqual(entry["provenance"]["record"], ".skill-lock.json")
        self.assertEqual(entry["provenance"]["reference"], "anthropics/skills")

    def test_two_records_claiming_one_path_report_a_collision(self):
        self.write_lock({self.skill_name: {"source": "someone/skills"}})
        entries, _ = entries_by_id(self.home)
        entry = entries[f"skill:{self.skill_name}"]
        self.assertEqual(entry["owner"], "catalog")
        self.assertEqual([item["owner"] for item in entry["collisions"]], ["foreign"])

    def test_link_leaving_the_runtime_is_reported_and_not_hashed(self):
        outside = pathlib.Path(self.temporary.name) / "elsewhere"
        (outside / "SKILL.md").parent.mkdir(parents=True, exist_ok=True)
        (outside / "SKILL.md").write_text("# elsewhere\n", encoding="utf-8")
        os.symlink(outside, self.home / "skills" / "linked-skill")
        entries, _ = entries_by_id(self.home)
        entry = entries["skill:linked-skill"]
        self.assertTrue(entry["escapes_home"])
        self.assertIsNone(entry["hash"])
        self.assertEqual(entry["link"], str(outside))


class PlanTests(RegistryFixture):
    def test_current_component_is_skipped(self):
        self.assertEqual(actions_by_id(self.home)[f"skill:{self.skill_name}"]["action"], "skip")

    def test_missing_component_is_created(self):
        shutil.rmtree(self.skill_path)
        self.assertEqual(actions_by_id(self.home)[f"skill:{self.skill_name}"]["action"], "create")

    def test_component_this_project_installed_is_updated(self):
        self.modify_installed_skill()
        self.record_installed_state()
        self.assertEqual(actions_by_id(self.home)[f"skill:{self.skill_name}"]["action"], "update")

    def test_component_changed_by_someone_else_is_a_conflict(self):
        self.modify_installed_skill()
        self.assertEqual(actions_by_id(self.home)[f"skill:{self.skill_name}"]["action"], "conflict")

    def test_paths_this_project_does_not_own_are_kept(self):
        self.add_unmanaged_skill("private-method")
        self.assertEqual(actions_by_id(self.home)["skill:private-method"]["action"], "keep")

    def test_plan_never_declares_a_write(self):
        code, output = run(self.home, "plan", "--json")
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(output)["writes"])


class ReconcileTests(RegistryFixture):
    def test_clean_runtime_reports_no_decision(self):
        code, output = run(self.home, "reconcile", "--json", "--fail-on-conflict")
        self.assertEqual(code, 0)
        document = json.loads(output)
        self.assertFalse([item for item in document["divergences"] if item["action"] == "conflict"])

    def test_conflict_can_fail_the_command_on_request(self):
        self.modify_installed_skill()
        code, _ = run(self.home, "reconcile", "--json", "--fail-on-conflict")
        self.assertEqual(code, 1)

    def test_conflict_alone_does_not_fail_the_command(self):
        self.modify_installed_skill()
        code, _ = run(self.home, "reconcile", "--json")
        self.assertEqual(code, 0)

    def test_matching_content_claimed_twice_is_an_overlap_not_a_conflict(self):
        self.write_lock({self.skill_name: {"source": "someone/skills"}})
        code, output = run(self.home, "reconcile", "--json", "--fail-on-conflict")
        self.assertEqual(code, 0)
        document = json.loads(output)
        self.assertIn(f"skills/{self.skill_name}", [item["path"] for item in document["overlaps"]])


class UntrustedInputTests(RegistryFixture):
    def test_invalid_third_party_record_warns_and_keeps_working(self):
        (self.home / ".skill-lock.json").write_text("{not json", encoding="utf-8")
        entries, warnings = entries_by_id(self.home)
        self.assertIn(f"skill:{self.skill_name}", entries)
        self.assertTrue(any(".skill-lock.json" in warning for warning in warnings))

    def test_third_party_record_without_skills_warns(self):
        (self.home / ".skill-lock.json").write_text('{"version": 3}', encoding="utf-8")
        _, warnings = entries_by_id(self.home)
        self.assertTrue(any("no readable" in warning or "holds no readable" in warning for warning in warnings))

    def test_traversing_name_in_a_third_party_record_is_ignored(self):
        self.write_lock({"../escape": {"source": "someone/skills"}, "nested/name": {}})
        entries, _ = entries_by_id(self.home)
        self.assertFalse([key for key in entries if "escape" in key or "nested" in key])

    def test_generated_index_files_are_not_attributed(self):
        (self.home / "skills" / "INDEX.md").write_text("# index\n", encoding="utf-8")
        entries, warnings = entries_by_id(self.home)
        self.assertNotIn("skill:INDEX", entries)
        self.assertTrue(any("generated index" in warning for warning in warnings))


class ReadOnlyTests(RegistryFixture):
    def test_no_command_changes_the_runtime_or_the_repository(self):
        self.add_unmanaged_skill("private-method")
        self.write_lock({self.skill_name: {"source": "someone/skills"}})
        self.modify_installed_skill()
        before_home = tree_digest(self.home)
        before_repo = digest_path(ROOT / "catalog")
        for arguments in (["report"], ["plan"], ["reconcile"], ["report", "--json"], ["reconcile", "--json"]):
            run(self.home, *arguments)
        self.assertEqual(tree_digest(self.home), before_home)
        self.assertEqual(digest_path(ROOT / "catalog"), before_repo)

    def test_command_line_entry_point_also_writes_nothing(self):
        before = tree_digest(self.home)
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "registry.py"),
                "--repo", str(ROOT),
                "--home", str(self.home),
                "--user-home", str(self.home),
                "report",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tree_digest(self.home), before)


if __name__ == "__main__":
    unittest.main()
