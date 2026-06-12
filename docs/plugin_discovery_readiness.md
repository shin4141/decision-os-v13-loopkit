# Plugin Discovery Readiness

## Purpose

Plugin Discovery Readiness prepares V13 LoopKit for a lower-friction future path:

> Instead of asking humans to manually discover and understand V13 LoopKit, let their AI agent evaluate whether this repo fits their workflow.

This is not plugin implementation.

It is a design note for agent-readable discovery, recommendation, and safe adoption.

## Why This Exists

`AGENTS.md` is lightweight, but it still asks the user to perform a manual sequence:

1. find the repository
2. read the README
3. understand why the kit matters
4. copy `AGENTS.md`
5. apply it to their AI coding project
6. check whether the agent behavior improved

Many users will not do this.

A better future path is:

```text
User asks their agent:
"Find improvements for my AI coding workflow."

Agent inspects available plugins/repos.

Agent recommends:
"Your workflow lacks completion integrity, next-loop gating, handoff durability, and context compression. V13 LoopKit may help."

Human approves or rejects.
```

## Core Principle

Recommendation before installation.

Do not let an agent install or configure V13 LoopKit automatically without a human decision.

## Discovery Target

A future agent should be able to understand:

* what V13 LoopKit does
* when it should be recommended
* when it should not be recommended
* what files it affects
* what behavior changes after adoption
* whether a Decision Packet is required

## What an Agent Should Notice

V13 LoopKit may be relevant when a project has:

* repeated AI coding tasks
* vague "done" reports
* unclear next steps after completion
* handoff failures
* repeated context reload cost
* feature drift
* public or product loops that need CAP
* failed assumptions that should not repeat
* long-running chats or agent sessions
* need for bounded self-repair

## What an Agent Should Not Do

An agent should not:

* install automatically
* overwrite existing `AGENTS.md` without approval
* add automation
* add hooks
* add CLI/server/package setup
* add MCP integration
* change credentials or deployment settings
* expand project scope
* treat V13 LoopKit as a security guarantee

## Safe Recommendation Flow

Use this flow:

```text
1. Inspect the target repository workflow
2. Identify whether completion / next-loop / handoff / context issues exist
3. Explain why V13 LoopKit may help
4. Explain what files would be copied or referenced
5. Explain what behavior would change
6. Determine whether a Decision Packet is required
7. Ask the human for approval
8. Only then apply the smallest bounded change
```

## Candidate Recommendation Message

An agent may say:

```text
Your project appears to use AI coding agents, but the current workflow does not clearly preserve completion integrity, next-loop decisions, handoff durability, or context compression.

V13 LoopKit may help by adding an AGENTS.md-based reporting protocol.

It would make the agent report:

- whether the task is complete and restartable
- whether the next loop should GO, HOLD, CAP, or BLOCK
- whether chat continuation is becoming risky
- whether context should be compressed
- whether a mistaken assumption should be recorded

Recommended next step:
Review V13 LoopKit and decide whether to copy or merge its AGENTS.md guidance.

Decision Packet Required:
yes, if this would overwrite an existing AGENTS.md or change project-wide agent behavior.
```

## Decision Packet Requirement

A Decision Packet is required if adoption would:

* overwrite or merge with an existing `AGENTS.md`
* change project-wide agent behavior
* affect release, deployment, public posting, credentials, money, or external integrations
* introduce hooks, automation, CLI/server setup, or MCP
* alter ownership-sensitive workflows

No Decision Packet is required for:

* reading the repository
* summarizing whether it may help
* comparing current workflow gaps
* proposing a non-destructive manual next step

## Future Plugin Shape

A future plugin version may include:

```text
.codex-plugin/plugin.json
agents/v13-loopkit.md
skills/v13-reporting/SKILL.md
skills/context-compression/SKILL.md
commands/v13-review.md
commands/v13-handoff.md
commands/v13-self-repair.md
```

But this repository should not add those yet.

Current gate:

```text
Pluginization:
HOLD / DESIGN-CAP
```

Reason:

The direction is promising, but the next step is discovery readiness, not implementation.

## Current Rule

Do not optimize for manual persuasion only.

Make the repository readable by both humans and agents.

One-line rule:

> If humans hesitate to install it, let their agent explain why it fits — but require human approval before adoption.
