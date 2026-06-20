# Decision Packet

## Purpose

A notification is not enough.

A normal alert says:

> Risk detected.

But this still leaves the operator with the full burden of deciding what to do next.

V13 LoopKit should eventually produce a **Decision Packet**: a short, human-actionable message that compresses the situation into a small number of valid choices.

The goal is not to give the operator more information.

The goal is to make the next decision possible.

## Core Idea

A Decision Packet is a compressed decision surface.

It should answer:

1. What happened?
2. Why does it matter?
3. What are the two main options?
4. What are the pros and cons?
5. What is the recommendation?
6. What should the human reply?

In one line:

> Do not send an alert. Send a decision.

## Why Alerts Are Not Enough

Bad alert:

```text
BLOCK detected.
CAP exceeded.
Irreversible action pending.
```

This tells the operator that something matters, but it does not reduce the decision burden.

The operator still has to reconstruct:

* what changed
* what is at risk
* what choices exist
* which choice is safer
* what happens if they wait
* what the system recommends

This creates noise.

A good Decision Packet compresses the choice.

## Minimal Decision Packet Format

```text
Signal:
🟡 CAP / Human decision needed

Situation:
<what happened>

Decision:
Choose A or B.

Option A:
<action>

Pros:
- <benefit>
- <benefit>

Cons:
- <cost>
- <risk>

Option B:
<action>

Pros:
- <benefit>
- <benefit>

Cons:
- <cost>
- <risk>

Recommendation:
A / B / HOLD / BLOCK

Confidence:
low / medium / high

Why:
<short reason>

Reply:
A / B / HOLD / BLOCK
```

## Default Rule: Two Paths Only

A Decision Packet should normally present two paths.

Do not give the operator five options.

Too many options recreate the original noise.

Preferred format:

```text
A: proceed under a cap
B: hold and recheck
```

or:

```text
A: push now
B: review once before push
```

or:

```text
A: continue proof
B: pause feature growth
```

The goal is not exhaustive analysis.

The goal is decision compression.

## Recommendation Is Required

A Decision Packet must include a recommendation.

Bad:

```text
You can choose A, B, C, D, or E.
```

Better:

```text
Recommendation:
A

Why:
The action is reversible, documentation-only, and V12 state is PASS.
```

The recommendation reduces operator burden.

However:

> Recommendation is not execution permission.

For irreversible, high-impact, public, financial, deletion, credential, or authority-changing actions, explicit human confirmation is still required.

## When to Send a Decision Packet

Send a Decision Packet when any of the following occurs:

* BLOCK is detected
* CAP would be exceeded
* Context Risk is YELLOW and the next action depends on context health
* Context Risk is RED and normal continuation must be replaced by Handoff / Split / Consult / Stop
* irreversible action is pending
* public release or public promotion is proposed
* money, credentials, deletion, account access, or external authority is involved
* Codex is uncertain whether the next loop should GO / HOLD / CAP / BLOCK
* the next action changes repository state in a way that affects restartability or public interpretation
* the next action may consume credibility, trust, attention, or Carrier capacity

## When Not to Send a Decision Packet

Do not notify for ordinary low-risk work such as:

* small README wording fixes
* JSON formatting
* local validation success
* field note creation within an already approved CAP
* non-public documentation edits
* routine git status checks
* reversible low-impact cleanup

These should be handled by the agent and recorded in the normal V12/V13 signal report.

## Example: Push Decision

```text
Signal:
🟡 CAP / Human decision needed

Situation:
Codex completed documentation updates and local main is ahead of origin/main by 1 commit.

Decision:
Choose A or B.

Option A:
Push now.

Pros:
- Public repo becomes restartable.
- Future agents can resume from GitHub.
- No local-only state remains.

Cons:
- If the docs are wrong, the public repo may briefly mislead readers.

Option B:
Hold and review once.

Pros:
- Reduces public mismatch risk.
- Gives the operator one more chance to inspect.

Cons:
- Delays the proof loop.
- Leaves useful state local-only.

Recommendation:
A

Confidence:
medium

Why:
The change is documentation-only, reversible, and V12 state is PASS. No deletion, credential, public promotion, or package setup is involved.

Reply:
A / B / HOLD
```

## Example: Public Exposure Decision

