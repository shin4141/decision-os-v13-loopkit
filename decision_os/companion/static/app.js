"use strict";

const DISCONNECTED_MESSAGE =
  "This companion session has ended. Close this tab and relaunch Decision OS Companion.app.";

let csrfToken = "";
let latestState = null;
let requestActive = false;
let connected = false;
let connectionGeneration = 0;
let bridgeRepositoryPath = null;
let guidedRepositoryPath = null;
let guidedInputError = "";
let guidedPurgeConfirmationIdentity = null;
let guidedPurgedInputClearedIdentity = null;
let guidedTransferredOriginalRequest = null;
let importedContract = null;
let contractImportGeneration = 0;
let ordinaryFocusIntent = null;
let ordinaryLastErrorId = null;
let ordinaryLastRevision = -1;
let ordinarySelectedFilename = null;
let ordinarySelectedFilenameRevision = null;
let operationStartPending = false;
let operationApprovalResponsePending = false;
let operationApprovalWasVisible = false;
let operationApprovalSeen = false;
let operationContinuingAfterApproval = false;
let operationTerminalTransitioned = false;
let operationLastApprovalKey = null;
let preparedContractTaskBinding = null;
let preparedContractTaskStarter = null;
let ordinaryReviewDisclosureIdentity = null;
let currentCodexResponse = "";
let copyResponseResetTimer = null;

const MAX_BRIDGE_ARTIFACT_BYTES = 1024 * 1024;
const CONTRACT_PREVIEW_CHARACTERS = 4096;
const CONTRACT_EXTENSIONS = [".md", ".txt"];
const GUIDED_INTAKE_AUTHORITY_CLAIM =
  "INTERPRETATION ONLY — NO EXECUTION AUTHORITY";
const MANUAL_OWNER_AUTHORITY = "MANUAL OWNER ATTESTED";
const CRYPTOGRAPHIC_PROVENANCE_NOT_ESTABLISHED = "NOT ESTABLISHED";
const MAX_ORDINARY_CONTRACT_BYTES = 61_440;
const EMPTY_SHA256 =
  "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

const byId = (id) => document.getElementById(id);
const optionalById = (id) => document.querySelectorAll(`#${id}`)[0] || null;

class CompanionUnavailableError extends Error {}

class RequestRejectedError extends Error {}

function setText(id, value) {
  byId(id).textContent = value == null ? "" : String(value);
}

function setHidden(id, hidden) {
  byId(id).classList.toggle("hidden", hidden);
}

function selectedContractFile() {
  return byId("contract-file").files?.[0] || null;
}

function supportedContractFile(file) {
  if (!file || typeof file.name !== "string") {
    return false;
  }
  const normalized = file.name.toLowerCase();
  return CONTRACT_EXTENSIONS.some((extension) =>
    normalized.endsWith(extension),
  );
}

function resetContractImport({ clearFile = false } = {}) {
  importedContract = null;
  guidedTransferredOriginalRequest = null;
  if (clearFile) {
    byId("contract-file").value = "";
  }
  byId("contract-full-content").value = "";
  setText("contract-import-state", "No contract");
  setText("contract-file-name", "No Contract imported");
  setText(
    "contract-preview-status",
    "Select a supported local file to preview it.",
  );
  setText("contract-preview", "");
  setHidden("contract-preview", true);
  setText("contract-import-error", "");
  setHidden("contract-import-error", true);
}

function renderContractImportControls() {
  byId("contract-file").disabled = !connected;
  byId("contract-import").disabled =
    !connected || selectedContractFile() === null;
  byId("contract-use-guided-intake").disabled =
    !connected || importedContract === null;
}

function showContractImportError(message) {
  resetContractImport();
  setText("contract-import-state", "Rejected");
  setText("contract-import-error", message);
  setHidden("contract-import-error", false);
  renderContractImportControls();
}

function statusLabel(state) {
  return {
    idle: "Idle",
    active: "Active",
    running: "Running",
    completed: "Completed",
    denied: "Denied",
    unsupported: "Unsupported",
    needs_attention: "Needs attention",
  }[state] || "Needs attention";
}

const OPERATION_STAGES = ["task", "run", "approval", "result"];
const OPERATION_TARGETS = {
  task: ["bounded-task-card", "task-heading"],
  run: ["progress-card", "progress-heading"],
  approval: ["approval-overlay", "approval-heading"],
  result: ["result-card", "result-heading"],
};
const TERMINAL_RUN_STATES = [
  "completed",
  "denied",
  "unsupported",
  "needs_attention",
];
const CONTRACT_TASK_MARKER = "Task to perform:";
const CONTRACT_TASK_PREFIX =
  "Perform only the bounded task defined by this fixed ordinary Contract context.";
const EXECUTION_AUTHORITY_INTERPRETATION_ONLY = "INTERPRETATION_ONLY";
const EXECUTION_AUTHORITY_BOUNDED = "BOUNDED_EXECUTION_AUTHORIZED";
const EXECUTION_AUTHORITY_UNKNOWN = "UNKNOWN";
const INTERPRETATION_ONLY_MESSAGE =
  "This Contract is fixed for interpretation only. It cannot authorize a Run.";
const UNKNOWN_EXECUTION_AUTHORITY_MESSAGE =
  "Execution authority is not established for this Contract.";

function reducedMotionRequested() {
  return Boolean(
    globalThis.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches,
  );
}

function moveToOperationStage(stage) {
  const targetIds = OPERATION_TARGETS[stage];
  if (!targetIds) {
    return false;
  }
  const target = byId(targetIds[0]);
  const focusTarget = byId(targetIds[1]);
  if (!target || target.classList.contains("hidden")) {
    return false;
  }
  target.scrollIntoView?.({
    behavior: reducedMotionRequested() ? "auto" : "smooth",
    block: "start",
  });
  focusTarget?.focus?.({ preventScroll: true });
  return true;
}

function approvalIdentity(approval) {
  if (!approval) {
    return null;
  }
  return [approval.repository, approval.action, approval.path].join("|");
}

