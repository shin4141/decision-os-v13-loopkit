# V13 Reconnection Packet Template

## Purpose

This template is a manual reconnection packet for V13 LoopKit work.

It helps a future Codex/AI session restart from the current operational state without asking the Decision Owner to reconstruct:

- Current Gate
- Next Action
- Do-Not-Do Boundary
- Recheck Condition
- Completion Line
- Missing Closure
- Seat Owner
- Context Risk
- blocked scope

This is not a runtime.
This is not automation.
This is not an execution engine.
This is a manual restart and handoff surface.

## When to Use

Use this packet when:

- a V13 session is ending
- a future Codex/AI must resume work
- context size is becoming risky
- a derived repo or child workflow has reached a gate
- an audit, launch capsule, scaffold, or field note sequence needs restartability
- a user should not have to re-explain current state
- a handoff must transfer ownership, not just information

Do not use this as a public post or product explanation.

## Non-Purpose

This packet does not:

- decide automatically
- replace the human Seat
- approve implementation
- authorize external posting
- create runtime automation
- generate PNG / PDF / screenshots
- replace Launch Capsule
- replace Acceptance Audit
- replace MISTAKEN.md
- replace the main handoff file when a full handoff is required

Human keeps the Seat.

## Reconnection Packet

Copy and fill the following packet.

```markdown
# V13 Reconnection Packet

Packet ID:
As-of Date:
Source Repo:
Target Layer:
Project / Quest Name:

## 1. Current Gate

GO:
HOLD:
CAP:
BLOCK:

## 2. What the Receiving AI Now Owns

The receiving AI now owns:

-

The receiving AI does not own:

-

## 3. One-line Judgment

-

## 4. Seat Owner

Decision Owner:
AI role:
Execution agent role, if any:

## 5. Completion Line

This packet is complete when:

-

## 6. Missing Closure

Known missing closure:

-

If none:

No known Missing Closure.

## 7. One Next Action

The next allowed action is:

-

Do not list multiple next actions unless the task itself is to choose between them.

## 8. Do-Not-Do Boundary

Do not:

-

## 9. Recheck Condition

Recheck when:

-

## 10. Context Risk

Current Context Risk:
- BLUE / YELLOW / RED / UNKNOWN

Reason:

-

If YELLOW or RED, state the safe continuation mode:

-

## 11. Source Anchors

Relevant commits / files / field notes / capsules / reports:

-

## 12. UNKNOWN Fields

The receiving AI must not invent these:

-

## 13. Decision Owner Questions

Ask the Decision Owner only if needed.

Maximum 3 questions:

1.
2.
3.

## 14. Handoff Success Signal

When this packet is accepted, tell the user:

Handoff success.

The receiving AI can now resume with:
- Current Gate
- Completion Line
- Missing Closure
- One Next Action
- Do-Not-Do Boundary
- Recheck Condition
- Seat Owner

Prevented worldline:

Without this packet, the next AI would likely have:

-
```

## Filled Packet Acceptance Check

A filled packet passes only if a receiving AI can answer:

```text
What do I now own?
What is the Current Gate?
What is the one next action?
What must I not do?
What remains unresolved?
When should this be rechecked?
Who keeps the Seat?
What did this packet prevent?
```

If the receiving AI cannot answer these, the packet is incomplete.

## Gate

```text
Manual packet use: GO
Runtime automation: BLOCK
External posting: BLOCK
Human Seat transfer: BLOCK
```

## Notes

This template is intentionally smaller than a full handoff.

Use it when the main problem is reconnection and safe restart, not full project transfer.

If a full transfer is required, use the repo's full handoff process.

## Completion Line

This template is complete when it gives a future Codex/AI enough structured state to restart V13 work without returning routine reconstruction burden to the Decision Owner.
