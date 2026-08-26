---
name: context-engineering
description: Build efficient context windows, summaries, and agent handoffs.
---

# Context Engineering

Use when a task has long history, multiple agents, large repositories, or
repeated model calls.

## Workflow

1. Define the exact next decision or deliverable.
2. Gather only authoritative inputs that can change that decision.
3. Separate stable facts, user decisions, current state, and unresolved risk.
4. Replace raw history with references and concise evidence summaries.
5. Keep exact interfaces, errors, constraints, and acceptance criteria.
6. Assign each subagent a minimal packet and explicit output contract.
7. Refresh the handoff when facts change; remove stale material.

## Output contract

Provide an objective, relevant facts, decisions, artifacts, constraints, open
questions, next action, and a confidence note. Compression is successful only
when another agent can act correctly without rediscovering omitted context.
