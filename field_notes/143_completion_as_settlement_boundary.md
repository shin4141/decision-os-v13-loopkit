# Field Note 143 — Completion as a Settlement Boundary

Status: Verification pending

As-of: 2026-08-31 JST

Primary layer: V13

Supporting layer: V12

Evidence class: External market-convergence observation

Canon promotion: HOLD

## Classification

- Artifact type: V13 Field Note
- Field Note type: External Signal / Completion Integrity / Commercial Boundary
- Gate: GO for recording / HOLD for Canon promotion, implementation, pricing design, or public product claim

This Field Note preserves an external market signal that makes an existing
Decision-OS boundary commercially consequential. It does not authorize a new
product loop, implementation change, pricing change, publication campaign, or
claim that an external company uses Decision-OS.

## Source and evidence boundary

The Information reported on 2026-08-30 that enterprise software providers are
moving from seat-based subscriptions toward usage- and outcome-based pricing.
The report states, based on people familiar with the matter, that OpenAI has in
recent months begun offering some large customers an option under which charges
are incurred only when AI completes a task.

Source:

- The Information, "How Salesforce Is Overhauling the Way It Charges for AI"
  (2026-08-30):
  https://www.theinformation.com/articles/salesforce-overhauling-way-charges-ai

This OpenAI-specific item is a reported enterprise-contract practice. It is not
an OpenAI public product announcement and was not independently confirmed for
this Note.

OpenAI's public business pricing page, inspected on 2026-08-31, continued to
describe Business seat pricing and Enterprise custom pricing with credit- and
token-based options. It did not expose a generally available outcome-priced
plan.

Source:

- OpenAI, Business Pricing:
  https://openai.com/business/pricing/

Two separately observable industry signals support the broader direction
without independently proving the reported OpenAI contract terms:

1. Bret Taylor, Sierra co-founder and OpenAI board chair, publicly described
   outcome-based pricing as the future of software business models and the
   process, rather than the person, as the atomic unit of AI productivity.

   Source:
   https://sierra.ai/resources/podcasts/bret-taylor-of-sierra-on-ai-agents-outcome-based-pricing-and-the-openai-board

2. Salesforce announced on 2026-06-15 an agreement to acquire Fin for
   approximately USD 3.6 billion. Salesforce described Fin's AI agent as
   resolving customer queries end-to-end and emphasized measurable outcomes.

   Source:
   https://www.salesforce.com/news/press-releases/2026/06/15/salesforce-signs-definitive-agreement-to-acquire-fin/

The bounded external observation is therefore:

```text
Reported OpenAI enterprise option:
payment conditioned on completed AI tasks

Public OpenAI pricing:
no generally available outcome-priced plan observed

Broader market direction:
independently visible movement toward pricing AI work by process or outcome
```

## Structural observation

Token, seat, and execution pricing can charge for input consumption, access, or
activity without first proving that the requested work reached a valid terminal
state.

Outcome pricing changes that requirement.

```text
AI consumed resources
!= AI executed an action
!= AI produced an artifact
!= the task completed
!= the completion is attributable and billable
```

When payment depends on completed work, a completion claim is no longer only an
execution, safety, or restartability statement. It can become a financial
settlement claim.

Central candidate principle:

> When AI is priced by completed work, completion is no longer only an
> execution or safety boundary. It becomes a settlement boundary.

Japanese:

> AIが完了した仕事によって課金されるとき、完了は実行上または安全上の境界に
> とどまらない。決済成立の境界になる。

This is a candidate interpretation of the external signal, not Canon.

## Completion Gate to Billing Gate

The market signal exposes a possible additional role for existing V12/V13
structures:

```text
exact task identity
-> completion contract
-> bounded execution
-> semantic completion check
-> external-effect evidence
-> immutable result identity
-> billable / non-billable settlement decision
```

The following mapping is a research candidate only:

| Existing boundary | Outcome-priced consequence |
|---|---|
| Task identity | Determines which work could be charged |
| Completion Line | Defines the claimed terminal condition |
| Semantic completion | Separates a finished Run from completed work |
| External-effect evidence | Distinguishes attempted action from changed external state |
| PASS integrity | Prevents an unsupported completion from becoming a billing claim |
| Retry / duplicate control | Prevents repeated attempts from silently becoming repeated charges |
| Result identity / receipt | Provides a reconnectable object for settlement and dispute review |
| Human Seat boundary | Preserves whether human approval remains a prerequisite to completion |
| As-of / freshness | Prevents stale success from settling a changed task state |

The concise candidate transformation is:

```text
Completion Gate
-> Billable Completion Gate

PASS
-> potentially charge-bearing completion assertion

Immutable Receipt
-> potential settlement and dispute evidence

False Completion
-> potential false or unsupported billing
```

