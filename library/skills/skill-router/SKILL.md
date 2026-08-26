---
name: skill-router
description: Select the smallest useful set of installed skills for a task.
---

# Skill Router

Use at the start of a task when several ecosystem capabilities may apply.

1. Read `~/.agents/catalog.json` if available.
2. Extract the task domain, deliverable, risk, dependencies, and required host.
3. Rank matching skills by direct relevance and avoid overlapping workflows.
4. Recommend at most three primary skills unless the task clearly spans more
   independent disciplines.
5. Explain what each selected skill contributes in one sentence.
6. If a capability is missing, use `find-skills`; do not pretend it exists.

Return `Selected`, `Optional`, and `Not needed`. Ask the user to choose only
when alternatives would materially change the work.
