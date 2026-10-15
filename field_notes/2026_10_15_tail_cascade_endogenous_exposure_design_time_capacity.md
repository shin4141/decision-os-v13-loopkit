# Field Note — Tail Cascade × Endogenous Exposure × Design-Time Capacity

As-of: 2026-10-15 JST
Status: Research candidate; Canon adoption HOLD
Primary holding layer: V13 Field Notes; conceptual connections to V9, V10, V14
Decision Owner: Shin
Evidence class: owner recollection + explicitly hypothetical calculations, NOT observed casino financials or tested software failure
Current Gate: preservation GO / new rule, publication and implementation HOLD

## Central question

A firm can rationally forecast ordinary utilization yet offer a contractual maximum much higher than that forecast. What if a rare payout increases subsequent participation, stakes and imitation by competing firms, while reducing the firm's own remaining liquidity? A positive per-bet expected value is not proof of capacity to honor the offered terms from the first day.

**Forecast utilization ≠ accepted obligation ≠ liquid capacity.**
**The competitor's payout schedule can be copied; the competitor's capital buffer cannot.**
**Stopping after a loss is not a substitute for viable commitments made before launch.**

The question concerns design-time product admission, not merely runtime stopping, repricing or loss cutting.

## Owner recollection: preserve uncertainty

About twenty years ago, the owner saw baccarat side bets described as a two-point draw in venues around Yokohama and Saitama. In the owner's recollection, Yokohama had greater popularity and stronger competition; Saitama sometimes offered around 150x, while Yokohama normally offered around 180x and a weekly promotional event around 225x. The venue reportedly held various events on different days (including bingo); this promotion was not especially interesting to the owner personally. The owner suspects participation increased on 225x days; this is not a counted observation.

Remembered rules: six decks, roughly fifty rounds per shoe, approximate hit probability 1/250, single-player stake cap around JPY 3,000, up to eight seats, independent side-bet participation. All numbers and actual venue rules are unverified, and whether quoted multipliers include stake is unknown. The remembered ordinary-draw odds and house-edge numbers are internally inconsistent and must not be treated as established.

The owner recalls seeing an experienced player reveal at least two consecutive winning two-point draws, perhaps three (uncertain). Observers reacted as if the player had special skill and offered substantial tips. This is a recollected behavioral observation, not evidence that subsequent betting or financial exposure actually reached its cap.

The owner conjectures some customers might mistakenly perceive 225x as positive-EV, and that recent wins or word of mouth could increase participation. No direct statements from those customers or verified betting logs establish their beliefs. Avoid labeling all participants as addicted or irrational.

## Illustrative math, conditional on assumptions

Assume independent win probability p=1/250, gross return multiplier M=225 including stake, max stake JPY 3,000 per person and 8 people. Then a JPY 3,000 bet has expected gross return 3,000×225/250=JPY 2,700 and expected house profit JPY 300 (10% edge). At maximum simultaneous participation, total stakes JPY 24,000 and gross win payout JPY 5.4 million. Three consecutive full-cap wins imply gross payouts JPY 16.2 million, not net loss; net cash outflow per full-cap win is JPY 5.376 million if no other flows.

With the same hypothetical p and gross-return convention, M=150/180/225 implies house edge 40%/28%/10%, respectively. These are *not* verified historical house edges. Real shoe probabilities can depend on remaining cards and the exact side-bet definition. Two or three wins can occur from the first rounds; 1/250 does not mean a mandatory waiting period.

For a simplified path, let B_t be total stakes and I_t indicate a win. Gross payout L_t=M_t B_t I_t; cash movement from these bets is B_t-L_t. Exposure can be history-dependent: B_(t+1)=f(previous payouts, publicity, participant beliefs, competing offers, available seats, limits). No particular functional form or empirical coefficient is established.

The crucial distinction is not merely that the maximum payout is knowable, but that normal observed utilization can be low while payout-induced participation and correlated stakes concentrate risk when available liquidity is already reduced.

## Three coupled mechanisms (hypotheses)

1. **Incentive design:** a weekly 225x promotion may raise participation even if house EV remains positive.
2. **Outcome-conditioned exposure:** salient wins may change beliefs, participation, stakes and publicity; the same win depletes liquidity and may increase the next liability.
3. **Competitive imitation:** smaller operators may copy an attractive multiplier set by larger operators without comparable capital capacity. The owner recalls regional differences, but competition causing those differences is unverified.

Distinguish external demand shocks (viral menu) from internally induced demand (promotion or winning streak). A restaurant can sell out without promising unlimited supply; a casino that has accepted a bet incurs a defined payout obligation. Similarly, an API free tier, insurance benefit or rewards program may impose different obligations depending on actual terms. Do not collapse opportunity loss, reputational loss and contractual payment insolvency into one category.

## Design-time capacity admission — research formulation

Before publishing terms, evaluate: time horizon, accepted contractual maximum, plausible correlated participation and stake paths, repeated early payouts, liquidity and financing availability, acceptable shortfall probability, contractual limits, and whether any post-event suspension is valid under the terms already accepted. This is **not** a demand for survival under every logically possible infinite sequence.

A candidate criterion is a bounded risk of liquidity shortfall under explicitly chosen history-dependent behavioral scenarios, together with the ability to honor already accepted obligations. Scenario choices, tolerance thresholds and liability assumptions require human owner judgment; they are not established by this note.

## Existing research overlap and falsification

Potential overlaps: V9 As-of and release responsibility; V10 Survival-Bounded Planning; V13 Loop Gate; V14 Resource Justice; financial ruin theory, insurance reserving, stress testing, liquidity risk, correlated exposure and behavioral demand models. FN147 concerns *runtime state repricing versus strategy switching* and is distinct from *pre-launch obligation/capacity admission*. No exhaustive source comparison has been performed. No novelty or patentability claim.

Research gates, **not authorized for execution by this preservation step**:
- R1: compare exact existing Canon and established financial-risk models, preserving citations and As-of.
- R2: construct paired cases with identical initial capital, terms and positive single-bet EV but fixed versus outcome-conditioned participation, including a competitive-mimic variant. Compare shortfall probability and liquidity paths.
- R3: show a concrete existing admission or agent-planning failure that a new condition catches, versus an adequate existing stress-test baseline.
- R4: assess cost, false blocks, conservative overprovisioning, customer restrictions and effects on smaller firms.
- R5: separate design owner, risk acceptor, operator, customers and post-failure burden; do not shift cleanup onto customers or Shin.

If established risk controls already catch the counterexample, retain this as an explanatory Field Note or regression scenario, not a new Canon.

## Handoff and completion

This note is a bounded research preservation artifact only. It does not alter runtime permissions, Loop Gate behavior, released manuscripts, Value-Locked Pattern Memory, public product promises or contracts. No new experiments, public posts or external outreach authorized.

Current Gate: Field Note preservation GO; Canon adoption HOLD; research testing HOLD.
Completion Line: note preserved in repository, remotely readable and indexed.
Missing Closure: established-source overlap, counterexample, comparative tests, design threshold and independent incremental value.
Next actor for any separately authorized bounded verification: Codex. Decision Owner remains Shin.
