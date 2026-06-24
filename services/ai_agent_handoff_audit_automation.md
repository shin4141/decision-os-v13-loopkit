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
