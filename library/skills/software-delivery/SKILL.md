---
name: software-delivery
description: Deliver bounded software changes from verified requirements through tests and review.
---

# Software Delivery

Use for implementing or modifying code, configuration, scripts, or tests.

1. Confirm scope, interfaces, constraints, and acceptance criteria.
2. Inspect the smallest relevant surface and preserve unrelated changes.
3. Choose a minimal design that fits existing conventions.
4. Implement in reviewable increments with explicit error handling.
5. Add tests for behavior, boundaries, and regressions.
6. Run focused checks before broader validation.
7. Review the final diff for correctness, security, compatibility, and scope.

Return changed artifacts, verification evidence, assumptions, and remaining
risks. Do not claim tests were run when they were not.
