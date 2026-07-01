# Field Note 101: Entry Window Radar - Mainline Note

## Classification

* Artifact type: V13 field note
* Line: Entry Window Radar
* Source note: V13 Field Note 1
* Root layer: V13
* Adjacent layers: V9 As-of, V10 Goal-Length, V12 Completion Integrity
* Status: Field Note / before new repo execution
* Gate: GO for recording / HOLD for implementation until Launch Capsule

## 1. What This Is

**Entry Window Radar** is an outward-facing acceleration-oriented OSS candidate for seeing which entry window an idea, GitHub repo, or README is currently in.

It is not a tool for predicting the future.
Uncertainty increases as the horizon moves farther out, so perfect prediction is impossible.

Its purpose is to use the currently visible market, competition, and operator execution capacity to judge **as-of whether a future line is worth betting on now**.

From V13, Entry Window Radar is an **external sensor for discovering, comparing, and re-evaluating future lines**.

V13 itself does not execute its output directly.
Entry Window Radar finds a future line, and V13 converts that future line into `GO / HOLD / CAP / BLOCK`.

## 2. Why It Emerged

When trying to explain V13 outwardly, "control," "stopping," and "governance" were hard to make people feel.

In AI circles, acceleration-oriented desires tend to resonate more strongly:

* build faster
* move without hesitation
* read the market
* know where to enter to win
* reduce waste before building
* know whether an idea is worth spending time on

Therefore, V13's judgment axis can be translated outward not as "control," but as **an acceleration device for quickly judging which future line is worth betting on now**.

## 3. Initial Target

The initial MVP should focus on **GitHub repos / READMEs**.

Reasons:

* GitHub OSS can directly pursue stars and forks.
* Codex / Claude Code / Cursor users can use it easily.
* Repos and READMEs provide artifacts that can be judged.
* If the first version expands to all artifacts, the diagnostic target becomes blurry.

Future expansion can apply the same entry-window model to:

* landing pages
* notes or articles
* X posts
* prompt packs
* prototypes
* demo videos
* app ideas
* partly written project proposals

Initial wording should lean toward repos / READMEs.
The design idea can still extend to artifacts more broadly.

## 4. Outward Copy Candidates

English:

> Your idea is somewhere on the market right now.
> Entry Window Radar shows you where -- and what's missing before the window closes.

Japanese:

> あなたのアイデアは今、市場のどこかにいる。
> 参入窓が閉じる前に、何が足りないかを見る。

Alternative:

> 今このアイデアに、本気で時間を使う価値があるかを見る。

## 5. Core Chart

The center of the free OSS version is one **Entry Window Chart**.

It has three lines.

### Market Line

Market growth, pain strength, demand, capital inflow, crowd movement, and major-player attention.

### Competition Line

Competition, major-player entry, LLM absorption risk, saturation, and price-down pressure.

### Operator Edge Line

The user's artifact, distribution capacity, execution conditions, past assets, credibility, and development speed.

Overlaying these three lines shows **where the current entry window is**.

## 6. Judgment Labels

Free OSS labels should use market and entry language, not control language.

* **FAST ENTRY**
  The entry window is open. It is worth entering small and fast.

* **NICHE WEDGE**
  There is still friction to cut off at the edge of incumbents or existing markets.

* **WAIT**
  The market may come, but it is too early or evidence is insufficient.

* **SHORT CYCLE**
  Long-term holding is dangerous, but a short build-and-recover cycle may work.

* **AVOID**
  Given market, competition, absorption, and distribution capacity, now is not the time to enter.

V13's `GO / HOLD / CAP / BLOCK` stays behind the surface.
Outwardly, the tool shows entry judgment labels.

## 7. Operator Edge Is the Differentiator

Ordinary AI can roughly inspect markets and competitors.

Entry Window Radar's difference is that it asks **whether this person, with this artifact, can take this market**.

The target is not the idea alone.

Look at:

* where it is the same as major players or existing services
* where the difference is
* who would pay for that difference and how much
* whether the person's artifact is showable
* whether there is a distribution path
* whether development speed and deadline fit
* whether past assets connect
* whether it can reach the line where authority winds begin to blow

## 8. Operator Edge Scoring Model

Operator Edge should not be scored from the AI's subjective impression.

First, build a base score from primary evidence.

### Base Evidence

1. **Artifact evidence**
   Repo, article, README, prototype, post, past results, and similar evidence.

2. **Distribution evidence**
   X, note, GitHub, Reddit, followers, engagement, ad capacity, community paths, and similar evidence.

3. **Execution conditions**
   Development speed, deadline, budget, available time, and distance to MVP.

4. **Personal hypothesis / past-asset connection**
   Why the user thinks they can win, and whether it connects to past articles, experience, expertise, or observation notes.

### Interaction Adjustment

Do not use simple addition.

* Add if artifact evidence and distribution evidence are both high.
* Reduce if artifact is strong but distribution is weak.
* Reduce for credibility and conversion if distribution is strong but artifact is weak.
* Add if past assets connect concretely to the current idea.

### AI Calibration

Opinions from Codex / MyGPT / Claude / Grok are not primary evidence.
They are calibration material.

* Do not let AI opinion move the score too much by itself.
* Do not adopt AI claims that ignore primary evidence.
* If multiple AIs produce similar conclusions from similar input, treat them as correlated signals, not independent evidence.
* Keep AI adjustment around -10 to +10 by default.

