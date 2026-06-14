# Field Note 035: Loop Gallery vs Decision-OS

Date: 2026-06-14

## Purpose

This note distinguishes generic loop galleries / execution-loop collections from Decision-OS V13.

The purpose is to prevent V13 from drifting into a generic prompt or loop-template collection.

## What Loop Galleries Do

Loop galleries provide reusable execution patterns.

They are strong for known tasks with known exit conditions.

Examples include:

- test-until-green
- build-until-green
- CI watcher
- PR babysitter
- README polish
- coverage threshold
- similar coding-agent workflows with known feedback gates

Their value is immediate usability.

They are copyable.

They answer:

```text
Here is a loop you can run.
```

## What Decision-OS Does

Decision-OS does not primarily provide more execution loops.

It judges whether a loop should:

- run
- continue
- cap
- hold
- stop

It asks whether the loop sends future delta or future debt.

It records what the loop reveals about missing fixed points.

It converts failure structure into future detection conditions.

Decision-OS is not mainly a gallery of loops.

It is a governance layer over loops.

## The Core Difference

Loop galleries answer:

```text
What loop should I run?
```

Decision-OS answers:

```text
Should this loop run at all?
What is the cap?
What is the exit condition?
What did this loop teach?
Where does the newly discovered fixed point belong?
Did this create delta or debt?
```

The difference is not vocabulary.

It is level.

Loop galleries help execute.

Decision-OS helps judge execution.

## Where Loop Galleries Are Strong

Loop galleries are strong at:

- execution clarity
- copyability
- immediate developer utility
- known feedback gates
- clear technical exit conditions
- easy adoption

This is a real strength.

V13 should not dismiss it.

## Where Decision-OS Must Not Compete

Decision-OS should not try to beat loop galleries by becoming a larger prompt/loop template collection.

That is a losing field.

Generic loop templates are easier to understand, copy, and market.

If V13 competes as a loop collection, it becomes heavier than the thing it is trying to beat.

That would weaken its distinctive value.

## Where Decision-OS Can Win

Decision-OS can sit above loop galleries as a loop governance and learning layer.

It can:

- evaluate loop admissibility
- set CAP axis and limit
- prevent polish momentum
- distinguish internal utility from public readiness
- detect premature claims
- preserve failure structure through Mistaken MD
- place discovered gaps by Decimal Depth
- convert failed loops into reusable detection conditions

This is a different job from providing the loop itself.

V13 wins if it helps decide which loops deserve to run, how far they may go, and what they reveal.

## Example Contrast

README polish:

Generic loop:

```text
Keep improving the README until it is clearer.
```

Decision-OS:

```text
Is clarity actually the missing node?
Is there reader evidence?
Is this polish momentum?
Should this be Evidence CAP instead?
If a readiness mistake appears, where does it belong in the map?
```

The generic loop may be useful when the missing node is known.

Decision-OS is useful when the missing node itself is uncertain.

## Relation to Fixpoint Learning

Loop galleries execute known loops.

Fixpoint Learning discovers the missing map while moving.

Decision-OS becomes stronger when loops reveal new fixed points that are recorded and reused.

The important output is not only:

```text
loop completed
```

It is also:

```text
the loop revealed a missing fixed point, and the map is now stronger
```

## Relation to Decimal Depth

A loop may reveal a missing fixed point after the fact.

Decision-OS must not append it as a generic lesson.

It should place it where it causally belonged.

Decimal Depth preserves the structure of what the loop revealed.

Without that placement, V13 can sound wise while losing the topology of the failure.

## Boundary

This is a contrast note only.

Do not build a loop gallery.

Do not modify AGENTS.md.

Do not rewrite README.

Do not claim superiority as public proof.

Do not broaden into outreach.

Do not add implementation.

Do not route this into AGENTS.md yet.

This note does not modify AGENTS.md, AGENTS.ja.md, README.md, previous field notes, docs, schemas, examples, prompts, CI, automation, or plugin files.

This note does not add features, hooks, skills, MCP, pluginization, automation, outreach, posting, loop galleries, or product behavior.

## V13 Signal

Signal:
🟢 BLUE / LOOP-GALLERY-CONTRAST-RECORDED
+
🟢 BLUE / EXECUTION-LOOP-VS-JUDGMENT-LOOP-SEPARATED
+
🟢 BLUE / DECISION-OS-POSITIONING-CLARIFIED
+
🟢 BLUE / DO-NOT-COMPETE-AS-LOOP-COLLECTION
+
🟡 YELLOW / PUBLIC-VALUE-STILL-NOT-PROVEN
+
🟡 YELLOW / DO-NOT-ROUTE-INTO-AGENTS-YET
+
🟡 YELLOW / DO-NOT-BUILD-LOOP-GALLERY

V12 State:
PASS

V13 Next Loop Gate:
CAP

Reason:
The contrast is recorded, but it is positioning evidence only. It does not prove public value or authorize V13 to become a loop gallery.

Next Loop Command:
Use this contrast later to prevent V13 from drifting into a generic loop-template collection.
