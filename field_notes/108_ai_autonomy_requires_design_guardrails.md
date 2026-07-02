# Field Note 108 — AI Autonomy Requires Design Guardrails

## Layer

V13 / Seat-Preserving Automation / Design Guardrails

Adjacent layers:
- V10 Goal-Length / bounded acceleration
- V12 Completion Integrity / review and closure before continuation
- V14 Resource Justice / avoiding hidden QA and maintenance burden

## Source

External article:

```text
AIが自走できるかは設計で決まる ― 良いコードを残し、悪いコードを入れさせない
Zenn
Published: 2026-07-02
URL: https://zenn.dev/sunagaku/articles/ai-autonomous-development-design
```

## Summary

The article provides an external observation that aligns strongly with V13:

```text
AI autonomy is not achieved by leaving the AI alone.
It is achieved by preparing the path the AI is allowed to follow.
```

The article argues that whether AI can “run autonomously” depends less on tool usage alone and more on the design quality of the codebase.

AI follows existing code.

Therefore:

```text
good design propagates
bad design propagates
```

This makes design, review accumulation, Plan quality, Skill usage, and CI important guardrails for AI-driven development.

## Key Observations from the Article

The article’s important claims for V13 are:

```text
AI uses existing code as a model.
AI horizontally expands existing design patterns.
Good design spreads through AI-generated code.
Bad design also spreads through AI-generated code.
PR count and generation speed alone do not equal productivity.
“Working code” is not the same as good design.
Human review should check whether the design is optimal, not only whether it runs.
Root design, boundaries, responsibilities, and extension axes should be set by humans.
Local, low-impact implementation can be delegated to AI.
Review feedback should be accumulated into CLAUDE.md or Skills.
Routine procedures can be Skillized.
Mechanically detectable mistakes should be prevented by CI.
```

## V13 Interpretation

This is not an anti-automation argument.

It supports the V13 framing:

```text
V13 is not against automation.
V13 helps automation accelerate while keeping Seat, Gate, design intent, restartability, and stop conditions visible.
```

The article shows that AI autonomy requires prepared operating conditions.

In V13 terms:

```text
automation without design guardrails becomes replication of whatever pattern already exists
```

If the existing pattern is good, AI can extend it.

If the existing pattern is bad, AI can multiply the damage.

## Why This Matters

A common AI-agent failure mode is to treat speed as success:

```text
more PRs
more generated code
more autonomous execution
more local patches
```

But the article warns that this can create:

```text
hidden design debt
QA burden
repeated bug-fix PRs
patch accumulation
loss of readability
loss of design intent
bad patterns that AI continues to imitate
```

This is directly relevant to V13.

V13 should not only ask:

```text
Can the AI continue?
```

It should also ask:

```text
What design pattern is the AI about to continue?
Should that pattern be allowed to propagate?
Where should the human Seat define the root boundary first?
```

## Seat Boundary

The article supports a clear Seat boundary:

```text
Humans define root design, responsibility boundaries, and extension direction.
AI handles local implementation where impact is bounded.
```

This maps to V13 as:

```text
Human Seat:
- design intent
- boundaries
- responsibility allocation
- stop conditions
- review criteria

AI Execution:
- local implementation
- routine procedures
- repeated checks
- bounded extension of approved patterns
```

## Relation to Skills and CLAUDE.md

The article’s practical tips also support V13’s routing logic.

Useful routing:

```text
Always-needed design intent -> CLAUDE.md / AGENTS.md
Repeated procedure -> Skill
Mechanically detectable mistake -> CI / check
Specialized review perspective -> Agent / subagent
Unsafe or irreversible action -> permission / gate / human approval
```

This should remain a design observation for now.

Do not implement new Skills, hooks, MCP, or CI from this field note.

## V13 Learning

The key learning is:

```text
Autonomy amplifies the environment.
```

AI does not merely execute a prompt.

It reads and extends the operating conditions around it:

```text
existing code
existing design
existing review rules
existing CLAUDE.md / AGENTS.md
existing Skills
existing CI
existing permissions
existing handoff state
```

Therefore, before increasing autonomy, V13 should check whether the environment is safe to amplify.

## Relation to Field Note 106

This connects with Field Note 106:

```text
Claude Code setup audit as Pre-Automation Check
```

Field Note 106 focuses on read-only inventory of the AI development environment before automation increases.

This field note adds an external confirmation:

```text
Even if tools are available, the quality of what AI will reproduce depends on the structure it is given.
```

Together:

```text
Field Note 106:
Inspect the environment before automating.

Field Note 108:
Ensure the environment contains patterns worth amplifying.
```

## CAP Conditions

CAP any attempt to use this article as a reason to immediately:

```text
rewrite CLAUDE.md
create Skills
create hooks
enable MCP
change CI
restructure the repo
start a Claude Code setup audit
publish an external post
```

The current task is observation capture only.

## BLOCK Conditions

BLOCK if work attempts to:

```text
modify Claude Code configuration
install tools
enable MCP
create Skills
create hooks
change permissions
change Git workflow
rewrite existing repo instructions
turn this into a broad automation roadmap
claim that AI autonomy is safe without human Seat
```

## Not a MISTAKEN.md Entry Yet

This is not yet a MISTAKEN.md rule.

Reason:

```text
This is an external observation and design learning, not a repeated internal failure.
```

Possible future MISTAKEN rule, only if repeated failures occur:

```text
Do not increase AI autonomy before verifying that the patterns it will copy are worth amplifying.
```

For now, keep it as a Field Note.

## Future Reuse

Use this observation when evaluating:

```text
Claude Code setup audits
Skill creation
hook creation
MCP integration
subagent design
AI-agent repo scaffolds
implementation capsules
acceptance audits
derived repo governance
```

Before increasing automation, ask:

```text
What will the AI imitate?
Is that pattern approved?
Is the human Seat still holding root design?
Are mistakes captured into reusable rules?
Are mechanical errors prevented by checks?
Is the next action bounded?
```

## Completion Line

This field note records an external V13-aligned observation:

```text
AI自走は放任ではない。
AIが速く進むほど、進んでよい設計・踏襲してよいパターン・止まる条件を先に整える必要がある。
```

Current status:

```text
Field Note: PASS
Implementation: HOLD
Claude Code setup audit integration: CAP
External posting: HOLD
```
