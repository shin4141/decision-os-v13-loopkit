# Fork + Codex Quickstart

This guide is for someone who forks this repo and wants to ask Codex to use V13 without guessing what to read first.

This is a post-interest setup guide, not the first showroom. Before forking,
the user can explore the public [External Intelligence Quest Board](external_intelligence_onboarding.md)
with no clone, Codex project attachment, setup, or file change. Use this guide
only after the user selects a Quest or says they want to try one.

If your goal is to build a growing external intelligence surface for your own
AI after that choice, continue here.
The broader [Codex Tutorial Guide](codex_tutorial_guide.md) is an on-demand map,
not a required first lesson.

## Open the repository and ask naturally

1. Fork or clone this repository.
2. Open the repository root in Codex or Claude Code.
3. Ask:

```text
外部知能を使ってみたい。何から始めればいい？
```

The tiny `AGENTS.md` router sends that request to the External Intelligence
Quest Board. `CLAUDE.md` already sends Claude Code to `AGENTS.md`. No long
copy-paste prompt or first-file instruction is required.

The upstream `docs/current_signal.md`, `handoff/current_codex_handoff.md`,
trajectory, and validation records describe upstream work, not the fork
user's current state. Do not read them during first contact unless the user is
specifically resuming or evaluating that upstream work.

Codex should show the Quest Board first and wait. After the user chooses or
asks what fits, it should use the current conversation and repository before
asking questions, ask only for missing facts that would change the next step,
and avoid repeating concepts the user already operates.

In a fork, the Decision Owner is the fork's actual owner or maintainer, not
automatically Shin from the upstream canonical repository. Do not attach a
full completion footer to each in-progress tutorial question; close the
bounded onboarding once after the selected use and restart point.

The first onboarding is complete when that one structure has been tried once
and a restart point remains. It is not measured by how many V13 concepts were
introduced.

When the user wants to graduate from the tutorial, present
`KEEP / MANUAL / REMOVE / NOT NOW`. Never remove the router or tutorial-only
surfaces automatically. `MANUAL` and `REMOVE` require an explicit file-change
approval and must preserve memory, notes, handoff, reusable intelligence,
rules, and V12/V13 operation.

## What V13 can help with

V13 helps after an AI-assisted task or loop, when the question is not only "is it done?" but:

* should the next loop run?
* should it be capped?
* should it be held until more evidence exists?
* should it be blocked because it may create debt, broaden scope, or damage the repo?

These concepts do not all need to be introduced at first contact. For example,
if the current friction is only session restart, a small handoff may be enough.

## Attach LoopKit to external goals

LoopKit does not need to replace another `/goal`, loop, or automation.

If an external prompt is good at making a coding agent execute work, keep it. Attach LoopKit at the boundary after the work so the result can be judged, capped, and restarted.

Use this as an exit gate after external goals or loops:

```text
V12 State: PASS / DELAY / BLOCK / UNKNOWN
V13 Next Loop Gate: GO / HOLD / CAP / BLOCK

Reason:
<why this gate applies>

Next Authorized Action:
<one bounded action or none>

Not Authorized:
<up to 3 boundaries>

Decision Packet Required:
yes / no

Decision Owner:
<one line>

Completion Line:
<one line>

Evidence:
<what was verified>

What changed:
<short summary>

Reusable residue:
<none, or one sentence>

Recommendation:
Low / Medium / High / Owner Approval Required

Suggested placement:
handoff / field_notes / examples / docs / AGENTS_candidate_HOLD / no record

Owner choices:
A. Record the minimal residue
B. Skip for now

Stop condition:
<why this loop stops here>
```

Do not put every external loop rule into `AGENTS.md`.

Use `AGENTS.md` for minimal always-on rules only. Use docs, examples, and handoff for on-demand guidance.

## After a task, ask for reusable residue

After Codex finishes a task, ask it to leave a small reusable residue, not only a completion summary.

Useful residue may include:

