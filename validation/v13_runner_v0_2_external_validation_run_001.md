# V13 Runner v0.2 External Validation Run 001

## Status

```text
External Validation Run 001:
PASS / COMPLETE

Runner:
V13 RUNNER V0.2 / UNCHANGED

Canonical As-of:
49c686bb21df8a89895e0200246b5dd8636cf502

Pre-activation V12 Completion Integrity Guard:
PASS / READ-ONLY RUN-SPECIFIC DETERMINATION

Historical V12 backfill:
NONE

Completed cases:
3 OF 3

Distinct project lineages:
3 OF 3

Scan executions:
12 OF 12 / EXIT 0

JSON repeated-byte determinism:
PASS / 3 OF 3

Text repeated-byte determinism:
PASS / 3 OF 3

Recommendation contract:
PASS / 3 OF 3

Target no-write proof:
PASS / 3 OF 3

USEFUL:
1

PARTIALLY USEFUL:
1

NOT USEFUL:
1

MISLEADING:
0

Pre-scan substitutions:
0 OF 2

Evaluator:
CODEX 13-9

Evaluator independence:
INTERNAL EVALUATION ON EXTERNAL REPOSITORIES / INDEPENDENCE NOT ESTABLISHED

External contact:
NONE

Attributable result publication:
NONE

Runner defect:
NONE OBSERVED

Authority Envelope:
V13 RUNNER V0.2 EXTERNAL VALIDATION RUN 001 / CONSUMED / CLOSED

Remaining authorized loops:
0

Current Gate:
HOLD — EXTERNAL VALIDATION RUN 001 CLOSED / NO NEXT AUTHORIZED ACTION

Active Branch:
none

Codex Next Authorized Action:
none

Decision Owner:
Shin
```

## Validation Question

This run tested whether the unchanged `decision-os scan` command produces
bounded, deterministic, non-misleading evidence on three real public
repositories outside the V13 development lineage.

The run did not test conversion, demand, revenue, repository safety, software
quality, task completion, workflow failure, or whether a paid Audit is
required.

## Privacy and Attribution Boundary

The durable receipt uses only the preregistered labels `Case A`, `Case B`, and
`Case C`. It does not contain repository owner/name, URL, commit SHA, local
path, file body, dirty filename, raw scan payload, credential, or private
observation.

The three targets were public, unauthenticated, from distinct project
lineages, and had no known Shin relationship in the recorded V13 surfaces.
No owner was contacted. No Issue, PR, comment, outreach, email, lead,
telemetry, or attributable result publication occurred.

## Fixed Cases

### Case A — Small Ordinary Repository

Preregistered structure:

- no allowlisted AI instruction surface;
- no bounded restart surface;
- no V13 state surface.

Runner result:

```text
Scan completion:
COMPLETE

Mode:
UNMANAGED_REPOSITORY

Recommendation:
NO ADOPTION RECOMMENDATION

JSON / text determinism:
PASS / PASS

No-write:
PASS

Evaluator judgment:
NOT USEFUL
```

Reason:

The result was contract-correct and non-misleading, but it added no material
operational signal beyond the preregistered quick structural glance.

### Case B — One Instruction Surface

Preregistered structure:

- exactly one allowlisted AI instruction surface;
- no bounded restart surface;
- no V13 state surface.

Runner result:

```text
Scan completion:
COMPLETE

Mode:
UNMANAGED_REPOSITORY

Recommendation:
LITE RESTART NOTE RECOMMENDED

JSON / text determinism:
PASS / PASS

No-write:
PASS

Evaluator judgment:
USEFUL
```

Reason:

The scan correctly joined one instruction surface with absent bounded restart
evidence, selected the documented first-match recommendation, and kept task
completion, instruction quality, software correctness, and remote freshness
explicitly unknown. This can reduce pre-fit explanation cost without
diagnosing the repository's workflow.

### Case C — Restart-Oriented Structure Outside the Allowlist

Preregistered structure:

- restart/handoff-related templates exist outside the exact v0.2 allowlist;
- no exact allowlisted instruction, restart, or V13 state surface.

Runner result:

```text
Scan completion:
COMPLETE

Mode:
UNMANAGED_REPOSITORY

Recommendation:
NO ADOPTION RECOMMENDATION

JSON / text determinism:
PASS / PASS

No-write:
PASS

Evaluator judgment:
PARTIALLY USEFUL
```

Reason:

The output accurately stated that no bounded allowlisted restart surface was
observed and did not claim that no restart design exists. Its value was mainly
to expose the scan's documented boundary: repository-specific restart
structure outside the allowlist still requires interpretation.

## Evidence Classification

Across all three cases:

- local repository, `HEAD`, branch, clean worktree, sanitized origin, and
  stable opening/closing snapshots were observed;
- local default-branch relationship remained unknown in the shallow clones;
- task completion, instruction quality, software correctness, and remote
  freshness remained explicit unknowns;
- V13 routing and restart-marker interpretation were not applicable where the
  required exact surfaces were absent;
- the result made no safety, quality, completion, causal, authority, Gate, or
  Revenue claim.

The first-match recommendation contract was independently recalculated from
the bounded payload and matched in all three cases.

## No-Write and Determinism Receipt

Each case was executed four times:

1. default JSON;
2. repeated default JSON;
3. explicit text;
4. repeated explicit text.

All 12 executions returned exit `0`. JSON bytes matched within each case, text
bytes matched within each case, and the opening and closing worktree-content,
Git-directory, and Git-state digests matched in all three cases.

Runner source, tests, fixtures, README, Revenue, price, offer, fit-check,
package, release, CI, telemetry, runtime, and v0.3 surfaces were unchanged.

## Result

```text
Success conditions:
PASS

Useful or partially useful:
2 OF 3

Misleading:
0 OF 3

Runner correction:
NONE

Generalization:
NOT ESTABLISHED

Independent reproduction:
NOT ESTABLISHED

Demand / conversion / Revenue evidence:
NOT ESTABLISHED
```

The run supports a bounded claim only:

> Runner v0.2 produced deterministic, no-write, contract-correct evidence on
> three unrelated public repositories; one result was operationally useful,
> one was partially useful, and one added no material value. No result was
> misleading under the fixed rubric.

## Closure and Re-entry

The private clones and bounded evidence bundle were retained only in the exact
temporary run root until canonical closure, then deleted. The durable receipt
contains no attributable target identity or raw payload.

The enclosing documentation-only commit supplies its own transport identity.
The history-preserving rollback boundary is the canonical starting main
`49c686bb21df8a89895e0200246b5dd8636cf502` plus one revert of the enclosing
receipt commit if required.

This receipt grants no new validation case, source correction, branch, PR,
outreach, publication, Revenue action, runtime, or v0.3 authority.

Completion Line:

V13 Runner v0.2 External Validation Run 001は三つの無関係な公開repoを12回の
offline scanで検証し、3/3 no-write、3/3 recommendation contract、2/3
USEFULまたはPARTIALLY USEFUL、0 MISLEADINGで閉じ、Runnerを変更せず
authority envelopeを消費した。
