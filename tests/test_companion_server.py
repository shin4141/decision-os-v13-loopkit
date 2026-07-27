from __future__ import annotations

import http.client
import json
from pathlib import Path
import tempfile
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
