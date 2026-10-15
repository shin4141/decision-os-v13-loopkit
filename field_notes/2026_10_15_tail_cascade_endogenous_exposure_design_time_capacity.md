# Field Note — Tail Cascade × Endogenous Exposure × Design-Time Capacity

As-of: 2026-10-15 JST
Status: Verification pending — research hypothesis, not adopted Canon
Primary layer: V13 research, with V9/V10/V14 connections
Decision Owner: Shin
Evidence class: abstract scenario and mathematical assumptions; not an empirical incident or validated product failure
Current Gate: hypothesis preserved / Canon and runtime adoption HOLD

## Problem

Positive expected unit economics do not by themselves establish that a firm can honor every obligation it accepts during a finite operating horizon. A product can have a high contractual utilization ceiling but ordinarily attract little utilization. Publicly visible extreme outcomes, promotional incentives, and competitors' terms may shift participation and correlated exposure, including after liquidity has already fallen.

Distinguish:
- **Contractual maximum:** what the provider promises to accept or pay.
- **Forecast utilization:** typical demand or participation.
- **Outcome-conditioned exposure:** future utilization depends on prior visible outcomes.
- **Available capacity:** liquid resources and enforceable financing to honor accepted obligations.
- **Competitive imitation:** product terms may be copied without copying capital buffers.

## Abstract probabilistic example

Consider a hypothetical product with a success event of probability p=1/250 and gross payment multiple M=225, including principal. Eight independent participants can each commit up to 3,000 monetary units to the same event. This is a deliberately simplified numerical example, not an observation about any real operator.

For one participant committing 3,000 units, expected gross payment is 3,000 × 225 / 250 = 2,700 units, leaving expected provider income of 300 units, or 10% of the stake. With all eight at the maximum, total commitments are 24,000 and gross payment on success is 5,400,000 units. Three successive full-utilization successes imply 16,200,000 units of gross payments, not net loss. If no other flows exist, the net cash outflow per full-utilization success is 5,376,000 units.

For the same hypothetical p and gross-payment convention, multiples of 150, 180 and 225 imply provider expected margins of 40%, 28% and 10%. These are illustrative parameter comparisons, not measured historical product terms. Independence may fail in real finite-population or correlated-event systems.

A history-dependent model can use B_t for total accepted commitments, I_t for a payment-triggering event, and M_t for the payment multiple:

Gross obligation L_t = M_t × B_t × I_t
Net cash movement from the product = B_t − L_t
B_(t+1) = f(B_t, previous visible outcomes, publicity, participant beliefs, promotional terms, participation constraints).

No empirical functional form for f is claimed. The issue is that B_t can rise after the same event that reduces the provider's liquid capacity.

## Three coupled candidate mechanisms

1. **Incentive shift:** higher advertised multiples may change participation even while the provider retains positive expected unit economics.
2. **Outcome-conditioned demand:** visible payouts can change subjective beliefs, participation and the concentration of commitments; the direction and magnitude require evidence.
3. **Competitive imitation:** an operator may copy a competitor's offer without comparable capital or liquidity capacity. Competitive pressure is a hypothesis, not proof of forced imitation.

External demand shocks differ from provider-induced demand. Capacity consequences also differ across stock-limited retail sales, guaranteed reservations, contingent payout contracts and uncapped API commitments. Do not confuse lost opportunity with a legally enforceable obligation.

## Design-time capacity admission — candidate

Before launch, evaluate the defined horizon, terms and maximum accepted obligations, liquidity and financing, plausible correlated utilization paths, early extreme sequences, participant response to public outcomes, permissible suspension rules and the explicitly chosen shortfall tolerance.

This is not a requirement to survive every logically possible infinite sequence. It is a requirement to make the assumed risk envelope and promise boundary explicit. Suspending new commitments after a loss cannot erase already accepted obligations.

## Research boundaries and tests

Potential overlaps: V9 As-of and release responsibility, V10 Survival-Bounded Planning, V13 Loop Gate, V14 Resource Justice, actuarial reserving, ruin theory, liquidity stress testing, behavioral demand and correlated risk models. FN147 addresses runtime repricing versus switching; this note addresses pre-launch acceptance of obligations. Distinct theoretical novelty remains UNKNOWN.

Next bounded research gates, not yet authorized:
- R1: source-level comparison with existing Canon and financial-risk models.
- R2: compare fixed utilization with outcome-conditioned participation under identical initial liquidity, product terms and positive per-unit expected value.
- R3: show whether a conventional stress-test baseline already catches the shortfall; identify a genuine incremental admission failure if any.
- R4: quantify false blocks, excess provisioning, cost and downstream burdens.
- R5: identify design owner, risk acceptor, operator and affected parties, preserving resource responsibility.

If existing risk controls suffice, keep the scenario as a teaching or regression case, not a new Canon.

## Handoff and closure

This is a public, impersonal mathematical research hypothesis. No personal history, specific real venue, verified customer psychology or observed operational failure is asserted.

Current Gate: research preservation PASS / Canon adoption HOLD.
Completion Line: public note and AI Reading Order link updated and remotely read back.
Missing Closure: prior-art comparison, counterexample, testing, threshold specification, incremental value.
No permission for new experiments, external outreach, runtime rule changes or Value-Locked additions.
