"use strict";

let csrfToken = "";
let latestState = null;
let requestActive = false;

const byId = (id) => document.getElementById(id);

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
  setHidden("approval-overlay", !approval);
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

function render(state) {
  latestState = state;
  csrfToken = state.csrf || csrfToken;
  const repository = state.repository;
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
}

async function readResponse(response) {
  let body;
  try {
    body = await response.json();
  } catch (_error) {
    throw new Error("The local companion returned an invalid response.");
  }
  if (!response.ok) {
    throw new Error(body.error || "The local companion rejected the request.");
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
  if (requestActive) {
    return null;
  }
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
    setText(
      "global-error",
      error instanceof Error ? error.message : "The local request failed.",
    );
    setHidden("global-error", false);
    return null;
  } finally {
    requestActive = false;
  }
}

byId("task").addEventListener("input", () => {
  if (latestState) {
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

async function refresh() {
  if (!requestActive) {
    try {
      render(await getState());
      setHidden("global-error", true);
    } catch (error) {
      setText(
        "global-error",
        error instanceof Error ? error.message : "The local companion is unavailable.",
      );
      setHidden("global-error", false);
    }
  }
  window.setTimeout(refresh, 750);
}

refresh();