## Why False Completion becomes financially material

An agent can finish a Run, return fluent prose, create a local artifact, or
report success without establishing the requested semantic terminal state.

Under activity-based pricing, that failure may waste compute or human review.
Under outcome-based pricing, the same failure can additionally create a dispute
over whether money is owed.

Examples include:

- `SENT` being treated as `DELIVERED`;
- a Worker reaching a terminal process state without semantic completion;
- an artifact existing locally without the required external effect;
- a retry being counted as a second successful task;
- a partial completion being upgraded to full completion;
- a stale or superseded result being charged against the current task;
- a human-required approval being treated as already satisfied;
- or a vendor-controlled evaluator marking its own work complete without an
  agreed evidence contract.

The financial layer therefore increases the value of not fabricating `PASS`
when semantic completion is absent.

## Attribution is adjacent but distinct

Task completion and business outcome attribution must not be collapsed.

```text
task completed
!= customer value created
!= revenue or cost change caused by this AI
```

A support ticket may have a comparatively observable terminal state. Revenue
growth, loss avoidance, or decision quality can depend on human action,
seasonality, other software, organizational change, and external events.

Therefore a Billable Completion Gate for a bounded task would not by itself
establish entitlement to a share of a broader business outcome. Attribution,
counterfactual baseline, measurement window, and dispute authority remain
separate unresolved contracts.

## Decision-OS lineage connection

### V12 — Completion integrity

V12 treats completion as a reconstructable state rather than a polished claim.
Outcome pricing makes that distinction commercially testable: unsupported
completion can become unsupported settlement.

### V13 — Gate and bounded continuation

V13 separates `PASS / DELAY / BLOCK / UNKNOWN` from
`GO / HOLD / CAP / BLOCK`, preserves the Human Seat, and prevents completion
from automatically authorizing another loop. A commercial settlement layer
would need the same separation: payment for one completed task must not silently
authorize another Run, retry, external effect, or charge.

### External Intelligence

Field Note 142 requires evidence maturity to travel with reusable intelligence.
The same requirement applies to completion used for settlement. A later payer,
vendor, auditor, or agent must be able to recover not only the claim that work
completed, but also its provenance, evidence state, As-of, and remaining
unknowns.

## Candidate research and product direction

The external signal creates a candidate direction beyond "an OS that helps AI
perform work":

> an evidence layer that determines whether AI work reached an agreed,
> charge-bearing completion state.

Possible future questions include:

1. Can a completion contract be specified independently of the model and
   vendor that performs the work?
2. Can the party that executes the task be separated from the party that
   verifies billable completion?
3. Which completion states are sufficiently observable to support settlement
   without disproportionate audit cost?
4. How should partial value, human intervention, retries, reversals, and delayed
   external effects be represented?
5. Can one immutable receipt establish task completion while explicitly
   refusing broader business-outcome attribution?

These are research candidates. This Note creates no implementation authority.

## Non-claims

This Note does not establish:

- that OpenAI has publicly launched outcome pricing;
- that the reported option is available beyond some large customers;
- the contract language, price, evaluator, task definition, or dispute process
  used in any OpenAI agreement;
- that OpenAI, Sierra, Fin, Salesforce, or any other company uses Decision-OS or
  an equivalent completion architecture;
- that Decision-OS currently provides a production billing or settlement
  system;
- that every AI task has an objectively measurable completion state;
- that completion alone establishes business value or causal attribution;
- that outcome pricing is always preferable to seat, token, credit, usage, or
  hybrid pricing;
- that a vendor's self-reported completion is sufficient billing evidence;
- or that this observation authorizes a product, pricing, publication, outreach,
  implementation, or new loop.

## Re-evaluation trigger

Re-evaluate this Note when at least one of the following becomes available:

- OpenAI publishes or confirms an outcome-priced product or contract structure;
- an accessible enterprise contract exposes the exact task, completion,
  evaluator, retry, attribution, and dispute rules;
- a bounded V13 receipt is tested as settlement evidence between distinct
  executor and verifier roles;
- a real outcome-priced workflow demonstrates a False Completion, duplicate
  charge, partial-completion, or attribution dispute;
- or contrary evidence shows that the reported OpenAI option was inaccurate,
  withdrawn, or materially different from task-completion pricing.

## Promotion boundary

```text
Current status: Verification pending
Canon promotion: HOLD
Implementation authority created: NO
Pricing authority created: NO
Publication authority created: NO
Current V13 Gate changed: NO
Current 13-43 HOLD changed: NO
```

Preserve this Note as an external market-convergence observation and research
origin record. Any Canon promotion, billing design, implementation, public
claim, or commercial offer requires a separate bounded task and evidence
review.