function nonEmptyString(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function validOrdinaryReview(review) {
  return Boolean(
    review &&
      typeof review === "object" &&
      !Array.isArray(review) &&
      nonEmptyString(review.preserves) &&
      nonEmptyString(review.completion) &&
      Array.isArray(review.must_not_change) &&
      review.must_not_change.every(nonEmptyString) &&
      Array.isArray(review.unresolved) &&
      review.unresolved.every(nonEmptyString) &&
      nonEmptyString(review.does_not_authorize),
  );
}

function usableCurrentOrdinaryContext(panel) {
  const details = panel?.technical_details;
  // The server withholds review unless the full preparation, native state,
  // and current-repository binding is valid.  Do not reconstruct that
  // security decision from client-supplied identities.
  return Boolean(
    panel?.state === "FIXED" &&
      validOrdinaryReview(panel.review) &&
      details &&
      typeof details === "object" &&
      nonEmptyString(details.request_id) &&
      /^[0-9a-f]{64}$/i.test(details.interpretation_sha256 || "") &&
      nonEmptyString(panel.repository_identity),
  );
}

function contractExecutionAuthorized(panel) {
  return panel?.execution_authority === EXECUTION_AUTHORITY_BOUNDED;
}

function contractAuthorityMessage(panel) {
  if (panel?.execution_authority === EXECUTION_AUTHORITY_INTERPRETATION_ONLY) {
    return INTERPRETATION_ONLY_MESSAGE;
  }
  if (panel?.execution_authority === EXECUTION_AUTHORITY_BOUNDED) {
    return "This Contract explicitly authorizes bounded execution.";
  }
  return UNKNOWN_EXECUTION_AUTHORITY_MESSAGE;
}

function contractAuthorityModeLabel(panel) {
  return {
    [EXECUTION_AUTHORITY_INTERPRETATION_ONLY]: "Interpretation only",
    [EXECUTION_AUTHORITY_BOUNDED]: "Bounded execution authorized",
    [EXECUTION_AUTHORITY_UNKNOWN]: "Unknown",
  }[panel?.execution_authority] || "Unknown";
}

function ordinaryContextBinding(panel, repository) {
  if (
    !usableCurrentOrdinaryContext(panel) ||
    !contractExecutionAuthorized(panel) ||
    !nonEmptyString(repository?.path)
  ) {
    return null;
  }
  return JSON.stringify([
    repository.path,
    panel.repository_identity,
    panel.technical_details.request_id,
    panel.technical_details.interpretation_sha256,
  ]);
}

function contractTaskUserText(value) {
  const marker = `\n${CONTRACT_TASK_MARKER}`;
  const markerIndex = value.lastIndexOf(marker);
  if (markerIndex < 0) {
    return null;
  }
  return value.slice(markerIndex + marker.length);
}

function looksLikePreparedContractTask(value) {
  return Boolean(
    value.startsWith(`${CONTRACT_TASK_PREFIX}\nCurrent repository identity: `) &&
      value.includes("\nFixed Contract Request identity: ") &&
      value.includes("\nInterpretation SHA-256: ") &&
      value.includes(`\n${CONTRACT_TASK_MARKER}`),
  );
}

function clearPreparedContractTaskBinding() {
  preparedContractTaskBinding = null;
  preparedContractTaskStarter = null;
}

function invalidateReplacedContractTask(value) {
  if (value.trim().length === 0) {
    clearPreparedContractTaskBinding();
    return;
  }
  if (
    preparedContractTaskBinding !== null &&
    (!nonEmptyString(preparedContractTaskStarter) ||
      !value.startsWith(preparedContractTaskStarter))
  ) {
    clearPreparedContractTaskBinding();
  }
}

function taskReadiness(ordinary, repository) {
  const value = byId("task").value;
  invalidateReplacedContractTask(value);
  if (value.trim().length === 0) {
    return {
      mode: "empty",
      runnable: false,
      contextInserted: false,
      stalePreparedContext: false,
    };
  }
  if (preparedContractTaskBinding === null) {
    if (looksLikePreparedContractTask(value)) {
      return {
        mode: "contract",
        runnable: false,
        contextInserted: contractTaskUserText(value) !== null,
        stalePreparedContext: true,
        authorityBlocked: !contractExecutionAuthorized(ordinary),
      };
    }
    return {
      mode: "manual",
      runnable: true,
      contextInserted: false,
      stalePreparedContext: false,
      authorityBlocked: false,
    };
  }
  const currentBinding = ordinaryContextBinding(ordinary, repository);
  const userText = contractTaskUserText(value);
  const bindingCurrent = currentBinding === preparedContractTaskBinding;
  return {
    mode: "contract",
    runnable: bindingCurrent && userText !== null && userText.trim().length > 0,
    contextInserted: userText !== null,
    stalePreparedContext: !bindingCurrent,
    authorityBlocked: !contractExecutionAuthorized(ordinary),
  };
}

function operationPresentation(
  run,
  ordinary,
  task,
  repository,
  context = {},
) {
  const state = run?.state || "idle";
  const approval = context.approvalResponsePending
    ? null
    : run?.approval || null;
  const startPending = Boolean(context.startPending);
  const approvalSeen = Boolean(context.approvalSeen);
  const continuing = Boolean(context.continuingAfterApproval);
  const runLifecycleActive =
    startPending || state === "running" || TERMINAL_RUN_STATES.includes(state);
  const runTaskMode = ["manual", "contract"].includes(run?.task_mode)
    ? run.task_mode
    : null;
  const taskMode = runLifecycleActive && runTaskMode ? runTaskMode : task.mode;
  const historicalFixed = ordinary?.state === "FIXED";
  const fixed = usableCurrentOrdinaryContext(ordinary);
  const staleFixed = historicalFixed && !fixed;
  const contractStatus =
    taskMode === "manual"
      ? "Not used"
      : fixed
        ? "Complete"
        : staleFixed
          ? "Needs attention"
          : repository && !runLifecycleActive
            ? "Current"
            : "Not started";
  const statuses = {
    contract: contractStatus,
    task: "Not started",
    run: "Not started",
    approval: approvalSeen ? "Complete" : "Not started",
    result: "Not started",
  };

  if (startPending) {
    statuses.contract = contractStatus;
    statuses.task = "Complete";
    statuses.run = "Waiting for system";
    return {
      currentStage: "run",
      statuses,
      current: "Starting Run",
      happening: "The bounded Run is being started.",
      action: "Wait — no action is needed.",
      next: "Codex will begin working on the bounded task.",
    };
  }

  if (state === "running") {
    statuses.contract = contractStatus;
    statuses.task = "Complete";
    statuses.run = approval ? "Waiting for you" : "Waiting for system";
    if (approval) {
      statuses.approval = "Waiting for you";
      return {
        currentStage: "approval",
        statuses,
        current: "Approval required",
        happening: `${approval.action} is requested for ${approval.path}.`,
        action: "Choose one response for this exact file change.",
        next: "Your decision will either continue or stop this Run.",
      };
    }
    return {
      currentStage: "run",
      statuses,
      current: continuing ? "The Run is continuing" : "Codex is working",
      happening: continuing
        ? "The Run is continuing after your approval decision."
        : (run.progress || []).at(-1) || "Codex is working on the bounded task.",
      action: "Wait — no action is needed.",
      next: "Approval will appear if an exact file change needs your decision.",
    };
  }

  if (TERMINAL_RUN_STATES.includes(state)) {
    const needsAttention = ["unsupported", "needs_attention"].includes(state);
    statuses.contract = contractStatus;
    statuses.task = "Complete";
    statuses.run = needsAttention ? "Needs attention" : "Complete";
    statuses.result = needsAttention ? "Needs attention" : "Current";
    return {
      currentStage: "result",
      statuses,
      current: needsAttention ? "Run needs attention" : "Run finished",
      happening: needsAttention
        ? "The Run finished with a verification outcome that needs review."
        : "The bounded Run reached its terminal result.",
      action: needsAttention
        ? "Review the Run verification outcome."
        : "Nothing — this Run is complete.",
      next: "A new Run will not start automatically.",
    };
  }

  if (!repository) {
    return {
      currentStage: null,
      statuses,
      current: "Choose repository",
      happening: "Choose one local Git repository.",
      action: "Choose one repository.",
      next: "The Task field is ready for one bounded task.",
    };
  }
  if (task.mode === "empty") {
    statuses.task = "Current";
    return {
      currentStage: "task",
      statuses,
      current: "Enter a task",
      happening: "The repository is ready for one bounded task.",
      action: "Paste or write one bounded task.",
      next: "Run becomes available when the task is ready.",
    };
  }
  if (task.mode === "manual" && task.runnable) {
    statuses.task = "Current";
    return {
      currentStage: "task",
      statuses,
      current: "Task ready",
      happening: "One manually written bounded task is ready to start.",
      action: "Select Run to start this bounded task.",
      next: "The view will move to Run progress.",
    };
  }
  if (task.stalePreparedContext && task.authorityBlocked && fixed) {
    statuses.task = "Needs attention";
    return {
      currentStage: "task",
      statuses,
      current: "Prepared context cannot authorize a Run",
      happening: contractAuthorityMessage(ordinary),
      action: "Clear the bounded task field before writing a manual task.",
      next: "A manually written bounded task remains available after the field is cleared.",
    };
  }
  if (task.stalePreparedContext || staleFixed) {
    statuses.task = task.stalePreparedContext
      ? "Needs attention"
      : "Not started";
    return {
      currentStage: "task",
      statuses,
      current: "Prepared task needs attention",
      happening: "The prepared Contract context is not current for this repository.",
      action: "Clear the Task field before writing a manual task.",
      next: "Contract fixation remains available separately under Advanced workflows.",
    };
  }
  if (!fixed) {
    return {
      currentStage: "task",
      statuses,
      current: "Enter a task",
      happening: "The repository is ready for one bounded task.",
      action: "Paste or write one bounded task.",
      next: "Run becomes available when the task is ready.",
    };
  }
  if (!contractExecutionAuthorized(ordinary)) {
    return {
      currentStage: "task",
      statuses,
      current: "Enter a task",
      happening: "The fixed Contract is separate from ordinary task execution.",
      action: "Paste or write one bounded task.",
      next: "A manual task remains independent of the fixed Contract artifact.",
    };
  }
  statuses.task = "Current";
  if (task.contextInserted && !task.runnable) {
    return {
      currentStage: "task",
      statuses,
      current: "Add bounded task",
      happening: "The fixed Contract context has been inserted.",
      action: "Write one exact task after “Task to perform:”.",
      next: "Run becomes available after the exact task is added.",
    };
  }
  return {
    currentStage: "task",
    statuses,
    current: task.runnable ? "Task ready" : "Contract fixed",
    happening: task.runnable
      ? "One bounded task is ready to start."
      : "The fixed Contract context is ready for a bounded task.",
    action: task.runnable
      ? "Select Run to start this bounded task."
      : "Use this Contract for a bounded task.",
    next: task.runnable
      ? "The view will move to Run progress."
      : "The Contract context will be inserted without starting a Run.",
  };
}

function renderOperationAwareness(run, ordinary, repository) {
  const presentation = operationPresentation(
    run,
    ordinary,
    taskReadiness(ordinary, repository),
    repository,
    {
      approvalResponsePending: operationApprovalResponsePending,
      approvalSeen: operationApprovalSeen,
      continuingAfterApproval: operationContinuingAfterApproval,
      startPending: operationStartPending,
    },
  );
  setText("operation-current", presentation.current);
  setText("operation-happening", presentation.happening);
  setText("operation-action", presentation.action);
  setText("operation-next", presentation.next);
  const stageButtons = Array.from(
    document.querySelectorAll("[data-operation-stage]"),
  );
  for (const stage of OPERATION_STAGES) {
    const button = stageButtons.find(
      (candidate) => candidate.dataset.operationStage === stage,
    );
    const status = presentation.statuses[stage];
    setText(`operation-${stage}-status`, status);
    button?.setAttribute("aria-label", `${stage}: ${status}`);
    if (stage === presentation.currentStage) {
      button?.setAttribute("aria-current", "step");
    } else {
      button?.removeAttribute("aria-current");
    }
  }
}

function resetOperationTransitionMemory() {
  operationApprovalResponsePending = false;
  operationApprovalWasVisible = false;
  operationApprovalSeen = false;
  operationContinuingAfterApproval = false;
  operationTerminalTransitioned = false;
  operationLastApprovalKey = null;
}

function coordinateOperationTransition(run) {
  const state = run?.state || "idle";
  const rawApproval = run?.approval || null;
  if (operationApprovalResponsePending && !rawApproval) {
    operationApprovalResponsePending = false;
  }
  const approval = operationApprovalResponsePending ? null : rawApproval;
  const approvalKey = approvalIdentity(approval);

  if (state === "idle") {
    resetOperationTransitionMemory();
    return;
  }
  if (approval && approvalKey !== operationLastApprovalKey) {
    operationApprovalSeen = true;
    operationContinuingAfterApproval = false;
    moveToOperationStage("approval");
  } else if (
    operationApprovalWasVisible &&
    !approval &&
    state === "running"
  ) {
    operationContinuingAfterApproval = true;
    moveToOperationStage("run");
  }
  if (
    TERMINAL_RUN_STATES.includes(state) &&
    !operationTerminalTransitioned
  ) {
    operationTerminalTransitioned = true;
    operationApprovalResponsePending = false;
    moveToOperationStage("result");
  }
  operationApprovalWasVisible = Boolean(approval);
  operationLastApprovalKey = approvalKey;
}

function beginOperationRun(taskMode) {
  resetOperationTransitionMemory();
  operationStartPending = true;
  byId("run").disabled = true;
  setHidden("progress-card", false);
  setText("run-state", "Starting Run");
  const progress = byId("progress");
  const item = document.createElement("li");
  item.textContent = "Starting Run";
  progress.replaceChildren(item);
  renderOperationAwareness(
    {
      state: "running",
      task_mode: taskMode,
      progress: ["Starting Run"],
      approval: null,
    },
    latestState?.ordinary_contract,
    latestState?.repository,
  );
  moveToOperationStage("run");
}

function formatNumber(value, digits = 0) {
  if (value == null) {
    return "UNKNOWN";
  }
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

function metricRows(target, receipt) {
  target.replaceChildren();
  const rows = receipt
    ? [
        ["Verified Saves", formatNumber(receipt.verified_saves)],
        ["Verified Reuses", formatNumber(receipt.verified_reuses)],
        ["Recovered", `${formatNumber(receipt.estimated_minutes, 1)} minutes`],
        ["Human-time value", `¥${formatNumber(receipt.estimated_money_jpy)}`],
        [
          "Token estimate",
          receipt.estimated_tokens == null
            ? "UNKNOWN"
            : formatNumber(receipt.estimated_tokens),
        ],
      ]
    : [
        ["Verified Saves", "0"],
        ["Verified Reuses", "0"],
        ["Recovered", "0.0 minutes"],
        ["Human-time value", "¥0"],
        ["Token estimate", "UNKNOWN"],
      ];
  for (const [label, value] of rows) {
    const term = document.createElement("dt");
    const detail = document.createElement("dd");
    term.textContent = label;
    detail.textContent = value;
    target.append(term, detail);
  }
}

function renderProgress(run) {
  const list = byId("progress");
  list.replaceChildren();
  for (const message of run.progress || []) {
    const item = document.createElement("li");
    item.textContent = message;
    list.append(item);
  }
  const visible = run.state !== "idle" || (run.progress || []).length > 0;
  setHidden("progress-card", !visible);
  setText("run-state", statusLabel(run.state));
  setHidden("run-error", !run.error);
  setText("run-error", run.error || "");
}

function renderActions(actions) {
  const container = byId("file-actions");
  container.replaceChildren();
  for (const action of actions || []) {
    const row = document.createElement("div");
    row.className = "file-action";
    const path = document.createElement("code");
    const status = document.createElement("span");
    path.textContent = `${action.action}: ${action.path}`;
    status.textContent = `${action.status} · ${action.access}`;
    row.append(path, status);
    container.append(row);
  }
}

function renderRuntime(runtime) {
  const target = byId("runtime");
  target.replaceChildren();
  if (!runtime) {
    return;
  }
  const rows = [
    ["Authentication", runtime.authentication],
    ["Model", runtime.model],
    ["Reasoning effort", runtime.reasoning_effort],
    ["Service tier", runtime.service_tier],
    ["Codex version", runtime.codex_version],
  ];
  for (const [label, value] of rows) {
    const term = document.createElement("dt");
    const detail = document.createElement("dd");
    term.textContent = label;
    detail.textContent = value;
    target.append(term, detail);
  }
}

function renderReadEvidence(evidence) {
  const values = Array.isArray(evidence) ? evidence : [];
  const target = byId("read-evidence-list");
  target.replaceChildren();
  setHidden("read-evidence-card", values.length === 0);
  for (const value of values) {
    const item = document.createElement("dl");
    item.className = "read-evidence-item";
    const rows = [
      ["Status", value.status],
      ["Path", value.path],
      ["Bytes", value.bytes],
      ["SHA-256", value.sha256],
      ["Repository", value.repository_identity],
      ["Reason", value.reason],
    ];
    for (const [label, field] of rows) {
      if (field == null || field === "") {
        continue;
      }
      const term = document.createElement("dt");
      const detail = document.createElement("dd");
      term.textContent = label;
      detail.textContent = String(field);
      item.append(term, detail);
    }
    target.append(item);
  }
}

function resetCopyResponseFeedback() {
  if (copyResponseResetTimer !== null) {
    window.clearTimeout?.(copyResponseResetTimer);
    copyResponseResetTimer = null;
  }
  setText("copy-response", "Copy response");
  setText("copy-response-status", "");
}

function renderCopyResponse(response, terminal) {
  const exactResponse = typeof response === "string" ? response : "";
  if (exactResponse !== currentCodexResponse) {
    currentCodexResponse = exactResponse;
    resetCopyResponseFeedback();
  }
  const available = terminal && currentCodexResponse.length > 0;
  setHidden("copy-response", !available);
  byId("copy-response").disabled = !available;
}

async function writeClipboardText(value) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }
  const activeElement = document.activeElement;
  const scrollX = window.scrollX;
  const scrollY = window.scrollY;
  const localCopy = document.createElement("textarea");
  localCopy.value = value;
  localCopy.readOnly = true;
  localCopy.setAttribute("aria-hidden", "true");
  localCopy.style.position = "fixed";
  localCopy.style.inset = "0 auto auto -10000px";
  document.body.append(localCopy);
  localCopy.select();
  const copied = document.execCommand?.("copy") === true;
  localCopy.remove();
  activeElement?.focus?.({ preventScroll: true });
  window.scrollTo?.(scrollX, scrollY);
  if (!copied) {
    throw new Error("Clipboard copy failed.");
  }
}

function visibleResponse(run) {
  const error = typeof run.error === "string" ? run.error : "";
  if (error) {
    return error;
  }
  const result = typeof run.result === "string" ? run.result : "";
  if (result) {
    return result;
  }
  if (!TERMINAL_RUN_STATES.includes(run.state)) {
    return "";
  }
  return run.state === "completed"
    ? "The bounded Run completed without a final text response."
    : "No final result was available.";
}

function renderResult(run) {
  const terminal = TERMINAL_RUN_STATES.includes(run.state);
  const response = visibleResponse(run);
  setHidden("result-card", !terminal);
  byId("new-run").disabled = !terminal;
  setText(
    "result-state",
    ["unsupported", "needs_attention"].includes(run.state)
      ? "Review required"
      : "Result available",
  );
  const outcomes = run.outcomes || {};
  setText("result-execution", outcomes.execution?.label || "Not established");
  setText(
    "result-file-change",
    outcomes.file_change?.label ||
      "Not established — file-change outcome requires review",
  );
  setText(
    "result-verification",
    outcomes.verification?.label || "Not established",
  );
  const verificationReason = outcomes.verification?.reason || "";
  setText("result-verification-reason", verificationReason);
  setHidden("result-verification-reason", !verificationReason);
  setText("result", response);
  renderCopyResponse(response, terminal);
  renderActions(run.file_actions);
  renderRuntime(run.runtime);
  renderReadEvidence(run.read_evidence);
}

