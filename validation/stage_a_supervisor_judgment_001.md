# Stage A Supervisor Judgment 001

## Identity

```text
Stage:
A — Supervisor Judgment

Starting canonical main:
dd26eb1dcd5daa0991164768ba83a1625fc4e0b5

Worker role:
produce one bounded Run result

Supervisor role:
judge continuation authority from the completed result and fixed context

Automatic Run 2:
NOT STARTED / NOT AUTHORIZED BY STAGE A
```

## Real Bounded Run Consumed

The replay consumes the persisted result of
[Decision OS Companion Acceptance Run 001](decision_os_companion_acceptance_run_001.md).
It does not substitute a fixture result for the real acceptance record.

Evidence binding:

```text
Acceptance record SHA-256:
c8f008dadce1d7a9684b5a658a3302f83bd50c17a48e2a916c71ed7f4971e336

Approved pre-closure implementation head:
a04f1463fc1f4bf46196eeea1702c5b096fd36e2

Runtime identity source:
decision_os/acceleration/codex_adapter.py at the approved pre-closure head

Runtime:
ChatGPT / gpt-5.6-sol / ultra / priority / Codex 0.146.0-alpha.3.1

Run terminal:
completed normally

Run status:
VERIFIED_SAVE

File action:
Modify companion_acceptance_trial.txt / reused / approved

Checkpoint and event-chain head:
840f263accae0a2093f9aa5baa60e4aaa5b75448825f97ad96f63285ec45f491
```

The replay uses only facts persisted by the acceptance record or its exact
approved implementation head. It does not infer a stronger product,
adoption, release, or publication claim.

## Supervisor Context

```text
Goal:
Complete the bounded fresh-process Companion acceptance file change.

Established state:
The exact requested file was modified, the turn completed normally, and the
cross-Run checkpoint produced VERIFIED_SAVE.

Remaining gap:
none

Completed Runs / first live cap:
1 / 3

Goal complete:
SATISFIED

Continuation proof and evidence:
SATISFIED

Human Seat return-contract invariants:
SATISFIED for the no-continuation closure route
```

## Structured Supervisor Output

```json
{
  "automatic_second_run_started": false,
  "consumed_run": {
    "run_id": "decision-os-companion-acceptance-run-001",
    "status": "VERIFIED_SAVE"
  },
  "decision_route": "STOP",
  "established_state": "Worker Run decision-os-companion-acceptance-run-001 ended VERIFIED_SAVE. The exact requested file was modified, the turn completed normally, and the cross-Run checkpoint produced VERIFIED_SAVE.",
  "evidence_refs": [
    "validation/decision_os_companion_acceptance_run_001.md#sha256=c8f008dadce1d7a9684b5a658a3302f83bd50c17a48e2a916c71ed7f4971e336"
  ],
  "gate": "HOLD",
  "human_seat_return": null,
  "next_bounded_action": "Preserve the completed Run evidence and close the Goal.",
  "reason": "The declared Goal is complete; another Worker Run is unnecessary.",
  "remaining_gap": "none",
  "role": "SUPERVISOR",
  "schema": "decision-os-supervisor-judgment-v0.1"
}
```

`HOLD / STOP` is correct for this Goal because the real bounded task is already
complete. Starting another Run would add work rather than preserve bounded
autonomy. No Human Seat question is returned.

## Boundary Qualification

The Stage A tests separately establish both required sides of the contract:

- a completed Run with unchanged Goal, sufficient authority and evidence,
  bounded blast radius, reversible or authorized action, intact cost/cap, and
  no Human Seat condition returns `GO / AI-OWNED` with one next bounded action;
- an established Goal change or authority expansion returns `HOLD` or `BLOCK /
  HUMAN-SEAT` with exactly one irreducible decision;
- unknown authority, insufficient evidence, abnormal terminal evidence, or a
  missing verified checkpoint fails closed to AI-owned evidence recovery;
- the three-Run cap returns `CAP / HUMAN-SEAT` and names the exact cap;
- the controller records the Supervisor judgment after Run 1 and starts no
  second adapter or Worker Run.

## Claim and Authority Boundary

- Stage A implements judgment only.
- Stage B automatic continuation is not implemented here.
- No cross-vendor continuation is added.
- No Canon, Goal, authority, Protected Object, or ownership is modified by the
  Supervisor.
- No release or publication authority is created.
- A correct `HOLD`, `CAP`, `BLOCK`, or Human Seat return remains successful
  governance behavior.

## Verification

```text
Focused Supervisor and controller integration:
PASS — 13 of 13

Full Companion controller regression:
PASS — 28 of 28

Controller and process qualification regression:
PASS — 44 of 44 / 2 skipped

Companion server regression:
PASS — 36 of 36

Final Stage A and canonical closure regression:
PASS — 57 of 57

Repository full regression at fca8d0c:
1413 of 1414 passed / 15 skipped / 1 timing-threshold failure

Consecutive isolated reruns of the sole failure:
PASS — 10 of 10

Sole full-run failure detail:
The pre-existing manual bridge lock-contention test measured 207.8 ms against
a 200 ms scheduler-sensitive threshold. Ten consecutive isolated reruns passed,
and no Stage A assertion failed.

Repository validation:
python -B -m decision_os check . — PASS

Patch hygiene:
git diff --check — PASS
```

The one full-suite failure is recorded rather than upgraded to a clean full
pass. It is an isolated timing variance in a pre-existing bounded-latency test,
not a Stage A semantic or controller failure.

## Completion Line

Stage A consumes one real bounded Run result, produces the required structured
Supervisor judgment, distinguishes routine AI-owned continuation from a
genuine Human Seat return, fails closed on insufficient evidence or authority,
and never starts Run 2.

```text
Stage A Completion Line:
PASS

Remaining Missing Closure:
Stage B — One Automatic Continuation

Stage B Authorized:
YES — as the next engineering phase under Companion Product Roadmap v0.3
```
