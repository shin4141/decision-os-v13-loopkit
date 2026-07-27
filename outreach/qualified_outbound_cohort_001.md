# Qualified Outbound Cohort 001

Status: REVIEW ONLY — no contact authorized
Research cut-off: 2026-07-27 JST
Base commit: `3c9142692dfe60785a033b91ad7b6e5226712a93`
Cohort: 20 organizations (Group A: 10; Group B: 10)

## Admission and evidence rules

Every admitted candidate scores at least 8/10 on the five requested dimensions. `Observed` means the public record contains a reproducible trace, log, or bounded before/after result. `Owner-reported` means an affected operator described the incident. `Inferred` means the failure window is demonstrated by source-path analysis but no live occurrence is claimed. A closed issue is evidence of the past operational boundary, not evidence that the defect still exists.

Authority scores distinguish a named or designated buying/partnership function (`2`) from an official commercial or general route with routing authority but no verified technical budget owner (`1`). No personal address, guessed address, commit metadata, issue comment, or private identity source is used.

Before admission, the organizations were compared with repository outreach records and a read-only Gmail Sent search from 2026-06-01 onward. Previously contacted organizations and people—including miryo.AI and every earlier V9/13-13 wave recipient—are excluded. Prior emails and the 2026-07-26 follow-ups are not part of this cohort or its denominator.

## Priority 1 — Letta

