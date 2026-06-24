# Restartable Handoff

Use this before ending a long AI-agent session.

The goal is to leave enough state for the next human or AI to restart without guessing.

## Copy-paste prompt

```text
Before ending this session, create a Restartable Handoff.

Report:

- Current goal
- What changed
- What was verified
- What was not touched
- What remains uncertain
- Open risks
- Off-limits scope
- Last known decision or gate
- Exactly one safe next action
- What the next AI/human should not assume

Do not start the next action.
Stop after the handoff.
```

## When to use

Use this when:

- context is getting long
- the session is ending
- another AI or human may continue the work
- you want to avoid losing the route, evidence, or limits

## Verify

The next human or AI can restart without guessing what happened, what was verified, what is off limits, or what the safest next action is.

## Stop when

The handoff includes current state, evidence, open risks, off-limits scope, and exactly one safe next action, without starting that action.