## 9. Definition of Confidence

Confidence is not prediction accuracy.

It is an **evidence-completeness score showing how much material was available for the as-of judgment**.

The first diagnostic is not a fixed verdict.
It is an as-of snapshot.
If the user adds more material, score and confidence can be updated.

## 10. Score-to-GO Bridge

The tool should not stop at the judgment label.

What the user actually wants to know is:

* What is the current score?
* What score is needed for FAST ENTRY?
* How many points are missing?
* Which item should be improved to reach it?
* If that item improves, will the market really buy?
* By when must it improve before the entry window closes?

The free version should output this lightly.

Example:

* Current Score: 60
* FAST ENTRY Threshold: 75
* Missing Delta: 15
* Biggest Bottleneck: distribution path
* Next Move: do not add features; get one reaction where the target audience already is

This shows the condition for getting closer to GO without rejecting the idea.

## 11. Mock-Exam Frame

Entry Window Radar is not a production pass/fail verdict.
It is a **mock exam** for the idea and operator.

High school students take mock exams not because the mock exam is the real entrance exam.
They take them because they want to know whether their current effort is moving them closer to their target school.

In the same way, Entry Window Radar does not predict the future.
It checks whether the direction of effort is moving closer to the entry window.

People do not buy prediction.
They buy **relief that their effort is not accumulating in the wrong direction**.

## 12. Free and Advanced Boundary

### Free

As-of fixed-point diagnostic.

* Entry Window Chart
* current position
* strengths
* missing pieces
* one biggest bottleneck
* one next move
* confidence
* missing evidence

The free version should be forward-moving.
It should not negate or stop the user, but say, "If you do this, start here."

### Pro / Advanced

Track lines and trajectories.

* Score History
* Entry Window Drift
* Operator Edge trajectory
* Aspire / Goal-Length changes
* Resource Budget Fit
* Proof Cost
* Runway
* Value Ceiling
* Branch Debt
* Re-entry Capacity
* whether effort is affecting the score
* whether enough slack exists to rest
* whether the user should hurry

The free version shows the current point.
The Pro version shows lines and trajectories.

## 13. Premise Contract

Before diagnosis, the goal must be fixed.

The same idea receives different judgments under different goals.

* learning
* side-income
* exposure / credibility
* client delivery
* long-term business foundation
* early withdrawal judgment
* burnout prevention

If the goal is to earn a specific monthly amount by a specific month, the judgment becomes stricter.
If the goal is learning, a candidate track, or the first public piece, do not cut too harshly.

It is important not to kill the user's seed here.

## 14. Tone Principles

This tool does not blame the maker or idea.

Bad wording:

* This idea is weak.
* Development is slow.
* You have no distribution capacity.

Better wording:

* Similar services are common, so the difference is currently hard to communicate.
* At the current pace, the entry window may narrow before the artifact reaches a competitive level.
* Taking a reaction before more development may protect upside better.

Phrase it as current market position, not personality evaluation.

## 15. MVP Input

The initial MVP focuses on GitHub repos / READMEs.

Input candidates:

* `artifact.md`
  Repo / README / artifact text.

* `evidence.md`
  Market information, competitor URLs, posts, user pain, reference articles.

* `operator.md`
  Goal, deadline, distribution path, budget, available time.

* `ai_profile.md`
  Strengths, weaknesses, background, and goals organized by the user's GPT / Gemini / Claude / Grok.

Do not require everything at first.
If material is missing, return an as-of diagnosis from the available material.
If the user adds material, re-evaluate.

## 16. MVP Output

* `report.md`
* `chart.json`
* `decision.md`
* `validate_prompt.md`

If possible later:

* `entry_window.png`

PNG output is easy to share on GitHub or X and helps spread the acceleration-oriented framing.

## 17. V13 Connection

Entry Window Radar is not V13 itself.
It is an outward-facing acceleration-oriented OSS candidate to split into a new repo.

From V13, it is a **Future Line Discovery Engine**.

Structure:

```text
V13
-> needs the next future line
-> calls Entry Window Radar
-> inspects Market / Competition / Operator Edge
-> receives FAST ENTRY / NICHE WEDGE / WAIT / SHORT CYCLE / AVOID
-> converts through V13 into GO / HOLD / CAP / BLOCK
-> returns execution results as evidence
```

Entry Window Radar looks for future lines.
V13 decides whether to run that future line.

## 18. Implementation Gate

At this point, the idea is sufficiently shaped to move toward execution.

However, creating the new repo must follow this sequence:

1. Save this V13 Field Note.
2. Create a V13-side Launch Capsule.
3. Fix Purpose / Non-purpose / MVP Completion Line / CAP conditions / prohibited actions.
4. Pass the capsule to the new repo.
5. Create the `entry-window-radar` repo.
6. If the repo starts successfully, return it to V13 as a case.

Do not create the repo without a Field Note.

## 19. Current Completion Line

Entry Window Radar now exists as an outward-facing acceleration-oriented OSS candidate derived from V13.

Next needed:

1. Save this Field Note in V13.
2. Separate derivative elements into a second note.
3. Create a Launch Capsule.
4. Confirm the GO conditions for starting the new repo.

This note is the first note in the Entry Window Radar line.
The second note should separate and record Delivery Scope Radar / Resource Justice / V14 elements / derivative candidates.
