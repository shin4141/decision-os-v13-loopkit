# Field Note 128: Mutable Path Is Not Artifact Identity

## Classification

- Artifact type: V13 field note
- Field note type: Self-Application
- Root layer: V13
- Adjacent layers: V9 As-of / V11 Reconnectable Forgetting / V12 Completion Integrity / V14 Resource Justice
- Status: Forward-only operational residue
- Gate: GO for recording / HOLD for runtime migration until qualification

This note is not a Cycle 006 attempt result, Candidate modification, A1–A7 evidence, behavior qualification, or publication evidence.

## 1. As-of Boundary

PR #36 established valid creator-owned live evidence under the runtime available at that time.

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

The PR #36 evidence remains valid under its original As-of conditions. This note does not retroactively invalidate that proof.

## 2. Outcome

The same absolute application path later reported:

```text
codex-cli 0.147.0-alpha.1.2
```

A bounded read-only search found no locally recoverable executable reporting exactly:

```text
codex-cli 0.146.0-alpha.3.1
```

The earlier runtime observation was preserved as historical evidence, but the executable artifact itself was not preserved as a recoverable object.

## 3. Missing Closure

A historical runtime observation was later promoted into an exact future runtime prerequisite without first establishing:

- preserved executable custody
- binary SHA-256 identity
- content-addressed storage
- recovery or reinstall path
- survival across application updates

The fixed object was a mutable application path, not a durably preserved runtime artifact.

## 4. Structural Distinction

```text
Path equality != artifact equality
Version observation != artifact preservation
Historical execution evidence != rerunnable runtime
```

Canonical rule:

> A mutable path must not be treated as a durable artifact identity.

Japanese:

> 内容が更新され得る場所の観測値を、再現可能なartifactとの同一性として固定してはならない。

## 5. Forward-Only Rule

When an exact runtime identity becomes a future execution Gate, fixation must include all of the following:

1. a preserved executable artifact
2. binary SHA-256
3. a content-addressed storage path
4. an exact version probe from the preserved artifact
5. a documented recovery or reinstall path

If these conditions are absent, the system must not require exact historical artifact equality.

It must instead use a new As-of runtime qualification process.

## 6. Responsibility Boundary

The failure was not that Shin failed to manually preserve an application binary.

Once an execution system promoted an observed runtime into a strict future Gate, artifact custody and recovery became part of the system's operational closure.

That closure was missing.

## 7. Cycle 006 Boundary

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

The next action is not a retry.

The next action is a bounded Forward-only assessment of whether the current runtime can be:

- captured as a real artifact
- content-addressed
- compatibility-qualified
- fixed under a new As-of
- used without changing Candidate v0.2, A1–A7, proof schemas, or one-attempt semantics

## 8. Re-evaluation Trigger

Re-evaluate when the current Codex runtime has been captured with a fixed SHA-256 and the compatibility impact from `0.146.0-alpha.3.1` to the current runtime has been independently assessed.

Until then:

```text
HOLD / RUNTIME MIGRATION NOT YET QUALIFIED
```

## 9. Transferable Residue

This incident changes the next loop by adding an artifact-custody invariant to any future strict runtime Gate.

The residue is therefore not the missing binary itself.

The residue is the rule that prevents a mutable location from being mistaken for a durable execution identity again.
