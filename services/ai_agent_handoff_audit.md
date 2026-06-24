# AI Agent Handoff Audit

## What this is

A lightweight audit for repos using AI coding agents.

This is for teams or builders using tools such as Codex, Claude Code, Cursor, `CLAUDE.md`, `AGENTS.md`, or similar agent instruction files.

The goal is to find where AI-agent work may lose context, drift, over-expand, or become hard to restart.

## Free diagnostic

The free diagnostic gives one small, concrete review.

It checks for:

- whether always-loaded instructions are too heavy
- whether task-specific guidance is separated from base rules
- whether the repo has a restartable handoff path
- whether the next AI/human can tell what changed and what was verified
- whether there is a clear stop condition before the next loop starts
- whether the next action is bounded or open-ended
- whether important assumptions are likely to be invented later

## Output

The free diagnostic should return:

1. One observed friction point
2. One risk if left unchanged
3. One suggested 0.01 improvement
4. One relevant LoopKit copy-paste link, if useful

## Example output

```text
Observed friction:
Your CLAUDE.md is doing both always-loaded rules and task-specific memory.

Risk:
As it grows, every AI session may spend context on instructions that do not apply to the current task.

Suggested 0.01:
Keep CLAUDE.md thin and move task-specific guidance into separate files.

Useful starter:
copy-paste/claude-md-thin-base.md
```

## Paid setup path

If the user wants help beyond the free diagnostic, the paid setup can include:

- thin `CLAUDE.md` / `AGENTS.md` rewrite
- task-specific instruction split
- restartable handoff prompt
- next-action confidence check
- source-of-truth map
- first working AI-agent workflow
- one example handoff for the repo

## Target users

Good candidates:

- use Codex, Claude Code, Cursor, or agent workflows
- already have `CLAUDE.md`, `AGENTS.md`, or similar files
- run long AI coding sessions
- have repeated context loss or drift
- have handoff or restart problems
- have unclear "done means next?" behavior

Poor candidates:

- do not use AI coding agents
- only need ordinary README writing
- want full automation before basic process exists
- expect the AI to run without human review
- want mass refactoring instead of handoff discipline

## Outreach principle

Do not spam.

Do not send mass automated emails.

Use targeted, manual review first.

Only contact a repo if there is a visible, concrete reason the audit may help.

The first message should be short, specific, and useful even if they never reply.

## Outreach draft

```text
Hi - I noticed your repo appears to use AI coding-agent instructions.

One small risk I look for is when always-loaded files like CLAUDE.md / AGENTS.md start mixing base rules, task-specific notes, and handoff state.

That can make future AI sessions spend context on instructions that may not apply, and it can make handoff harder.

I built a small LoopKit / handoff pattern for this, including a Loop Library-listed exit check for AI-agent workflows.

If useful, I can do a small free audit and point out one concrete 0.01 improvement for your repo.
```

## Boundary

This service should not promise:

- automatic correctness
- full AI governance
- zero drift
- replacing human review
- instant productivity gains

It should promise:

- one concrete friction point
- one bounded improvement
- lower restart friction
- clearer handoff
- better separation between always-loaded rules and task-specific guidance
