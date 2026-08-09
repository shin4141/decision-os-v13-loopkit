# Field Note 129: Mutable Path Is Not Artifact Identity

Date: 2026-08-07

Lifecycle status: Canon-promoted

Primary layer: V13

Supporting layers: V9 / V11 / V12 / V14

Evidence class: Pre-Cycle operational incident / local verification completed

Canon promotion: PASS — `field_notes/125_execution_context_proof_selection.md`, Exact Artifact Identity and Mutable Paths

## Lifecycle Closure — 2026-08-09

The verified residue was promoted into the already-routed Canon operating
reference `field_notes/125_execution_context_proof_selection.md`, section
Exact Artifact Identity and Mutable Paths. Root `AGENTS.md` remains the fixed
Cycle candidate artifact and continues to route detailed continuation-proof
selection to Field Note 125.

Promoted residue:

> When exact artifact identity matters, a mutable path or observed version is
> not durable identity. Use evidence proportional to the claim, and use a new
> Forward-only As-of qualification when historical artifact equality cannot be
> established.

The re-evaluation trigger was satisfied by the preserved content-addressed
runtime, exact binary SHA-256 and version probe, recovery receipt, and bounded
Forward-only compatibility assessment recorded in
`validation/a7_creator_live_whole_flow_reentry_charter_delta_v1_1.md`. Stage D
independently rechecked the preserved artifact's type, size, mode, SHA-256,
version output, and receipt.

Countercondition: a path can contribute to identity when an authoritative
custody system makes that path immutable or separately binds it to exact
content; ordinary use that makes no exact-byte or rerun-identity claim does not
require this control.

Rollback or downgrade: if the custody evidence, exact identity checks, or
bounded compatibility assessment is shown invalid or materially overbroad,
remove or narrow the promoted paragraph through a Forward-only change and
return this Note to `Verification pending`, preserving this closure and all
historical incident evidence.

All later `Verification pending` and `HOLD` wording below is the preserved
pre-promotion disposition as of the original incident. It remains historical
evidence and does not override this current lifecycle status.

## Classification

- Artifact type: V13 Field Note
- Field Note type: Self-Application
- Status: Forward-only operational residue / verification pending
- Gate: GO for recording / HOLD for runtime migration until qualification

This Field Note is advisory memory. It does not authorize runtime migration,
Cycle 006 execution, exact P0, Candidate modification, proof-schema change,
Charter change, merge, release, or publication.

This note is not a Cycle 006 attempt result, A1–A7 evidence, behavior
qualification, or publication evidence.

## As-of Boundary

PR #36 established valid creator-owned live evidence under the runtime
available at that time.

Observed path:

```text
/Applications/ChatGPT.app/Contents/Resources/codex
```

Observed runtime:

```text
codex-cli 0.146.0-alpha.3.1
```

Observed execution identity:

```text
gpt-5.6-sol / ultra / priority / codex-cli 0.146.0-alpha.3.1
```

The PR #36 evidence remains valid under its original As-of conditions. This
note does not retroactively invalidate that proof.

## Outcome

The same absolute application path later reported:

```text
codex-cli 0.147.0-alpha.1.2
```

A bounded read-only search found no locally recoverable executable reporting
exactly:

```text
codex-cli 0.146.0-alpha.3.1
```

The earlier runtime observation was preserved as historical evidence, but the
executable artifact itself was not preserved as a recoverable object.

## Missing Closure

A historical runtime observation was later promoted into an exact future
runtime prerequisite without first establishing:

- preserved executable custody
- binary SHA-256 identity
- content-addressed storage
- recovery or reinstall path
- survival across application updates

The fixed object was a mutable application path, not a durably preserved
runtime artifact.

## Structural Distinction

```text
Path equality != artifact equality
Version observation != artifact preservation
Historical execution evidence != rerunnable runtime
```

Advisory residue:

> A mutable path should not be treated as durable artifact identity without
> separate artifact-custody evidence.

Japanese:

> 内容が更新され得る場所の観測値は、artifact custody の別証拠なしに、
> 再現可能な実体との同一性として扱うべきではない。

This statement is a verification-pending rule candidate. It is not Canon and
must not be used as execution authority. Any promotion into AGENTS.md,
templates, schemas, Gate requirements, or other operating rules requires a
separate Concept Promotion Gate.

## Forward-Only Control Candidate

A future strict runtime Gate may need to preserve the following evidence when
exact artifact equality is required:

1. a preserved executable artifact
2. binary SHA-256
3. a content-addressed storage path
4. an exact version probe from the preserved artifact
5. a documented recovery or reinstall path

This is a candidate control derived from the incident, not a currently promoted
repository requirement.

If exact historical artifact equality cannot be established, a separate new
As-of runtime qualification may be considered. That qualification requires its
own authorization and must not be inferred from this Field Note.

## Responsibility Boundary

The incident is not classified as Shin failing to manually preserve an
application binary.

Once an execution system promotes an observed runtime into a strict future
Gate, artifact custody and recovery become a closure question for that
execution system. In this incident, that closure was not established.

This responsibility statement records the observed burden boundary. It does
not assign new authority or automatically amend repository policy.

## Cycle 006 Boundary

Cycle 006 remains:

```text
UNSTARTED
```

Model invocation:

```text
0
```

Task transmission:

```text
0
```

Retry / replacement:

```text
0 / 0
```

Proof root:

```text
ABSENT
```

The next authorized work, if separately approved, would be a bounded
Forward-only assessment of whether the current runtime can be:

- captured as a real artifact
- content-addressed
- compatibility-qualified
- fixed under a new As-of
- used without changing Candidate v0.2, A1–A7, proof schemas, or one-attempt
  semantics

This Field Note does not authorize that assessment or its implementation.

## Re-evaluation Trigger

Re-evaluate this residue when the current Codex runtime has been captured with
a fixed SHA-256 and the compatibility impact from `0.146.0-alpha.3.1` to the
current runtime has been independently assessed.

Until then:

```text
HOLD / RUNTIME MIGRATION NOT YET QUALIFIED
```

## Transferable Residue

This incident produced a reusable distinction for later evaluation:

- mutable location
- observed version
- preserved artifact
- rerunnable runtime

These are separate objects and should not be collapsed without evidence.

The missing binary is not the transferable residue. The transferable residue is
the distinction that may prevent the same fixation failure in a later loop.

Promotion status remains:

```text
HOLD / VERIFICATION PENDING
```