function renderApproval(approval) {
  for (const button of document.querySelectorAll("[data-choice]")) {
    button.disabled = !approval;
  }
  setHidden("approval-overlay", !approval);
  setText("approval-repository", "");
  setText("approval-action", "");
  setText("approval-path", "");
  setText("approval-diff", "");
  setHidden("approval-reason-label", true);
  setHidden("approval-reason", true);
  setText("approval-reason", "");
  if (!approval) {
    return;
  }
  setText("approval-repository", approval.repository);
  setText("approval-action", approval.action);
  setText("approval-path", approval.path);
  setText("approval-diff", approval.diff);
  const hasReason = Boolean(approval.reason);
  setHidden("approval-reason-label", !hasReason);
  setHidden("approval-reason", !hasReason);
  setText("approval-reason", approval.reason || "");
}

function renderDefaults(defaults) {
  const target = byId("defaults");
  target.replaceChildren();
  if (!defaults || defaults.length === 0) {
    const empty = document.createElement("p");
    empty.className = "path-value";
    empty.textContent = "No saved repository access.";
    target.append(empty);
    return;
  }
  for (const item of defaults) {
    const row = document.createElement("div");
    row.className = "default-row";
    const description = document.createElement("code");
    description.textContent = `${item.action}: ${item.path}`;
    const revoke = document.createElement("button");
    revoke.type = "button";
    revoke.className = "danger";
    revoke.textContent = "Revoke";
    revoke.disabled = !connected;
    revoke.addEventListener("click", async () => {
      const confirmed = window.confirm(
        "Revoke this exact saved repository access? Historical proof remains.",
      );
      if (confirmed) {
        await postJSON("/api/default/revoke", { handle: item.handle });
      }
    });
    row.append(description, revoke);
    target.append(row);
  }
}

function displayValue(value, fallback = "") {
  if (value == null || value === "") {
    return fallback;
  }
  if (typeof value === "string") {
    return value;
  }
  const serialized = JSON.stringify(value, null, 2);
  return serialized == null ? fallback : serialized;
}

function renderGuidedList(id, values) {
  const target = byId(id);
  target.replaceChildren();
  const items = Array.isArray(values) ? values : [];
  if (items.length === 0) {
    const item = document.createElement("li");
    item.textContent = "None recorded.";
    target.append(item);
    return;
  }
  for (const value of items) {
    const item = document.createElement("li");
    item.textContent = displayValue(value, "UNKNOWN");
    target.append(item);
  }
}

function intelligenceTransplantDisplay(value, fallback) {
  const displayed = displayValue(value, fallback);
  return displayed
    .split("MANUAL_OWNER_ATTESTED")
    .join(MANUAL_OWNER_AUTHORITY)
    .split("NOT_ESTABLISHED")
    .join(CRYPTOGRAPHIC_PROVENANCE_NOT_ESTABLISHED);
}

function renderIntelligenceTransplant(value, repository) {
  const panel = value && typeof value === "object" ? value : null;
  const visible = Boolean(
    repository &&
      panel &&
      (panel.run_id ||
        panel.error ||
        panel.store_state === "BLOCKED_CORRUPT" ||
        panel.store_state === "BUSY"),
  );
  setHidden("intelligence-transplant-card", !visible);
  setText(
    "intelligence-transplant-gate",
    panel ? intelligenceTransplantDisplay(panel.current_gate, "UNKNOWN") : "",
  );
  setText(
    "intelligence-transplant-run-id",
    panel ? intelligenceTransplantDisplay(panel.run_id, "UNKNOWN") : "",
  );
  setText(
    "intelligence-transplant-execution-status",
    panel
      ? intelligenceTransplantDisplay(panel.execution_status, "NOT ESTABLISHED")
      : "",
  );
  setText(
    "intelligence-transplant-delta-state",
    panel ? intelligenceTransplantDisplay(panel.delta_state, "NONE") : "",
  );
  setText(
    "intelligence-transplant-structural-validation",
    panel
      ? intelligenceTransplantDisplay(panel.structural_validation, "UNKNOWN")
      : "",
  );
  setText(
    "intelligence-transplant-authority-provenance",
    panel
      ? intelligenceTransplantDisplay(
          panel.authority_provenance,
          MANUAL_OWNER_AUTHORITY,
        )
      : "",
  );
  setText(
    "intelligence-transplant-cryptographic-provenance",
    panel
      ? intelligenceTransplantDisplay(
          panel.cryptographic_provenance,
          CRYPTOGRAPHIC_PROVENANCE_NOT_ESTABLISHED,
        )
      : "",
  );
  setText(
    "intelligence-transplant-generalized-transplant",
    panel
      ? intelligenceTransplantDisplay(
          panel.generalized_transplant,
          CRYPTOGRAPHIC_PROVENANCE_NOT_ESTABLISHED,
        )
      : "",
  );
  renderGuidedList(
    "intelligence-transplant-missing-evidence",
    panel ? panel.missing_evidence : [],
  );
  setText(
    "intelligence-transplant-next-action",
    panel ? intelligenceTransplantDisplay(panel.next_one_action, "UNKNOWN") : "",
  );
  renderGuidedList(
    "intelligence-transplant-not-allowed-next",
    panel ? panel.not_allowed_next : [],
  );
  setText(
    "intelligence-transplant-active-cap",
    panel ? displayValue(panel.active_cap, "None recorded.") : "",
  );
  setText(
    "intelligence-transplant-evidence-objects",
    panel
      ? displayValue(
          Array.isArray(panel.evidence_objects)
            ? panel.evidence_objects
            : [],
          "[]",
        )
      : "",
  );
  setText(
    "intelligence-transplant-lineage",
    panel
      ? displayValue(
          panel.lineage || panel.evidence_lineage || [],
          "[]",
        )
      : "",
  );
  const error = panel ? panel.error || "" : "";
  setText("intelligence-transplant-error", error);
  setHidden("intelligence-transplant-error", !error);
}

function renderOrdinaryList(id, values, emptyText) {
  const target = byId(id);
  target.replaceChildren();
  const items = Array.isArray(values) && values.length ? values : [emptyText];
  for (const value of items) {
    const item = document.createElement("li");
    item.textContent = value == null ? "" : String(value);
    target.append(item);
  }
}

function friendlyFixedState(value) {
  return {
    NO: "No",
    YES: "Yes",
    UNKNOWN_READ_BACK_REQUIRED: "Unknown — receipt read-back is required",
  }[value] || "Unknown";
}

function showOrdinarySelectedFilename(filename) {
  ordinarySelectedFilename =
    typeof filename === "string" && filename.length ? filename : null;
  setText(
    "ordinary-contract-selected-file",
    ordinarySelectedFilename
      ? `Selected file: ${ordinarySelectedFilename}`
      : "Selected file: None selected.",
  );
}

function recordOrdinarySelectedFilename(filename, operationRevision) {
  ordinarySelectedFilenameRevision = Number.isInteger(operationRevision)
    ? operationRevision
    : ordinaryLastRevision;
  showOrdinarySelectedFilename(filename);
}

function syncOrdinarySelectedFilename(panel) {
  const serverFilename = panel?.source_identity?.filename;
  const serverRevision = Number.isInteger(panel?.operation_revision)
    ? panel.operation_revision
    : 0;
  const preparationSucceeded = [
    "REVIEW_READY",
    "NEEDS_CONFIRMATION",
    "FIXING",
    "FIXED",
  ].includes(panel?.state);
  if (
    typeof serverFilename === "string" &&
    serverFilename.length &&
    (ordinarySelectedFilename === null ||
      ordinarySelectedFilenameRevision === null ||
      (preparationSucceeded &&
        serverRevision > ordinarySelectedFilenameRevision))
  ) {
    ordinarySelectedFilenameRevision = null;
    showOrdinarySelectedFilename(serverFilename);
    return;
  }
  showOrdinarySelectedFilename(ordinarySelectedFilename);
}

function ordinaryTaskStarterValue(value, fallback = "") {
  const concise = displayValue(value, fallback).replace(/\s+/g, " ").trim();
  return concise || fallback;
}

function ordinaryTaskStarterList(values, emptyText) {
  if (!Array.isArray(values) || values.length === 0) {
    return emptyText;
  }
  return values
    .map((value) => ordinaryTaskStarterValue(value))
    .join("; ");
}

function ordinaryFixedTaskStarter(panel) {
  const details =
    panel?.technical_details && typeof panel.technical_details === "object"
      ? panel.technical_details
      : {};
  const review =
    panel?.review && typeof panel.review === "object" ? panel.review : {};
  return [
    CONTRACT_TASK_PREFIX,
    `Current repository identity: ${ordinaryTaskStarterValue(panel?.repository_identity)}`,
    `Fixed Contract Request identity: ${ordinaryTaskStarterValue(details.request_id)}`,
    `Interpretation SHA-256: ${ordinaryTaskStarterValue(details.interpretation_sha256)}`,
    `What the Contract preserves: ${ordinaryTaskStarterValue(review.preserves)}`,
    `What counts as completion: ${ordinaryTaskStarterValue(review.completion)}`,
    `What must not be changed: ${ordinaryTaskStarterList(review.must_not_change, "No additional protected wording is listed.")}`,
    `What remains unresolved: ${ordinaryTaskStarterList(review.unresolved, "Nothing remains unresolved.")}`,
    `What the operation does not authorize: ${ordinaryTaskStarterValue(review.does_not_authorize)}`,
    CONTRACT_TASK_MARKER,
  ].join("\n");
}

function ensureOrdinaryPrepareTaskButton() {
  let button = byId("ordinary-contract-prepare-task");
  if (button) {
    return button;
  }
  button = document.createElement("button");
  button.id = "ordinary-contract-prepare-task";
  button.type = "button";
  button.textContent = "Use this Contract for a bounded task";
  button.addEventListener("click", () => {
    const panel = latestState?.ordinary_contract;
    const repository = latestState?.repository;
    const binding = ordinaryContextBinding(panel, repository);
    if (binding === null) {
      return;
    }
    const task = byId("task");
    if (task.value.trim().length === 0) {
      const starter = ordinaryFixedTaskStarter(panel);
      preparedContractTaskBinding = binding;
      preparedContractTaskStarter = starter;
      task.value = starter;
      task.dispatchEvent(new Event("input", { bubbles: true }));
    }
    task.scrollIntoView?.({ block: "center" });
    task.focus();
    task.setSelectionRange?.(task.value.length, task.value.length);
  });
  byId("ordinary-contract-success").insertAdjacentElement("afterend", button);
  return button;
}

