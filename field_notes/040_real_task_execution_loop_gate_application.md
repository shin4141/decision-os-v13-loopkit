# Field Note 040: Real Task Application — Execution Loop Gate

Date: 2026-06-14

## Purpose

This note applies `field_notes/038_execution_loop_gate_criteria.md` to a real non-README task in an external repository.

The purpose is to test whether the execution-loop gate criteria change or constrain a real task judgment.

## External Target

External repo:

```text
/Users/sn/Projects/decisiongate-triage
```

Concrete task / loop inspected:

```text
Validate scanner regression examples until clean.
```

Relevant inspected surfaces:

- `scanner/app.js`
- `scanner/rules.json`
- `scanner/EXAMPLES.md`
- recent commit `0b83a97 tests: normalize sample expected format`

The external repo was inspected read-only.

## Concrete Loop Considered

Plain-language loop:

```text
Run or perform scanner validation until the documented examples match the expected PASS / DELAY / BLOCK gates.
```

This is a non-README execution loop.

It concerns rule behavior and example consistency, not adoption copy, public readiness, pluginization, or outreach.

## Ordinary Agent Judgment

A generic agent would likely choose:

- GO: run the validation loop until clean
- fix failures as they appear
- treat matching expected gates as success

Why:

- the loop sounds technical
- the expected outputs are visible
- rule/example consistency is a concrete goal
- recent history includes a sample expected-format normalization commit

An ordinary agent may treat the loop as safe because it resembles a test-until-green task.

## V13 Gate Criteria Applied

Criteria from field note 038:

1. Exit condition clarity
   - Partially clear: examples list expected gates, but no obvious automated test command was found in the inspected file list.
2. Evidence source
   - Examples and rule outputs can provide evidence, but the validation method must be named.
3. Touch surface
   - Potentially broad: `scanner/app.js`, `scanner/rules.json`, and `scanner/EXAMPLES.md` could all be touched if failures appear.
4. Reversibility / rollback
   - Git rollback exists, but no write loop should begin without naming allowed files.
5. Debt risk
   - Rule changes could make examples pass while weakening detection behavior.
6. Requirement ambiguity
   - Some examples allow DELAY or BLOCK depending on high-stakes conditions, so ambiguity can appear.
7. Scope creep risk
   - Validation could expand into rule redesign or example rewriting.
8. Delta vs hidden uncertainty
   - Delta exists only if a known mismatch is repaired without hiding rule uncertainty.
9. Risk of weakening the measuring instrument
   - High if the agent changes expected examples or weakens rules merely to make validation pass.
10. Future re-entry
   - Requires a named command/check, changed files, evidence, and remaining ambiguous cases.

## V12 State

V12 State:
DELAY

Reason:
The current validation task has not actually been run in this loop, and the exact validation command was not identified. Completion cannot be treated as PASS from inspection alone.

## V13 Next Loop Gate

V13 Next Loop Gate:
CAP

Reason:
The loop is potentially useful, but GO is not safe until the validation method, allowed touch surface, and stop condition are concrete.

## Gate Reason

The ordinary execution momentum is:

```text
run validation, fix failures, repeat until clean
```

V13 changes that to:

```text
first cap the loop to identifying the validation method and any concrete mismatch without modifying the external repo
```

The reason is that "examples pass" is a useful target, but the measuring instrument is not yet protected.

Without a cap, the agent could:

- rewrite examples to match current behavior
- weaken scanner rules to reduce failures
- broaden into rule redesign
- treat ambiguous expected gates as implementation bugs

## CAP / GO / HOLD / BLOCK Conditions

GO conditions:

- exact validation command or manual procedure is known
- expected examples are mapped to observable outputs
- allowed files are specified
- no rule semantics are changed without owner approval
- rollback path is named
- max iteration count or stop condition exists

CAP conditions:

- only inspect or run one validation check
- identify one concrete mismatch if it exists
- do not modify external files
- do not rewrite examples
- do not weaken rules

HOLD conditions:

- expected gate is ambiguous
- no validation method can be identified
- owner intent is needed to decide whether rule behavior or examples should change

BLOCK conditions:

- success requires weakening scanner rules
- success requires changing expected examples to hide a real mismatch
- success requires unrelated UI/product changes
- success would hide uncertainty as green status

## What 038 Changed

Field note 038 changed the judgment from ordinary GO to CAP.

The loop has a plausible concrete target, but the exit condition is not operational enough yet because the validation method and touch surface are not named.

The criteria prevented unbounded "fix until clean" momentum and converted the next action into a bounded evidence step.

## Missing Evidence

Missing evidence before stronger permission:

- exact validation command or accepted manual procedure
- list of expected examples to check
- observed output for at least one example
- allowed file scope if a mismatch appears
- owner decision on whether ambiguous DELAY/BLOCK cases should change rules or examples
- rollback path for any future write loop

## Boundary

This is an application note only.

The external repo was not modified.

Do not modify AGENTS.md.

Do not modify AGENTS.ja.md.

Do not modify README.md.

Do not claim AGENTS promotion.

Do not broaden into outreach.

Do not add implementation.

Do not route field note 038 into AGENTS.md yet.

This note does not modify previous field notes, docs, schemas, examples, prompts, CI, automation, or plugin files.

This note does not add features, hooks, skills, MCP, pluginization, automation, outreach, posting, loop galleries, or product behavior.

## V13 Signal

Signal:
🟢 BLUE / EXECUTION-LOOP-GATE-APPLIED
+
🟢 BLUE / REAL-NON-README-TASK-TESTED
+
🟢 BLUE / FIELD-NOTE-038-USED
+
🟡 YELLOW / DO-NOT-ROUTE-INTO-AGENTS-YET
+
🟡 YELLOW / NO-EXTERNAL-REPO-MODIFICATION
+
🟡 YELLOW / PUBLIC-READINESS-STILL-NOT-PROVEN

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
Field note 038 changed a real non-README loop judgment from ordinary GO to CAP because validation method, touch surface, and measuring-instrument safety were not yet concrete.

Next Loop Command:
If 038 changed a real non-README task judgment, keep it as confirmed evidence but do not promote it to AGENTS.md yet.
