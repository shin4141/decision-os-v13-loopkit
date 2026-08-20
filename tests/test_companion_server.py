from __future__ import annotations

import base64
import hashlib
import http.client
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
import time
import unittest
import uuid
from unittest.mock import Mock
from urllib.parse import urlsplit

from decision_os.acceleration.engine import AccelerationEngine
from decision_os.acceleration.model import DecisionType
from decision_os.acceleration.store import StateIntegrityError
from decision_os.companion.controller import CompanionController
from decision_os.companion.guided_intake import (
    GuidedIntakeBusyError,
    GuidedIntakeConflictError,
    GuidedIntakeIntegrityError,
    GuidedIntakeValidationError,
)
from decision_os.companion.server import CompanionServer
from tests.test_companion_controller import (
    ScriptedFactory,
    bridge_boundary,
    create_repository,
    pro_design_metadata,
)
from tests.test_companion_continuation import stage_b_request
from tests.test_companion_small_compound_loop import stage_c_request


BRIDGE_POST_ROUTES = (
    "/api/bridge/session",
    "/api/bridge/copy",
    "/api/bridge/import",
    "/api/bridge/handoff/generate",
    "/api/bridge/output/freeze",
    "/api/bridge/receipt/generate",
    "/api/bridge/manifest/generate",
    "/api/bridge/replay",
    "/api/bridge/observation",
)
GUIDED_INTAKE_POST_ROUTES = (
    "/api/guided-intake/capture",
    "/api/guided-intake/copy",
    "/api/guided-intake/import-draft",
    "/api/guided-intake/confirm",
    "/api/guided-intake/freeze",
    "/api/guided-intake/purge",
    "/api/guided-intake/transfer-to-bridge",
)
INTELLIGENCE_TRANSPLANT_POST_ROUTES = (
    "/api/intelligence-transplant/charter/freeze",
    "/api/intelligence-transplant/manifest/freeze",
    "/api/intelligence-transplant/evidence/attach",
    "/api/intelligence-transplant/receipt/attach",
    "/api/intelligence-transplant/control/record",
)
ORDINARY_CONTRACT_POST_ROUTES = (
    "/api/ordinary-contract/prepare",
    "/api/ordinary-contract/confirm",
    "/api/ordinary-contract/fix",
    "/api/ordinary-contract/error/dismiss",
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
        raw_body: bytes | None = None,
        cookie: str | None = None,
        csrf: str | None = None,
        origin: str | None = None,
        host: str | None = None,
        declared_content_length: int | None = None,
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
        self.assertFalse(
            body is not None and raw_body is not None,
            "request body must use one encoding",
        )
        payload = raw_body
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
        if payload is not None:
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(
                declared_content_length
                if declared_content_length is not None
                else len(payload)
            )
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

    def start_bridge_session(
        self,
        cookie: str,
        csrf: str,
    ) -> dict[str, object]:
        status, _headers, raw = self.request(
            "POST",
            "/api/bridge/session",
            body={"boundary": bridge_boundary()},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        return json.loads(raw)

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

    def test_all_manual_bridge_posts_require_session_origin_and_csrf(
        self,
    ) -> None:
        for path in BRIDGE_POST_ROUTES:
            with self.subTest(path=path, missing="session"):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body={},
                    origin=self.server.origin,
                )
                self.assertEqual(401, status)

        cookie, csrf = self.bootstrap()
        for path in BRIDGE_POST_ROUTES:
            with self.subTest(path=path, missing="origin"):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body={},
                    cookie=cookie,
                    csrf=csrf,
                )
                self.assertEqual(403, status)
            with self.subTest(path=path, missing="csrf"):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body={},
                    cookie=cookie,
                    origin=self.server.origin,
                )
                self.assertEqual(403, status)

    def test_all_guided_intake_routes_keep_private_session_boundary(
        self,
    ) -> None:
        status, _headers, _raw = self.request(
            "GET",
            "/api/guided-intake/state",
        )
        self.assertEqual(401, status)
        for path in GUIDED_INTAKE_POST_ROUTES:
            with self.subTest(path=path, missing="session"):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body={},
                    origin=self.server.origin,
                )
                self.assertEqual(401, status)

        cookie, csrf = self.bootstrap()
        status, _headers, raw = self.request(
            "GET",
            "/api/guided-intake/state",
            cookie=cookie,
        )
        self.assertEqual(200, status)
        state = json.loads(raw)
        self.assertIn("guided_intake", state)
        self.assertEqual(csrf, state["csrf"])
        for path in GUIDED_INTAKE_POST_ROUTES:
            with self.subTest(path=path, missing="origin"):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body={},
                    cookie=cookie,
                    csrf=csrf,
                )
                self.assertEqual(403, status)
            with self.subTest(path=path, missing="csrf"):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body={},
                    cookie=cookie,
                    origin=self.server.origin,
                )
                self.assertEqual(403, status)

    def test_all_intelligence_transplant_posts_require_private_boundary(
        self,
    ) -> None:
        for path in INTELLIGENCE_TRANSPLANT_POST_ROUTES:
            with self.subTest(path=path, missing="session"):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body={},
                    origin=self.server.origin,
                )
                self.assertEqual(401, status)

        cookie, csrf = self.bootstrap()
        for path in INTELLIGENCE_TRANSPLANT_POST_ROUTES:
            with self.subTest(path=path, missing="origin"):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body={},
                    cookie=cookie,
                    csrf=csrf,
                )
                self.assertEqual(403, status)
            with self.subTest(path=path, missing="csrf"):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body={},
                    cookie=cookie,
                    origin=self.server.origin,
                )
                self.assertEqual(403, status)

    def test_intelligence_transplant_routes_reject_non_exact_bodies(
        self,
    ) -> None:
        cookie, csrf = self.bootstrap()
        transport_payload = '{"object_type":"E1_DISCOVERY"}'
        transport = {
            "as_of": "2026-07-30T00:00:00Z",
            "context_evidence_ref": None,
            "declared_sha256": hashlib.sha256(
                transport_payload.encode("utf-8")
            ).hexdigest(),
            "mode": "PASTE_CAPTURE",
            "payload_text": transport_payload,
            "source_path_or_label": "e1.json",
        }
        invalid_requests = [
            ("/api/intelligence-transplant/charter/freeze", {}),
            (
                "/api/intelligence-transplant/charter/freeze",
                {"record": {}, "unexpected": True},
            ),
            (
                "/api/intelligence-transplant/charter/freeze",
                {"record": []},
            ),
            *[
                (path, {})
                for path in INTELLIGENCE_TRANSPLANT_POST_ROUTES[1:]
            ],
            (
                "/api/intelligence-transplant/evidence/attach",
                {**transport, "unexpected": True},
            ),
            (
                "/api/intelligence-transplant/evidence/attach",
                {
                    **transport,
                    "payload_base64": "e30=",
                },
            ),
            (
                "/api/intelligence-transplant/evidence/attach",
                {**transport, "context_evidence_ref": "not-an-object"},
            ),
            (
                "/api/intelligence-transplant/evidence/attach",
                {**transport, "declared_sha256": 1},
            ),
            (
                "/api/intelligence-transplant/evidence/attach",
                {**transport, "declared_sha256": None},
            ),
            (
                "/api/intelligence-transplant/evidence/attach",
                {**transport, "as_of": 1},
            ),
            (
                "/api/intelligence-transplant/evidence/attach",
                {
                    **transport,
                    "mode": "BYTE_EXACT_FILE_IMPORT",
                },
            ),
            (
                "/api/intelligence-transplant/evidence/attach",
                {
                    **{
                        key: value
                        for key, value in transport.items()
                        if key != "payload_text"
                    },
                    "mode": "BYTE_EXACT_FILE_IMPORT",
                    "payload_base64": "%%%not-base64%%%",
                },
            ),
        ]
        for path, body in invalid_requests:
            with self.subTest(path=path, body=body):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body=body,
                    cookie=cookie,
                    csrf=csrf,
                    origin=self.server.origin,
                )
                self.assertEqual(400, status)

    def test_intelligence_transplant_outer_json_is_strict_only_there(
        self,
    ) -> None:
        cookie, csrf = self.bootstrap()
        original_charter = (
            self.controller.intelligence_transplant_freeze_charter
        )
        original_start_run = self.controller.start_run
        charter = Mock(side_effect=AssertionError("invalid JSON dispatched"))
        bounded_tasks: list[str] = []

        def start_run(task: str) -> dict[str, object]:
            bounded_tasks.append(task)
            return self.controller.snapshot()

        self.controller.intelligence_transplant_freeze_charter = charter  # type: ignore[method-assign]
        self.controller.start_run = start_run  # type: ignore[method-assign]
        try:
            for raw_body in (
                b'{"record":{"object_type":"RUN_CHARTER",'
                b'"object_type":"E1_DISCOVERY"}}',
                b'{"record":{"object_type":NaN}}',
                b'{"record":{},"record":{}}',
            ):
                with self.subTest(raw_body=raw_body):
                    status, _headers, _raw = self.request(
                        "POST",
                        "/api/intelligence-transplant/charter/freeze",
                        raw_body=raw_body,
                        cookie=cookie,
                        csrf=csrf,
                        origin=self.server.origin,
                    )
                    self.assertEqual(400, status)

            status, _headers, raw = self.request(
                "POST",
                "/api/run",
                raw_body=b'{"task":"first","task":"second"}',
                cookie=cookie,
                csrf=csrf,
                origin=self.server.origin,
            )
            self.assertEqual(
                200,
                status,
                raw.decode("utf-8", errors="replace"),
            )
            self.assertEqual(["second"], bounded_tasks)
        finally:
            self.controller.intelligence_transplant_freeze_charter = (  # type: ignore[method-assign]
                original_charter
            )
            self.controller.start_run = original_start_run  # type: ignore[method-assign]

        charter.assert_not_called()

    def test_intelligence_transplant_routes_never_dispatch_runner(
        self,
    ) -> None:
        cookie, csrf = self.bootstrap()
        original_start_run = self.controller.start_run
        original_methods = {
            "charter": (
                self.controller.intelligence_transplant_freeze_charter
            ),
            "manifest": (
                self.controller.intelligence_transplant_freeze_manifest
            ),
            "evidence": (
                self.controller.intelligence_transplant_attach_evidence
            ),
            "receipt": (
                self.controller.intelligence_transplant_attach_receipt
            ),
            "control": (
                self.controller.intelligence_transplant_record_control
            ),
        }
        received: list[tuple[str, object]] = []

        def charter(record: dict[str, object]) -> dict[str, object]:
            received.append(("charter", record))
            return self.controller.snapshot()

        def transport(
            *,
            payload: bytes,
            mode: str,
            source_path_or_label: str,
            declared_sha256: str,
            context_evidence_ref: dict[str, object] | None,
            as_of: str,
            label: str,
        ) -> dict[str, object]:
            received.append(
                (
                    label,
                    {
                        "as_of": as_of,
                        "context_evidence_ref": context_evidence_ref,
                        "declared_sha256": declared_sha256,
                        "mode": mode,
                        "payload": payload,
                        "source_path_or_label": source_path_or_label,
                    },
                )
            )
            return self.controller.snapshot()

        self.controller.start_run = Mock(  # type: ignore[method-assign]
            side_effect=AssertionError("Stage 5 must not start the runner")
        )
        self.controller.intelligence_transplant_freeze_charter = charter  # type: ignore[method-assign]
        self.controller.intelligence_transplant_freeze_manifest = (  # type: ignore[method-assign]
            lambda **value: transport(label="manifest", **value)
        )
        self.controller.intelligence_transplant_attach_evidence = (  # type: ignore[method-assign]
            lambda **value: transport(label="evidence", **value)
        )
        self.controller.intelligence_transplant_attach_receipt = (  # type: ignore[method-assign]
            lambda **value: transport(label="receipt", **value)
        )
        self.controller.intelligence_transplant_record_control = (  # type: ignore[method-assign]
            lambda **value: transport(label="control", **value)
        )
        try:
            status, _headers, raw = self.request(
                "POST",
                "/api/intelligence-transplant/charter/freeze",
                body={"record": {"object_type": "RUN_CHARTER"}},
                cookie=cookie,
                csrf=csrf,
                origin=self.server.origin,
            )
            self.assertEqual(
                200,
                status,
                raw.decode("utf-8", errors="replace"),
            )
            for label, path in (
                ("manifest", "/api/intelligence-transplant/manifest/freeze"),
                ("evidence", "/api/intelligence-transplant/evidence/attach"),
                ("receipt", "/api/intelligence-transplant/receipt/attach"),
                ("control", "/api/intelligence-transplant/control/record"),
            ):
                payload_text = f'{{"route_label":"{label}"}}'
                status, _headers, raw = self.request(
                    "POST",
                    path,
                    body={
                        "as_of": "2026-07-30T00:00:00Z",
                        "context_evidence_ref": None,
                        "declared_sha256": hashlib.sha256(
                            payload_text.encode("utf-8")
                        ).hexdigest(),
                        "mode": "PASTE_CAPTURE",
                        "payload_text": payload_text,
                        "source_path_or_label": f"{label}.json",
                    },
                    cookie=cookie,
                    csrf=csrf,
                    origin=self.server.origin,
                )
                self.assertEqual(
                    200,
                    status,
                    raw.decode("utf-8", errors="replace"),
                )
        finally:
            self.controller.start_run = original_start_run  # type: ignore[method-assign]
            self.controller.intelligence_transplant_freeze_charter = (  # type: ignore[method-assign]
                original_methods["charter"]
            )
            self.controller.intelligence_transplant_freeze_manifest = (  # type: ignore[method-assign]
                original_methods["manifest"]
            )
            self.controller.intelligence_transplant_attach_evidence = (  # type: ignore[method-assign]
                original_methods["evidence"]
            )
            self.controller.intelligence_transplant_attach_receipt = (  # type: ignore[method-assign]
                original_methods["receipt"]
            )
            self.controller.intelligence_transplant_record_control = (  # type: ignore[method-assign]
                original_methods["control"]
            )

        self.assertEqual(
            ["charter", "manifest", "evidence", "receipt", "control"],
            [label for label, _value in received],
        )
        for label, value in received[1:]:
            self.assertIsInstance(value, dict)
            self.assertEqual(
                f'{{"route_label":"{label}"}}'.encode("utf-8"),
                value["payload"],
            )
        factory = self.controller.adapter_factory
        self.assertIsInstance(factory, ScriptedFactory)
        self.assertEqual(1, len(factory.modes))

    def test_guided_intake_routes_reject_non_exact_bodies(self) -> None:
        cookie, csrf = self.bootstrap()
        invalid_requests = (
            ("/api/guided-intake/capture", {}),
            (
                "/api/guided-intake/capture",
                {"original_request": "task", "unexpected": True},
            ),
            (
                "/api/guided-intake/capture",
                {"original_request": 1},
            ),
            ("/api/guided-intake/copy", {"unexpected": True}),
            (
                "/api/guided-intake/import-draft",
                {"draft_json": "{}", "producer_label": 1},
            ),
            (
                "/api/guided-intake/import-draft",
                {"draft_json": "{}"},
            ),
            (
                "/api/guided-intake/confirm",
                {
                    "question": "q",
                    "answer": "a",
                    "resulting_delta": "not-an-object",
                },
            ),
            ("/api/guided-intake/freeze", {"unexpected": True}),
            (
                "/api/guided-intake/purge",
                {
                    "request_id": "GI-REQ-EXACT",
                    "request_sha256": "a" * 64,
                },
            ),
            (
                "/api/guided-intake/purge",
                {
                    "confirmed": True,
                    "request_id": "GI-REQ-EXACT",
                    "request_sha256": "a" * 64,
                    "unexpected": True,
                },
            ),
            (
                "/api/guided-intake/purge",
                {
                    "confirmed": "true",
                    "request_id": "GI-REQ-EXACT",
                    "request_sha256": "a" * 64,
                },
            ),
            (
                "/api/guided-intake/purge",
                {
                    "confirmed": True,
                    "request_id": 1,
                    "request_sha256": "a" * 64,
                },
            ),
            (
                "/api/guided-intake/purge",
                {
                    "confirmed": True,
                    "request_id": "GI-REQ-EXACT",
                    "request_sha256": 1,
                },
            ),
            (
                "/api/guided-intake/transfer-to-bridge",
                {"unexpected": True},
            ),
        )
        for path, body in invalid_requests:
            with self.subTest(path=path, body=body):
                status, _headers, _raw = self.request(
                    "POST",
                    path,
                    body=body,
                    cookie=cookie,
                    csrf=csrf,
                    origin=self.server.origin,
                )
                self.assertEqual(400, status)

    def test_guided_intake_capture_cap_and_no_runner_dispatch(self) -> None:
        cookie, csrf = self.bootstrap()
        original_capture = self.controller.guided_intake_capture
        captured: list[tuple[str, str | None]] = []

        def capture(
            original_request: str,
            *,
            supersedes_request_id: str | None = None,
        ) -> dict[str, object]:
            captured.append((original_request, supersedes_request_id))
            return self.controller.snapshot()

        self.controller.guided_intake_capture = capture  # type: ignore[method-assign]
        try:
            exact_request = "x" * 65_536
            status, _headers, raw = self.request(
                "POST",
                "/api/guided-intake/capture",
                body={"original_request": exact_request},
                cookie=cookie,
                csrf=csrf,
                origin=self.server.origin,
            )
            self.assertEqual(
                200,
                status,
                raw.decode("utf-8", errors="replace"),
            )
            self.assertEqual([(exact_request, None)], captured)

            status, _headers, raw = self.request(
                "POST",
                "/api/guided-intake/capture",
                body={"original_request": "not read"},
                cookie=cookie,
                csrf=csrf,
                origin=self.server.origin,
                declared_content_length=(2 * 1024 * 1024) + 1,
            )
            self.assertEqual(413, status)
            self.assertEqual(
                {"error": "Request is too large."},
                json.loads(raw),
            )
        finally:
            self.controller.guided_intake_capture = original_capture  # type: ignore[method-assign]

        factory = self.controller.adapter_factory
        self.assertIsInstance(factory, ScriptedFactory)
        self.assertEqual(1, len(factory.modes))

    def test_guided_intake_purge_route_forwards_only_exact_payload(
        self,
    ) -> None:
        cookie, csrf = self.bootstrap()
        original_purge = self.controller.guided_intake_purge
        received: list[tuple[str, str, bool]] = []

        def purge(
            request_id: str,
            request_sha256: str,
            confirmed: bool,
        ) -> dict[str, object]:
            received.append((request_id, request_sha256, confirmed))
            return self.controller.snapshot()

        self.controller.guided_intake_purge = purge  # type: ignore[method-assign]
        try:
            body = {
                "confirmed": True,
                "request_id": "GI-REQ-EXACT",
                "request_sha256": "a" * 64,
            }
            status, _headers, raw = self.request(
                "POST",
                "/api/guided-intake/purge",
                body=body,
                cookie=cookie,
                csrf=csrf,
                origin=self.server.origin,
            )
            self.assertEqual(
                200,
                status,
                raw.decode("utf-8", errors="replace"),
            )
            self.assertEqual(
                [("GI-REQ-EXACT", "a" * 64, True)],
                received,
            )
        finally:
            self.controller.guided_intake_purge = original_purge  # type: ignore[method-assign]

        factory = self.controller.adapter_factory
        self.assertIsInstance(factory, ScriptedFactory)
        self.assertEqual(1, len(factory.modes))

    def test_guided_intake_purge_http_identity_confirmation_and_terminal_state(
        self,
    ) -> None:
        cookie, csrf = self.bootstrap()
        original_request = "private exact request\nwith identity-bearing bytes\r\n"
        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/capture",
            body={"original_request": original_request},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        captured = json.loads(raw)["guided_intake"]
        request_id = captured["request_identity"]["request_id"]
        request_sha256 = captured["request_identity"]["sha256"]

        attempts = (
            (
                {
                    "confirmed": False,
                    "request_id": request_id,
                    "request_sha256": request_sha256,
                },
                400,
            ),
            (
                {
                    "confirmed": True,
                    "request_id": f"{request_id}-WRONG",
                    "request_sha256": request_sha256,
                },
                409,
            ),
            (
                {
                    "confirmed": True,
                    "request_id": request_id,
                    "request_sha256": "f" * 64,
                },
                409,
            ),
        )
        for body, expected_status in attempts:
            with self.subTest(body=body):
                status, _headers, _raw = self.request(
                    "POST",
                    "/api/guided-intake/purge",
                    body=body,
                    cookie=cookie,
                    csrf=csrf,
                    origin=self.server.origin,
                )
                self.assertEqual(expected_status, status)

        status, _headers, raw = self.request(
            "GET",
            "/api/guided-intake/state",
            cookie=cookie,
        )
        self.assertEqual(200, status)
        self.assertEqual(
            original_request,
            json.loads(raw)["guided_intake"]["original_request"],
        )

        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/purge",
            body={
                "confirmed": True,
                "request_id": request_id,
                "request_sha256": request_sha256,
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        state = json.loads(raw)
        guided = state["guided_intake"]
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            guided["state"],
        )
        self.assertIsNone(guided["original_request"])
        self.assertIsNone(guided["interpretation"])
        self.assertEqual("UNAVAILABLE", guided["raw_source_availability"])
        self.assertEqual("BLOCKED", guided["judgment_reuse"])
        self.assertEqual("BLOCKED", guided["fidelity_evaluation"])
        self.assertEqual("PRESERVED", guided["historical_identity"])
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            guided["transfer_state"],
        )
        self.assertEqual(
            {
                "completed_at",
                "confirmation",
                "event_hash",
                "event_id",
                "purge_request_event_hash",
                "purge_request_event_id",
                "purged_at",
                "raw_blob_disposition",
                "remaining_non_purged_references",
                "request_id",
                "request_sha256",
            },
            set(guided["purge"]),
        )
        self.assertEqual(request_id, guided["purge"]["request_id"])
        self.assertEqual(
            request_sha256,
            guided["purge"]["request_sha256"],
        )
        self.assertEqual(
            "EXPLICIT_USER_CONFIRMATION",
            guided["purge"]["confirmation"],
        )
        self.assertEqual(
            "DELETED_NO_NON_PURGED_REFERENCES",
            guided["purge"]["raw_blob_disposition"],
        )
        self.assertEqual(
            0,
            guided["purge"]["remaining_non_purged_references"],
        )
        self.assertRegex(guided["purge"]["event_hash"], r"^[0-9a-f]{64}$")
        self.assertNotIn(original_request, raw.decode("utf-8"))
        self.assertEqual("idle", state["run"]["state"])

        status, _headers, snapshot_raw = self.request(
            "GET",
            "/api/guided-intake/state",
            cookie=cookie,
        )
        self.assertEqual(200, status)
        snapshot = json.loads(snapshot_raw)
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            snapshot["guided_intake"]["state"],
        )
        self.assertIsNone(snapshot["guided_intake"]["original_request"])
        self.assertNotIn(original_request, snapshot_raw.decode("utf-8"))

        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/transfer-to-bridge",
            body={},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(409, status)
        self.assertEqual(
            {"error": "BLOCK — ORIGINAL REQUEST UNAVAILABLE"},
            json.loads(raw),
        )
        factory = self.controller.adapter_factory
        self.assertIsInstance(factory, ScriptedFactory)
        self.assertEqual(1, len(factory.modes))

    def test_guided_intake_error_status_mapping(self) -> None:
        cookie, csrf = self.bootstrap()
        original_copy = self.controller.guided_intake_copy_for_pro
        cases = (
            (
                GuidedIntakeValidationError("invalid guided intake"),
                400,
            ),
            (
                GuidedIntakeConflictError("conflicting guided intake"),
                409,
            ),
            (
                GuidedIntakeIntegrityError("corrupt guided intake"),
                409,
            ),
            (
                GuidedIntakeBusyError("busy guided intake"),
                409,
            ),
        )
        try:
            for error, expected in cases:
                def fail(current: Exception = error) -> dict[str, object]:
                    raise current

                self.controller.guided_intake_copy_for_pro = fail  # type: ignore[method-assign]
                status, _headers, _raw = self.request(
                    "POST",
                    "/api/guided-intake/copy",
                    body={},
                    cookie=cookie,
                    csrf=csrf,
                    origin=self.server.origin,
                )
                self.assertEqual(expected, status)
        finally:
            self.controller.guided_intake_copy_for_pro = original_copy  # type: ignore[method-assign]

    def test_guided_intake_bounded_local_smoke(self) -> None:
        subprocess.run(
            ("git", "config", "user.email", "smoke@example.test"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "config", "user.name", "Guided Intake Smoke"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "add", "target.txt"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "commit", "-qm", "smoke baseline"),
            cwd=self.repository,
            check=True,
        )
        cookie, csrf = self.bootstrap()
        status, _headers, html = self.request("GET", "/", cookie=cookie)
        self.assertEqual(200, status)
        self.assertIn(b'id="guided-intake-card"', html)

        fixture_root = (
            Path(__file__).resolve().parents[1]
            / "validation"
            / "fixtures"
            / "guided_intake_v0_1"
        )
        original_request = (
            fixture_root / "ambiguous_request.txt"
        ).read_text(encoding="utf-8")
        draft_json = (fixture_root / "pro_draft.json").read_text(
            encoding="utf-8"
        )
        confirmation = json.loads(
            (fixture_root / "user_confirmation.json").read_text(
                encoding="utf-8"
            )
        )

        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/capture",
            body={"original_request": original_request},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        state = json.loads(raw)
        request_id = state["guided_intake"]["request_identity"]["request_id"]
        request_sha256 = state["guided_intake"]["request_identity"]["sha256"]
        self.assertEqual(
            original_request,
            state["guided_intake"]["original_request"],
        )
        self.assertEqual(
            hashlib.sha256(original_request.encode("utf-8")).hexdigest(),
            request_sha256,
        )

        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/import-draft",
            body={
                "draft_json": draft_json,
                "producer_label": "LOCAL_SMOKE_PRO_DRAFT",
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        state = json.loads(raw)
        self.assertEqual(
            "NEEDS USER CONFIRMATION",
            state["guided_intake"]["interpretation"]["gate"],
        )
        self.assertEqual(
            "UNKNOWN",
            state["guided_intake"]["interpretation"]["completion_line"][
                "testability_status"
            ],
        )

        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/freeze",
            body={},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(409, status)
        self.assertIn("INTAKE NOT FREEZABLE", json.loads(raw)["error"])

        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/confirm",
            body=confirmation,
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        state = json.loads(raw)
        self.assertEqual(
            "CLEAR ENOUGH TO FREEZE",
            state["guided_intake"]["interpretation"]["gate"],
        )

        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/freeze",
            body={},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        state = json.loads(raw)
        freeze_sha256 = state["guided_intake"]["freeze"]["sha256"]
        freeze_receipt_sha256 = state["guided_intake"]["freeze"]["receipt"][
            "receipt_sha256"
        ]
        self.assertRegex(freeze_sha256, r"^[0-9a-f]{64}$")

        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/transfer-to-bridge",
            body={},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        state = json.loads(raw)
        self.assertEqual("idle", state["run"]["state"])
        self.assertEqual(
            "TRANSFERRED WITHOUT EXECUTION",
            state["guided_intake"]["transfer_receipt"]["result"],
        )
        self.assertEqual(
            freeze_sha256,
            state["manual_bridge"]["guided_intake_transfer"][
                "freeze_sha256"
            ],
        )

        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/purge",
            body={
                "confirmed": True,
                "request_id": request_id,
                "request_sha256": request_sha256,
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        state = json.loads(raw)
        guided = state["guided_intake"]
        self.assertEqual(
            "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
            guided["state"],
        )
        self.assertIsNone(guided["original_request"])
        self.assertEqual("UNAVAILABLE", guided["raw_source_availability"])
        self.assertEqual("BLOCKED", guided["judgment_reuse"])
        self.assertEqual("BLOCKED", guided["fidelity_evaluation"])
        self.assertEqual("PRESERVED", guided["historical_identity"])
        self.assertEqual(freeze_sha256, guided["freeze"]["sha256"])
        self.assertEqual(
            freeze_receipt_sha256,
            guided["freeze"]["receipt"]["receipt_sha256"],
        )
        self.assertEqual("idle", state["run"]["state"])
        self.assertNotIn(original_request, raw.decode("utf-8"))

        status, _headers, raw = self.request(
            "POST",
            "/api/guided-intake/transfer-to-bridge",
            body={},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(409, status)
        self.assertEqual(
            {"error": "BLOCK — ORIGINAL REQUEST UNAVAILABLE"},
            json.loads(raw),
        )
        self.assertEqual("idle", self.controller.snapshot()["run"]["state"])
        factory = self.controller.adapter_factory
        self.assertIsInstance(factory, ScriptedFactory)
        self.assertEqual(1, len(factory.modes))

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

    def test_contract_import_dom_is_local_only_and_layout_is_bounded(
        self,
    ) -> None:
        cookie, _csrf = self.bootstrap()
        status, _headers, html = self.request("GET", "/", cookie=cookie)
        self.assertEqual(200, status)
        for element_id in (
            "contract-import-card",
            "contract-import-heading",
            "contract-import-state",
            "contract-file",
            "contract-import",
            "contract-use-guided-intake",
            "contract-file-name",
            "contract-preview-status",
            "contract-preview",
            "contract-full-content",
            "contract-import-error",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"'.encode("utf-8"), html)
        self.assertIn(b'accept=".md,.txt"', html)
        self.assertIn(b"Import Contract", html)
        self.assertIn(b"Use in Guided Intake", html)
        normalized_html = " ".join(html.decode("utf-8").split())
        self.assertIn(
            (
                "The file stays in this local tab. Import does not start a "
                "Run, implement anything, or send the Contract anywhere."
            ),
            normalized_html,
        )
        full_content_tag = normalized_html.split(
            'id="contract-full-content"',
            1,
        )[1].split(">", 1)[0]
        self.assertIn("readonly", full_content_tag)
        self.assertIn("hidden", full_content_tag)
        self.assertNotIn("maxlength", full_content_tag)
        guided_intake_action_tag = normalized_html.split(
            'id="contract-use-guided-intake"',
            1,
        )[1].split(">", 1)[0]
        self.assertIn("disabled", guided_intake_action_tag)

        status, _headers, javascript = self.request(
            "GET",
            "/app.js",
            cookie=cookie,
        )
        self.assertEqual(200, status)
        contract_handler = javascript.split(
            b'byId("contract-import").addEventListener',
            1,
        )[1].split(
            b'byId("contract-use-guided-intake").addEventListener',
            1,
        )[0]
        self.assertIn(b"await file.text()", contract_handler)
        self.assertIn(b"content.slice(0, CONTRACT_PREVIEW_CHARACTERS)", contract_handler)
        self.assertNotIn(b"postJSON", contract_handler)
        self.assertNotIn(b"fetch(", contract_handler)
        guided_intake_handler = javascript.split(
            b'byId("contract-use-guided-intake").addEventListener',
            1,
        )[1].split(b'byId("task").addEventListener', 1)[0]
        self.assertIn(b"importedContract.content", guided_intake_handler)
        self.assertIn(b"guidedTransferredOriginalRequest", guided_intake_handler)
        self.assertIn(b'byId("guided-intake-original-request")', guided_intake_handler)
        self.assertNotIn(b"postJSON", guided_intake_handler)
        self.assertNotIn(b"fetch(", guided_intake_handler)
        self.assertNotIn(b'"/api/run"', guided_intake_handler)
        self.assertNotIn(b'"/api/guided-intake/capture"', guided_intake_handler)
        self.assertNotIn(b'"/api/guided-intake/freeze"', guided_intake_handler)

        status, _headers, stylesheet = self.request(
            "GET",
            "/app.css",
            cookie=cookie,
        )
        self.assertEqual(200, status)
        self.assertIn(
            b'input:not([type="checkbox"]):not([type="radio"])',
            stylesheet,
        )
        self.assertIn(b".default-row span", stylesheet)
        self.assertIn(b".primary-value", stylesheet)
        self.assertIn(b".contract-preview", stylesheet)
        self.assertIn(b"max-height: 18rem", stylesheet)
        self.assertIn(b"overflow-wrap: anywhere", stylesheet)

    def test_ordinary_task_precedes_collapsed_advanced_workflows(self) -> None:
        cookie, _csrf = self.bootstrap()
        status, _headers, html = self.request("GET", "/", cookie=cookie)
        self.assertEqual(200, status)
        text = html.decode("utf-8")
        repository_start = text.index('id="repository-heading"')
        bounded_start = text.index('id="bounded-task-card"')
        rail_start = text.index('id="operation-awareness"')
        progress_start = text.index('id="progress-card"')
        result_start = text.index('id="result-card"')
        research_start = text.index('id="advanced-research-mode"')
        contract_mode_start = text.index('id="advanced-contract-mode"')
        ordinary_start = text.index('id="ordinary-contract-card"')
        evidence_start = text.index('id="additional-evidence"')
        audit_start = text.index('id="advanced-audit-mode"')
        guided_start = text.index('id="guided-intake-card"')
        bridge_start = text.index('id="bridge-heading"')
        global_error_start = text.index('id="global-error"')
        self.assertLess(repository_start, bounded_start)
        self.assertLess(bounded_start, rail_start)
        self.assertLess(rail_start, progress_start)
        self.assertLess(progress_start, result_start)
        self.assertLess(result_start, research_start)
        self.assertLess(research_start, contract_mode_start)
        self.assertLess(contract_mode_start, ordinary_start)
        self.assertLess(ordinary_start, evidence_start)
        self.assertLess(evidence_start, audit_start)
        self.assertLess(audit_start, guided_start)
        self.assertLess(guided_start, bridge_start)
        self.assertLess(bridge_start, global_error_start)
        task_card = text[bounded_start:rail_start]
        self.assertIn('id="task"', task_card)
        self.assertIn('id="run"', task_card)
        self.assertIn("Paste or write one bounded task", task_card)
        self.assertIn("Contract fixation is", task_card)
        self.assertNotIn('id="ordinary-contract-card"', task_card)

        for details_id, content_id in (
            ("advanced-research-mode", "advanced-research-content"),
            ("advanced-contract-mode", "advanced-contract-content"),
            ("advanced-audit-mode", "advanced-audit-content"),
        ):
            details_start = text.index(f'id="{details_id}"')
            details_tag = text[details_start : text.index(">", details_start)]
            self.assertNotIn(" open", details_tag)
            content_start = text.index(f'id="{content_id}"')
            content_tag = text[content_start : text.index(">", content_start)]
            self.assertIn(" inert", content_tag)

        research_workflow = text[research_start:contract_mode_start]
        self.assertIn('id="creator-live-cycle-006-card"', research_workflow)
        self.assertIn('id="creator-live-cycle-005-card"', research_workflow)
        contract_workflow = text[contract_mode_start:evidence_start]
        self.assertIn('id="ordinary-contract-card"', contract_workflow)
        ordinary_card = text[ordinary_start:evidence_start]
        for element_id in (
            "ordinary-contract-status",
            "ordinary-contract-file",
            "ordinary-contract-selected-file",
            "ordinary-contract-meaning",
            "ordinary-contract-summary",
            "ordinary-contract-usage-mode",
            "ordinary-contract-can-run",
            "ordinary-contract-authority-message",
            "ordinary-contract-review",
            "ordinary-contract-preserves",
            "ordinary-contract-completion",
            "ordinary-contract-dnt",
            "ordinary-contract-unresolved",
            "ordinary-contract-authority",
            "ordinary-contract-clarification",
            "ordinary-contract-fix",
            "ordinary-contract-error",
            "ordinary-contract-technical",
        ):
            self.assertIn(f'id="{element_id}"', ordinary_card)
        self.assertNotIn("Import Contract", ordinary_card)
        self.assertNotIn("Use in Guided Intake", ordinary_card)
        self.assertNotIn("Capture Original Request", ordinary_card)
        self.assertNotIn("Producer label", ordinary_card)
        self.assertNotIn("Draft JSON", ordinary_card)
        self.assertIn("View fixed Contract meaning", ordinary_card)
        self.assertIn("Current usage mode", ordinary_card)
        self.assertIn("Can authorize a bounded Run", ordinary_card)
        review_id = ordinary_card.index('id="ordinary-contract-review"')
        review_start = ordinary_card.rfind("<", 0, review_id)
        review_tag = ordinary_card[review_start : ordinary_card.index(">", review_id)]
        self.assertTrue(review_tag.startswith("<details "))
        self.assertNotIn(" open", review_tag)
        for internal_term in (
            "PRESERVED",
            "TESTABLE",
            "authority_claim",
            "schema_version",
            "Request ID",
            "Draft ID",
            "Freeze ID",
            "SHA-256",
            "Producer label",
            "Draft JSON",
        ):
            self.assertNotIn(internal_term, ordinary_card)
        self.assertIn("Producer label", text[audit_start:])
        self.assertIn("Draft JSON", text[audit_start:])

        status, _headers, javascript = self.request(
            "GET", "/app.js", cookie=cookie
        )
        self.assertEqual(200, status)
        ordinary_handler = javascript.split(
            b'byId("ordinary-contract-file").addEventListener', 1
        )[1].split(b"function contractFileSelectionChanged", 1)[0]
        self.assertIn(b"await file.arrayBuffer()", ordinary_handler)
        self.assertIn(b'crypto.subtle.digest("SHA-256"', javascript)
        self.assertIn(
            b"recordOrdinarySelectedFilename(file.name, panel?.operation_revision)",
            ordinary_handler,
        )
        self.assertIn(b"bytes?.fill(0)", ordinary_handler)
        self.assertIn(b'byId("ordinary-contract-file").value = ""', ordinary_handler)
        self.assertNotIn(b"file.text()", ordinary_handler)
        self.assertNotIn(b"guided-intake-original-request", ordinary_handler)
        self.assertNotIn(b'"/api/run"', ordinary_handler)
        self.assertNotIn(b"innerHTML", javascript)
        self.assertIn(b"window.setTimeout(refresh, 750)", javascript)
        self.assertIn(b"revision < ordinaryLastRevision && requestActive", javascript)
        self.assertIn(b"disableStateChangingControls();", javascript)
        self.assertIn(b'byId("ordinary-contract-question").focus()', javascript)
        self.assertIn(b'byId("ordinary-contract-success").focus()', javascript)
        self.assertIn(b'byId("ordinary-contract-error").focus()', javascript)

    def test_operation_awareness_dom_order_copy_and_boundaries(self) -> None:
        cookie, _csrf = self.bootstrap()
        status, _headers, html = self.request("GET", "/", cookie=cookie)
        self.assertEqual(200, status)
        text = html.decode("utf-8")
        repository_start = text.index('id="repository-heading"')
        task_start = text.index('id="bounded-task-card"')
        rail_start = text.index('id="operation-awareness"')
        progress_start = text.index('id="progress-card"')
        result_start = text.index('id="result-card"')
        research_start = text.index('id="advanced-research-mode"')
        contract_mode_start = text.index('id="advanced-contract-mode"')
        contract_start = text.index('id="ordinary-contract-card"')
        evidence_start = text.index('id="additional-evidence"')
        transplant_start = text.index('id="intelligence-transplant-card"')
        advanced_start = text.index('id="advanced-audit-mode"')
        bridge_start = text.index('id="bridge-heading"')
        self.assertLess(repository_start, task_start)
        self.assertLess(task_start, rail_start)
        self.assertLess(rail_start, progress_start)
        self.assertLess(progress_start, result_start)
        self.assertLess(result_start, research_start)
        self.assertLess(research_start, contract_mode_start)
        self.assertLess(contract_mode_start, contract_start)
        self.assertLess(contract_start, evidence_start)
        self.assertLess(evidence_start, transplant_start)
        self.assertLess(transplant_start, advanced_start)
        self.assertLess(advanced_start, bridge_start)
        main_operation = text[repository_start:research_start]
        self.assertNotIn("Intelligence Transplant Run", main_operation)
        self.assertNotIn('id="ordinary-contract-card"', main_operation)
        self.assertNotIn("Import Contract", main_operation)
        self.assertNotIn("Guided Intake", main_operation)
        evidence_tag = text[evidence_start : text.index(">", evidence_start)]
        self.assertNotIn(" open", evidence_tag)
        for details_id, content_id in (
            ("advanced-research-mode", "advanced-research-content"),
            ("advanced-contract-mode", "advanced-contract-content"),
            ("advanced-audit-mode", "advanced-audit-content"),
        ):
            details_start = text.index(f'id="{details_id}"')
            details_tag = text[details_start : text.index(">", details_start)]
            self.assertNotIn(" open", details_tag)
            content_start = text.index(f'id="{content_id}"')
            content_tag = text[content_start : text.index(">", content_start)]
            self.assertIn(" inert", content_tag)
        stages = re.findall(r'data-operation-stage="([^"]+)"', text)
        self.assertEqual(["task", "run", "approval", "result"], stages)
        for stage in stages:
            self.assertIn(f'data-operation-stage="{stage}"', text)
            self.assertIn(f'id="operation-{stage}-status"', text)
        self.assertNotIn('data-operation-stage="contract"', text)
        self.assertNotIn('id="operation-contract-status"', text)
        contract_workflow = text[contract_mode_start:evidence_start]
        self.assertIn('id="ordinary-contract-card"', contract_workflow)
        self.assertNotIn("Import Contract", contract_workflow)
        audit_workflow = text[advanced_start:]
        self.assertIn("Import Contract", audit_workflow)
        self.assertIn("Guided Intake", audit_workflow)
        self.assertIn('id="bridge-heading"', audit_workflow)
        for element_id in (
            "operation-current",
            "operation-happening",
            "operation-action",
            "operation-next",
            "result-execution",
            "result-file-change",
            "result-verification",
            "result-verification-reason",
        ):
            self.assertIn(f'id="{element_id}"', text)
        for exact_copy in (
            "Allow this change once",
            "Allows only this request in the current Run.",
            "Use for this repository",
            "Saves permission for this repository, action, and exact path in",
            "Future proposed content may differ",
            "may reuse it without showing this diff again",
            "This diff is not the",
            "only allowed future diff.",
            "It does not bind future content to the diff that created",
            "Deny and stop this Run",
            "No requested file change will be approved.",
        ):
            self.assertIn(exact_copy, text)
        self.assertNotIn("Save this exact permission", text)

        status, _headers, javascript = self.request(
            "GET", "/app.js", cookie=cookie
        )
        self.assertEqual(200, status)
        self.assertIn(b'button?.setAttribute("aria-current", "step")', javascript)
        self.assertIn(b'"(prefers-reduced-motion: reduce)"', javascript)
        self.assertIn(b'"Wait \xe2\x80\x94 no action is needed."', javascript)
        self.assertIn(b'"Nothing \xe2\x80\x94 this Run is complete."', javascript)
        self.assertNotIn(b'includes("successfully")', javascript)

        status, _headers, stylesheet = self.request(
            "GET", "/app.css", cookie=cookie
        )
        self.assertEqual(200, status)
        self.assertIn(b".operation-awareness", stylesheet)
        self.assertIn(b"position: sticky", stylesheet)
        self.assertIn(b'.operation-stage[aria-current="step"]', stylesheet)
        self.assertIn(b"grid-template-columns: repeat(4, minmax(0, 1fr))", stylesheet)

    def test_ordinary_contract_endpoints_are_private_and_strict(self) -> None:
        for path in ORDINARY_CONTRACT_POST_ROUTES:
            status, _headers, _raw = self.request(
                "POST", path, body={}, origin=self.server.origin
            )
            self.assertEqual(401, status)

        cookie, csrf = self.bootstrap()
        raw_duplicate = (
            b'{"error_id":"OUP-ERR-a","error_id":"OUP-ERR-b",'
            b'"idempotency_key":"00000000-0000-4000-8000-000000000000"}'
        )
        status, _headers, raw = self.request(
            "POST",
            "/api/ordinary-contract/error/dismiss",
            raw_body=raw_duplicate,
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(400, status)
        body = json.loads(raw)
        self.assertIsInstance(body["error"], dict)
        self.assertIn("ordinary_contract", body)
        self.assertIsNotNone(body["error"]["error_id"])
        self.assertEqual(
            body["error"]["error_id"],
            body["ordinary_contract"]["action_error"]["error_id"],
        )

        status, _headers, raw = self.request(
            "GET", "/api/state", cookie=cookie
        )
        self.assertEqual(200, status)
        persisted = json.loads(raw)["ordinary_contract"]["action_error"]
        self.assertEqual(body["error"]["error_id"], persisted["error_id"])
        self.assertEqual(
            "PREP_SOURCE_TRANSPORT_MISMATCH",
            persisted["code"],
        )

        oversized = b'{"padding":"' + (b"x" * 131_072) + b'"}'
        status, _headers, raw = self.request(
            "POST",
            "/api/ordinary-contract/prepare",
            raw_body=oversized,
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(413, status)
        body = json.loads(raw)
        self.assertEqual("PREP_SOURCE_TOO_LARGE", body["error"]["code"])
        self.assertIsNotNone(body["error"]["error_id"])
        self.assertEqual(
            body["error"]["error_id"],
            body["ordinary_contract"]["action_error"]["error_id"],
        )

    def test_ordinary_contract_http_golden_prepare_and_fix(self) -> None:
        subprocess.run(
            ("git", "config", "user.email", "ordinary@example.test"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "config", "user.name", "Ordinary Contract Smoke"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(("git", "add", "target.txt"), cwd=self.repository, check=True)
        subprocess.run(
            ("git", "commit", "-qm", "ordinary baseline"),
            cwd=self.repository,
            check=True,
        )
        cookie, csrf = self.bootstrap()
        status, _headers, raw = self.request("GET", "/api/state", cookie=cookie)
        self.assertEqual(200, status)
        initial = json.loads(raw)
        panel = initial["ordinary_contract"]
        source = (
            Path(__file__).parent
            / "fixtures"
            / "ordinary_user_path_v0_1"
            / "Decision_OS_Ordinary_User_Path_Contract_v0.1_APPROVED_CANDIDATE.md"
        ).read_bytes()
        status, _headers, raw = self.request(
            "POST",
            "/api/ordinary-contract/prepare",
            body={
                "filename": "Decision_OS_Ordinary_User_Path_Contract_v0.1_APPROVED_CANDIDATE.md",
                "source_base64": base64.b64encode(source).decode("ascii"),
                "source_byte_size": len(source),
                "source_sha256": hashlib.sha256(source).hexdigest(),
                "expected_repository_identity": panel["repository_identity"],
                "expected_active_request_id": panel["technical_details"][
                    "active_request_id"
                ],
                "idempotency_key": str(uuid.uuid4()),
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        prepared = json.loads(raw)["ordinary_contract"]
        self.assertEqual("REVIEW_READY", prepared["state"])
        self.assertEqual("Ready to fix", prepared["status_label"])
        details = prepared["technical_details"]
        status, _headers, raw = self.request(
            "POST",
            "/api/ordinary-contract/fix",
            body={
                "preparation_id": prepared["preparation_id"],
                "expected_repository_identity": prepared[
                    "repository_identity"
                ],
                "expected_source_sha256": prepared["source_identity"][
                    "sha256"
                ],
                "expected_request_id": details["request_id"],
                "expected_draft_id": details["draft_id"],
                "expected_interpretation_sha256": details[
                    "interpretation_sha256"
                ],
                "idempotency_key": str(uuid.uuid4()),
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        fixed = json.loads(raw)["ordinary_contract"]
        self.assertEqual("FIXED", fixed["state"])
        factory = self.controller.adapter_factory
        self.assertIsInstance(factory, ScriptedFactory)
        self.assertEqual(1, len(factory.modes))

    def test_failed_ordinary_prepare_hides_prior_review_across_poll(self) -> None:
        subprocess.run(
            ("git", "config", "user.email", "ordinary@example.test"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(
            ("git", "config", "user.name", "Ordinary Contract Smoke"),
            cwd=self.repository,
            check=True,
        )
        subprocess.run(("git", "add", "target.txt"), cwd=self.repository, check=True)
        subprocess.run(
            ("git", "commit", "-qm", "ordinary baseline"),
            cwd=self.repository,
            check=True,
        )
        cookie, csrf = self.bootstrap()
        status, _headers, raw = self.request("GET", "/api/state", cookie=cookie)
        self.assertEqual(200, status)
        initial = json.loads(raw)["ordinary_contract"]
        source = (
            Path(__file__).parent
            / "fixtures"
            / "ordinary_user_path_v0_1"
            / "Decision_OS_Ordinary_User_Path_Contract_v0.1_APPROVED_CANDIDATE.md"
        ).read_bytes()
        status, _headers, raw = self.request(
            "POST",
            "/api/ordinary-contract/prepare",
            body={
                "filename": "Decision_OS_Ordinary_User_Path_Contract_v0.1_APPROVED_CANDIDATE.md",
                "source_base64": base64.b64encode(source).decode("ascii"),
                "source_byte_size": len(source),
                "source_sha256": hashlib.sha256(source).hexdigest(),
                "expected_repository_identity": initial["repository_identity"],
                "expected_active_request_id": None,
                "idempotency_key": str(uuid.uuid4()),
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        prepared = json.loads(raw)["ordinary_contract"]
        details = prepared["technical_details"]
        status, _headers, raw = self.request(
            "POST",
            "/api/ordinary-contract/fix",
            body={
                "preparation_id": prepared["preparation_id"],
                "expected_repository_identity": prepared["repository_identity"],
                "expected_source_sha256": prepared["source_identity"]["sha256"],
                "expected_request_id": details["request_id"],
                "expected_draft_id": details["draft_id"],
                "expected_interpretation_sha256": details[
                    "interpretation_sha256"
                ],
                "idempotency_key": str(uuid.uuid4()),
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        guided = self.controller._require_guided_intake()
        before_native_state = guided.store.load_state()
        before_events = guided.store.read_events()
        unsupported = b"# Ordinary User Path Contract Fixation Closure v0.1\n"

        status, _headers, raw = self.request(
            "POST",
            "/api/ordinary-contract/prepare",
            body={
                "filename": (
                    "Decision_OS_Ordinary_User_Path_Contract_"
                    "Fixation_Closure_v0.1.md"
                ),
                "source_base64": base64.b64encode(unsupported).decode("ascii"),
                "source_byte_size": len(unsupported),
                "source_sha256": hashlib.sha256(unsupported).hexdigest(),
                "expected_repository_identity": prepared["repository_identity"],
                "expected_active_request_id": details["request_id"],
                "idempotency_key": str(uuid.uuid4()),
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(422, status, raw.decode("utf-8", errors="replace"))
        failed = json.loads(raw)["ordinary_contract"]
        status, _headers, raw = self.request("GET", "/api/state", cookie=cookie)
        self.assertEqual(200, status)
        polled = json.loads(raw)["ordinary_contract"]
        for panel in (failed, polled):
            self.assertEqual("CANNOT_FIX_SAFELY", panel["state"])
            self.assertIsNone(panel["review"])
            self.assertIsNone(panel["clarification"])
            self.assertNotIn("FIX_CONTRACT", panel["allowed_actions"])
            self.assertEqual(
                "PREP_UNSUPPORTED_CONTRACT_ROLE",
                panel["action_error"]["code"],
            )
        self.assertEqual(failed["action_error"], polled["action_error"])
        self.assertEqual(before_native_state, guided.store.load_state())
        self.assertEqual(before_events, guided.store.read_events())

    def test_guided_intake_dom_and_authority_boundary_are_present(self) -> None:
        cookie, _csrf = self.bootstrap()
        status, _headers, html = self.request("GET", "/", cookie=cookie)

        self.assertEqual(200, status)
        for element_id in (
            "guided-intake-card",
            "guided-intake-heading",
            "guided-intake-state",
            "guided-intake-authority-explanation",
            "guided-intake-original-request",
            "guided-intake-capture",
            "guided-intake-original-exact",
            "guided-intake-objective",
            "guided-intake-objective-atoms",
            "guided-intake-completion-line",
            "guided-intake-completion-checks",
            "guided-intake-do-not-touch",
            "guided-intake-unknown",
            "guided-intake-confirmation-history",
            "guided-intake-copy",
            "guided-intake-copy-output",
            "guided-intake-fidelity-evaluation",
            "guided-intake-producer-label",
            "guided-intake-draft-json",
            "guided-intake-import-draft",
            "guided-intake-question",
            "guided-intake-answer",
            "guided-intake-resulting-delta",
            "guided-intake-confirm",
            "guided-intake-freeze",
            "guided-intake-purge-confirm",
            "guided-intake-purge",
            "guided-intake-purge-status",
            "guided-intake-raw-source-availability",
            "guided-intake-judgment-reuse",
            "guided-intake-transfer",
            "guided-intake-error",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"'.encode("utf-8"), html)
        self.assertIn(b"Original Request", html)
        self.assertIn(b"Objective", html)
        self.assertIn(b"Completion Line", html)
        self.assertIn(b"Do Not Touch", html)
        self.assertIn(b"UNKNOWN", html)
        self.assertIn(b"exact support and byte ranges", html)
        self.assertIn(b"Completion checks and evidence sources", html)
        self.assertIn(b"Forward-only confirmation history", html)
        normalized_html = " ".join(html.decode("utf-8").split())
        self.assertIn(
            (
                "Purge applies only to the exact current Request identity "
                "shown above. It makes the raw Original Request unavailable "
                "and blocks transfer, judgment reuse, and fidelity "
                "evaluation. Historical hashes and receipts remain preserved. "
                "Purge grants no execution authority and never starts a Run."
            ),
            normalized_html,
        )
        self.assertIn(
            b"I explicitly confirm purge of this exact Original Request.",
            html,
        )
        self.assertIn(b"Purge Exact Original Request", html)
        self.assertIn(
            "INTERPRETATION ONLY — NO EXECUTION AUTHORITY".encode("utf-8"),
            html,
        )
        self.assertIn(b'maxlength="65536"', html)

    def test_bridge_import_cap_preserves_legacy_cap_and_exact_bytes(
        self,
    ) -> None:
        cookie, csrf = self.bootstrap()
        status, _headers, raw = self.request(
            "POST",
            "/api/run",
            body={"task": "x" * (64 * 1024)},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(413, status)
        self.assertEqual({"error": "Request is too large."}, json.loads(raw))

        self.start_bridge_session(cookie, csrf)
        exact_payload = (b"p" * 64_155) + b"\r\n"
        self.assertEqual(64_157, len(exact_payload))
        hostile_source = 'design<script>alert("x")</script>&.md'
        status, _headers, raw = self.request(
            "POST",
            "/api/bridge/import",
            body={
                "mode": "BYTE_EXACT_FILE_IMPORT",
                "selected_role": "PRO_DESIGN",
                "source_path_or_label": hostile_source,
                "payload_base64": base64.b64encode(exact_payload).decode("ascii"),
                "metadata": pro_design_metadata(),
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )

        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))
        status, _headers, raw = self.request(
            "GET",
            "/api/state",
            cookie=cookie,
        )
        self.assertEqual(200, status)
        self.assertNotIn(b"<script>", raw)
        self.assertIn(b"\\u003cscript\\u003e", raw)
        self.assertIn(b"\\u0026", raw)
        state = json.loads(raw)
        identity = state["manual_bridge"]["imports"][0]
        self.assertEqual(hostile_source, identity["source_path_or_label"])
        self.assertEqual(
            hashlib.sha256(exact_payload).hexdigest(),
            identity["artifact_content_hash"],
        )
        self.assertEqual("BYTE_EXACT_FILE_IMPORT", identity["import_mode"])

        status, _headers, raw = self.request(
            "POST",
            "/api/bridge/import",
            body={
                "mode": "BYTE_EXACT_FILE_IMPORT",
                "selected_role": "PRO_DESIGN",
                "source_path_or_label": "invalid-base64.md",
                "payload_base64": "%%%not-base64%%%",
                "metadata": pro_design_metadata(),
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(400, status)
        self.assertEqual(
            {"error": "Byte-exact import payload is invalid."},
            json.loads(raw),
        )

        status, _headers, raw = self.request(
            "POST",
            "/api/bridge/import",
            body={
                "mode": "BYTE_EXACT_FILE_IMPORT",
                "selected_role": "PRO_DESIGN",
                "source_path_or_label": "oversize.md",
                "payload_base64": "AAAA",
                "metadata": pro_design_metadata(),
            },
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
            declared_content_length=(2 * 1024 * 1024) + 1,
        )
        self.assertEqual(413, status)
        self.assertEqual({"error": "Request is too large."}, json.loads(raw))

    def test_manual_bridge_dom_and_independent_results_are_present(self) -> None:
        cookie, _csrf = self.bootstrap()
        status, _headers, html = self.request("GET", "/", cookie=cookie)

        self.assertEqual(200, status)
        for element_id in (
            "bridge-heading",
            "bridge-start",
            "bridge-copy",
            "bridge-role",
            "bridge-file",
            "bridge-paste",
            "bridge-identities",
            "bridge-generate-handoff",
            "bridge-generate-receipt",
            "bridge-generate-manifest",
            "bridge-replay-run",
            "bridge-protocol-result",
            "bridge-product-result",
            "bridge-replay-result",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"'.encode("utf-8"), html)
        self.assertIn(b"Protocol Result", html)
        self.assertIn(b"Product Result", html)
        self.assertIn(b"Replay Result", html)
        self.assertIn(
            b"BUILDER EVIDENCE ONLY / INDEPENDENT AUDIT REQUIRED",
            html,
        )

    def test_intelligence_transplant_dom_is_read_only_and_boundary_exact(
        self,
    ) -> None:
        cookie, _csrf = self.bootstrap()
        status, _headers, html = self.request("GET", "/", cookie=cookie)
        self.assertEqual(200, status)
        for element_id in (
            "intelligence-transplant-card",
            "intelligence-transplant-heading",
            "intelligence-transplant-gate",
            "intelligence-transplant-run-id",
            "intelligence-transplant-execution-status",
            "intelligence-transplant-delta-state",
            "intelligence-transplant-structural-validation",
            "intelligence-transplant-authority-provenance",
            "intelligence-transplant-cryptographic-provenance",
            "intelligence-transplant-generalized-transplant",
            "intelligence-transplant-missing-evidence",
            "intelligence-transplant-next-action",
            "intelligence-transplant-not-allowed-next",
            "intelligence-transplant-active-cap",
            "intelligence-transplant-evidence-objects",
            "intelligence-transplant-lineage",
            "intelligence-transplant-error",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"'.encode("utf-8"), html)
        normalized_html = " ".join(html.decode("utf-8").split())
        self.assertIn("Structural Validation", normalized_html)
        self.assertIn("Authority Provenance", normalized_html)
        self.assertIn("MANUAL OWNER ATTESTED", normalized_html)
        self.assertIn("Cryptographic Provenance", normalized_html)
        self.assertIn("NOT ESTABLISHED", normalized_html)
        self.assertIn(
            (
                "Local manual authority receipt —not cryptographic "
                "identity proof."
            ),
            normalized_html,
        )
        section = normalized_html.split(
            'id="intelligence-transplant-card"',
            1,
        )[1].split("</section>", 1)[0]
        self.assertNotIn("<button", section)

        status, _headers, javascript = self.request(
            "GET",
            "/app.js",
            cookie=cookie,
        )
        self.assertEqual(200, status)
        self.assertNotIn(b'postJSON("/api/intelligence-transplant', javascript)

    def test_one_active_run_and_browser_reconnect(self) -> None:
        cookie, csrf = self.bootstrap()
        status, _headers, _raw = self.request(
            "POST",
            "/api/run",
            body={
                "task": "Modify target.txt once.",
                "task_mode": "contract",
            },
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
        self.assertEqual("contract", first["run"]["task_mode"])

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

    def test_authenticated_stage_b_route_runs_exactly_one_continuation(
        self,
    ) -> None:
        self.controller.adapter_factory = ScriptedFactory(
            "read_only",
            "read_only",
        )
        cookie, csrf = self.bootstrap()

        status, _headers, raw = self.request(
            "POST",
            "/api/compound-run",
            body={"request": stage_b_request().as_dict()},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))

        deadline = time.monotonic() + 5
        snapshot = None
        while time.monotonic() < deadline:
            status, _headers, raw = self.request(
                "GET",
                "/api/state",
                cookie=cookie,
            )
            self.assertEqual(200, status)
            snapshot = json.loads(raw)
            if snapshot["compound_loop"]["state"] == "COMPLETE":
                break
            time.sleep(0.01)
        self.assertIsNotNone(snapshot)
        self.assertEqual("COMPLETE", snapshot["compound_loop"]["state"])
        self.assertEqual(2, len(snapshot["compound_loop"]["runs"]))
        self.assertEqual(
            1,
            snapshot["compound_loop"]["automatic_continuations_started"],
        )
        self.assertEqual(2, snapshot["run"]["continuation"]["run_number"])

        status, _headers, _raw = self.request(
            "POST",
            "/api/compound-run",
            body={"request": stage_b_request().as_dict(), "extra": True},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(400, status)

    def test_authenticated_stage_c_route_stops_after_no_progress(self) -> None:
        self.controller.adapter_factory = ScriptedFactory(
            "read_only",
            "read_only",
            "read_only",
            "read_only",
        )
        cookie, csrf = self.bootstrap()

        status, _headers, raw = self.request(
            "POST",
            "/api/compound-loop",
            body={"request": stage_c_request().as_dict()},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(200, status, raw.decode("utf-8", errors="replace"))

        deadline = time.monotonic() + 5
        snapshot = None
        while time.monotonic() < deadline:
            status, _headers, raw = self.request(
                "GET",
                "/api/state",
                cookie=cookie,
            )
            self.assertEqual(200, status)
            snapshot = json.loads(raw)
            if snapshot["compound_loop"]["state"] == "TERMINAL":
                break
            time.sleep(0.01)
        self.assertIsNotNone(snapshot)
        self.assertEqual("HOLD", snapshot["compound_loop"]["outcome"])
        self.assertEqual(1, len(snapshot["compound_loop"]["runs"]))
        self.assertEqual(0, len(snapshot["compound_loop"]["automatic_tasks"]))
        self.assertEqual(1, snapshot["run"]["continuation"]["run_number"])
        self.assertEqual(3, len(self.controller.adapter_factory.modes))

        status, _headers, _raw = self.request(
            "POST",
            "/api/compound-loop",
            body={"request": stage_c_request().as_dict(), "extra": True},
            cookie=cookie,
            csrf=csrf,
            origin=self.server.origin,
        )
        self.assertEqual(400, status)

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
        state = json.loads(raw)
        defaults_text = json.dumps(state["defaults"])
        self.assertNotIn("decision_key", defaults_text)
        self.assertNotIn("rule_hash", defaults_text)
        self.assertNotIn("event_hash", defaults_text)
        self.assertNotIn("request_id", defaults_text)
        self.assertNotIn("credential", defaults_text)
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
    def test_creator_live_terminal_render_removes_all_start_paths(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required for client behavior tests.")
        static_root = (
            Path(__file__).resolve().parents[1]
            / "decision_os"
            / "companion"
            / "static"
        )
        html = (static_root / "index.html").read_text(encoding="utf-8")
        javascript = (static_root / "app.js").read_text(encoding="utf-8")
        self.assertIn("TERMINAL — NO RETRY OR REPLACEMENT", html)
        self.assertNotIn("832 bytes · unavailable", html)
        self.assertNotIn("856 bytes · unavailable", html)
        self.assertNotIn("2026-08-05T08:47:00Z", html)
        harness = textwrap.dedent(
            r"""
            "use strict";
            const assert = require("assert");
            const fs = require("fs");
            const vm = require("vm");
            const source = fs.readFileSync(process.argv[1], "utf8");
            const renderStart = source.indexOf("function renderCreatorLiveCycle005");
            const renderEnd = source.indexOf("\nfunction render(state)", renderStart);
            const clickStart = source.indexOf(
              'optionalById("creator-live-start")?.addEventListener("click"'
            );
            const clickEnd = source.indexOf(
              '\n\nbyId("new-run").addEventListener',
              clickStart,
            );
            assert(renderStart >= 0 && renderEnd > renderStart);
            assert(clickStart >= 0 && clickEnd > clickStart);

            const ids = [
              "creator-live-start", "creator-live-terminal-label",
              "creator-live-cycle-005-status", "creator-live-revision",
              "creator-live-contract", "creator-live-contract-authority",
              "creator-live-freeze-authority", "creator-live-authorization",
              "creator-live-implementation-authorization", "creator-live-runtime",
              "creator-live-run-1", "creator-live-run-2",
              "creator-live-attempt-policy", "creator-live-historical-boundary",
              "creator-live-p0", "creator-live-binding-sha256",
              "creator-live-stage", "creator-live-failure-code",
              "creator-live-proof-attempt", "creator-live-proof-as-of",
              "creator-live-journal-sha256", "creator-live-anchor-sha256",
              "creator-live-readback-sha256", "creator-live-output-artifact",
              "creator-live-compiler",
            ];
            const elements = Object.fromEntries(ids.map((id) => [id, {
              id, textContent: "", hidden: false, disabled: false, listener: null,
              addEventListener(_kind, listener) { this.listener = listener; },
            }]));
            let postCount = 0;
            const context = {
              byId: (id) => elements[id],
              optionalById: (id) => elements[id] || null,
              setText: (id, value) => { elements[id].textContent = String(value); },
              latestState: null,
              requestActive: false,
              postJSON: async () => { postCount += 1; return null; },
            };
            vm.createContext(context);
            vm.runInContext(source.slice(renderStart, renderEnd), context);
            const cycle = {
              state: "FAILED",
              stage: "A3_REUSE",
              storage_occupied: true,
              start_allowed: false,
              p0: { ready: false, failure_code: "CYCLE_005_ATTEMPT_EXISTS" },
              launch_binding_sha256: "a".repeat(64),
              identities: {
                revision: "b".repeat(40),
                contract_identity: "NOT_DURABLY_PERSISTED",
                ordinary_contract_execution_authority: "NOT_DURABLY_PERSISTED",
                guided_intake_freeze_authority: "NOT_DURABLY_PERSISTED",
                runtime: {
                  account_type: "chatgpt", model: "gpt-5.6-sol",
                  reasoning_effort: "ultra", service_tier: "priority",
                  codex_cli_version: "0.146.0-alpha.3.1",
                },
                run_1_task: {
                  byte_count: "NOT_DURABLY_PERSISTED", sha256: "c".repeat(64),
                },
                run_2_task: {
                  byte_count: "NOT_DURABLY_PERSISTED",
                  sha256: "NOT_DURABLY_PERSISTED",
                },
                cycle_authorization_observed_at: "2026-08-05T06:22:00Z",
                implementation_authorization_observed_at: "NOT_DURABLY_PERSISTED",
                historical_boundary: "NOT_DURABLY_PERSISTED",
                launch_binding_sha256: "a".repeat(64),
                proof_attempt_id: "proof-fixture",
                proof_as_of: "2026-08-05T11:24:40.255812Z",
                journal_sha256: "d".repeat(64), anchor_sha256: "e".repeat(64),
                readback_sha256: "f".repeat(64), terminal_stage: "A3_REUSE",
                failure_code: "A3_EXACT_STRUCTURE_MISSING",
                retry_count: "NOT_DURABLY_PERSISTED",
                replacement_count: "NOT_DURABLY_PERSISTED",
                output_artifact: "NOT_DURABLY_PERSISTED",
                compiler: "NOT_DURABLY_PERSISTED",
              },
            };
            context.renderCreatorLiveCycle005(cycle);
            assert.strictEqual(elements["creator-live-start"].hidden, true);
            assert.strictEqual(elements["creator-live-start"].disabled, true);
            assert.strictEqual(elements["creator-live-terminal-label"].hidden, false);
            assert.strictEqual(
              elements["creator-live-contract"].textContent,
              "NOT_DURABLY_PERSISTED",
            );
            assert.strictEqual(
              elements["creator-live-run-1"].textContent,
              `NOT_DURABLY_PERSISTED · ${"c".repeat(64)}`,
            );
            assert.strictEqual(
              elements["creator-live-run-2"].textContent,
              "NOT_DURABLY_PERSISTED",
            );
            assert.strictEqual(
              elements["creator-live-attempt-policy"].textContent,
              "NOT_DURABLY_PERSISTED",
            );
            context.latestState = { creator_live_cycle_005: cycle };
            vm.runInContext(source.slice(clickStart, clickEnd), context);
            elements["creator-live-start"].disabled = false;
            Promise.resolve(elements["creator-live-start"].listener()).then(() => {
              assert.strictEqual(postCount, 0);
            }).catch((error) => { console.error(error); process.exitCode = 1; });
            """
        )
        completed = subprocess.run(
            [node, "-e", harness, str(static_root / "app.js")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            0,
            completed.returncode,
            msg=f"Node terminal Cycle 005 harness failed:\n{completed.stdout}{completed.stderr}",
        )

    def test_operation_awareness_state_transition_harness(self) -> None:
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
            const source = fs.readFileSync(process.argv[2], "utf8");
            const operationStart = source.indexOf("function statusLabel");
            const operationEnd = source.indexOf("\nfunction formatNumber", operationStart);
            const resultStart = source.indexOf("function visibleResponse");
            const resultEnd = source.indexOf("\nfunction renderApproval", resultStart);
            assert(operationStart >= 0 && operationEnd > operationStart);
            assert(resultStart >= 0 && resultEnd > resultStart);

            class ClassList {
              constructor(initial = []) { this.values = new Set(initial); }
              contains(value) { return this.values.has(value); }
              toggle(value, force) {
                if (force) this.values.add(value);
                else this.values.delete(value);
              }
            }

            class Element {
              constructor(id = "") {
                this.id = id;
                this.value = "";
                this.textContent = "";
                this.disabled = false;
                this.dataset = {};
                this.classList = new ClassList();
                this.attributes = new Map();
                this.focusCalls = [];
                this.scrollIntoViewCalls = [];
                this.open = false;
                this.inert = false;
                this.children = [];
              }
              setAttribute(name, value) { this.attributes.set(name, String(value)); }
              removeAttribute(name) { this.attributes.delete(name); }
              getAttribute(name) { return this.attributes.get(name) ?? null; }
              focus(options) { this.focusCalls.push(options); }
              scrollIntoView(options) { this.scrollIntoViewCalls.push(options); }
              replaceChildren(...children) { this.children = children; }
            }

            const stages = ["task", "run", "approval", "result"];
            const ids = [
              "approval-heading", "approval-overlay", "bounded-task-card",
              "new-run",
              "operation-action", "operation-current", "operation-happening",
              "operation-next", "progress", "progress-card", "progress-heading",
              "run-activity", "run-activity-age", "run-activity-progress",
              "run-activity-status",
              "result", "result-card", "result-execution", "result-file-change",
              "result-heading", "result-state", "result-verification",
              "result-verification-reason", "run", "run-state", "task", "task-heading",
              ...stages.map((stage) => `operation-${stage}-status`),
            ];
            const elements = new Map(ids.map((id) => [id, new Element(id)]));
            for (const id of ["approval-overlay", "progress-card", "result-card"]) {
              elements.get(id).classList.toggle("hidden", true);
            }
            const stageButtons = stages.map((stage) => {
              const button = new Element(`stage-${stage}`);
              button.dataset.operationStage = stage;
              return button;
            });
            assert.deepStrictEqual(
              stageButtons.map((button) => button.dataset.operationStage),
              ["task", "run", "approval", "result"],
            );
            assert.strictEqual(elements.has("operation-contract-status"), false);
            let reducedMotion = false;
            let now = 100000;
            const sandbox = {
              console,
              Date: { now: () => now },
              document: {
                createElement: () => new Element(),
                querySelectorAll: (selector) =>
                  selector === "[data-operation-stage]" ? stageButtons : [],
              },
              globalThis: {
                matchMedia: () => ({ matches: reducedMotion }),
              },
              latestState: null,
              operationApprovalResponsePending: false,
              operationApprovalWasVisible: false,
              operationApprovalSeen: false,
              operationContinuingAfterApproval: false,
              preparedContractTaskBinding: null,
              preparedContractTaskStarter: null,
              operationLastApprovalKey: null,
              operationStartPending: false,
              operationTerminalTransitioned: false,
              runObservedStartedAt: null,
              runObservedProgressAt: null,
              runObservedProgressSignature: null,
              runObservedLatestProgress: "",
              runActivityVisible: false,
              CONTRACT_TASK_MARKER: "Task to perform:",
              CONTRACT_TASK_PREFIX:
                "Perform only the bounded task defined by this fixed ordinary Contract context.",
              EXECUTION_AUTHORITY_INTERPRETATION_ONLY: "INTERPRETATION_ONLY",
              EXECUTION_AUTHORITY_BOUNDED: "BOUNDED_EXECUTION_AUTHORIZED",
              EXECUTION_AUTHORITY_UNKNOWN: "UNKNOWN",
              INTERPRETATION_ONLY_MESSAGE:
                "This Contract is fixed for interpretation only. It cannot authorize a Run.",
              UNKNOWN_EXECUTION_AUTHORITY_MESSAGE:
                "Execution authority is not established for this Contract.",
              byId: (id) => elements.get(id),
              setText: (id, value) => {
                elements.get(id).textContent = value == null ? "" : String(value);
              },
              setHidden: (id, hidden) => elements.get(id).classList.toggle("hidden", hidden),
              renderActions: () => {},
              renderCopyResponse: () => {},
              renderReadEvidence: () => {},
              renderRuntime: () => {},
            };
            vm.createContext(sandbox);
            vm.runInContext(
              source.slice(operationStart, operationEnd) +
                source.slice(resultStart, resultEnd) +
                "\nthis.operationPresentation = operationPresentation;" +
                "\nthis.renderOperationAwareness = renderOperationAwareness;" +
                "\nthis.coordinateOperationTransition = coordinateOperationTransition;" +
                "\nthis.moveToOperationStage = moveToOperationStage;" +
                "\nthis.beginOperationRun = beginOperationRun;" +
                "\nthis.renderRunActivity = renderRunActivity;" +
                "\nthis.updateRunActivityClock = updateRunActivityClock;" +
                "\nthis.renderResult = renderResult;",
              sandbox,
            );

            const fixed = {
              state: "FIXED",
              execution_authority: "BOUNDED_EXECUTION_AUTHORIZED",
              repository_identity: "commit-a",
              review: {
                preserves: "One bounded operation.",
                completion: "One observable result.",
                must_not_change: ["No broad permission."],
                unresolved: [],
                does_not_authorize: "No automatic Run.",
              },
              technical_details: {
                request_id: "GI-REQ-ONE",
                interpretation_sha256: "a".repeat(64),
              },
            };
            const repository = { name: "repo", path: "/tmp/repo" };
            const idle = { state: "idle", progress: [], approval: null };
            const emptyTask = {
              mode: "empty",
              runnable: false,
              contextInserted: false,
              stalePreparedContext: false,
            };
            const manualTask = {
              mode: "manual",
              runnable: true,
              contextInserted: false,
              stalePreparedContext: false,
            };
            let view = sandbox.operationPresentation(idle, null, emptyTask, null, {});
            assert.strictEqual(view.currentStage, null);
            assert.strictEqual(view.statuses.run, "Not started");
            view = sandbox.operationPresentation(
              idle,
              null,
              emptyTask,
              repository,
              {},
            );
            assert.strictEqual(view.currentStage, "task");
            assert.strictEqual(view.statuses.task, "Current");
            assert.strictEqual(view.current, "Enter a task");
            assert.strictEqual(view.action, "Paste or write one bounded task.");
            view = sandbox.operationPresentation(idle, fixed, manualTask, repository, {});
            assert.strictEqual(view.currentStage, "task");
            assert.strictEqual(view.statuses.contract, "Not used");
            assert.strictEqual(view.statuses.task, "Current");
            assert.strictEqual(view.action, "Select Run to start this bounded task.");
            const manualLifecycle = [
              [{ ...idle, task_mode: "manual" }, { startPending: true }, "Run starting"],
              [
                {
                  state: "running",
                  task_mode: "manual",
                  progress: ["Working"],
                  approval: null,
                },
                {},
                "Run working",
              ],
              [
                {
                  state: "running",
                  task_mode: "manual",
                  progress: ["Waiting for approval"],
                  approval: {
                    action: "Modify",
                    path: "decision_os/companion/static/app.js",
                  },
                },
                { approvalSeen: true },
                "Approval waiting",
              ],
              [
                {
                  state: "running",
                  task_mode: "manual",
                  progress: ["Continuing"],
                  approval: null,
                },
                { approvalSeen: true, continuingAfterApproval: true },
                "post-Approval continuation",
              ],
              [
                {
                  state: "completed",
                  task_mode: "manual",
                  progress: [],
                  approval: null,
                },
                {},
                "terminal success",
              ],
              [
                {
                  state: "denied",
                  task_mode: "manual",
                  progress: [],
                  approval: null,
                },
                {},
                "terminal denial",
              ],
              [
                {
                  state: "needs_attention",
                  task_mode: "manual",
                  progress: [],
                  approval: null,
                },
                {},
                "terminal needs-attention",
              ],
            ];
            for (const [run, context, label] of manualLifecycle) {
              view = sandbox.operationPresentation(
                run,
                fixed,
                manualTask,
                repository,
                context,
              );
              assert.strictEqual(view.statuses.contract, "Not used", label);
            }
            for (const state of ["running", "completed", "needs_attention"]) {
              view = sandbox.operationPresentation(
                { state, task_mode: "contract", progress: [], approval: null },
                null,
                emptyTask,
                repository,
                {},
              );
              assert.strictEqual(
                view.statuses.contract,
                "Not started",
                `non-manual repository without Contract: ${state}`,
              );
            }
            const insertedTask = {
              mode: "contract",
              runnable: false,
              contextInserted: true,
              stalePreparedContext: false,
            };
            view = sandbox.operationPresentation(
              idle,
              fixed,
              insertedTask,
              repository,
              {},
            );
            assert.strictEqual(view.current, "Add bounded task");
            assert.strictEqual(
              view.happening,
              "The fixed Contract context has been inserted.",
            );
            assert.strictEqual(
              view.action,
              "Write one exact task after “Task to perform:”.",
            );

            const staleFixed = { ...fixed, review: null };
            view = sandbox.operationPresentation(
              idle,
              staleFixed,
              emptyTask,
              repository,
              {},
            );
            assert.strictEqual(view.currentStage, "task");
            assert.strictEqual(view.statuses.contract, "Needs attention");
            assert.notStrictEqual(view.statuses.contract, "Complete");
            assert.strictEqual(view.statuses.task, "Current");
            assert.strictEqual(view.current, "Enter a task");
            assert.strictEqual(
              view.action,
              "Paste or write one bounded task.",
            );

            const interpretationOnly = {
              ...fixed,
              execution_authority: "INTERPRETATION_ONLY",
            };
            view = sandbox.operationPresentation(
              idle,
              interpretationOnly,
              emptyTask,
              repository,
              {},
            );
            assert.strictEqual(view.statuses.contract, "Complete");
            assert.strictEqual(view.statuses.task, "Current");
            assert.strictEqual(view.currentStage, "task");
            assert.strictEqual(view.current, "Enter a task");
            assert.strictEqual(
              view.happening,
              "The repository is ready for one bounded task.",
            );
            assert.strictEqual(view.action, "Paste or write one bounded task.");

            const unknownAuthority = {
              ...fixed,
              execution_authority: "UNKNOWN",
            };
            view = sandbox.operationPresentation(
              idle,
              unknownAuthority,
              emptyTask,
              repository,
              {},
            );
            assert.strictEqual(view.statuses.contract, "Complete");
            assert.strictEqual(view.statuses.task, "Current");
            assert.strictEqual(view.currentStage, "task");
            assert.strictEqual(view.current, "Enter a task");
            assert.strictEqual(
              view.happening,
              "The repository is ready for one bounded task.",
            );

            view = sandbox.operationPresentation(
              idle,
              staleFixed,
              manualTask,
              repository,
              {},
            );
            assert.strictEqual(view.currentStage, "task");
            assert.strictEqual(view.current, "Task ready");
            assert.strictEqual(view.action, "Select Run to start this bounded task.");
            view = sandbox.operationPresentation(
              idle,
              fixed,
              {
                mode: "contract",
                runnable: false,
                contextInserted: true,
                stalePreparedContext: true,
              },
              repository,
              {},
            );
            assert.strictEqual(view.currentStage, "task");
            assert.strictEqual(view.statuses.task, "Needs attention");
            assert.strictEqual(view.current, "Prepared task needs attention");
            assert.strictEqual(
              view.action,
              "Clear the Task field before writing a manual task.",
            );
            view = sandbox.operationPresentation(
              idle,
              interpretationOnly,
              {
                mode: "contract",
                runnable: false,
                contextInserted: true,
                stalePreparedContext: true,
                authorityBlocked: true,
              },
              repository,
              {},
            );
            assert.strictEqual(view.currentStage, "task");
            assert.strictEqual(view.statuses.task, "Needs attention");
            assert.strictEqual(
              view.current,
              "Prepared context cannot authorize a Run",
            );
            assert.strictEqual(
              view.action,
              "Clear the bounded task field before writing a manual task.",
            );

            elements.get("task").value = "one bounded task";
            sandbox.latestState = { ordinary_contract: fixed, repository };
            sandbox.beginOperationRun("manual");
            assert.strictEqual(elements.get("run").disabled, true);
            assert.strictEqual(elements.get("operation-current").textContent, "Starting Run");
            assert.strictEqual(
              elements.get("operation-action").textContent,
              "Wait — no action is needed.",
            );
            assert.strictEqual(elements.get("operation-task-status").textContent, "Complete");
            assert.strictEqual(elements.get("progress-card").classList.contains("hidden"), false);
            assert.strictEqual(elements.get("progress-heading").focusCalls.length, 1);
            assert.strictEqual(elements.get("run-activity").classList.contains("hidden"), false);
            assert.strictEqual(elements.get("run-activity-status").textContent, "Working · 00:00");
            assert.strictEqual(elements.get("run-activity-progress").textContent, "Starting Run");
            assert.strictEqual(elements.get("run-activity-age").textContent, "Last progress update just now");

            sandbox.operationStartPending = false;
            const working = {
              state: "running",
              task_mode: "manual",
              progress: ["Starting the private Codex runtime."],
              approval: null,
            };
            now += 2000;
            sandbox.renderRunActivity(working);
            sandbox.coordinateOperationTransition(working);
            sandbox.renderOperationAwareness(working, fixed, repository);
            assert.strictEqual(elements.get("operation-current").textContent, "Codex is working");
            assert.strictEqual(elements.get("operation-task-status").textContent, "Complete");
            assert.strictEqual(elements.get("operation-run-status").textContent, "Waiting for system");
            assert.strictEqual(elements.get("run-activity-status").textContent, "Working · 00:02");
            assert.strictEqual(
              elements.get("run-activity-progress").textContent,
              "Starting the private Codex runtime.",
            );
            now += 6000;
            sandbox.renderRunActivity(working);
            assert.strictEqual(elements.get("run-activity-status").textContent, "Working · 00:08");
            assert.strictEqual(elements.get("run-activity-age").textContent, "Last progress update 6s ago");
            now += 28000;
            sandbox.updateRunActivityClock();
            assert.strictEqual(
              elements.get("run-activity-age").textContent,
              "No new progress update for 00:34",
              "unchanged polling must not create a progress event",
            );
            const progressFocusAfterWorking = elements.get("progress-heading").focusCalls.length;
            sandbox.coordinateOperationTransition(working);
            assert.strictEqual(
              elements.get("progress-heading").focusCalls.length,
              progressFocusAfterWorking,
            );

            elements.get("approval-overlay").classList.toggle("hidden", false);
            const approval = {
              state: "running",
              task_mode: "manual",
              progress: ["Waiting for one exact file-change decision."],
              approval: {
                repository: "repo",
                action: "Modify",
                path: "decision_os/companion/static/app.js",
              },
            };
            sandbox.renderRunActivity(approval);
            sandbox.coordinateOperationTransition(approval);
            sandbox.renderOperationAwareness(approval, fixed, repository);
            assert.strictEqual(elements.get("approval-heading").focusCalls.length, 1);
            assert.strictEqual(elements.get("operation-current").textContent, "Approval required");
            assert.strictEqual(elements.get("operation-task-status").textContent, "Complete");
            assert.strictEqual(elements.get("operation-approval-status").textContent, "Waiting for you");
            assert.strictEqual(
              elements.get("operation-happening").textContent,
              "Modify is requested for decision_os/companion/static/app.js.",
            );
            assert.strictEqual(
              elements.get("run-activity").classList.contains("hidden"),
              true,
              "approval must replace generic working presentation",
            );
            sandbox.coordinateOperationTransition(approval);
            assert.strictEqual(elements.get("approval-heading").focusCalls.length, 1);

            elements.get("approval-overlay").classList.toggle("hidden", true);
            sandbox.coordinateOperationTransition(working);
            sandbox.renderRunActivity(working);
            sandbox.renderOperationAwareness(working, fixed, repository);
            assert.strictEqual(elements.get("operation-current").textContent, "The Run is continuing");
            assert.strictEqual(elements.get("operation-task-status").textContent, "Complete");
            assert.strictEqual(elements.get("progress-heading").focusCalls.length, progressFocusAfterWorking + 1);
            sandbox.coordinateOperationTransition(working);
            assert.strictEqual(elements.get("progress-heading").focusCalls.length, progressFocusAfterWorking + 1);

            elements.get("result-card").classList.toggle("hidden", false);
            const terminal = {
              state: "unsupported",
              task_mode: "manual",
              progress: ["Finalizing the local Receipt."],
              result: "The requested file was modified.",
              file_actions: [{ action: "Modify", path: "README.md", status: "approved", access: "one-time" }],
              outcomes: {
                execution: { state: "completed", label: "Codex turn completed" },
                file_change: { state: "modified", label: "Modified successfully" },
                verification: {
                  state: "unsupported",
                  label: "Unsupported — review required",
                  reason: "read_file_too_large",
                },
              },
            };
            sandbox.coordinateOperationTransition(terminal);
            sandbox.renderOperationAwareness(terminal, fixed, repository);
            sandbox.renderRunActivity(terminal);
            sandbox.renderResult(terminal);
            assert.strictEqual(elements.get("result-heading").focusCalls.length, 1);
            assert.strictEqual(elements.get("result-state").textContent, "Review required");
            assert.strictEqual(elements.get("result-file-change").textContent, "Modified successfully");
            assert.strictEqual(elements.get("result-verification").textContent, "Unsupported — review required");
            assert.strictEqual(
              elements.get("result-verification-reason").textContent,
              "read_file_too_large",
            );
            assert.strictEqual(
              elements.get("operation-current").textContent,
              "Change applied — verification needs review",
            );
            assert.strictEqual(elements.get("operation-task-status").textContent, "Complete");
            assert.strictEqual(elements.get("operation-run-status").textContent, "Complete");
            assert.strictEqual(elements.get("operation-result-status").textContent, "Needs review");
            assert.strictEqual(
              elements.get("operation-happening").textContent,
              "The approved file change was applied, but verification did not complete.",
            );
            assert.strictEqual(
              elements.get("operation-action").textContent,
              "Review why verification did not complete.",
            );
            assert.strictEqual(
              elements.get("run-activity").classList.contains("hidden"),
              true,
              "terminal state must stop the activity presentation",
            );

            const mutationFailure = {
              ...terminal,
              state: "needs_attention",
              outcomes: {
                execution: { state: "failed", label: "Execution failed" },
                file_change: { state: "failed", label: "Modification failed" },
                verification: {
                  state: "needs_attention",
                  label: "Needs attention",
                  reason: "mutation_failed",
                },
              },
            };
            let preserved = sandbox.operationPresentation(
              mutationFailure,
              fixed,
              { mode: "manual" },
              repository,
            );
            assert.strictEqual(preserved.current, "Run needs attention");
            assert.strictEqual(preserved.statuses.run, "Needs attention");

            preserved = sandbox.operationPresentation(
              { ...terminal, file_actions: [], outcomes: {
                ...terminal.outcomes,
                file_change: { state: "none", label: "No file change" },
              } },
              fixed,
              { mode: "manual" },
              repository,
            );
            assert.strictEqual(preserved.current, "Run needs attention");

            preserved = sandbox.operationPresentation(
              { ...terminal, state: "denied" },
              fixed,
              { mode: "manual" },
              repository,
            );
            assert.strictEqual(preserved.current, "Run finished");

            preserved = sandbox.operationPresentation(
              { ...terminal, state: "completed", outcomes: {
                ...terminal.outcomes,
                verification: { state: "verified", label: "Verified" },
              } },
              fixed,
              { mode: "manual" },
              repository,
            );
            assert.strictEqual(preserved.current, "Run finished");
            sandbox.coordinateOperationTransition(terminal);
            assert.strictEqual(elements.get("result-heading").focusCalls.length, 1);

            elements.get("task").value = "one bounded task";
            for (const state of ["completed", "denied", "needs_attention"]) {
              const manualTerminal = {
                state,
                task_mode: "manual",
                progress: [],
                approval: null,
              };
              sandbox.renderOperationAwareness(manualTerminal, fixed, repository);
              assert.strictEqual(
                elements.get("operation-task-status").textContent,
                "Complete",
                `manual terminal DOM: ${state}`,
              );
            }
            elements.get("task").value = "";
            sandbox.renderOperationAwareness(
              { ...terminal, state: "completed" },
              fixed,
              repository,
            );
            assert.strictEqual(
              elements.get("operation-task-status").textContent,
              "Complete",
              "clearing the editor must not relabel a completed manual Task",
            );
            elements.get("task").value = [
              sandbox.CONTRACT_TASK_PREFIX,
              "Current repository identity: commit-a",
              "Fixed Contract Request identity: GI-REQ-ONE",
              `Interpretation SHA-256: ${"a".repeat(64)}`,
              sandbox.CONTRACT_TASK_MARKER,
              "Contract-bound replacement.",
            ].join("\n");
            sandbox.renderOperationAwareness(
              { ...terminal, state: "completed" },
              fixed,
              repository,
            );
            assert.strictEqual(
              elements.get("operation-task-status").textContent,
              "Complete",
              "editing the editor must not relabel a completed manual Task",
            );

            reducedMotion = true;
            sandbox.moveToOperationStage("task");
            const reducedScroll =
              elements.get("bounded-task-card").scrollIntoViewCalls.at(-1);
            assert.strictEqual(reducedScroll.behavior, "auto");
            assert.strictEqual(reducedScroll.block, "start");
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
            msg=(
                "Node operation-awareness harness failed:\n"
                f"{completed.stdout}{completed.stderr}"
            ),
        )

    def test_self_hosted_task_preparation_delta_is_local_and_non_overwriting(
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
            const source = fs.readFileSync(process.argv[2], "utf8");
            const contextStart = source.indexOf("function nonEmptyString");
            const contextEnd = source.indexOf("\nfunction operationPresentation", contextStart);
            const start = source.indexOf("function ordinaryTaskStarterValue");
            const end = source.indexOf("\nfunction renderOrdinaryContract", start);
            assert(contextStart >= 0 && contextEnd > contextStart);
            assert(start >= 0 && end > start);
            const snippet =
              source.slice(contextStart, contextEnd) + source.slice(start, end);
            assert.strictEqual(snippet.includes("postJSON"), false);
            assert.strictEqual(snippet.includes("fetch("), false);
            assert.strictEqual(snippet.includes("/api/run"), false);

            class Element {
              constructor(id = "") {
                this.id = id;
                this.value = "";
                this.textContent = "";
                this.type = "";
                this.listeners = new Map();
                this.focusCalls = 0;
                this.scrollCalls = 0;
                this.selection = null;
              }
              addEventListener(name, callback) { this.listeners.set(name, callback); }
              dispatch(name) { this.listeners.get(name)?.(); }
              dispatchEvent() {}
              focus() { this.focusCalls += 1; }
              scrollIntoView() { this.scrollCalls += 1; }
              setSelectionRange(start, end) { this.selection = [start, end]; }
              insertAdjacentElement(_position, element) {
                elements.set(element.id, element);
              }
              remove() { elements.delete(this.id); }
            }
            const elements = new Map([
              ["ordinary-contract-success", new Element("ordinary-contract-success")],
              ["task", new Element("task")],
            ]);
            const fixed = {
              state: "FIXED",
              execution_authority: "BOUNDED_EXECUTION_AUTHORIZED",
              repository_identity: "commit-a",
              technical_details: {
                request_id: "GI-REQ-ONE",
                interpretation_sha256: "a".repeat(64),
              },
              review: {
                preserves: "The fixed decision meaning.",
                completion: "One bounded change is verified.",
                must_not_change: ["No Transfer", "No broad access"],
                unresolved: [],
                does_not_authorize: "No automatic Run.",
              },
            };
            const sandbox = {
              console,
              Event: class Event {},
              CONTRACT_TASK_MARKER: "Task to perform:",
              CONTRACT_TASK_PREFIX:
                "Perform only the bounded task defined by this fixed ordinary Contract context.",
              EXECUTION_AUTHORITY_INTERPRETATION_ONLY: "INTERPRETATION_ONLY",
              EXECUTION_AUTHORITY_BOUNDED: "BOUNDED_EXECUTION_AUTHORIZED",
              EXECUTION_AUTHORITY_UNKNOWN: "UNKNOWN",
              INTERPRETATION_ONLY_MESSAGE:
                "This Contract is fixed for interpretation only. It cannot authorize a Run.",
              UNKNOWN_EXECUTION_AUTHORITY_MESSAGE:
                "Execution authority is not established for this Contract.",
              preparedContractTaskBinding: null,
              preparedContractTaskStarter: null,
              latestState: {
                ordinary_contract: { state: "REVIEW_READY" },
                repository: { name: "repo-a", path: "/tmp/repo-a" },
              },
              displayValue: (value, fallback = "") => {
                if (value == null || value === "") return fallback;
                return typeof value === "string" ? value : JSON.stringify(value);
              },
              byId: (id) => elements.get(id) || null,
              document: { createElement: () => new Element() },
            };
            vm.createContext(sandbox);
            vm.runInContext(
              snippet +
                "\nthis.ensureButton = ensureOrdinaryPrepareTaskButton;" +
                "\nthis.taskReadiness = taskReadiness;",
              sandbox,
            );
            const button = sandbox.ensureButton();
            assert.strictEqual(
              button.textContent,
              "Use this Contract for a bounded task",
            );
            assert.strictEqual(elements.get("task").value, "");

            button.dispatch("click");
            assert.strictEqual(elements.get("task").value, "");
            assert.strictEqual(elements.get("task").focusCalls, 0);

            sandbox.latestState = {
              ordinary_contract: fixed,
              repository: { name: "repo-a", path: "/tmp/repo-a" },
            };
            button.dispatch("click");
            assert(elements.get("task").value.includes("GI-REQ-ONE"));
            assert(elements.get("task").value.includes("No automatic Run."));
            assert(elements.get("task").value.endsWith("Task to perform:"));
            assert.strictEqual(
              sandbox.taskReadiness(
                fixed,
                sandbox.latestState.repository,
              ).runnable,
              false,
            );
            assert.deepStrictEqual(
              elements.get("task").selection,
              [elements.get("task").value.length, elements.get("task").value.length],
            );
            assert.strictEqual(elements.get("task").focusCalls, 1);
            assert.strictEqual(elements.get("task").scrollCalls, 1);

            elements.get("task").value += " Modify one exact file.";
            assert.strictEqual(
              sandbox.taskReadiness(
                fixed,
                sandbox.latestState.repository,
              ).runnable,
              true,
            );
            const preparedValue = elements.get("task").value;
            button.dispatch("click");
            assert.strictEqual(elements.get("task").value, preparedValue);
            assert.strictEqual(elements.get("task").focusCalls, 2);
            assert.strictEqual(elements.get("task").scrollCalls, 2);

            const otherRepository = { name: "repo-b", path: "/tmp/repo-b" };
            assert.strictEqual(
              sandbox.taskReadiness(fixed, otherRepository).runnable,
              false,
            );
            sandbox.preparedContractTaskBinding = null;
            const legacyPrepared = sandbox.taskReadiness(fixed, otherRepository);
            assert.strictEqual(legacyPrepared.mode, "contract");
            assert.strictEqual(legacyPrepared.runnable, false);
            assert.strictEqual(legacyPrepared.stalePreparedContext, true);

            const interpretationOnly = {
              ...fixed,
              execution_authority: "INTERPRETATION_ONLY",
            };
            const authorityBlocked = sandbox.taskReadiness(
              interpretationOnly,
              sandbox.latestState.repository,
            );
            assert.strictEqual(authorityBlocked.runnable, false);
            assert.strictEqual(authorityBlocked.authorityBlocked, true);

            elements.get("task").value = "";
            assert.strictEqual(
              sandbox.taskReadiness(interpretationOnly, otherRepository).runnable,
              false,
            );
            elements.get("task").value = "Keep my existing bounded task.";
            const manual = sandbox.taskReadiness(interpretationOnly, otherRepository);
            assert.strictEqual(manual.mode, "manual");
            assert.strictEqual(manual.runnable, true);

            elements.get("task").value = "";
            sandbox.latestState = {
              ordinary_contract: fixed,
              repository: { name: "repo-a", path: "/tmp/repo-a" },
            };
            button.dispatch("click");
            assert(elements.get("task").value.includes("GI-REQ-ONE"));
            elements.get("task").value = "Replacement manual task.";
            const replaced = sandbox.taskReadiness(
              fixed,
              sandbox.latestState.repository,
            );
            assert.strictEqual(replaced.mode, "manual");
            assert.strictEqual(replaced.runnable, true);
            assert.strictEqual(sandbox.preparedContractTaskBinding, null);

            const renderStart = source.indexOf("function renderOrdinaryContract");
            const renderEnd = source.indexOf("\nconst guidedIntakeActionIds", renderStart);
            const renderSnippet = source.slice(renderStart, renderEnd);
            assert(renderSnippet.includes("const fixed = usableCurrentOrdinaryContext(panel)"));
            assert(renderSnippet.includes("const canPrepareTask = fixed && contractExecutionAuthorized(panel)"));
            assert(renderSnippet.includes("? ensureOrdinaryPrepareTaskButton()"));
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
            msg=(
                "Node self-hosted task-preparation harness failed:\n"
                f"{completed.stdout}{completed.stderr}"
            ),
        )

    def test_operation_awareness_browser_transition_sequence(self) -> None:
        chrome_candidates = (
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        chrome = next(
            (
                candidate
                for candidate in chrome_candidates
                if candidate and Path(candidate).is_file()
            ),
            None,
        )
        if chrome is None:
            self.skipTest("Chrome or Chromium is unavailable for browser qualification.")

        static_root = (
            Path(__file__).resolve().parents[1]
            / "decision_os"
            / "companion"
            / "static"
        )
        html = (static_root / "index.html").read_text(encoding="utf-8")
        stylesheet = (static_root / "app.css").read_text(encoding="utf-8")
        javascript = (static_root / "app.js").read_text(encoding="utf-8")
        shin_task = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "ordinary_entry_ux_v0_1"
            / "shin_readme_task.txt"
        ).read_text(encoding="utf-8")
        shin_task_script = (
            f"<script>window.__shinTask = {json.dumps(shin_task)};</script>"
        )
        html = html.replace(
            '<link rel="stylesheet" href="/app.css">',
            f"<style>{stylesheet}</style>",
        )
        browser_state = textwrap.dedent(
            r"""
            <script>
              const ordinary = {
                state: "FIXED",
                execution_authority: "BOUNDED_EXECUTION_AUTHORIZED",
                execution_authority_reason: "Synthetic future authorized-family browser fixture.",
                contract_summary: "Preserves one bounded Contract meaning.",
                operation_revision: 7,
                status_label: "Contract fixed",
                progress_text: "The Contract is fixed.",
                review: {
                  preserves: "One bounded operation.",
                  completion: "One observable result.",
                  must_not_change: ["No broad permission."],
                  unresolved: [],
                  does_not_authorize: "No automatic Run.",
                },
                clarification: null,
                action_error: null,
                allowed_actions: ["SELECT_CONTRACT"],
                source_identity: { filename: "contract.md" },
                technical_details: {
                  request_id: "GI-REQ-BROWSER",
                  interpretation_sha256: "b".repeat(64),
                },
                repository_identity: "browser-fixture",
              };
              const interpretationOnly = {
                ...ordinary,
                execution_authority: "INTERPRETATION_ONLY",
                execution_authority_reason:
                  "Synthetic interpretation-only browser fixture.",
              };
              const baseRun = {
                run_type: "bounded_task",
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
              const workingRun = {
                ...baseRun,
                state: "running",
                task_mode: "manual",
                progress: ["Starting the private Codex runtime."],
              };
              const approvalRun = {
                ...workingRun,
                progress: [
                  "Starting the private Codex runtime.",
                  "Waiting for one exact file-change decision.",
                ],
                approval: {
                  repository: "repo",
                  action: "Modify",
                  path: "decision_os/companion/static/app.js",
                  diff: "--- before\n+++ after",
                  reason: "Apply the bounded update.",
                },
              };
              const continuingRun = {
                ...workingRun,
                progress: [
                  "Starting the private Codex runtime.",
                  "Waiting for one exact file-change decision.",
                ],
              };
              const terminalRun = {
                ...baseRun,
                state: "unsupported",
                task_mode: "manual",
                progress: ["Finalizing the local Receipt."],
                result: "Guarded prefix\n[Repository source content withheld.]\n日本語 🌐\nGuarded suffix",
                file_actions: [{
                  action: "Modify",
                  path: "decision_os/companion/static/app.js",
                  access: "one-time",
                  status: "approved",
                }],
                read_evidence: [{
                  path: "decision_os/companion/static/app.js",
                  bytes: 43210,
                  sha256: "a".repeat(64),
                  repository_identity: "b".repeat(40),
                  status: "succeeded",
                  reason: null,
                }],
                outcomes: {
                  execution: {
                    state: "completed",
                    label: "Codex turn completed",
                  },
                  file_change: {
                    state: "modified",
                    label: "Modified successfully",
                  },
                  verification: {
                    state: "unsupported",
                    label: "Unsupported — review required",
                    reason: "unsupported_request_method:commandExecution",
                  },
                },
              };
              const failureResponse =
                "The bounded Codex Run failed closed while verifying runtime settings.";
              const failureRun = {
                ...baseRun,
                state: "needs_attention",
                task_mode: "manual",
                progress: ["Starting the private Codex runtime."],
                result: "PRIVATE incomplete model text",
                error: failureResponse,
                failure: {
                  code: "codex_settings_verification_failed",
                  protocol_phase: "settings_verification",
                  reason: failureResponse,
                  action: "recheck_runtime",
                },
                outcomes: {
                  execution: {
                    state: "not_completed",
                    label: "Codex turn did not complete",
                  },
                  file_change: {
                    state: "unknown",
                    label: "Not established — file-change outcome requires review",
                  },
                  verification: {
                    state: "needs_attention",
                    label: "Needs attention",
                    reason: failureResponse,
                  },
                },
              };
              const terminalCycle005 = {
                cycle_key: "cycle-005",
                state: "FAILED",
                stage: "A3",
                failure_code: "SYNTHETIC_TERMINAL_EVIDENCE",
                storage_occupied: true,
                start_allowed: false,
                p0: {
                  ready: true,
                  failure_code: null,
                },
                launch_binding_sha256: "5".repeat(64),
                identities: {
                  proof_attempt_id: "cycle-005-attempt-001",
                  terminal_stage: "A3",
                  failure_code: "SYNTHETIC_TERMINAL_EVIDENCE",
                  journal_sha256: "6".repeat(64),
                  anchor_sha256: "7".repeat(64),
                  readback_sha256: "8".repeat(64),
                },
              };
              function state(run, ordinaryContract = interpretationOnly) {
                return {
                  csrf: "browser-csrf",
                  repository: { name: "repo", path: "/tmp/repo" },
                  run,
                  creator_live_cycle_005: terminalCycle005,
                  ordinary_contract: ordinaryContract,
                  guided_intake: null,
                  manual_bridge: {
                    state: "BOUNDARY_INCOMPLETE",
                    session: null,
                    imports: [],
                    outputs: {},
                    results: {
                      protocol: "IN PROGRESS / NOT FINAL",
                      product: "BUILDER EVIDENCE ONLY / INDEPENDENT AUDIT REQUIRED",
                      replay: "NOT YET PERFORMED",
                    },
                    burden: {},
                    error: null,
                  },
                  intelligence_transplant: null,
                  defaults: [],
                  receipt: null,
                };
              }
              let serverPhase = "idle";
              let reducedMotion = false;
              window.__requests = [];
              window.__clipboardWrites = [];
              window.__clipboardFail = false;
              Object.defineProperty(navigator, "clipboard", {
                configurable: true,
                value: {
                  writeText: async (value) => {
                    if (window.__clipboardFail) {
                      throw new Error("Synthetic clipboard failure.");
                    }
                    window.__clipboardWrites.push(value);
                  },
                },
              });
              window.__focusCounts = {};
              window.__scrollRecords = [];
              const nativeFocus = HTMLElement.prototype.focus;
              HTMLElement.prototype.focus = function(options) {
                window.__focusCounts[this.id] =
                  (window.__focusCounts[this.id] || 0) + 1;
                nativeFocus.call(this, options);
              };
              HTMLElement.prototype.scrollIntoView = function(options = {}) {
                window.__scrollRecords.push({
                  id: this.id,
                  behavior: options.behavior || "auto",
                });
              };
              window.matchMedia = () => ({ matches: reducedMotion });
              function browserResponse(body) {
                return {
                  ok: true,
                  status: 200,
                  json: async () => structuredClone(body),
                };
              }
              window.fetch = async (path, options = {}) => {
                let body = null;
                if (typeof options.body === "string") {
                  try {
                    body = JSON.parse(options.body);
                  } catch (_error) {
                    body = options.body;
                  }
                }
                window.__requests.push({
                  path,
                  method: options.method || "GET",
                  body,
                });
                if (path === "/api/run") {
                  serverPhase = "working";
                  return new Promise((resolve) => {
                    window.setTimeout(
                      () => resolve(browserResponse(state(workingRun))),
                      60,
                    );
                  });
                }
                if (path === "/api/approval") {
                  serverPhase = "approval-answered";
                  return browserResponse(state(approvalRun));
                }
                if (path === "/api/state") {
                  if (serverPhase === "working") {
                    serverPhase = "approval";
                    return browserResponse(state(approvalRun));
                  }
                  if (serverPhase === "approval-answered") {
                    serverPhase = "continuing";
                    return browserResponse(state(continuingRun));
                  }
                  if (serverPhase === "continuing") {
                    serverPhase = "terminal";
                    return browserResponse(state(terminalRun));
                  }
                  if (serverPhase === "approval") {
                    return browserResponse(state(approvalRun));
                  }
                  if (serverPhase === "terminal") {
                    return browserResponse(state(terminalRun));
                  }
                  if (serverPhase === "failure") {
                    return browserResponse(state(failureRun));
                  }
                  return browserResponse(state(baseRun));
                }
                throw new Error(`Unexpected browser harness request: ${path}`);
              };
            </script>
            """
        ).strip()
        probe = textwrap.dedent(
            r"""
            <script>
              let probePhase = "idle";
              const probe = window.setInterval(() => {
                const current = document.getElementById("operation-current");
                if (probePhase === "idle" && current.textContent === "Enter a task") {
                  const task = document.getElementById("task");
                  const advanced = document.getElementById("advanced-audit-mode");
                  const advancedResearch = document.getElementById(
                    "advanced-research-mode",
                  );
                  const advancedResearchContent = document.getElementById(
                    "advanced-research-content",
                  );
                  const advancedContract = document.getElementById(
                    "advanced-contract-mode",
                  );
                  const advancedContractContent = document.getElementById(
                    "advanced-contract-content",
                  );
                  const ordinaryCard = document.getElementById(
                    "ordinary-contract-card",
                  );
                  const bridge = document.getElementById("bridge-heading").closest("section");
                  const bridgeAction = document.getElementById("bridge-start");
                  const additionalEvidence = document.getElementById("additional-evidence");
                  bridgeAction.focus();
                  document.body.dataset.advancedClosed = String(
                    !advancedResearch.open &&
                    advancedResearchContent.inert &&
                    !advancedContract.open &&
                    advancedContractContent.inert &&
                    !advanced.open &&
                    document.getElementById("advanced-audit-content").inert
                  );
                  document.body.dataset.evidenceClosed = String(!additionalEvidence.open);
                  document.body.dataset.copyHiddenEmpty = String(
                    document.getElementById("copy-response").classList.contains("hidden") &&
                    document.getElementById("copy-response").disabled
                  );
                  document.body.dataset.bridgeContained = String(advanced.contains(bridge));
                  document.body.dataset.bridgeHidden = String(
                    typeof bridge.checkVisibility === "function"
                      ? !bridge.checkVisibility()
                      : bridge.getClientRects().length === 0
                  );
                  document.body.dataset.bridgeNotFocused = String(
                    document.activeElement !== bridgeAction
                  );
                  document.body.dataset.disclosureContainment = String(
                    !advancedResearch.open &&
                    advancedResearchContent.inert &&
                    !advancedContract.open &&
                    advancedContractContent.inert &&
                    advancedContract.contains(ordinaryCard) &&
                    !advanced.open &&
                    !additionalEvidence.open &&
                    advanced.contains(bridge) &&
                    (typeof bridge.checkVisibility === "function"
                      ? !bridge.checkVisibility()
                      : bridge.getClientRects().length === 0) &&
                    document.activeElement !== bridgeAction
                  );
                  document.body.dataset.ordinaryEntryRoute = String(
                    current.textContent === "Enter a task" &&
                    document.getElementById("operation-task-status").textContent ===
                      "Current" &&
                    document.querySelector('[data-operation-stage="contract"]') === null &&
                    document.getElementById("operation-contract-status") === null &&
                    advancedContract.contains(ordinaryCard) &&
                    advancedContractContent.inert &&
                    advanced.contains(document.getElementById("guided-intake-card")) &&
                    document.getElementById("advanced-audit-content").inert
                  );
                  advanced.open = true;
                  syncAdvancedAuditContainment();
                  bridgeAction.focus();
                  document.body.dataset.operationalOpen = String(advanced.open);
                  document.body.dataset.operationalNotInert = String(
                    !document.getElementById("advanced-audit-content").inert
                  );
                  document.body.dataset.operationalFocused = String(
                    document.activeElement === bridgeAction
                  );
                  document.body.dataset.disclosureOperational = String(
                    !document.getElementById("advanced-audit-content").inert &&
                    advanced.open &&
                    document.activeElement === bridgeAction
                  );
                  advanced.open = false;
                  syncAdvancedAuditContainment();
                  render(state(baseRun, ordinary));
                  document.body.dataset.contractDensity = String(
                    !document.getElementById("ordinary-contract-review").open &&
                    document.getElementById("ordinary-contract-summary").textContent ===
                      "Preserves one bounded Contract meaning." &&
                    document.getElementById("ordinary-contract-usage-mode").textContent ===
                      "Bounded execution authorized" &&
                    document.getElementById("ordinary-contract-can-run").textContent === "Yes"
                  );
                  const interpretationState = state(baseRun);
                  render(interpretationState);
                  task.value = "One manually written bounded task.";
                  task.dispatchEvent(new Event("input", { bubbles: true }));
                  const manualRunnable = !document.getElementById("run").disabled;
                  task.value = "";
                  task.dispatchEvent(new Event("input", { bubbles: true }));
                  document.body.dataset.interpretationOnly = String(
                    document.getElementById("ordinary-contract-prepare-task") === null &&
                    document.getElementById("ordinary-contract-authority-message").textContent ===
                      "This Contract is fixed for interpretation only. It cannot authorize a Run." &&
                    document.getElementById("ordinary-contract-can-run").textContent === "No" &&
                    current.textContent === "Enter a task" &&
                    document.getElementById("operation-task-status").textContent === "Current" &&
                    manualRunnable
                  );

                  const unknownState = state(baseRun, {
                    ...ordinary,
                    execution_authority: "UNKNOWN",
                  });
                  render(unknownState);
                  document.body.dataset.unknownAuthority = String(
                    document.getElementById("ordinary-contract-prepare-task") === null &&
                    document.getElementById("ordinary-contract-authority-message").textContent ===
                      "Execution authority is not established for this Contract." &&
                    current.textContent === "Enter a task" &&
                    document.getElementById("operation-task-status").textContent === "Current"
                  );

                  render(state(baseRun, ordinary));
                  document.getElementById("ordinary-contract-prepare-task").click();
                  preparedContractTaskBinding = null;
                  render(interpretationState);
                  document.body.dataset.preparedContextInvalidated = String(
                    document.getElementById("run").disabled &&
                    current.textContent === "Prepared context cannot authorize a Run" &&
                    document.getElementById("operation-happening").textContent ===
                      "This Contract is fixed for interpretation only. It cannot authorize a Run."
                  );
                  task.value = "";
                  task.dispatchEvent(new Event("input", { bubbles: true }));
                  render(state(baseRun, ordinary));
                  document.getElementById("ordinary-contract-prepare-task").click();
                  document.body.dataset.contextIncomplete = String(
                    task.value.endsWith("Task to perform:") &&
                    document.getElementById("run").disabled &&
                    current.textContent === "Add bounded task" &&
                    document.getElementById("operation-happening").textContent ===
                      "The fixed Contract context has been inserted." &&
                    document.getElementById("operation-action").textContent ===
                      "Write one exact task after “Task to perform:”." &&
                    task.selectionStart === task.value.length &&
                    task.selectionEnd === task.value.length
                  );
                  task.value += " Modify one file only.";
                  task.dispatchEvent(new Event("input", { bubbles: true }));
                  document.body.dataset.contextReady = String(
                    !document.getElementById("run").disabled &&
                    current.textContent === "Task ready" &&
                    document.getElementById("operation-action").textContent ===
                      "Select Run to start this bounded task."
                  );
                  const switched = state(baseRun, ordinary);
                  switched.repository = {
                    name: "other-repo",
                    path: "/tmp/other-repo",
                  };
                  render(switched);
                  document.body.dataset.contextSwitchBlocked = String(
                    document.getElementById("run").disabled &&
                    document.getElementById("operation-task-status").textContent ===
                      "Needs attention"
                  );
                  render(interpretationState);
                  task.value = window.__shinTask;
                  task.dispatchEvent(new Event("input", { bubbles: true }));
                  document.body.dataset.ordinaryEntryReady = String(
                    task.value === window.__shinTask &&
                    !document.getElementById("run").disabled &&
                    current.textContent === "Task ready" &&
                    document.getElementById("operation-task-status").textContent ===
                      "Current" &&
                    !advancedContract.open &&
                    advancedContractContent.inert &&
                    !advanced.open &&
                    document.getElementById("advanced-audit-content").inert
                  );
                  const boundedTaskCard = document.getElementById(
                    "bounded-task-card",
                  );
                  document.body.dataset.creatorTerminalOrdinaryEntry = String(
                    !boundedTaskCard.hidden &&
                    task.disabled === false &&
                    !document.getElementById("run").disabled &&
                    document.getElementById("creator-live-cycle-005-status").textContent ===
                      "FAILED" &&
                    document.getElementById("creator-live-failure-code").textContent ===
                      "SYNTHETIC_TERMINAL_EVIDENCE" &&
                    document.getElementById("creator-live-start").hidden &&
                    !document.getElementById("creator-live-terminal-label").hidden &&
                    !advancedResearch.open &&
                    advancedResearchContent.inert &&
                    !advancedContract.open &&
                    advancedContractContent.inert
                  );
                  document.getElementById("run").click();
                  document.body.dataset.startImmediate = String(
                    current.textContent === "Starting Run" &&
                    document.getElementById("run").disabled &&
                    document.getElementById("operation-action").textContent ===
                      "Wait — no action is needed." &&
                    document.activeElement.id === "progress-heading"
                  );
                  probePhase = "working";
                  return;
                }
                if (probePhase === "working" && current.textContent === "Codex is working") {
                  const runRequests = window.__requests.filter(
                    (request) => request.path === "/api/run",
                  );
                  const runRequest = runRequests.at(-1);
                  const usedContractOrGuidedRoute = window.__requests.some(
                    (request) =>
                      request.path.startsWith("/api/ordinary-contract/") ||
                      request.path.startsWith("/api/guided-intake/"),
                  );
                  document.body.dataset.ordinaryRunRequest = String(
                    runRequests.length === 1 &&
                    runRequest.method === "POST" &&
                    runRequest.body?.task_mode === "manual" &&
                    runRequest.body?.task === window.__shinTask
                  );
                  document.body.dataset.noContractGuidedRoute = String(
                    !usedContractOrGuidedRoute
                  );
                  document.body.dataset.working = String(
                    document.getElementById("operation-run-status").textContent ===
                      "Waiting for system" &&
                    document.getElementById("operation-action").textContent ===
                      "Wait — no action is needed." &&
                    !document.getElementById("run-activity").classList.contains("hidden") &&
                    document.getElementById("run-activity-status").textContent.startsWith(
                      "Working · ",
                    ) &&
                    document.getElementById("run-activity-progress").textContent ===
                      "Starting the private Codex runtime."
                  );
                  probePhase = "approval";
                  return;
                }
                if (probePhase === "approval" && current.textContent === "Approval required") {
                  const approvalFocusBefore = window.__focusCounts["approval-heading"] || 0;
                  document.body.dataset.approval = String(
                    document.getElementById("approval-path").textContent ===
                      "decision_os/companion/static/app.js" &&
                    document.querySelector('[data-choice="allow_once"]').textContent.trim() ===
                      "Allow this change once" &&
                    document.querySelector('[data-choice="repository"]').textContent.trim() ===
                      "Use for this repository" &&
                    document.querySelector('[data-choice="deny"]').textContent.trim() ===
                      "Deny and stop this Run" &&
                    approvalFocusBefore === 1 &&
                    document.getElementById("run-activity").classList.contains("hidden")
                  );
                  document.querySelector('[data-choice="allow_once"]').click();
                  document.body.dataset.approvalAnsweredImmediate = String(
                    document.getElementById("approval-overlay").classList.contains("hidden") &&
                    current.textContent === "The Run is continuing" &&
                    document.getElementById("operation-action").textContent ===
                      "Wait — no action is needed." &&
                    document.activeElement.id === "progress-heading"
                  );
                  probePhase = "continuing";
                  return;
                }
                if (probePhase === "continuing" && current.textContent === "The Run is continuing") {
                  document.body.dataset.continuing = "true";
                  probePhase = "terminal";
                  return;
                }
                if (
                  probePhase === "terminal" &&
                  current.textContent === "Change applied — verification needs review"
                ) {
                  const focusCounts = window.__focusCounts;
                  document.body.dataset.terminal = String(
                    document.getElementById("result-state").textContent ===
                      "Review required" &&
                    document.getElementById("result-file-change").textContent ===
                      "Modified successfully" &&
                    document.getElementById("result-verification").textContent ===
                      "Unsupported — review required" &&
                    document.getElementById("result-verification-reason").textContent ===
                      "unsupported_request_method:commandExecution" &&
                    focusCounts["approval-heading"] === 1 &&
                    focusCounts["result-heading"] === 1 &&
                    document.getElementById("run-activity").classList.contains("hidden")
                  );
                  const readEvidence = document.getElementById("read-evidence-card");
                  const readEvidenceText = document.getElementById(
                    "read-evidence-list",
                  ).textContent;
                  document.body.dataset.readEvidence = String(
                    !readEvidence.classList.contains("hidden") &&
                    readEvidenceText.includes("decision_os/companion/static/app.js") &&
                    readEvidenceText.includes("43210") &&
                    readEvidenceText.includes("a".repeat(64)) &&
                    readEvidenceText.includes("b".repeat(40)) &&
                    !readEvidenceText.includes("Line one") &&
                    !readEvidenceText.includes("日本語")
                  );
                  reducedMotion = true;
                  const taskStage = document.querySelector(
                    '[data-operation-stage="task"]'
                  );
                  taskStage.click();
                  const lastScroll = window.__scrollRecords.at(-1);
                  const resultStage = document.querySelector(
                    '[data-operation-stage="result"]'
                  );
                  resultStage.focus();
                  resultStage.dispatchEvent(new KeyboardEvent("keydown", {
                    bubbles: true,
                    key: "Home",
                  }));
                  document.body.dataset.manualNavigation = String(
                    lastScroll.id === "bounded-task-card" &&
                    lastScroll.behavior === "auto" &&
                    document.activeElement === taskStage
                  );
                  document.body.dataset.sticky = String(
                    getComputedStyle(
                      document.getElementById("operation-awareness")
                    ).position === "sticky"
                  );
                  const copy = document.getElementById("copy-response");
                  document.body.dataset.copyAvailable = String(
                    !copy.classList.contains("hidden") &&
                    !copy.disabled &&
                    copy.tagName === "BUTTON"
                  );
                  copy.focus();
                  copy.click();
                  probePhase = "copy-success";
                  return;
                }
                if (
                  probePhase === "copy-success" &&
                  document.getElementById("copy-response").textContent === "Copied"
                ) {
                  const copy = document.getElementById("copy-response");
                  document.body.dataset.copySuccess = String(
                    document.activeElement === copy &&
                    document.getElementById("copy-response-status").textContent ===
                      "Codex response copied." &&
                    window.__clipboardWrites.length === 1 &&
                    window.__clipboardWrites[0] ===
                      "Guarded prefix\n[Repository source content withheld.]\n日本語 🌐\nGuarded suffix" &&
                    latestState.run.state === "unsupported"
                  );
                  copy.click();
                  probePhase = "copy-repeat";
                  return;
                }
                if (
                  probePhase === "copy-repeat" &&
                  window.__clipboardWrites.length === 2
                ) {
                  document.body.dataset.copyRepeated = String(
                    window.__clipboardWrites[0] === window.__clipboardWrites[1] &&
                    latestState.run.state === "unsupported"
                  );
                  probePhase = "copy-restore";
                  return;
                }
                if (
                  probePhase === "copy-restore" &&
                  document.getElementById("copy-response").textContent === "Copy response"
                ) {
                  document.body.dataset.copyRestored = String(
                    document.getElementById("copy-response-status").textContent === "" &&
                    document.activeElement.id === "copy-response"
                  );
                  window.__clipboardFail = true;
                  document.getElementById("copy-response").click();
                  probePhase = "copy-failure";
                  return;
                }
                if (
                  probePhase === "copy-failure" &&
                  document.getElementById("copy-response").textContent === "Copy failed"
                ) {
                  const failedCopyPreserved = (
                    document.activeElement.id === "copy-response" &&
                    document.getElementById("copy-response-status").textContent ===
                      "Codex response could not be copied." &&
                    latestState.run.state === "unsupported"
                  );
                  serverPhase = "failure";
                  window.__clipboardFail = false;
                  render(state(failureRun));
                  const failureCopy = document.getElementById("copy-response");
                  document.body.dataset.copyFailure = String(
                    failedCopyPreserved &&
                    document.getElementById("result").textContent === failureResponse &&
                    document.getElementById("result-verification-reason").textContent ===
                      failureResponse &&
                    !failureCopy.classList.contains("hidden") &&
                    !failureCopy.disabled &&
                    visibleResponse({ state: "running", result: "", error: null }) === "" &&
                    visibleResponse({ state: "completed", result: "", error: null }) ===
                      "The bounded Run completed without a final text response." &&
                    visibleResponse({
                      state: "needs_attention",
                      result: "",
                      error: null,
                    }) === "No final result was available."
                  );
                  failureCopy.click();
                  probePhase = "failure-copy";
                  return;
                }
                if (
                  probePhase === "failure-copy" &&
                  document.getElementById("copy-response").textContent === "Copied"
                ) {
                  document.body.dataset.failureCopy = String(
                    document.getElementById("result").textContent === failureResponse &&
                    window.__clipboardWrites.at(-1) === failureResponse &&
                    latestState.run.state === "needs_attention" &&
                    latestState.run.file_actions.length === 0 &&
                    latestState.run.approval == null
                  );
                  document.body.dataset.qualified = "true";
                  window.clearInterval(probe);
                }
              }, 20);
            </script>
            """
        ).strip()
        html = html.replace(
            '<script src="/app.js" defer></script>',
            (
                f"{shin_task_script}\n{browser_state}\n"
                f"<script>{javascript}</script>\n{probe}"
            ),
        )

        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            fixture = temporary_root / "operation-awareness-browser.html"
            fixture.write_text(html, encoding="utf-8")
            chrome_process = subprocess.Popen(
                [
                    chrome,
                    "--headless=new",
                    "--disable-background-networking",
                    "--disable-component-update",
                    "--disable-gpu",
                    "--disable-sync",
                    "--force-device-scale-factor=1",
                    "--no-default-browser-check",
                    "--no-first-run",
                    f"--user-data-dir={temporary_root / 'profile'}",
                    "--virtual-time-budget=5000",
                    "--window-size=1280,900",
                    "--dump-dom",
                    fixture.as_uri(),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            chrome_finished = True
            try:
                chrome_stdout, chrome_stderr = chrome_process.communicate(
                    timeout=20,
                )
            except subprocess.TimeoutExpired:
                chrome_finished = False
                chrome_process.kill()
                chrome_stdout, chrome_stderr = chrome_process.communicate()
        if chrome_finished:
            self.assertEqual(
                0,
                chrome_process.returncode,
                msg=f"Chrome operation-awareness probe failed:\n{chrome_stderr}",
            )
        self.assertTrue(
            chrome_stdout.strip(),
            msg=f"Chrome operation-awareness probe emitted no DOM:\n{chrome_stderr}",
        )
        body_match = re.search(r"<body ([^>]*)>", chrome_stdout)
        self.assertIsNotNone(body_match, "Chrome operation probe body was not emitted.")
        attributes = dict(
            re.findall(r'data-([a-z-]+)="([^"]*)"', body_match.group(1))
        )
        for name in (
            "start-immediate",
            "contract-density",
            "advanced-closed",
            "evidence-closed",
            "copy-hidden-empty",
            "bridge-contained",
            "bridge-hidden",
            "bridge-not-focused",
            "disclosure-containment",
            "ordinary-entry-route",
            "operational-open",
            "operational-not-inert",
            "operational-focused",
            "disclosure-operational",
            "interpretation-only",
            "unknown-authority",
            "prepared-context-invalidated",
            "context-incomplete",
            "context-ready",
            "context-switch-blocked",
            "ordinary-entry-ready",
            "creator-terminal-ordinary-entry",
            "ordinary-run-request",
            "no-contract-guided-route",
            "working",
            "approval",
            "approval-answered-immediate",
            "continuing",
            "terminal",
            "read-evidence",
            "manual-navigation",
            "sticky",
            "copy-available",
            "copy-success",
            "copy-repeated",
            "copy-restored",
            "copy-failure",
            "failure-copy",
            "qualified",
        ):
            self.assertEqual("true", attributes.get(name), name)

    def test_failed_ordinary_panel_clears_stale_review_and_disables_fix(
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
            const source = fs.readFileSync(process.argv[2], "utf8");
            const contextStart = source.indexOf("function nonEmptyString");
            const contextEnd = source.indexOf("\nfunction operationPresentation", contextStart);
            const start = source.indexOf("function renderOrdinaryList");
            const end = source.indexOf("\nconst guidedIntakeActionIds", start);
            assert(contextStart >= 0 && contextEnd > contextStart);
            assert(start >= 0 && end > start);

            class Element {
              constructor(id = "") {
                this.id = id;
                this.checked = false;
                this.children = [];
                this.open = false;
                this.classList = {
                  values: new Set(),
                  toggle: (value, force) => {
                    if (force) this.classList.values.add(value);
                    else this.classList.values.delete(value);
                  },
                  contains: (value) => this.classList.values.has(value),
                };
                this.disabled = false;
                this.textContent = "";
              }
              append(child) { this.children.push(child); }
              replaceChildren(...children) { this.children = children; }
              focus() {}
              setAttribute() {}
              remove() { elements.delete(this.id); }
            }

            const ids = [
              "ordinary-contract-answer-confirm",
              "ordinary-contract-answer-reject",
              "ordinary-contract-authority",
              "ordinary-contract-authority-message",
              "ordinary-contract-can-run",
              "ordinary-contract-clarification",
              "ordinary-contract-completion",
              "ordinary-contract-confirm",
              "ordinary-contract-dnt",
              "ordinary-contract-error",
              "ordinary-contract-error-action",
              "ordinary-contract-error-dismiss",
              "ordinary-contract-prepare-task",
              "ordinary-contract-error-fixed",
              "ordinary-contract-error-retry",
              "ordinary-contract-error-state",
              "ordinary-contract-error-what",
              "ordinary-contract-file",
              "ordinary-contract-selected-file",
              "ordinary-contract-fix",
              "ordinary-contract-preserves",
              "ordinary-contract-progress",
              "ordinary-contract-question",
              "ordinary-contract-review",
              "ordinary-contract-meaning",
              "ordinary-contract-summary",
              "ordinary-contract-status",
              "ordinary-contract-success",
              "ordinary-contract-technical-body",
              "ordinary-contract-unresolved",
              "ordinary-contract-usage-mode",
            ];
            const elements = new Map(ids.map((id) => [id, new Element(id)]));
            const sandbox = {
              console,
              document: { createElement: () => new Element() },
              connected: true,
              requestActive: false,
              ordinaryLastRevision: 0,
              ordinaryFocusIntent: null,
              ordinaryLastErrorId: null,
              ordinarySelectedFilename: null,
              ordinarySelectedFilenameRevision: null,
              ordinaryReviewDisclosureIdentity: null,
              CONTRACT_TASK_MARKER: "Task to perform:",
              CONTRACT_TASK_PREFIX:
                "Perform only the bounded task defined by this fixed ordinary Contract context.",
              EXECUTION_AUTHORITY_INTERPRETATION_ONLY: "INTERPRETATION_ONLY",
              EXECUTION_AUTHORITY_BOUNDED: "BOUNDED_EXECUTION_AUTHORIZED",
              EXECUTION_AUTHORITY_UNKNOWN: "UNKNOWN",
              INTERPRETATION_ONLY_MESSAGE:
                "This Contract is fixed for interpretation only. It cannot authorize a Run.",
              UNKNOWN_EXECUTION_AUTHORITY_MESSAGE:
                "Execution authority is not established for this Contract.",
              preparedContractTaskBinding: null,
              preparedContractTaskStarter: null,
              byId: (id) => elements.get(id),
              setText: (id, value) => {
                elements.get(id).textContent = value == null ? "" : String(value);
              },
              setHidden: (id, hidden) => {
                elements.get(id).classList.toggle("hidden", hidden);
              },
            };
            vm.createContext(sandbox);
            vm.runInContext(
              source.slice(contextStart, contextEnd) +
                source.slice(start, end) +
                "\nthis.renderOrdinaryContract = renderOrdinaryContract;" +
                "\nthis.recordOrdinarySelectedFilename = recordOrdinarySelectedFilename;",
              sandbox,
            );
            const prior = {
              state: "REVIEW_READY",
              operation_revision: 8,
              status_label: "Ready to fix",
              progress_text: "Review the interpretation before fixing this Contract.",
              review: {
                preserves: "Prior native interpretation",
                completion: "Prior completion",
                must_not_change: [],
                unresolved: [],
                does_not_authorize: "No execution authority.",
              },
              clarification: null,
              allowed_actions: ["SELECT_CONTRACT", "FIX_CONTRACT"],
              action_error: null,
              technical_details: {},
              source_identity: { filename: "verified-prior.md" },
              contract_summary: "Preserves the fixed Contract meaning.",
              execution_authority: "INTERPRETATION_ONLY",
            };
            const failed = {
              state: "CANNOT_FIX_SAFELY",
              operation_revision: 9,
              status_label: "Cannot be fixed safely",
              progress_text: "Choose another supported Contract.",
              review: null,
              clarification: null,
              allowed_actions: ["SELECT_CONTRACT", "DISMISS_ERROR"],
              action_error: {
                error_id: "OUP-ERR-ONE",
                code: "PREP_UNSUPPORTED_CONTRACT_ROLE",
                what_failed: "This Contract family is not supported.",
                anything_fixed: "NO",
                user_action_required: "Select another supported Contract.",
                retryable: false,
              },
              technical_details: {},
              source_identity: { filename: "unsupported-server.md" },
            };

            sandbox.renderOrdinaryContract(prior, { name: "repo" });
            assert.strictEqual(
              elements.get("ordinary-contract-selected-file").textContent,
              "Selected file: verified-prior.md",
            );
            assert.strictEqual(
              elements.get("ordinary-contract-review").classList.contains("hidden"),
              false,
            );
            assert.strictEqual(elements.get("ordinary-contract-fix").disabled, false);
            sandbox.recordOrdinarySelectedFilename("attempted-unsupported.md");
            assert.strictEqual(
              elements.get("ordinary-contract-selected-file").textContent,
              "Selected file: attempted-unsupported.md",
            );
            sandbox.renderOrdinaryContract(prior, { name: "repo" });
            assert.strictEqual(
              elements.get("ordinary-contract-selected-file").textContent,
              "Selected file: attempted-unsupported.md",
            );
            elements.get("ordinary-contract-file").value = "";
            for (let poll = 0; poll < 2; poll += 1) {
              sandbox.renderOrdinaryContract(failed, { name: "repo" });
              assert.strictEqual(elements.get("ordinary-contract-file").value, "");
              assert.strictEqual(
                elements.get("ordinary-contract-selected-file").textContent,
                "Selected file: attempted-unsupported.md",
              );
              assert.strictEqual(
                elements.get("ordinary-contract-review").classList.contains("hidden"),
                true,
              );
              assert.strictEqual(
                elements.get("ordinary-contract-preserves").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("ordinary-contract-completion").textContent,
                "",
              );
              assert.strictEqual(elements.get("ordinary-contract-fix").disabled, true);
              assert.strictEqual(
                elements.get("ordinary-contract-error").classList.contains("hidden"),
                false,
              );
              assert.strictEqual(
                elements.get("ordinary-contract-error-what").textContent,
                "This Contract family is not supported.",
              );
            }
            sandbox.recordOrdinarySelectedFilename("replacement.md");
            assert.strictEqual(
              elements.get("ordinary-contract-selected-file").textContent,
              "Selected file: replacement.md",
            );
            sandbox.renderOrdinaryContract({
              ...prior,
              operation_revision: 10,
              source_identity: { filename: "server-verified-replacement.md" },
            }, { name: "repo" });
            assert.strictEqual(
              elements.get("ordinary-contract-selected-file").textContent,
              "Selected file: server-verified-replacement.md",
            );

            sandbox.ordinarySelectedFilename = null;
            sandbox.ordinarySelectedFilenameRevision = null;
            sandbox.renderOrdinaryContract({
              ...failed,
              operation_revision: 11,
            }, { name: "repo" });
            assert.strictEqual(
              elements.get("ordinary-contract-selected-file").textContent,
              "Selected file: unsupported-server.md",
            );

            const staleFixed = {
              ...prior,
              state: "FIXED",
              operation_revision: 12,
              status_label: "Contract fixed",
              progress_text: "Historical fixation remains recorded.",
              review: null,
              allowed_actions: ["SELECT_CONTRACT"],
              repository_identity: "commit-b",
              technical_details: {
                request_id: "GI-REQ-AT-A",
                interpretation_sha256: "a".repeat(64),
                preparation_repository_identity: "commit-a",
              },
            };
            sandbox.renderOrdinaryContract(
              staleFixed,
              { name: "repo", path: "/tmp/repo" },
            );
            assert.strictEqual(
              elements.get("ordinary-contract-status").textContent,
              "Needs attention",
            );
            assert.strictEqual(
              elements.get("ordinary-contract-progress").textContent,
              "Select and fix this Contract for the current repository.",
            );
            assert.strictEqual(
              elements.get("ordinary-contract-success").classList.contains("hidden"),
              true,
            );
            assert.strictEqual(
              elements.has("ordinary-contract-prepare-task"),
              false,
            );

            const currentFixed = {
              ...staleFixed,
              operation_revision: 13,
              review: prior.review,
              repository_identity: "commit-b",
              technical_details: {
                request_id: "GI-REQ-AT-B",
                interpretation_sha256: "b".repeat(64),
                preparation_repository_identity: "commit-b",
              },
            };
            sandbox.renderOrdinaryContract(
              currentFixed,
              { name: "repo", path: "/tmp/repo" },
            );
            assert.strictEqual(
              elements.get("ordinary-contract-success").classList.contains("hidden"),
              false,
            );
            assert.strictEqual(
              elements.has("ordinary-contract-prepare-task"),
              false,
            );
            assert.strictEqual(
              elements.get("ordinary-contract-usage-mode").textContent,
              "Interpretation only",
            );
            assert.strictEqual(
              elements.get("ordinary-contract-can-run").textContent,
              "No",
            );
            assert.strictEqual(
              elements.get("ordinary-contract-authority-message").textContent,
              "This Contract is fixed for interpretation only. It cannot authorize a Run.",
            );
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
            msg=f"Node ordinary panel harness failed:\n{completed.stdout}{completed.stderr}",
        )

    def test_desktop_layout_contains_long_contract_without_overflow(
        self,
    ) -> None:
        chrome_candidates = (
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )
        chrome = next(
            (
                candidate
                for candidate in chrome_candidates
                if candidate and Path(candidate).is_file()
            ),
            None,
        )
        if chrome is None:
            self.skipTest(
                "Chrome or Chromium is unavailable for layout qualification."
            )

        static_root = (
            Path(__file__).resolve().parents[1]
            / "decision_os"
            / "companion"
            / "static"
        )
        html = (static_root / "index.html").read_text(encoding="utf-8")
        html = html.replace(
            '<link rel="stylesheet" href="/app.css">',
            f'<link rel="stylesheet" href="{(static_root / "app.css").as_uri()}">',
        )
        long_filename = ("contract-" * 80) + ".md"
        long_content = "A" * 20000
        layout_probe = textwrap.dedent(
            f"""
            <script>
              const longFilename = {json.dumps(long_filename)};
              const longContent = {json.dumps(long_content)};
              const filename = document.getElementById("contract-file-name");
              const preview = document.getElementById("contract-preview");
              const full = document.getElementById("contract-full-content");
              document.getElementById("advanced-audit-mode").open = true;
              document.getElementById("advanced-audit-content").inert = false;
              const importCard = document.getElementById("contract-import-card");
              const guidedIntakeAction = document.getElementById(
                "contract-use-guided-intake"
              );
              filename.textContent = longFilename;
              preview.textContent = longContent.slice(0, 4096);
              preview.classList.remove("hidden");
              full.value = longContent;
              const root = document.documentElement;
              const control = document.getElementById("bridge-as-of-commit");
              const importCardRect = importCard.getBoundingClientRect();
              const guidedIntakeActionRect =
                guidedIntakeAction.getBoundingClientRect();
              document.body.dataset.viewportWidth = String(window.innerWidth);
              document.body.dataset.viewportHeight = String(window.innerHeight);
              document.body.dataset.horizontalOverflow = String(
                root.scrollWidth > root.clientWidth
              );
              document.body.dataset.previewBounded = String(
                preview.clientHeight <= 290 &&
                preview.scrollHeight > preview.clientHeight &&
                getComputedStyle(preview).overflowY === "auto"
              );
              document.body.dataset.controlBlock = String(
                getComputedStyle(control).display === "block" &&
                control.getBoundingClientRect().width >= 760
              );
              document.body.dataset.controlDisplay =
                getComputedStyle(control).display;
              document.body.dataset.controlWidth = String(
                control.getBoundingClientRect().width
              );
              document.body.dataset.fullPreserved = String(
                full.value === longContent
              );
              document.body.dataset.guidedIntakeActionContained = String(
                getComputedStyle(guidedIntakeAction).display !== "none" &&
                guidedIntakeActionRect.width > 0 &&
                guidedIntakeActionRect.height > 0 &&
                guidedIntakeActionRect.left >= importCardRect.left &&
                guidedIntakeActionRect.right <= importCardRect.right
              );
            </script>
            """
        ).strip()
        html = html.replace(
            '<script src="/app.js" defer></script>',
            layout_probe,
        )

        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            fixture = temporary_root / "companion-layout.html"
            fixture.write_text(html, encoding="utf-8")
            chrome_process = subprocess.Popen(
                [
                    chrome,
                    "--headless=new",
                    "--disable-background-networking",
                    "--disable-component-update",
                    "--disable-gpu",
                    "--disable-sync",
                    "--force-device-scale-factor=1",
                    "--no-default-browser-check",
                    "--no-first-run",
                    f"--user-data-dir={temporary_root / 'profile'}",
                    "--window-size=1664,945",
                    "--dump-dom",
                    fixture.as_uri(),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            chrome_finished = True
            try:
                chrome_stdout, chrome_stderr = chrome_process.communicate(
                    timeout=20,
                )
            except subprocess.TimeoutExpired:
                # Some macOS Chrome builds keep the headless browser process
                # alive after --dump-dom has emitted the completed document.
                chrome_finished = False
                chrome_process.kill()
                chrome_stdout, chrome_stderr = chrome_process.communicate()

        if chrome_finished:
            self.assertEqual(
                0,
                chrome_process.returncode,
                msg=f"Chrome layout probe failed:\n{chrome_stderr}",
            )
        self.assertTrue(
            chrome_stdout.strip(),
            msg=f"Chrome emitted no layout probe DOM:\n{chrome_stderr}",
        )
        body_match = re.search(r"<body ([^>]*)>", chrome_stdout)
        self.assertIsNotNone(body_match, "Chrome probe body was not emitted.")
        attributes = dict(
            re.findall(r'data-([a-z-]+)="([^"]*)"', body_match.group(1))
        )
        self.assertEqual("1664", attributes.get("viewport-width"))
        viewport_height = int(attributes.get("viewport-height", "0"))
        self.assertGreaterEqual(viewport_height, 850)
        self.assertLessEqual(viewport_height, 945)
        self.assertEqual("false", attributes.get("horizontal-overflow"))
        self.assertEqual("true", attributes.get("preview-bounded"))
        self.assertEqual(
            "true",
            attributes.get("control-block"),
            f"display={attributes.get('control-display')} width={attributes.get('control-width')}",
        )
        self.assertEqual("true", attributes.get("full-preserved"))
        self.assertEqual(
            "true",
            attributes.get("guided-intake-action-contained"),
        )

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
                this.checked = false;
                this.files = [];
                this._value = "";
                this.type = "";
                this.children = [];
                this.parentNode = null;
                this.listeners = new Map();
                this.ownText = "";
                this.focusCalls = [];
                this.scrollIntoViewCalls = [];
              }

              get value() {
                return this._value;
              }

              set value(value) {
                const stringValue = value == null ? "" : String(value);
                this._value =
                  this.id === "guided-intake-original-request"
                    ? stringValue.replace(/\r\n?/g, "\n")
                    : stringValue;
                if (this._value === "") {
                  this.files = [];
                }
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

              focus(options) {
                this.focusCalls.push(options);
              }

              scrollIntoView(options) {
                this.scrollIntoViewCalls.push(options);
              }
            }

            const bridgeButtonIds = [
              "bridge-copy",
              "bridge-freeze-handoff",
              "bridge-freeze-manifest",
              "bridge-freeze-receipt",
              "bridge-generate-handoff",
              "bridge-generate-manifest",
              "bridge-generate-receipt",
              "bridge-import-file",
              "bridge-import-paste",
              "bridge-record-intervention",
              "bridge-record-reexplanation",
              "bridge-replay-run",
              "bridge-start",
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
            const guidedIntakeButtonIds = [
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
            const buttonIds = new Set([
              "choose-repository",
              "contract-import",
              "contract-use-guided-intake",
              "ordinary-contract-confirm",
              "ordinary-contract-fix",
              "ordinary-contract-error-retry",
              "ordinary-contract-error-dismiss",
              "ordinary-contract-prepare-task",
              "copy-response",
              "new-run",
              "run",
              ...guidedIntakeButtonIds,
              ...bridgeButtonIds,
            ]);
            const ids = [
              "advanced-audit-content",
              "advanced-audit-mode",
              "advanced-contract-content",
              "advanced-contract-mode",
              "advanced-research-content",
              "advanced-research-mode",
              "approval-action",
              "approval-diff",
              "approval-overlay",
              "approval-path",
              "approval-reason",
              "approval-reason-label",
              "approval-repository",
              "approval-heading",
              "contract-file",
              "contract-file-name",
              "contract-full-content",
              "contract-import",
              "contract-import-error",
              "contract-import-state",
              "contract-preview",
              "contract-preview-status",
              "contract-use-guided-intake",
              "bridge-as-of-commit",
              "bridge-authority-boundary",
              "bridge-burden-status",
              "bridge-completion-line",
              "bridge-copy",
              "bridge-copy-output",
              "bridge-current-gate",
              "bridge-do-not-touch",
              "bridge-evidence-blob",
              "bridge-evidence-commit",
              "bridge-evidence-path",
              "bridge-evidence-sha256",
              "bridge-file",
              "bridge-framework-finding",
              "bridge-framework-layer",
              "bridge-framework-lens",
              "bridge-framework-question",
              "bridge-freeze-handoff",
              "bridge-freeze-manifest",
              "bridge-freeze-receipt",
              "bridge-generate-handoff",
              "bridge-generate-manifest",
              "bridge-generate-receipt",
              "bridge-handoff-output",
              "bridge-identities",
              "bridge-import-file",
              "bridge-import-paste",
              "bridge-manifest-output",
              "bridge-metadata",
              "bridge-objective",
              "bridge-paste",
              "bridge-product-result",
              "bridge-protocol-result",
              "bridge-protocol-run-id",
              "bridge-receipt-output",
              "bridge-record-intervention",
              "bridge-record-reexplanation",
              "bridge-replay-baseline",
              "bridge-replay-candidate",
              "bridge-replay-output",
              "bridge-replay-result",
              "bridge-replay-run",
              "bridge-required-next-actor",
              "bridge-role",
              "bridge-session-id",
              "bridge-source",
              "bridge-start",
              "bridge-state",
              "bridge-task-id",
              "bounded-task-card",
              "task-heading",
              "bounded-run-receipt-column",
              "choose-repository",
              "claim-boundary",
              "copy-response",
              "copy-response-status",
              "defaults",
              "file-actions",
              "global-error",
              "guided-intake-answer",
              "guided-intake-authority-claim",
              "guided-intake-authority-explanation",
              "guided-intake-card",
              "guided-intake-capture",
              "guided-intake-completion-checks",
              "guided-intake-completion-line",
              "guided-intake-completion-status",
              "guided-intake-confirm",
              "guided-intake-confirmation-history",
              "guided-intake-confirmation",
              "guided-intake-copy",
              "guided-intake-copy-output",
              "guided-intake-do-not-touch",
              "guided-intake-draft-json",
              "guided-intake-error",
              "guided-intake-fidelity-evaluation",
              "guided-intake-freeze",
              "guided-intake-freeze-identity",
              "guided-intake-gate",
              "guided-intake-import-draft",
              "guided-intake-objective",
              "guided-intake-objective-atoms",
              "guided-intake-objective-status",
              "guided-intake-original-exact",
              "guided-intake-original-request",
              "guided-intake-producer-label",
              "guided-intake-purge",
              "guided-intake-purge-confirm",
              "guided-intake-purge-status",
              "guided-intake-question",
              "guided-intake-question-field",
              "guided-intake-raw-source-availability",
              "guided-intake-request-identity",
              "guided-intake-resulting-delta",
              "guided-intake-state",
              "guided-intake-judgment-reuse",
              "guided-intake-transfer",
              "guided-intake-transfer-receipt",
              "guided-intake-unknown",
              "intelligence-transplant-active-cap",
              "intelligence-transplant-authority-provenance",
              "intelligence-transplant-card",
              "intelligence-transplant-cryptographic-provenance",
              "intelligence-transplant-delta-state",
              "intelligence-transplant-error",
              "ordinary-contract-clarification",
              "ordinary-contract-answer-confirm",
              "ordinary-contract-answer-reject",
              "ordinary-contract-authority",
              "ordinary-contract-authority-message",
              "ordinary-contract-can-run",
              "ordinary-contract-completion",
              "ordinary-contract-confirm",
              "ordinary-contract-dnt",
              "ordinary-contract-error",
              "ordinary-contract-error-action",
              "ordinary-contract-error-dismiss",
              "ordinary-contract-error-fixed",
              "ordinary-contract-error-retry",
              "ordinary-contract-error-state",
              "ordinary-contract-error-what",
              "ordinary-contract-heading",
              "ordinary-contract-meaning",
              "ordinary-contract-file",
              "ordinary-contract-selected-file",
              "ordinary-contract-fix",
              "ordinary-contract-preserves",
              "ordinary-contract-progress",
              "ordinary-contract-prepare-task",
              "ordinary-contract-question",
              "ordinary-contract-review",
              "ordinary-contract-summary",
              "ordinary-contract-status",
              "ordinary-contract-success",
              "ordinary-contract-technical-body",
              "ordinary-contract-unresolved",
              "ordinary-contract-usage-mode",
              "intelligence-transplant-evidence-objects",
              "intelligence-transplant-execution-status",
              "intelligence-transplant-gate",
              "intelligence-transplant-generalized-transplant",
              "intelligence-transplant-lineage",
              "intelligence-transplant-missing-evidence",
              "intelligence-transplant-next-action",
              "intelligence-transplant-not-allowed-next",
              "intelligence-transplant-run-id",
              "intelligence-transplant-structural-validation",
              "new-run",
              "operation-action",
              "operation-approval-status",
              "operation-current",
              "operation-happening",
              "operation-next",
              "operation-result-status",
              "operation-run-status",
              "operation-task-status",
              "progress",
              "progress-card",
              "progress-heading",
              "receipt-status",
              "read-evidence-card",
              "read-evidence-heading",
              "read-evidence-list",
              "repository-name",
              "repository-path",
              "repository-receipt",
              "result",
              "result-card",
              "result-execution",
              "result-file-change",
              "result-heading",
              "result-state",
              "result-verification",
              "result-verification-reason",
              "run",
              "run-activity",
              "run-activity-age",
              "run-activity-progress",
              "run-activity-status",
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
                  buttonIds.has(id)
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
              "contract-import-error",
              "contract-preview",
              "global-error",
              "guided-intake-confirmation",
              "guided-intake-error",
              "intelligence-transplant-card",
              "intelligence-transplant-error",
              "run-activity",
              "ordinary-contract-clarification",
              "ordinary-contract-error",
              "ordinary-contract-meaning",
              "ordinary-contract-review",
              "ordinary-contract-success",
              "progress-card",
              "result-card",
              "run-error",
            ]) {
              elements.get(id).classList.toggle("hidden", true);
            }
            elements.get("task").value = "Keep this bounded task";
            elements.get("guided-intake-draft-json").value = "{}";
            elements.get("guided-intake-resulting-delta").value = "{}";

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
            const clipboardWrites = [];
            const navigator = {
              clipboard: {
                async writeText(value) {
                  clipboardWrites.push(value);
                },
              },
            };
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
            function emptyGuidedIntake(overrides = {}) {
              return {
                state: "EMPTY",
                error: null,
                original_request: "",
                request_identity: null,
                copy_for_pro_prompt: "",
                interpretation: {
                  objective: {
                    text: "",
                    fidelity_status: "UNKNOWN",
                    atoms: [],
                  },
                  completion_line: {
                    text: "",
                    testability_status: "UNKNOWN",
                    checks: [],
                  },
                  do_not_touch: [],
                  unknown: [],
                  gate: "UNKNOWN",
                },
                active_question: null,
                confirmation_history: [],
                fidelity_evaluation: "AVAILABLE",
                freeze: null,
                historical_identity: null,
                judgment_reuse: "AVAILABLE",
                purge: null,
                raw_source_availability: "NONE",
                transfer_state: null,
                transfer_receipt: null,
                authority_claim:
                  "INTERPRETATION ONLY — NO EXECUTION AUTHORITY",
                authority_explanation: "",
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
              intelligence_transplant: {
                run_id: "IT-RUN-STALE",
                run_type: "intelligence_transplant",
                execution_status: "ACTIVE",
                delta_state: "CANDIDATE",
                current_gate: "HOLD",
                missing_evidence: [
                  "</li><script>globalThis.stage5Hostile = true</script>",
                ],
                next_one_action: "Attach current E4.",
                not_allowed_next: ["MODEL_INVOCATION", "ROLE_ASSIGNMENT"],
                evidence_objects: [
                  {
                    object_id: "E3-ONE",
                    content_hash: "<script>literal-stage5-hash</script>",
                  },
                ],
                lineage: [
                  {
                    from: "E1-ONE",
                    to: "E3-ONE",
                  },
                ],
                active_cap: null,
                generalized_transplant: "NOT_ESTABLISHED",
                structural_validation: "PASS",
                authority_provenance: "MANUAL_OWNER_ATTESTED",
                cryptographic_provenance: "NOT_ESTABLISHED",
                error: null,
              },
              guided_intake: emptyGuidedIntake({
                state: "AWAITING_CONFIRMATION",
                original_request:
                  '</pre><script>globalThis.hostile = true</script>&ORIGINAL',
                request_identity: {
                  request_id: "GUIDED-REQUEST-ONE",
                  sha256: "GUIDED-REQUEST-HASH",
                },
                raw_source_availability: "AVAILABLE",
                copy_for_pro_prompt: "HOSTILE <PROMPT> & COPY",
                interpretation: {
                  objective: {
                    text: "HOSTILE <OBJECTIVE>",
                    fidelity_status: "EXPLICIT",
                    atoms: [
                      {
                        atom_id: "OBJ-HOSTILE",
                        text:
                          "</pre><script>globalThis.atomHostile = true</script>",
                        support: [
                          {
                            kind: "ORIGINAL_REQUEST_QUOTE",
                            quote: "<script>ATOM_SUPPORT</script>",
                            quote_sha256: "ATOM-SUPPORT-HASH",
                            occurrence: 2,
                            byte_start: 17,
                            byte_end: 46,
                          },
                        ],
                      },
                    ],
                  },
                  completion_line: {
                    text: "HOSTILE </dd><script>COMPLETE</script>",
                    testability_status: "TESTABLE",
                    checks: [
                      {
                        observable:
                          "<script>globalThis.checkHostile = true</script>",
                        pass_condition: "PASS </pre> & exact",
                        evidence_source: "<img src=x onerror=alert(1)>",
                      },
                    ],
                  },
                  do_not_touch: ["<script>DO_NOT_TOUCH</script>"],
                  unknown: ["UNKNOWN <img src=x>"],
                  gate: "CONFIRMATION_REQUIRED",
                },
                active_question: {
                  field: "completion_line",
                  question: "Is <this> the exact completion line?",
                },
                confirmation_history: [
                  {
                    confirmation_event_id: "GI-CONF-HOSTILE",
                    field: "COMPLETION_LINE",
                    question:
                      "<script>globalThis.historyHostile = true</script>",
                    answer: "Forward-only <answer>",
                    resulting_delta: {
                      completion_line: {
                        evidence_source: "</pre><script>HISTORY</script>",
                      },
                    },
                    resulting_gate: "CLEAR ENOUGH TO FREEZE",
                  },
                ],
                authority_explanation:
                  "Full authority explanation.\n<script>literal only</script>\nNo execution, approval, build, merge, publication, or release authority.",
              }),
              manual_bridge: {
                state: "DESIGN_IMPORTED",
                session: {
                  session_id: "STALE_BRIDGE_SESSION",
                },
                imports: [
                  {
                    selected_role: "PRO_DESIGN",
                    artifact_content_hash: "STALE_BRIDGE_HASH",
                    import_mode: "BYTE_EXACT_FILE_IMPORT",
                    source_path_or_label: "STALE_BRIDGE_SOURCE",
                    model_identity: { value: "STALE_PRO_MODEL" },
                    role_identity: "STALE_PRO_ROLE",
                    artifact_authored_at: "STALE_PRO_TIME",
                    authority_state: "DESIGN_ONLY_NO_EXECUTION_AUTHORITY",
                  },
                ],
                outputs: {
                  COPY_FOR_PRO: { content: "STALE_COPY_FOR_PRO" },
                  EXECUTION_HANDOFF: { content: "STALE_HANDOFF" },
                  BRIDGE_RECEIPT: { content: "STALE_BRIDGE_RECEIPT" },
                  GOLDEN_MANIFEST: { content: "STALE_MANIFEST" },
                  REPLAY_RESULT: { content: "STALE_REPLAY_OUTPUT" },
                },
                golden_manifest: null,
                results: {
                  protocol: "STALE_PROTOCOL_RESULT",
                  product: "STALE_PRODUCT_RESULT",
                  replay: "STALE_REPLAY_RESULT",
                },
                burden: {
                  shin_copy_paste_count: {
                    value_or_unknown: 1,
                  },
                },
              },
            };
            const confirmedGuidedState = {
              ...completedState,
              csrf: "csrf-guided-confirmed",
              guided_intake: {
                ...completedState.guided_intake,
                state: "READY_TO_FREEZE",
                active_question: null,
                interpretation: {
                  ...completedState.guided_intake.interpretation,
                  gate: "CLEAR ENOUGH TO FREEZE",
                },
              },
            };
            const frozenGuidedState = {
              ...confirmedGuidedState,
              csrf: "csrf-guided-frozen",
              guided_intake: {
                ...confirmedGuidedState.guided_intake,
                state: "FROZEN",
                freeze: {
                  freeze_id: "GUIDED-FREEZE-ONE",
                  sha256: "GUIDED-FREEZE-HASH",
                  current: true,
                },
              },
            };
            const correctedAfterFreezeState = {
              ...frozenGuidedState,
              csrf: "csrf-guided-corrected",
              guided_intake: {
                ...frozenGuidedState.guided_intake,
                state: "READY_TO_FREEZE",
                freeze: {
                  ...frozenGuidedState.guided_intake.freeze,
                  current: false,
                },
              },
            };
            const refrozenGuidedState = {
              ...correctedAfterFreezeState,
              csrf: "csrf-guided-refrozen",
              guided_intake: {
                ...correctedAfterFreezeState.guided_intake,
                state: "FROZEN",
                freeze: {
                  freeze_id: "GUIDED-FREEZE-TWO",
                  sha256: "GUIDED-FREEZE-HASH-TWO",
                  current: true,
                },
              },
            };
            const transferredGuidedState = {
              ...refrozenGuidedState,
              csrf: "csrf-guided-transferred",
              guided_intake: {
                ...refrozenGuidedState.guided_intake,
                state: "TRANSFERRED_TO_BRIDGE",
                transfer_receipt: {
                  transfer_id: "GUIDED-TRANSFER-ONE",
                },
              },
            };
            const purgedGuidedState = {
              ...transferredGuidedState,
              csrf: "csrf-guided-purged",
              guided_intake: {
                ...transferredGuidedState.guided_intake,
                active_question: null,
                confirmation_history: [],
                copy_for_pro_prompt: null,
                fidelity_evaluation: "BLOCKED",
                freeze: {
                  ...transferredGuidedState.guided_intake.freeze,
                  current: false,
                  purged: true,
                },
                historical_identity: "PRESERVED",
                interpretation: null,
                judgment_reuse: "BLOCKED",
                original_request: null,
                purge: {
                  confirmation: "EXPLICIT_USER_CONFIRMATION",
                  event_hash: "PURGE-EVENT-HASH",
                  event_id: "GI-PURGE-ONE",
                  purged_at: "2026-07-29T00:00:00Z",
                  raw_blob_disposition:
                    "DELETED_NO_NON_PURGED_REFERENCES",
                  remaining_non_purged_references: 0,
                  request_id: "GUIDED-REQUEST-ONE",
                  request_sha256: "GUIDED-REQUEST-HASH",
                },
                raw_source_availability: "UNAVAILABLE",
                state: "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
                transfer_state: "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
              },
            };
            const changedPurgeIdentityState = {
              ...transferredGuidedState,
              csrf: "csrf-guided-identity-changed",
              guided_intake: {
                ...transferredGuidedState.guided_intake,
                request_identity: {
                  request_id: "GUIDED-REQUEST-TWO",
                  sha256: "GUIDED-REQUEST-HASH-TWO",
                },
              },
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
            const selectedStage5State = {
              ...completedState,
              csrf: "csrf-stage5-selected",
              run: {
                ...completedState.intelligence_transplant,
                state: "active",
              },
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
              guided_intake: emptyGuidedIntake(),
              manual_bridge: {
                state: "BOUNDARY_INCOMPLETE",
                session: null,
                imports: [],
                outputs: {},
                golden_manifest: null,
                results: {
                  protocol: "IN PROGRESS / NOT FINAL",
                  product:
                    "BUILDER EVIDENCE ONLY / INDEPENDENT AUDIT REQUIRED",
                  replay: "NOT YET PERFORMED",
                },
                burden: {},
              },
            };
            const runtimeMismatchState = {
              ...recoveredState,
              csrf: "csrf-runtime-mismatch",
              run: emptyRun({
                state: "needs_attention",
                error:
                  "The bounded Codex Run failed closed while verifying the runtime version.",
                failure: {
                  code: "codex_version_verification_failed",
                  protocol_phase: "version_verification",
                  reason:
                    "The bounded Codex Run failed closed while verifying the runtime version.",
                  action: "recheck_runtime",
                  category: "unknown",
                  jsonrpc_code: null,
                  protocol_method: null,
                },
              }),
            };
            const switchedRepositoryState = {
              ...recoveredState,
              csrf: "csrf-switched",
              repository: {
                name: "OTHER_REPOSITORY_NAME",
                path: "/tmp/OTHER_REPOSITORY_PATH",
              },
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
                Uint8Array,
                btoa(value) {
                  return Buffer.from(value, "binary").toString("base64");
                },
                console,
                document,
                fetch: fetchMock,
                navigator,
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
              assert.strictEqual(elements.get("contract-file").disabled, false);
              assert.strictEqual(elements.get("contract-import").disabled, true);
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              assert.strictEqual(
                hidden("intelligence-transplant-card"),
                false,
              );
              assert.strictEqual(
                elements.get("intelligence-transplant-run-id").textContent,
                "IT-RUN-STALE",
              );
              assert.strictEqual(
                elements.get(
                  "intelligence-transplant-authority-provenance",
                ).textContent,
                "MANUAL OWNER ATTESTED",
              );
              assert.strictEqual(
                elements.get(
                  "intelligence-transplant-cryptographic-provenance",
                ).textContent,
                "NOT ESTABLISHED",
              );
              assert.strictEqual(
                elements.get(
                  "intelligence-transplant-generalized-transplant",
                ).textContent,
                "NOT ESTABLISHED",
              );
              assert.strictEqual(
                elements.get(
                  "intelligence-transplant-missing-evidence",
                ).textContent.includes("<script>"),
                true,
              );
              assert.strictEqual(sandbox.stage5Hostile, undefined);
              assert.strictEqual(
                elements.get("bridge-state").textContent,
                "DESIGN_IMPORTED",
              );
              assert.strictEqual(
                elements.get("bridge-protocol-result").textContent,
                "STALE_PROTOCOL_RESULT",
              );
              assert.strictEqual(
                elements.get("bridge-product-result").textContent,
                "STALE_PRODUCT_RESULT",
              );
              assert.strictEqual(
                elements.get("bridge-replay-result").textContent,
                "STALE_REPLAY_RESULT",
              );
              assert.strictEqual(
                elements.get("bridge-copy-output").textContent,
                "STALE_COPY_FOR_PRO",
              );
              assert.strictEqual(
                elements.get("bridge-identities").textContent.includes(
                  "STALE_BRIDGE_SOURCE",
                ),
                true,
              );
              assert.strictEqual(elements.get("bridge-start").disabled, true);
              assert.strictEqual(elements.get("bridge-copy").disabled, false);
              const firstRevoke =
                elements.get("defaults").children[0].children[1];
              assert.strictEqual(firstRevoke.disabled, false);

              assert.strictEqual(
                elements.get("guided-intake-state").textContent,
                "AWAITING_CONFIRMATION",
              );
              assert.strictEqual(
                elements.get("guided-intake-authority-claim").textContent,
                "INTERPRETATION ONLY — NO EXECUTION AUTHORITY",
              );
              assert.strictEqual(
                elements.get("guided-intake-authority-explanation").textContent,
                "Full authority explanation.\n" +
                  "<script>literal only</script>\n" +
                  "No execution, approval, build, merge, publication, or release authority.",
              );
              assert.strictEqual(
                elements.get("guided-intake-original-exact").textContent,
                '</pre><script>globalThis.hostile = true</script>&ORIGINAL',
              );
              assert.strictEqual(sandbox.hostile, undefined);
              assert.strictEqual(
                elements.get("guided-intake-objective").textContent,
                "HOSTILE <OBJECTIVE>",
              );
              assert.strictEqual(
                elements.get("guided-intake-completion-line").textContent,
                "HOSTILE </dd><script>COMPLETE</script>",
              );
              const objectiveAtomsText =
                elements.get("guided-intake-objective-atoms").textContent;
              assert.strictEqual(
                objectiveAtomsText.includes(
                  "</pre><script>globalThis.atomHostile = true</script>",
                ),
                true,
              );
              assert.strictEqual(
                objectiveAtomsText.includes('"byte_start": 17'),
                true,
              );
              assert.strictEqual(
                objectiveAtomsText.includes('"byte_end": 46'),
                true,
              );
              assert.strictEqual(
                objectiveAtomsText.includes(
                  '"quote": "<script>ATOM_SUPPORT</script>"',
                ),
                true,
              );
              const completionChecksText =
                elements.get("guided-intake-completion-checks").textContent;
              assert.strictEqual(
                completionChecksText.includes(
                  '"evidence_source": "<img src=x onerror=alert(1)>"',
                ),
                true,
              );
              assert.strictEqual(
                completionChecksText.includes("PASS </pre> & exact"),
                true,
              );
              const confirmationHistoryText =
                elements.get("guided-intake-confirmation-history").textContent;
              assert.strictEqual(
                confirmationHistoryText.includes("GI-CONF-HOSTILE"),
                true,
              );
              assert.strictEqual(
                confirmationHistoryText.includes(
                  "<script>globalThis.historyHostile = true</script>",
                ),
                true,
              );
              assert.strictEqual(sandbox.atomHostile, undefined);
              assert.strictEqual(sandbox.checkHostile, undefined);
              assert.strictEqual(sandbox.historyHostile, undefined);
              assert.strictEqual(
                elements.get("guided-intake-do-not-touch").textContent,
                "<script>DO_NOT_TOUCH</script>",
              );
              assert.strictEqual(
                elements.get("guided-intake-unknown").textContent,
                "UNKNOWN <img src=x>",
              );
              assert.strictEqual(hidden("guided-intake-confirmation"), false);
              assert.strictEqual(elements.get("guided-intake-capture").disabled, true);
              assert.strictEqual(elements.get("guided-intake-copy").disabled, false);
              assert.strictEqual(
                elements.get("guided-intake-import-draft").disabled,
                true,
              );
              assert.strictEqual(elements.get("guided-intake-confirm").disabled, true);
              assert.strictEqual(elements.get("guided-intake-freeze").disabled, true);
              assert.strictEqual(
                elements.get("guided-intake-raw-source-availability").textContent,
                "AVAILABLE",
              );
              assert.strictEqual(
                elements.get("guided-intake-judgment-reuse").textContent,
                "AVAILABLE",
              );
              assert.strictEqual(
                elements.get("guided-intake-fidelity-evaluation").textContent,
                "AVAILABLE",
              );
              assert.strictEqual(
                elements.get("guided-intake-purge-confirm").disabled,
                false,
              );
              assert.strictEqual(
                elements.get("guided-intake-purge").disabled,
                true,
              );
              assert.strictEqual(elements.get("guided-intake-transfer").disabled, true);

              const boundedTaskBeforeImport = elements.get("task").value;
              const markdownContent =
                "# Approved Product Contract\r\n\r\n" +
                "Unicode: 契約\n" +
                "<script>globalThis.contractHostile = true</script>";
              let markdownReads = 0;
              elements.get("contract-file").files = [
                {
                  name: "approved-product-contract.md",
                  async text() {
                    markdownReads += 1;
                    return markdownContent;
                  },
                },
              ];
              await elements.get("contract-file").dispatch("input");
              assert.strictEqual(elements.get("contract-import").disabled, false);
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              await elements.get("contract-import").dispatch("click");
              await settle();
              assert.strictEqual(markdownReads, 1);
              assert.strictEqual(
                elements.get("contract-import-state").textContent,
                "Imported locally",
              );
              assert.strictEqual(
                elements.get("contract-file-name").textContent,
                "approved-product-contract.md",
              );
              assert.strictEqual(
                elements.get("contract-preview").textContent,
                markdownContent,
              );
              assert.strictEqual(
                elements.get("contract-full-content").value,
                markdownContent,
              );
              assert.strictEqual(
                vm.runInContext("importedContract.content", sandbox),
                markdownContent,
              );
              assert.strictEqual(hidden("contract-preview"), false);
              assert.strictEqual(hidden("contract-import-error"), true);
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                false,
              );
              assert.strictEqual(sandbox.contractHostile, undefined);

              const textContent = "Plain text Contract\r\nkept exactly.\n";
              let textReads = 0;
              elements.get("contract-file").files = [
                {
                  name: "approved-product-contract.txt",
                  async text() {
                    textReads += 1;
                    return textContent;
                  },
                },
              ];
              await elements.get("contract-file").dispatch("change");
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              assert.strictEqual(
                vm.runInContext("importedContract", sandbox),
                null,
              );
              await elements.get("contract-import").dispatch("click");
              await settle();
              assert.strictEqual(textReads, 1);
              assert.strictEqual(
                elements.get("contract-preview").textContent,
                textContent,
              );
              assert.strictEqual(
                elements.get("contract-full-content").value,
                textContent,
              );
              assert.strictEqual(
                vm.runInContext("importedContract.content", sandbox),
                textContent,
              );
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                false,
              );

              let rejectStaleRead;
              const staleFile = {
                name: "superseded-contract.md",
                text() {
                  return new Promise((_resolve, reject) => {
                    rejectStaleRead = reject;
                  });
                },
              };
              elements.get("contract-file").files = [staleFile];
              await elements.get("contract-file").dispatch("input");
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              const staleImport = elements.get("contract-import").dispatch("click");
              await settle();

              const currentContent = "Current Contract stays retained.";
              elements.get("contract-file").files = [
                {
                  name: "current-contract.md",
                  async text() {
                    return currentContent;
                  },
                },
              ];
              await elements.get("contract-file").dispatch("input");
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              await elements.get("contract-import").dispatch("click");
              await settle();
              rejectStaleRead(new Error("superseded read failed"));
              await staleImport;
              await settle();
              assert.strictEqual(
                elements.get("contract-file-name").textContent,
                "current-contract.md",
              );
              assert.strictEqual(
                elements.get("contract-full-content").value,
                currentContent,
              );
              assert.strictEqual(hidden("contract-import-error"), true);
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                false,
              );

              let sameFileReadCount = 0;
              let rejectFirstSameFileRead;
              const sameFileContent =
                "Newest same-file import wins.\r\nUnicode: 契約";
              const displayedSameFileContent = sameFileContent.replace(
                /\r\n?/g,
                "\n",
              );
              const sameFile = {
                name: "same-contract.md",
                text() {
                  sameFileReadCount += 1;
                  if (sameFileReadCount === 1) {
                    return new Promise((_resolve, reject) => {
                      rejectFirstSameFileRead = reject;
                    });
                  }
                  return Promise.resolve(sameFileContent);
                },
              };
              elements.get("contract-file").files = [sameFile];
              await elements.get("contract-file").dispatch("input");
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              const firstSameFileImport =
                elements.get("contract-import").dispatch("click");
              await settle();
              await elements.get("contract-import").dispatch("click");
              await settle();
              rejectFirstSameFileRead(new Error("first same-file read failed"));
              await firstSameFileImport;
              await settle();
              assert.strictEqual(sameFileReadCount, 2);
              assert.strictEqual(
                vm.runInContext("importedContract.content", sandbox),
                sameFileContent,
              );
              assert.strictEqual(
                elements.get("contract-full-content").value,
                sameFileContent,
              );
              assert.strictEqual(hidden("contract-import-error"), true);
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                false,
              );

              const guidedOriginal = elements.get(
                "guided-intake-original-request"
              );
              await elements
                .get("contract-use-guided-intake")
                .dispatch("click");
              await settle();
              assert.strictEqual(guidedOriginal.value, displayedSameFileContent);
              assert.strictEqual(
                vm.runInContext(
                  "guidedTransferredOriginalRequest.content",
                  sandbox,
                ),
                sameFileContent,
              );

              const preservedDecodedTail =
                "\r\nUnicode: 契約\n" +
                "LF stays decoded\n" +
                "CR stays decoded\r" +
                "CRLF stays decoded\r\nFULL_TAIL";
              const longContent =
                "A".repeat(11698 - preservedDecodedTail.length) +
                preservedDecodedTail;
              const displayedLongContent = longContent.replace(/\r\n?/g, "\n");
              assert.strictEqual(longContent.length, 11698);
              assert.notStrictEqual(displayedLongContent, longContent);
              const longFilename = `${"very-long-contract-name-".repeat(30)}.MD`;
              const longFile = {
                name: longFilename,
                async text() {
                  return longContent;
                },
              };
              elements.get("contract-file").files = [longFile];
              await elements.get("contract-file").dispatch("input");
              assert.strictEqual(
                vm.runInContext("guidedTransferredOriginalRequest", sandbox),
                null,
              );
              assert.strictEqual(guidedOriginal.value, displayedSameFileContent);
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );

              fetchQueue.push(() => Promise.resolve(response(completedState)));
              await elements.get("guided-intake-capture").dispatch("click");
              await settle();
              const resetBackingCaptureRequest = fetchCalls.at(-1);
              assert.strictEqual(
                resetBackingCaptureRequest.path,
                "/api/guided-intake/capture",
              );
              assert.deepStrictEqual(
                JSON.parse(resetBackingCaptureRequest.options.body),
                {
                  original_request: displayedSameFileContent,
                  supersedes_request_id: "GUIDED-REQUEST-ONE",
                },
              );
              assert.notStrictEqual(
                JSON.parse(resetBackingCaptureRequest.options.body)
                  .original_request,
                sameFileContent,
              );

              elements.get("contract-file").files = [sameFile];
              await elements.get("contract-file").dispatch("input");
              await elements.get("contract-import").dispatch("click");
              await settle();
              await elements
                .get("contract-use-guided-intake")
                .dispatch("click");
              await settle();
              assert.strictEqual(
                vm.runInContext(
                  "guidedTransferredOriginalRequest.content",
                  sandbox,
                ),
                sameFileContent,
              );

              let unsupportedReads = 0;
              elements.get("contract-file").files = [
                {
                  name: "approved-product-contract.md.exe",
                  async text() {
                    unsupportedReads += 1;
                    return "must not be read";
                  },
                },
              ];
              await elements.get("contract-file").dispatch("input");
              assert.strictEqual(
                vm.runInContext("guidedTransferredOriginalRequest", sandbox),
                null,
              );
              assert.strictEqual(guidedOriginal.value, displayedSameFileContent);
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              await elements.get("contract-import").dispatch("click");
              await settle();
              assert.strictEqual(unsupportedReads, 0);
              assert.strictEqual(
                elements.get("contract-import-state").textContent,
                "Rejected",
              );
              assert.strictEqual(
                elements.get("contract-import-error").textContent,
                "Only .md and .txt Product Contract files are supported.",
              );
              assert.strictEqual(elements.get("contract-full-content").value, "");
              assert.strictEqual(hidden("contract-preview"), true);
              assert.strictEqual(hidden("contract-import-error"), false);
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              assert.strictEqual(
                vm.runInContext("guidedTransferredOriginalRequest", sandbox),
                null,
              );
              assert.strictEqual(guidedOriginal.value, displayedSameFileContent);

              const contractFetchStart = fetchCalls.length;
              elements.get("contract-file").files = [longFile];
              await elements.get("contract-file").dispatch("input");
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              await elements.get("contract-import").dispatch("click");
              await settle();
              assert.strictEqual(
                elements.get("contract-file-name").textContent,
                longFilename,
              );
              assert.strictEqual(
                elements.get("contract-preview").textContent,
                longContent.slice(0, 4096),
              );
              assert.strictEqual(
                elements.get("contract-preview").textContent.length,
                4096,
              );
              assert.strictEqual(
                elements.get("contract-full-content").value,
                longContent,
              );
              assert.strictEqual(
                vm.runInContext("importedContract.content", sandbox),
                longContent,
              );
              assert.strictEqual(
                elements.get("contract-preview-status").textContent,
                `Showing first 4096 of ${longContent.length} characters. Full content is retained locally.`,
              );
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                false,
              );
              assert.strictEqual(fetchCalls.length, contractFetchStart);
              assert.strictEqual(elements.get("task").value, boundedTaskBeforeImport);
              assert.strictEqual(
                fetchCalls.some((call) => call.path === "/api/run"),
                false,
              );

              const guidedCard = elements.get("guided-intake-card");
              assert.strictEqual(guidedOriginal.value, displayedSameFileContent);
              const guidedFocusBeforeUse = guidedOriginal.focusCalls.length;
              const guidedOriginalScrollBeforeUse =
                guidedOriginal.scrollIntoViewCalls.length;
              const guidedCardScrollBeforeUse =
                guidedCard.scrollIntoViewCalls.length;
              const useFetchStart = fetchCalls.length;
              await elements
                .get("contract-use-guided-intake")
                .dispatch("click");
              await settle();
              assert.strictEqual(guidedOriginal.value, displayedLongContent);
              assert.strictEqual(
                vm.runInContext(
                  "guidedTransferredOriginalRequest.content",
                  sandbox,
                ),
                longContent,
              );
              assert.strictEqual(
                vm.runInContext(
                  "guidedTransferredOriginalRequest.content.length",
                  sandbox,
                ),
                11698,
              );
              assert.strictEqual(
                vm.runInContext(
                  "guidedTransferredOriginalRequest.displayedValue",
                  sandbox,
                ),
                displayedLongContent,
              );
              assert.notStrictEqual(guidedOriginal.value, sameFileContent);
              assert.strictEqual(
                elements.get("guided-intake-capture").disabled,
                false,
              );
              assert.strictEqual(
                elements.get("guided-intake-freeze").disabled,
                true,
              );
              assert.strictEqual(
                elements.get("guided-intake-state").textContent,
                "AWAITING_CONFIRMATION",
              );
              assert.strictEqual(
                elements.get("guided-intake-original-exact").textContent,
                '</pre><script>globalThis.hostile = true</script>&ORIGINAL',
              );
              assert.strictEqual(fetchCalls.length, useFetchStart);
              assert.strictEqual(
                fetchCalls.slice(useFetchStart).some(
                  (call) => call.path === "/api/guided-intake/capture",
                ),
                false,
              );
              assert.strictEqual(
                fetchCalls.some(
                  (call) => call.path === "/api/guided-intake/freeze",
                ),
                false,
              );
              assert.strictEqual(
                fetchCalls.some(
                  (call) => call.path === "/api/guided-intake/copy",
                ),
                false,
              );
              assert.strictEqual(
                fetchCalls.some((call) => call.path === "/api/run"),
                false,
              );
              assert.strictEqual(
                fetchCalls.every(
                  (call) =>
                    typeof call.path === "string" &&
                    call.path.startsWith("/"),
                ),
                true,
              );
              assert.strictEqual(
                guidedOriginal.focusCalls.length > guidedFocusBeforeUse ||
                  guidedOriginal.scrollIntoViewCalls.length >
                    guidedOriginalScrollBeforeUse ||
                  guidedCard.scrollIntoViewCalls.length >
                    guidedCardScrollBeforeUse,
                true,
              );

              fetchQueue.push(() =>
                Promise.resolve(response(selectedStage5State)),
              );
              await runNextTimer();
              assert.strictEqual(hidden("bounded-task-card"), true);
              assert.strictEqual(
                hidden("bounded-run-receipt-column"),
                true,
              );
              assert.strictEqual(hidden("progress-card"), true);
              assert.strictEqual(hidden("result-card"), true);
              assert.strictEqual(elements.get("run").disabled, true);
              assert.strictEqual(elements.get("task").disabled, true);
              assert.strictEqual(
                hidden("intelligence-transplant-card"),
                false,
              );
              assert.strictEqual(
                elements.get("intelligence-transplant-run-id").textContent,
                "IT-RUN-STALE",
              );

              const guidedFetchStart = fetchCalls.length;
              assert.strictEqual(
                elements.get("guided-intake-original-request").value,
                displayedLongContent,
              );
              assert.strictEqual(elements.get("guided-intake-capture").disabled, false);
              assert.strictEqual(
                vm.runInContext(
                  "guidedTransferredOriginalRequest.content",
                  sandbox,
                ),
                longContent,
              );
              fetchQueue.push(() => Promise.resolve(response(completedState)));
              await elements.get("guided-intake-capture").dispatch("click");
              await settle();
              const captureRequest = fetchCalls.at(-1);
              assert.strictEqual(
                captureRequest.path,
                "/api/guided-intake/capture",
              );
              assert.deepStrictEqual(
                JSON.parse(captureRequest.options.body),
                {
                  original_request: longContent,
                  supersedes_request_id: "GUIDED-REQUEST-ONE",
                },
              );
              assert.strictEqual(
                JSON.parse(captureRequest.options.body).original_request.length,
                11698,
              );
              assert.strictEqual(
                JSON.parse(captureRequest.options.body).original_request,
                longContent,
              );

              const manualOriginalRequest =
                "CAPTURE <script>literal</script> & exact";
              elements.get("guided-intake-original-request").value =
                manualOriginalRequest;
              await elements
                .get("guided-intake-original-request")
                .dispatch("input");
              assert.strictEqual(
                vm.runInContext(
                  "guidedTransferredOriginalRequest",
                  sandbox,
                ),
                null,
              );
              assert.strictEqual(elements.get("guided-intake-capture").disabled, false);
              fetchQueue.push(() => Promise.resolve(response(completedState)));
              await elements.get("guided-intake-capture").dispatch("click");
              await settle();
              const manualCaptureRequest = fetchCalls.at(-1);
              assert.strictEqual(
                manualCaptureRequest.path,
                "/api/guided-intake/capture",
              );
              assert.deepStrictEqual(
                JSON.parse(manualCaptureRequest.options.body),
                {
                  original_request: manualOriginalRequest,
                  supersedes_request_id: "GUIDED-REQUEST-ONE",
                },
              );

              fetchQueue.push(() => Promise.resolve(response(completedState)));
              await elements.get("guided-intake-copy").dispatch("click");
              await settle();
              assert.strictEqual(
                fetchCalls.at(-1).path,
                "/api/guided-intake/copy",
              );
              assert.strictEqual(
                clipboardWrites.at(-1),
                "HOSTILE <PROMPT> & COPY",
              );

              elements.get("guided-intake-producer-label").value =
                "Pro <producer>";
              elements.get("guided-intake-draft-json").value = "[]";
              await elements.get("guided-intake-producer-label").dispatch("input");
              await elements.get("guided-intake-draft-json").dispatch("input");
              const beforeInvalidDraft = fetchCalls.length;
              await elements.get("guided-intake-import-draft").dispatch("click");
              await settle();
              assert.strictEqual(fetchCalls.length, beforeInvalidDraft);
              assert.strictEqual(
                elements.get("guided-intake-error").textContent,
                "Guided Intake draft must be a strict JSON object.",
              );
              elements.get("guided-intake-draft-json").value =
                '{"objective":{"text":"one"},"objective":{"text":"<script>draft</script>"}}';
              await elements.get("guided-intake-draft-json").dispatch("input");
              fetchQueue.push(() => Promise.resolve(response(completedState)));
              await elements.get("guided-intake-import-draft").dispatch("click");
              await settle();
              const importRequest = fetchCalls.at(-1);
              assert.strictEqual(
                importRequest.path,
                "/api/guided-intake/import-draft",
              );
              assert.deepStrictEqual(
                JSON.parse(importRequest.options.body),
                {
                  draft_json:
                    '{"objective":{"text":"one"},"objective":{"text":"<script>draft</script>"}}',
                  producer_label: "Pro <producer>",
                },
              );

              elements.get("guided-intake-answer").value =
                "Yes, exact <answer>.";
              elements.get("guided-intake-resulting-delta").value =
                '{"completion_line":{"text":"Done & verified"}}';
              await elements.get("guided-intake-answer").dispatch("input");
              await elements.get("guided-intake-resulting-delta").dispatch("input");
              assert.strictEqual(elements.get("guided-intake-confirm").disabled, false);
              fetchQueue.push(() =>
                Promise.resolve(response(confirmedGuidedState)),
              );
              await elements.get("guided-intake-confirm").dispatch("click");
              await settle();
              const confirmRequest = fetchCalls.at(-1);
              assert.strictEqual(
                confirmRequest.path,
                "/api/guided-intake/confirm",
              );
              assert.deepStrictEqual(
                JSON.parse(confirmRequest.options.body),
                {
                  question: "Is <this> the exact completion line?",
                  answer: "Yes, exact <answer>.",
                  resulting_delta: {
                    completion_line: { text: "Done & verified" },
                  },
                },
              );
              assert.strictEqual(elements.get("guided-intake-freeze").disabled, false);

              fetchQueue.push(() => Promise.resolve(response(frozenGuidedState)));
              await elements.get("guided-intake-freeze").dispatch("click");
              await settle();
              assert.strictEqual(
                fetchCalls.at(-1).path,
                "/api/guided-intake/freeze",
              );
              assert.strictEqual(
                elements
                  .get("guided-intake-freeze-identity")
                  .textContent.includes("GUIDED-FREEZE-ONE"),
                true,
              );
              assert.strictEqual(elements.get("guided-intake-transfer").disabled, false);

              assert.strictEqual(
                elements.get("guided-intake-producer-label").disabled,
                false,
              );
              assert.strictEqual(
                elements.get("guided-intake-draft-json").disabled,
                false,
              );
              assert.strictEqual(
                elements.get("guided-intake-import-draft").disabled,
                false,
              );
              elements.get("guided-intake-draft-json").value =
                '{"forward_correction":"after current freeze"}';
              await elements.get("guided-intake-draft-json").dispatch("input");
              fetchQueue.push(() =>
                Promise.resolve(response(correctedAfterFreezeState)),
              );
              await elements.get("guided-intake-import-draft").dispatch("click");
              await settle();
              const postFreezeImportRequest = fetchCalls.at(-1);
              assert.strictEqual(
                postFreezeImportRequest.path,
                "/api/guided-intake/import-draft",
              );
              assert.deepStrictEqual(
                JSON.parse(postFreezeImportRequest.options.body),
                {
                  draft_json:
                    '{"forward_correction":"after current freeze"}',
                  producer_label: "Pro <producer>",
                },
              );
              assert.strictEqual(elements.get("guided-intake-transfer").disabled, true);
              assert.strictEqual(elements.get("guided-intake-freeze").disabled, false);
              assert.strictEqual(
                elements
                  .get("guided-intake-freeze-identity")
                  .textContent.includes('"current": false'),
                true,
              );

              fetchQueue.push(() => Promise.resolve(response(refrozenGuidedState)));
              await elements.get("guided-intake-freeze").dispatch("click");
              await settle();
              assert.strictEqual(
                fetchCalls.at(-1).path,
                "/api/guided-intake/freeze",
              );
              assert.strictEqual(
                elements
                  .get("guided-intake-freeze-identity")
                  .textContent.includes("GUIDED-FREEZE-TWO"),
                true,
              );
              assert.strictEqual(elements.get("guided-intake-transfer").disabled, false);

              fetchQueue.push(() =>
                Promise.resolve(response(transferredGuidedState)),
              );
              await elements.get("guided-intake-transfer").dispatch("click");
              await settle();
              assert.strictEqual(
                fetchCalls.at(-1).path,
                "/api/guided-intake/transfer-to-bridge",
              );
              assert.strictEqual(
                elements
                  .get("guided-intake-transfer-receipt")
                  .textContent.includes("GUIDED-TRANSFER-ONE"),
                true,
              );
              assert.strictEqual(elements.get("guided-intake-transfer").disabled, true);

              elements.get("guided-intake-purge-confirm").checked = true;
              await elements.get("guided-intake-purge-confirm").dispatch("input");
              assert.strictEqual(
                elements.get("guided-intake-purge").disabled,
                false,
              );
              fetchQueue.push(() =>
                Promise.resolve(response(changedPurgeIdentityState)),
              );
              await runNextTimer();
              assert.strictEqual(
                elements.get("guided-intake-purge-confirm").checked,
                false,
              );
              assert.strictEqual(
                elements.get("guided-intake-purge").disabled,
                true,
              );
              fetchQueue.push(() =>
                Promise.resolve(response(transferredGuidedState)),
              );
              await runNextTimer();

              const beforeUnconfirmedPurge = fetchCalls.length;
              await elements.get("guided-intake-purge").dispatch("click");
              await settle();
              assert.strictEqual(fetchCalls.length, beforeUnconfirmedPurge);
              assert.strictEqual(
                elements.get("guided-intake-error").textContent,
                "Explicit Original Request purge confirmation is required.",
              );

              elements.get("guided-intake-purge-confirm").checked = true;
              await elements.get("guided-intake-purge-confirm").dispatch("input");
              assert.strictEqual(
                elements.get("guided-intake-purge").disabled,
                false,
              );
              fetchQueue.push(() =>
                Promise.resolve(response(purgedGuidedState)),
              );
              await elements.get("guided-intake-purge").dispatch("click");
              await settle();
              const purgeRequest = fetchCalls.at(-1);
              assert.strictEqual(
                purgeRequest.path,
                "/api/guided-intake/purge",
              );
              assert.deepStrictEqual(
                JSON.parse(purgeRequest.options.body),
                {
                  request_id: "GUIDED-REQUEST-ONE",
                  request_sha256: "GUIDED-REQUEST-HASH",
                  confirmed: true,
                },
              );
              assert.strictEqual(
                elements.get("guided-intake-state").textContent,
                "BLOCK — ORIGINAL REQUEST UNAVAILABLE",
              );
            assert.strictEqual(
              elements.get("guided-intake-original-exact").textContent,
              "UNAVAILABLE",
            );
            assert.strictEqual(
              elements.get("guided-intake-original-request").value,
              "",
            );
            assert.strictEqual(
              elements.get("guided-intake-raw-source-availability").textContent,
              "UNAVAILABLE",
              );
              assert.strictEqual(
                elements.get("guided-intake-judgment-reuse").textContent,
                "BLOCKED",
              );
              assert.strictEqual(
                elements.get("guided-intake-fidelity-evaluation").textContent,
                "BLOCKED",
              );
              assert.strictEqual(
                elements
                  .get("guided-intake-purge-status")
                  .textContent.includes("GI-PURGE-ONE"),
                true,
              );
              assert.strictEqual(
                elements
                  .get("guided-intake-purge-status")
                  .textContent.includes(
                    "DELETED_NO_NON_PURGED_REFERENCES",
                  ),
                true,
              );
              assert.strictEqual(
                elements.get("guided-intake-purge-confirm").checked,
                false,
              );
              assert.strictEqual(
                elements.get("guided-intake-purge-confirm").disabled,
                true,
              );
              assert.strictEqual(
                elements.get("guided-intake-purge").disabled,
                true,
              );
              assert.strictEqual(elements.get("guided-intake-copy").disabled, true);
              assert.strictEqual(elements.get("guided-intake-freeze").disabled, true);
              assert.strictEqual(elements.get("guided-intake-transfer").disabled, true);
              const guidedFetches = fetchCalls.slice(guidedFetchStart);
              const guidedMutationFetches = guidedFetches.filter(
                (call) => call.options.method === "POST",
              );
              assert.strictEqual(
                guidedMutationFetches.every((call) =>
                  call.path.startsWith("/api/guided-intake/"),
                ),
                true,
              );
              assert.strictEqual(
                guidedFetches.some((call) => call.path === "/api/run"),
                false,
              );

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

              elements.get("bridge-objective").value = "STALE_BOUNDARY_DRAFT";
              elements.get("bridge-role").value = "PRO_DESIGN";
              elements.get("bridge-source").value = "STALE_SOURCE_DRAFT";
              elements.get("bridge-file").value = "STALE_FILE_SELECTION";
              elements.get("bridge-paste").value = "STALE_RAW_PROSE";
              elements.get("bridge-metadata").value = '{"stale":true}';
              elements.get("bridge-replay-baseline").value = '{"stale":"base"}';
              elements.get("bridge-replay-candidate").value =
                '{"stale":"candidate"}';
              elements.get("guided-intake-original-request").value =
                "STALE_GUIDED_REQUEST";
              elements.get("guided-intake-producer-label").value =
                "STALE_GUIDED_PRODUCER";
              elements.get("guided-intake-draft-json").value =
                '{"stale":"draft"}';
              elements.get("guided-intake-answer").value =
                "STALE_GUIDED_ANSWER";
              elements.get("guided-intake-resulting-delta").value =
                '{"stale":"delta"}';

              let resolveAfterDisconnect;
              let disconnectFileReads = 0;
              const disconnectReadyContent =
                "Transfer-ready before disconnect\r\nUnicode: 契約\n";
              const pendingAtDisconnectFile = {
                name: "pending-at-disconnect.md",
                text() {
                  disconnectFileReads += 1;
                  if (disconnectFileReads === 1) {
                    return Promise.resolve(disconnectReadyContent);
                  }
                  return new Promise((resolve) => {
                    resolveAfterDisconnect = resolve;
                  });
                },
              };
              elements.get("contract-file").files = [pendingAtDisconnectFile];
              await elements.get("contract-file").dispatch("input");
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              await elements.get("contract-import").dispatch("click");
              await settle();
              assert.strictEqual(disconnectFileReads, 1);
              assert.strictEqual(
                vm.runInContext("importedContract.content", sandbox),
                disconnectReadyContent,
              );
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                false,
              );
              const disconnectUseFetchStart = fetchCalls.length;
              await elements
                .get("contract-use-guided-intake")
                .dispatch("click");
              await settle();
              assert.strictEqual(fetchCalls.length, disconnectUseFetchStart);
              assert.strictEqual(
                vm.runInContext(
                  "guidedTransferredOriginalRequest.content",
                  sandbox,
                ),
                disconnectReadyContent,
              );
              assert.strictEqual(
                elements.get("guided-intake-original-request").value,
                disconnectReadyContent.replace(/\r\n?/g, "\n"),
              );
              const importPendingAtDisconnect =
                elements.get("contract-import").dispatch("click");
              await settle();
              assert.strictEqual(disconnectFileReads, 2);
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                false,
              );

              fetchQueue.push(() =>
                Promise.reject(new TypeError("fetch failed")),
              );
              await runNextTimer();
              resolveAfterDisconnect("late content must stay discarded");
              await importPendingAtDisconnect;
              await settle();

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
              assert.strictEqual(elements.get("contract-file").value, "");
              assert.strictEqual(elements.get("contract-file").files.length, 0);
              assert.strictEqual(elements.get("contract-file").disabled, true);
              assert.strictEqual(elements.get("contract-import").disabled, true);
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              assert.strictEqual(
                elements.get("contract-import-state").textContent,
                "No contract",
              );
              assert.strictEqual(
                elements.get("contract-full-content").value,
                "",
              );
              assert.strictEqual(
                vm.runInContext("importedContract", sandbox),
                null,
              );
              assert.strictEqual(
                vm.runInContext(
                  "guidedTransferredOriginalRequest",
                  sandbox,
                ),
                null,
              );
              assert.strictEqual(hidden("contract-preview"), true);
              assert.strictEqual(hidden("contract-import-error"), true);
              assert.strictEqual(
                hidden("intelligence-transplant-card"),
                true,
              );
              for (const id of [
                "intelligence-transplant-run-id",
                "intelligence-transplant-execution-status",
                "intelligence-transplant-delta-state",
                "intelligence-transplant-structural-validation",
                "intelligence-transplant-authority-provenance",
                "intelligence-transplant-cryptographic-provenance",
                "intelligence-transplant-generalized-transplant",
                "intelligence-transplant-next-action",
                "intelligence-transplant-active-cap",
                "intelligence-transplant-evidence-objects",
                "intelligence-transplant-lineage",
                "intelligence-transplant-error",
              ]) {
                assert.strictEqual(elements.get(id).textContent, "", id);
              }
              assert.strictEqual(
                elements.get("guided-intake-state").textContent,
                "No intake",
              );
              assert.strictEqual(
                elements.get("guided-intake-authority-claim").textContent,
                "INTERPRETATION ONLY — NO EXECUTION AUTHORITY",
              );
              assert.strictEqual(
                elements.get("guided-intake-authority-explanation").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-original-exact").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-raw-source-availability").textContent,
                "UNKNOWN",
              );
              assert.strictEqual(
                elements.get("guided-intake-judgment-reuse").textContent,
                "UNKNOWN",
              );
              assert.strictEqual(
                elements.get("guided-intake-fidelity-evaluation").textContent,
                "UNKNOWN",
              );
              assert.strictEqual(
                elements.get("guided-intake-purge-status").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-purge-confirm").checked,
                false,
              );
              assert.strictEqual(
                elements.get("guided-intake-objective-atoms").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-completion-checks").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-confirmation-history").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-copy-output").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-freeze-identity").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-transfer-receipt").textContent,
                "",
              );
              assert.strictEqual(hidden("guided-intake-confirmation"), true);
              assert.strictEqual(hidden("guided-intake-error"), true);
              assert.strictEqual(
                elements.get("bridge-state").textContent,
                "No session",
              );
              assert.strictEqual(
                elements.get("bridge-copy-output").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("bridge-handoff-output").textContent,
                "",
              );
              assert.strictEqual(
                elements.get("bridge-identities").textContent,
                "No artifacts imported.",
              );
              assert.strictEqual(
                elements.get("bridge-protocol-result").textContent,
                "IN PROGRESS / NOT FINAL",
              );
              assert.strictEqual(
                elements.get("bridge-product-result").textContent,
                "BUILDER EVIDENCE ONLY / INDEPENDENT AUDIT REQUIRED",
              );
              assert.strictEqual(
                elements.get("bridge-replay-result").textContent,
                "NOT YET PERFORMED",
              );
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
              for (const id of guidedIntakeButtonIds) {
                assert.strictEqual(elements.get(id).disabled, true, id);
              }
              for (const id of guidedIntakeInputIds) {
                assert.strictEqual(elements.get(id).disabled, true, id);
              }
              for (const id of bridgeButtonIds) {
                assert.strictEqual(elements.get(id).disabled, true, id);
              }
              for (const id of bridgeInputIds) {
                assert.strictEqual(elements.get(id).disabled, true, id);
              }
              assert.strictEqual(elements.get("bridge-objective").value, "");
              assert.strictEqual(elements.get("bridge-role").value, "");
              assert.strictEqual(elements.get("bridge-source").value, "");
              assert.strictEqual(elements.get("bridge-file").value, "");
              assert.strictEqual(elements.get("bridge-paste").value, "");
              assert.strictEqual(elements.get("bridge-metadata").value, "{}");
              assert.strictEqual(
                elements.get("bridge-replay-baseline").value,
                "{}",
              );
              assert.strictEqual(
                elements.get("bridge-replay-candidate").value,
                "{}",
              );
              assert.strictEqual(
                elements.get("guided-intake-original-request").value,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-producer-label").value,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-draft-json").value,
                "{}",
              );
              assert.strictEqual(
                elements.get("guided-intake-answer").value,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-resulting-delta").value,
                "{}",
              );
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
              assert.strictEqual(
                elements.get("contract-use-guided-intake").disabled,
                true,
              );
              assert.strictEqual(
                elements.get("guided-intake-state").textContent,
                "EMPTY",
              );
              assert.strictEqual(
                elements.get("guided-intake-objective-atoms").textContent,
                "[]",
              );
              assert.strictEqual(
                elements.get("guided-intake-completion-checks").textContent,
                "[]",
              );
              assert.strictEqual(
                elements.get("guided-intake-confirmation-history").textContent,
                "[]",
              );
              assert.strictEqual(
                elements.get("guided-intake-original-request").disabled,
                false,
              );
              assert.strictEqual(elements.get("guided-intake-capture").disabled, true);
              assert.strictEqual(elements.get("guided-intake-copy").disabled, true);
              assert.strictEqual(elements.get("guided-intake-freeze").disabled, true);
              assert.strictEqual(elements.get("guided-intake-transfer").disabled, true);
              assert.strictEqual(
                elements.get("bridge-state").textContent,
                "BOUNDARY_INCOMPLETE",
              );
              assert.strictEqual(elements.get("bridge-start").disabled, false);
              assert.strictEqual(elements.get("bridge-copy").disabled, true);
              assert.strictEqual(
                elements.get("bridge-product-result").textContent,
                "BUILDER EVIDENCE ONLY / INDEPENDENT AUDIT REQUIRED",
              );

              let oversizedRead = false;
              elements.get("bridge-role").value = "PRO_DESIGN";
              elements.get("bridge-file").files = [
                {
                  name: "oversized.bin",
                  size: 1024 * 1024 + 1,
                  async arrayBuffer() {
                    oversizedRead = true;
                    return new ArrayBuffer(0);
                  },
                },
              ];
              const fetchCountBeforeOversized = fetchCalls.length;
              await elements.get("bridge-import-file").dispatch("click");
              await settle();
              assert.strictEqual(oversizedRead, false);
              assert.strictEqual(fetchCalls.length, fetchCountBeforeOversized);
              assert.strictEqual(
                elements.get("global-error").textContent,
                "Artifact exceeds the 1 MiB Manual Bridge limit.",
              );

              elements.get("bridge-objective").value = "REPOSITORY_A_DRAFT";
              elements.get("bridge-role").value = "PRO_DESIGN";
              elements.get("bridge-source").value = "REPOSITORY_A_SOURCE";
              elements.get("bridge-file").value = "REPOSITORY_A_FILE";
              elements.get("bridge-paste").value = "REPOSITORY_A_PROSE";
              elements.get("bridge-metadata").value = '{"repo":"A"}';
              elements.get("bridge-replay-baseline").value = '{"repo":"A"}';
              elements.get("bridge-replay-candidate").value = '{"repo":"A"}';
              elements.get("guided-intake-original-request").value =
                "REPOSITORY_A_GUIDED_REQUEST";
              elements.get("guided-intake-producer-label").value =
                "REPOSITORY_A_GUIDED_PRODUCER";
              elements.get("guided-intake-draft-json").value =
                '{"repo":"A"}';
              elements.get("guided-intake-answer").value =
                "REPOSITORY_A_GUIDED_ANSWER";
              elements.get("guided-intake-resulting-delta").value =
                '{"repo":"A"}';
              fetchQueue.push(() =>
                Promise.resolve(response(switchedRepositoryState)),
              );
              await runNextTimer();
              assert.strictEqual(
                elements.get("repository-path").textContent,
                "/tmp/OTHER_REPOSITORY_PATH",
              );
              assert.strictEqual(elements.get("bridge-objective").value, "");
              assert.strictEqual(elements.get("bridge-role").value, "");
              assert.strictEqual(elements.get("bridge-source").value, "");
              assert.strictEqual(elements.get("bridge-file").value, "");
              assert.strictEqual(elements.get("bridge-paste").value, "");
              assert.strictEqual(elements.get("bridge-metadata").value, "{}");
              assert.strictEqual(
                elements.get("bridge-replay-baseline").value,
                "{}",
              );
              assert.strictEqual(
                elements.get("bridge-replay-candidate").value,
                "{}",
              );
              assert.strictEqual(
                elements.get("guided-intake-original-request").value,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-producer-label").value,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-draft-json").value,
                "{}",
              );
              assert.strictEqual(
                elements.get("guided-intake-answer").value,
                "",
              );
              assert.strictEqual(
                elements.get("guided-intake-resulting-delta").value,
                "{}",
              );

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

              fetchQueue.push(() => Promise.resolve(response(recoveredState)));
              await runNextTimer();
              assert.strictEqual(
                elements.get("global-error").textContent,
                "One bounded Run is already active.",
              );
              assert.strictEqual(hidden("global-error"), false);
              assert.strictEqual(elements.get("task").disabled, false);

              fetchQueue.push(() => Promise.resolve(response(recoveredState)));
              await elements.get("run").dispatch("click");
              await settle();
              assert.strictEqual(fetchCalls.at(-1).path, "/api/run");
              assert.strictEqual(hidden("global-error"), true);

              for (let index = 0; index < 2; index += 1) {
                fetchQueue.push(() =>
                  Promise.resolve(response(runtimeMismatchState)),
                );
                await runNextTimer();
                assert.strictEqual(
                  elements.get("run-error").textContent,
                  "The bounded Codex Run failed closed while verifying the runtime version.",
                );
                assert.strictEqual(hidden("progress-card"), false);
              }

              fetchQueue.push(() => Promise.resolve(response(recoveredState)));
              await runNextTimer();

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
