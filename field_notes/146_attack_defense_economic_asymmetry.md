# Field Note 146 — Attack–Defense Economic Asymmetry

Date: 2026-10-09

As-of: 2026-10-09 JST

Status: Field Note candidate / Verification pending

Japanese status: Field Note候補／検証待ち

Evidence state: Direct field observation plus bounded external signals

## Purpose

This note preserves a structural concern observed across recent security work:

```text
attack automation becomes cheaper and easier to scale
while defensive contribution remains expensive to produce
and difficult to fund
```

The concern is not that open source contribution is inherently exploitative, nor that every company should pay every contributor. The question is whether the economic system for defensive work is becoming too asymmetric as offensive automation scales.

## Observation

Recent work exposed a recurring pattern.

On the attack side, AI-assisted reconnaissance, vulnerability discovery, and intrusion workflows can reduce the marginal cost of testing additional targets. A successful attacker can automate broad search and deepen only the paths that work.

On the defense side, a useful repair can still require a human contributor to:

- reproduce the failure;
- isolate the boundary or root condition;
- design a repair;
- implement the patch;
- add regression coverage;
- respond to review;
- maintain context until merge or release.

The benefit of that work may be distributed across a project, company, and user base, while the labor cost remains concentrated on the contributor.

This creates a possible asymmetry:

```text
offensive scale advantage
+
distributed defensive benefit
+
concentrated contributor cost
=
defensive sustainability risk
```

## Field signal

In recent commercial and OSS outreach, a recurring distinction became visible:

```text
technical acceptance != commercial purchase
```

Some projects explicitly prefer a normal open-source pull request rather than a paid repair. That can be a legitimate project policy. However, if complex defensive work is routinely expected to arrive as unpaid contribution, the system can depend on contributors absorbing investigation and repair costs that the benefiting organizations do not directly bear.

The present observation does not establish that contributors will stop contributing, that a given organization is underpaying contributors, or that paid repair is the correct model for all open-source maintenance.

## Core hypothesis

Attack automation may be becoming economically scalable faster than defensive contribution is becoming economically sustainable.

```text
Attack automation is becoming economically scalable
faster than defensive contribution is becoming economically sustainable.
```

If this persists, the practical bottleneck may shift from "can the bug be found?" to:

```text
who is willing and able to absorb the cost of proving and repairing it?
```

## Resource Justice interpretation

This pattern is relevant to Resource Justice.

A local optimization can be rational for each actor:

- the company minimizes external repair spend;
- the project receives a useful patch;
- users benefit from the improvement;
- the contributor receives reputation or credit.

But system-wide, the arrangement may transfer:

- investigation time;
- verification burden;
- patch construction;
- regression design;
- review response;
- and opportunity cost

onto the contributor.

The transfer is not necessarily unjust in every case. It becomes a Resource Justice concern when the benefiting side treats the contributor's cost as effectively free while the contributor repeatedly absorbs unrecovered work.

## V13 / Loop Gate relevance

This also creates a compound-loop question.

If the loop is:

```text
find defect
-> prove defect
-> repair defect
-> contribute patch
-> receive recognition
-> repeat
```

then recognition alone is not proof that the loop is sustainable.

A V13-style loop review should ask:

- Does each repetition reduce future burden?
- Does the contributor gain reusable leverage, authority, payment, or durable reputation?
- Is the next loop funded by accumulated value, or only by more unpaid effort?
- Is the loop still advancing Aspire, or merely producing externally captured value?

A loop that repeatedly produces public benefit while depleting the contributor may require CAP even if each individual PR is technically successful.

## Non-claims

This note does not establish:

- that open source contribution should always be paid;
- that companies are acting maliciously;
- that paid repair markets are the only solution;
- that AI-assisted attacks are uniformly cheap or autonomous;
- that any specific breach would have been prevented by a paid contributor;
- that contributor credit has no value;
- or that current evidence proves a broad labor-market effect.

## Recheck conditions

Strengthen or revise this hypothesis when evidence accumulates on:

- marginal cost of AI-assisted offensive campaigns;
- time and cost required for independent defensive reproduction and repair;
- conversion from accepted technical work to paid follow-on work;
- contributor retention after repeated unpaid repairs;
- bounty / sponsorship / paid-maintenance models;
- release-note, changelog, and reputation effects on contributor opportunity;
- and cases where defensive automation materially lowers contributor cost.

## Completion Line

Field Note 146 preserves a candidate system-level asymmetry:

```text
attack cost is scaling downward
while defensive repair burden remains concentrated
and commercial capture remains weak
```

It remains a verification-pending field observation. It changes no V13 Canon, no public pricing, no contribution policy, and creates no execution authority.
