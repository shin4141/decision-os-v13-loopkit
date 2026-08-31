# V13 13-206 Bounded Contract Repair Validation

## Authority and Canonical Start

- Decision Owner: Shin
- Authorized repair IDs: AR-01, AR-02, AR-03, AR-04, AR-05, AR-06, AR-07
- Fetched canonical ref: `origin/main`
- Fetched canonical SHA: `19fc706d72e125ccb208e049c944e3b00b2bc0af`
- Declared starting SHA: `19fc706d72e125ccb208e049c944e3b00b2bc0af`
- Relationship: exact match
- Working branch: `codex/13-206-agents-bounded-contract-repair`

The branch was created in an isolated worktree from fetched `origin/main`. The
unrelated dirty checkout was not used as canonical evidence and was not changed.

## Implemented Repairs

### AR-01 — Generic admission and historical fixture separation

- `tests/test_current_state_admission.py` now checks the stable generic
  admission fields, byte-identical paired first blocks, explained `UNKNOWN`,
  exact fetched-`origin/main` read-back, and declared-base ancestry.
- A synthetic future frontier passes without any 13-42 / 13-43-specific field.
- A candidate branch containing the exact future block is rejected until the
  block is present on fetched `origin/main`.
- The existing 13-42 / 13-43 assertions and byte-preservation hashes remain in
  `tests/test_13_42_13_43_historical_regression.py`.
- `AGENTS.md` requires future frontiers to preserve all older blocks and the
  separately named historical regressions rather than rebaseline them.

### AR-02 — FN060 / FN100 authority

- Both notes use the existing lifecycle state `Folded`.
- Both notes remain origin and trajectory evidence and explicitly have no
  independent execution or Gate authority.
- Their current operational distinctions are stated in `AGENTS.md` instead of
  routing current GO-blocking authority through either note.
- Neither note is `Canon-promoted`.

### AR-03 — Routed-document precedence

`AGENTS.md` now states that it controls repository instructions, explicitly
routed documents bind only within delegated scope, routed detail may add
requirements but cannot override `AGENTS.md`, and a shorter summary does not
waive routed-document requirements.

### AR-04 and AR-07 — Canonical relationship and non-admission

Canonical admission now requires all of the following:

1. the exact candidate change is present in the paired first blocks read from
   fetched `origin/main`;
2. those blocks are byte-identical;
3. their declared Canonical Reconstruction Base is an ancestor of fetched
   `origin/main`.

A branch, commit, pushed artifact, or PR establishes delivery or review
availability only. It does not establish canonical admission.

### AR-05 — Material regression risk

The undefined `0.99 risk` shorthand is replaced by `material regression risk`.

### AR-06 — Explained UNKNOWN

Required current-state and handoff fields may remain `UNKNOWN` when evidence is
genuinely unavailable, but must include a concise reason.

## Changed-Path Scope

- `AGENTS.md`
- `field_notes/060_v13_active_and_parked_lines_status_review.md`
- `field_notes/100_session_size_context_risk.md`
- `tests/test_current_state_admission.py`
- `tests/test_13_42_13_43_historical_regression.py`
- `validation/v13_13_206_bounded_contract_repair.md`

`README.md`, both paired current-state surfaces, Gate definitions, Gate values,
and all other Field Notes are unchanged.

## Verification

### Focused and relevant suites

| Command / suite | Result |
| --- | --- |
| `python -m unittest discover -s tests -p 'test_current_state_admission.py'` | PASS — 8 tests |
| `python -m unittest discover -s tests -p 'test_13_42_13_43_historical_regression.py'` | PASS — 6 tests |
| `python -m unittest discover -s tests -p 'test_decision_os_checks.py'` | PASS — 33 tests |
| `python -m unittest discover -s tests -p 'test_decision_os_handoff_acceptance.py'` | PASS — 56 tests |
| `python -m unittest discover -s tests -p 'test_decision_os_handoff_acceptance_cli.py'` | PASS — 10 tests |
| Focused/relevant total | PASS — 113 tests, 0 failures, 0 errors |

### Full suite

The first sandboxed full discovery ran 1,547 tests with 4 failures, 87 errors,
and 14 skips. Ephemeral localhost binds were denied by the sandbox and local
browser probes aborted there, so that run is retained as environment-limited
evidence rather than treated as the repository baseline.

The same command was then rerun with the local permissions required by the
existing server and browser tests:

```text
Ran 1547 tests in 855.920s
FAILED (failures=1, errors=44, skipped=15)
```

The 44 errors are the pre-existing creator-live fixed-identity baseline already
declared in the unchanged current-state block. The one failure is
`test_compound_evidence_meter.CompoundEvidenceMeterCanonicalSurfaceTests.test_current_canonical_and_handoff_surfaces_are_consistent`, which expects
`None. Stop.` while the unchanged admitted 13-42 / 13-43 first block contains
its bounded 13-43 acceptance action. Neither the current-state surfaces nor
that test were changed by 13-206.

### Contract assertions

- Historical 13-42 / 13-43 regression preserved: PASS
- Generic future frontier without historical fields: PASS
- Branch before `origin/main` admission: rejected as required
- Fetched `origin/main` descendant after candidate integration: admitted in the
  synthetic fixture
- Routed handoff fields remain binding: PASS
- FN060 / FN100 non-Canon authority: PASS
- Explained `UNKNOWN` rejected/accepted cases: PASS
- Gate outcome vocabulary unchanged: PASS
- Unauthorized broad `BLOCK` change: absent
- Unauthorized recommendations: absent
- `README.md`: unchanged
- `git diff --check`: PASS before report creation; rerun required before commit

## Boundary

This repair stops at an unmerged PR. Merge, post-merge canonical reconstruction,
and any later publication or next loop require separate Human Seat authority.
