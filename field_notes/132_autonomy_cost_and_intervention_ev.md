# Field Note 132: Autonomy Cost and Intervention EV

Date: 2026-08-09

Lifecycle status: Verification pending

Primary layer: V13

Supporting layers: V9 / V10 / V12 / V14

Evidence class: Stage D creator-owned dogfood observation

Canon promotion: HOLD

## Classification

- Artifact type: V13 Field Note
- Field Note type: Self-Application / Product-Value Observation
- Status: Forward-only operational residue / verification pending
- Gate: GO for recording / HOLD for design, implementation, or Canon promotion

This Field Note records an observation produced by the completed Stage D
Leave-the-Desk Dogfood. It does not authorize a new product loop, controller
change, routing change, cap increase, release, publication, or external claim.

## As-of Boundary

Stage D completed one creator-owned real task under the fixed three-Run cap:

```text
one user Goal
→ Run 1
→ Supervisor
→ automatic Run 2
→ Supervisor
→ automatic Run 3
→ terminal COMPLETE
```

The run demonstrated that V13 could preserve the Goal, evidence chain,
authority boundary, Human Seat contract, restartability, and hard Run cap while
Shin performed zero intermediate Receipt-to-Task translation.

Stage D therefore established bounded zero-intermediate-translation autonomy
for that task.

It did not establish that zero intervention was the fastest, cheapest, or
highest-EV operating route.

## Observation

The creator-side result was positive, but the run felt longer than expected.

A plausible counterfactual became visible during review:

- some intermediate work could potentially have been shortened by one bounded
  intervention;
- removing that intervention preserved autonomy but consumed additional model
  calls, elapsed time, and token budget;
- therefore, intervention count and autonomous resource consumption form a
  trade-off rather than a one-directional objective.

This produces the central distinction:

```text
Autonomy possible != autonomy optimal
```

The ability to continue autonomously does not by itself establish that
continuing autonomously is the best resource allocation.

## Core Candidate Principle

Autonomy is not the objective. Decision efficiency is.

A bounded intervention may be preferable to autonomous continuation when the
expected reduction in elapsed time, model cost, token use, loop count,
reconstruction burden, or execution risk exceeds the cost and coordination
burden of the intervention, while preserving the existing Goal, authority,
Protected Object, and Human Seat contract.

Japanese:

> 自律性は目的ではない。判断資源の最適配分が目的である。介入コストより、
> 介入によって削減される時間・モデルコスト・ループ数・再構築負荷・実行リスク
> の期待値が大きく、Goal・権限・Protected Object・Human Seat契約を変えないなら、
> その介入は自律継続より優先され得る。

This statement is a verification-pending rule candidate. It is not Canon.

## Three Candidate Routes

The next bounded action may conceptually be carried through one of three routes:

```text
A. Autonomous AI continuation
B. Bounded Operational Assist
C. Human Seat return
```

These routes must not be collapsed.

### A. Autonomous AI Continuation

Use when the next action remains AI-owned and autonomous continuation has a
reasonable expected resource profile under the current cap.

### B. Bounded Operational Assist

Operational Assist is a non-Seat intervention that reduces search,
verification, routing, or reconstruction cost without changing the governing
human decision.

Examples may include supplying an already-known exact artifact pointer,
confirming a routine factual state, or providing a bounded routing hint.

Operational Assist must not change:

- Goal / Aspire;
- authority;
- material risk tolerance;
- value direction;
- Protected Object or ownership;
- external or irreversible commitment;
- authorized cap.

If any of those must change, the route is no longer Operational Assist.

### C. Human Seat Return

Human Seat remains mandatory when the existing V13 Human Seat Return Contract
requires a human decision.

EV comparison must never be used to bypass a required Human Seat decision.

## Guard-First, EV-Second Ordering

The candidate operating order is:

```text
1. Exclude routes that violate Guard, authority, Seat, or cap.
2. Preserve any mandatory Human Seat return.
3. Compare EV only among the remaining admissible routes.
4. Assign the next action to the highest-EV admissible actor/route.
```

