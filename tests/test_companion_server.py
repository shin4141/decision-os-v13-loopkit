from __future__ import annotations

import http.client
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import time
import unittest
from urllib.parse import urlsplit

from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import DecisionType
from decision_os.acceleration.store import StateIntegrityError
from decision_os.companion.controller import CompanionController
from decision_os.companion.server import CompanionServer
from tests.test_companion_controller import (
    ScriptedFactory,
    create_repository,
)


class CompanionServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository = create_repository(self.root, "repo<script>")
        self.controller = CompanionController(
            state_path=self.root / "state" / "state.json",
            picker_script=self.root / "fixed-picker.applescript",
            picker_runner=lambda _script: str(self.repository),
            adapter_factory=ScriptedFactory("mutation"),
        )
        self.controller.select_repository(self.repository)
        static_root = (
            Path(__file__).resolve().parents[1]
            / "decision_os"
            / "companion"
            / "static"
        )
        self.server = CompanionServer(
            self.controller,
            static_root=static_root,
        )
        self.server.start_background()

    def tearDown(self) -> None:
        run = self.controller.snapshot()["run"]
        if run["state"] == "running" and run["approval"] is not None:
            self.controller.submit_approval("deny")
        self.server.close()
        self.temporary.cleanup()

    def request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, object] | None = None,
        cookie: str | None = None,
        csrf: str | None = None,
        origin: str | None = None,
        host: str | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.port,
            timeout=5,
        )
        headers: dict[str, str] = {}
        if host is not None:
            headers["Host"] = host
        if cookie is not None:
            headers["Cookie"] = cookie
        if csrf is not None:
            headers["X-Decision-OS-CSRF"] = csrf
        if origin is not None:
            headers["Origin"] = origin
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(payload))
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        raw = response.read()
        result_headers = {
            key.lower(): value for key, value in response.getheaders()
        }
        status = response.status
        connection.close()
        return status, result_headers, raw

    def bootstrap(self) -> tuple[str, str]:
        path = urlsplit(self.server.bootstrap_url).path
        status, headers, _body = self.request("GET", path)
        self.assertEqual(303, status)
        cookie = headers["set-cookie"].split(";", 1)[0]
        status, _headers, raw = self.request(
            "GET",
            "/api/state",
            cookie=cookie,
        )
        self.assertEqual(200, status)
        csrf = json.loads(raw)["csrf"]
        return cookie, csrf

    def test_bootstrap_session_and_security_headers(self) -> None:
        status, _headers, _raw = self.request("GET", "/api/state")
        self.assertEqual(401, status)
        status, _headers, _raw = self.request(
            "GET",
            "/api/state",
            cookie="decision_os_session=invalid",
        )
        self.assertEqual(401, status)
        wrong = "/bootstrap/not-the-private-token"
        status, _headers, _raw = self.request("GET", wrong)
        self.assertEqual(401, status)

        path = urlsplit(self.server.bootstrap_url).path
        status, headers, _raw = self.request("GET", path)

        self.assertEqual(303, status)
        self.assertIn("HttpOnly", headers["set-cookie"])
        self.assertIn("SameSite=Strict", headers["set-cookie"])
        cookie = headers["set-cookie"].split(";", 1)[0]
        status, headers, _raw = self.request("GET", "/", cookie=cookie)
        self.assertEqual(200, status)
        self.assertEqual("no-store, max-age=0", headers["cache-control"])
        self.assertEqual("DENY", headers["x-frame-options"])
        self.assertIn("default-src 'none'", headers["content-security-policy"])
        self.assertIn("frame-ancestors 'none'", headers["content-security-policy"])
        status, _headers, _raw = self.request("GET", path)
        self.assertEqual(401, status)

    def test_host_origin_and_csrf_rejections(self) -> None:
        cookie, csrf = self.bootstrap()
        status, _headers, _raw = self.request(
            "GET",
            "/api/state",
            cookie=cookie,
            host="attacker.invalid",
        )
        self.assertEqual(403, status)
        status, _headers, _raw = self.request(
            "GET",
            "/api/state",
            cookie=cookie,
            origin="http://attacker.invalid",
        )
        self.assertEqual(403, status)
        status, _headers, _raw = self.request(
            "POST",
            "/api/new-run",
            body={},
            cookie=cookie,
            csrf=csrf,
            origin="http://attacker.invalid",
        )
        self.assertEqual(403, status)
        status, _headers, _raw = self.request(
            "POST",
            "/api/new-run",
            body={},
            cookie=cookie,
            origin=self.server.origin,
        )
        self.assertEqual(403, status)

    def test_static_allowlist_blocks_traversal_and_arbitrary_files(self) -> None:
        cookie, _csrf = self.bootstrap()
        for path in (
            "/../AGENTS.md",
            "/%2e%2e/AGENTS.md",
            "/etc/passwd",
            "/decision_os/acceleration/store.py",
            "/missing.js",
        ):
            status, _headers, raw = self.request(
                "GET",
                path,
                cookie=cookie,
            )
            self.assertEqual(404, status)
            self.assertNotIn(b"Agent Operating Rule", raw)

    def test_json_and_dom_rendering_are_script_safe(self) -> None:
        cookie, _csrf = self.bootstrap()
        status, _headers, raw = self.request(
            "GET",
            "/api/state",
            cookie=cookie,
        )
        self.assertEqual(200, status)
        self.assertIn(b"repo\\u003cscript\\u003e", raw)
        self.assertNotIn(b"<script>", raw)
        parsed = json.loads(raw)
        self.assertEqual("repo<script>", parsed["repository"]["name"])

        status, _headers, javascript = self.request(
            "GET",
            "/app.js",
            cookie=cookie,
        )
        self.assertEqual(200, status)
        self.assertIn(b"textContent", javascript)
        self.assertNotIn(b"innerHTML", javascript)

    def test_one_active_run_and_browser_reconnect(self) -> None:
        cookie, csrf = self.bootstrap()
        status, _headers, _raw = self.request(
            "POST",
            "/api/run",
            body={"task": "Modify target.txt once."},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status)
        deadline = time.monotonic() + 4
        first = None
        while time.monotonic() < deadline:
            status, _headers, raw = self.request(
                "GET",
                "/api/state",
                cookie=cookie,
            )
            self.assertEqual(200, status)
            first = json.loads(raw)
            if first["run"]["approval"] is not None:
                break
            time.sleep(0.01)
        self.assertIsNotNone(first)
        self.assertIsNotNone(first["run"]["approval"])

        status, _headers, raw = self.request(
            "GET",
            "/api/state",
            cookie=cookie,
        )
        second = json.loads(raw)
        self.assertEqual(first["run"]["approval"], second["run"]["approval"])

        status, _headers, raw = self.request(
            "POST",
            "/api/run",
            body={"task": "Overlapping task."},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(409, status)
        self.assertIn(b"already active", raw)

        status, _headers, _raw = self.request(
            "POST",
            "/api/approval",
            body={"choice": "deny"},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status)

    def test_public_state_exposes_opaque_default_handle_only(self) -> None:
        self.server.close()
        engine = AccelerationEngine(self.repository)
        engine.evaluate(
            run_id=engine.new_run_id(),
            iteration=1,
            decision_type=DecisionType.MODIFY_FILE,
            requested_scope="target.txt",
            source_interrupt_id="server-default-setup",
            choice_provider=lambda _identity: "2",
        )
        self.controller = CompanionController(
            state_path=self.root / "second-state" / "state.json",
            picker_runner=lambda _script: str(self.repository),
            adapter_factory=ScriptedFactory(),
        )
        self.controller.select_repository(self.repository)
        static_root = (
            Path(__file__).resolve().parents[1]
            / "decision_os"
            / "companion"
            / "static"
        )
        self.server = CompanionServer(self.controller, static_root=static_root)
        self.server.start_background()
        cookie, _csrf = self.bootstrap()

        status, _headers, raw = self.request(
            "GET",
            "/api/state",
            cookie=cookie,
        )

        self.assertEqual(200, status)
        text = raw.decode("utf-8")
        self.assertNotIn("decision_key", text)
        self.assertNotIn("rule_hash", text)
        self.assertNotIn("event_hash", text)
        self.assertNotIn("request_id", text)
        self.assertNotIn("credential", text)
        state = json.loads(raw)
        self.assertEqual(1, len(state["defaults"]))
        self.assertEqual(
            {"action", "created_at", "handle", "path"},
            set(state["defaults"][0]),
        )

    def test_corrupted_repository_state_error_is_sanitized(self) -> None:
        cookie, _csrf = self.bootstrap()
        original_snapshot = self.controller.snapshot

        def corrupted_snapshot() -> dict[str, object]:
            raise StateIntegrityError("secret chain detail")

        self.controller.snapshot = corrupted_snapshot  # type: ignore[method-assign]
        try:
            status, _headers, raw = self.request(
                "GET",
                "/api/state",
                cookie=cookie,
            )
        finally:
            self.controller.snapshot = original_snapshot  # type: ignore[method-assign]

        self.assertEqual(409, status)
        body = json.loads(raw)
        self.assertEqual(
            {"error": "Local companion state could not be read safely."},
            body,
        )
        self.assertNotIn("secret", raw.decode("utf-8"))


class CompanionClientBehaviorTest(unittest.TestCase):
    def test_disconnection_clears_and_disables_stale_ui_until_recovery(
        self,
    ) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for client behavior tests.")
        javascript = (
            Path(__file__).resolve().parents[1]
            / "decision_os"
            / "companion"
            / "static"
            / "app.js"
        )
        harness = textwrap.dedent(
            r"""
            "use strict";

            const assert = require("assert");
            const fs = require("fs");
            const vm = require("vm");

            const javascriptPath = process.argv[2];
            const source = fs.readFileSync(javascriptPath, "utf8");
            const disconnectedMessage =
              "This companion session has ended. Close this tab and relaunch Decision OS Companion.app.";

            class ClassList {
              constructor(initial = []) {
                this.values = new Set(initial);
              }

              contains(value) {
                return this.values.has(value);
              }

              toggle(value, force) {
                const enabled =
                  force === undefined ? !this.values.has(value) : Boolean(force);
                if (enabled) {
                  this.values.add(value);
                } else {
                  this.values.delete(value);
                }
                return enabled;
              }
            }

            class Element {
              constructor(tagName = "div", id = "") {
                this.tagName = tagName.toUpperCase();
                this.id = id;
                this.classList = new ClassList();
                this.className = "";
                this.dataset = {};
                this.disabled = false;
                this.value = "";
                this.type = "";
                this.children = [];
                this.parentNode = null;
                this.listeners = new Map();
                this.ownText = "";
              }

              get textContent() {
                return (
                  this.ownText +
                  this.children.map((child) => child.textContent).join("")
                );
              }

              set textContent(value) {
                this.ownText = value == null ? "" : String(value);
                for (const child of this.children) {
                  child.parentNode = null;
                }
                this.children = [];
              }

              append(...children) {
                for (const child of children) {
                  child.parentNode = this;
                  this.children.push(child);
                }
              }

              replaceChildren(...children) {
                for (const child of this.children) {
                  child.parentNode = null;
                }
                this.children = [];
                this.ownText = "";
                this.append(...children);
              }

              querySelectorAll(selector) {
                const matches = [];
                for (const child of this.children) {
                  if (selector === "button" && child.tagName === "BUTTON") {
                    matches.push(child);
                  }
                  matches.push(...child.querySelectorAll(selector));
                }
                return matches;
              }

              addEventListener(name, callback) {
                const listeners = this.listeners.get(name) || [];
                listeners.push(callback);
                this.listeners.set(name, listeners);
              }

              async dispatch(name) {
                for (const callback of this.listeners.get(name) || []) {
                  await callback({ target: this });
                }
              }

              focus() {}
            }

            const ids = [
              "approval-action",
              "approval-diff",
              "approval-overlay",
              "approval-path",
              "approval-reason",
              "approval-reason-label",
              "approval-repository",
              "choose-repository",
              "claim-boundary",
              "defaults",
              "file-actions",
              "global-error",
              "new-run",
              "progress",
              "progress-card",
              "receipt-status",
              "repository-name",
              "repository-path",
              "repository-receipt",
              "result",
              "result-card",
              "result-state",
              "run",
              "run-error",
              "run-receipt",
              "run-state",
              "runtime",
              "task",
            ];
            const elements = new Map(
              ids.map((id) => [
                id,
                new Element(
                  ["choose-repository", "new-run", "run"].includes(id)
                    ? "button"
                    : id === "task"
                      ? "textarea"
                      : "div",
                  id,
                ),
              ]),
            );
            for (const id of [
              "approval-overlay",
              "approval-reason",
              "approval-reason-label",
              "global-error",
              "progress-card",
              "result-card",
              "run-error",
            ]) {
              elements.get(id).classList.toggle("hidden", true);
            }
            elements.get("task").value = "Keep this bounded task";

            const approvalButtons = [
              "allow_once",
              "repository",
              "deny",
            ].map((choice) => {
              const button = new Element("button");
              button.dataset.choice = choice;
              return button;
            });
            const document = {
              createElement(tagName) {
                return new Element(tagName);
              },
              getElementById(id) {
                assert(elements.has(id), `Unknown DOM id: ${id}`);
                return elements.get(id);
              },
              querySelectorAll(selector) {
                if (selector === "[data-choice]") {
                  return approvalButtons;
                }
                return [];
              },
            };

            const timers = [];
            const fetchQueue = [];
            const fetchCalls = [];
            const window = {
              confirm() {
                return false;
              },
              setTimeout(callback) {
                timers.push(callback);
                return timers.length;
              },
            };
            async function fetchMock(path, options = {}) {
              fetchCalls.push({ path, options });
              assert(fetchQueue.length > 0, `Unexpected fetch: ${path}`);
              return fetchQueue.shift()();
            }
            function response(body, status = 200) {
              return {
                ok: status >= 200 && status < 300,
                status,
                async json() {
                  return body;
                },
              };
            }
            function deferred() {
              let resolve;
              let reject;
              const promise = new Promise((resolvePromise, rejectPromise) => {
                resolve = resolvePromise;
                reject = rejectPromise;
              });
              return { promise, reject, resolve };
            }
            function emptyRun(overrides = {}) {
              return {
                state: "idle",
                progress: [],
                result: "",
                file_actions: [],
                runtime: null,
                receipt_delta: null,
                approval: null,
                error: null,
                ...overrides,
              };
            }
            const staleReceipt = {
              status: "STALE_RECEIPT_STATUS",
              verified_saves: 7,
              verified_reuses: 8,
              estimated_minutes: 90,
              estimated_money_jpy: 12000,
              estimated_tokens: 3456,
              claim_boundary: "STALE_CLAIM_BOUNDARY",
            };
            const completedState = {
              csrf: "csrf-one",
              repository: {
                name: "STALE_REPOSITORY_NAME",
                path: "/tmp/STALE_REPOSITORY_PATH",
              },
              run: emptyRun({
                state: "completed",
                progress: ["STALE_PROGRESS"],
                result: "STALE_RESULT",
                file_actions: [
                  {
                    action: "Modify",
                    path: "STALE_FILE_PATH",
                    status: "approved",
                    access: "one-time",
                  },
                ],
                runtime: {
                  authentication: "STALE_AUTH",
                  model: "STALE_MODEL",
                  reasoning_effort: "STALE_REASONING",
                  service_tier: "STALE_TIER",
                  codex_version: "STALE_VERSION",
                },
                receipt_delta: staleReceipt,
              }),
              defaults: [
                {
                  action: "Modify",
                  path: "STALE_DEFAULT_PATH",
                  handle: "opaque-handle",
                },
              ],
              receipt: staleReceipt,
            };
            const approvalState = {
              ...completedState,
              csrf: "csrf-two",
              run: emptyRun({
                state: "running",
                progress: ["WAITING_FOR_APPROVAL"],
                approval: {
                  repository: "STALE_APPROVAL_REPOSITORY",
                  action: "Modify",
                  path: "STALE_APPROVAL_PATH",
                  diff: "STALE_APPROVAL_DIFF",
                  reason: "STALE_APPROVAL_REASON",
                },
              }),
            };
            const recoveredState = {
              csrf: "csrf-recovered",
              repository: {
                name: "FRESH_REPOSITORY_NAME",
                path: "/tmp/FRESH_REPOSITORY_PATH",
              },
              run: emptyRun({
                state: "completed",
                progress: ["FRESH_PROGRESS"],
                result: "FRESH_RESULT",
              }),
              defaults: [],
              receipt: null,
            };

            function hidden(id) {
              return elements.get(id).classList.contains("hidden");
            }
            async function settle() {
              await new Promise((resolve) => setImmediate(resolve));
              await new Promise((resolve) => setImmediate(resolve));
            }
            async function runNextTimer() {
              assert(timers.length > 0, "Expected a scheduled refresh.");
              await timers.shift()();
              await settle();
            }

            async function main() {
              fetchQueue.push(() => Promise.resolve(response(completedState)));
              const sandbox = {
                Boolean,
                Error,
                Intl,
                JSON,
                Promise,
                String,
                TypeError,
                console,
                document,
                fetch: fetchMock,
                window,
              };
              vm.createContext(sandbox);
              vm.runInContext(source, sandbox, { filename: javascriptPath });
              await settle();

              assert.strictEqual(
                elements.get("repository-name").textContent,
                "STALE_REPOSITORY_NAME",
              );
              assert.strictEqual(
                elements.get("repository-path").textContent,
                "/tmp/STALE_REPOSITORY_PATH",
              );
              assert.strictEqual(elements.get("result").textContent, "STALE_RESULT");
              assert.strictEqual(hidden("result-card"), false);
              assert.strictEqual(hidden("global-error"), true);
              assert.strictEqual(elements.get("choose-repository").disabled, false);
              assert.strictEqual(elements.get("task").disabled, false);
              assert.strictEqual(elements.get("run").disabled, false);
              assert.strictEqual(elements.get("new-run").disabled, false);
              const firstRevoke =
                elements.get("defaults").children[0].children[1];
              assert.strictEqual(firstRevoke.disabled, false);

              fetchQueue.push(() => Promise.resolve(response(approvalState)));
              await runNextTimer();
              assert.strictEqual(hidden("approval-overlay"), false);
              assert.strictEqual(
                elements.get("approval-repository").textContent,
                "STALE_APPROVAL_REPOSITORY",
              );
              for (const button of approvalButtons) {
                assert.strictEqual(button.disabled, false);
              }
              const pendingRevoke =
                elements.get("defaults").children[0].children[1];

              fetchQueue.push(() =>
                Promise.reject(new TypeError("fetch failed")),
              );
              await runNextTimer();

              assert.strictEqual(
                elements.get("repository-name").textContent,
                "Companion disconnected",
              );
              assert.strictEqual(
                elements.get("repository-path").textContent,
                disconnectedMessage,
              );
              assert.strictEqual(
                elements.get("global-error").textContent,
                disconnectedMessage,
              );
              assert.strictEqual(hidden("global-error"), false);
              assert.strictEqual(hidden("progress-card"), true);
              assert.strictEqual(elements.get("progress").children.length, 0);
              assert.strictEqual(elements.get("run-error").textContent, "");
              assert.strictEqual(hidden("result-card"), true);
              assert.strictEqual(elements.get("result").textContent, "");
              assert.strictEqual(elements.get("file-actions").children.length, 0);
              assert.strictEqual(elements.get("runtime").children.length, 0);
              assert.strictEqual(elements.get("run-receipt").children.length, 0);
              assert.strictEqual(
                elements.get("repository-receipt").children.length,
                0,
              );
              assert.strictEqual(
                elements.get("receipt-status").textContent,
                "Session ended",
              );
              assert.strictEqual(elements.get("claim-boundary").textContent, "");
              assert.strictEqual(elements.get("defaults").children.length, 0);
              assert.strictEqual(hidden("approval-overlay"), true);
              for (const id of [
                "approval-repository",
                "approval-action",
                "approval-path",
                "approval-diff",
                "approval-reason",
              ]) {
                assert.strictEqual(elements.get(id).textContent, "");
              }
              for (const id of [
                "choose-repository",
                "run",
                "new-run",
                "task",
              ]) {
                assert.strictEqual(elements.get(id).disabled, true, id);
              }
              for (const button of approvalButtons) {
                assert.strictEqual(button.disabled, true);
              }
              assert.strictEqual(pendingRevoke.disabled, true);

              elements.get("task").value = "Changed while disconnected";
              await elements.get("task").dispatch("input");
              assert.strictEqual(
                elements.get("repository-path").textContent,
                disconnectedMessage,
              );
              assert.strictEqual(elements.get("run").disabled, true);

              fetchQueue.push(() => Promise.resolve(response(recoveredState)));
              await runNextTimer();
              assert.strictEqual(
                elements.get("repository-name").textContent,
                "FRESH_REPOSITORY_NAME",
              );
              assert.strictEqual(
                elements.get("repository-path").textContent,
                "/tmp/FRESH_REPOSITORY_PATH",
              );
              assert.strictEqual(elements.get("result").textContent, "FRESH_RESULT");
              assert.strictEqual(hidden("global-error"), true);
              assert.strictEqual(elements.get("choose-repository").disabled, false);
              assert.strictEqual(elements.get("task").disabled, false);
              assert.strictEqual(elements.get("run").disabled, false);
              assert.strictEqual(elements.get("new-run").disabled, false);

              const freshApprovalState = {
                ...approvalState,
                csrf: "csrf-approval",
                repository: recoveredState.repository,
              };
              fetchQueue.push(() =>
                Promise.resolve(response(freshApprovalState)),
              );
              await runNextTimer();
              assert.strictEqual(hidden("approval-overlay"), false);
              for (const button of approvalButtons) {
                assert.strictEqual(button.disabled, false);
              }

              fetchQueue.push(() =>
                Promise.reject(new TypeError("post fetch failed")),
              );
              await approvalButtons[0].dispatch("click");
              await settle();
              const approvalRequest = fetchCalls.at(-1);
              assert.strictEqual(approvalRequest.path, "/api/approval");
              assert.strictEqual(approvalRequest.options.method, "POST");
              assert.strictEqual(
                approvalRequest.options.headers["X-Decision-OS-CSRF"],
                "csrf-approval",
              );
              assert.strictEqual(hidden("approval-overlay"), true);
              assert.strictEqual(
                elements.get("approval-repository").textContent,
                "",
              );
              for (const button of approvalButtons) {
                assert.strictEqual(button.disabled, true);
              }
              assert.strictEqual(elements.get("choose-repository").disabled, true);
              assert.strictEqual(elements.get("task").disabled, true);

              fetchQueue.push(() => Promise.resolve(response(recoveredState)));
              await runNextTimer();
              assert.strictEqual(
                elements.get("repository-name").textContent,
                "FRESH_REPOSITORY_NAME",
              );
              assert.strictEqual(hidden("approval-overlay"), true);
              assert.strictEqual(elements.get("choose-repository").disabled, false);

              fetchQueue.push(() =>
                Promise.resolve(
                  response({ error: "One bounded Run is already active." }, 409),
                ),
              );
              await elements.get("run").dispatch("click");
              await settle();
              assert.strictEqual(
                elements.get("global-error").textContent,
                "One bounded Run is already active.",
              );
              assert.strictEqual(hidden("global-error"), false);
              assert.strictEqual(
                elements.get("repository-name").textContent,
                "FRESH_REPOSITORY_NAME",
              );
              assert.strictEqual(elements.get("choose-repository").disabled, false);

              const oldState = deferred();
              fetchQueue.push(() => oldState.promise);
              assert(timers.length > 0, "Expected a refresh for the race test.");
              const oldRefresh = timers.shift()();
              await settle();
              assert.strictEqual(fetchCalls.at(-1).path, "/api/state");

              fetchQueue.push(() =>
                Promise.reject(new TypeError("racing post fetch failed")),
              );
              await elements.get("run").dispatch("click");
              await settle();
              assert.strictEqual(
                elements.get("repository-path").textContent,
                disconnectedMessage,
              );

              oldState.resolve(response(recoveredState));
              await oldRefresh;
              await settle();
              assert.strictEqual(
                elements.get("repository-path").textContent,
                disconnectedMessage,
              );
              assert.strictEqual(elements.get("choose-repository").disabled, true);

              fetchQueue.push(() => Promise.resolve(response(recoveredState)));
              await runNextTimer();
              assert.strictEqual(
                elements.get("repository-name").textContent,
                "FRESH_REPOSITORY_NAME",
              );
              assert.strictEqual(elements.get("choose-repository").disabled, false);
            }

            main().catch((error) => {
              console.error(error.stack || error);
              process.exitCode = 1;
            });
            """
        )
        completed = subprocess.run(
            [node, "-", str(javascript)],
            input=harness,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(
            0,
            completed.returncode,
            msg=f"Node client harness failed:\n{completed.stdout}{completed.stderr}",
        )
