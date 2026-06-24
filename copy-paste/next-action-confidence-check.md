# Next-Action Confidence Check

Use this before letting an AI agent continue from one task into the next.

This check separates two decisions:

1. Is the current task actually complete?
2. Should the next loop actually run?

## Copy-paste prompt

```text
Before starting the next task, run a Next-Action Confidence Check.

Report:

- What changed
- What was verified
- What was not touched
- What remains uncertain
- Is the current task complete? PASS / DELAY / BLOCK
- Should the next loop run? GO / HOLD / CAP / BLOCK
- Reason
- One allowed next action
- Not allowed
- CAP limit, if any

Do not start the next task automatically.
Stop after this report and wait for the user.
```

## When to use

Use this when an AI agent says a task is done and there is a visible next action.

## Verify

The agent separates task completion from next-loop permission.

## Stop when

The agent outputs one gate, one allowed next action, and does not start the next task.