function renderOrdinaryContract(ordinary, repository) {
  const panel = ordinary && typeof ordinary === "object" ? ordinary : null;
  const revision = Number.isInteger(panel?.operation_revision)
    ? panel.operation_revision
    : 0;
  if (revision < ordinaryLastRevision && requestActive) {
    return;
  }
  ordinaryLastRevision = Math.max(ordinaryLastRevision, revision);
  const state = panel?.state || "NO_CONTRACT";
  const review = panel?.review && typeof panel.review === "object"
    ? panel.review
    : null;
  const clarification =
    panel?.clarification && typeof panel.clarification === "object"
      ? panel.clarification
      : null;
  const error =
    panel?.action_error && typeof panel.action_error === "object"
      ? panel.action_error
      : null;
  const actions = new Set(
    Array.isArray(panel?.allowed_actions) ? panel.allowed_actions : [],
  );
  syncOrdinarySelectedFilename(panel);

  setText(
    "ordinary-contract-status",
    panel?.status_label || "Select a Contract",
  );
  setText(
    "ordinary-contract-progress",
    panel?.progress_text || "Choose one local Markdown or text Contract.",
  );
  const reviewDisclosure = byId("ordinary-contract-review");
  const reviewIdentity = review
    ? [
        panel?.technical_details?.request_id || "",
        panel?.technical_details?.interpretation_sha256 || "",
      ].join("|")
    : null;
  if (reviewIdentity !== ordinaryReviewDisclosureIdentity) {
    reviewDisclosure.open = false;
    ordinaryReviewDisclosureIdentity = reviewIdentity;
  }
  setHidden("ordinary-contract-meaning", !review);
  setHidden("ordinary-contract-review", !review);
  setText("ordinary-contract-summary", review ? panel?.contract_summary || "" : "");
  setText(
    "ordinary-contract-usage-mode",
    review ? contractAuthorityModeLabel(panel) : "",
  );
  setText(
    "ordinary-contract-can-run",
    review ? (contractExecutionAuthorized(panel) ? "Yes" : "No") : "",
  );
  setText(
    "ordinary-contract-authority-message",
    review ? contractAuthorityMessage(panel) : "",
  );
  setText("ordinary-contract-preserves", review?.preserves || "");
  setText("ordinary-contract-completion", review?.completion || "");
  renderOrdinaryList(
    "ordinary-contract-dnt",
    review?.must_not_change,
    "No additional protected wording is listed.",
  );
  renderOrdinaryList(
    "ordinary-contract-unresolved",
    review?.unresolved,
    "Nothing remains unresolved.",
  );
  setText("ordinary-contract-authority", review?.does_not_authorize || "");

  setHidden("ordinary-contract-clarification", !clarification);
  setText("ordinary-contract-question", clarification?.question || "");
  if (!clarification) {
    byId("ordinary-contract-answer-confirm").checked = false;
    byId("ordinary-contract-answer-reject").checked = false;
  }
  const answerSelected = Boolean(
    byId("ordinary-contract-answer-confirm").checked ||
      byId("ordinary-contract-answer-reject").checked,
  );
  byId("ordinary-contract-confirm").disabled =
    !connected || requestActive || !actions.has("CONFIRM_ANSWER") || !answerSelected;
  byId("ordinary-contract-answer-confirm").disabled =
    !connected || requestActive || !actions.has("CONFIRM_ANSWER");
  byId("ordinary-contract-answer-reject").disabled =
    !connected || requestActive || !actions.has("CONFIRM_ANSWER");

  byId("ordinary-contract-file").disabled =
    !connected || requestActive || !repository || !actions.has("SELECT_CONTRACT");
  byId("ordinary-contract-fix").disabled =
    !connected || requestActive || !actions.has("FIX_CONTRACT");
  const fixed = usableCurrentOrdinaryContext(panel);
  const staleFixed = state === "FIXED" && !fixed;
  if (staleFixed) {
    setText("ordinary-contract-status", "Needs attention");
    setText(
      "ordinary-contract-progress",
      "Select and fix this Contract for the current repository.",
    );
  }
  setText(
    "ordinary-contract-success",
    fixed
      ? "Contract fixed. This Contract can now be used to resume the same decision in this repository without reconstructing its meaning from scratch."
      : "",
  );
  setHidden("ordinary-contract-success", !fixed);
  const canPrepareTask = fixed && contractExecutionAuthorized(panel);
  const prepareTaskButton = canPrepareTask
    ? ensureOrdinaryPrepareTaskButton()
    : byId("ordinary-contract-prepare-task");
  if (canPrepareTask) {
    prepareTaskButton?.classList.toggle("hidden", false);
  } else {
    prepareTaskButton?.remove?.();
  }

  setHidden("ordinary-contract-error", !error);
  setText("ordinary-contract-error-what", error?.what_failed || "");
  setText(
    "ordinary-contract-error-state",
    error ? panel?.status_label || "Action needs attention" : "",
  );
  setText(
    "ordinary-contract-error-fixed",
    error ? friendlyFixedState(error.anything_fixed) : "",
  );
  setText(
    "ordinary-contract-error-action",
    error?.user_action_required || "",
  );
  const retryableFix = Boolean(
    error?.retryable &&
      state === "FIX_FAILED" &&
      panel?.preparation_id &&
      panel?.technical_details,
  );
  byId("ordinary-contract-error-retry").disabled =
    !connected || requestActive || !retryableFix;
  setHidden("ordinary-contract-error-retry", !retryableFix);
  byId("ordinary-contract-error-dismiss").disabled =
    !connected || requestActive || !actions.has("DISMISS_ERROR");
  setText(
    "ordinary-contract-technical-body",
    panel ? JSON.stringify(panel.technical_details || {}, null, 2) : "",
  );

  if (ordinaryFocusIntent === "prepare" && state === "NEEDS_CONFIRMATION") {
    byId("ordinary-contract-question").focus();
    ordinaryFocusIntent = null;
  } else if (
    ordinaryFocusIntent === "prepare" &&
    ["REVIEW_READY", "CANNOT_FIX_SAFELY"].includes(state)
  ) {
    const status = byId("ordinary-contract-status");
    status.setAttribute("tabindex", "-1");
    status.focus();
    ordinaryFocusIntent = null;
  } else if (ordinaryFocusIntent === "fix" && fixed) {
    byId("ordinary-contract-success").focus();
    ordinaryFocusIntent = null;
  } else if (
    error &&
    error.error_id &&
    error.error_id !== ordinaryLastErrorId &&
    ordinaryFocusIntent
  ) {
    ordinaryLastErrorId = error.error_id;
    byId("ordinary-contract-error").focus();
    ordinaryFocusIntent = null;
  }
}

const guidedIntakeActionIds = [
  "guided-intake-capture",
  "guided-intake-copy",
  "guided-intake-import-draft",
  "guided-intake-confirm",
  "guided-intake-freeze",
  "guided-intake-purge",
  "guided-intake-transfer",
];

const guidedIntakeInputIds = [
  "guided-intake-original-request",
  "guided-intake-producer-label",
  "guided-intake-draft-json",
  "guided-intake-answer",
  "guided-intake-resulting-delta",
  "guided-intake-purge-confirm",
];

function resetGuidedIntakeDrafts() {
  byId("guided-intake-original-request").value = "";
  byId("guided-intake-producer-label").value = "";
  byId("guided-intake-draft-json").value = "{}";
  byId("guided-intake-answer").value = "";
  byId("guided-intake-resulting-delta").value = "{}";
  byId("guided-intake-purge-confirm").checked = false;
  guidedPurgeConfirmationIdentity = null;
  guidedPurgedInputClearedIdentity = null;
  guidedTransferredOriginalRequest = null;
  guidedInputError = "";
}

function guidedRequestIdentityKey(panel) {
  const identity = panel && panel.request_identity;
  if (
    !identity ||
    typeof identity !== "object" ||
    !identity.request_id ||
    !identity.sha256
  ) {
    return null;
  }
  return `${identity.request_id}:${identity.sha256}`;
}

function renderGuidedIntake(intake, repository) {
  const panel = intake && typeof intake === "object" ? intake : null;
  const interpretation =
    panel && panel.interpretation && typeof panel.interpretation === "object"
      ? panel.interpretation
      : {};
  const objective =
    interpretation.objective &&
    typeof interpretation.objective === "object"
      ? interpretation.objective
      : {};
  const completion =
    interpretation.completion_line &&
    typeof interpretation.completion_line === "object"
      ? interpretation.completion_line
      : {};
  const activeQuestion =
    panel &&
    panel.active_question &&
    typeof panel.active_question === "object"
      ? panel.active_question
      : null;
  const freeze =
    panel && panel.freeze && typeof panel.freeze === "object"
      ? panel.freeze
      : null;
  const purged = Boolean(
    panel && panel.state === "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
  );
  const currentPurgeIdentity = guidedRequestIdentityKey(panel);
  if (
    purged &&
    guidedPurgedInputClearedIdentity !== currentPurgeIdentity
  ) {
    byId("guided-intake-original-request").value = "";
    guidedTransferredOriginalRequest = null;
    guidedPurgedInputClearedIdentity = currentPurgeIdentity;
  } else if (!purged) {
    guidedPurgedInputClearedIdentity = null;
  }
  if (
    byId("guided-intake-purge-confirm").checked &&
    guidedPurgeConfirmationIdentity !== currentPurgeIdentity
  ) {
    byId("guided-intake-purge-confirm").checked = false;
    guidedPurgeConfirmationIdentity = null;
  }

  setText("guided-intake-state", panel ? panel.state || "No intake" : "No intake");
  setText(
    "guided-intake-authority-claim",
    panel && panel.authority_claim
      ? panel.authority_claim
      : GUIDED_INTAKE_AUTHORITY_CLAIM,
  );
  setText(
    "guided-intake-authority-explanation",
    panel ? panel.authority_explanation || "" : "",
  );
  setText(
    "guided-intake-original-exact",
    purged ? "UNAVAILABLE" : panel ? panel.original_request || "" : "",
  );
  setText(
    "guided-intake-request-identity",
    panel ? displayValue(panel.request_identity) : "",
  );
  setText(
    "guided-intake-raw-source-availability",
    panel ? displayValue(panel.raw_source_availability, "UNKNOWN") : "UNKNOWN",
  );
  setText(
    "guided-intake-judgment-reuse",
    panel ? displayValue(panel.judgment_reuse, "UNKNOWN") : "UNKNOWN",
  );
  setText(
    "guided-intake-fidelity-evaluation",
    panel ? displayValue(panel.fidelity_evaluation, "UNKNOWN") : "UNKNOWN",
  );
  setText(
    "guided-intake-purge-status",
    panel ? displayValue(panel.purge) : "",
  );
  setText("guided-intake-objective", objective.text || "");
  setText(
    "guided-intake-objective-status",
    objective.fidelity_status || "UNKNOWN",
  );
  setText("guided-intake-completion-line", completion.text || "");
  setText(
    "guided-intake-completion-status",
    completion.testability_status || "UNKNOWN",
  );
  setText(
    "guided-intake-gate",
    displayValue(interpretation.gate, "UNKNOWN"),
  );
  setText(
    "guided-intake-objective-atoms",
    panel
      ? displayValue(
          Array.isArray(objective.atoms) ? objective.atoms : [],
          "[]",
        )
      : "",
  );
  setText(
    "guided-intake-completion-checks",
    panel
      ? displayValue(
          Array.isArray(completion.checks) ? completion.checks : [],
          "[]",
        )
      : "",
  );
  setText(
    "guided-intake-confirmation-history",
    panel
      ? displayValue(
          Array.isArray(panel.confirmation_history)
            ? panel.confirmation_history
            : [],
          "[]",
        )
      : "",
  );
  renderGuidedList(
    "guided-intake-do-not-touch",
    interpretation.do_not_touch,
  );
  renderGuidedList("guided-intake-unknown", interpretation.unknown);
  setText(
    "guided-intake-copy-output",
    panel ? panel.copy_for_pro_prompt || "" : "",
  );
  setHidden("guided-intake-confirmation", !activeQuestion);
  setText(
    "guided-intake-question-field",
    activeQuestion ? `Field: ${activeQuestion.field || "UNKNOWN"}` : "",
  );
  setText(
    "guided-intake-question",
    activeQuestion ? activeQuestion.question || "" : "",
  );
  setText(
    "guided-intake-freeze-identity",
    freeze ? displayValue(freeze) : "",
  );
  setText(
    "guided-intake-transfer-receipt",
    panel ? displayValue(panel.transfer_receipt) : "",
  );

  const error = guidedInputError || (panel ? panel.error || "" : "");
  setText("guided-intake-error", error);
  setHidden("guided-intake-error", !error);

  const usable = Boolean(
    connected && repository && !(panel && panel.error),
  );
  const hasOriginal = Boolean(panel && panel.original_request);
  const freezeIsCurrent = Boolean(freeze && freeze.current === true);
  const purgeIdentity = panel && panel.request_identity;
  byId("guided-intake-original-request").disabled = !usable;
  byId("guided-intake-capture").disabled =
    !usable ||
    byId("guided-intake-original-request").value.trim().length === 0;
  byId("guided-intake-copy").disabled = !usable || !hasOriginal;
  byId("guided-intake-producer-label").disabled =
    !usable || !hasOriginal;
  byId("guided-intake-draft-json").disabled =
    !usable || !hasOriginal;
  byId("guided-intake-import-draft").disabled =
    !usable ||
    !hasOriginal ||
    byId("guided-intake-producer-label").value.trim().length === 0 ||
    byId("guided-intake-draft-json").value.trim().length === 0;
  byId("guided-intake-answer").disabled = !usable || !activeQuestion;
  byId("guided-intake-resulting-delta").disabled =
    !usable || !activeQuestion;
  byId("guided-intake-confirm").disabled =
    !usable ||
    !activeQuestion ||
    byId("guided-intake-answer").value.trim().length === 0 ||
    byId("guided-intake-resulting-delta").value.trim().length === 0;
  byId("guided-intake-purge-confirm").disabled =
    !usable || !hasOriginal || purged;
  byId("guided-intake-purge").disabled =
    !usable ||
    !hasOriginal ||
    purged ||
    !(purgeIdentity && typeof purgeIdentity === "object") ||
    !byId("guided-intake-purge-confirm").checked;
  byId("guided-intake-freeze").disabled =
    !usable ||
    !hasOriginal ||
    Boolean(activeQuestion) ||
    freezeIsCurrent ||
    interpretation.gate !== "CLEAR ENOUGH TO FREEZE";
  byId("guided-intake-transfer").disabled =
    !usable ||
    !freezeIsCurrent ||
    Boolean(panel && panel.transfer_receipt);
}

function bridgeOutput(bridge, role) {
  if (!bridge || !bridge.outputs) {
    return "";
  }
  const output =
    bridge.outputs[role] ||
    bridge.outputs[role.toLowerCase()] ||
    null;
  if (typeof output === "string") {
    return output;
  }
  if (!output) {
    return "";
  }
  return output.content || output.markdown || output.text || "";
}

function bridgeResultValue(results, name, fallback) {
  if (!results || results[name] == null) {
    return fallback;
  }
  const result = results[name];
  if (typeof result === "string") {
    return result;
  }
  return result.result || result.state || fallback;
}