This ordering matters.

A faster or cheaper route is not admissible if it requires authority expansion,
changes the protected object, creates an irreversible commitment, or bypasses a
Human Seat condition.

## Candidate EV Dimensions

No numeric scoring formula is fixed by this Note.

Future evaluation may compare observable dimensions such as:

- expected task progress;
- elapsed time;
- model / token cost;
- number of additional Runs;
- evidence-reconstruction burden;
- coordination burden;
- human attention burden;
- probability and cost of routing or reconstruction error;
- restartability after the route completes.

These dimensions are candidate measurement axes only. This Field Note does not
authorize scalarization, weights, thresholds, or automatic next-actor routing.

## Relationship to Existing V13 Product Thesis

The existing product-value target remains:

> More safe autonomous progress per Human decision.

This Note does not replace that target.

It adds a constraint discovered by dogfood:

> More autonomy is not automatically more product value when the cost of
> preserving autonomy exceeds the cost of a bounded non-Seat intervention.

The relevant optimization target may therefore be better expressed as the
allocation of scarce judgment and execution resources, not autonomy count by
itself.

## Why This Is Not Yet a Rule

The Stage D observation comes from one creator-owned case.

The counterfactual route was not executed under a controlled comparison.
Therefore the repository does not yet know:

- how often a bounded assist would actually reduce total cost;
- whether assist coordination introduces new errors or delays;
- whether the effect persists across task types;
- whether AI-to-AI assistance differs materially from human assistance;
- which cost dimensions dominate in practice;
- whether a routing heuristic can outperform a simple autonomy-first policy.

Accordingly, promotion remains HOLD.

## Falsifier / Countercondition

This candidate loses operational value if bounded comparisons repeatedly show
that zero-intervention autonomous continuation is equal or better in total
resource cost, elapsed time, restartability, and error burden while preserving
the same governance boundaries.

It also weakens if Operational Assist consistently creates enough coordination,
context-switch, or misrouting cost to erase the expected savings.

## Re-evaluation Triggers

Re-open this Field Note when one or more of the following are available:

1. Multiple real V13 tasks record autonomous elapsed time, model calls, Run
   count, and reconstruction burden.
2. At least one comparable task is executed with a bounded non-Seat Operational
   Assist and the total resource delta can be inspected.
3. A repeated failure pattern shows that autonomous continuation routinely
   spends extra Runs recovering information that could be supplied cheaply
   without Human Seat judgment.
4. A repeated opposite pattern shows that interventions create more
   coordination burden than they save.
5. The repository is ready to evaluate a bounded Next-Actor Selection rule
   without expanding Human Seat, authority, or cap semantics.

## Candidate Future Question

The next product question is not:

> Can V13 continue without a human?

Stage D already demonstrated that in one bounded creator-owned case.

The next question is:

> Among the admissible routes, who should carry the next action so that total
> decision and execution EV is highest without weakening Guard or Human Seat?

Possible future label:

```text
Intervention EV / Next-Actor Selection
```

The label is provisional and creates no implementation authority.

## Responsibility Boundary

This observation must not be used to move routine work back to Shin merely
because a human intervention might be faster.

If a bounded assist can be supplied by another AI or execution layer, that
remains AI-owned unless the Human Seat contract is triggered.

The purpose of this candidate is resource allocation, not responsibility
laundering.

## Current Gate

```text
GO FOR RECORDING
HOLD FOR PROMOTION / IMPLEMENTATION
```

## Missing Closure

- no controlled autonomous-vs-assist comparison yet;
- no validated EV dimensions or weights;
- no Next-Actor Selection rule;
- no evidence that the Stage D cost trade-off generalizes;
- no product decision authorizing implementation.

## Explicit Non-Authority Statement

This Field Note does not authorize:

- another V13 product loop;
- changes to Stage A/B/C/D semantics;
- automatic next-actor routing;
- new EV weights or thresholds;
- cap expansion;
- Human Seat reduction;
- release;
- publication;
- external performance or cost claims.
