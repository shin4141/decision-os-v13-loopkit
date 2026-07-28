"use strict";

const DISCONNECTED_MESSAGE =
  "This companion session has ended. Close this tab and relaunch Decision OS Companion.app.";

let csrfToken = "";
let latestState = null;
let requestActive = false;
let connected = false;
let connectionGeneration = 0;
let bridgeRepositoryPath = null;

const MAX_BRIDGE_ARTIFACT_BYTES = 1024 * 1024;

const byId = (id) => document.getElementById(id);

class CompanionUnavailableError extends Error {}

class RequestRejectedError extends Error {}

function setText(id, value) {
  byId(id).textContent = value == null ? "" : String(value);
}

function setHidden(id, hidden) {
  byId(id).classList.toggle("hidden", hidden);
}

function statusLabel(state) {
  return {
    idle: "Idle",
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
  bridgeRepositoryPath = repositoryPath;
  setText(
    "repository-name",
    repository ? repository.name : "No repository selected",
  );
  setText(
    "repository-path",
    repository ? repository.path : "Select one local Git repository.",
  );

  const running = state.run.state === "running";
  byId("run").disabled =
    running || !repository || byId("task").value.trim().length === 0;
  byId("choose-repository").disabled = running;
  byId("task").disabled = running;

  renderProgress(state.run);
  renderResult(state.run);
  renderApproval(state.run.approval);
  renderDefaults(state.defaults);

  setText(
    "receipt-status",
    state.receipt ? state.receipt.status : "No repository",
  );
  metricRows(byId("run-receipt"), state.run.receipt_delta);
  metricRows(byId("repository-receipt"), state.receipt);
  if (state.receipt) {
    setText("claim-boundary", state.receipt.claim_boundary);
  }
  renderBridge(state.manual_bridge, repository);
}

function disableStateChangingControls() {
  byId("choose-repository").disabled = true;
  byId("run").disabled = true;
  byId("new-run").disabled = true;
  byId("task").disabled = true;
  for (const button of document.querySelectorAll("[data-choice]")) {
    button.disabled = true;
  }
  for (const button of byId("defaults").querySelectorAll("button")) {
    button.disabled = true;
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
  resetBridgeDrafts();
  disableStateChangingControls();

  setText("repository-name", "Companion disconnected");
  setText("repository-path", DISCONNECTED_MESSAGE);

  const emptyRun = {
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
  byId("repository-receipt").replaceChildren();
  setText("claim-boundary", "");
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
