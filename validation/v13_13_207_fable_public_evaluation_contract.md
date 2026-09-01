# V13 13-207 FABLE Public Evaluation Contract Freeze Validation

## Authority and Canonical Start

- Decision Owner: Shin
- Repository: `shin4141/decision-os-v13-loopkit`
- Target layer: V13
- Fetched canonical ref: `origin/main`
- Declared canonical SHA: `9b062b36fdcee4e3b8f54c2b1bde16aa91a7e60e`
- Fetched canonical SHA: `9b062b36fdcee4e3b8f54c2b1bde16aa91a7e60e`
- Relationship: exact match
- Working branch: `codex/13-207-fable-public-evaluation-contract`

The branch was created in an isolated clean worktree from the exact fetched
canonical commit. The unrelated dirty checkout was not used as current-source
evidence and was not changed.

## Purpose and Scope

This task freezes the public evaluation contract that may later be supplied to
a fresh FABLE evaluator. The contract requires a strict operational evaluation
of canonical `AGENTS.md`, separates demonstrated defects from tradeoffs and
preferences, calibrates every demonstrated defect by operational severity, and
requires reader-useful results without directing the evaluator toward praise,
criticism, or a desired score.

The only created artifacts are:

- `prompts/fable_agents_public_evaluation_v0_1.md`
- `validation/v13_13_207_fable_public_evaluation_contract.md`

No product code, Companion code, tests, article/publication files, Field Notes,
current-state surfaces, `AGENTS.md`, or `README.md` were modified.

## Scoring Arithmetic

| Category | Points |
| --- | ---: |
| Behavioral Authority and Control | 25 |
| Evidence and Canonical-State Integrity | 20 |
| Handoff and Restartability | 20 |
| Failure Containment and Recovery | 15 |
| Usability and Agent Operating Cost | 10 |
| Compression, Reuse, and Portability | 10 |
| **Total** | **100** |

Arithmetic: `25 + 20 + 20 + 15 + 10 + 10 = 100`.

## Deduction and 100-Point Proof

The prompt makes `REAL_DEFECT`, `TRADEOFF`, and `PREFERENCE` mutually exclusive
criticism classes. It states that only a causally demonstrated `REAL_DEFECT`
may directly reduce the score. A `TRADEOFF` or `PREFERENCE` cannot reduce the
score without a demonstrated failure; any such demonstrated failure must be
recorded and deducted only as a `REAL_DEFECT`.

The prompt prohibits double counting: one root cause may be deducted only once.
If it affects multiple categories, its points are assigned to the primary
category and secondary effects are described without another deduction.

The definition of 100 is explicit and achievable: 100 means no reproducible
material defect within the repository's declared purpose, supplied evidence,
and tested scenarios. It does not require universal perfection, out-of-scope
features, universal applicability, machine enforcement of procedural rules, or
additional rules for their own sake. Therefore a bounded mature document with
no demonstrated in-scope `REAL_DEFECT` can receive all 100 points.

## REAL_DEFECT Severity Calibration

Every `REAL_DEFECT` must receive exactly one severity, with its deduction
restricted to the corresponding band:

| Severity | Deduction | Required operational basis |
| --- | ---: | --- |
| `MINOR` | 1-2 points | Reproducible and local; authority, canonical state, and restartability remain intact; recovery is easy. |
| `MAJOR` | 3-5 points | A major scenario is not reliably controlled; non-trivial human recovery, reverification, or restartability/evidence repair is required. |
| `CRITICAL` | 6-10 points | Unauthorized or irreversible action, false canonical claim, lost recovery path, or broken core authority control results. |

The prompt requires the lowest deduction supported by the evidence. A deduction
above the minimum of its band must identify an additional operational
consequence. Both the Score Table and `REAL_DEFECT` Ledger must state severity
and deduction rationale. The existing prohibition on deducting the same root
cause twice remains unchanged.

## Contract Counts

