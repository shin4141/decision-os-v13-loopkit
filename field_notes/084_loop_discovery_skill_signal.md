# Loop Discovery Skill Signal

## Observation

An external skill, `loop-me`, shows that loop tooling is moving beyond prompt templates.

It frames loops as recurring patterns in a user's life, work, week, or repeated activity, then uses an interview-style process to turn those loops into workflow specs.

The skill is not primarily about executing work.

It is about discovering, sharpening, and specifying loops until an implementer agent could build the workflow without asking another question.

Source:
https://github.com/mattpocock/skills/blob/main/skills/in-progress/loop-me/SKILL.md

## Why this matters

This is a strong external signal for the next stage of AI-agent workflow tooling.

The emerging direction is:

1. discover recurring loops
2. turn them into workflow specs
3. defer human checkpoints until decision-ready summaries
4. let implementer agents build from the spec
5. reduce ambiguous human involvement

This confirms that the market is moving from "write a prompt" toward "identify and operationalize loops."

## V13 interpretation

Loop discovery is not the same as loop governance.

`loop-me` helps identify and specify loops.

V13 asks whether a discovered or specified loop should actually run, under what gate, and whether the loop remains restartable and returnable.

External loop discovery makes V13 more necessary, not less.

As more loops are discovered, the problem shifts from:

- "Can we find loops?"

to:

- "Which loop should run next?"
- "Should this loop run now?"
- "What is the stopping condition?"
- "What checkpoint can safely be pushed right?"
- "What must remain under human decision?"
- "Can the next human or AI restart without guessing?"

## Risk

A tool that finds many loops can create loop abundance.

Loop abundance can lead to:

- too many candidate workflows
- over-automation
- delayed human checkpoints
- unclear ownership
- hidden drift
- route lock-in
- weak restartability

Therefore, discovered loops need a gate.

## V13 position

The useful distinction is:

```text
Loop discovery:
Find and specify candidate loops.

Loop governance:
Decide which loop should run, when it should stop, and how the next human or AI can safely continue.
```

V13 sits in the governance layer.

It does not need to copy `loop-me`.

It should treat `loop-me` as evidence that loop discovery and workflow specification are becoming more important.

## Parked Horizon

Potential future direction:

`Discover-to-Gate`

When an external tool discovers candidate loops, V13 can evaluate them before execution.

Candidate evaluation fields:

- trigger
- intended outcome
- evidence needed
- stop condition
- human checkpoint
- context risk
- returnability
- next safe action
- GO / HOLD / CAP / BLOCK

## Boundary

Do not implement a skill now.

Do not add MCP, hooks, pluginization, automation, or workflow generation.

Do not compete with loop discovery tools.

Capture the signal only.

## Status

Signal captured.

No README rewrite.
No tutorial change.
No feature expansion.
No automation.
