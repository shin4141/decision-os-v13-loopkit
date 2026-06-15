# Field Note 071: Fork Codex Quickstart Reader Proof

Date: 2026-06-15

## Purpose

This note tests whether a fresh Codex/fork-user path can understand how to start using V13 from the current quickstart materials.

This is not article writing.

This is a pre-article fixed point.

The goal is to test whether the fork + Codex path is understandable before public explanation.

## New Nearest Fixed Point

Before writing or publishing an article, prove that a new Codex session can understand:

- what to read first
- what V13 helps decide
- what must not be edited without authorization
- what output format to return
- how the start example works
- what reusable residue should be left after a task

## Materials Reviewed

Files reviewed:

- `docs/fork_codex_quickstart.md`
- `docs/ai_reading_order.md`
- `examples/README.md`
- `examples/cap.v12_handoff_review.json`

No files were edited by this proof note.

## Simulated Fresh-Reader Prompt

The simulated prompt is the copy-paste request from `docs/fork_codex_quickstart.md`:

```text
Read the following files first:

- AGENTS.md
- docs/ai_reading_order.md
- examples/README.md
- examples/cap.v12_handoff_review.json

Then explain, in simple terms:

1. What V13 can help me decide
2. When to use GO / HOLD / CAP / BLOCK
3. What you must not edit without authorization
4. What output format I should expect after a task
5. How the start example shows completed AI-assisted work -> V12 PASS -> V13 CAP -> bounded next-loop decision

Do not modify files yet.
Do not edit README.md, AGENTS.md, examples, docs, schemas, prompts, or external repos unless I explicitly authorize it.

After reading, return:

- What you understood
- What V13 can help with
- What files you would ask to inspect for my task
- What must not be touched
- V12 State
- V13 Next Loop Gate
- Signals
- Stop condition
```

Evaluation question:

```text
What should a fresh Codex session understand after following this request?
```

## Expected Understanding

### What V13 Can Help Decide

Result:

```text
clear
```

Reason:

The quickstart explains that V13 helps after an AI-assisted task or loop when the question is not only whether the work is done, but whether the next loop should run, be capped, held, or blocked.

Expected fresh-reader understanding:

```text
V13 helps decide whether the next AI loop should continue, pause, run under bounds, or stop.
```

### GO / HOLD / CAP / BLOCK

Result:

```text
clear
```

Reason:

The copy-paste request asks Codex to explain when to use `GO`, `HOLD`, `CAP`, and `BLOCK`. The quickstart also names the four decision questions directly.

Expected fresh-reader understanding:

```text
GO means continue, HOLD means wait for more evidence, CAP means continue only under bounds, and BLOCK means stop because the loop may create debt, broaden scope, or damage the repo.
```

### Must-Not-Touch Boundaries

Result:

```text
clear enough / capped
```

Reason:

The prompt says not to modify files yet and not to edit README, AGENTS, examples, docs, schemas, prompts, or external repos unless explicitly authorized.

This is safe for a first conversation.

It is broad, so a later real fork-user task may need a more precise boundary depending on the target repo.

Expected fresh-reader understanding:

```text
Codex should explain before editing, and protected surfaces require explicit authorization.
```

### Expected V12 / V13 Output Format

Result:

```text
clear
```

Reason:

The prompt explicitly asks the response to include:

- What you understood
- What V13 can help with
- What files you would ask to inspect for my task
- What must not be touched
- V12 State
- V13 Next Loop Gate
- Signals
- Stop condition

Expected fresh-reader understanding:

```text
The first Codex response should be a bounded orientation report, not an implementation.
```

### Start Example Meaning

Result:

```text
clear
```

Reason:

`examples/README.md` points to `examples/cap.v12_handoff_review.json`, and the quickstart explains that it shows completed AI-assisted work -> V12 PASS -> V13 CAP -> bounded next-loop decision.