* what was changed
* what was not touched
* validation or checks performed
* V12 State
* V13 Next Loop Gate
* why the next loop is GO / HOLD / CAP / BLOCK
* what a future Codex session should read first
* stop condition

This helps the next session restart without rereading the full history.

A task summary is not automatically reusable intelligence. Preserve it as a
candidate or current restart state until repeated or independent evidence and
the required promotion authority exist.

## Where to record things

Before or after a task, decide where the residue belongs:

* `field_notes/`: observations, failures, near-misses, and reusable lessons that are not yet canonical.
* `handoff/current_codex_handoff.md`: the current restart point for a future Codex or human session.
* `examples/`: reusable examples that teach a pattern.
* `AGENTS.md`: minimal always-on rules only. Treat promotion to AGENTS.md as HOLD unless separately authorized.
* `README.md`: public entrypoint only. Do not use it as a work log.
* No record: tiny, reversible work with no reusable lesson or restart need.

Before starting a non-trivial task, Codex should state the expected record target:
`none`, `field_note`, `handoff`, `example`, or `AGENTS_candidate_HOLD`.

## When to read each surface

Do not read every surface for every task. Use the smallest surface that matches the current need.

* `AGENTS.md`: read as the always-on rule surface before repo work.
* `README.md`: read when you need the public entrypoint or project positioning.
* `docs/external_intelligence_onboarding.md`: read when a user wants their own
  AI memory or a capacity-aware first use.
* `docs/fork_codex_quickstart.md`: read when onboarding a fork user or choosing where residue should go.
* `docs/codex_tutorial_guide.md`: read when the user wants an interactive first-run walkthrough.
* `handoff/current_codex_handoff.md`: read when resuming prior work or checking the current restart anchor.
* `examples/`: read only when a similar reusable pattern is needed.
* `field_notes/`: read only when investigating a related failure, observation, or non-canonical lesson.

If the current task is tiny, reversible, and has no reusable residue, no extra memory surface is required.

## When to add one more structure

Add another structure only when current use exposes a real need: the current
surface cannot resolve the friction, a failure repeats, restart or retrieval
cost becomes material, multiple observations make a rule candidate worth
reviewing, or externalization requires another Gate.

Otherwise stop and leave a return condition, for example:

```text
今はhandoffだけ使います。新しいsessionで同じ説明を繰り返す負担がまだ
残るなら、その時にmemory構造を一つ追加で検討します。
```

## When residue is detected

Do not ask the Owner a heavy open-ended question like "Should I add this?"

When reusable residue is detected, the coding agent should report it with a recommendation level, expected effect, suggested placement, and two choices.

Recommendation levels:

* `Low`: mention in the report only. No record may be needed.
* `Medium`: recording may reduce future re-onboarding cost or prevent a small repeat mistake.
* `High`: recording is likely to improve restartability, safety, or repeated task quality.
* `Owner Approval Required`: needed for `AGENTS.md` promotion, new files, automation, routing, or canonical rule changes.

Use this format:

```text
Detected reusable residue:
<one sentence>

Recommendation:
Low / Medium / High / Owner Approval Required

Expected effect:
<one sentence>

Suggested placement:
handoff / field_notes / examples / docs / AGENTS_candidate_HOLD / no record

Owner choices:
A. Record the minimal residue
B. Skip for now
```

Default placements:

* Current restart need -> `handoff/current_codex_handoff.md`
* Non-canonical lesson, failure, or observation -> `field_notes/`
* Reusable task pattern -> `examples/`
* Onboarding or manual guidance -> `docs/`
* Always-on safety rule -> `AGENTS_candidate_HOLD`
* Tiny reversible task with no reusable lesson -> `no record`

## Start example

Start with:

`examples/cap.v12_handoff_review.json`

It shows a completed AI-assisted handoff review where the work is V12 PASS, but the next loop is V13 CAP because further expansion needs bounds.

## Boundary

This quickstart does not authorize Codex to edit files.
It only helps a fork user start the conversation safely.
