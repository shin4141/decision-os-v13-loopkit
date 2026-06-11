# Self-Repair Diagnostic

## Purpose

Self-Repair Diagnostic is a pre-invasion check.

Before V13 chooses the next Aspire-oriented move, it should first ask:

> What is currently the weakest point, and what is the highest-EV 0.01 repair?

This prevents the project from confusing forward motion with compounding improvement.

A 0.01 loop is not merely a small task.

A true 0.01 loop is:

> the smallest high-EV repair to the most relevant exposed weakness.

## Why This Exists

V13 is not only a system for moving forward.

It is a system for deciding when not to move forward yet.

After defense is stable, the temptation is to immediately begin Aspire invasion:

- seek stars
- post publicly
- add demos
- build product paths
- expand features
- prepare v1.0

But if the current base is weak, invasion becomes leakage.

Self-Repair Diagnostic creates a controlled step before expansion.

## Diagnostic Sequence

Use this sequence:

```text
1. Current state
2. Weakest point
3. Highest-EV repair
4. Repair size
5. Carrier load
6. Gate
7. Next Loop Command
```

## Diagnostic Areas

Evaluate these areas:

| Area                 | Question                                                                                 |
| -------------------- | ---------------------------------------------------------------------------------------- |
| First-use clarity    | Can a first-time user quickly understand what to do?                                     |
| Copy-paste usability | Can the user copy `AGENTS.md` and receive useful signals?                                |
| Signal reliability   | Do V12, V13, and Chat Continuation Footers appear naturally?                             |
| Handoff durability   | Can another session restart without reconstructing the full chat?                        |
| Aspire alignment     | Does the next action move toward stars, reuse, adoption, revenue, or operationalization? |
| Overbuild risk       | Is the project adding features before evidence?                                          |
| Public readiness     | Would an outside reader understand the value quickly?                                    |
| Carrier load         | Does the next action preserve the operator's ability to continue?                        |

## Gates

### GREEN

Proceed to an Aspire-oriented move.

Use when:

- no major weak point blocks the next step
- the next move is clearly Aspire-aligned
- Carrier load is acceptable
- the move is bounded

### YELLOW

Repair before invasion.

Use when:

- the project can continue
- but a specific weak point has higher EV than public exposure, new features, or v1.0 work

### RED

Stop invasion and recover.

Use when:

- context is unstable
- handoff is insufficient
- the next move would cause overbuild, public overexposure, or Carrier damage
- the current state cannot be safely restarted

## Output Format

Use this format:

```text
Self-Repair Diagnostic:
GREEN / YELLOW / RED

Weakest Point:
<one line>

Highest-EV 0.01 Repair:
<one line>

Reason:
<1-3 lines>

Carrier Load:
LOW / MEDIUM / HIGH

Allowed Next Action:
<one line>

Not Allowed:
<up to 3 bullets>

Next Loop Command:
<one line>
```

## Rule

Do not proceed to Aspire invasion just because a next move is available.

Proceed only when the current weakest point is either repaired or lower-EV than the invasion move.

One-line rule:

> Diagnose the highest-EV exposed weakness before choosing the next Aspire-invasion move.
