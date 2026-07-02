# Field Note 106 — Claude Code Setup Audit as Pre-Automation Check

## Layer

V13 / Pre-Automation Governance / Environment Inventory

Adjacent layers:
- V10 Goal-Length / avoiding premature automation load
- V12 Completion Integrity / handoff and closure before execution
- V14 Resource Justice / avoiding hidden operational burden

## Summary

A Claude Code setup audit prompt revealed a useful V13 pattern:

```text
Before increasing automation, first inspect the operating environment in read-only mode.
```

The important idea is not Claude Code optimization by itself.

The important V13 lesson is that automation should not begin from an unexamined environment.

Before adding skills, hooks, MCP, subagents, permissions, or workflow automation, the operator should first know:

```text
what is always in context
what is procedural
what is enforced
what is delegated
what can modify files
what can run commands
what returns control to the human Seat
```

This makes the prompt a candidate source for a V13 pre-automation audit layer.

## Core Pattern

The reusable pattern is:

```text
read-only inventory
→ component classification
→ V13 gate check
→ risk / missing closure report
→ only then consider automation
```

This is aligned with V13 because it avoids jumping directly from capability to execution.

## Read-only Audit Requirement

The first phase must be read-only.

Before explicit approval, the audit must not:

```text
create files
edit files
install packages
enable hooks
enable MCP
change permissions
modify Git workflow
write global settings
run destructive commands
start automation
```

The first output should be an inventory and risk report, not a modified environment.

## Claude Code Components to Inventory

A Claude Code setup audit should inspect or ask about the following surfaces:

```text
CLAUDE.md
.claude/rules
skills
agents
hooks
output-styles
MCP
settings
permissions
Git workflow
repo-local instructions
global instructions
project-specific overrides
```

The purpose is to see where behavior is coming from before adding more behavior.

## Routing Principle

The prompt surfaced a useful routing principle:

```text
Always-needed context → CLAUDE.md
Procedure → skill
Mandatory enforcement → hook / permissions
Isolation or specialization → subagent
External tool connection → MCP
Current project state → STATUS / handoff
```

V13 should preserve this as a candidate classification rule, not as an immediate implementation requirement.

## V13 Additions Required

The original audit prompt is not sufficient for V13 unless it also checks:

```text
Current Gate
Completion Line
Missing Closure
Seat / Decision Owner
next actor
what must not be returned to the human
rollback condition
re-evaluation condition
blocked scope
handoff responsibility transfer
```

A setup audit that only lists tools may still miss the governance state.

V13 requires the audit to ask:

```text
Who owns the next decision?
What is safe to do next?
What is still blocked?
What would require human approval?
What cleanup should the AI close instead of returning to the human?
```

## Risk

The original Claude Code setup audit prompt is broad.

It can easily expand into:

```text
PC-wide audit
Claude Code full optimization
MCP planning
hook design
skill design
permission restructuring
Git workflow redesign
long report generation
automation roadmap
```

That is too much for the first V13 pass.

## CAP Rule

For V13 use, Phase 1 should be capped to read-only inventory.

Initial Phase 1 scope:

```text
list existing instruction surfaces
list existing automation surfaces
list permission surfaces
list Git workflow assumptions
identify missing Gate / Completion Line / Seat / rollback conditions
recommend no more than one next safe action
```

Do not optimize yet.

Do not implement yet.

Do not create automation yet.

## BLOCK Conditions

BLOCK if the audit attempts to:

```text
edit Claude Code settings without approval
create or modify hooks
enable MCP
install tools
change permissions
create skills
create subagents
rewrite CLAUDE.md
rewrite AGENTS.md
change Git workflow
run commands beyond read-only inspection
produce a full automation roadmap before inventory is complete
```

## V13 Interpretation

This prompt can become a way to V13-ify a Claude Code environment.

The goal is not:

```text
make Claude Code more powerful immediately
```

The goal is:

```text
make the environment legible before automation increases
```

Automation should accelerate only after:

```text
Seat is clear
Gate is clear
Completion Line is clear
Missing Closure is visible
rollback / re-evaluation conditions exist
blocked scope is explicit
```

## Relation to Automation Positioning

This supports the V13 automation framing:

```text
V13 is not anti-automation.
V13 helps automation move faster while keeping Seat, Gate, restartability, and stop conditions visible.
```

A Claude Code setup audit is one practical entry point for that framing.

It asks:

```text
Before we automate more, do we actually know what is already controlling the environment?
```

## Not a MISTAKEN.md Entry Yet

This is not yet a MISTAKEN.md rule.

Reason:

```text
This is a design learning and future audit pattern, not a repeated failure.
```

Promote only if future work repeatedly jumps into Claude Code automation without read-only inventory.

Possible future MISTAKEN rule:

```text
Do not automate a Claude Code environment before read-only inventory of context, permissions, hooks, MCP, skills, agents, and Seat conditions.
```

For now, keep it as a Field Note.

## Future Reuse

A future V13 Claude Code setup audit may use this phased structure:

```text
Phase 1: read-only inventory
Phase 2: governance gap report
Phase 3: one safe recommendation
Phase 4: explicit approval
Phase 5: bounded implementation
Phase 6: acceptance audit
```

The first reusable output should be a short report, not a changed environment.

## Completion Line

This field note records the Claude Code setup audit prompt as a V13 pre-automation check candidate.

Current status:

```text
Field Note: PASS
Execution: HOLD
Read-only inventory design: NEXT candidate
Automatic optimization: BLOCK until explicit approval
```
