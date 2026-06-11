# Use Case: AI Coding After Completion

Use this when an AI coding agent has finished a task and wants to continue with another implementation loop.

The danger is false momentum: a task can be complete, tested, and useful, while the next coding loop is still not admissible.

V13 prevents the agent from treating completion as permission to keep modifying the codebase.

## Typical Completed State

- A bug fix, feature, scaffold, or refactor is complete.
- Tests or manual checks have passed.
- The agent has a summary and possibly a clean git state.
- There are tempting follow-up improvements.

## V13 Question

Given the completed coding state, should the agent run another coding loop, hold for review, cap the next change, or block further edits?

## Copy-Paste Input

Paste the agent's final summary into [`../prompts/v13_loop_review.md`](../prompts/v13_loop_review.md).

Add this context:

```text
Use case: AI coding after completion.

Pay special attention to:
- whether tests actually cover the changed behavior
- whether follow-up work is related or scope creep
- whether the codebase is easier to re-enter after the loop
- whether another loop risks changing unrelated files
- whether human review should happen before more edits
```

## Gate Examples

- GO: run the next coding loop when the next variable is clear, tests are available, and re-entry capacity is preserved.
- HOLD: wait when correctness, review status, or scope is unclear.
- CAP: allow a small bounded follow-up, such as one file, one failing test, or one documented issue.
- BLOCK: stop when the loop is causing broad churn, weak rollback, damaged trust, or reduced re-entry capacity.

## Example CAP

```text
Change at most one file and one test file. Do not introduce dependencies. Stop after one verification pass.
```

## Example Next Loop Command

```text
Run one bounded follow-up loop to add the missing test only, then stop for review.
```
