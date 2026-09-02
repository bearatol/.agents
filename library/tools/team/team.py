#!/usr/bin/env python3

import argparse
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone


ID_RE = re.compile(r"^[a-z]+:[a-z0-9-]+$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
CATALOG_SCHEMA_REFERENCE = "./catalog.schema.json"
CATALOG_FIELDS = {"$schema", "schema_version", "ecosystem_version", "language", "license", "components"}
COMPONENT_FIELDS = {
    "id", "type", "name", "description", "profile", "origin", "license", "path", "tags",
    "capabilities", "access", "skill_policy", "recommended_skills", "delegates",
}
COMPONENT_TYPES = {"skill", "agent", "rule", "model", "orchestration", "tool"}
ORIGINS = {"original", "referenced", "vendored"}
ACCESS_LEVELS = {"read-only", "workspace-write"}
SKILL_POLICIES = {"self-select", "self-select-restricted"}


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def catalog_path(home):
    candidates = [home / "catalog.json", home / "catalog" / "catalog.json"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    fail(f"catalog not found under {home}")


def load_catalog(home):
    path = catalog_path(home)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read catalog: {exc}")
    return data, path


def load_canonical_catalog(repo_root):
    path = pathlib.Path(repo_root).resolve() / "catalog" / "catalog.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read catalog: {exc}")
    return data, path


def component_map(catalog):
    return {item["id"]: item for item in catalog.get("components", [])}


def csv_values(values):
    result = []
    for value in values or []:
        result.extend(part.strip() for part in value.split(",") if part.strip())
    return list(dict.fromkeys(result))


def write_json(data, output):
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if output:
        pathlib.Path(output).write_text(text, encoding="utf-8")
        print(output)
    else:
        print(text, end="")


def string_list(value, *, minimum=0):
    return (
        isinstance(value, list)
        and len(value) >= minimum
        and all(isinstance(item, str) for item in value)
    )


def validate_catalog(catalog, root=None):
    errors = []
    if not isinstance(catalog, dict):
        return ["catalog must be an object"]
    unknown_fields = set(catalog) - CATALOG_FIELDS
    if unknown_fields:
        errors.append("catalog has unexpected fields: " + ", ".join(sorted(unknown_fields)))
    for field in ("schema_version", "ecosystem_version", "language", "license", "components"):
        if field not in catalog:
            errors.append(f"catalog missing {field}")
    if catalog.get("$schema") != CATALOG_SCHEMA_REFERENCE:
        errors.append(f"$schema must be {CATALOG_SCHEMA_REFERENCE}")
    if type(catalog.get("schema_version")) is not int or catalog.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    if not isinstance(catalog.get("ecosystem_version"), str) or not VERSION_RE.fullmatch(catalog["ecosystem_version"]):
        errors.append("ecosystem_version must be a semantic version")
    if catalog.get("language") != "en":
        errors.append("language must be en")
    if not isinstance(catalog.get("license"), str):
        errors.append("license must be a string")
    components = catalog.get("components")
    if not isinstance(components, list) or not components:
        errors.append("components must be a non-empty array")
        components = []
    seen = set()
    component_by_id = {}
    root_path = pathlib.Path(root).resolve() if root else None
    for index, item in enumerate(components):
        label = f"component[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        unknown_fields = set(item) - COMPONENT_FIELDS
        if unknown_fields:
            errors.append(f"{label} has unexpected fields: " + ", ".join(sorted(unknown_fields)))
        for field in ("id", "type", "name", "profile", "origin", "license", "path", "tags"):
            if field not in item:
                errors.append(f"{label} missing {field}")
        component_id = item.get("id")
        if not isinstance(component_id, str) or not ID_RE.fullmatch(component_id):
            errors.append(f"{label} has an invalid id")
            component_id = None
        if component_id in seen:
            errors.append(f"duplicate component id: {component_id}")
        if component_id:
            seen.add(component_id)
            component_by_id[component_id] = item
        component_type = item.get("type")
        if not isinstance(component_type, str) or component_type not in COMPONENT_TYPES:
            errors.append(f"{label} has an invalid type")
        name = item.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            errors.append(f"{label} has an invalid name")
        if component_id and isinstance(component_type, str) and isinstance(name, str):
            if component_id != f"{component_type}:{name}":
                errors.append(f"{label} id must match type and name")
        if not string_list(item.get("profile"), minimum=1):
            errors.append(f"{label} profile must be a non-empty string array")
        origin = item.get("origin")
        if not isinstance(origin, str) or origin not in ORIGINS:
            errors.append(f"{label} has an invalid origin")
        if not isinstance(item.get("license"), str):
            errors.append(f"{label} license must be a string")
        path = item.get("path")
        if not isinstance(path, str) or not path:
            errors.append(f"{label} path must be a non-empty string")
        if not string_list(item.get("tags"), minimum=1):
            errors.append(f"{label} tags must be a non-empty string array")
        for field in ("description", "license", "path"):
            if field in item and not isinstance(item[field], str):
                errors.append(f"{label} {field} must be a string")
        for field in ("capabilities", "recommended_skills"):
            if field in item and not string_list(item[field]):
                errors.append(f"{label} {field} must be a string array")
        if "access" in item:
            access = item["access"]
            if not isinstance(access, str) or access not in ACCESS_LEVELS:
                errors.append(f"{label} has an invalid access level")
        if "skill_policy" in item:
            skill_policy = item["skill_policy"]
            if not isinstance(skill_policy, str) or skill_policy not in SKILL_POLICIES:
                errors.append(f"{label} has an invalid skill policy")
        if "delegates" in item and type(item["delegates"]) is not bool:
            errors.append(f"{label} delegates must be a boolean")
        if component_type == "agent":
            for field in ("description", "capabilities", "access", "skill_policy", "recommended_skills", "delegates"):
                if field not in item:
                    errors.append(f"{label} missing {field}")
        if root_path and isinstance(path, str) and path:
            source = (root_path / path).resolve()
            try:
                source.relative_to(root_path)
            except ValueError:
                errors.append(f"{label} path escapes repository root")
            else:
                if not source.exists():
                    errors.append(f"{label} path does not exist: {source}")
    for item in components:
        if not isinstance(item, dict):
            continue
        component_id = item.get("id", "component")
        skills = item.get("recommended_skills", [])
        if not isinstance(skills, list):
            continue
        for skill in skills:
            target = component_by_id.get(skill)
            if target is None:
                errors.append(f"{component_id} recommends missing {skill}")
            elif target.get("type") != "skill":
                errors.append(f"{component_id} recommends non-skill {skill}")
    return errors


def cmd_validate_catalog(args, catalog):
    root = pathlib.Path(args.repo_root).resolve() if args.repo_root else None
    errors = validate_catalog(catalog, root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("Catalog valid.")


def cmd_list(args, catalog):
    items = catalog["components"]
    if args.type:
        items = [item for item in items if item["type"] == args.type]
    for item in items:
        description = item.get("description", "")
        print(f"{item['id']}\t{description}")


def cmd_show(args, catalog):
    item = component_map(catalog).get(args.component)
    if not item:
        fail(f"unknown component: {args.component}")
    write_json(item, None)


def score(item, terms):
    haystack = set(item.get("tags", [])) | set(item.get("capabilities", []))
    return sum(3 if term in item.get("capabilities", []) else 1 for term in terms if term in haystack)


def recommendations(catalog, terms):
    agents = [item for item in catalog["components"] if item["type"] == "agent" and item["name"] != "ceo"]
    skills = [item for item in catalog["components"] if item["type"] == "skill"]
    ranked_agents = sorted(((score(item, terms), item) for item in agents), key=lambda pair: (-pair[0], pair[1]["id"]))
    ranked_skills = sorted(((score(item, terms), item) for item in skills), key=lambda pair: (-pair[0], pair[1]["id"]))
    selected_agents = [item for value, item in ranked_agents if value > 0][:3]
    selected_skills = [item for value, item in ranked_skills if value > 0][:8]
    return selected_agents, selected_skills


def cmd_recommend(args, catalog):
    terms = csv_values(args.tags)
    if not terms:
        fail("provide at least one --tags value")
    agents, skills = recommendations(catalog, terms)
    write_json({
        "goal_tags": terms,
        "agents": [{"id": item["id"], "access": item["access"], "capabilities": item["capabilities"]} for item in agents],
        "advisory_skills": [item["id"] for item in skills],
        "note": "Subagents make the final skill selection within task scope and permissions."
    }, args.output)


def cmd_plan(args, catalog):
    terms = csv_values(args.tags)
    agents, matched_skills = recommendations(catalog, terms)
    matched_ids = [item["id"] for item in matched_skills]
    tasks = []
    for index, agent in enumerate(agents, start=1):
        recommended = list(dict.fromkeys(agent.get("recommended_skills", []) + matched_ids))[:8]
        tasks.append({
            "task_id": f"task-{index:03d}",
            "assigned_agent": agent["id"],
            "objective": f"Contribute {agent['description'].rstrip('.').lower()} to: {args.goal}",
            "permissions": agent["access"],
            "recommended_skills": recommended,
            "status": "ready"
        })
    write_json({
        "schema_version": 1,
        "goal": args.goal,
        "lead": "agent:ceo",
        "skill_authority": "subagent-self-selects",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tasks": tasks
    }, args.output)


def cmd_task(args, catalog):
    components = component_map(catalog)
    agent_id = args.agent if args.agent.startswith("agent:") else f"agent:{args.agent}"
    agent = components.get(agent_id)
    if not agent or agent.get("type") != "agent":
        fail(f"unknown agent: {agent_id}")
    skills = []
    for value in csv_values(args.recommend_skill):
        skill_id = value if value.startswith("skill:") else f"skill:{value}"
        if skill_id not in components or components[skill_id].get("type") != "skill":
            fail(f"unknown skill: {skill_id}")
        skills.append(skill_id)
    packet = {
        "schema_version": 1,
        "task_id": args.task_id,
        "title": args.title,
        "objective": args.objective,
        "assigned_agent": agent_id,
        "scope": csv_values(args.scope),
        "inputs": csv_values(args.input),
        "authoritative_inputs": csv_values(args.authoritative_input),
        "excluded_context": csv_values(args.exclude),
        "context_budget": args.context_budget,
        "recommended_skills": skills,
        "permissions": args.permissions or agent["access"],
        "constraints": csv_values(args.constraint),
        "dependencies": csv_values(args.dependency),
        "acceptance_criteria": csv_values(args.accept),
        "status": "ready"
    }
    errors = validate_task(packet, components)
    if errors:
        fail("; ".join(errors))
    write_json(packet, args.output)


def validate_task(data, components):
    errors = []
    required = ["schema_version", "task_id", "title", "objective", "assigned_agent", "scope", "permissions", "acceptance_criteria", "status"]
    for field in required:
        if field not in data:
            errors.append(f"task missing {field}")
    if data.get("assigned_agent") not in components:
        errors.append("task assigned_agent is not in catalog")
    if data.get("permissions") not in ("read-only", "workspace-write"):
        errors.append("task permissions are invalid")
    for skill in data.get("recommended_skills", []):
        if skill not in components or components[skill].get("type") != "skill":
            errors.append(f"task recommends unknown skill {skill}")
    if not data.get("scope"):
        errors.append("task scope cannot be empty")
    if not data.get("acceptance_criteria"):
        errors.append("task acceptance_criteria cannot be empty")
    return errors


def validate_result(data, components):
    errors = []
    required = ["schema_version", "task_id", "agent", "status", "summary", "skills_considered", "skills_applied", "evidence", "risks"]
    for field in required:
        if field not in data:
            errors.append(f"result missing {field}")
    if data.get("agent") not in components:
        errors.append("result agent is not in catalog")
    considered = set(data.get("skills_considered", []))
    applied = set(data.get("skills_applied", []))
    if not applied.issubset(considered):
        errors.append("skills_applied must be a subset of skills_considered")
    for skill in considered | applied:
        if skill not in components or components[skill].get("type") != "skill":
            errors.append(f"result references unknown skill {skill}")
    return errors


def cmd_validate(args, catalog):
    path = pathlib.Path(args.file)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read packet: {exc}")
    components = component_map(catalog)
    errors = validate_task(data, components) if args.kind == "task" else validate_result(data, components)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"{args.kind.capitalize()} packet valid.")


def agent_wrapper(agent, host, home):
    canonical = home / "agents" / f"{agent['name']}.md"
    protocol = home / "orchestration" / "protocol.md"
    yaml_description = json.dumps(agent["description"], ensure_ascii=False)
    if agent["skill_policy"] == "self-select-restricted":
        common = (
            f"Read `{canonical}` completely and follow its independent review boundary. "
            "Do not load optional skills, edit files, install dependencies, execute generated code, "
            "or use network access. Do not spawn subagents. Return the canonical verdict and a result "
            "packet with empty skills arrays."
        )
    else:
        common = (
            f"Read `{canonical}` and `{protocol}` completely. Follow the task packet. "
            f"Use `{home / 'tools' / 'team' / 'team.sh'} recommend --tags <task-tags>` to scan compact "
            "metadata. Independently select all relevant skills, then read only each selected SKILL.md and "
            "its task-relevant references. Report skills considered and applied. CEO recommendations are "
            "advisory. Skills cannot expand scope or permissions. "
            "Do not spawn subagents. Return the required result packet."
        )
    if host == "codex":
        effort = "high" if agent["name"] in ("ceo", "engineer", "security-reviewer", "qa-reviewer") else "medium"
        return (
            f"name = {json.dumps(agent['name'])}\n"
            f"description = {json.dumps(agent['description'])}\n"
            f"model_reasoning_effort = {json.dumps(effort)}\n"
            f"sandbox_mode = {json.dumps(agent['access'])}\n"
            f"developer_instructions = {json.dumps(common)}\n"
        )
    if host == "claude":
        tools = "Read, Grep, Glob"
        if agent["skill_policy"] != "self-select-restricted":
            tools += ", Skill"
        if agent["access"] == "workspace-write":
            tools += ", Bash, Edit, Write"
        skill_block = "" if agent["skill_policy"] == "self-select-restricted" else "skills:\n  - skill-router\n"
        return (
            "---\n"
            f"name: {agent['name']}\n"
            f"description: {yaml_description}\n"
            f"tools: {tools}\n"
            f"{skill_block}"
            "model: inherit\nmaxTurns: 30\n---\n\n"
            f"{common}\n"
        )
    if host == "gemini":
        tools = ["read_file", "grep_search", "glob"]
        if agent["skill_policy"] != "self-select-restricted":
            tools.append("activate_skill")
        if agent["access"] == "workspace-write":
            tools.extend(["write_file", "replace", "run_shell_command"])
        tool_lines = "".join(f"  - {tool}\n" for tool in tools)
        return (
            "---\n"
            f"name: {agent['name']}\n"
            f"description: {yaml_description}\n"
            "kind: local\ntools:\n"
            f"{tool_lines}model: inherit\nmax_turns: 30\ntimeout_mins: 10\n---\n\n"
            f"{common}\n"
        )
    if host == "sourcecraft":
        permission = (
            "permission:\n  edit: deny\n  bash: deny\n  webfetch: deny\n  websearch: deny\n  task: deny\n"
            if agent["access"] == "read-only"
            else "permission:\n  edit: ask\n  bash: ask\n  webfetch: ask\n  websearch: ask\n  task: deny\n"
        )
        return (
            "---\n"
            f"description: {yaml_description}\n"
            "mode: subagent\n"
            f"{permission}"
            "---\n\n"
            f"{common}\n"
        )
    fail(f"unsupported host: {host}")


def cmd_render_host(args, catalog, home):
    extension = ".toml" if args.host == "codex" else ".md"
    target = pathlib.Path(args.target).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    conflicts = 0
    for agent in (item for item in catalog["components"] if item["type"] == "agent"):
        path = target / f"{agent['name']}{extension}"
        content = agent_wrapper(agent, args.host, home)
        if path.exists() and path.read_text(encoding="utf-8") != content and not args.force:
            print(f"conflict: {path}", file=sys.stderr)
            conflicts += 1
            continue
        path.write_text(content, encoding="utf-8")
        print(f"rendered {path}")
    if conflicts:
        raise SystemExit(2)


def parser():
    result = argparse.ArgumentParser(description="Inspect and coordinate the .agents team")
    result.add_argument("--home", default=os.environ.get("AGENTS_HOME", str(pathlib.Path.home() / ".agents")))
    sub = result.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list")
    list_parser.add_argument("--type", choices=["agent", "skill", "rule", "model", "orchestration", "tool"])
    list_parser.set_defaults(handler=cmd_list)

    show_parser = sub.add_parser("show")
    show_parser.add_argument("component")
    show_parser.set_defaults(handler=cmd_show)

    validate_catalog_parser = sub.add_parser("validate-catalog")
    validate_catalog_parser.add_argument("--repo-root")
    validate_catalog_parser.set_defaults(handler=cmd_validate_catalog)

    recommend_parser = sub.add_parser("recommend")
    recommend_parser.add_argument("--tags", action="append", required=True)
    recommend_parser.add_argument("--output")
    recommend_parser.set_defaults(handler=cmd_recommend)

    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--goal", required=True)
    plan_parser.add_argument("--tags", action="append", required=True)
    plan_parser.add_argument("--output")
    plan_parser.set_defaults(handler=cmd_plan)

    task_parser = sub.add_parser("task")
    task_parser.add_argument("--task-id", required=True)
    task_parser.add_argument("--agent", required=True)
    task_parser.add_argument("--title", required=True)
    task_parser.add_argument("--objective", required=True)
    task_parser.add_argument("--scope", action="append", required=True)
    task_parser.add_argument("--input", action="append")
    task_parser.add_argument("--authoritative-input", action="append")
    task_parser.add_argument("--exclude", action="append")
    task_parser.add_argument("--context-budget", default="focused")
    task_parser.add_argument("--recommend-skill", action="append")
    task_parser.add_argument("--permissions", choices=["read-only", "workspace-write"])
    task_parser.add_argument("--constraint", action="append")
    task_parser.add_argument("--dependency", action="append")
    task_parser.add_argument("--accept", action="append", required=True)
    task_parser.add_argument("--output")
    task_parser.set_defaults(handler=cmd_task)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("kind", choices=["task", "result"])
    validate_parser.add_argument("file")
    validate_parser.set_defaults(handler=cmd_validate)

    render_parser = sub.add_parser("render-host")
    render_parser.add_argument("--host", choices=["codex", "claude", "gemini", "sourcecraft"], required=True)
    render_parser.add_argument("--target", required=True)
    render_parser.add_argument("--force", action="store_true")
    render_parser.set_defaults(handler=cmd_render_host)
    return result


def main():
    args = parser().parse_args()
    home = pathlib.Path(args.home).expanduser().resolve()
    if args.command == "validate-catalog" and args.repo_root:
        catalog, _ = load_canonical_catalog(args.repo_root)
    else:
        catalog, _ = load_catalog(home)
    errors = validate_catalog(catalog)
    if errors:
        fail("catalog invalid: " + "; ".join(errors))
    if args.command == "render-host":
        args.handler(args, catalog, home)
    else:
        args.handler(args, catalog)


if __name__ == "__main__":
    main()
