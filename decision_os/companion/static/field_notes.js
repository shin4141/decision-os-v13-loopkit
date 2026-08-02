(() => {
  "use strict";

  const root = document.createElement("section");
  root.id = "field-notes-lite";
  root.hidden = true;
  document.body.appendChild(root);

  let csrf = "";
  let lastSignature = "";

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

  function showError(error) {
    let node = root.querySelector(".field-note-error");
    if (!node) {
      node = text("p", "", "field-note-error");
      root.appendChild(node);
    }
    node.textContent = error instanceof Error ? error.message : String(error);
  }

  function render(snapshot) {
    csrf = snapshot.csrf || csrf;
    const field = snapshot.run && snapshot.run.field_note;
    const signature = JSON.stringify(field || null);
    if (signature === lastSignature) return;
    lastSignature = signature;
    clear();

    if (!field || field.state === "none" || field.state === "skipped") {
      root.hidden = true;
      return;
    }
    root.hidden = false;

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
      actions.appendChild(
        button("Save", () => post("/api/field-notes/save").catch(showError))
      );
      actions.appendChild(
        button("Skip", () => post("/api/field-notes/skip").catch(showError))
      );
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
      root.appendChild(text("pre", approval.content, "field-note-content"));
      const actions = document.createElement("div");
      actions.className = "field-note-actions";
      actions.appendChild(
        button("Allow once", () =>
          post("/api/field-notes/approval", { choice: "allow_once" }).catch(
            showError
          )
        )
      );
      actions.appendChild(
        button("Deny", () =>
          post("/api/field-notes/approval", { choice: "deny" }).catch(showError)
        )
      );
      root.appendChild(actions);
    }
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