function renderBridgeIdentities(imports) {
  const target = byId("bridge-identities");
  target.replaceChildren();
  if (!imports || imports.length === 0) {
    const empty = document.createElement("p");
    empty.className = "path-value";
    empty.textContent = "No artifacts imported.";
    target.append(empty);
    return;
  }
  for (const identity of imports) {
    const row = document.createElement("div");
    row.className = "default-row";
    const primary = document.createElement("code");
    const detail = document.createElement("span");
    primary.textContent =
      `${identity.selected_role || "UNKNOWN"} · ` +
      `${identity.artifact_content_hash || identity.artifact_sha256 || "UNKNOWN"}`;
    detail.textContent =
      `${identity.import_mode || "UNKNOWN"} · ` +
      `${identity.source_path_or_label || "UNKNOWN"} · ` +
      `${identity.model_identity?.value || "UNKNOWN"} · ` +
      `${identity.role_identity || "UNKNOWN"} · ` +
      `${identity.artifact_authored_at || "UNKNOWN"} · ` +
      `${identity.authority_state || "UNKNOWN"}`;
    row.append(primary, detail);
    target.append(row);
  }
}

const bridgeActionIds = [
  "bridge-start",
  "bridge-copy",
  "bridge-import-file",
  "bridge-import-paste",
  "bridge-generate-handoff",
  "bridge-freeze-handoff",
  "bridge-generate-receipt",
  "bridge-freeze-receipt",
  "bridge-generate-manifest",
  "bridge-freeze-manifest",
  "bridge-replay-run",
  "bridge-record-reexplanation",
  "bridge-record-intervention",
];

const bridgeInputIds = [
  "bridge-task-id",
  "bridge-protocol-run-id",
  "bridge-objective",
  "bridge-completion-line",
  "bridge-do-not-touch",
  "bridge-current-gate",
  "bridge-authority-boundary",
  "bridge-as-of-commit",
  "bridge-required-next-actor",
  "bridge-evidence-commit",
  "bridge-evidence-path",
  "bridge-evidence-blob",
  "bridge-evidence-sha256",
  "bridge-framework-lens",
  "bridge-framework-layer",
  "bridge-framework-question",
  "bridge-framework-finding",
  "bridge-role",
  "bridge-source",
  "bridge-file",
  "bridge-paste",
  "bridge-metadata",
  "bridge-replay-baseline",
  "bridge-replay-candidate",
];

function resetBridgeDrafts() {
  const defaults = {
    "bridge-task-id": "V13-CMB-001",
    "bridge-protocol-run-id": "V13-PMR-002",
    "bridge-as-of-commit":
      "63eb260a94595298e2b07b476f7f9d8572c9ef09",
    "bridge-required-next-actor": "Fresh SOL / coding-agent Builder",
    "bridge-evidence-commit":
      "970ae5e24e59dada54e1b829229360d9945a0910",
    "bridge-evidence-path":
      "validation/companion_manual_bridge_v0_1_shared_evidence_packet.md",
    "bridge-evidence-blob":
      "92f9f69f18db052b421fa5fa7f233ce77f5a42b8",
    "bridge-evidence-sha256":
      "847c344508763a83d0368f0d1336f07a0022598a9db07078f7dfc99e918f7aab",
    "bridge-metadata": "{}",
    "bridge-replay-baseline": "{}",
    "bridge-replay-candidate": "{}",
  };
  for (const id of bridgeInputIds) {
    byId(id).value = defaults[id] || "";
  }
}

function renderBridge(bridge, repository) {
  const session = bridge && bridge.session ? bridge.session : null;
  const state = bridge ? bridge.state || "BOUNDARY_INCOMPLETE" : "No session";
  setText("bridge-state", state);
  setText(
    "bridge-session-id",
    session
      ? `Session: ${session.session_id || session.id || "UNKNOWN"}`
      : "No session created.",
  );
  renderBridgeIdentities(bridge ? bridge.imports : []);
  setText("bridge-copy-output", bridgeOutput(bridge, "COPY_FOR_PRO"));
  setText(
    "bridge-handoff-output",
    bridgeOutput(bridge, "EXECUTION_HANDOFF"),
  );
  setText("bridge-receipt-output", bridgeOutput(bridge, "BRIDGE_RECEIPT"));
  const manifestText =
    bridgeOutput(bridge, "GOLDEN_MANIFEST") ||
    (bridge && bridge.golden_manifest
      ? JSON.stringify(bridge.golden_manifest, null, 2)
      : "");
  setText("bridge-manifest-output", manifestText);
  setText("bridge-replay-output", bridgeOutput(bridge, "REPLAY_RESULT"));
  setText(
    "bridge-protocol-result",
    bridgeResultValue(
      bridge ? bridge.results : null,
      "protocol",
      "IN PROGRESS / NOT FINAL",
    ),
  );
  setText(
    "bridge-product-result",
    bridgeResultValue(
      bridge ? bridge.results : null,
      "product",
      "BUILDER EVIDENCE ONLY / INDEPENDENT AUDIT REQUIRED",
    ),
  );
  setText(
    "bridge-replay-result",
    bridgeResultValue(
      bridge ? bridge.results : null,
      "replay",
      "NOT YET PERFORMED",
    ),
  );
  const burden = bridge && bridge.burden ? bridge.burden : {};
  const burdenKnown = Object.values(burden).filter(
    (record) =>
      record &&
      typeof record === "object" &&
      record.value_or_unknown !== "UNKNOWN",
  ).length;
  setText(
    "bridge-burden-status",
    session
      ? `${burdenKnown} burden fields currently system-observed or explicitly recorded; unresolved fields remain UNKNOWN.`
      : "Pre-Bridge manual events remain UNKNOWN.",
  );

  const usable = Boolean(connected && repository && bridge && !bridge.error);
  const hasSession = Boolean(usable && session);
  byId("bridge-start").disabled = !usable || hasSession;
  for (const id of bridgeInputIds.slice(0, 18)) {
    byId(id).disabled = !usable || hasSession;
  }
  byId("bridge-copy").disabled =
    !hasSession || state === "BOUNDARY_INCOMPLETE";
  const roleSelected = Boolean(byId("bridge-role").value);
  byId("bridge-role").disabled = !hasSession;
  byId("bridge-source").disabled = !hasSession;
  byId("bridge-file").disabled = !hasSession;
  byId("bridge-paste").disabled = !hasSession;
  byId("bridge-metadata").disabled = !hasSession;
  byId("bridge-import-file").disabled =
    !hasSession || !roleSelected || !byId("bridge-file").files?.length;
  byId("bridge-import-paste").disabled =
    !hasSession ||
    !roleSelected ||
    byId("bridge-paste").value.length === 0;
  byId("bridge-generate-handoff").disabled = !hasSession;
  byId("bridge-freeze-handoff").disabled =
    !hasSession || !bridgeOutput(bridge, "EXECUTION_HANDOFF");
  byId("bridge-generate-receipt").disabled = !hasSession;
  byId("bridge-freeze-receipt").disabled =
    !hasSession || !bridgeOutput(bridge, "BRIDGE_RECEIPT");
  byId("bridge-generate-manifest").disabled = !hasSession;
  byId("bridge-freeze-manifest").disabled =
    !hasSession || !manifestText;
  byId("bridge-replay-baseline").disabled = !hasSession;
  byId("bridge-replay-candidate").disabled = !hasSession;
  byId("bridge-replay-run").disabled = !hasSession;
  byId("bridge-record-reexplanation").disabled = !hasSession;
  byId("bridge-record-intervention").disabled = !hasSession;
}

function renderCreatorLiveCycle006(value) {
  if (!optionalById("creator-live-cycle-006-start")) {
    return;
  }
  const cycle = value && typeof value === "object" ? value : null;
  const binding = cycle?.binding;
  const candidate = binding?.candidate;
  const before = candidate?.common_before;
  const run1 = binding?.tasks?.run_1;
  const run2 = binding?.tasks?.run_2;
  const runtime = binding?.runtime;
  const history = binding?.historical_boundary?.cycle_005;
  const state = cycle?.state || "UNAVAILABLE";
  const formatTask = (task) =>
    task
      ? `${task.utf8_byte_count} bytes · ${task.sha256} · ${task.lane}`
      : "Unavailable";
  setText("creator-live-cycle-006-status", state.replaceAll("_", " "));
  setText(
    "creator-live-cycle-006-candidate",
    cycle?.candidate_id ?? candidate?.candidate_id ?? "Unavailable",
  );
  setText(
    "creator-live-cycle-006-revision",
    binding?.repository?.head ?? "Unavailable",
  );
  setText(
    "creator-live-cycle-006-before",
    before
      ? `${before.utf8_byte_count} bytes · ${before.sha256}`
      : "Unavailable",
  );
  setText("creator-live-cycle-006-run-1", formatTask(run1));
  setText("creator-live-cycle-006-run-2", formatTask(run2));
  setText(
    "creator-live-cycle-006-runtime",
    runtime
      ? `${runtime.provider} · ${runtime.account} · ${runtime.model} · ${runtime.reasoning_effort} · ${runtime.service_tier} · CLI ${runtime.codex_cli_version} · sandbox ${runtime.sandbox} · model network ${runtime.model_sandbox_network} · provider transport ${runtime.provider_transport_required ? "required" : "not required"} · ${runtime.fresh_ephemeral_thread_per_run ? "fresh ephemeral thread per Run" : "thread policy unavailable"} · cwd ${runtime.repository_cwd}`
      : "Unavailable",
  );
  setText(
    "creator-live-cycle-006-attempt-policy",
    `${cycle?.one_attempt === true ? "One attempt" : "Policy unavailable"} · retry ${cycle?.retry_count ?? 0} · replacement ${cycle?.replacement_count ?? 0}`,
  );
  setText(
    "creator-live-cycle-006-history",
    history
      ? `${history.cycle_key} · ${history.state} / ${history.failure_boundary} / ${history.failure_code}`
      : "Unavailable",
  );
  setText(
    "creator-live-cycle-006-behavior",
    cycle?.artifact_behavior ?? "NOT_RUN",
  );
  setText(
    "creator-live-cycle-006-comparison",
    cycle?.comparison_result ?? "NOT_ESTABLISHED",
  );
  setText(
    "creator-live-cycle-006-authorization",
    cycle?.live_start_authorization ?? "ABSENT",
  );
  setText(
    "creator-live-cycle-006-p0",
    cycle?.p0?.ready
      ? "PASS"
      : cycle?.p0?.failure_code || "Unavailable",
  );
  setText(
    "creator-live-cycle-006-binding-sha256",
    cycle?.launch_binding_sha256 ?? "Unavailable",
  );
  const start = byId("creator-live-cycle-006-start");
  const startAllowed =
    cycle?.start_allowed === true &&
    cycle?.live_start_authorization === "PRESENT" &&
    cycle?.storage_occupied === false &&
    state === "READY" &&
    cycle?.p0?.ready === true &&
    typeof cycle?.launch_binding_sha256 === "string";
  start.disabled = !startAllowed;
  byId("creator-live-cycle-006-disabled-label").hidden = startAllowed;
}

