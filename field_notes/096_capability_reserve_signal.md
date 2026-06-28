# Capability Reserve Signal

## Observation

`V12 PASS` means the artifact appears restartable.

It does not prove that the executing agent or chat still has enough remaining capability for the next complex development loop.

A long context can still produce clean, coherent outputs while losing reserve for deeper reasoning, fresh constraint detection, and high-friction development decisions.

## Core distinction

```text
V12 = artifact restartability
Execution Health = tool/process reliability
Capability Reserve = remaining reasoning capacity under long context
V13 = next-loop permission
```

## Key rule

```text
Clean completion does not prove remaining capability.
```

Japanese framing:

```text
綺麗な完了は、能力余力が残っている証明ではない。
```

## Why this matters

A chat or agent run may produce clean final artifacts while showing signs that the next loop should not continue at the same weight.

Examples:

- the conversation is very long
- many recent concepts have accumulated
- responses become clean but overly long
- the agent over-summarizes rather than sharpening decisions
- fresh constraints may be missed
- artifact quality is confused with process health
- the next action is not strongly narrowed
- subtle new concepts are treated as just another note
- the agent can still organize, but may no longer be safe for heavy development

No visible failure does not mean full capability remains.

## Contact lens analogy

Using contact lenses safely for two weeks does not prove they should be used for three weeks.

Likewise:

```text
The last task completed cleanly
```

does not imply:

```text
This same long context should continue into another complex development loop.
```

## Signal categories

### 🟢 GREEN

The context is still short or clear enough for the next bounded task.

Use only for light next actions or clearly scoped work.

### 🟡 YELLOW

The artifact may be clean, but the context is long or dense enough that heavy next-loop development should be capped.

Recommended action:

```text
Create a restartable handoff before continuing.
Move heavy development to a fresh or lighter context.
```

### 🔴 RED

The context is no longer reliable for even bounded development.

Recommended action:

```text
Stop development.
Create a handoff only.
Resume elsewhere.
```

## Correct gate when reserve is YELLOW

```text
V12 State: PASS
Execution Health Signal: 🟡 if there was silence, interruption, tool uncertainty, or reporting uncertainty
Capability Reserve Signal: 🟡
V13 Next Loop Gate: CAP
```

Meaning:

The artifacts can be restarted, but the current long context should not continue heavy development.

## Allowed next action

When Capability Reserve is 🟡 or 🔴, the allowed next action is not more implementation.

Allowed:

- create a restartable handoff
- record current artifact state
- record process/capability signals
- define where a fresh session should resume
- split the next loop into a smaller task

Not allowed:

- continue heavy concept expansion
- change architecture
- rewrite README
- promote AGENTS.md changes
- add automation
- make external moves
- treat clean output as proof of safe continuation

## Relationship to V12 and V13

V12 checks whether the artifact can be resumed.

Capability Reserve checks whether the current execution context should continue producing more work.

V13 uses both signals to decide whether the next loop is GO, HOLD, CAP, or BLOCK.

## Status

Signal captured.

This note is a close-out criterion, not a new feature implementation.
