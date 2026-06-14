# Field Note 025: Footer Axis Consolidation

Date: 2026-06-14

## Observation

V13 has several footer forms:

- V13 Lite Footer
- Chat Continuation Footer
- Context Compression Footer

Each was useful when introduced.

But together they can look like multiple versions of the same question:

```text
Should we prepare before continuing?
```

That creates report weight and possible confusion.

## Problem

Multiple footers can make V13 look more precise while actually duplicating the same judgment in different vocabulary.

The risk is footer inflation:

- more labels
- more lines
- more status words
- less clarity

More footers are not automatically better governance.

If the axes are not separated, agents may include all footers by default and make the report heavier without improving the decision.

## Axis Separation

Footers must not duplicate judgment under different names.

Each footer must answer a different operational question.

The axes are:

1. next-loop admissibility
2. conversation/session continuity risk
3. memory/restart compression need

If a footer does not answer a separate axis, it should not be added.

## Footer Roles

### V13 Lite Footer

Question:

```text
Should the next work loop run, wait, be capped, or be blocked?
```

Axis:

```text
Next-loop admissibility
```

Primary output:

```text
GO / HOLD / CAP / BLOCK
```

Use when:

Every task report needs a next-loop decision.

### Chat Continuation Footer

Question:

```text
Can this conversation/session continue safely, or should a handoff be prepared?
```

Axis:

```text
Conversation/session continuity risk
```

Primary output:

```text
CHAT_CONTINUE / PREPARE_HANDOFF / HANDOFF_NOW
```

Use when:

The chat has accumulated decisions, branches, corrections, or enough context that continuing in the same thread may create restart risk.

### Context Compression Footer

Question:

```text
Does future work require compressed restart anchors instead of raw long history?
```

Axis:

```text
Memory/restart compression need
```

Primary output:

```text
KEEP / COMPRESS / HANDOFF
```

Use when:

The task has accumulated enough context that future work would require rereading long history or risks losing current state.

## Consolidation Rule

Always include V13 Lite Footer for task reports.

Include Chat Continuation only when the conversation/session itself is becoming a risk.

Include Context Compression only when future restart from raw history is becoming inefficient or unsafe.

If Chat Continuation and Context Compression point to the same action, do not inflate the report.

State the shared risk once and keep the shorter footer.

Do not use all footers by default.

Do not treat more footers as better governance.

If the axis cannot be separated, use the V13 Lite Footer plus one sentence explaining the context/restart concern.

## Examples

### Example 1: Small code task, low context

Situation:

```text
One small bug fix, one commit, no long thread, no future restart risk.
```

Use:

```text
V13 Lite Footer only
```

Reason:

The only required judgment is whether the next work loop should GO / HOLD / CAP / BLOCK.

### Example 2: Long discussion with many decisions, no file changes

Situation:

```text
Many decisions were made in chat, but there is no large file or commit history to compress.
```

Use:

```text
V13 Lite Footer
Chat Continuation Footer
```

Reason:

The work-loop gate and session-continuity risk are separate.

### Example 3: Large multi-commit session with future restart risk

Situation:

```text
Several commits, field notes, and repaired assumptions accumulated. Future work would require rereading long history.
```

Use:

```text
V13 Lite Footer
Context Compression Footer
```

Add Chat Continuation only if the current chat should not continue into another major task.

Reason:

The memory/restart compression need is real. The conversation/session risk is separate and should not be assumed.

## Boundary

This field note records consolidation logic only.

It does not modify AGENTS.md yet.

It does not remove any footer yet.

It does not rewrite footer formats.

It does not solve all reporting format questions.

It does not update AGENTS.ja.md, README.md, docs, schemas, examples, prompts, plugin files, CI, or automation.

It does not add features, hooks, skills, MCP, pluginization, automation, or product behavior.

This should guide the later AGENTS.md repair so footers are not duplicated.

## V13 Signal

Signal:
🟢 BLUE / FOOTER-AXES-SEPARATED
+
🟢 BLUE / MORE-FOOTERS-NOT-BETTER
+
🟡 YELLOW / AGENTS-REFLECTION-STILL-PENDING
+
🟡 YELLOW / DO-NOT-REWRITE-FOOTERS-YET

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The footer axes are now separated as a bounded field-note-only repair. The rule prevents duplicated footer judgments without yet changing AGENTS.md or rewriting any footer format.

Next Loop Command:
Proceed to bounded AGENTS.md reflection of field notes 021–025.
