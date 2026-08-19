# AI Tutorial Capsule

This repository can be read by a human, but it can also be read by your AI assistant.

Use this capsule when you want your AI to explain V13 LoopKit, guide a
capacity-aware first use, or review whether the repo has enough first-use
onboarding.

## First-contact onboarding rule

If the user asks for onboarding, do not rely on the onboarding page alone.

In this repository, a natural request such as
`外部知能を使ってみたいんだけど、何から始めればいい？` refers to the
repository-memory External Intelligence tutorial unless the user explicitly
asks to delegate to another model. Do not route that phrase to ChatGPT
delegation, plugin setup, or a single prescribed exercise.

First inspect `README.md`, `AGENTS.md`,
`docs/external_intelligence_onboarding.md`, `docs/ai_reading_order.md`, and
`docs/field_note_lifecycle.md`. Briefly explain only the External Intelligence
mechanisms those repository surfaces support, then disclose what was and was
not inspectable. Do not infer missing implementation.

Read `docs/codex_tutorial_guide.md` only when the requested explanation needs
the wider on-demand framework map.

Follow the `First Response Contract` section. For Japanese first contact, show
the External Intelligence Quest Board before asking diagnostic questions or
recommending a starting structure. Keep all six core areas plus `GRADUATE`,
`Little OSI`, `Little Compactor`, and the multi-AI
`External Intelligence候補があります` idea visible rather than compressing
them out of the first screen. Render the
participant-facing block from `docs/external_intelligence_onboarding.md`
instead of paraphrasing it into a shorter menu.

Wait for the user to choose, explore, say what they already use, ask to see
everything, or request a recommendation. Viewing or selecting a Quest does not
authorize setup or file changes.

The public Quest Board is a no-fork showroom. Do not require a Fork, clone,
repository attachment, Codex project, setup, or file change before showing it.
After selection, inspect only the actual rules, docs, relevant Field Notes, and
public implementation needed for that Quest before explaining it. Offer the
`🔓 Full Experience — Forkして体感する` CTA only after that explanation or a
small trial when the user expresses interest in growing their own workspace.

After the map, use the conversation and repository to recognize what the user
already has. Ask only about missing facts that change the recommendation. Do
not classify the user as a beginner from one unfamiliar tool or term.

Recommend at most one currently useful starting structure only when the user
asks what fits, or help with the Quest they selected. Do not explain V12, V13,
Field Notes, promotion, handoff, and every Gate together unless the user asks
for the full framework.

A Quest name is not proof that its complete implementation is public. Little
Compactor is represented here by an entry concept and a research-candidate
document; do not invent a shipped public implementation. Forking does not
expose private repositories, unpublished separate artifacts, private memory,
or upstream internal trajectory absent from public `main`.

Treat the guided exchange as one bounded onboarding task. Do not append the
full canonical completion report to every in-progress conversational turn;
emit it when the selected use and restart point close, or when a real blocker
ends the onboarding.

In a third-party fork, do not inherit Shin as that fork's Decision Owner.
Identify the fork's owner or maintainer from current evidence; if it is not yet
known and does not affect the read-only first step, leave it unresolved.

Do not edit files during onboarding.

If the user asks to graduate, present `KEEP / MANUAL / REMOVE / NOT NOW` and
wait. Never graduate the user automatically. Before `MANUAL` or `REMOVE`, show
the proposed tutorial-only file changes and obtain explicit approval. Preserve
the user's memory, notes, handoff, reusable intelligence, rules, and V12/V13
operation.

## Recommended onboarding prompt

Use the single primary copy block under `まず試してみる — Fork不要` in
`README.md`. It binds the fresh AI to the public repository, the five minimum
first-contact files, compact access disclosure, the full Quest Board, and the
post-selection deep-read boundary.

## 1. Generate an adaptive tutorial

Copy this prompt into your AI assistant:

```text
Read this repository and guide me from my current level.

Focus on:
- what problem this repo solves
- the available External Intelligence Quests
- what I already use for instructions, memory, and handoff
- the one selected structure, or one recommendation if I ask what fits
- one concrete use of that structure
- the condition that would justify adding another structure later

Read README.md, AGENTS.md, docs/external_intelligence_onboarding.md,
docs/ai_reading_order.md, and docs/field_note_lifecycle.md first.
Use other docs and examples only when the current choice requires them.
State what you could and could not inspect, then show the Quest Board before
choosing or recommending a starting structure.
Wait for my selection before setup or file changes.
Do not invent features that are not in the repo.
Do not treat a recorded observation as a promoted Rule.
End with a restart point.
```

## 2. Review first-use onboarding

Copy this prompt into your AI assistant:

```text
Review this repository for first-time onboarding.

Check whether a new user can quickly understand:
- what this repo is for
- where to start
- what GO / HOLD / CAP / BLOCK means
- where the first tutorial or first-use example is
- how to avoid over-expanding the loop
- what not to modify without approval

If something is missing, suggest the smallest edit.
Do not propose a broad redesign.
```

## 3. Suggest the smallest onboarding edit

Copy this prompt into your AI assistant:

```text
Read the README and onboarding docs.

Suggest the smallest edit that would help a first-time user start.

Rules:
- one edit only
- no new features
- no automation
- no hooks
- no MCP
- no pluginization
- no broad productization
- prefer a link, sentence, or short section over a rewrite
```

## 4. Expected good output

A good AI-generated tutorial should:

- explain the repo in plain language
- show the External Intelligence Quest Board before prescription
- preserve user choice and wait before setup or file changes
- avoid repeating layers the user already operates
- select at most one structure after the user chooses or requests advice
- help the user use that one structure once
- preserve the observation / reusable-candidate / promoted-Rule boundary
- leave a restart point and a condition for adding anything else
- avoid turning LoopKit into an execution engine
- avoid claiming model self-training or automatic Canon growth
- keep the human as the decision owner

## 5. What not to do

Do not ask your AI to:

- create new features without approval
- rewrite the repo broadly
- add hooks, MCP, plugins, or automation
- convert LoopKit into a full agent framework
- skip the human decision owner
- treat GO / HOLD / CAP / BLOCK as automatic execution
- load all Field Notes for first contact
- treat user capability as unlimited attention or confirmation capacity
