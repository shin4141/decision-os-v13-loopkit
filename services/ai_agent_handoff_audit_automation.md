# AI Agent Handoff Audit Automation

## Goal

Reduce manual outreach burden for the AI Agent Handoff Audit service.

The system should find candidate repos, identify one concrete AI-agent workflow friction, generate a small free audit point, and draft a contact message.

It must not contact anyone without human approval.

## Core principle

Automate discovery and drafting.

Keep human Seat for contact.

```text
AI finds candidates.
AI drafts the audit.
AI drafts the message.
Human approves SEND / HOLD / SKIP.
Only then contact is made.
```

## Pipeline

### 1. Candidate discovery

Find public repos that show signs of AI-agent workflow usage:

- `CLAUDE.md`
- `AGENTS.md`
- `CODEX.md`
- `.cursor/rules`
- Claude Code
- Codex
- Cursor
- AI handoff
- agent workflow
- subagent
- MCP agent
- automation PR flow
- long-running coding agent sessions

Return at most 10 candidates per run.

### 2. Candidate filtering

Skip candidates when:

- no visible agent workflow exists
- friction is too generic
- repo is inactive
- no safe outreach route exists
- outreach would look spammy
- the repo already solves the issue better than LoopKit
- the candidate is a competitor where contact would feel self-promotional

Prefer candidates when:

- they already use AI coding agents
- they have public agent instruction files
- they have open issues related to summaries, handoff, PR automation, context, or follow-up
- the audit point can be stated in one concrete sentence

### 3. Friction extraction

For each candidate, identify:

- visible AI-agent signal
- likely friction
- evidence from public files/issues
- one small risk if left unchanged
- one 0.01 improvement
- relevant LoopKit copy-paste file

Useful LoopKit files:

- `copy-paste/claude-md-thin-base.md`
- `copy-paste/next-action-confidence-check.md`
- `copy-paste/restartable-handoff.md`

### 4. Outreach route detection

Classify route:

- GitHub issue
- GitHub discussion
- public email
- X
- website contact form
- no safe route

Prefer existing issues when the comment is directly relevant.

Avoid opening new issues unless the repo clearly accepts suggestions.

### 5. Draft generation

Generate one short message.

Message must:

- start from the repo's visible context
- mention one concrete friction
- offer one small suggestion
- include one relevant LoopKit link only if useful
- avoid broad Decision-OS explanation
- avoid sales language
- avoid "free audit" language unless the user has invited it
- avoid pressure

### 6. Human approval gate

Before contact, output:

```text
Candidate:
Route:
Evidence:
Draft:
Risk: LOW / MEDIUM / HIGH
Recommendation: SEND / HOLD / SKIP
```

No contact may be made until Shin explicitly approves `SEND`.

## Contact Readiness Card

Before recommending `SEND`, produce a Contact Readiness Card.

No message should be sent unless this card is complete.

```text
Contact Readiness Card

Candidate:
Repo:
Route:
Target URL:

Evidence depth:
E0 = search result only
E1 = README / top-level files checked
E2 = relevant agent instruction or workflow file checked
E3 = relevant issue / PR / code path checked
E4 = repo-specific friction confirmed from multiple public sources

Required for SEND:
At least E2.
Prefer E3 when commenting on an existing issue.

What was inspected:
-
-
-

Why this repo fits:
<one concrete reason>

Why this route fits:
<why GitHub issue / discussion / email / X is appropriate>

Visible friction:
<one concrete friction point>

Proposed 0.01:
<one small improvement>

Message type:
- issue comment
- new issue
- discussion reply
- email
- X reply
- hold

Risk:
LOW / MEDIUM / HIGH

Risk reason:
<why this may be welcomed, ignored, or feel spammy>

Estimated probability:
- Reply probability:
- Adoption probability:
- Useful learning probability:

Waiting rule:
<how long to wait before considering the contact closed>

Default:
- GitHub issue/comment: wait 7 days, no follow-up unless they reply
- Email/DM: wait 7 days, no follow-up unless there is a clear reason
- Public social reply: no follow-up unless they engage

Success definition:
<what counts as success>

Failure definition:
<what counts as no signal>

Learning if no reply:
<what this contact teaches even if ignored>

Next action if success:
<one action>

Next action if no reply:
<one action or HOLD>

Recommendation:
SEND / HOLD / SKIP
```

## SEND rules

`SEND` is allowed only when:

- the contact route is public or clearly appropriate
- the friction is repo-specific
- the message is useful even if the person never replies
- the message is short
- only one LoopKit link is included
- no pressure, hype, or broad Decision-OS explanation is included
- Shin only has to approve and paste

`HOLD` when:

- the repo seems relevant but the evidence depth is too shallow
- the message would require more context than the AI has
- the outreach route is unclear
- the suggestion may look self-promotional

`SKIP` when:

- the friction is generic
- the repo is inactive
- no safe route exists
- the suggestion would look like spam
- the repo already solves the issue better than LoopKit

## Probability guidance

Use rough estimates, not false precision.

For a cold GitHub issue/comment:

- Reply probability is often low.
- Adoption probability is lower.
- Useful learning probability may still be meaningful if the friction is well matched.

Example estimate:

```text
Reply probability: 10-20%
Adoption probability: 3-8%
Useful learning probability: 40-70%
```

Do not present these as facts.

They are planning estimates only.

## Boundary

The AI may recommend.

Shin decides.

Automatic contact remains `BLOCK`.

Mass outreach remains `BLOCK`.

### 7. Contact logging

After contact, record:

```text
Repo:
Route:
Date:
Message type:
LoopKit link used:
Status: SENT / REPLIED / NO REPLY / CLOSED / CONVERTED / SKIP
Next check:
```

### 8. Follow-up rule

No automatic follow-up.

A follow-up is allowed only if:

- the recipient replies
- there is a direct question
- the repo owner asks for more detail
- Shin explicitly approves a follow-up

## Output format for discovery run

```text
Candidate 1:
Repo:
Signal:
Evidence:
Friction:
Free audit point:
0.01 improvement:
Useful LoopKit file:
Outreach route:
Risk:
Recommendation:
```

## Safety boundaries

Do not spam.

Do not send mass automated emails.

Do not create GitHub issues automatically.

Do not comment automatically.

Do not contact high-risk candidates.

Do not contact competitors with generic suggestions.

Do not pretend to be a user of the repo if not true.

Do not overstate LoopKit.

Do not claim guaranteed productivity gains.

## V13 gate

Discovery run:
`GO`

Automatic contact:
`BLOCK`

Human-approved single contact:
`CAP`

Mass outreach:
`BLOCK`

## Status

Automation design captured.

No implementation yet.
No scraping tool added.
No email sender added.
No GitHub bot added.
No workflow automation added.