function renderCreatorLiveCycle005(value) {
  if (!optionalById("creator-live-start")) {
    return;
  }
  const cycle = value && typeof value === "object" ? value : null;
  const binding = cycle?.binding;
  const identities = cycle?.identities;
  const contract = identities?.contract_identity ?? binding?.contract;
  const runtime = identities?.runtime ?? binding?.runtime;
  const run1 = identities?.run_1_task ?? binding?.tasks?.run_1;
  const run2 = identities?.run_2_task ?? binding?.tasks?.run_2;
  const notDurable = "NOT_DURABLY_PERSISTED";
  const formatTaskIdentity = (task) => {
    if (!task) {
      return "Unavailable";
    }
    if (task.byte_count === notDurable && task.sha256 === notDurable) {
      return notDurable;
    }
    const byteCount =
      task.byte_count === notDurable
        ? notDurable
        : `${task.byte_count} bytes`;
    return `${byteCount} · ${task.sha256}${task.lane ? ` · ${task.lane}` : ""}`;
  };
  const state = cycle?.state || "UNAVAILABLE";
  setText("creator-live-cycle-005-status", state.replaceAll("_", " "));
  setText(
    "creator-live-revision",
    identities?.revision ?? binding?.repository?.head ?? "Unavailable",
  );
  setText(
    "creator-live-contract",
    typeof contract === "string"
      ? contract
      : contract?.source_sha256
        ? `${contract.profile} · ${contract.title} · ${contract.source_byte_count} bytes · ${contract.source_sha256}`
        : "Unavailable",
  );
  setText(
    "creator-live-contract-authority",
    identities?.ordinary_contract_execution_authority ??
      contract?.ordinary_contract_execution_authority ??
      "Unavailable",
  );
  setText(
    "creator-live-freeze-authority",
    identities?.guided_intake_freeze_authority ??
      contract?.guided_intake_freeze_authority_state ??
      "Unavailable",
  );
  setText(
    "creator-live-authorization",
    identities?.cycle_authorization_observed_at ??
      binding?.authorizations?.cycle_observed_at ??
      "Unavailable",
  );
  setText(
    "creator-live-implementation-authorization",
    identities?.implementation_authorization_observed_at ??
      binding?.authorizations?.implementation_observed_at ??
      "Unavailable",
  );
  setText(
    "creator-live-runtime",
    runtime
      ? `${runtime.account_type} · ${runtime.model} · ${runtime.reasoning_effort} · ${runtime.service_tier} · CLI ${runtime.codex_cli_version}`
      : "Unavailable",
  );
  setText(
    "creator-live-run-1",
    formatTaskIdentity(run1),
  );
  setText(
    "creator-live-run-2",
    formatTaskIdentity(run2),
  );
  setText(
    "creator-live-attempt-policy",
    identities
      ? identities.retry_count === notDurable &&
        identities.replacement_count === notDurable
        ? notDurable
        : `${identities.retry_count} retries · ${identities.replacement_count} replacements`
      : cycle
      ? `${cycle.one_attempt_no_retry ? "One attempt · no retry" : "Policy unavailable"} · ${cycle.replacement_permitted ? "replacement permitted" : "no replacement"}`
      : "One attempt · no retry · no replacement",
  );
  const historical =
    identities?.historical_boundary ?? binding?.historical_boundary;
  setText(
    "creator-live-historical-boundary",
    typeof historical === "string"
      ? historical
      : historical
        ? `${historical.cycle_key} · ${historical.state} / ${historical.failure_boundary} / ${historical.failure_code}`
        : "Unavailable",
  );
  setText(
    "creator-live-p0",
    cycle?.p0?.ready
      ? "PASS"
      : cycle?.p0?.failure_code || "Unavailable",
  );
  setText(
    "creator-live-binding-sha256",
    identities?.launch_binding_sha256 ??
      cycle?.launch_binding_sha256 ??
      "Unavailable",
  );
  setText(
    "creator-live-stage",
    identities?.terminal_stage ?? cycle?.stage ?? "P0",
  );
  setText(
    "creator-live-failure-code",
    identities?.failure_code ?? cycle?.failure_code ?? "Unavailable",
  );
  setText(
    "creator-live-proof-attempt",
    identities?.proof_attempt_id ?? "Unavailable",
  );
  setText(
    "creator-live-proof-as-of",
    identities?.proof_as_of ?? "Unavailable",
  );
  setText(
    "creator-live-journal-sha256",
    identities?.journal_sha256 ?? "Unavailable",
  );
  setText(
    "creator-live-anchor-sha256",
    identities?.anchor_sha256 ?? "Unavailable",
  );
  setText(
    "creator-live-readback-sha256",
    identities?.readback_sha256 ?? "Unavailable",
  );
  const artifact = identities?.output_artifact;
  setText(
    "creator-live-output-artifact",
    typeof artifact === "string"
      ? artifact
      : artifact
        ? `${artifact.artifact_id} · ${artifact.byte_count} bytes · ${artifact.sha256}`
        : "Unavailable",
  );
  const compiler = identities?.compiler;
  setText(
    "creator-live-compiler",
    typeof compiler === "string"
      ? compiler
      : compiler
        ? `${compiler.compiler_version} · ${compiler.compiler_branch} · eligible ${compiler.eligible_candidate_count} · winners ${compiler.winning_candidate_count} · ${compiler.terminal_a3_code ?? "PASS"} · ${compiler.audit_sha256}`
        : "Unavailable",
  );
  const start = byId("creator-live-start");
  const terminal = cycle?.storage_occupied === true || [
    "FAILED",
    "TRACE_COMPLETE",
    "PASS",
    "OPEN_UNRESUMABLE",
    "INTEGRITY_FAILURE",
  ].includes(state);
  const startAllowed =
    cycle?.start_allowed === true &&
    state === "READY" &&
    cycle?.p0?.ready === true &&
    typeof cycle?.launch_binding_sha256 === "string";
  start.hidden = terminal;
  start.disabled = !startAllowed;
  byId("creator-live-terminal-label").hidden = !terminal;
}

function render(state) {
  if (!connected) {
    return;
  }
  latestState = state;
  csrfToken = state.csrf || csrfToken;
  const repository = state.repository;
  const repositoryPath = repository ? repository.path : null;
  if (
    bridgeRepositoryPath !== null &&
    repositoryPath !== bridgeRepositoryPath
  ) {
    resetBridgeDrafts();
  }
  if (
    guidedRepositoryPath !== null &&
    repositoryPath !== guidedRepositoryPath
  ) {
    resetGuidedIntakeDrafts();
  }
  bridgeRepositoryPath = repositoryPath;
  guidedRepositoryPath = repositoryPath;
  setText(
    "repository-name",
    repository ? repository.name : "No repository selected",
  );
  setText(
    "repository-path",
    repository ? repository.path : "Select one local Git repository.",
  );
  renderContractImportControls();

  const run =
    state.run && typeof state.run === "object"
      ? state.run
      : { run_type: "bounded_task", state: "idle" };
  const runType = run.run_type || "bounded_task";
  const boundedRun = runType === "bounded_task";
  const boundedRunView = boundedRun
    ? run
    : {
        run_type: "bounded_task",
        task_mode: null,
        state: "idle",
        progress: [],
        result: "",
        file_actions: [],
        read_evidence: [],
        outcomes: null,
        runtime: null,
        receipt_delta: null,
        approval: null,
        error: null,
      };
  const running = boundedRun && run.state === "running";
  const currentTask = taskReadiness(state.ordinary_contract, repository);
  setHidden("bounded-task-card", !boundedRun);
  setHidden("bounded-run-receipt-column", !boundedRun);
  byId("run").disabled =
    !boundedRun ||
    running ||
    !repository ||
    !currentTask.runnable;
  byId("choose-repository").disabled = running;
  byId("task").disabled = !boundedRun || running;

  renderProgress(boundedRunView);
  renderResult(boundedRunView);
  renderApproval(
    operationApprovalResponsePending ? null : boundedRunView.approval,
  );
  coordinateOperationTransition(boundedRunView);
  renderOperationAwareness(
    boundedRunView,
    state.ordinary_contract,
    repository,
  );
  renderDefaults(state.defaults);

  setText(
    "receipt-status",
    state.receipt ? state.receipt.status : "No repository",
  );
  metricRows(byId("run-receipt"), boundedRunView.receipt_delta);
  metricRows(byId("repository-receipt"), state.receipt);
  if (state.receipt) {
    setText("claim-boundary", state.receipt.claim_boundary);
  }
  const persistentTransplant =
    state.intelligence_transplant &&
    typeof state.intelligence_transplant === "object"
      ? state.intelligence_transplant
      : null;
  const transplantView =
    persistentTransplant &&
    (persistentTransplant.run_id ||
      persistentTransplant.error ||
      persistentTransplant.store_state)
      ? persistentTransplant
      : runType === "intelligence_transplant"
        ? run
        : persistentTransplant;
  renderIntelligenceTransplant(transplantView, repository);
  renderOrdinaryContract(state.ordinary_contract, repository);
  renderGuidedIntake(state.guided_intake, repository);
  renderBridge(state.manual_bridge, repository);
  renderCreatorLiveCycle006(state.creator_live_cycle_006);
  renderCreatorLiveCycle005(state.creator_live_cycle_005);
  if (state.creator_live_cycle_005?.state === "RUNNING") {
    disableStateChangingControls();
  }
  if (["PREPARING", "FIXING"].includes(state.ordinary_contract?.state)) {
    byId("contract-file").disabled = true;
    byId("contract-import").disabled = true;
    byId("contract-use-guided-intake").disabled = true;
    for (const id of [...guidedIntakeActionIds, ...guidedIntakeInputIds]) {
      byId(id).disabled = true;
    }
  }
}

function disableStateChangingControls() {
  const creatorLiveCycle006Start = optionalById(
    "creator-live-cycle-006-start",
  );
  if (creatorLiveCycle006Start) {
    creatorLiveCycle006Start.disabled = true;
  }
  const creatorLiveStart = optionalById("creator-live-start");
  if (creatorLiveStart) {
    creatorLiveStart.disabled = true;
  }
  byId("choose-repository").disabled = true;
  byId("ordinary-contract-file").disabled = true;
  byId("ordinary-contract-confirm").disabled = true;
  byId("ordinary-contract-answer-confirm").disabled = true;
  byId("ordinary-contract-answer-reject").disabled = true;
  byId("ordinary-contract-fix").disabled = true;
  byId("ordinary-contract-error-retry").disabled = true;
  byId("ordinary-contract-error-dismiss").disabled = true;
  byId("contract-file").disabled = true;
  byId("contract-import").disabled = true;
  byId("contract-use-guided-intake").disabled = true;
  byId("run").disabled = true;
  byId("new-run").disabled = true;
  byId("task").disabled = true;
  for (const button of document.querySelectorAll("[data-choice]")) {
    button.disabled = true;
  }
  for (const button of byId("defaults").querySelectorAll("button")) {
    button.disabled = true;
  }
  for (const id of [...guidedIntakeActionIds, ...guidedIntakeInputIds]) {
    byId(id).disabled = true;
  }
  for (const id of [...bridgeActionIds, ...bridgeInputIds]) {
    byId(id).disabled = true;
  }
}

function enterDisconnected() {
  connectionGeneration += 1;
  connected = false;
  latestState = null;
  csrfToken = "";
  bridgeRepositoryPath = null;
  guidedRepositoryPath = null;
  contractImportGeneration += 1;
  resetContractImport({ clearFile: true });
  resetBridgeDrafts();
  resetGuidedIntakeDrafts();
  disableStateChangingControls();

  setText("repository-name", "Companion disconnected");
  setText("repository-path", DISCONNECTED_MESSAGE);

  const emptyRun = {
    run_type: "bounded_task",
    task_mode: null,
    state: "idle",
    progress: [],
    result: "",
    file_actions: [],
    read_evidence: [],
    outcomes: null,
    runtime: null,
    receipt_delta: null,
    approval: null,
    error: null,
  };
  renderProgress(emptyRun);
  renderResult(emptyRun);
  setText("run-state", "");
  setText("result-state", "");
  setText("result", "");
  renderApproval(null);
  operationStartPending = false;
  resetOperationTransitionMemory();
  clearPreparedContractTaskBinding();
  renderOperationAwareness(emptyRun, null, null);

  byId("defaults").replaceChildren();
  setText("receipt-status", "Session ended");
  byId("run-receipt").replaceChildren();
  setHidden("bounded-run-receipt-column", false);
  byId("repository-receipt").replaceChildren();
  setText("claim-boundary", "");
  renderIntelligenceTransplant(null, null);
  ordinaryLastRevision = -1;
  ordinaryLastErrorId = null;
  renderOrdinaryContract(null, null);
  renderGuidedIntake(null, null);
  renderBridge(null, null);
  renderCreatorLiveCycle006(null);
  renderCreatorLiveCycle005(null);

  setText("global-error", DISCONNECTED_MESSAGE);
  setHidden("global-error", false);
}

function renderAuthenticatedState(state) {
  connected = true;
  render(state);
  setText("global-error", "");
  setHidden("global-error", true);
}

async function readResponse(response) {
  let body;
  try {
    body = await response.json();
  } catch (_error) {
    throw new CompanionUnavailableError();
  }
  if (!response.ok) {
    if (
      response.status === 401 ||
      response.status === 403 ||
      response.status >= 500
    ) {
      throw new CompanionUnavailableError();
    }
    throw new RequestRejectedError(
      body.error || "The local companion rejected the request.",
    );
  }
  return body;
}

async function getState() {
  const response = await fetch("/api/state", {
    cache: "no-store",
    credentials: "same-origin",
  });
  return readResponse(response);
}

async function postJSON(path, value) {
  if (!connected || requestActive) {
    return null;
  }
  connectionGeneration += 1;
  requestActive = true;
  setHidden("global-error", true);
  try {
    const response = await fetch(path, {
      method: "POST",
      cache: "no-store",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-Decision-OS-CSRF": csrfToken,
      },
      body: JSON.stringify(value),
    });
    const state = await readResponse(response);
    render(state);
    return state;
  } catch (error) {
    if (error instanceof RequestRejectedError) {
      setText("global-error", error.message);
      setHidden("global-error", false);
    } else {
      enterDisconnected();
    }
    return null;
  } finally {
    requestActive = false;
  }
}

async function postOrdinaryJSON(path, value) {
  if (!connected || requestActive) {
    return null;
  }
  connectionGeneration += 1;
  requestActive = true;
  disableStateChangingControls();
  try {
    const response = await fetch(path, {
      method: "POST",
      cache: "no-store",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-Decision-OS-CSRF": csrfToken,
      },
      body: JSON.stringify(value),
    });
    let body;
    try {
      body = await response.json();
    } catch (_error) {
      throw new CompanionUnavailableError();
    }
    if (!response.ok) {
      if (body?.ordinary_contract && latestState) {
        latestState = { ...latestState, ordinary_contract: body.ordinary_contract };
        renderOrdinaryContract(body.ordinary_contract, latestState.repository);
      }
      if (!body?.error || typeof body.error !== "object") {
        throw new CompanionUnavailableError();
      }
      return null;
    }
    render(body);
    return body;
  } catch (_error) {
    enterDisconnected();
    return null;
  } finally {
    requestActive = false;
    if (latestState) {
      render(latestState);
    }
  }
}

