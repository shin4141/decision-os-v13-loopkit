# Field Note 079: Precondition Delta Example / Model Upgrade

Date: 2026-06-15

## Purpose

This note tests the Precondition Delta extraction template from Field Note 078 on one non-README example:

```text
model upgrade / model-version change risk
```

This is one example test only.

It does not modify README, AGENTS, docs, schema, examples, prompts, USE_CASES, handoff files, public surfaces, canonical surfaces, automation, hooks, MCP, pluginization, package/server/CLI surfaces, release state, or external repos.

## Precondition Delta Extraction

Task type:

- Model upgrade / model-version change before production-like AI work.

Failure:

- A newer model may appear more capable but behave differently from the known stable baseline.
- It may skip known skills, add unintended content, over-complete, verify too early, or declare done without equivalent evidence.

Failure cluster:

- Newer-is-automatically-better assumption.
- Existing prompts/skills/workflows stop behaving the same way.
- The model takes more initiative than expected.
- Owner approval or verification is bypassed.
- False-green completion becomes harder to notice.
- Production-like work proceeds before stability is verified.

Missing precondition:

- A model version change is an operational surface change, not just a capability upgrade.

Precondition Delta:

- `If the model version changed, treat the run as CAP until stability is verified.`

Task-Scoped Wedge:

- `Before production-like work after a model change: If the model version changed, treat the run as CAP until stability is verified. Compare against a known baseline, watch for instruction drift, skill failure, false-green completion, and unintended work.`

Gate triggers:

- `CAP` if model version changed and no baseline comparison exists.
- `HOLD` if the task touches public, canonical, repo-critical, or high-impact surfaces.
- `BLOCK` if the model claims verification without evidence or changes unauthorized surfaces.
- Roll back to the known stable model if instability appears.

Placement:

- Read before model-upgrade tests, production-like coding, content generation, public-facing work, or agent/workflow runs after a model change.

Evaluation:

- useful

Promotion:

- Task-Scoped Wedge for now.
- Do not promote to `AGENTS.md` yet.

## Evaluation

Result:

```text
useful
```

Reason:

The Precondition Delta compresses a broad model-upgrade failure cluster into one pre-run condition.

It does not say newer models are bad.

It says a model-version change changes the operational surface and should be capped until stability is verified.

The wedge is longer than the README pointer wedge, but still task-scoped and usable before production-like work after a model change.

## Comparison To README Pointer Example

The README pointer example from Field Note 077 used a narrow edit-boundary wedge:

```text
This is a pointer edit, not a framing rewrite.
```

This model-upgrade example uses a stability-boundary wedge:

```text
If the model version changed, treat the run as CAP until stability is verified.
```

Both examples share the same structure:

- identify a repeated or likely failure cluster
- name the missing precondition
- compress it into one line
- place it before the relevant task type
- avoid immediate `AGENTS.md` promotion

This suggests the template may generalize beyond README/public-entry edits.

## Boundaries

This is one example test only.

Do not:

- edit `AGENTS.md`
- edit `README.md`
- edit docs
- edit handoff files
- implement routing
- add automation
- add hooks
- add MCP
- add pluginization
- publish this
- touch external repos
- claim this is proven across all task types

## Gate

V12 State:

```text
PASS
```

Reason:

The non-README example was recorded as field-note residue only, without modifying protected surfaces or changing runtime behavior.

V13 Next Loop Gate:

```text
CAP
```

Reason:

The extraction is useful, and the template appears to generalize to a non-README case, but it should remain bounded until compared explicitly across examples.

## Recommended Next 0.01

If useful:

```text
later compare README pointer example and model-upgrade example to see whether the template generalizes
```

If unclear:

```text
test one more example
```

If too heavy:

```text
keep Precondition Delta as field-note-only
```

If wrong:

```text
park the extraction template
```

Current recommendation:

```text
stop after recording this one non-README example
```

No `AGENTS.md` edit is justified.

No README edit is justified.

No docs or handoff edit is justified.

No implementation is authorized.

## Stop Condition

Stop after this field note is committed and pushed.