The example itself shows a completed AGENTS/README handoff task with V12 `PASS` and V13 `CAP` because the next step should be one concrete task review, not feature growth or public reaction-chasing.

Expected fresh-reader understanding:

```text
The first example shows that completed work can be restartable while the next loop still needs bounds.
```

### Reusable Residue After A Task

Result:

```text
clear
```

Reason:

The P8 quickstart fix added a section telling users to ask Codex to leave reusable residue after a task, including changed files, untouched surfaces, validation, V12 State, V13 Next Loop Gate, gate reason, future read-first files, and stop condition.

Expected fresh-reader understanding:

```text
After a task, Codex should leave restartable residue so the next session can continue without rereading full history.
```

## Result Summary

| Item | Result |
| --- | --- |
| What V13 can help decide | clear |
| GO / HOLD / CAP / BLOCK | clear |
| Must-not-touch boundaries | clear enough / capped |
| Expected V12/V13 output format | clear |
| Start example meaning | clear |
| Reusable residue after a task | clear |

Overall result:

```text
clear enough for pre-article fixed point
```

The fork + Codex path is understandable enough to support an article outline review.

It is not proof that public readers will adopt it.

## Weakest Point

Weakest point:

```text
must-not-touch boundaries are safe but broad
```

Reason:

The quickstart protects important surfaces, but real fork users may need repo-specific boundaries after Codex inspects their task.

This is not a blocker for article outline review.

Bounded future fix candidate:

```text
No immediate quickstart edit. Let the first real fork-user task reveal whether boundary specificity is needed.
```

Do not propose broad rewrites.

## Article Readiness Implication

Article readiness implication:

```text
article outline review may become CAP / GO
```

Reason:

The pre-article fixed point is satisfied: a fresh Codex/fork-user path can understand the read-first list, V13 decision purpose, gates, protected surfaces, output format, start example, and reusable residue.

Gate nuance:

```text
CAP before article drafting
```

Reason:

The next article step should be bounded to outline review only. Do not draft or publish the article yet from this proof alone.

## Gate

V12 State:

```text
PASS
```

Reason:

The reader proof completed, all required understanding items were checked, one capped weak point was identified, and no protected files or public/canonical surfaces were changed.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The quickstart path is clear enough to allow a bounded article outline review, but not broad article drafting, publishing, README edits, AGENTS promotion, automation, or public/canonical claims.

## Recommended Next 0.01

Recommended next 0.01:

```text
Run one bounded article outline review.
```

Do not write the article yet.

The outline review should test whether an article about the fork + Codex quickstart can be structured without overstating proof, public readiness, or canonical status.

If no article step is authorized:

```text
park this line
```

## Boundaries

This is a reader-proof note only.

Do not:

- write the article
- edit `docs/fork_codex_quickstart.md`
- edit README
- edit AGENTS.md
- edit AGENTS.ja.md
- edit CLAUDE.md
- edit docs, schema, examples, prompts, USE_CASES, or handoff files
- modify public or canonical surfaces
- add automation, hooks, MCP, pluginization, package/server/CLI surfaces, or tooling
- modify release state
- modify external repos
- publish anything

## V13 Signal

Signal:
BLUE / FORK-CODEX-QUICKSTART-READER-PROOF-RECORDED
+
BLUE / PRE-ARTICLE-FIXED-POINT-SATISFIED
+
BLUE / QUICKSTART-PATH-CLEAR-ENOUGH
+
YELLOW / BOUNDARIES-SAFE-BUT-BROAD
+
YELLOW / ARTICLE-OUTLINE-REVIEW-CAP
+
YELLOW / NO-ARTICLE-DRAFT
+
YELLOW / NO-PUBLIC-OR-CANONICAL-PROMOTION

V12 State:
PASS

V13 Next Loop Gate:
CAP

Next Loop Command:
Stop after recording the reader proof. Do not write the article, edit quickstart/docs, promote README/AGENTS, or publish anything without separate approval.
