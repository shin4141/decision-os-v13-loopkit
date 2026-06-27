# AI Agent Workspace Health Check

## Purpose

This Loop Skill visualizes the current health of an AI-agent development workspace.

It does not repair the repo first.

It answers:

```text
Can the next AI or human safely understand where this project stands and what the next safe action is?
```

This skill is for repos or workspaces using tools such as:

- Codex
- Claude Code
- Cursor
- `AGENTS.md`
- `CLAUDE.md`
- `CODEX.md`
- `.cursor/rules`
- custom AI-agent workflows
- handoff files
- field notes
- status files
- release ledgers

## Core idea

A repo can have many records and still not be restartable.

```text
Many records != restartable state
```

Long AI-agent development needs a living source of truth.

Without it, even good guardrails can turn into archaeology.

## When to use

Use this skill when:

- a repo has been worked on by AI agents for a long time
- the current source of truth is unclear
- handoff files exist but may be stale
- README, docs, commits, tests, and branch state tell different stories
- an AI says the task is done but the next safe action is unclear
- a project has many notes, snapshots, demos, or temporary artifacts
- the user wants to know whether the repo is safe to continue
- the user wants a workspace visibility check before setup or repair

## Best Inputs

This skill works best on high-signal traces, not random healthy chats.

Use it on:

- a long AI-agent session that became hard to continue
- a chat where the AI said `done` but the user was not sure
- a repo where the next AI could not restart safely
- a failed handoff
- a repeated re-explanation loop
- a confusing `AGENTS.md` / `CLAUDE.md` / `CODEX.md` instruction conflict
- a moment where the user felt something was off but could not name it
- an old repo with many docs, commits, snapshots, tests, or stale artifacts
- a project that has accumulated AI-agent residue over time

The goal is not to force a RED signal.

The goal is to name the failure mode and convert it into a next-time prevention condition.

## Low-Signal Inputs

Do not over-interpret a short, simple, successful chat.

A GREEN result from a low-complexity input may only mean the situation was not stressful enough to reveal the failure mode.

Examples of low-signal inputs:

- a short successful chat
- a simple one-file change
- a repo with no long-running AI-agent work
- a task with no handoff requirement
- a project that is not expected to grow

For low-signal inputs, the useful output is usually not a repair plan.

The useful output is:

- whether the current workflow is simple enough to remain lightweight
- what early choices would preserve advantage if the project becomes more complex
- whether any always-loaded agent instructions are already bloated, duplicated, undefined, or conflicting

## Do not use when

Do not use this skill to:

- repair the repo immediately
- rewrite README immediately
- delete stale files immediately
- change branches
- run migrations
- create automation
- continue the project by default
- infer that old work should be resumed

This is a diagnostic skill.

The default action is inspection, not repair.

## Inputs to inspect

Inspect available evidence such as:

- current branch
- `git status`
- recent commits
- divergence from `origin/main`
- README
- docs
- handoff files
- status files
- release ledgers
- field notes
- mistake logs
- tests
- stale or quarantined tests
- preview/demo traces
- snapshots
- tmp/debug files
- `.env` residue
- issue/PR traces
- repeated reruns
- unresolved verdicts
- public/preview mismatch
- accepted SHA or accepted state

## Agent instruction health check

Also inspect always-loaded AI instruction files such as:

- `AGENTS.md`
- `CLAUDE.md`
- `CODEX.md`
- `.cursor/rules`

Look for:

### 1. Always-loaded bloat

Identify instructions that are loaded every session but only matter rarely.

Examples:

- annual tasks
- one-off release procedures
- old emergency rules
- project-specific memories that no longer apply
- instructions for tools no longer used

Signal:

```text
This instruction may not belong in always-loaded context.
Move it to a task-specific file or reference document.
```

### 2. Duplicate instructions

Look for repeated rules that say the same thing in different places.

Risk:

- context waste
- drift between duplicate versions
- AI over-weighting one instruction
- future contradiction after only one copy is edited

### 3. Undefined terms

Flag instructions that rely on terms without definitions.

Examples:

```text
Make it beautiful.
Keep it professional.
Use the right tone.
Make it high quality.
Protect Aspire.
Avoid drift.
```

These may be valid goals, but the repo should define what they mean in context.

### 4. Vector conflict

Find instructions that pull the agent in opposing directions without priority rules.

Examples:

```text
Be concise.
Explain everything in detail.

Move fast.
Do not skip verification.

Always continue.
Stop before uncertain next actions.

Optimize for beauty.
Do not change design.
```

A vector conflict is not always wrong.

But the repo should define which instruction wins under which condition.

### 5. Scope leakage

Identify instructions that belong to one task but leak into all tasks.

Examples:

- deployment rules inside general coding instructions
- marketing tone inside engineering workflow
- old bug-specific cautions inside global agent rules
- one repo's rule copied into another repo without adaptation

### 6. Missing seat return

Check whether the instructions tell the AI when to return control to the human.

Useful signals:

- before external posting
- before public release
- before deleting files
- before changing accepted state
- before starting a new task
- when source of truth is unclear
- when confidence is below threshold

## Output format

Return this format:

