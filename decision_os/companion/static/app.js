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

const MAX_BRIDGE_ARTIFACT_BYTES = 1024 * 1024;
const CONTRACT_PREVIEW_CHARACTERS = 4096;
const CONTRACT_EXTENSIONS = [".md", ".txt"];
const GUIDED_INTAKE_AUTHORITY_CLAIM =
  "INTERPRETATION ONLY — NO EXECUTION AUTHORITY";
const MANUAL_OWNER_AUTHORITY = "MANUAL OWNER ATTESTED";
const CRYPTOGRAPHIC_PROVENANCE_NOT_ESTABLISHED = "NOT ESTABLISHED";

const byId = (id) => document.getElementById(id);

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

function renderResult(run) {
  const terminal = ["completed", "denied", "unsupported", "needs_attention"].includes(
    run.state,
  );
  setHidden("result-card", !terminal);
  byId("new-run").disabled = !terminal;
  setText("result-state", statusLabel(run.state));
  setText(
    "result",
    run.result ||
      (run.state === "completed"
        ? "The bounded Run completed without a final text response."
        : run.error || "No final result was available."),
  );
  renderActions(run.file_actions);
  renderRuntime(run.runtime);
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
        state: "idle",
        progress: [],
        result: "",
        file_actions: [],
        runtime: null,
        receipt_delta: null,
        approval: null,
        error: null,
      };
  const running = boundedRun && run.state === "running";
  setHidden("bounded-task-card", !boundedRun);
  setHidden("bounded-run-receipt-column", !boundedRun);
  byId("run").disabled =
    !boundedRun ||
    running ||
    !repository ||
    byId("task").value.trim().length === 0;
  byId("choose-repository").disabled = running;
  byId("task").disabled = !boundedRun || running;

  renderProgress(boundedRunView);
  renderResult(boundedRunView);
  renderApproval(boundedRunView.approval);
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
  renderGuidedIntake(state.guided_intake, repository);
  renderBridge(state.manual_bridge, repository);
}

function disableStateChangingControls() {
  byId("choose-repository").disabled = true;
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
    state: "idle",
    progress: [],
    result: "",
    file_actions: [],
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

  byId("defaults").replaceChildren();
  setText("receipt-status", "Session ended");
  byId("run-receipt").replaceChildren();
  setHidden("bounded-run-receipt-column", false);
  byId("repository-receipt").replaceChildren();
  setText("claim-boundary", "");
  renderIntelligenceTransplant(null, null);
  renderGuidedIntake(null, null);
  renderBridge(null, null);

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

byId("task").addEventListener("input", () => {
  if (connected && latestState) {
    render(latestState);
  }
});

byId("choose-repository").addEventListener("click", async () => {
  await postJSON("/api/repository/pick", {});
});

byId("run").addEventListener("click", async () => {
  await postJSON("/api/run", { task: byId("task").value });
});

byId("new-run").addEventListener("click", async () => {
  const state = await postJSON("/api/new-run", {});
  if (state) {
    byId("task").value = "";
    render(state);
    byId("task").focus();
  }
});

for (const button of document.querySelectorAll("[data-choice]")) {
  button.addEventListener("click", async () => {
    await postJSON("/api/approval", { choice: button.dataset.choice });
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