```text
Signal:
🟡 PUBLIC-CAP / Human decision needed

Situation:
The operator is considering a follow-up post after announcing V13.

Decision:
Choose A or B.

Option A:
Do not post again for 48 hours.

Pros:
- Prevents reaction-chasing.
- Preserves credibility and attention.
- Keeps public exposure within CAP.

Cons:
- Slower feedback.
- Less immediate visibility.

Option B:
Post one clarification.

Pros:
- May help readers understand faster.
- May correct confusion.

Cons:
- Risks looking like over-explanation.
- Consumes attention.
- May convert weak reaction into a public loop.

Recommendation:
A

Confidence:
high

Why:
The announcement loop is already executed and public exposure is capped. The next compound loop is proof, not reaction recovery.

Reply:
A / B / HOLD
```

## Relationship to V12 and V13

V12 asks:

> Is the previous work complete and restartable?

V13 asks:

> Should the next loop GO, HOLD, CAP, or BLOCK?

Decision Packet asks:

> What should the human choose now?

The sequence is:

```text
V12 Completion State
↓
V13 Loop Gate
↓
Decision Packet
↓
Human Reply
↓
Next Loop Command
```

## Relationship to Next Action Card and Context Risk

In the MVP, a Next Action Card is the compact next-step surface that may precede or trigger a Decision Packet.

It must obey the Context Risk Modifier from `docs/loop_map.md`:

```text
Loop Map Confidence >= Required Confidence
AND
Context Risk is not RED
```

When Context Risk is BLUE, the card may recommend normal continuation if confidence is sufficient.

When Context Risk is YELLOW, the card must show the adjusted Required Confidence, include Consult / Handoff / Split as available choices, and frame Continue as "continue under cap."

When Context Risk is RED, the card must not recommend normal continuation. It may recommend only Handoff, Split context, Consult and restore missing anchors, or Stop and resume later.

## Minimal Next Action Card Template

Loop Map Confidence is not progress percentage. It is confidence that the next 0.01 action can be chosen without breaking the map.

```md
# Next Action Card

Signal:
- 🟢 / 🟡 / 🔴

Context Risk:
- BLUE / YELLOW / RED

Loop Map Confidence:
- X%

Required Confidence:
- Y%
- Context Risk Modifier: none / +10 / blocked

Proceed Rule:
- Proceed only if Loop Map Confidence >= Required Confidence
- and Context Risk is not RED

Reason:
- Why this signal and confidence were assigned.

Missing:
- The one missing input that would most improve the next 0.01 action.
- Use `None` if no critical input is missing.

Recommended Next:
- The best conditional next 0.01 action.

Choices:
1. Continue with GOAL-style execution
2. Consult and fill the missing map field
3. Show another option
4. Create handoff / split context
```

## Worked Example: Context Risk YELLOW After A Small Docs Edit

```md
# Next Action Card

Signal:
- 🟡

Context Risk:
- YELLOW

Loop Map Confidence:
- 76%

Required Confidence:
- 80%
- Context Risk Modifier: +10

Proceed Rule:
- Proceed only if Loop Map Confidence >= Required Confidence
- and Context Risk is not RED

Reason:
- A small docs/repo edit has base Required Confidence in the 60-75 range.
- Context Risk is YELLOW because the Codex context is long or a context pressure warning appears.
- The adjusted threshold is 80.
- Loop Map Confidence is 76, which is below the adjusted threshold.

Missing:
- Current restart anchor confirmation.

Recommended Next:
- Do not silently continue with normal GOAL-style execution.
- Consult the Owner or restore the missing restart anchor before editing further.
- If the context remains long or unstable, create a handoff or split context.

Choices:
1. Continue with GOAL-style execution only under cap after the missing anchor is restored
2. Consult and confirm the current restart anchor
3. Show another bounded option that does not edit files
4. Create handoff / split context before further repo edits
```

This example does not mean "stop everything."

It means normal continuation is not justified under the adjusted threshold. The next best 0.01 action is to consult, restore the missing anchor, or hand off / split before editing further.

If Context Risk were RED, option 1 would not be valid. Normal GOAL-style continuation would be blocked, and the available choices would narrow to Handoff / Split / Consult / Stop.

## Final Seat

The final Seat remains with the human.

The agent may recommend.

The agent may compress options.

The agent may identify risk.

The agent may prepare the next command.

But for high-impact or irreversible actions, the agent must not execute without explicit human reply.

## One-Line Summary

A Decision Packet is not an alert.

It is a compressed choice surface that lets the human decide quickly without losing the final Seat.