function ordinaryBytesToBase64(bytes) {
  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + chunkSize));
  }
  return btoa(binary);
}

async function ordinarySha256(bytes) {
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (value) =>
    value.toString(16).padStart(2, "0"),
  ).join("");
}

function ordinaryFixRequest() {
  const panel = latestState?.ordinary_contract;
  const source = panel?.source_identity;
  const details = panel?.technical_details;
  if (!panel?.preparation_id || !source || !details) {
    return null;
  }
  return {
    preparation_id: panel.preparation_id,
    expected_repository_identity: panel.repository_identity,
    expected_source_sha256: source.sha256,
    expected_request_id: details.request_id,
    expected_draft_id: details.draft_id,
    expected_interpretation_sha256: details.interpretation_sha256,
    idempotency_key: crypto.randomUUID(),
  };
}

byId("ordinary-contract-file").addEventListener("change", async () => {
  const file = byId("ordinary-contract-file").files?.[0] || null;
  const panel = latestState?.ordinary_contract;
  if (file) {
    recordOrdinarySelectedFilename(file.name, panel?.operation_revision);
  }
  if (!file || !panel || !latestState?.repository) {
    return;
  }
  if (typeof file.arrayBuffer !== "function") {
    setText("ordinary-contract-status", "Cannot be fixed safely");
    setText("ordinary-contract-progress", "The Contract could not be read locally.");
    return;
  }
  ordinaryFocusIntent = "prepare";
  setText("ordinary-contract-status", "Preparing…");
  setText(
    "ordinary-contract-progress",
    "Reading exact bytes and checking the Contract safely.",
  );
  byId("ordinary-contract-file").disabled = true;
  let bytes;
  let sourceBase64 = "";
  try {
    if (Number(file.size) > MAX_ORDINARY_CONTRACT_BYTES) {
      await postOrdinaryJSON("/api/ordinary-contract/prepare", {
        filename: file.name,
        source_base64: "",
        source_byte_size: Number(file.size),
        source_sha256: EMPTY_SHA256,
        expected_repository_identity: panel.repository_identity,
        expected_active_request_id:
          panel.technical_details?.active_request_id ?? null,
        idempotency_key: crypto.randomUUID(),
      });
      return;
    }
    bytes = new Uint8Array(await file.arrayBuffer());
    const sourceSha256 = await ordinarySha256(bytes);
    sourceBase64 = ordinaryBytesToBase64(bytes);
    await postOrdinaryJSON("/api/ordinary-contract/prepare", {
      filename: file.name,
      source_base64: sourceBase64,
      source_byte_size: bytes.byteLength,
      source_sha256: sourceSha256,
      expected_repository_identity: panel.repository_identity,
      expected_active_request_id:
        panel.technical_details?.active_request_id ?? null,
      idempotency_key: crypto.randomUUID(),
    });
  } catch (_error) {
    enterDisconnected();
  } finally {
    bytes?.fill(0);
    sourceBase64 = "";
    byId("ordinary-contract-file").value = "";
  }
});

for (const id of [
  "ordinary-contract-answer-confirm",
  "ordinary-contract-answer-reject",
]) {
  byId(id).addEventListener("input", () => {
    if (latestState) {
      renderOrdinaryContract(
        latestState.ordinary_contract,
        latestState.repository,
      );
    }
  });
}

byId("ordinary-contract-confirm").addEventListener("click", async () => {
  const panel = latestState?.ordinary_contract;
  const answer = byId("ordinary-contract-answer-confirm").checked
    ? "CONFIRM"
    : byId("ordinary-contract-answer-reject").checked
      ? "REJECT"
      : null;
  if (!panel?.clarification || !answer) {
    return;
  }
  ordinaryFocusIntent = "prepare";
  await postOrdinaryJSON("/api/ordinary-contract/confirm", {
    preparation_id: panel.preparation_id,
    clarification_id: panel.clarification.clarification_id,
    answer,
    expected_interpretation_sha256:
      panel.technical_details.interpretation_sha256,
    idempotency_key: crypto.randomUUID(),
  });
});

byId("ordinary-contract-fix").addEventListener("click", async () => {
  const request = ordinaryFixRequest();
  if (!request) {
    return;
  }
  ordinaryFocusIntent = "fix";
  setText("ordinary-contract-status", "Fixing…");
  setText(
    "ordinary-contract-progress",
    "Rechecking the reviewed Contract and preserving its receipt.",
  );
  byId("ordinary-contract-fix").disabled = true;
  await postOrdinaryJSON("/api/ordinary-contract/fix", request);
});

byId("ordinary-contract-error-retry").addEventListener("click", async () => {
  const request = ordinaryFixRequest();
  if (!request) {
    return;
  }
  ordinaryFocusIntent = "fix";
  await postOrdinaryJSON("/api/ordinary-contract/fix", request);
});

byId("ordinary-contract-error-dismiss").addEventListener("click", async () => {
  const error = latestState?.ordinary_contract?.action_error;
  if (!error?.error_id) {
    return;
  }
  await postOrdinaryJSON("/api/ordinary-contract/error/dismiss", {
    error_id: error.error_id,
    idempotency_key: crypto.randomUUID(),
  });
});

function contractFileSelectionChanged() {
  contractImportGeneration += 1;
  resetContractImport();
  renderContractImportControls();
}

byId("contract-file").addEventListener("input", contractFileSelectionChanged);
byId("contract-file").addEventListener("change", contractFileSelectionChanged);

byId("contract-import").addEventListener("click", async () => {
  const file = selectedContractFile();
  const generation = ++contractImportGeneration;
  if (!file) {
    showContractImportError("Choose one Product Contract file first.");
    return;
  }
  if (!supportedContractFile(file)) {
    showContractImportError(
      "Only .md and .txt Product Contract files are supported.",
    );
    return;
  }
  if (typeof file.text !== "function") {
    showContractImportError("The Product Contract could not be read locally.");
    return;
  }

  let content;
  try {
    content = await file.text();
  } catch (_error) {
    if (
      !connected ||
      generation !== contractImportGeneration ||
      selectedContractFile() !== file
    ) {
      return;
    }
    showContractImportError("The Product Contract could not be read locally.");
    return;
  }
  if (
    !connected ||
    generation !== contractImportGeneration ||
    selectedContractFile() !== file
  ) {
    return;
  }
  if (typeof content !== "string") {
    showContractImportError("The Product Contract could not be read locally.");
    return;
  }

  importedContract = { filename: file.name, content };
  byId("contract-full-content").value = importedContract.content;
  setText("contract-import-state", "Imported locally");
  setText("contract-file-name", importedContract.filename);
  setText(
    "contract-preview-status",
    content.length > CONTRACT_PREVIEW_CHARACTERS
      ? `Showing first ${CONTRACT_PREVIEW_CHARACTERS} of ${content.length} characters. Full content is retained locally.`
      : `Showing all ${content.length} characters. Full content is retained locally.`,
  );
  setText(
    "contract-preview",
    content.slice(0, CONTRACT_PREVIEW_CHARACTERS),
  );
  setHidden("contract-preview", false);
  setText("contract-import-error", "");
  setHidden("contract-import-error", true);
  renderContractImportControls();
});

byId("contract-use-guided-intake").addEventListener("click", () => {
  if (!connected || importedContract === null) {
    return;
  }
  const originalRequestInput = byId("guided-intake-original-request");
  originalRequestInput.value = importedContract.content;
  guidedTransferredOriginalRequest = {
    content: importedContract.content,
    displayedValue: originalRequestInput.value,
  };
  guidedInputError = "";
  if (latestState) {
    renderGuidedIntake(latestState.guided_intake, latestState.repository);
  }
  byId("guided-intake-card").scrollIntoView?.({ block: "start" });
  originalRequestInput.focus();
});

const operationStageButtons = Array.from(
  document.querySelectorAll("[data-operation-stage]"),
);
for (const [index, button] of operationStageButtons.entries()) {
  button.addEventListener("click", () => {
    moveToOperationStage(button.dataset.operationStage);
  });
  button.addEventListener("keydown", (event) => {
    const lastIndex = operationStageButtons.length - 1;
    let targetIndex = null;
    if (["ArrowRight", "ArrowDown"].includes(event.key)) {
      targetIndex = Math.min(index + 1, lastIndex);
    } else if (["ArrowLeft", "ArrowUp"].includes(event.key)) {
      targetIndex = Math.max(index - 1, 0);
    } else if (event.key === "Home") {
      targetIndex = 0;
    } else if (event.key === "End") {
      targetIndex = lastIndex;
    }
    if (targetIndex !== null) {
      event.preventDefault();
      operationStageButtons[targetIndex].focus();
    }
  });
}

byId("task").addEventListener("input", () => {
  invalidateReplacedContractTask(byId("task").value);
  if (connected && latestState) {
    render(latestState);
  }
});

byId("choose-repository").addEventListener("click", async () => {
  await postJSON("/api/repository/pick", {});
});

byId("run").addEventListener("click", async () => {
  const currentTask = taskReadiness(
    latestState?.ordinary_contract,
    latestState?.repository,
  );
  if (byId("run").disabled || requestActive || !currentTask.runnable) {
    return;
  }
  beginOperationRun(currentTask.mode);
  const state = await postJSON("/api/run", {
    task: byId("task").value,
    task_mode: currentTask.mode,
  });
  operationStartPending = false;
  if (state) {
    render(state);
  } else if (latestState) {
    render(latestState);
  }
});

optionalById("creator-live-start")?.addEventListener("click", async () => {
  const cycle = latestState?.creator_live_cycle_005;
  const digest = cycle?.launch_binding_sha256;
  if (
    byId("creator-live-start").disabled ||
    requestActive ||
    cycle?.storage_occupied !== false ||
    cycle?.start_allowed !== true ||
    cycle?.state !== "READY" ||
    typeof digest !== "string"
  ) {
    return;
  }
  const state = await postJSON("/api/creator-live/cycles/005/start", {
    launch_binding_sha256: digest,
  });
  if (state) {
    render(state);
  }
});

optionalById("creator-live-cycle-006-start")?.addEventListener(
  "click",
  async () => {
    const cycle = latestState?.creator_live_cycle_006;
    const digest = cycle?.launch_binding_sha256;
    if (
      byId("creator-live-cycle-006-start").disabled ||
      requestActive ||
      cycle?.live_start_authorization !== "PRESENT" ||
      cycle?.storage_occupied !== false ||
      cycle?.start_allowed !== true ||
      cycle?.state !== "READY" ||
      cycle?.p0?.ready !== true ||
      typeof digest !== "string"
    ) {
      return;
    }
    const state = await postJSON("/api/creator-live/cycles/006/start", {
      launch_binding_sha256: digest,
    });
    if (state) {
      render(state);
    }
  },
);

byId("new-run").addEventListener("click", async () => {
  const state = await postJSON("/api/new-run", {});
  if (state) {
    operationStartPending = false;
    resetOperationTransitionMemory();
    byId("task").value = "";
    clearPreparedContractTaskBinding();
    render(state);
    byId("task").focus();
  }
});

byId("copy-response").addEventListener("click", async () => {
  const response = currentCodexResponse;
  if (byId("copy-response").disabled || response.length === 0) {
    return;
  }
  try {
    await writeClipboardText(response);
    setText("copy-response", "Copied");
    setText("copy-response-status", "Codex response copied.");
    if (copyResponseResetTimer !== null) {
      window.clearTimeout?.(copyResponseResetTimer);
    }
    copyResponseResetTimer = window.setTimeout(() => {
      if (currentCodexResponse === response) {
        setText("copy-response", "Copy response");
        setText("copy-response-status", "");
      }
      copyResponseResetTimer = null;
    }, 1600);
  } catch (_error) {
    if (copyResponseResetTimer !== null) {
      window.clearTimeout?.(copyResponseResetTimer);
      copyResponseResetTimer = null;
    }
    setText("copy-response", "Copy failed");
    setText("copy-response-status", "Codex response could not be copied.");
  }
});

for (const button of document.querySelectorAll("[data-choice]")) {
  button.addEventListener("click", async () => {
    if (button.disabled || requestActive) {
      return;
    }
    operationApprovalResponsePending = true;
    operationApprovalSeen = true;
    operationApprovalWasVisible = false;
    operationContinuingAfterApproval = true;
    renderApproval(null);
    renderOperationAwareness(
      { ...latestState.run, approval: null },
      latestState.ordinary_contract,
      latestState.repository,
    );
    moveToOperationStage("run");
    const state = await postJSON("/api/approval", {
      choice: button.dataset.choice,
    });
    if (!state) {
      operationApprovalResponsePending = false;
      operationContinuingAfterApproval = false;
      if (latestState) {
        render(latestState);
      }
    }
  });
}

function guidedJSONObject(id, label) {
  let value;
  try {
    value = JSON.parse(byId(id).value.trim() || "{}");
  } catch (_error) {
    throw new RequestRejectedError(`${label} must be a strict JSON object.`);
  }
  if (!value || Array.isArray(value) || typeof value !== "object") {
    throw new RequestRejectedError(`${label} must be a strict JSON object.`);
  }
  return value;
}