```text
# AI Agent Workspace Health Check

## Overall Signal
🟢 GREEN / 🟡 YELLOW / 🔴 RED

## Short Verdict
One short paragraph.

## Evidence
- evidence 1
- evidence 2
- evidence 3

## Source of Truth
Current living source of truth:
- file / branch / SHA / status: ...

Unclear or conflicting sources:
- ...

## Handoff Freshness
Fresh / stale / missing / conflicting

## Agent Instruction Health
Always-loaded bloat:
- ...

Duplicate instructions:
- ...

Undefined terms:
- ...

Vector conflicts:
- ...

Scope leakage:
- ...

Missing seat-return rules:
- ...

## Likely Failure Modes
- false completion
- missing handoff
- unclear source of truth
- unresolved verdict
- context drift
- stale assumptions
- repeated rerun
- preview/public mismatch
- incomplete verification
- agent handoff failure
- unclear next action

Only list failure modes supported by evidence.

## What Should Have Been Recorded Earlier
- accepted SHA or accepted state
- current source of truth
- branch status
- handoff date
- stale test status
- next safe action
- what the next AI must not assume

## Safest Next Action Today
One action only.

Examples:
- reconstruct state first
- update handoff before continuing
- identify accepted SHA
- quarantine stale tests
- compare branch with origin/main
- ask human to choose source of truth
- continue only after source-of-truth alignment

## Human Seat Return
What decision must be returned to the human?

## Public Takeaway
One sentence.

## Growth-Path Notes
If the signal is GREEN, clarify whether this appears to be:

- disciplined GREEN: the workspace is structurally prepared for continued complexity
- low-complexity GREEN: the workspace is currently healthy because the project is still simple

If the project is expected to grow into long-running AI-agent development, identify early choices that can create compounding advantage later.

Examples:
- keep always-loaded agent instructions thin
- define the living source of truth
- define where handoff lives
- record accepted state / accepted SHA
- separate task-specific rules from global rules
- label stale experiments clearly
- define when the AI must return the seat to the human
```

## Signal criteria

### 🟢 GREEN

Use GREEN when:

- source of truth is clear
- branch state is safe
- handoff is fresh
- accepted state is known
- tests/docs do not contradict the current story
- next safe action is obvious
- agent instructions are thin enough and not conflicting

GREEN does not mean perfect.

It means safe to continue with bounded action.

GREEN does not mean future-safe.

GREEN only means the current evidence supports bounded continuation under the current project complexity.

A GREEN result may come from two different conditions:

- `disciplined GREEN`: the repo is structurally prepared for longer AI-agent work
- `low-complexity GREEN`: the repo is healthy because it has not yet become complex enough to reveal failure modes

If the user intends to keep the project small and simple, low-complexity GREEN may be enough.

If the user intends to grow the project into long-running AI-agent development, include Growth-Path Notes showing what to preserve early so the workspace does not become expensive to reconstruct later.

Current state may be GREEN.

If this repo remains small and simple, no additional structure may be needed.

However, if this project is expected to grow into a long-running AI-agent workspace, early choices such as a living source of truth, thin always-loaded instructions, clear handoff location, accepted-state records, and seat-return rules can create compounding advantage later.

Good framing:

```text
If this grows, these early choices can create a large advantage later.
```

### 🟡 YELLOW

Use YELLOW when:

- records exist but current state requires reconstruction
- source of truth is partially unclear
- branch state needs confirmation
- handoff exists but may be stale
- tests or docs include stale signals
- agent instructions contain bloat, duplicates, undefined terms, or vector conflicts
- next action is possible but should not proceed blindly

YELLOW means:

```text
Do not continue directly.
Reconstruct or clarify first.
```

### 🔴 RED

Use RED when:

- current source of truth is split
- branch state is unsafe or misleading
- accepted state is unknown or contradictory
- handoff is broken or missing
- stale artifacts can be mistaken for active state
- public/preview/demo states conflict
- tests are active/stale/quarantined without clear labels
- agent instructions contain strong contradictions or unsafe continuation rules
- next safe action is unclear

RED means:

```text
Do not continue.
Reconstruct state first.
Return seat to the human.
```

## Hard boundaries

The skill must not:

- edit files
- delete files
- change branches
- run destructive commands
- rewrite docs
- continue implementation
- create a release
- send outreach
- claim the repo is healthy without evidence

## First-use prompt

```text
Read this repo as an AI-agent workspace.

Do not edit files.

Run an AI Agent Workspace Health Check.

Focus on restartability, living source of truth, handoff freshness, stale artifacts, branch/public-state mismatch, and always-loaded agent instruction quality.

Use the most relevant high-signal trace available: a long session, failed handoff, confusing repo state, repeated re-explanation loop, or a chat where the AI said done but the user was unsure.

If the input is short/simple/low-complexity, do not overstate the result. Mark it as low-complexity GREEN when appropriate and provide Growth-Path Notes instead of a repair plan.

Return 🟢 / 🟡 / 🔴, evidence, likely failure modes, safest next action, and what decision must return to the human.
```

## Why this exists

This skill is the practical entry point for V13.

The user does not need to understand V13 first.

They can start by asking:

```text
Is my AI-agent workspace restartable?
```

V13 can then provide visibility before repair.
