# AI Agent Handoff Audit

## What this is

A small audit and setup service for repos using AI coding agents.

This is for people using tools such as:

- Codex
- Claude Code
- Cursor
- `CLAUDE.md`
- `AGENTS.md`
- `CODEX.md`
- `.cursor/rules`
- custom agent workflows

The goal is to reduce AI-agent drift, restart friction, bloated always-loaded instructions, unclear completion reports, and weak handoff between sessions.

## The pain

AI agents can do a lot of work.

But long-running AI work often creates hidden costs:

- the next AI does not know what happened
- the agent says `done` but the task is not really restartable
- `CLAUDE.md` / `AGENTS.md` becomes too large
- task-specific instructions get loaded all the time
- final summaries are missing, noisy, or not useful
- the agent continues into the next task without permission
- humans cannot tell what was verified
- future AI sessions have to rediscover context from scratch

This audit looks for those failure points.

## Free diagnostic

The free diagnostic is intentionally small.

It returns:

1. one observed friction point
2. one risk if left unchanged
3. one 0.01 improvement
4. one relevant LoopKit copy-paste link, if useful

Example:

```text
Observed friction:
Your CLAUDE.md mixes always-loaded rules with task-specific memory.

Risk:
Future AI sessions may spend context on instructions that do not apply to the current task.

0.01 improvement:
Keep CLAUDE.md thin and move task-specific instructions into separate files.

Useful starter:
copy-paste/claude-md-thin-base.md
```

## Paid Light Audit

Draft price range:
`15,000-30,000 JPY`

The Paid Light Audit reviews one repo or one agent workflow.

Deliverables:

- one short audit note
- friction map
- restart / handoff risk
- instruction-bloat risk
- one recommended 0.01 improvement
- one suggested prompt or gate
- one short implementation direction

Good for:

- people who already use AI coding agents
- repos with `CLAUDE.md`, `AGENTS.md`, `CODEX.md`, or agent workflows
- builders who feel their AI workflow is working but messy
- people who want a concrete first fix, not a large consulting project

Not included:

- full repo refactor
- full automation setup
- writing all documentation
- maintaining the workflow
- guaranteed productivity increase
- replacing human review

## Paid Setup

Draft price range:
`50,000-100,000 JPY`

The Paid Setup turns the audit into a minimal working AI-agent operation layer.

Possible deliverables:

- thin `CLAUDE.md` / `AGENTS.md` base
- task-specific instruction split
- Restartable Handoff prompt
- Next-Action Confidence Check
- source-of-truth map
- one example handoff
- one example next-loop gate
- one first-use instruction for the repo's AI agent

Good for:

- small teams
- solo builders
- AI-heavy repo maintainers
- people using Codex / Claude Code / Cursor for long sessions
- people who want the repo to be easier for future AI sessions to restart

Not included:

- building product features
- coding full implementation unless separately scoped
- setting up unsafe autonomous execution
- mass automation
- growth hacking
- marketing strategy
- replacing engineering judgment

## What I need from you

Send one of the following:

- public GitHub repo URL
- relevant `CLAUDE.md` / `AGENTS.md` / `CODEX.md`
- issue or PR where AI-agent workflow broke down
- example of a bad handoff / missing summary / agent drift
- description of your current Codex / Claude Code / Cursor workflow

Best first input:

```text
Here is my repo.
I use [Codex / Claude Code / Cursor].
I want to reduce [handoff friction / context bloat / agent drift / unclear completion / restart cost].
Please give me one 0.01 improvement.
```

## What you get

You get a small, concrete improvement path.

The goal is not to add more process.

The goal is to make your AI-agent workflow:

- easier to restart
- less likely to drift
- lighter on context
- clearer at task completion
- safer before the next loop starts
- easier for another AI or human to continue

## Why LoopKit

LoopKit is based on Decision-OS V12/V13:

- V12: is the current task actually complete and restartable?
- V13: should the next loop run, and under what gate?

Two V13-derived loops have been listed in Forward Future's Loop Library:

- `The next-action confidence check`
- `The restartable handoff loop`

This service applies those patterns to a real repo or workflow.

## Boundaries

This service does not promise:

- automatic correctness
- guaranteed adoption
- zero drift
- full AI governance
- replacing human review
- instant productivity gains

It does promise:

- one concrete friction point
- one bounded improvement
- clearer handoff
- better restartability
- less ambiguity before the next AI action

## Status

Draft offer.

Not yet publicly launched.

Pricing is provisional.

No mass outreach.
No automation.
No guaranteed result claims.