1. **Candidate / organization:** Letta
2. **Group:** A
3. **Role and decision authority:** Agent-runtime product/engineering owner, routed through Letta's official business contact form. The form can route a technical proposal, but the individual budget owner is not public.
4. **Official public source:** [Letta contact](https://www.letta.com/contact/) and [API plans](https://docs.letta.com/guides/cloud/plans).
5. **Concrete observed incident or operational gap:** A mid-run crash left unmatched tool messages in persistent agent state. One affected agent had 20 broken messages out of 37, hit the condition twice in 48 hours, and required manual reconstruction of the full `message_ids` array before any later run could proceed.
6. **Evidence class:** owner-reported
7. **Exact evidence URL:** https://github.com/letta-ai/letta/issues/3250
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Tool-call pairing, crash recovery, approvals, compaction, and provider-format validation are shared run-boundary concerns across every stateful agent and model provider.
10. **First operational rule shown in advance:** Persist `tool_call` and `tool_return` as one run-boundary unit; on failure, roll back the pair or quarantine it before the next model request.
11. **Unresolved questions:** Did the repair cover every crash path or only the reported sequence? Is orphan validation enforced before every provider call? Is there a durable repair receipt for automatic cleanup?
12. **Proposed offer:** bounded implementation
13. **One small CTA:** Ask for a 20-minute call with the owner of run-state recovery.
14. **Verified professional contact route:** Official business form — https://www.letta.com/contact/
15. **Personalized subject line:** A bounded run-boundary check for Letta's orphaned tool-message recovery
16. **Complete email draft:**

> Hello Letta team,
>
> Your public issue #3250 records a sharp recovery boundary: after a mid-run crash, 20 of 37 persisted messages were broken, the agent was blocked on every later run, and the operator had to reconstruct `message_ids` manually. One rule I would put in front of that path is: persist `tool_call` and `tool_return` as one run-boundary unit; on failure, roll back or quarantine the pair before the next provider request.
>
> The public record leaves three questions: whether every crash path now reaches the same cleanup, whether validation runs before every provider call, and whether automatic repair emits a durable receipt.
>
> I can implement a bounded failure-injection and repair-receipt slice around this boundary, without replacing your runtime design. Would the owner of run-state recovery be open to a 20-minute scoping call?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The issue is closed and may already be fully repaired. The form is designed around business use cases, not unsolicited engineering vendors; stop if the pre-send DOM requires Canon-external data.
18. **Recommended send priority:** 1

## Priority 2 — Temporal

1. **Candidate / organization:** Temporal Technologies
2. **Group:** B
3. **Role and decision authority:** Agency/System Integrator Partnerships team, an explicitly designated route for joint delivery and service-line partners.
4. **Official public source:** [Temporal Partners](https://temporal.io/partners).
5. **Concrete observed incident or operational gap:** A production TypeScript worker handling about 100 workflow types exhausted a 6 GB heap during bursts; at times all workers entered crash-loop backoff and processing resumed only after a person manually scaled the fleet.
6. **Evidence class:** owner-reported
7. **Exact evidence URL:** https://github.com/temporalio/sdk-typescript/issues/2227
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 2 + ability to pay 2 + recurrence 2 = **10/10**
9. **Why this may recur or expand:** Cache admission, replay, worker sizing, and burst recovery repeat across customer deployments, SDKs, and AI-agent workloads; Temporal also maintains an agency/SI ecosystem.
10. **First operational rule shown in advance:** Admit workflows to cache against an explicit memory budget; evict or backpressure before OOM, and bind the capacity decision to a load-test receipt.
11. **Unresolved questions:** Which signal owns safe eviction before heap pressure? Does replay cost change the safe cache floor? Is burst recovery tested against all-worker loss, not only single-worker failure?
12. **Proposed offer:** embedded / recurring workflow role
13. **One small CTA:** Ask whether the partnerships team will route a one-page joint-delivery outline to the SDK/reliability owner.
14. **Verified professional contact route:** Official “Become a Partner” form — https://temporal.io/partners
15. **Personalized subject line:** Joint delivery rule for Temporal worker-cache crash-loop recovery
16. **Complete email draft:**

> Hello Temporal Partnerships team,
>
> Temporal's public TypeScript SDK issue #2227 describes production workers with 6 GB heaps crashing as the workflow cache grew; during bursts, all workers could enter crash-loop backoff until someone manually scaled the fleet. One rule I would show a client before implementation is: admit workflows to cache against an explicit memory budget, evict or backpressure before OOM, and bind that choice to a repeatable load-test receipt.
>
> The record leaves three delivery questions: which signal owns safe eviction, how replay cost changes the cache floor, and whether recovery is tested against simultaneous worker loss.
>
> I work as an implementation and verification operator for bounded restartability problems. Would you route a one-page joint-delivery outline to the SDK or reliability owner?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The incident belongs to a user deployment, not a Temporal-authored postmortem. The partnership program may require certifications or a larger firm; do not imply existing Temporal expertise or partnership status.
18. **Recommended send priority:** 2

## Priority 3 — n8n

1. **Candidate / organization:** n8n
2. **Group:** B
3. **Role and decision authority:** Resellers & Implementation Partners team, an official route for implementation partnerships.
4. **Official public source:** [n8n contact and partner routes](https://n8n.io/contact/).
5. **Concrete observed incident or operational gap:** Four production workflows sharing Google service-account credentials remained in `running` with empty `runData`; credential rotation, workflow rebuilds, auth-path changes, and deactivate/reactivate did not restore execution, blocking a production render pipeline.
6. **Evidence class:** owner-reported
7. **Exact evidence URL:** https://github.com/n8n-io/n8n/issues/31329
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 2 + ability to pay 2 + recurrence 2 = **10/10**
9. **Why this may recur or expand:** Credential loading, webhook acknowledgement, queue admission, and worker pickup are common to integrations and AI automations across hosted and self-hosted deployments.
10. **First operational rule shown in advance:** A workflow-start acknowledgement requires either worker acceptance or a durable, visible failure; credential tests and runtime must share the same deserialization path.
11. **Unresolved questions:** Where did ownership disappear between the execution row and worker pickup? Can support distinguish a credential-load wedge without backend access? What is the safe re-entry path after credential rotation?
12. **Proposed offer:** embedded / recurring workflow role
13. **One small CTA:** Ask the partner team to identify the owner for a bounded diagnostic-receipt pilot.
14. **Verified professional contact route:** Official implementation-partners route — https://n8n.io/contact/
15. **Personalized subject line:** An implementation-partner diagnostic rule for n8n's credential-load wedge
16. **Complete email draft:**

> Hello n8n Partnerships team,
>
> Public issue #31329 records four production workflows stuck in `running` with empty `runData`; key rotation, three rebuilds, an alternate JWT path, and reactivation did not restore worker pickup. One rule I would place before this boundary is: a start acknowledgement must bind either worker acceptance or a durable visible failure, and credential tests must use the same deserialization path as runtime.
>
> The public evidence leaves three questions: where ownership disappears after the execution row is created, how support can identify this wedge without backend access, and what exact checkpoint permits safe re-entry after rotation.
>
> I can support implementation partners with bounded diagnostics and restart receipts for cases like this. Who owns a small diagnostic-receipt pilot on the partner side?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The affected instance and identifiers are in a user report; do not repeat unnecessary account details. Partner intake may be capped or waitlisted. Do not use community or issue comments as the sales route.
18. **Recommended send priority:** 3

## Priority 4 — Flowise

1. **Candidate / organization:** FlowiseAI
2. **Group:** B
3. **Role and decision authority:** Commercial/support routing team via the official company support address; technical budget owner is not named.
4. **Official public source:** [Flowise product and enterprise plans](https://flowiseai.com/) and [company terms naming the support route](https://flowiseai.com/terms).
5. **Concrete observed incident or operational gap:** Chained Agentflows duplicated predictions. A five-iteration UI run produced seven calls, hit rate limits and budget, and could only be stopped by stopping Redis and deleting Redis data; deleting executions in the UI did not stop persistence.
6. **Evidence class:** owner-reported
7. **Exact evidence URL:** https://github.com/FlowiseAI/Flowise/issues/4854
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** The same duplicate-execution boundary appeared in Execute Flow, Agent as Tool, iterations, and loops, making it a platform-wide composition concern.
10. **First operational rule shown in advance:** Give every logical prediction a stable execution key; UI, loop, and retry paths must reuse its receipt rather than launch another provider call.
11. **Unresolved questions:** Was the 3.0.5 fix validated across Redis restarts? Does the idempotency boundary cover nested flows and provider retries? Can operators terminate persisted duplicates without database cleanup?
12. **Proposed offer:** embedded / recurring workflow role
13. **One small CTA:** Ask for the owner of composed-flow execution to review a one-page verification matrix.
14. **Verified professional contact route:** Official support email published by FlowiseAI — `support@flowiseai.com`
15. **Personalized subject line:** Verification matrix for Flowise nested-flow duplicate execution
16. **Complete email draft:**

> Hello FlowiseAI team,
>
> In public issue #4854, a five-iteration Agentflow produced seven provider calls, hit rate limits and budget, and persisted until Redis was stopped and cleared. The same report covered Execute Flow, Agent as Tool, iterations, and loops. One rule I would put in front of composed execution is: every logical prediction gets a stable execution key, and UI, loop, and retry paths reuse its receipt instead of launching another call.
>
> Three questions remain public: whether the 3.0.5 repair survived Redis restart testing, whether nested provider retries share the same boundary, and whether an operator can terminate duplicates without data-store cleanup.
>
> I can prepare a bounded cross-surface verification matrix. Could the owner of composed-flow execution review that one page?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** A contributor stated the defect was fixed in 3.0.5, so position this as regression verification, not an unfixed-bug claim. Support may decline vendor proposals.
18. **Recommended send priority:** 4

## Priority 5 — LangChain / LangGraph

1. **Candidate / organization:** LangChain / LangGraph
2. **Group:** B
3. **Role and decision authority:** LangSmith commercial routing team; official form has business-routing authority but no verified engineering buyer.
4. **Official public source:** [LangChain contact sales](https://www.langchain.com/contact-sales) and [LangSmith pricing](https://www.langchain.com/pricing).
5. **Concrete observed incident or operational gap:** Long tool calls on LangGraph Cloud were silently re-dispatched from a checkpoint while the original was still running, producing two to three successful executions with redundant work and cost across versions 1.1.3–1.1.6.
6. **Evidence class:** owner-reported
7. **Exact evidence URL:** https://github.com/langchain-ai/langgraph/issues/7417
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Long-running tools, worker sweeps, checkpoint replay, and non-idempotent side effects are central to production agent deployments and support engagements.
10. **First operational rule shown in advance:** Before a side-effecting tool runs, claim a durable execution key; checkpoint replay must return the original receipt instead of executing the side effect again.
11. **Unresolved questions:** What server signal marks a long run stale? Does the heartbeat cover nested sub-agent awaits? Where can customers bind idempotency across worker re-dispatch?
12. **Proposed offer:** embedded / recurring workflow role
13. **One small CTA:** Ask for routing to the owner of Cloud run re-dispatch for a 20-minute boundary review.
14. **Verified professional contact route:** Official LangChain sales form — https://www.langchain.com/contact-sales
15. **Personalized subject line:** A durable execution-key boundary for LangGraph Cloud re-dispatch
16. **Complete email draft:**

> Hello LangChain team,
>
> LangGraph issue #7417 reports 3–10 minute tool calls being silently re-dispatched while the original kept running, with both copies succeeding and creating 2–3× work and cost across versions 1.1.3–1.1.6. One rule I would show before any repair is: a side-effecting tool claims a durable execution key before it runs, and checkpoint replay returns the prior receipt rather than running the side effect again.
>
> The public record leaves three questions: what server signal marks the run stale, whether nested sub-agent awaits keep liveness, and where customers can bind idempotency across workers.
>
> I can audit this as a bounded run-ownership slice and leave a replay test plus receipt. Could you route me to the Cloud re-dispatch owner for a 20-minute boundary review?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The sales form is buyer-oriented and may reject vendor proposals. The incident is customer-reported; do not present its source analysis as LangChain-confirmed root cause.
18. **Recommended send priority:** 5

## Priority 6 — CrewAI

1. **Candidate / organization:** CrewAI
2. **Group:** A
3. **Role and decision authority:** Enterprise/AMP commercial routing team; it can route the proposal, but the reliability engineering buyer is unnamed.
4. **Official public source:** [CrewAI](https://crewai.com/) and [Meet with CrewAI](https://crewai.com/meet-with-us).
5. **Concrete observed incident or operational gap:** In a production report, an async task swallowed an LLM failure, left the flow in `running`, and blocked downstream agents indefinitely; the operator reports losing a full day to diagnosis and carrying a wrapper workaround.
6. **Evidence class:** owner-reported
7. **Exact evidence URL:** https://github.com/crewAIInc/crewAI/issues/6380
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Provider timeouts, 429/500 responses, async fan-out, downstream dependency waits, and state transitions repeat across every multi-agent customer workflow.
10. **First operational rule shown in advance:** Every async child ends with a propagated terminal payload—success, retryable failure, or stop—and downstream waits may consume only that explicit state.
11. **Unresolved questions:** Which executor owns propagation from the failed coroutine? Are retries bounded by both count and wall time? Can existing `running` flows be re-entered without manual process restart?
12. **Proposed offer:** bounded implementation
13. **One small CTA:** Ask for a 20-minute call with the async execution owner.
14. **Verified professional contact route:** Official enterprise meeting form — https://crewai.com/meet-with-us
15. **Personalized subject line:** A bounded terminal-payload slice for CrewAI async flow freezes
16. **Complete email draft:**

> Hello CrewAI team,
>
> Public issue #6380 describes a production async task whose LLM failure was swallowed: the flow stayed `running`, dependent agents waited indefinitely, and the operator spent a full day diagnosing it before carrying a wrapper workaround. One rule I would put in front of that executor is: every async child must end with a propagated terminal payload—success, retryable failure, or explicit stop—and downstream waits may consume only that state.
>
> The record leaves three questions: which layer owns propagation from the failed coroutine, whether retry limits bind both count and wall time, and how an already-stuck flow re-enters safely.
>
> I can implement a bounded failure-injection and terminal-receipt slice around that path. Would the async execution owner be open to a 20-minute scoping call?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The report includes a third-party workaround and may not reflect current AMP behavior. The official form is designed for prospective customers, so routing fit is uncertain.
18. **Recommended send priority:** 6

## Priority 7 — Dify

1. **Candidate / organization:** Dify / LangGenius
2. **Group:** B
3. **Role and decision authority:** Enterprise business team at the company's officially published address; it has commercial authority and can route an implementation-partner proposal.
4. **Official public source:** [Dify Enterprise](https://dify.ai/pricing/dify-enterprise).
5. **Concrete observed incident or operational gap:** A primary-key conflict left a workflow node permanently in `Running`; restarting API and worker services did not move it to success or failure.
6. **Evidence class:** owner-reported
7. **Exact evidence URL:** https://github.com/langgenius/dify/issues/23174
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 2 + ability to pay 2 + recurrence 2 = **10/10**
9. **Why this may recur or expand:** Dify's enterprise offer spans many workflows, workers, databases, plugins, and partner-delivered deployments; node-state finalization is a repeated operating boundary.
10. **First operational rule shown in advance:** Commit the execution record and node-state transition atomically; a write conflict must become a visible retryable or terminal state, never indefinite `Running`.
11. **Unresolved questions:** Was the failure an ID-generation, transaction, or retry collision? What reconciler detects stale `Running` rows? Can a node resume without replaying completed side effects?
12. **Proposed offer:** embedded / recurring workflow role
13. **One small CTA:** Ask the business team to route a one-page stale-node reconciliation outline to the workflow-runtime owner.
14. **Verified professional contact route:** Official enterprise email — `business@dify.ai`
15. **Personalized subject line:** Stale-node reconciliation rule for Dify workflow execution
16. **Complete email draft:**

> Hello Dify business team,
>
> Dify issue #23174 records a primary-key conflict that left a workflow node permanently in `Running`; restarting both API and worker services did not move it to success or failure. One rule I would put in front of this path is: the execution record and node-state transition commit atomically, and a write conflict becomes a visible retryable or terminal state—never indefinite `Running`.
>
> The public record leaves three questions: whether the collision began in ID generation, transaction handling, or retry; what reconciler detects stale rows; and whether re-entry can avoid replaying completed side effects.
>
> I support bounded implementation and verification for restartable AI workflows. Would you route a one-page stale-node reconciliation outline to the workflow-runtime owner?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The issue is closed and current enterprise code may differ from v1.4.0. The business address is mainly for buyers; do not frame the public issue as proof of a current enterprise defect.
18. **Recommended send priority:** 7

## Priority 8 — deepset / Haystack

1. **Candidate / organization:** deepset / Haystack
2. **Group:** B
3. **Role and decision authority:** deepset commercial team at its published sales address; routing authority is clear, technical buying authority is not named.
4. **Official public source:** [deepset enterprise datasheet](https://www.deepset.ai/downloads/deepset-Cloud-datasheet.pdf).
5. **Concrete observed incident or operational gap:** A pipeline snapshot taken on the second visit to a loop component fails immediately on resume with `PipelineComponentsBlockedError`; first-visit resume works.
6. **Evidence class:** observed
7. **Exact evidence URL:** https://github.com/deepset-ai/haystack/issues/12145
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Breakpoints, loops, retries, human review, pipeline snapshots, and deterministic replay are shared across production agent pipelines and enterprise support.
10. **First operational rule shown in advance:** A snapshot must bind component visit count and scheduler readiness; resume validates the pending component's eligibility before declaring the pipeline blocked.
11. **Unresolved questions:** Which scheduler datum is lost after visit zero? Does resume preserve queued loop inputs? Are side effects before the breakpoint protected from replay?
12. **Proposed offer:** embedded / recurring workflow role
13. **One small CTA:** Ask the sales team to route a one-page resume-state test matrix to the Haystack pipeline owner.
14. **Verified professional contact route:** Official sales email — `sales@deepset.ai`
15. **Personalized subject line:** Resume-state test matrix for Haystack loop snapshots
16. **Complete email draft:**

> Hello deepset team,
>
> Haystack issue #12145 shows a pipeline snapshot resuming correctly on visit zero but failing immediately with `PipelineComponentsBlockedError` when the breakpoint is taken on the second loop visit. One rule I would put in advance is: a snapshot binds both component visit count and scheduler readiness, and resume validates the pending component's eligibility before it can declare the pipeline blocked.
>
> The public reproduction leaves three questions: which scheduler datum is lost after visit zero, whether queued loop inputs survive, and whether pre-breakpoint side effects are protected from replay.
>
> I can maintain a bounded resume-state verification lane across loop, retry, and HITL cases. Would you route a one-page test matrix to the Haystack pipeline owner?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The issue is recent and may already have an active maintainer fix. Sales intake may not accept vendor work; do not use the GitHub issue itself as a solicitation channel.
18. **Recommended send priority:** 8

## Priority 9 — Agno

1. **Candidate / organization:** Agno
2. **Group:** A
3. **Role and decision authority:** AgentOS business/product routing via the official “Contact Us” form embedded on the product page; individual buyer is unnamed.
4. **Official public source:** [AgentOS](https://www.agno.com/agentos).
5. **Concrete observed incident or operational gap:** A HITL pause exposed through A2A was mapped to `working`, never emitted `input-required`, and had no A2A resume path; a compliant client waited until timeout.
6. **Evidence class:** observed
7. **Exact evidence URL:** https://github.com/agno-agi/agno/issues/9068
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** AgentOS exposes agents across A2A, Slack, MCP, APIs, and live UI; every interface must preserve the same pause/resume identity and approval payload.
10. **First operational rule shown in advance:** Map `paused` to `input-required`, expose the requirement, and bind every approval response to the same durable `run_id`.
11. **Unresolved questions:** Is resume parity tested across every AgentOS interface? What payload identifies multiple pending approvals? Can a disconnected client rehydrate the pending requirement?
12. **Proposed offer:** bounded implementation
13. **One small CTA:** Ask for a 20-minute interface-parity review with the AgentOS lifecycle owner.
14. **Verified professional contact route:** Official AgentOS “Contact Us” form — https://www.agno.com/agentos
15. **Personalized subject line:** A2A pause/resume parity check for AgentOS
16. **Complete email draft:**

> Hello Agno team,
>
> Agno issue #9068 demonstrates an A2A HITL run that paused server-side but remained `working` to the client, never emitted `input-required`, and offered no route to resume; the client simply timed out. One rule I would show before implementation is: map `paused` to `input-required`, expose the requirement, and bind the approval response to the same durable `run_id`.
>
> The public evidence leaves three questions: whether resume parity is tested across every AgentOS interface, how multiple pending approvals are identified, and how a disconnected client rehydrates the requirement.
>
> I can implement a bounded interface-parity test and receipt around that lifecycle. Would the AgentOS lifecycle owner be open to a 20-minute review?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The issue closed as completed on 2026-07-26, so the relevant offer is regression/parity verification, not initial bug repair. The contact control is a page form; pre-send DOM provenance remains mandatory.
18. **Recommended send priority:** 9

## Priority 10 — Trigger.dev

1. **Candidate / organization:** Trigger.dev
2. **Group:** B
3. **Role and decision authority:** General inquiry/product routing team via the official contact form; technical buying authority is not named.
4. **Official public source:** [Trigger.dev contact](https://trigger.dev/contact) and [Trigger.dev repository](https://github.com/triggerdotdev/trigger.dev).
5. **Concrete observed incident or operational gap:** With durable chat sessions and `watch: true`, an out-of-band turn duplicated the prior assistant message, merged new parts into the wrong message, left `useChat` permanently non-ready, and reconnected every 60 seconds while idle.
6. **Evidence class:** observed
7. **Exact evidence URL:** https://github.com/triggerdotdev/trigger.dev/issues/4326
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Durable sessions, background wakeups, streaming cursors, UI reconstruction, and disconnect/reconnect semantics repeat in every chat-agent implementation.
10. **First operational rule shown in advance:** Each logical turn owns a fresh message identity and request lifecycle; the UI reaches `ready` only after a bound terminal event for that turn.
11. **Unresolved questions:** Where is turn identity durably separated from transport connection identity? Can reconnect resume without mutating the prior message object? Is idle termination tested with out-of-band input?
12. **Proposed offer:** embedded / recurring workflow role
13. **One small CTA:** Ask for routing to the durable-chat owner for a one-page turn-boundary test.
14. **Verified professional contact route:** Official business/general inquiry form — https://trigger.dev/contact
15. **Personalized subject line:** Turn-boundary verification for Trigger.dev durable chat wakeups
16. **Complete email draft:**

> Hello Trigger.dev team,
>
> Public issue #4326 shows a durable chat wakeup with `watch: true` duplicating the previous assistant message, merging the new turn into the wrong message, leaving `useChat` non-ready, and reconnecting every 60 seconds while idle. One rule I would put in front of this transport is: each logical turn owns a fresh message identity and request lifecycle, and the UI reaches `ready` only after that turn's terminal event.
>
> Three questions remain: where turn identity separates from connection identity, whether reconnect can resume without mutating the prior message object, and whether idle termination is tested with out-of-band input.
>
> I can keep a small recurring verification lane for these durable-session boundaries. Would you route a one-page turn-boundary test to the durable-chat owner?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The form may include reCAPTCHA and must not be automated past a human-verification gate. The issue is open and detailed, but its proposed mechanism is reporter analysis, not an owner-confirmed root cause.
18. **Recommended send priority:** 10

## Priority 11 — OpenHands

1. **Candidate / organization:** OpenHands
2. **Group:** A
3. **Role and decision authority:** Enterprise/product team reachable through the official company contact address; individual engineering buyer is not named.
4. **Official public source:** [OpenHands Enterprise](https://docs.openhands.dev/enterprise) and [official contact address](https://docs.openhands.dev/overview/contributing).
5. **Concrete observed incident or operational gap:** During an automated PR follow-up, the agent committed the requested README change, evaluated completion against only the tip-to-tip diff rather than the cumulative PR, declared the request unresolved, skipped push, and discarded the valid commit.
6. **Evidence class:** observed
7. **Exact evidence URL:** https://github.com/OpenHands/OpenHands/issues/12950
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Enterprise automations run issue-to-PR and review-follow-up workflows across repositories; completion identity, merge-base selection, commit retention, and restart receipts repeat in every run.
10. **First operational rule shown in advance:** Evaluate follow-up completion against the merge base and cumulative PR scope; never discard a valid incremental commit without a preservation receipt.
11. **Unresolved questions:** Which diff identity is authoritative for follow-up tasks today? Are valid commits preserved when semantic completion fails? Can an operator resume from the discarded boundary without reconstruction?
12. **Proposed offer:** bounded Audit
13. **One small CTA:** Ask for a 20-minute review with the owner of PR automation completion.
14. **Verified professional contact route:** Official company email — `contact@openhands.dev`
15. **Personalized subject line:** A bounded completion-identity audit for OpenHands PR automations
16. **Complete email draft:**

> Hello OpenHands team,
>
> OpenHands issue #12950 documents a review follow-up where the agent correctly committed the README change, then judged the task against only the new tip diff, skipped push, and discarded the valid commit because the earlier implementation was outside that comparison. One rule I would put in front of this workflow is: evaluate completion from the merge base and cumulative PR scope, and never discard a valid incremental commit without a preservation receipt.
>
> The public record leaves three questions: which diff identity is authoritative now, whether valid commits survive a failed completion check, and how an operator resumes without reconstructing the follow-up.
>
> I can run a bounded audit of completion identity and commit retention across one PR-automation path. Would the PR automation owner be open to a 20-minute review?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The issue closed as not planned, and current Enterprise Automations may use a different path. Do not imply access to the commercially licensed enterprise directory.
18. **Recommended send priority:** 11

## Priority 12 — Composio

1. **Candidate / organization:** Composio
2. **Group:** A
3. **Role and decision authority:** Business routing team via the official general contact form; named reliability buyer is not public.
4. **Official public source:** [Composio contact](https://composio.dev/contact) and [enterprise pricing](https://composio.dev/pricing).
5. **Concrete observed incident or operational gap:** Calling `stop()` from the documented trigger callback path deadlocks the process; a subscribe timeout can also leak a forever-reconnecting websocket thread, with one new abandoned thread per retry.
6. **Evidence class:** observed
7. **Exact evidence URL:** https://github.com/ComposioHQ/composio/issues/3858
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Trigger subscriptions, callback shutdown, timeout cleanup, retries, and abandoned consumers sit under many agent-tool integrations and customer workflows.
10. **First operational rule shown in advance:** A subscription may not join its calling thread; every timeout must close all connection and executor resources it created before raising.
11. **Unresolved questions:** Which object owns connection teardown on partial subscribe? Is callback-initiated stop covered in integration tests? How are abandoned subscriptions prevented from later consuming live events?
12. **Proposed offer:** bounded implementation
13. **One small CTA:** Ask for a 20-minute scoping call with the Python SDK trigger owner.
14. **Verified professional contact route:** Official general business form — https://composio.dev/contact
15. **Personalized subject line:** A bounded trigger-lifecycle repair for Composio's callback deadlock
16. **Complete email draft:**

> Hello Composio team,
>
> Public issue #3858 reproduces two trigger-lifecycle failures: `stop()` from the documented callback path deadlocks the process, while subscribe timeouts can leave one forever-reconnecting websocket thread per retry. One rule I would put in front of the SDK is: a subscription may not join its calling thread, and every timeout closes every connection and executor resource it created before raising.
>
> The public evidence leaves three questions: which object owns partial-subscribe teardown, whether callback stop is integration-tested, and how abandoned connections are prevented from later consuming events.
>
> I can implement a bounded lifecycle repair with deterministic thread-leak and shutdown tests. Would the Python SDK trigger owner be open to a 20-minute scoping call?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The issue may already have an assigned fix. The general contact form must be checked for required phone or Canon-external fields before any approved send.
18. **Recommended send priority:** 12

## Priority 13 — Mastra

1. **Candidate / organization:** Mastra
2. **Group:** A
3. **Role and decision authority:** Product/commercial team through the official organizational contact form; it can route the case but the workflow-runtime buyer is unnamed.
4. **Official public source:** [Mastra contact](https://mastra.ai/contact).
5. **Concrete observed incident or operational gap:** An agent invoking a workflow with HITL suspend/resume had no way to provide the input from Mastra Studio; even adding values in the workflow thread did not update the parent conversation.
6. **Evidence class:** owner-reported
7. **Exact evidence URL:** https://github.com/mastra-ai/mastra/issues/11015
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Parent-agent/child-workflow state, human input, thread projection, durable resume, and Studio rendering recur across organizational agent deployments.
10. **First operational rule shown in advance:** A suspended child keeps a typed pending-input record; the parent may not report completion until the child resumes or reaches an explicit terminal stop.
11. **Unresolved questions:** Which thread owns pending HITL input? Is child resume projected atomically into the parent conversation? Can Studio rehydrate pending state after disconnect?
12. **Proposed offer:** bounded implementation
13. **One small CTA:** Ask for a 20-minute scoping call with the suspend/resume owner.
14. **Verified professional contact route:** Official organizational contact form — https://mastra.ai/contact
15. **Personalized subject line:** Parent/child resume boundary for Mastra agent-invoked workflows
16. **Complete email draft:**

> Hello Mastra team,
>
> Mastra issue #11015 records an agent-invoked workflow that suspended for HITL input but could not receive that input from Studio; even entering values in the workflow thread did not update the parent conversation. One rule I would place before this boundary is: a suspended child keeps a typed pending-input record, and the parent may not report completion until the child resumes or reaches an explicit terminal stop.
>
> The public record leaves three questions: which thread owns the pending input, whether child resume is projected atomically to the parent, and how Studio rehydrates the pending state after disconnect.
>
> I can implement a bounded parent/child resume slice with a restart receipt. Would the suspend/resume owner be open to a 20-minute scoping call?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The report used beta packages and is closed; current behavior must be rechecked before send. Mastra offers its own concierge/forward-deployed services, so external implementation fit may be low.
18. **Recommended send priority:** 13

## Priority 14 — Prefect

1. **Candidate / organization:** Prefect
2. **Group:** B
3. **Role and decision authority:** Sales Engineering/commercial routing team through the official business form; technical buyer is unnamed.
4. **Official public source:** [Prefect support](https://www.prefect.io/support), [contact sales](https://www.prefect.io/contact-sales), and [pricing](https://www.prefect.io/pricing).
5. **Concrete observed incident or operational gap:** A flow watcher swallowed websocket errors, emitted end-of-stream, and returned while the flow was still `Running`. The report identified recurrence through a new code path after a prior fix.
6. **Evidence class:** observed
7. **Exact evidence URL:** https://github.com/PrefectHQ/prefect/issues/22549
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Flow-state watching, websocket reconnect, CLI exit identity, automations, MCP/Horizon, and customer support all depend on a reliable terminal-state contract.
10. **First operational rule shown in advance:** A watcher returns only after reading a terminal flow state; socket loss is an explicit reconnect or failure, never silent end-of-stream.
11. **Unresolved questions:** Which surface owns reconnect after subscriber loss? Can a CLI distinguish transport end from workflow end? Is recurrence tested across event and log sockets independently?
12. **Proposed offer:** embedded / recurring workflow role
13. **One small CTA:** Ask for the workflow-observability owner to review a one-page terminal-state matrix.
14. **Verified professional contact route:** Official Sales Engineering form — https://www.prefect.io/contact-sales
15. **Personalized subject line:** Terminal-state matrix for Prefect watcher reconnects
16. **Complete email draft:**

> Hello Prefect team,
>
> Prefect issue #22549 shows a watcher swallowing a websocket exception, ending iteration, and returning while the flow still reported `Running`; the report also identifies the pattern as a recurrence through a newer subscriber path. One rule I would show in advance is: a watcher returns only after a terminal flow state, while socket loss becomes explicit reconnect or failure—never silent end-of-stream.
>
> The public record leaves three questions: which layer owns reconnect, how CLI callers distinguish transport end from workflow end, and whether event and log sockets are failure-tested independently.
>
> I can maintain a small terminal-state verification lane across subscriber changes. Would the workflow-observability owner review a one-page state matrix?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The issue closed as completed within days, so this is a recurrence-test offer only. The sales form is buyer-oriented and may not accept implementation proposals.
18. **Recommended send priority:** 14

## Priority 15 — Pydantic

1. **Candidate / organization:** Pydantic
2. **Group:** A
3. **Role and decision authority:** Commercial team at the official sales address; routing authority is verified, individual framework buyer is not.
4. **Official public source:** [Pydantic contact](https://pydantic.dev/contact) and [Logfire pricing](https://pydantic.dev/pricing).
5. **Concrete observed incident or operational gap:** A Pydantic AI agent entered an unbounded model-call loop when a required structured field could not be populated; configured retry limits did not stop it.
6. **Evidence class:** owner-reported
7. **Exact evidence URL:** https://github.com/pydantic/pydantic-ai/issues/267
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Structured output validation, `ModelRetry`, provider calls, durable execution, and cost control are shared across Pydantic AI and observed through Logfire.
10. **First operational rule shown in advance:** Every agent run has a total turn and external-call budget; repeating the same invalid state exhausts the budget before another provider call.
11. **Unresolved questions:** Which retry counter owns structured-output repair? Is identical-state detection available across models? Does a terminal budget error preserve the last valid partial output?
12. **Proposed offer:** bounded Audit
13. **One small CTA:** Ask for a 20-minute review with the Pydantic AI retry owner.
14. **Verified professional contact route:** Official sales email — `sales@pydantic.dev`
15. **Personalized subject line:** A bounded retry-budget audit for Pydantic AI structured-output loops
16. **Complete email draft:**

> Hello Pydantic team,
>
> Pydantic AI issue #267 records an agent repeatedly calling the model when a required structured field could not be populated; configured retry limits did not stop the loop. One rule I would place before this path is: every run has a total turn and external-call budget, and the same invalid state exhausts that budget before another provider call.
>
> Three questions remain in the public record: which counter owns structured-output repair, whether identical-state detection works across models, and whether terminal budget exhaustion preserves the last valid partial output.
>
> I can run a bounded audit of retry ownership and termination receipts across one structured-output path. Would the Pydantic AI retry owner be open to a 20-minute review?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The issue is old and closed; the current durable-execution system is materially newer. Do not imply the reported behavior persists without a fresh public reproduction.
18. **Recommended send priority:** 15

## Priority 16 — LiteLLM

1. **Candidate / organization:** LiteLLM
2. **Group:** A
3. **Role and decision authority:** Enterprise commercial routing through the official product page; named technical buyer is not public.
4. **Official public source:** [LiteLLM Enterprise](https://www.litellm.ai/enterprise) and [pricing](https://www.litellm.ai/pricing).
5. **Concrete observed incident or operational gap:** Anthropic-format tool history was stripped or rejected by the proxy, causing the model to rerun the same tools indefinitely and eventually error.
6. **Evidence class:** observed
7. **Exact evidence URL:** https://github.com/BerriAI/litellm/issues/25669
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Tool-call normalization crosses many providers, clients, gateways, retries, and multi-turn agents; a pairing defect can duplicate any downstream side effect.
10. **First operational rule shown in advance:** Provider-format transforms must preserve a bijection between tool calls and results; validate pair identity before and after normalization.
11. **Unresolved questions:** Which schema is canonical inside the proxy? Are sanitizer losses observable before provider dispatch? Does retry reuse the transformed history or recompute it differently?
12. **Proposed offer:** bounded Audit
13. **One small CTA:** Ask for a 20-minute review with the proxy normalization owner.
14. **Verified professional contact route:** Official enterprise “Talk to sales” form — https://www.litellm.ai/enterprise
15. **Personalized subject line:** Tool-history identity audit for LiteLLM's Anthropic normalization path
16. **Complete email draft:**

> Hello LiteLLM team,
>
> LiteLLM issue #25669 reproduces Anthropic-format `tool_use` and `tool_result` blocks being stripped or rejected, after which the model reruns the same tools indefinitely and eventually errors. One rule I would put in front of normalization is: every transform preserves a one-to-one identity between tool calls and results, with pair validation before and after conversion.
>
> The public record leaves three questions: which schema is canonical internally, whether sanitizer losses are observable before dispatch, and whether retry reuses or recomputes the transformed history.
>
> I can run a bounded identity audit across one client/provider matrix and leave executable receipts. Would the proxy normalization owner be open to a 20-minute review?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The issue remains open but may affect only clients sending Anthropic content blocks to an OpenAI-compatible endpoint. The enterprise page is buyer-oriented.
18. **Recommended send priority:** 16

## Priority 17 — LlamaIndex

1. **Candidate / organization:** LlamaIndex
2. **Group:** A
3. **Role and decision authority:** Commercial/product routing through the official contact page; individual OSS runtime buyer is unnamed.
4. **Official public source:** [LlamaIndex contact](https://www.llamaindex.ai/contact) and [LlamaIndex platform](https://www.llamaindex.ai/).
5. **Concrete observed incident or operational gap:** Three parallel HITL branches derived the same waiter ID; only one input request survived, one branch resumed, and the other two hung until timeout.
6. **Evidence class:** observed
7. **Exact evidence URL:** https://github.com/run-llama/llama_index/issues/22070
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Parallel tool fan-out, HITL, waiter identity, fan-in, and timeout behavior are reusable primitives across LlamaIndex workflows and enterprise agents.
10. **First operational rule shown in advance:** Every parallel HITL waiter is keyed by its tool-call identity; fan-in completes only after every expected waiter reaches a terminal state.
11. **Unresolved questions:** Is uniqueness generated by the framework or required from each tool? What persists if the process restarts while multiple waiters are pending? Can clients enumerate all unresolved requirements?
12. **Proposed offer:** bounded Audit
13. **One small CTA:** Ask for a 20-minute review with the workflow runtime owner.
14. **Verified professional contact route:** Official contact-sales form — https://www.llamaindex.ai/contact
15. **Personalized subject line:** Parallel HITL waiter-identity audit for LlamaIndex workflows
16. **Complete email draft:**

> Hello LlamaIndex team,
>
> LlamaIndex issue #22070 reproduces three parallel HITL branches deriving one waiter ID: only one input request survives, one branch resumes, and the other two hang until timeout. One rule I would show before implementation is: every parallel waiter is keyed by its tool-call identity, and fan-in completes only after every expected waiter reaches a terminal state.
>
> The public evidence leaves three questions: whether uniqueness is framework-owned or tool-owned, what persists across a restart with multiple waiters pending, and whether clients can enumerate every unresolved requirement.
>
> I can run a bounded waiter-identity and restart audit across this fan-out path. Would the workflow runtime owner be open to a 20-minute review?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The issue was fixed quickly and closed, so position this as a restart/coverage audit. The contact page focuses on LlamaParse buyers rather than OSS framework services.
18. **Recommended send priority:** 17

## Priority 18 — Mem0

1. **Candidate / organization:** Mem0
2. **Group:** A
3. **Role and decision authority:** Enterprise routing team through the official form; the runtime SDK buyer is unnamed.
4. **Official public source:** [Mem0 Enterprise](https://app.mem0.ai/enterprise) and [Mem0](https://mem0.ai/).
5. **Concrete observed incident or operational gap:** `AsyncMemoryClient` initialization performed a synchronous validation request with no timeout and bypassed the injected client, so initialization could hang indefinitely or validate against the wrong host.
6. **Evidence class:** observed
7. **Exact evidence URL:** https://github.com/mem0ai/mem0/issues/6554
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Client construction, custom gateways, private endpoints, auth validation, async event loops, and network failure are common to every persistent-memory integration.
10. **First operational rule shown in advance:** Initialization uses the injected transport and a bounded deadline; timeout returns no half-initialized client and owns cleanup of all started resources.
11. **Unresolved questions:** Does every SDK share one validation contract? Can validation be deferred for offline construction? What diagnostic distinguishes bad credentials from unreachable custom hosts?
12. **Proposed offer:** bounded implementation
13. **One small CTA:** Ask for a 20-minute scoping call with the Python SDK owner.
14. **Verified professional contact route:** Official enterprise form — https://app.mem0.ai/enterprise
15. **Personalized subject line:** A bounded async-client initialization repair for Mem0
16. **Complete email draft:**

> Hello Mem0 team,
>
> Mem0 issue #6554 shows `AsyncMemoryClient` initialization making a synchronous validation request with no timeout and bypassing the injected client, so construction can hang indefinitely or validate against the wrong host. One rule I would put in front of client setup is: initialization uses the injected transport under a bounded deadline, and timeout returns no half-initialized client while cleaning every resource it started.
>
> The public evidence leaves three questions: whether all SDKs share one validation contract, whether validation can be deferred for offline construction, and how diagnostics separate bad credentials from an unreachable custom host.
>
> I can implement this as a bounded client-lifecycle slice with timeout and proxy tests. Would the Python SDK owner be open to a 20-minute scoping call?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The evidence is a deterministic source-path reproduction, not a published customer incident. The enterprise form shows phone as optional now; recheck the DOM and leave it blank under the Sender Canon.
18. **Recommended send priority:** 18

## Priority 19 — Dagster

1. **Candidate / organization:** Dagster Labs
2. **Group:** B
3. **Role and decision authority:** Commercial routing via the official sales contact referenced by Dagster support; technical buyer is unnamed.
4. **Official public source:** [Dagster support](https://dagster.io/support).
5. **Concrete observed incident or operational gap:** A run step occupied a single-slot concurrency pool and then blocked on that same pool, holding the whole single-process run; affected slots could remain in that condition.
6. **Evidence class:** owner-reported
7. **Exact evidence URL:** https://github.com/dagster-io/dagster/issues/31243
8. **Qualification score:** workflow 2 + recovery burden 2 + authority 1 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Concurrency pools, retries, dynamic assets, queues, and run leases are recurring platform primitives in data and AI automation.
10. **First operational rule shown in advance:** A concurrency lease is checked against the current run identity; a self-held lease renews or re-enters and can never block its own run.
11. **Unresolved questions:** How can a slot be reclaimed after owner ambiguity? Is lease identity persisted through daemon restart? Are dynamic asset tags normalized before acquisition?
12. **Proposed offer:** embedded / recurring workflow role
13. **One small CTA:** Ask for the concurrency owner to review a one-page lease-invariant test.
14. **Verified professional contact route:** Official sales contact linked from https://dagster.io/support
15. **Personalized subject line:** Lease-invariant test for Dagster self-blocking concurrency slots
16. **Complete email draft:**

> Hello Dagster Labs team,
>
> Dagster issue #31243 records a run step occupying a single-slot concurrency pool and then blocking on that same pool, holding the whole single-process run. One rule I would put in advance is: a concurrency lease is checked against current run identity, and a self-held lease renews or re-enters—it can never block its own run.
>
> The public record leaves three questions: how an ambiguous slot is reclaimed, whether lease identity survives daemon restart, and whether dynamic asset tags are normalized before acquisition.
>
> I can maintain a small recurring verification lane for lease, retry, and restart invariants. Would the concurrency owner review a one-page executable test?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** The reproduction uses a workaround that mutates asset tags, so the root may sit partly outside the supported API. The sales form may not accept vendor proposals.
18. **Recommended send priority:** 19

## Priority 20 — Inngest

1. **Candidate / organization:** Inngest
2. **Group:** B
3. **Role and decision authority:** Partnerships & Integrations team at an explicitly designated professional address.
4. **Official public source:** [Inngest contact](https://www.inngest.com/get-in-touch) and [pricing](https://www.inngest.com/pricing).
5. **Concrete observed incident or operational gap:** Source-path analysis shows a fail-early timeout can delete durable run state before finalization effects publish; if publishing then fails, the handler logs the error, returns success, and loses the terminal failure.
6. **Evidence class:** inferred
7. **Exact evidence URL:** https://github.com/inngest/inngest/issues/4652
8. **Qualification score:** workflow 2 + recovery burden 1 + authority 2 + ability to pay 2 + recurrence 2 = **9/10**
9. **Why this may recur or expand:** Delete-before-publish ordering, queue acknowledgement, terminal events, retries, and run-state reconciliation are shared across fail-early paths and durable AI workflows.
10. **First operational rule shown in advance:** Publish or durably stage the terminal outcome before deleting run state; acknowledge the queue item only after finalization is recoverable.
11. **Unresolved questions:** Which finalization effects are transactional with state deletion? Can a reconciler re-publish terminal outcomes? Does queue redelivery retain enough identity after deletion?
12. **Proposed offer:** embedded / recurring workflow role
13. **One small CTA:** Ask the partnerships team to route a one-page finalization-invariant review to the executor owner.
14. **Verified professional contact route:** Official partnerships email — `partnerships@inngest.com`
15. **Personalized subject line:** Finalization invariant for Inngest terminal-run durability
16. **Complete email draft:**

> Hello Inngest Partnerships team,
>
> Inngest issue #4652 maps a durability window where run state is deleted before finalization effects publish; if publishing then fails, the handler logs the error, returns success, and the terminal failure has no durable observer. One rule I would show in advance is: publish or durably stage the terminal outcome before deleting run state, and acknowledge the queue item only after finalization is recoverable.
>
> The public analysis leaves three questions: which effects are transactional with deletion, whether a reconciler can re-publish terminal outcomes, and whether redelivery retains identity after state loss.
>
> I can keep a recurring failure-injection and receipt lane for boundaries like this. Would you route a one-page finalization-invariant review to the executor owner?
>
> Best,
>
> Shinichi Nagata
>
> AI-native Implementation & Verification Operator
17. **Risks or reasons not to contact:** This is static source analysis, not a live observed incident, so it receives only 1/2 for recovery evidence. The issue mentions a third-party AI review; independently verify the path before any send.
18. **Recommended send priority:** 20

## Cohort-level hold

No draft above is approved for sending. Before any future externalization, the receiving AI must re-open each evidence and contact URL, confirm the issue status and route purpose, compare the exact sender fields against the private Sender Canon, and produce a DOM-level field manifest. Any required phone, CAPTCHA, untraceable autofill value, or route-purpose mismatch is a stop condition for that prospect.
