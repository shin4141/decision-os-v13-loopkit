# End-of-Chat Salvage Pass

## Observation

AI conversations often produce more useful material than the user can act on immediately.

Some ideas are used right away.

Some are clearly irrelevant.

But many sit in the middle:

- not ready now
- not part of the immediate next action
- not worth turning into a full task yet
- but too valuable to lose

If these fragments are not captured, they disappear into the chat history.

## Core claim

Before closing a long AI conversation, the AI should help separate restart material from future-value material.

This prevents two opposite failures:

1. putting everything into handoff and making handoff too heavy
2. discarding weak-but-important ideas that may later converge into future decisions

## Three entry routes

There are three ways a Field Note candidate can be captured.

### 1. User-declared

The user explicitly says:

```text
This feels important.
Save this as a note.
This may matter later.
Do not lose this idea.
```

This is high-confidence because the user is signaling personal value.

### 2. AI-detected

The AI notices a potential future-value signal and asks whether to preserve it.

Examples:

```text
This may be worth preserving as a Field Note.
This seems like a reusable failure pattern.
This may connect to a future article, product, or decision.
Should I save this as a Field Note candidate?
```

The AI should not save everything automatically.

It should surface candidates when the signal is strong.

### 3. End-of-chat salvage

At the end of a long conversation, the AI summarizes:

- what is needed for next restart
- what may be worth preserving as Field Notes
- what can be discarded

This is the most user-friendly path for ordinary users.

The user does not need to identify every valuable fragment while thinking.

## Handoff vs Field Note

Do not mix V12 handoff and Field Notes.

### Handoff

Handoff is for immediate restart.

It should answer:

```text
What does the next AI or human need in order to continue safely?
```

Handoff should be concise, current, and operational.

### Field Note

Field Notes are for future value.

They capture:

```text
What is not needed for immediate restart, but may become future decision, article, product, research, story, or prevention material?
```

Field Notes can preserve weak or partial signals.

They should not make the handoff heavy.

## End-of-Chat Salvage Pass format

At the end of a long conversation, return:

```text
# End-of-Chat Salvage Pass

## V12 Handoff
What must be preserved so the next AI/human can restart safely?

## Field Note Candidates
What ideas, failure patterns, questions, metaphors, or signals may create future value if preserved?

For each candidate:
- title:
- why it may matter later:
- related layer: V11 / V12 / V13 / other
- suggested action: save / park / ignore

## Discard
What can be safely treated as transient or already-covered conversation?
```

## What to preserve

Preserve candidates such as:

- a newly named concept
- a repeated discomfort or unresolved question
- a failure mode that could recur
- an idea that may become a post, article, product, story, or research section
- a metaphor that makes a complex idea easier to explain
- a weak signal that may later combine with other weak signals
- a distinction that prevents future confusion
- a boundary or stop condition that protects future work

## What not to preserve

Do not preserve by default:

- ordinary emotional drift
- one-off comments with no future use
- duplicates of existing notes
- ideas with no clear future retrieval path
- vague excitement without a named signal
- material that belongs only in immediate handoff
- private details that do not need to become durable memory

## Why this matters

Ordinary generative AI users may not want to manage notes manually during a conversation.

They may prefer the AI to help at the end:

```text
Here is what you need to restart.
Here are the ideas worth saving.
Here is what can be ignored.
```

This turns AI conversation from disposable chat into a reusable idea stream.

## V11 / V12 / V13 connection

V11:
preserve fragments so they can be reconnected later.

V12:
preserve the minimum state needed to restart safely.

V13:
decide whether preserved fragments justify a next loop, remain parked, or should be ignored.

## One-sentence summary

End-of-Chat Salvage Pass separates immediate handoff from future-value fragments so important ideas are not lost and handoff does not become overloaded.

## Boundary

Do not implement automation now.

Do not create a new product now.

Do not modify README now.

Do not modify AGENTS.md / CLAUDE.md now.

Do not create a new skill now.

This note only records the operating pattern.

## Status

Signal captured.

No automation.
No README change.
No productization.
No new skill.