function showGuidedInputError(error) {
  guidedInputError =
    error instanceof RequestRejectedError
      ? error.message
      : "The Guided Intake input could not be prepared safely.";
  if (connected && latestState) {
    renderGuidedIntake(latestState.guided_intake, latestState.repository);
  }
}

function clearGuidedInputError() {
  guidedInputError = "";
  if (connected && latestState) {
    renderGuidedIntake(latestState.guided_intake, latestState.repository);
  }
}

byId("guided-intake-capture").addEventListener("click", async () => {
  const displayedOriginalRequest = byId(
    "guided-intake-original-request",
  ).value;
  const originalRequest =
    guidedTransferredOriginalRequest !== null &&
    displayedOriginalRequest ===
      guidedTransferredOriginalRequest.displayedValue
      ? guidedTransferredOriginalRequest.content
      : displayedOriginalRequest;
  if (originalRequest.trim().length === 0) {
    showGuidedInputError(
      new RequestRejectedError("Original Request must not be empty."),
    );
    return;
  }
  clearGuidedInputError();
  const value = { original_request: originalRequest };
  const identity = latestState?.guided_intake?.request_identity;
  const supersedesRequestId =
    identity && typeof identity === "object"
      ? identity.request_id || identity.id || null
      : null;
  if (supersedesRequestId) {
    value.supersedes_request_id = supersedesRequestId;
  }
  await postJSON("/api/guided-intake/capture", value);
});

byId("guided-intake-copy").addEventListener("click", async () => {
  clearGuidedInputError();
  const state = await postJSON("/api/guided-intake/copy", {});
  if (!state) {
    return;
  }
  const text = state.guided_intake?.copy_for_pro_prompt || "";
  if (text && globalThis.navigator?.clipboard?.writeText) {
    try {
      await globalThis.navigator.clipboard.writeText(text);
    } catch (_error) {
      showGuidedInputError(
        new RequestRejectedError(
          "Copy for Pro was generated, but clipboard access was unavailable.",
        ),
      );
    }
  }
});

byId("guided-intake-import-draft").addEventListener("click", async () => {
  try {
    const draftText = byId("guided-intake-draft-json").value;
    guidedJSONObject(
      "guided-intake-draft-json",
      "Guided Intake draft",
    );
    const producerLabel = byId("guided-intake-producer-label").value.trim();
    if (!producerLabel) {
      throw new RequestRejectedError("Producer label must not be empty.");
    }
    clearGuidedInputError();
    await postJSON("/api/guided-intake/import-draft", {
      draft_json: draftText,
      producer_label: producerLabel,
    });
  } catch (error) {
    showGuidedInputError(error);
  }
});

byId("guided-intake-confirm").addEventListener("click", async () => {
  try {
    const activeQuestion = latestState?.guided_intake?.active_question;
    if (!activeQuestion || !activeQuestion.question) {
      throw new RequestRejectedError(
        "There is no active Guided Intake question.",
      );
    }
    const answer = byId("guided-intake-answer").value;
    if (!answer.trim()) {
      throw new RequestRejectedError("Answer must not be empty.");
    }
    const resultingDelta = guidedJSONObject(
      "guided-intake-resulting-delta",
      "Resulting delta",
    );
    clearGuidedInputError();
    const state = await postJSON("/api/guided-intake/confirm", {
      question: activeQuestion.question,
      answer,
      resulting_delta: resultingDelta,
    });
    if (state) {
      byId("guided-intake-answer").value = "";
      byId("guided-intake-resulting-delta").value = "{}";
      renderGuidedIntake(state.guided_intake, state.repository);
    }
  } catch (error) {
    showGuidedInputError(error);
  }
});

byId("guided-intake-freeze").addEventListener("click", async () => {
  clearGuidedInputError();
  await postJSON("/api/guided-intake/freeze", {});
});

byId("guided-intake-purge").addEventListener("click", async () => {
  try {
    const identity = latestState?.guided_intake?.request_identity;
    if (
      !identity ||
      typeof identity !== "object" ||
      !identity.request_id ||
      !identity.sha256
    ) {
      throw new RequestRejectedError(
        "There is no current Original Request identity to purge.",
      );
    }
    if (
      !byId("guided-intake-purge-confirm").checked ||
      guidedPurgeConfirmationIdentity !==
        guidedRequestIdentityKey(latestState.guided_intake)
    ) {
      throw new RequestRejectedError(
        "Explicit Original Request purge confirmation is required.",
      );
    }
    clearGuidedInputError();
    const state = await postJSON("/api/guided-intake/purge", {
      request_id: identity.request_id,
      request_sha256: identity.sha256,
      confirmed: true,
    });
    if (state) {
      guidedTransferredOriginalRequest = null;
      byId("guided-intake-purge-confirm").checked = false;
      guidedPurgeConfirmationIdentity = null;
      renderGuidedIntake(state.guided_intake, state.repository);
    }
  } catch (error) {
    showGuidedInputError(error);
  }
});

byId("guided-intake-transfer").addEventListener("click", async () => {
  clearGuidedInputError();
  await postJSON("/api/guided-intake/transfer-to-bridge", {});
});

for (const id of guidedIntakeInputIds) {
  byId(id).addEventListener("input", () => {
    if (id === "guided-intake-original-request") {
      guidedTransferredOriginalRequest = null;
    }
    if (id === "guided-intake-purge-confirm") {
      guidedPurgeConfirmationIdentity = byId(id).checked
        ? guidedRequestIdentityKey(latestState?.guided_intake)
        : null;
    }
    guidedInputError = "";
    if (connected && latestState) {
      renderGuidedIntake(latestState.guided_intake, latestState.repository);
    }
  });
}

function bridgeMetadata() {
  const raw = byId("bridge-metadata").value.trim() || "{}";
  let value;
  try {
    value = JSON.parse(raw);
  } catch (_error) {
    throw new RequestRejectedError(
      "Explicit Bridge metadata must be a JSON object.",
    );
  }
  if (!value || Array.isArray(value) || typeof value !== "object") {
    throw new RequestRejectedError(
      "Explicit Bridge metadata must be a JSON object.",
    );
  }
  return value;
}

function replayObject(id, label) {
  let value;
  try {
    value = JSON.parse(byId(id).value.trim() || "{}");
  } catch (_error) {
    throw new RequestRejectedError(`${label} must be a JSON object.`);
  }
  if (!value || Array.isArray(value) || typeof value !== "object") {
    throw new RequestRejectedError(`${label} must be a JSON object.`);
  }
  return value;
}

function showBridgeInputError(error) {
  setText(
    "global-error",
    error instanceof RequestRejectedError
      ? error.message
      : "The Manual Bridge input could not be prepared safely.",
  );
  setHidden("global-error", false);
}

byId("bridge-start").addEventListener("click", async () => {
  const optional = (id) => byId(id).value.trim() || "UNKNOWN";
  await postJSON("/api/bridge/session", {
    boundary: {
      task_id: optional("bridge-task-id"),
      protocol_run_id: optional("bridge-protocol-run-id"),
      objective: optional("bridge-objective"),
      completion_line: optional("bridge-completion-line"),
      do_not_touch: optional("bridge-do-not-touch"),
      current_gate: optional("bridge-current-gate"),
      authority_boundary: optional("bridge-authority-boundary"),
      as_of_commit: optional("bridge-as-of-commit"),
      required_next_actor: optional("bridge-required-next-actor"),
      evidence_packet_identity: {
        commit: optional("bridge-evidence-commit"),
        path: optional("bridge-evidence-path"),
        blob_sha: optional("bridge-evidence-blob"),
        sha256: optional("bridge-evidence-sha256"),
        product_as_of_commit: optional("bridge-as-of-commit"),
      },
      framework_lens_used: optional("bridge-framework-lens"),
      relevant_decision_os_layer: optional("bridge-framework-layer"),
      reinterpretation_question: optional("bridge-framework-question"),
      framework_derived_finding: optional("bridge-framework-finding"),
    },
  });
});

byId("bridge-copy").addEventListener("click", async () => {
  const state = await postJSON("/api/bridge/copy", {});
  if (state) {
    const text = bridgeOutput(state.manual_bridge, "COPY_FOR_PRO");
    if (text && globalThis.navigator?.clipboard?.writeText) {
      try {
        await globalThis.navigator.clipboard.writeText(text);
      } catch (_error) {
        setText(
          "global-error",
          "Copy for Pro was generated, but clipboard access was unavailable.",
        );
        setHidden("global-error", false);
      }
    }
  }
});

byId("bridge-import-file").addEventListener("click", async () => {
  try {
    const file = byId("bridge-file").files?.[0];
    if (!file) {
      throw new RequestRejectedError("Choose one artifact file first.");
    }
    if (
      typeof file.size !== "number" ||
      file.size < 0 ||
      file.size > MAX_BRIDGE_ARTIFACT_BYTES
    ) {
      throw new RequestRejectedError(
        "Artifact exceeds the 1 MiB Manual Bridge limit.",
      );
    }
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = "";
    for (let offset = 0; offset < bytes.length; offset += 0x8000) {
      binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
    }
    await postJSON("/api/bridge/import", {
      mode: "BYTE_EXACT_FILE_IMPORT",
      selected_role: byId("bridge-role").value,
      source_path_or_label: byId("bridge-source").value.trim() || file.name,
      payload_base64: globalThis.btoa(binary),
      metadata: bridgeMetadata(),
    });
  } catch (error) {
    showBridgeInputError(error);
  }
});

byId("bridge-import-paste").addEventListener("click", async () => {
  try {
    await postJSON("/api/bridge/import", {
      mode: "PASTE_CAPTURE",
      selected_role: byId("bridge-role").value,
      source_path_or_label:
        byId("bridge-source").value.trim() || "Manual paste capture",
      payload_text: byId("bridge-paste").value,
      metadata: bridgeMetadata(),
    });
  } catch (error) {
    showBridgeInputError(error);
  }
});

byId("bridge-generate-handoff").addEventListener("click", async () => {
  await postJSON("/api/bridge/handoff/generate", {});
});

byId("bridge-freeze-handoff").addEventListener("click", async () => {
  await postJSON("/api/bridge/output/freeze", { role: "EXECUTION_HANDOFF" });
});

byId("bridge-generate-receipt").addEventListener("click", async () => {
  await postJSON("/api/bridge/receipt/generate", {});
});

byId("bridge-freeze-receipt").addEventListener("click", async () => {
  await postJSON("/api/bridge/output/freeze", { role: "BRIDGE_RECEIPT" });
});

byId("bridge-generate-manifest").addEventListener("click", async () => {
  await postJSON("/api/bridge/manifest/generate", {});
});

byId("bridge-freeze-manifest").addEventListener("click", async () => {
  await postJSON("/api/bridge/output/freeze", { role: "GOLDEN_MANIFEST" });
});

byId("bridge-replay-run").addEventListener("click", async () => {
  try {
    await postJSON("/api/bridge/replay", {
      baseline: replayObject(
        "bridge-replay-baseline",
        "Replay baseline",
      ),
      candidate: replayObject(
        "bridge-replay-candidate",
        "Replay candidate",
      ),
    });
  } catch (error) {
    showBridgeInputError(error);
  }
});

byId("bridge-record-reexplanation").addEventListener("click", async () => {
  await postJSON("/api/bridge/observation", {
    field: "shin_re_explanation_count",
    value: 1,
    unit: "count",
    method: "EXPLICIT_ONE_CLICK_INCREMENT",
  });
});

byId("bridge-record-intervention").addEventListener("click", async () => {
  await postJSON("/api/bridge/observation", {
    field: "shin_operational_intervention_count",
    value: 1,
    unit: "count",
    method: "EXPLICIT_ONE_CLICK_INCREMENT",
  });
});

for (const id of [
  "bridge-role",
  "bridge-file",
  "bridge-paste",
]) {
  byId(id).addEventListener("input", () => {
    if (connected && latestState) {
      render(latestState);
    }
  });
}

function syncAdvancedAuditContainment() {
  byId("advanced-audit-content").inert = !byId("advanced-audit-mode").open;
}

function syncResearchWorkflowContainment() {
  byId("advanced-research-content").inert =
    !byId("advanced-research-mode").open;
}

function syncContractWorkflowContainment() {
  byId("advanced-contract-content").inert =
    !byId("advanced-contract-mode").open;
}

byId("advanced-audit-mode").addEventListener(
  "toggle",
  syncAdvancedAuditContainment,
);
byId("advanced-research-mode").addEventListener(
  "toggle",
  syncResearchWorkflowContainment,
);
byId("advanced-contract-mode").addEventListener(
  "toggle",
  syncContractWorkflowContainment,
);
syncAdvancedAuditContainment();
syncResearchWorkflowContainment();
syncContractWorkflowContainment();

async function refresh() {
  if (!requestActive) {
    const generation = connectionGeneration;
    try {
      const state = await getState();
      if (generation === connectionGeneration) {
        renderAuthenticatedState(state);
      }
    } catch (_error) {
      if (generation === connectionGeneration) {
        enterDisconnected();
      }
    }
  }
  window.setTimeout(refresh, 750);
}

disableStateChangingControls();
refresh();