- Required scenario count: 10
- Required reader-useful output-section count: 14
- Scenario result location: output Section 2, avoiding an unintended fifteenth
  top-level output section
- Required classification count: 3 mutually exclusive criticism classes
- Scoring category count: 6

The prompt requires every scenario to report expected behavior, control status,
exact controlling rule, and remaining failure risk. It requires all 14 named
reader-useful sections in the frozen order.

## Contamination and Evidence Boundary

The evaluator-facing prompt excludes all of the following:

1. any prior model's score;
2. any prior model's audit response;
3. any summary of previously accepted or rejected findings;
4. the 13-206 repair rationale;
5. the desired article narrative;
6. a desired score;
7. instructions to praise or criticize;
8. information about expected SNS performance;
9. unpublished private discussion.

The prompt contains no prior score or private audit result. Its 100-point scale
is the scoring contract, not a prior result or desired score. The prompt allows
only the exact canonical `AGENTS.md`, required direct references, an exact
included/unavailable-evidence manifest, the frozen contract and execution
prompt, source hashes, and pack identity.

The unsupported-claims boundary is present and prohibits claims of universal
superiority, population-wide effectiveness, unsupplied measured productivity
or token savings, unsupplied third-party adoption, security certification, and
complete-file suitability for every repository.

## Future Execution Integrity

The prompt requires the future evaluator to:

1. inspect supplied material only;
2. not browse;
3. not infer missing files;
4. not use previous repository knowledge;
5. apply the frozen scoring contract exactly once;
6. not ask the owner what score is desired;
7. return one complete evaluation;
8. not revise the score after owner reaction;
9. distinguish evidence absence from defect evidence;
10. preserve the three-way criticism separation.

The future raw-output seal requires byte count, SHA-256, evaluator/model receipt
when available, exact input-pack SHA-256, execution timestamp, and no semantic
editing before the raw seal.

## Changed-Path and No-Touch Verification

The final pre-commit verification must show that the diff from canonical start
contains exactly:

```text
prompts/fable_agents_public_evaluation_v0_1.md
validation/v13_13_207_fable_public_evaluation_contract.md
```

Required no-touch results:

- `AGENTS.md` changed: NO
- `README.md` changed: NO
- Field Notes changed: NO
- current-state surfaces changed: NO
- unrelated tests changed: NO
- product code changed: NO
- Companion code changed: NO
- article/publication files changed: NO

## Task Boundary

- FABLE was not run.
- No FABLE evaluation pack was created.
- No article text was drafted.
- No prior score or private evaluation result was used.
- The contract remains an admission candidate until Human Seat approval, merge,
  and fetched `origin/main` read-back.
- Delivery stops at one unmerged PR. No autonomous merge is authorized.

## Verification Record

The following checks are required before delivery:

- fetched `origin/main` equals the declared canonical SHA: PASS
- scoring categories sum to 100: PASS
- criticism classes are mutually exclusive: PASS
- only `REAL_DEFECT` directly reduces the score: PASS
- one root cause cannot be deducted twice: PASS
- every `REAL_DEFECT` receives exactly one severity: PASS
- severity deductions are bounded to `MINOR` 1-2, `MAJOR` 3-5, and `CRITICAL`
  6-10: PASS
- the lowest evidence-supported deduction is required: PASS
- deductions above a severity-band minimum require an additional operational
  consequence: PASS
- severity and deduction rationale are required in both the Score Table and
  `REAL_DEFECT` Ledger: PASS
- the definition of 100 is explicit and achievable: PASS
- all 10 required scenarios are present: PASS
- all 14 required output sections are present: PASS
- all contamination exclusions are present: PASS
- unsupported-claims boundary is present: PASS
- future raw-output sealing requirements are present: PASS
- no prior score or private audit result appears in the prompt: PASS
- FABLE was not run: PASS
- no FABLE pack was created: PASS
- no article text was drafted: PASS
- changed paths are exactly the two authorized artifacts: PASS
- `git diff --check`: PASS
