(() => {
  "use strict";

  const root = document.createElement("section");
  root.id = "field-notes-lite";
  root.hidden = true;
  document.body.appendChild(root);

  let csrf = "";
  let lastSignature = "";
  let actionPending = false;
  const reconnectFields = [
    "state",
    "selected_field_note_path",
    "selected_full_note_sha256",
    "full_notes_injected",
    "failure_reason",
    "metadata_entries_seen",
    "metadata_files_valid",
    "metadata_bytes_read",
    "full_note_bytes_read",
    "ordinary_distinct_paths_consumed",
    "run_id",
  ];

  function clear() {
    while (root.firstChild) root.removeChild(root.firstChild);
  }

  function text(tag, value, className) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = value;
    return node;
  }

  function button(label, action) {
    const node = document.createElement("button");
    node.type = "button";
    node.textContent = label;
    node.addEventListener("click", action);
    return node;
  }

  async function post(path, payload = {}) {
    const response = await fetch(path, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-Decision-OS-CSRF": csrf,
      },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!response.ok) {
      throw new Error(body.error || "Field Notes action failed.");
    }
    render(body);
  }

  function primaryAction(path, payload, primary, secondary, pendingLabel) {
    if (actionPending) return;
    actionPending = true;
    const originalLabel = primary.textContent;
    primary.disabled = true;
    secondary.disabled = true;
    primary.textContent = pendingLabel;
    root.setAttribute("aria-busy", "true");
    post(path, payload).catch((error) => {
      actionPending = false;
      primary.disabled = false;
      secondary.disabled = false;
      primary.textContent = originalLabel;
      root.removeAttribute("aria-busy");
      showError(error);
    });
  }

  function guardedPost(path, payload = {}) {
    if (actionPending) return;
    post(path, payload).catch(showError);
  }

  function showError(error) {
    let node = root.querySelector(".field-note-error");
    if (!node) {
      node = text("p", "", "field-note-error");
      root.appendChild(node);
    }
    node.textContent = error instanceof Error ? error.message : String(error);
  }

  function renderFieldNote(field) {
    if (field.state === "saved") {
      root.appendChild(text("code", field.path, "field-note-saved-path"));
      return;
    }

    root.appendChild(text("h2", "♻️ Field Note candidate"));
    if (field.title) root.appendChild(text("h3", field.title));

    if (field.state === "candidate") {
      root.appendChild(text("p", `Value level: ${field.value_level}`));
      root.appendChild(text("p", field.reusable_structure || ""));
      const actions = document.createElement("div");
      actions.className = "field-note-actions";
      const save = button("Save", () =>
        primaryAction(
          "/api/field-notes/save",
          {},
          save,
          skip,
          "Preparing approval…"
        )
      );
      const skip = button("Skip", () =>
        guardedPost("/api/field-notes/skip")
      );
      actions.appendChild(save);
      actions.appendChild(skip);
      root.appendChild(actions);
      if (field.error) {
        root.appendChild(text("p", field.error, "field-note-error"));
      }
      return;
    }

    if (field.state === "approval" && field.approval) {
      const approval = field.approval;
      root.appendChild(text("p", `${approval.action} ${approval.path}`));
      root.appendChild(text("p", `SHA-256: ${approval.content_sha256}`));
      root.appendChild(text("p", `Precondition: ${approval.precondition}`));
      root.appendChild(text("p", `Scope: ${approval.approval_scope}`));
      root.appendChild(text("pre", approval.content, "field-note-content"));
      const actions = document.createElement("div");
      actions.className = "field-note-actions";
      const allowOnce = button("Allow once", () =>
        primaryAction(
          "/api/field-notes/approval",
          { choice: "allow_once" },
          allowOnce,
          deny,
          "Saving Field Note…"
        )
      );
      const deny = button("Deny", () =>
        guardedPost("/api/field-notes/approval", { choice: "deny" })
      );
      actions.appendChild(allowOnce);
      actions.appendChild(deny);
      root.appendChild(actions);
    }
  }

  function renderReconnectReceipt(receipt) {
    const section = document.createElement("section");
    section.className = "field-note-reconnect-receipt";
    section.appendChild(text("h2", "Field Note reconnect receipt"));

    const values = document.createElement("dl");
    values.className = "field-note-reconnect-values";
    for (const key of reconnectFields) {
      values.appendChild(text("dt", key));
      values.appendChild(
        text("dd", receipt[key] == null ? "NONE" : String(receipt[key]))
      );
    }
    section.appendChild(values);
    root.appendChild(section);
  }

  function render(snapshot) {
    csrf = snapshot.csrf || csrf;
    const run = snapshot.run || null;
    const field = run && run.field_note;
    const reconnect = run && run.field_note_reconnect;
    const signature = JSON.stringify({
      field_note: field || null,
      field_note_reconnect: reconnect || null,
    });
    if (signature === lastSignature) return;
    lastSignature = signature;
    actionPending = false;
    root.removeAttribute("aria-busy");
    clear();

    const fieldVisible = Boolean(
      field && field.state !== "none" && field.state !== "skipped"
    );
    if (!fieldVisible && !reconnect) {
      root.hidden = true;
      return;
    }
    root.hidden = false;
    if (fieldVisible) renderFieldNote(field);
    if (reconnect) renderReconnectReceipt(reconnect);
  }

  async function refresh() {
    try {
      const response = await fetch("/api/state", {
        credentials: "same-origin",
      });
      if (!response.ok) return;
      render(await response.json());
    } catch (_error) {
      return;
    }
  }

  refresh();
  window.setInterval(refresh, 1000);
})();
