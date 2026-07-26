# Turn one AI incident into a paste-ready instruction rule

You do not need to share your repository, contact anyone, or post the
incident publicly.

Remove credentials, customer data, private code, and production secrets.
Then paste the prompt below into your own AI together with one incident.

## Use in three steps

1. Paste an incident description after removing confidential information.
2. Send the entire prompt to your own AI.
3. Review the returned rule before adding it to an existing instruction surface.

No account, installation, direct message, repository share, JSON edit, or CLI
command is required.

## Copy-paste prompt

```text
You are converting one observed AI workflow incident into one bounded,
paste-ready instruction rule.

Use only the incident evidence supplied below.

Do not:
- judge the operator's competence;
- invent a root cause;
- claim that the rule prevents future incidents;
- redesign the entire workflow;
- produce multiple competing fixes;
- require the user to understand a framework.

If information is missing, mark it UNKNOWN.
Choose exactly one first operational gap and exactly one priority fix.

Select the most appropriate target surface:
AGENTS.md, CLAUDE.md, system prompt, operational runbook, or an equivalent
project instruction file.

Return the following:

1. Incident As-of
2. First Operational Gap
3. Target Surface
4. Target Path or Placement
5. Intended Scope
6. Exact Paste-Ready Insertion Block
7. Required Completion Evidence
8. HOLD Conditions
9. BLOCK Conditions
10. Handoff Requirements
11. Rollback
12. Re-evaluation Trigger
13. Still UNKNOWN

The Exact Paste-Ready Insertion Block must:
- be usable without reading the analysis;
- require inspection of the canonical artifact or accepted state;
- require evidence before completion;
- stop on unresolved state disagreement;
- forbid silent retry, unauthorized overwrite, and guessed canonical state;
- preserve UNKNOWN items;
- name the next actor and next safe action;
- leave an exact restart point for the next human or AI.

Keep the analysis brief. Put the usable insertion block first after the
target recommendation.

Return a draft only. Do not edit or apply the target instruction surface.

INCIDENT:
<paste one sanitized incident, screenshot transcription, or log excerpt here>
```

## Paid Audit boundary

This self-service prompt returns a draft. The paid AI Application Workflow
Audit checks whether the rule addresses the right gap, belongs in the right
surface and scope, conflicts with existing instructions, has sufficient
completion evidence, and can be safely rolled back and handed off.
