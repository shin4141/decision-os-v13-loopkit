# Incident-to-Instruction Self-Service Run 001

## Status

```text
As-of:
2026-07-26 / Asia/Tokyo

Result:
PASS / COMPLETE

Repository:
shin4141/decision-os-v13-loopkit

Base:
bead87552ef4a379d734ad9fc3c84f98315ca419

Branch:
docs/self-service-incident-to-instruction-v0-1

Changed files:
PASS / EXACT 4

README links:
PASS / 2 OF 2

Prompt replacement point:
PASS / EXACTLY 1

Required output fields:
PASS / 13 OF 13 IN PROMPT AND EXAMPLE

Example:
PASS / ONE COMPLETE BLOCK / NO TEMPLATE MARKERS

Self-service boundary:
PASS / FREE DRAFT DISTINCT FROM PAID AUDIT

Markdown:
PASS / 60 LOCAL LINKS / 94 HEADINGS / 26 CLOSED FENCES

Full suite:
PASS / 166 OF 166

Protected-blob guard:
PASS / 14 OF 14 BLOBS AND MODES

git diff --check:
PASS

Publication handoff:
PASS / CLEAN WORKTREE / LOCAL = TRACKING = REMOTE
```

## Validation question

Can a first-time visitor move from the repository README to one public
copy-paste prompt, provide one sanitized incident to their own AI, and receive
one reviewable instruction-rule draft without installing LoopKit, sharing a
repository, editing JSON, running a CLI, or entering the paid Audit?

## Validation subject

This run covers:

- the new first README route in [`README.md`](../README.md);
- the
  [Incident-to-Instruction prompt](../copy-paste/incident-to-instruction-rule.md);
- the complete
  [synthetic Before / After example](../examples/incident-to-instruction-before-after-v0-1.md);
- this validation receipt.

## Exact four-file scope

```text
ADD copy-paste/incident-to-instruction-rule.md
ADD examples/incident-to-instruction-before-after-v0-1.md
ADD validation/incident-to-instruction-self-service-run-001.md
MODIFY README.md
```

No checker, code, test, service, price, release, version, Canon,
branch-protection, Reddit, or unrelated PR surface is in scope.

## Self-service contract receipt

The prompt must contain exactly one visible incident replacement point and all
thirteen requested output fields:

1. Incident As-of
2. First Operational Gap
3. Target Surface
4. Target Path or Placement
5. Intended Scope
6. Exact Paste-Ready Insertion Block
7. Required Completion Evidence
8. HOLD Conditions
9. BLOCK Conditions
10. Handoff Requirements
11. Rollback
12. Re-evaluation Trigger
13. Still UNKNOWN

The example must contain one complete, placeholder-free `AGENTS.md` block and
must identify itself as synthetic, invented, non-private, non-customer
evidence, unmeasured, and not prevention proof.

The public self-service path returns a draft. It does not perform the paid
Audit, diagnose a customer workflow, verify implementation, authorize a write,
or establish prevention or effectiveness.

## Exact commands

### Full suite and protected guard

```sh
python3 -B -m unittest discover -s tests

python3 -B -m unittest -v \
  tests.test_decision_os_scan_cli.DecisionOsScanCliTest.test_protected_v01_blobs_and_modes_are_unchanged
```

### Existing Loop Record examples

```sh
python3 -B scripts/validate_loop_record_examples.py \
  --schema schema/v13_loop_record.schema.json \
  --examples-dir examples
```

### Documentation and self-service contract

The final pass uses a dependency-free, non-committed validation script to
check the exact four files, relative links, README placement, one incident
replacement point, all thirteen fields, the completed example, boundary
language, ATX heading order, fenced blocks, and placeholder markers.

## Command receipt

```text
Full suite:
PASS / 166 tests / exit 0

Protected-blob guard:
PASS / 14 protected blobs and modes / exit 0

Loop Record examples:
PASS / 12 of 12 / exit 0

Documentation and self-service contract:
PASS / exit 0
```

## Documentation receipt

```text
Exact changed files:
PASS / 4 of 4

README placement:
PASS / first H2 after the five existing badges

README primary and secondary links:
PASS / 2 of 2

Visible incident replacement points:
PASS / exactly 1

Required output fields:
PASS / 13 of 13 in the prompt
PASS / 13 of 13 completed in the example

Example template markers:
PASS / 0

Paste-ready instruction blocks:
PASS / exactly 1

Synthetic / non-private / non-evidence markers:
PASS

Free draft / paid Audit distinction:
PASS

Account, install, direct message, repository share, JSON, or CLI requirement:
NONE

Relative local links:
PASS / 60 resolved

Heading hierarchy:
PASS / 94 headings / no level jump

Fenced blocks:
PASS / 26 closed fences

git diff --check:
PASS / no output / exit 0

Clean worktree:
PASS / after commit

Branch heads:
PASS / local = tracking = remote
```

## Scope and no-write boundary

The run reads repository documents and executes the existing test suite. It
does not send an incident, invoke an external AI, edit a target instruction
surface, create an account, install a tool, contact Shin, open a fit check, or
perform the paid Audit.

The README keeps the existing scan, intake, Audit, and tutorial paths below the
new first-time route without deleting or rewriting them.

## Bounded conclusion

The README now begins with one direct self-service reward, the copy-paste page
contains one incident replacement point and all thirteen output fields, and
the complete synthetic example returns one placeholder-free instruction block.
The route requires no public incident, contact, repository share, account,
installation, JSON edit, or CLI and remains a draft rather than a verified
Audit or prevention claim.

## Limitations

- The incident and returned rule are synthetic and non-private.
- No external AI response was measured.
- No real target surface was inspected or edited.
- No customer reviewed, accepted, or applied the rule.
- One example cannot establish target correctness, instruction compliance,
  prevention, recovery, safety, productivity, paid value, or general
  reliability.

## Completion Line

A first-time Reddit visitor can:

1. open the README;
2. immediately understand the reward;
3. open one copy-paste prompt;
4. privately insert one sanitized incident into their own AI;
5. receive one paste-ready instruction rule;
6. see a complete Before / After example;
7. understand the boundary between the free draft and the human-reviewed Audit;

without posting the incident, contacting Shin, sharing a repository,
installing LoopKit, editing JSON, or running a CLI.
