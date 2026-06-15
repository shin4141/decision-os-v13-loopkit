# Field Note 072: AGENTS Context Bloat Article Outline Review

Date: 2026-06-15

## Purpose

This note reviews an outline for a beginner-facing article explaining why `AGENTS.md` / `CLAUDE.md` can become too heavy when everything is always loaded, and how V13 separates always-read rules from reconnectable manuals.

This is an outline review only.

It does not write the article.

It does not publish anything.

It does not edit README, AGENTS, docs, schema, examples, prompts, USE_CASES, handoff files, public surfaces, canonical surfaces, automation, hooks, MCP, pluginization, package/server/CLI surfaces, release state, or external repos.

## Article Purpose

The article should explain:

1. the current common operation

   Many AI coding users put agent instructions into `AGENTS.md`, `CLAUDE.md`, or similar project-level files.

2. the risk

   If every rule, memory, example, policy, workflow, and historical lesson is always loaded, the instruction surface becomes heavy.

3. V13's difference

   V13 separates always-read operating rules from reconnectable manuals, field notes, handoffs, examples, and quickstarts.

4. user benefit

   Users can keep the agent controllable without forcing every piece of context into the always-read file.

5. GitHub introduction timing

   Introduce the repo only after the reader understands the pain and benefit.

## Target Reader

Target readers:

- AI coding agent users
- people using `AGENTS.md` / `CLAUDE.md`
- people starting to feel context bloat, cost, or over-edit risk

Reader pain:

```text
My agent instructions are useful, but the always-loaded context is getting heavy.
```

## Core Message

Core message:

```text
AGENTS.md is useful, but not all memory should be always-read.
```

Supporting points:

- `AGENTS.md` is useful.
- `CLAUDE.md` is useful.
- Always-read rules are good for stable operating boundaries.
- But if everything is always loaded, context becomes heavy.
- Heavy context can increase cost, confusion, buried rules, stale assumptions, and over-implementation.
- Some memory should be reconnectable instead of always-read.
- V13 separates always-read rules from reconnectable manuals.

## Article Outline

### 1. Most People Put Agent Rules Into `AGENTS.md` / `CLAUDE.md`

Purpose:

Open with a familiar operation.

Key point:

```text
Project-level instruction files are useful because they give the agent stable rules.
```

### 2. This Works At First

Purpose:

Avoid attacking the current practice.

Key point:

```text
Small instruction files improve consistency and reduce repeated prompting.
```

### 3. Then The File Grows

Purpose:

Name the transition from useful instruction surface to overloaded memory surface.

Key point:

```text
Rules, examples, lessons, decisions, workflows, and history start accumulating in one always-loaded place.
```

### 4. The Risk

Purpose:

Explain why bloat matters.

Risks:

- cost
- confusion
- buried rules
- over-implementation
- stale context
- weaker restartability
- more effort to identify what matters now

Key point:

```text
The problem is not AGENTS.md. The problem is treating all memory as always-read memory.
```

### 5. My Current Approach: Keep AGENTS Small And Externalize Manuals

Purpose:

Introduce the alternative.

Key point:

```text
Keep the always-read layer small, then reconnect to manuals, examples, handoffs, and field notes only when the task requires them.
```

### 6. V13 Components

Purpose:

Explain the repo shape without making the article a repo tour too early.

Components:

- `AGENTS.md`: always-read operating rule
- field notes: bounded proof and observations
- handoff: restart anchor
- examples: concrete loop records
- quickstart: fork-user Codex first request
- transfer packet: parked pattern for external task handoff

Key point:

```text
V13 is organized so the agent can reconnect to the right manual instead of loading every detail all the time.
```

### 7. What A Fork User Can Ask Codex To Read First

Purpose:

Use the proven pre-article fixed point from Field Note 071.

Suggested read-first set:

- `AGENTS.md`
- `docs/ai_reading_order.md`
- `examples/README.md`
- `examples/cap.v12_handoff_review.json`

Key point:

```text
The first Codex request should be orientation and gating, not immediate editing.
```

### 8. GitHub Link / Repo Introduction

Purpose:

Introduce the repo only after the pain and benefit are clear.

Framing:

```text
This is an experimental LoopKit, not a finished product.
```

## What Not To Say

Do not say:

- this is the only way
- `AGENTS.md` is bad
- `CLAUDE.md` is bad
- V13 is product-ready
- V13 is proven for all users
- V13 is uniquely original in every part
- everyone should migrate
- other users are doing it wrong
- automation or pluginization is ready

Tone rule:

```text
Explain the tradeoff without attacking the common practice.
```

## GitHub Mention Strategy

GitHub mention strategy:

```text
pain first, repo second
```

Rules:

- The main article body should explain the pain first.
- The GitHub link should appear after the reader understands the benefit.
- The repo should be framed as an experimental LoopKit.
- Do not frame the repo as a finished product.
- Do not turn the article into public-readiness proof.

## Gate

V12 State:

```text
PASS
```

Reason:

The outline review defines article purpose, target reader, core message, section structure, prohibited claims, and GitHub mention strategy without writing or publishing the article.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The outline is clear enough for a separate bounded article draft step, but the next loop must remain capped: no publishing, no README edits, no AGENTS promotion, no product-ready claim, and no broad public copy expansion.

## Recommended Next 0.01

Recommended next 0.01:

```text
If separately authorized, draft the article in one bounded step from this outline.
```

Cap for that future step:

- draft only
- no publishing
- no repo edits
- no README edits
- no AGENTS promotion
- no public/canonical claims
- no automation/pluginization

If the draft becomes too promotional:

```text
HOLD
```

If the outline feels weak:

```text
revise outline before drafting
```

## Boundaries

This is an outline review only.

Do not:

- write the article in this note
- publish anything
- edit README
- edit AGENTS.md
- edit AGENTS.ja.md
- edit CLAUDE.md
- edit docs, schema, examples, prompts, USE_CASES, or handoff files
- modify public or canonical surfaces
- add automation, hooks, MCP, pluginization, package/server/CLI surfaces, or tooling
- modify release state
- modify external repos

## V13 Signal

Signal:
BLUE / AGENTS-CONTEXT-BLOAT-ARTICLE-OUTLINE-REVIEW-RECORDED
+
BLUE / BEGINNER-FACING-ANGLE-DEFINED
+
BLUE / PAIN-FIRST-GITHUB-SECOND-STRATEGY-SET
+
YELLOW / ARTICLE-DRAFT-CAP
+
YELLOW / NO-PUBLISHING
+
YELLOW / NO-README-OR-AGENTS-EDIT
+
YELLOW / NO-PUBLIC-OR-CANONICAL-PROMOTION

V12 State:
PASS

V13 Next Loop Gate:
CAP

Next Loop Command:
Stop after recording the outline review. Do not write or publish the article without separate approval.
