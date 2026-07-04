# Field Note 111 — Codex Reset, Automation Habit, and Residue Progress

## Layer

V13 / Automation Habit / Cost and Residue Gate

Adjacent layers:
- V10 Goal-Length / bounded continuation
- V11 Reconnectable Forgetting / reusable residue
- V12 Completion Integrity / end-of-session closure
- V14 Resource Justice / finite time, tokens, attention, and credits

## Summary

This field note records a V13 observation about reset-based usage windows and AI-agent work habits.

The subject is not whether Codex resets or usage limits are good or bad.

The subject is:

```text
What operating habit does a reset-based usage design teach the user?
```

A usage window, reset counter, or limit display can be useful. However, users who are still learning AI-agent development may confuse:

```text
the AI ran for a long time
the usage window was consumed
the reset was used
the limit was reached
```

with real progress.

V13 rejects that confusion.

## Core Rule

```text
Runtime is not progress.
Reset is not strategy.
Residue is progress.
```

Japanese:

```text
稼働時間は進捗ではない。
リセットは戦略ではない。
次に残る構造だけが進捗。
```

## Observation

In AI-agent development, visible runtime can feel productive.

A user may think:

```text
The agent kept running.
The limit was reached.
The reset was used.
Therefore work advanced.
```

But elapsed runtime and usage consumption do not prove progress.

The real questions are:

```text
What was verified?
What remains unverified?
Where did the session stop?
What was learned?
What residue can the next loop reuse?
What should the next AI not repeat?
What was made cheaper, clearer, safer, or more restartable?
```

If a session leaves no reusable residue, it may have consumed runtime without compounding the next loop.

## V13 Interpretation

AI-agent work should not be evaluated by how far the agent ran.

It should be evaluated by whether the loop left a better starting condition for the next loop.

In V13 terms:

```text
A loop is not valuable because it ran.
A loop is valuable when it leaves residue that makes the next loop lighter, safer, clearer, or more restartable.
```

This connects directly to Compound Loop.

A runtime-heavy session can still be a 1.00 loop or even a 0.99 loop if it increases review burden, hides uncertainty, or leaves no restartable structure.

A shorter session can be a 1.01 loop if it leaves a reusable rule, test, handoff, checklist, packet, or verified boundary.

## Risk: Learning the Wrong Automation Habit

The risk is not reset itself.

The risk is learning to treat reset as strategy.

Dangerous habits include:

```text
letting the AI run while confused
running without a cost cap
running without a Completion Line
running without a stop condition
running without handoff or audit residue
treating usage limit exhaustion as work completed
using reset availability instead of strategy
scaling automation before knowing what it should observe
```

These habits can remain hidden while resets are available.

Later, when pricing, credits, higher plans, usage caps, or organizational budgets become binding, the same habit becomes expensive.

## Resource Justice Frame

The user’s resources are finite:

```text
time
tokens
credits
money
attention
review capacity
context-loading capacity
trust
recovery capacity
```

If AI work is supposed to reduce cost, then AI-agent sessions must not waste these resources by producing motion without residue.

A reset can restore usage access.

It cannot restore lost attention, unclear state, unverified work, or missing handoff.

## No Intent Claim

Do not infer or claim OpenAI’s intention.

This field note does not assert why Codex or any AI product uses reset windows, usage displays, credits, or plan tiers.

It only observes a general SaaS and AI-agent risk:

```text
When usage is visible and resettable, users may learn to optimize for consumption instead of compounding residue.
```

The V13 response is not vendor criticism.

The V13 response is operating discipline.

## Practical Rule Candidate

For Codex / Claude Code / AI project instructions, a minimal rule may be:

```text
Before ending a session, write one line stating what was verified, where the work stopped, and what residue makes the next loop lighter.
```

Expanded one-line form:

```text
Before ending this session, leave a restart residue: what was verified, where you stopped, what remains unverified, and what the next AI should reuse or avoid.
```

Japanese:

```text
セッションを終える前に、何を確認したか、どこで止めたか、何が未確認か、次のAIが再利用または回避すべきものを一行で残してください。
```

This rule shifts attention from runtime consumed to structure preserved.

## Relation to V13 Reconnection Packet

This observation connects to:

```text
templates/v13_reconnection_packet_template.md
```

The Reconnection Packet is a larger structured form.

The restart residue line is a smaller end-of-session habit.

Both exist to prevent the same failure:

```text
The agent ran, but the next loop starts from fog.
```

## Gate

```text
Residue progress rule: GO
Codex criticism: HOLD
Vendor intent claim: BLOCK
Automation scaling: CAP / BLOCK
Runtime as progress: BLOCK
```

## CAP Conditions

CAP if this observation starts becoming:

```text
a complaint about Codex
a pricing speculation essay
a broad SaaS criticism
a demand for more usage
a push toward automation without stop conditions
a new runtime feature proposal
```

The useful V13 object is not the complaint.

The useful object is the operating rule.

## BLOCK Conditions

BLOCK if work attempts to:

```text
claim OpenAI's business intent
rewrite README
change AGENTS.md
create automation
add hooks / MCP / pluginization
modify Codex settings
turn reset windows into a productivity metric
treat usage exhaustion as completion
```

## Not a MISTAKEN.md Entry Yet

This is not yet a MISTAKEN.md rule.

Reason:

```text
This is an observed automation-habit risk, not yet a repeated internal failure pattern.
```

Promote only if future work repeatedly treats runtime, reset, or usage exhaustion as progress.

Possible future MISTAKEN rule:

```text
Do not treat runtime, reset usage, or limit exhaustion as progress. Require reusable residue before closing the loop.
```

For now, keep it as a Field Note.

## Future Reuse

Use this observation when evaluating:

```text
Codex sessions
Claude Code sessions
long-running AI-agent tasks
automation loops
implementation capsules
acceptance audits
handoffs
reconnection packets
cost-cap decisions
usage-limit planning
```

Before extending runtime, ask:

```text
What will this run verify?
Where will it stop?
What cost cap applies?
What residue must remain?
What will the next AI reuse?
What would make this session a 1.01 loop rather than consumed runtime?
```

## Completion Line

This field note records a V13 automation-habit rule:

```text
Runtime is not progress.
Reset is not strategy.
Residue is progress.
```

The purpose is to prevent AI-agent users from confusing usage-window consumption with compound progress.

Current status:

```text
Field Note: PASS
OpenAI intent claim: BLOCK
Codex criticism: HOLD
Automation implementation: BLOCK
SNS posting: CAP
```
