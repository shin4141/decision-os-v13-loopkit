# V13 Runner v0.1

V13 Runner v0.1 is a repository-local, read-only reference CLI for inspecting
Git state and the two canonical V13 current-state surfaces:

- `docs/current_signal.md`
- `handoff/current_codex_handoff.md`

It runs locally without an LLM and emits one deterministic JSON object. It does
not grant authority, select values, modify a repository, contact a remote
service, or perform an operational action.

## Five-Minute Local Path

From this repository:

```sh
PATH="$PWD/bin:$PATH"
decision-os check .
```

The equivalent module form is:

```sh
python3 -B -m decision_os check .
```

No installation, package publication, release, or network access is required.
The `bin/decision-os` entry point resolves this source tree and disables Python
bytecode writes. Run it against another local Git repository by replacing `.`
with that repository's path.

## Output Contract

Every result, including usage and failure results, is exactly one UTF-8 JSON
object followed by one newline. Keys are sorted, evidence is in stable check
order, and no timestamp or elapsed duration is included.

The minimum top-level fields are:

| Field | Type | Meaning |
| --- | --- | --- |
| `v12_state` | string | `PASS`, `DELAY`, `BLOCK`, or `UNKNOWN` |
| `v13_gate` | string | `GO`, `HOLD`, `CAP`, `BLOCK`, or `UNKNOWN` |
| `authority_match` | string | `YES`, `NO`, or `UNKNOWN` |
| `missing_closure` | array of strings | Applicable missing rollback, receipt, or closure-tail evidence |
| `human_seat_required` | boolean or null | Explicit current value, contradiction escalation, inactive-state derivation, or unavailable result |
| `next_authorized_action` | string | Current bounded action, `none`, or `UNKNOWN` |
| `evidence` | array of objects | Stable `check`, `status`, `source`, and `detail` records |

`UNKNOWN` and `null` are not permissions to continue.

## Deterministic Checks

The reference implementation checks:

1. whether the target resolves to an inspectable Git worktree with a valid
   `HEAD`;
2. repository identity from the resolved root name, local `origin` URL, and
   current `HEAD`;
3. the current branch or detached state;
4. clean or dirty worktree state;
5. the relationship between `HEAD` and the locally recorded
   `refs/remotes/origin/HEAD`;
6. existence, containment, regular-file identity, strict UTF-8 readability,
   and a closed first fenced block for both canonical state surfaces;
7. presence and validity of current V12 state, V13 Gate, Active Branch, and
   next authorized action;
8. authority-match and Human-Seat fields when an implementation-loop phase is
   declared;
9. applicable authority-envelope, rollback-identity, receipt, and
   closure-tail evidence when an implementation-loop or closed-run phase is
   declared;
10. affirmative Required/Held Authority, operational-effect, validation,
    rollback, receipt, and closure-tail witnesses before accepting
    `Authority Match: YES`;
11. disagreement within or across the two current state blocks; and
12. explicit contradictions such as a fifth V13 Gate, implementation under
    `Authority Match: NO`, an active run while declared run authority is
    `NONE`, or exhausted authority with positive remaining loops.

Dirty worktree state, detached state, and a non-default branch are evidence.
They do not independently change the semantic exit code.

## Current-Block Rule

Only the first closed triple-backtick block in each canonical surface is
parsed. Later blocks are historical As-of evidence and never backfill a missing
current field.

Fields use the canonical two-line form:

```text
Field:
resolved value
```

Unfilled alternatives such as `YES / NO`, placeholders such as `<commit>`, and
negative evidence such as `MISSING`, `PENDING`, `NONE`, `UNKNOWN`, or
`NOT AVAILABLE` do not satisfy an authority or closure-presence check.

Run-only authority and closure evidence is phase-conditional. Its absence is
valid when the first current blocks declare no implementation-loop or
closed-run phase. This prevents an inactive state from manufacturing a stale
authority envelope.

At the starting canonical As-of
`d9596f8145d4da6d4445486e7d03884277f7dd94`, the first current blocks do not
contain a V12 State. The Runner therefore returns exit `4`; it deliberately
does not recover a later historical V12 value.

## Exit Codes

| Code | Meaning |
| ---: | --- |
| `0` | Current inspected evidence is structurally complete and internally consistent |
| `2` | Invalid CLI invocation |
| `3` | Target is not an inspectable Git repository or a required Git read failed |
| `4` | A required current surface, field, or applicable closure item is missing, unreadable, malformed, unresolved, or invalid |
| `5` | Explicit contradictory current state |
| `6` | Unexpected bounded Runner failure |

Contradiction takes precedence over incompleteness. Exit `0` is a structural
and consistency result, not approval, correctness of a value decision, or
permission to act.

## Read-Only Boundary

The implementation invokes only local Git reads: `rev-parse`, `config --get`,
`symbolic-ref`, `status`, and `rev-list`. Git runs with
`GIT_OPTIONAL_LOCKS=0`, prompting disabled, and stable locale and timezone
settings. It does not run `fetch`, `pull`, `ls-remote`, `add`, `commit`,
`switch`, `merge`, `push`, or another mutating or network Git command.

Tests compare a full content-and-mode digest of the inspected target,
including `.git`, before and after repeated inspection. Module and executable
forms must produce byte-identical output from outside the source repository.

## Explicit Non-Claims

V13 Runner v0.1 does not:

- rank Aspire values or candidates;
- make Successor Debt or Human value judgments;
- decide whether authority should be granted;
- prove remote-branch freshness;
- merge, publish, release, deploy, communicate externally, or change settings;
- execute a runtime autonomous loop; or
- modify Canon, papers, V7, Revenue, outreach, or public surfaces.

It reports bounded local evidence. Missing or unmeasurable evidence remains a
stop condition rather than becoming permission.
