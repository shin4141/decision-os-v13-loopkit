from __future__ import annotations

from collections import deque
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from typing import Any
from unittest.mock import patch

from decision_os.acceleration.codex_adapter import (
    ADAPTER_NAME,
    CODEX_CLI_VERSION,
    CODEX_MODEL,
    CODEX_REASONING_EFFORT,
    CODEX_SERVICE_TIER,
    CodexAdapter,
    CodexAdapterFailure,
    CodexAdapterUnavailable,
    CodexApproval,
    CodexFailureDiagnostic,
    CodexLifecycleEvent,
    CodexRunResult,
    _SubprocessTransport,
    _redact_complete_source_echo,
    canonical_failure_diagnostic,
)
from decision_os.acceleration.engine import AccelerationEngine


def create_repository(parent: Path) -> Path:
    repository = parent / "repo"
    repository.mkdir()
    subprocess.run(
        ("git", "init", "-q", str(repository)),
        check=True,
        capture_output=True,
    )
    (repository / "target.txt").write_text("one\n", encoding="utf-8")
    subprocess.run(
        ("git", "-C", str(repository), "add", "target.txt"),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        (
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "initial",
        ),
        check=True,
        capture_output=True,
    )
    return repository


def change(
    *,
    path: str = "target.txt",
    kind: str = "update",
    move_path: str | None = None,
    diff: str = "@@ -1 +1 @@\n-one\n+two\n",
) -> dict[str, Any]:
    kind_value: dict[str, Any] = {"type": kind}
    if kind == "update":
        kind_value["move_path"] = move_path
    return {
        "diff": diff,
        "kind": kind_value,
        "path": path,
    }


def handshake_messages(
    repository: Path,
    *,
    thread_id: str,
    turn_id: str,
    model: str = CODEX_MODEL,
    effort: str = CODEX_REASONING_EFFORT,
    service_tier: str = CODEX_SERVICE_TIER,
    account_type: str = "chatgpt",
    catalog_effort: str = CODEX_REASONING_EFFORT,
    catalog_tier: str = CODEX_SERVICE_TIER,
    model_provider: str = "openai",
    approval_policy: str = "on-request",
    approvals_reviewer: str = "user",
    sandbox_type: str = "readOnly",
    network_access: bool = False,
    effective_cwd: str | None = None,
    ephemeral: bool = True,
    include_settings_update: bool = False,
) -> list[dict[str, Any]]:
    cwd = str(repository.resolve()) if effective_cwd is None else effective_cwd
    messages = [
        {
            "id": 1,
            "result": {
                "codexHome": "/tmp/codex-home",
                "platformFamily": "unix",
                "platformOs": "macos",
                "userAgent": f"codex_cli_rs/{CODEX_CLI_VERSION}",
            },
        },
        {
            "id": 2,
            "result": {
                "account": {
                    "email": None,
                    "planType": "pro",
                    "type": account_type,
                },
                "requiresOpenaiAuth": True,
            },
        },
        {
            "id": 3,
            "result": {
                "data": [
                    {
                        "id": CODEX_MODEL,
                        "model": CODEX_MODEL,
                        "serviceTiers": [
                            {
                                "description": "Fast",
                                "id": catalog_tier,
                                "name": "Fast",
                            }
                        ],
                        "supportedReasoningEfforts": [
                            {
                                "description": "Ultra",
                                "reasoningEffort": catalog_effort,
                            }
                        ],
                    }
                ]
            },
        },
        {
            "id": 4,
            "result": {
                "approvalPolicy": approval_policy,
                "approvalsReviewer": approvals_reviewer,
                "cwd": cwd,
                "model": model,
                "modelProvider": model_provider,
                "reasoningEffort": effort,
                "sandbox": {
                    "networkAccess": network_access,
                    "type": sandbox_type,
                },
                "serviceTier": service_tier,
                "thread": {
                    "cliVersion": CODEX_CLI_VERSION,
                    "cwd": cwd,
                    "ephemeral": ephemeral,
                    "id": thread_id,
                },
            },
        },
        {
            "id": 5,
            "result": {
                "turn": {
                    "id": turn_id,
                    "items": [],
                    "status": "inProgress",
                }
            },
        },
    ]
    if include_settings_update:
        messages.append(
            {
                "method": "thread/settings/updated",
                "params": {
                    "threadId": thread_id,
                    "threadSettings": {
                        "approvalPolicy": approval_policy,
                        "approvalsReviewer": approvals_reviewer,
                        "cwd": cwd,
                        "effort": effort,
                        "model": model,
                        "modelProvider": model_provider,
                        "sandboxPolicy": {
                            "networkAccess": network_access,
                            "type": sandbox_type,
                        },
                        "serviceTier": service_tier,
                    },
                },
            }
        )
    return messages


def started_item(
    *,
    thread_id: str,
    turn_id: str,
    item_id: str,
    changes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "method": "item/started",
        "params": {
            "item": {
                "changes": changes,
                "id": item_id,
                "status": "inProgress",
                "type": "fileChange",
            },
            "startedAtMs": 1,
            "threadId": thread_id,
            "turnId": turn_id,
        },
    }


def approval_request(
    *,
    thread_id: str,
    turn_id: str,
    item_id: str,
    request_id: str | int,
    method: str = "item/fileChange/requestApproval",
) -> dict[str, Any]:
    return {
        "id": request_id,
        "method": method,
        "params": {
            "itemId": item_id,
            "startedAtMs": 2,
            "threadId": thread_id,
            "turnId": turn_id,
        },
    }


def completed_item(
    *,
    thread_id: str,
    turn_id: str,
    item_id: str,
    changes: list[dict[str, Any]],
    status: str = "completed",
) -> dict[str, Any]:
    return {
        "method": "item/completed",
        "params": {
            "completedAtMs": 3,
            "item": {
                "changes": changes,
                "id": item_id,
                "status": status,
                "type": "fileChange",
            },
            "threadId": thread_id,
            "turnId": turn_id,
        },
    }


def completed_agent_message(
    *,
    thread_id: str,
    turn_id: str,
    text: str,
    phase: str = "final_answer",
) -> dict[str, Any]:
    return {
        "method": "item/completed",
        "params": {
            "completedAtMs": 4,
            "item": {
                "id": "agent-message-1",
                "phase": phase,
                "text": text,
                "type": "agentMessage",
            },
            "threadId": thread_id,
            "turnId": turn_id,
        },
    }


def started_read(
    *,
    thread_id: str,
    turn_id: str,
    call_id: str,
    path: str,
) -> dict[str, Any]:
    return {
        "method": "item/started",
        "params": {
            "item": {
                "arguments": {"path": path},
                "id": call_id,
                "status": "inProgress",
                "tool": "read_repository_text_file",
                "type": "dynamicToolCall",
            },
            "startedAtMs": 1,
            "threadId": thread_id,
            "turnId": turn_id,
        },
    }


def read_request(
    *,
    thread_id: str,
    turn_id: str,
    call_id: str,
    request_id: str | int,
    path: str,
) -> dict[str, Any]:
    return {
        "id": request_id,
        "method": "item/tool/call",
        "params": {
            "arguments": {"path": path},
            "callId": call_id,
            "threadId": thread_id,
            "tool": "read_repository_text_file",
            "turnId": turn_id,
        },
    }


def completed_read(
    *,
    thread_id: str,
    turn_id: str,
    call_id: str,
    path: str,
    status: str = "completed",
) -> dict[str, Any]:
    return {
        "method": "item/completed",
        "params": {
            "completedAtMs": 2,
            "item": {
                "arguments": {"path": path},
                "id": call_id,
                "status": status,
                "tool": "read_repository_text_file",
                "type": "dynamicToolCall",
            },
            "threadId": thread_id,
            "turnId": turn_id,
        },
    }


def read_messages(
    *,
    thread_id: str,
    turn_id: str,
    call_id: str,
    path: str,
    status: str = "completed",
) -> list[dict[str, Any]]:
    request_id = f"request-{call_id}"
    return [
        started_read(
            thread_id=thread_id,
            turn_id=turn_id,
            call_id=call_id,
            path=path,
        ),
        read_request(
            thread_id=thread_id,
            turn_id=turn_id,
            call_id=call_id,
            request_id=request_id,
            path=path,
        ),
        resolved_request(thread_id=thread_id, request_id=request_id),
        completed_read(
            thread_id=thread_id,
            turn_id=turn_id,
            call_id=call_id,
            path=path,
            status=status,
        ),
    ]


def resolved_request(
    *,
    thread_id: str,
    request_id: str | int,
) -> dict[str, Any]:
    return {
        "method": "serverRequest/resolved",
        "params": {
            "requestId": request_id,
            "threadId": thread_id,
        },
    }


def patch_updated(
    *,
    thread_id: str,
    turn_id: str,
    item_id: str,
    changes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "method": "item/fileChange/patchUpdated",
        "params": {
            "changes": changes,
            "itemId": item_id,
            "threadId": thread_id,
            "turnId": turn_id,
        },
    }


def completed_turn(
    *,
    thread_id: str,
    turn_id: str,
    status: str = "completed",
) -> dict[str, Any]:
    return {
        "method": "turn/completed",
        "params": {
            "threadId": thread_id,
            "turn": {
                "id": turn_id,
                "items": [],
                "status": status,
            },
        },
    }


def file_run_messages(
    repository: Path,
    *,
    thread_id: str,
    turn_id: str,
    item_id: str,
    file_changes: list[dict[str, Any]] | None = None,
    item_status: str = "completed",
    turn_status: str = "completed",
    include_item_completion: bool = True,
    **handshake_overrides: Any,
) -> list[dict[str, Any]]:
    changes = [change()] if file_changes is None else file_changes
    messages = handshake_messages(
        repository,
        thread_id=thread_id,
        turn_id=turn_id,
        **handshake_overrides,
    )
    if (
        len(changes) == 1
        and changes[0].get("kind", {}).get("type") == "update"
        and changes[0].get("kind", {}).get("move_path") in {None, ""}
        and isinstance(changes[0].get("path"), str)
        and not Path(changes[0]["path"]).is_absolute()
        and ".." not in Path(changes[0]["path"]).parts
    ):
        messages.extend(
            read_messages(
                thread_id=thread_id,
                turn_id=turn_id,
                call_id=f"read-{item_id}",
                path=changes[0]["path"],
            )
        )
    messages.extend(
        [
            started_item(
                thread_id=thread_id,
                turn_id=turn_id,
                item_id=item_id,
                changes=changes,
            ),
            approval_request(
                thread_id=thread_id,
                turn_id=turn_id,
                item_id=item_id,
                request_id=f"approval-{item_id}",
            ),
            resolved_request(
                thread_id=thread_id,
                request_id=f"approval-{item_id}",
            ),
        ]
    )
    if include_item_completion:
        messages.append(
            completed_item(
                thread_id=thread_id,
                turn_id=turn_id,
                item_id=item_id,
                changes=changes,
                status=item_status,
            )
        )
    messages.append(
        completed_turn(
            thread_id=thread_id,
            turn_id=turn_id,
            status=turn_status,
        )
    )
    return messages


class FakeTransport:
    def __init__(
        self,
        messages: list[dict[str, Any]],
        *,
        version: str = CODEX_CLI_VERSION,
    ) -> None:
        self.messages = deque(messages)
        self._version = version
        self.sent: list[dict[str, Any]] = []
        self.events: list[str] = []
        self.started = False
        self.closed = False

    @property
    def version(self) -> str:
        return self._version

    def start(self) -> None:
        self.started = True
        self.events.append("server_opened")

    def send(self, message: dict[str, Any]) -> None:
        if not self.started or self.closed:
            raise AssertionError("send requires an open control stream")
        self.sent.append(message)
        if "method" in message:
            self.events.append(f"sent:{message['method']}")
        elif "result" in message:
            decision = message["result"].get("decision", "response")
            self.events.append(f"approval_completed:{decision}")
        else:
            self.events.append("sent:error")

    def receive(self) -> dict[str, Any]:
        if not self.started or self.closed:
            raise AssertionError("receive requires an open control stream")
        if not self.messages:
            raise EOFError("fake app-server stream ended")
        message = self.messages.popleft()
        method = message.get("method")
        if method:
            self.events.append(f"received:{method}")
        else:
            self.events.append(f"received:response:{message.get('id')}")
        return message

    def close(self) -> None:
        self.closed = True
        self.events.append("server_closed")


class FakeTransportFactory:
    def __init__(
        self,
        scripts: list[list[dict[str, Any]]],
        *,
        versions: list[str] | None = None,
    ) -> None:
        self.scripts = deque(scripts)
        self.versions = deque(versions or [CODEX_CLI_VERSION] * len(scripts))
        self.transports: list[FakeTransport] = []

    def __call__(self, _executable: Path) -> FakeTransport:
        transport = FakeTransport(
            self.scripts.popleft(),
            version=self.versions.popleft(),
        )
        self.transports.append(transport)
        return transport


class FakeProcess:
    def __init__(self, stdout: str) -> None:
        self.stdin = io.StringIO()
        self.stdout = io.StringIO(stdout)
        self.stderr = io.StringIO()
        self.running = True
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return None if self.running else 0

    def terminate(self) -> None:
        self.terminated = True
        self.running = False

    def wait(self, timeout: int | None = None) -> int:
        del timeout
        self.running = False
        return 0

    def kill(self) -> None:
        self.killed = True
        self.running = False


def adapter_for(
    repository: Path,
    factory: FakeTransportFactory,
    *,
    choice: Any,
    output: io.StringIO | None = None,
) -> tuple[AccelerationEngine, CodexAdapter, io.StringIO]:
    engine = AccelerationEngine(
        repository,
        adapter=ADAPTER_NAME,
        adapter_version=CODEX_CLI_VERSION,
    )
    stdout = output or io.StringIO()
    return (
        engine,
        CodexAdapter(
            engine,
            input_func=choice,
            stdout=stdout,
            transport_factory=factory,
        ),
        stdout,
    )


class CodexAdapterTest(unittest.IsolatedAsyncioTestCase):
    def test_untrusted_failure_diagnostics_are_canonically_rebuilt(self) -> None:
        private = "PRIVATE raw exception, source, prompt, and secret"

        class Lookalike:
            code = "codex_thread_start_failed"
            protocol_phase = "thread_start"
            reason = private
            action = "expose_private_data"
            category = "PRIVATE_CATEGORY"
            jsonrpc_code = -32600
            protocol_method = "thread/start"

            def as_dict(self) -> dict[str, str]:
                raise AssertionError("untrusted as_dict must not be called")

        class DiagnosticSubclass(CodexFailureDiagnostic):
            def as_dict(self) -> dict[str, str]:
                return {"reason": private}

        canonical = CodexFailureDiagnostic.for_phase("thread_start")
        invalid_values: list[object] = [
            Lookalike(),
            DiagnosticSubclass(
                code=canonical.code,
                protocol_phase=canonical.protocol_phase,
                reason=canonical.reason,
                action=canonical.action,
            ),
        ]
        for field, value in (
            ("code", "PRIVATE_FAILURE"),
            ("protocol_phase", "private_phase"),
            ("reason", private),
            ("action", "expose_private_data"),
            ("category", "PRIVATE_CATEGORY"),
            ("jsonrpc_code", True),
            ("protocol_method", "private/method"),
        ):
            forged = CodexFailureDiagnostic.for_phase("thread_start")
            object.__setattr__(forged, field, value)
            invalid_values.append(forged)
        incomplete = object.__new__(CodexFailureDiagnostic)
        object.__setattr__(incomplete, "protocol_phase", "thread_start")
        invalid_values.append(incomplete)

        for value in invalid_values:
            with self.subTest(value_type=type(value).__name__):
                rebuilt = canonical_failure_diagnostic(value)
                self.assertEqual("unknown", rebuilt.protocol_phase)
                self.assertEqual("codex_unknown_failure", rebuilt.code)
                self.assertNotIn(private, json.dumps(rebuilt.as_dict()))

        rebuilt = canonical_failure_diagnostic(canonical)
        self.assertIsNot(canonical, rebuilt)
        self.assertEqual(canonical.as_dict(), rebuilt.as_dict())

    def test_allowed_value_cross_combinations_downgrade_to_unknown(
        self,
    ) -> None:
        cases = (
            (
                "thread_start",
                "jsonrpc_method_rejected",
                -32601,
                "turn/start",
            ),
            (
                "turn_start",
                "jsonrpc_invalid_params",
                -32602,
                "thread/start",
            ),
            (
                "model_verification",
                "jsonrpc_method_rejected",
                -32601,
                "account/read",
            ),
            (
                "thread_identity_verification",
                "jsonrpc_invalid_params",
                -32600,
                "thread/start",
            ),
            (
                "thread_start",
                "transport_or_process",
                -32000,
                "thread/start",
            ),
            (
                "thread_start",
                "unknown",
                -32601,
                "thread/start",
            ),
            (
                "thread_start",
                "jsonrpc_invalid_params",
                -32600,
                None,
            ),
        )

        for phase, category, code, method in cases:
            with self.subTest(
                phase=phase,
                category=category,
                code=code,
                method=method,
            ):
                forged = CodexFailureDiagnostic.for_phase(phase)
                object.__setattr__(forged, "category", category)
                object.__setattr__(forged, "jsonrpc_code", code)
                object.__setattr__(forged, "protocol_method", method)

                rebuilt = canonical_failure_diagnostic(forged)

                self.assertEqual(
                    CodexFailureDiagnostic.for_phase("unknown").as_dict(),
                    rebuilt.as_dict(),
                )

    def test_valid_thread_start_diagnostics_survive_canonical_rebuild(
        self,
    ) -> None:
        phase = CodexFailureDiagnostic.for_phase("thread_start")
        cases = (
            ("jsonrpc_method_rejected", -32601),
            ("jsonrpc_invalid_params", -32600),
            ("jsonrpc_invalid_params", -32602),
            ("state_or_filesystem", -32000),
            ("transport_or_process", None),
            ("unknown", -32600),
            ("unknown", None),
        )

        for category, code in cases:
            with self.subTest(category=category, code=code):
                diagnostic = CodexFailureDiagnostic(
                    code=phase.code,
                    protocol_phase=phase.protocol_phase,
                    reason=phase.reason,
                    action=phase.action,
                    category=category,
                    jsonrpc_code=code,
                    protocol_method="thread/start",
                )

                rebuilt = canonical_failure_diagnostic(diagnostic)

                self.assertIsNot(diagnostic, rebuilt)
                self.assertEqual(diagnostic.as_dict(), rebuilt.as_dict())

    async def test_safe_failure_diagnostics_distinguish_protocol_phases(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            thread_failure_messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )[:3]
            thread_failure_messages.append(
                {
                    "id": 4,
                    "error": {
                        "code": -32600,
                        "message": (
                            "thread/start.dynamicTools requires "
                            "experimentalApi capability; PRIVATE secret"
                        ),
                    },
                }
            )
            factory = FakeTransportFactory([thread_failure_messages])
            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("must not prompt"),
            )

            with self.assertRaises(CodexAdapterFailure) as captured:
                await adapter.run("thread failure")

            thread_diagnostic = captured.exception.diagnostic
            self.assertIsNotNone(thread_diagnostic)
            assert thread_diagnostic is not None
            self.assertEqual("codex_thread_start_failed", thread_diagnostic.code)
            self.assertEqual("thread_start", thread_diagnostic.protocol_phase)
            self.assertEqual(
                "jsonrpc_invalid_params",
                thread_diagnostic.category,
            )
            self.assertEqual(-32600, thread_diagnostic.jsonrpc_code)
            self.assertEqual("thread/start", thread_diagnostic.protocol_method)
            self.assertNotIn("PRIVATE", json.dumps(thread_diagnostic.as_dict()))
            self.assertNotIn("secret", json.dumps(thread_diagnostic.as_dict()))
            self.assertNotIn(
                "turn/start",
                [
                    message.get("method")
                    for message in factory.transports[0].sent
                ],
            )

            cases = (
                (
                    "settings_verification",
                    {
                        "method": "thread/settings/updated",
                        "params": {
                            "threadId": "thread-1",
                            "threadSettings": "PRIVATE settings secret",
                        },
                    },
                ),
                (
                    "dynamic_tool_call",
                    {
                        "id": "read-private",
                        "method": "item/tool/call",
                        "params": "PRIVATE repository source",
                    },
                ),
                (
                    "terminal_completion",
                    {
                        "method": "turn/completed",
                        "params": {
                            "threadId": "thread-1",
                            "turn": "PRIVATE terminal secret",
                        },
                    },
                ),
            )
            for phase, failure_message in cases:
                with self.subTest(phase=phase):
                    messages = handshake_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                    )
                    messages.append(failure_message)
                    case_factory = FakeTransportFactory([messages])
                    _, case_adapter, _ = adapter_for(
                        repository,
                        case_factory,
                        choice=lambda: self.fail("must not prompt"),
                    )

                    result = await case_adapter.run(f"{phase} failure")

                    diagnostic = result.failure_diagnostic
                    self.assertIsNotNone(diagnostic)
                    assert diagnostic is not None
                    self.assertEqual(phase, diagnostic.protocol_phase)
                    self.assertNotIn("PRIVATE", json.dumps(diagnostic.as_dict()))
                    self.assertNotIn("secret", json.dumps(diagnostic.as_dict()))
                    self.assertEqual((), result.file_actions)
                    self.assertEqual((), result.checkpoint_outcomes)

    def test_repaired_capability_qualifies_thread_without_starting_turn(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            before = subprocess.run(
                ("git", "-C", str(repository), "status", "--porcelain"),
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            messages = handshake_messages(
                repository,
                thread_id="thread-qualified",
                turn_id="unused-turn",
            )[:4]
            factory = FakeTransportFactory([messages])
            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("qualification must not prompt"),
            )
            transport = factory(adapter.executable)
            adapter._transport = transport

            try:
                transport.start()
                adapter._protocol_phase = "initialize_handshake"
                adapter._initialize()
                adapter._protocol_phase = "account_verification"
                adapter._verify_account()
                adapter._protocol_phase = "model_verification"
                adapter._verify_model_catalog()
                adapter._protocol_phase = "thread_start"
                adapter._start_thread()
            finally:
                transport.close()

            methods = [
                message.get("method")
                for message in transport.sent
                if "method" in message
            ]
            initialize = next(
                message
                for message in transport.sent
                if message.get("method") == "initialize"
            )
            self.assertEqual(
                {"experimentalApi": True},
                initialize["params"]["capabilities"],
            )
            self.assertIn("thread/start", methods)
            self.assertNotIn("turn/start", methods)
            self.assertEqual("thread-qualified", adapter._thread_id)
            after = subprocess.run(
                ("git", "-C", str(repository), "status", "--porcelain"),
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            self.assertEqual(before, after)

    async def test_thread_start_jsonrpc_categories_are_bounded(self) -> None:
        cases = (
            (-32601, "PRIVATE method secret", "jsonrpc_method_rejected"),
            (-32602, "PRIVATE schema secret", "jsonrpc_invalid_params"),
            (
                -32000,
                "Failed to create state database at /PRIVATE/path secret",
                "state_or_filesystem",
            ),
            (-32099, "PRIVATE arbitrary provider secret", "unknown"),
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            for code, message, category in cases:
                with self.subTest(code=code):
                    messages = handshake_messages(
                        repository,
                        thread_id="unused-thread",
                        turn_id="unused-turn",
                    )[:3]
                    messages.append(
                        {
                            "id": 4,
                            "error": {"code": code, "message": message},
                        }
                    )
                    factory = FakeTransportFactory([messages])
                    _, adapter, _ = adapter_for(
                        repository,
                        factory,
                        choice=lambda: self.fail("must not prompt"),
                    )

                    with self.assertRaises(CodexAdapterFailure) as captured:
                        await adapter.run("bounded thread failure")

                    diagnostic = captured.exception.diagnostic
                    self.assertIsNotNone(diagnostic)
                    assert diagnostic is not None
                    self.assertEqual(category, diagnostic.category)
                    self.assertEqual(code, diagnostic.jsonrpc_code)
                    self.assertEqual(
                        "thread/start",
                        diagnostic.protocol_method,
                    )
                    serialized = json.dumps(diagnostic.as_dict())
                    self.assertNotIn("PRIVATE", serialized)
                    self.assertNotIn("secret", serialized)

    async def test_thread_start_transport_failure_is_bounded(self) -> None:
        class FailingReceiveTransport(FakeTransport):
            def receive(self) -> dict[str, Any]:
                if self.messages:
                    return super().receive()
                raise CodexAdapterFailure(
                    "PRIVATE control stream path and secret"
                )

        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            transport = FailingReceiveTransport(
                handshake_messages(
                    repository,
                    thread_id="unused-thread",
                    turn_id="unused-turn",
                )[:3]
            )
            engine = AccelerationEngine(
                repository,
                adapter=ADAPTER_NAME,
                adapter_version=CODEX_CLI_VERSION,
            )
            adapter = CodexAdapter(
                engine,
                input_func=lambda: self.fail("must not prompt"),
                stdout=io.StringIO(),
                transport_factory=lambda _executable: transport,
            )

            with self.assertRaises(CodexAdapterFailure) as captured:
                await adapter.run("transport failure")

            diagnostic = captured.exception.diagnostic
            self.assertIsNotNone(diagnostic)
            assert diagnostic is not None
            self.assertEqual("transport_or_process", diagnostic.category)
            self.assertIsNone(diagnostic.jsonrpc_code)
            self.assertEqual("thread/start", diagnostic.protocol_method)
            self.assertNotIn("PRIVATE", json.dumps(diagnostic.as_dict()))

    async def test_first_failure_phase_latch_preserves_actual_boundary(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))

            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                [
                    {
                        "method": "turn/started",
                        "params": {
                            "threadId": "thread-1",
                            "turn": {"id": "wrong-turn"},
                        },
                    },
                    completed_turn(
                        thread_id="thread-1",
                        turn_id="turn-1",
                    ),
                ]
            )
            _, adapter, _ = adapter_for(
                repository,
                FakeTransportFactory([messages]),
                choice=lambda: self.fail("must not prompt"),
            )

            result = await adapter.run("turn identity failure")

            self.assertEqual(
                "turn_started",
                result.failure_diagnostic.protocol_phase,
            )

            deferred = handshake_messages(
                repository,
                thread_id="thread-2",
                turn_id="turn-2",
            )
            deferred.insert(
                3,
                {
                    "method": "thread/settings/updated",
                    "params": {
                        "threadId": "thread-2",
                        "threadSettings": "PRIVATE malformed settings",
                    },
                },
            )
            _, adapter, _ = adapter_for(
                repository,
                FakeTransportFactory([deferred]),
                choice=lambda: self.fail("must not prompt"),
            )

            with self.assertRaises(CodexAdapterFailure) as captured:
                await adapter.run("deferred settings failure")

            diagnostic = captured.exception.diagnostic
            self.assertIsNotNone(diagnostic)
            assert diagnostic is not None
            self.assertEqual(
                "settings_verification",
                diagnostic.protocol_phase,
            )
            self.assertNotIn("PRIVATE", json.dumps(diagnostic.as_dict()))

    async def test_item_failure_phases_follow_the_actual_item_type(self) -> None:
        cases = (
            (
                "agent_message",
                {
                    "id": "message-1",
                    "phase": "final_answer",
                    "text": 42,
                    "type": "agentMessage",
                },
            ),
            (
                "dynamic_tool_call",
                {
                    "id": "read-1",
                    "status": "completed",
                    "tool": "read_repository_text_file",
                    "type": "dynamicToolCall",
                },
            ),
            (
                "file_change_item",
                {
                    "changes": [],
                    "id": "file-1",
                    "status": "completed",
                    "type": "fileChange",
                },
            ),
        )
        for index, (expected_phase, item) in enumerate(cases, start=1):
            with self.subTest(expected_phase=expected_phase):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory))
                    thread_id = f"thread-{index}"
                    turn_id = f"turn-{index}"
                    messages = handshake_messages(
                        repository,
                        thread_id=thread_id,
                        turn_id=turn_id,
                    )
                    messages.extend(
                        [
                            {
                                "method": "item/completed",
                                "params": {
                                    "item": item,
                                    "threadId": thread_id,
                                    "turnId": turn_id,
                                },
                            },
                            completed_turn(
                                thread_id=thread_id,
                                turn_id=turn_id,
                            ),
                        ]
                    )
                    _, adapter, _ = adapter_for(
                        repository,
                        FakeTransportFactory([messages]),
                        choice=lambda: self.fail("must not prompt"),
                    )

                    result = await adapter.run("typed item failure")

                    diagnostic = result.failure_diagnostic
                    self.assertIsNotNone(diagnostic)
                    assert diagnostic is not None
                    self.assertEqual(
                        expected_phase,
                        diagnostic.protocol_phase,
                    )

    async def test_unsupported_item_phase_precedes_secondary_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                [
                    {
                        "method": "item/completed",
                        "params": {
                            "item": {
                                "id": "command-1",
                                "type": "commandExecution",
                            },
                            "threadId": "thread-1",
                            "turnId": "turn-1",
                        },
                    },
                    {
                        "method": "item/completed",
                        "params": "PRIVATE malformed secondary error",
                    },
                ]
            )
            _, adapter, _ = adapter_for(
                repository,
                FakeTransportFactory([messages]),
                choice=lambda: self.fail("must not prompt"),
            )

            result = await adapter.run("unsupported item failure")

            diagnostic = result.failure_diagnostic
            self.assertIsNotNone(diagnostic)
            assert diagnostic is not None
            self.assertEqual("unsupported_item", diagnostic.protocol_phase)
            self.assertEqual((), result.file_actions)
            self.assertNotIn("PRIVATE", json.dumps(diagnostic.as_dict()))

    async def test_later_failure_does_not_replace_first_latched_phase(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                [
                    {
                        "method": "turn/started",
                        "params": {
                            "threadId": "thread-1",
                            "turn": {"id": "wrong-turn"},
                        },
                    },
                    {
                        "method": "item/completed",
                        "params": "PRIVATE malformed secondary error",
                    },
                ]
            )
            _, adapter, _ = adapter_for(
                repository,
                FakeTransportFactory([messages]),
                choice=lambda: self.fail("must not prompt"),
            )

            result = await adapter.run("multiple failure signals")

            self.assertEqual(
                "turn_started",
                result.failure_diagnostic.protocol_phase,
            )

    def test_transport_start_distinguishes_version_and_process_failures(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "codex"
            executable.write_text("placeholder", encoding="utf-8")
            transport = _SubprocessTransport(executable)
            invalid_version = subprocess.CompletedProcess(
                args=(str(executable), "--version"),
                returncode=1,
                stdout="PRIVATE invalid version response",
                stderr="PRIVATE stderr",
            )
            with patch.object(subprocess, "run", return_value=invalid_version):
                with self.assertRaises(CodexAdapterFailure) as captured:
                    transport.start()
            diagnostic = captured.exception.diagnostic
            self.assertIsNotNone(diagnostic)
            assert diagnostic is not None
            self.assertEqual(
                "version_verification",
                diagnostic.protocol_phase,
            )
            self.assertNotIn("PRIVATE", json.dumps(diagnostic.as_dict()))

            valid_version = subprocess.CompletedProcess(
                args=(str(executable), "--version"),
                returncode=0,
                stdout=f"codex-cli {CODEX_CLI_VERSION}\n",
                stderr="",
            )
            transport = _SubprocessTransport(executable)
            with (
                patch.object(subprocess, "run", return_value=valid_version),
                patch.object(
                    subprocess,
                    "Popen",
                    side_effect=OSError("PRIVATE process path and secret"),
                ),
            ):
                with self.assertRaises(CodexAdapterUnavailable) as captured:
                    transport.start()
            diagnostic = captured.exception.diagnostic
            self.assertIsNotNone(diagnostic)
            assert diagnostic is not None
            self.assertEqual("transport_start", diagnostic.protocol_phase)
            self.assertNotIn("PRIVATE", json.dumps(diagnostic.as_dict()))

    def test_failure_diagnostic_rejects_unbounded_public_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "bounded"):
            CodexFailureDiagnostic(
                code="PRIVATE_FAILURE",
                protocol_phase="thread_start",
                reason="PRIVATE source body and secret",
                action="expose_private_data",
            )

    def test_complete_source_echo_guard_preserves_short_and_partial_text(
        self,
    ) -> None:
        cases = (
            ("Changed target safely.", "a"),
            ("Line one\n\nLine two\nLine three", "\n"),
            ("Concatenate safely; do not recatalog anything.", "cat"),
            (
                "Prefix alpha\nbeta only; gamma was not reproduced.",
                "alpha\nbeta\ngamma\n",
            ),
        )
        for message, source_content in cases:
            with self.subTest(source_content=source_content):
                self.assertEqual(
                    message,
                    _redact_complete_source_echo(message, source_content),
                )

        self.assertEqual(
            "unchanged",
            _redact_complete_source_echo("unchanged", ""),
        )

    def test_complete_source_echo_guard_redacts_only_exact_structures(
        self,
    ) -> None:
        marker = "[Repository source content withheld.]"
        source_content = "alpha\nbeta\ngamma\n"
        self.assertEqual(
            marker,
            _redact_complete_source_echo(
                f" \t\n{source_content} \n",
                source_content,
            ),
        )
        self.assertEqual(
            f"Prefix exact.\n\n```text\n{marker}\n```\n\nSuffix exact.",
            _redact_complete_source_echo(
                f"Prefix exact.\n\n```text\n{source_content}```\n\n"
                "Suffix exact.",
                source_content,
            ),
        )
        long_source = (
            "first bounded line\n"
            "second bounded line\n"
            "third bounded line\n"
        )
        self.assertEqual(
            f"Prefix exact.\n\n{marker}\n\nSuffix exact.",
            _redact_complete_source_echo(
                f"Prefix exact.\n\n{long_source}\nSuffix exact.",
                long_source,
            ),
        )

    def test_run_result_rejects_unbounded_unsupported_reason(self) -> None:
        common = {
            "run_id": "run-1",
            "normal_terminal": False,
            "error_type": None,
            "turn_status": "completed",
            "runtime_identity": None,
            "checkpoint_outcomes": (),
        }
        with self.assertRaisesRegex(ValueError, "bounded code"):
            CodexRunResult(
                **common,
                status="UNSUPPORTED_MUTATION",
                unsupported_reason="PRIVATE_PROMPT",
            )
        with self.assertRaisesRegex(ValueError, "must agree"):
            CodexRunResult(
                **common,
                status="UNSUPPORTED_MUTATION",
            )
        with self.assertRaisesRegex(ValueError, "must agree"):
            CodexRunResult(
                **common,
                status="ABNORMAL_TERMINAL",
                unsupported_reason="unsupported_request_method:other",
            )

    async def test_dynamic_read_returns_exact_typed_content_without_approval(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            before = (repository / "target.txt").read_bytes()
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                read_messages(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    call_id="read-1",
                    path="target.txt",
                )
            )
            messages.append(
                completed_agent_message(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    text="Before\none\nAfter",
                )
            )
            messages.append(
                completed_turn(thread_id="thread-1", turn_id="turn-1")
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, output = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("read must not prompt"),
            )

            result = await adapter.run("Read target.txt.")

            self.assertEqual("NORMAL_TERMINAL", result.status)
            self.assertTrue(result.normal_terminal)
            self.assertEqual(
                "Before\none\nAfter",
                result.final_message,
            )
            self.assertEqual("", output.getvalue())
            self.assertEqual([], engine.store.read_events())
            self.assertEqual(before, (repository / "target.txt").read_bytes())
            self.assertEqual((), result.file_actions)
            self.assertEqual(1, len(result.read_evidence))
            evidence = result.read_evidence[0]
            self.assertEqual("succeeded", evidence.status)
            self.assertEqual("target.txt", evidence.path)
            self.assertEqual(len(before), evidence.byte_count)
            self.assertEqual(hashlib.sha256(before).hexdigest(), evidence.sha256)
            expected_head = subprocess.run(
                ("git", "-C", str(repository), "rev-parse", "HEAD"),
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(expected_head, evidence.repository_identity)
            sent = factory.transports[0].sent
            thread_start = next(
                value for value in sent if value.get("method") == "thread/start"
            )
            self.assertIn(
                "Do not reproduce the complete repository source file in the "
                "final response. Report only what was changed, the path, and "
                "the bounded completion result.",
                thread_start["params"]["developerInstructions"],
            )
            self.assertEqual(
                [
                    {
                        "type": "function",
                        "name": "read_repository_text_file",
                        "description": (
                            "Read one existing strict UTF-8 text file inside "
                            "the selected repository before proposing a "
                            "modification to that same file."
                        ),
                        "inputSchema": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["path"],
                            "properties": {
                                "path": {"type": "string", "minLength": 1}
                            },
                        },
                    }
                ],
                thread_start["params"]["dynamicTools"],
            )
            response = next(
                value
                for value in sent
                if value.get("id") == "request-read-1"
            )
            self.assertTrue(response["result"]["success"])
            payload = json.loads(response["result"]["contentItems"][0]["text"])
            self.assertEqual(
                {
                    "bytes": len(before),
                    "content": "one\n",
                    "path": "target.txt",
                    "repository_identity": expected_head,
                    "sha256": hashlib.sha256(before).hexdigest(),
                },
                payload,
            )
            self.assertFalse(
                any(
                    "decision" in value.get("result", {})
                    for value in sent
                )
            )

    async def test_exact_dynamic_read_replay_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            replay = read_messages(
                thread_id="thread-1",
                turn_id="turn-1",
                call_id="read-1",
                path="target.txt",
            )
            messages.extend(replay[:2])
            messages.append(replay[1])
            messages.extend(replay[2:])
            messages.append(
                completed_turn(thread_id="thread-1", turn_id="turn-1")
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("read replay must not prompt"),
            )

            result = await adapter.run("Replay one read.")

            self.assertEqual("NORMAL_TERMINAL", result.status)
            self.assertEqual(1, len(result.read_evidence))
            self.assertEqual([], engine.store.read_events())
            responses = [
                value
                for value in factory.transports[0].sent
                if value.get("id") == "request-read-1"
            ]
            self.assertEqual(2, len(responses))
            self.assertEqual(responses[0], responses[1])

    async def test_second_read_and_changed_replay_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            (repository / "other.txt").write_text("other\n", encoding="utf-8")
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                read_messages(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    call_id="read-1",
                    path="target.txt",
                )
            )
            messages.extend(
                read_messages(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    call_id="read-2",
                    path="other.txt",
                    status="failed",
                )
            )
            messages.append(
                completed_turn(thread_id="thread-1", turn_id="turn-1")
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("read must not prompt"),
            )

            result = await adapter.run("Try two reads.")

            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertEqual("additional_read_target", result.unsupported_reason)
            self.assertEqual(
                ["succeeded", "failed"],
                [value.status for value in result.read_evidence],
            )
            self.assertEqual([], engine.store.read_events())
            response = next(
                value
                for value in factory.transports[0].sent
                if value.get("id") == "request-read-2"
            )
            self.assertFalse(response["result"]["success"])
            self.assertNotIn(
                "content",
                json.loads(response["result"]["contentItems"][0]["text"]),
            )

        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = handshake_messages(
                repository,
                thread_id="thread-2",
                turn_id="turn-2",
            )
            replay = read_messages(
                thread_id="thread-2",
                turn_id="turn-2",
                call_id="read-1",
                path="target.txt",
            )
            replay[-1] = completed_read(
                thread_id="thread-2",
                turn_id="turn-2",
                call_id="read-1",
                path="target.txt",
                status="failed",
            )
            messages.extend(replay[:2])
            messages.append(replay[1])
            messages.extend(replay[2:])
            messages.append(
                completed_turn(thread_id="thread-2", turn_id="turn-2")
            )
            factory = FakeTransportFactory([messages])
            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("read must not prompt"),
            )
            original = adapter._read_repository_file
            calls = 0

            def mutate_before_replay(path: str) -> tuple[str, bytes, str, str]:
                nonlocal calls
                calls += 1
                if calls == 2:
                    (repository / "target.txt").write_text(
                        "changed\n",
                        encoding="utf-8",
                    )
                return original(path)

            with patch.object(
                adapter,
                "_read_repository_file",
                side_effect=mutate_before_replay,
            ):
                result = await adapter.run("Replay after byte drift.")

            self.assertEqual("read_identity_changed", result.unsupported_reason)
            self.assertIsNone(result.error_type)
            self.assertEqual(
                ["succeeded", "failed"],
                [value.status for value in result.read_evidence],
            )

    async def test_read_path_and_encoding_failures_are_typed(self) -> None:
        cases = (
            ("/tmp/outside.txt", "read_path_outside_repository", None),
            ("../outside.txt", "read_path_outside_repository", None),
            (".git/config", "read_path_outside_repository", None),
            ("missing.txt", "read_path_not_found", None),
            ("directory", "read_path_not_regular_file", "directory"),
            ("invalid.txt", "read_file_not_utf8", "invalid"),
            ("large.txt", "read_file_too_large", "large"),
            ("escape.txt", "read_path_outside_repository", "symlink"),
            ("git-config.txt", "read_path_outside_repository", "git-symlink"),
        )
        for index, (path, reason, fixture) in enumerate(cases, start=1):
            with self.subTest(path=path):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    repository = create_repository(root)
                    if fixture == "directory":
                        (repository / path).mkdir()
                    elif fixture == "invalid":
                        (repository / path).write_bytes(b"\xff\xfe")
                    elif fixture == "large":
                        (repository / path).write_bytes(b"x" * 131_073)
                    elif fixture == "symlink":
                        outside = root / "outside.txt"
                        outside.write_text("outside\n", encoding="utf-8")
                        (repository / path).symlink_to(outside)
                    elif fixture == "git-symlink":
                        (repository / path).symlink_to(
                            repository / ".git" / "config"
                        )
                    thread_id = f"thread-{index}"
                    turn_id = f"turn-{index}"
                    messages = handshake_messages(
                        repository,
                        thread_id=thread_id,
                        turn_id=turn_id,
                    )
                    messages.extend(
                        read_messages(
                            thread_id=thread_id,
                            turn_id=turn_id,
                            call_id=f"read-{index}",
                            path=path,
                            status="failed",
                        )
                    )
                    messages.append(
                        completed_turn(thread_id=thread_id, turn_id=turn_id)
                    )
                    factory = FakeTransportFactory([messages])
                    engine, adapter, _ = adapter_for(
                        repository,
                        factory,
                        choice=lambda: self.fail("read must not prompt"),
                    )

                    result = await adapter.run("Rejected read.")

                    self.assertEqual("UNSUPPORTED_MUTATION", result.status)
                    self.assertEqual(reason, result.unsupported_reason)
                    self.assertEqual("failed", result.read_evidence[0].status)
                    self.assertEqual([], engine.store.read_events())

    async def test_modify_is_bound_to_read_path_and_current_preimage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                    )
                ]
            )
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: "1",
            )

            result = await adapter.run("Read then modify target.txt.")

            self.assertEqual("NORMAL_TERMINAL", result.status)
            self.assertEqual(1, len(result.read_evidence))
            self.assertEqual(1, len(result.file_actions))
            self.assertEqual(
                1,
                len(
                    [
                        event
                        for event in engine.store.read_events()
                        if event["event_type"] == "DECISION_CHECK"
                    ]
                ),
            )

        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = file_run_messages(
                repository,
                thread_id="thread-2",
                turn_id="turn-2",
                item_id="item-2",
                item_status="declined",
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("stale preimage must not prompt"),
            )
            original = adapter._read_repository_file
            calls = 0

            def mutate_before_approval(path: str) -> tuple[str, bytes, str, str]:
                nonlocal calls
                calls += 1
                if calls == 2:
                    (repository / "target.txt").write_text(
                        "changed\n",
                        encoding="utf-8",
                    )
                return original(path)

            with patch.object(
                adapter,
                "_read_repository_file",
                side_effect=mutate_before_approval,
            ):
                result = await adapter.run("Stale preimage.")

            self.assertEqual(
                "read_preimage_changed_before_approval",
                result.unsupported_reason,
            )
            self.assertEqual((), result.file_actions)
            self.assertEqual([], engine.store.read_events())
            decisions = [
                value["result"]["decision"]
                for value in factory.transports[0].sent
                if "decision" in value.get("result", {})
            ]
            self.assertEqual(["decline"], decisions)

        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            (repository / "other.txt").write_text("other\n", encoding="utf-8")
            changes = [change(path="other.txt")]
            messages = handshake_messages(
                repository,
                thread_id="thread-3",
                turn_id="turn-3",
            )
            messages.extend(
                read_messages(
                    thread_id="thread-3",
                    turn_id="turn-3",
                    call_id="read-3",
                    path="target.txt",
                )
            )
            messages.extend(
                [
                    started_item(
                        thread_id="thread-3",
                        turn_id="turn-3",
                        item_id="item-3",
                        changes=changes,
                    ),
                    approval_request(
                        thread_id="thread-3",
                        turn_id="turn-3",
                        item_id="item-3",
                        request_id="approval-item-3",
                    ),
                    resolved_request(
                        thread_id="thread-3",
                        request_id="approval-item-3",
                    ),
                    completed_item(
                        thread_id="thread-3",
                        turn_id="turn-3",
                        item_id="item-3",
                        changes=changes,
                        status="declined",
                    ),
                    completed_turn(thread_id="thread-3", turn_id="turn-3"),
                ]
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("mismatched path must not prompt"),
            )

            result = await adapter.run("Modify a different file.")

            self.assertEqual("read_write_path_mismatch", result.unsupported_reason)
            self.assertEqual((), result.file_actions)
            self.assertEqual([], engine.store.read_events())

    async def test_create_remains_supported_without_repository_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        file_changes=[change(path="created.txt", kind="add")],
                    )
                ]
            )
            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: "1",
            )

            result = await adapter.run("Create created.txt.")

            self.assertEqual("NORMAL_TERMINAL", result.status)
            self.assertEqual((), result.read_evidence)
            self.assertEqual("Create", result.file_actions[0].action)

    async def test_structured_approval_lifecycle_and_final_message_bridge(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = file_run_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
                item_id="item-1",
            )
            approval_message = next(
                message
                for message in messages
                if message.get("method")
                == "item/fileChange/requestApproval"
            )
            approval_message["params"]["reason"] = "Bounded reason."
            messages.insert(
                -1,
                completed_agent_message(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    text="Sanitized final result.",
                ),
            )
            factory = FakeTransportFactory([messages])
            engine = AccelerationEngine(
                repository,
                adapter=ADAPTER_NAME,
                adapter_version=CODEX_CLI_VERSION,
            )
            approvals: list[CodexApproval] = []
            lifecycle: list[CodexLifecycleEvent] = []
            adapter = CodexAdapter(
                engine,
                input_func=lambda: (_ for _ in ()).throw(
                    AssertionError("CLI input must not be used")
                ),
                stdout=io.StringIO(),
                transport_factory=factory,
                approval_provider=lambda approval: (
                    approvals.append(approval) or "1"
                ),
                lifecycle_sink=lifecycle.append,
            )

            result = await adapter.run("Modify target.txt once.")

            self.assertEqual("Sanitized final result.", result.final_message)
            self.assertEqual(1, len(approvals))
            self.assertEqual(
                CodexApproval(
                    repository_name="repo",
                    action="Modify",
                    normalized_scope="target.txt",
                    diff="@@ -1 +1 @@\n-one\n+two\n",
                    reason="Bounded reason.",
                ),
                approvals[0],
            )
            self.assertEqual(1, len(result.file_actions))
            self.assertEqual("Modify", result.file_actions[0].action)
            self.assertEqual(
                "target.txt",
                result.file_actions[0].normalized_scope,
            )
            self.assertEqual("one-time", result.file_actions[0].access)
            self.assertEqual("approved", result.file_actions[0].status)
            self.assertIsNone(result.unsupported_reason)
            self.assertEqual(
                [
                    "starting",
                    "runtime",
                    "account",
                    "model",
                    "run",
                    "working",
                    "approval",
                    "finalizing",
                ],
                [event.kind for event in lifecycle],
            )

    async def test_exact_file_item_replay_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            changes = [change()]
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                read_messages(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    call_id="read-item-1",
                    path="target.txt",
                )
            )
            messages.extend(
                [
                    started_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=changes,
                    ),
                    started_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=changes,
                    ),
                    approval_request(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        request_id="approval-item-1",
                    ),
                    approval_request(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        request_id="approval-item-1",
                    ),
                    approval_request(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        request_id="approval-item-1-retry",
                    ),
                    resolved_request(
                        thread_id="thread-1",
                        request_id="approval-item-1",
                    ),
                    resolved_request(
                        thread_id="thread-1",
                        request_id="approval-item-1",
                    ),
                    resolved_request(
                        thread_id="thread-1",
                        request_id="approval-item-1-retry",
                    ),
                    completed_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=changes,
                    ),
                    completed_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=changes,
                    ),
                    completed_turn(
                        thread_id="thread-1",
                        turn_id="turn-1",
                    ),
                ]
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, output = adapter_for(
                repository,
                factory,
                choice=lambda: "1",
            )

            result = await adapter.run("idempotent item replay")

            self.assertEqual("NORMAL_TERMINAL", result.status)
            self.assertTrue(result.normal_terminal)
            self.assertEqual(1, output.getvalue().count("Selection:"))
            self.assertEqual(1, len(result.file_actions))
            self.assertEqual({"item-1"}, adapter._completed_items)
            self.assertEqual(1, len(adapter._file_action_candidates))
            checks = [
                event
                for event in engine.store.read_events()
                if event["event_type"] == "DECISION_CHECK"
            ]
            self.assertEqual(1, len(checks))
            decisions = [
                message["result"]["decision"]
                for message in factory.transports[0].sent
                if "result" in message
                and "decision" in message["result"]
            ]
            self.assertEqual(["accept", "accept", "accept"], decisions)

    async def test_live_incident_distinct_same_scope_items_fail_closed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            changes = [change()]
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                read_messages(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    call_id="read-item-1",
                    path="target.txt",
                )
            )
            for index, item_id in enumerate(
                ("item-1", "item-2", "item-3"),
                start=1,
            ):
                messages.extend(
                    [
                        started_item(
                            thread_id="thread-1",
                            turn_id="turn-1",
                            item_id=item_id,
                            changes=changes,
                        ),
                        approval_request(
                            thread_id="thread-1",
                            turn_id="turn-1",
                            item_id=item_id,
                            request_id=f"approval-{index}",
                        ),
                        resolved_request(
                            thread_id="thread-1",
                            request_id=f"approval-{index}",
                        ),
                        completed_item(
                            thread_id="thread-1",
                            turn_id="turn-1",
                            item_id=item_id,
                            changes=changes,
                            status=(
                                "completed" if index == 1 else "declined"
                            ),
                        ),
                    ]
                )
            messages.append(
                completed_turn(thread_id="thread-1", turn_id="turn-1")
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, output = adapter_for(
                repository,
                factory,
                choice=lambda: "1",
            )

            result = await adapter.run("live incident shape")

            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertFalse(result.normal_terminal)
            self.assertIsNone(result.error_type)
            self.assertEqual(
                "duplicate_file_action_item_after_completion",
                result.unsupported_reason,
            )
            self.assertEqual(1, output.getvalue().count("Selection:"))
            self.assertEqual(1, len(result.file_actions))
            self.assertEqual("target.txt", result.file_actions[0].normalized_scope)
            self.assertEqual({"item-1"}, adapter._completed_items)
            self.assertEqual({"item-2", "item-3"}, adapter._declined_items)
            checks = [
                event
                for event in engine.store.read_events()
                if event["event_type"] == "DECISION_CHECK"
            ]
            self.assertEqual(1, len(checks))
            self.assertEqual("item-1", checks[0]["source_interrupt_id"])
            decisions = [
                message["result"]["decision"]
                for message in factory.transports[0].sent
                if "result" in message
                and "decision" in message["result"]
            ]
            self.assertEqual(["accept", "decline", "decline"], decisions)

    async def test_distinct_different_file_item_never_inherits_decision(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            first_changes = [change()]
            second_changes = [change(path="other.txt", kind="add")]
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                read_messages(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    call_id="read-item-1",
                    path="target.txt",
                )
            )
            messages.extend(
                [
                    started_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=first_changes,
                    ),
                    approval_request(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        request_id="approval-1",
                    ),
                    resolved_request(
                        thread_id="thread-1",
                        request_id="approval-1",
                    ),
                    completed_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=first_changes,
                    ),
                    started_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-2",
                        changes=second_changes,
                    ),
                    approval_request(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-2",
                        request_id="approval-2",
                    ),
                    resolved_request(
                        thread_id="thread-1",
                        request_id="approval-2",
                    ),
                    completed_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-2",
                        changes=second_changes,
                        status="declined",
                    ),
                    completed_turn(
                        thread_id="thread-1",
                        turn_id="turn-1",
                    ),
                ]
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, output = adapter_for(
                repository,
                factory,
                choice=lambda: "1",
            )

            result = await adapter.run("different second item")

            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertEqual(
                "additional_file_action_item",
                result.unsupported_reason,
            )
            self.assertEqual(1, output.getvalue().count("Selection:"))
            self.assertEqual(1, len(result.file_actions))
            self.assertEqual({"item-1"}, adapter._completed_items)
            checks = [
                event
                for event in engine.store.read_events()
                if event["event_type"] == "DECISION_CHECK"
            ]
            self.assertEqual(1, len(checks))
            decisions = [
                message["result"]["decision"]
                for message in factory.transports[0].sent
                if "result" in message
                and "decision" in message["result"]
            ]
            self.assertEqual(["accept", "decline"], decisions)

    async def test_denied_item_cannot_be_reused_or_upgraded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            changes = [change()]
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                read_messages(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    call_id="read-item-1",
                    path="target.txt",
                )
            )
            for index, item_id in enumerate(("item-1", "item-2"), start=1):
                messages.extend(
                    [
                        started_item(
                            thread_id="thread-1",
                            turn_id="turn-1",
                            item_id=item_id,
                            changes=changes,
                        ),
                        approval_request(
                            thread_id="thread-1",
                            turn_id="turn-1",
                            item_id=item_id,
                            request_id=f"approval-{index}",
                        ),
                        resolved_request(
                            thread_id="thread-1",
                            request_id=f"approval-{index}",
                        ),
                        completed_item(
                            thread_id="thread-1",
                            turn_id="turn-1",
                            item_id=item_id,
                            changes=changes,
                            status="declined",
                        ),
                    ]
                )
            messages.append(
                completed_turn(thread_id="thread-1", turn_id="turn-1")
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, output = adapter_for(
                repository,
                factory,
                choice=lambda: "3",
            )

            result = await adapter.run("deny and repeat")

            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertEqual(
                "duplicate_file_action_item_after_completion",
                result.unsupported_reason,
            )
            self.assertEqual(1, output.getvalue().count("Selection:"))
            self.assertEqual(1, len(result.file_actions))
            self.assertEqual("denied", result.file_actions[0].status)
            self.assertEqual(set(), adapter._completed_items)
            checks = [
                event
                for event in engine.store.read_events()
                if event["event_type"] == "DECISION_CHECK"
            ]
            self.assertEqual(1, len(checks))
            decisions = [
                message["result"]["decision"]
                for message in factory.transports[0].sent
                if "result" in message
                and "decision" in message["result"]
            ]
            self.assertEqual(["decline", "decline"], decisions)

    async def test_two_fresh_threads_create_default_then_verified_save(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                    ),
                    file_run_messages(
                        repository,
                        thread_id="thread-2",
                        turn_id="turn-2",
                        item_id="item-2",
                    ),
                ]
            )
            choices = iter(("2",))
            engine, adapter, output = adapter_for(
                repository,
                factory,
                choice=lambda: next(choices),
            )

            first = await adapter.run("first")
            second = await adapter.run("second")

            self.assertEqual("NORMAL_TERMINAL", first.status)
            self.assertTrue(first.normal_terminal)
            self.assertEqual("VERIFIED_SAVE", second.status)
            self.assertTrue(second.normal_terminal)
            self.assertNotEqual(first.run_id, second.run_id)
            self.assertEqual("newly-saved", first.file_actions[0].access)
            self.assertEqual("reused", second.file_actions[0].access)
            self.assertEqual((1, 1), engine.store.counters())
            self.assertEqual(1, output.getvalue().count("Selection:"))
            events = engine.store.read_events()
            checks = [
                event
                for event in events
                if event["event_type"] == "DECISION_CHECK"
            ]
            self.assertEqual(2, len(checks))
            self.assertEqual(
                checks[0]["decision_key"],
                checks[1]["decision_key"],
            )
            self.assertTrue(
                any(
                    event["event_type"] == "INTERRUPT_SKIPPED"
                    for event in events
                )
            )
            for transport in factory.transports:
                methods = [
                    message.get("method")
                    for message in transport.sent
                    if "method" in message
                ]
                self.assertIn("thread/start", methods)
                self.assertNotIn("thread/resume", methods)
                approvals = [
                    message["result"]["decision"]
                    for message in transport.sent
                    if "result" in message
                    and "decision" in message["result"]
                ]
                self.assertEqual(["accept"], approvals)
                self.assertNotIn("acceptForSession", approvals)
            turn_thread_ids = [
                next(
                    message["params"]["threadId"]
                    for message in transport.sent
                    if message.get("method") == "turn/start"
                )
                for transport in factory.transports
            ]
            self.assertEqual(["thread-1", "thread-2"], turn_thread_ids)

    async def test_later_verified_reuse_keeps_final_reused_label(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id=f"thread-{index}",
                        turn_id=f"turn-{index}",
                        item_id=f"item-{index}",
                    )
                    for index in range(1, 4)
                ]
            )
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: "2",
            )

            first = await adapter.run("create default")
            second = await adapter.run("verify save")
            third = await adapter.run("verify reuse")

            self.assertEqual("NORMAL_TERMINAL", first.status)
            self.assertEqual("VERIFIED_SAVE", second.status)
            self.assertEqual("VERIFIED_REUSE", third.status)
            self.assertEqual("newly-saved", first.file_actions[0].access)
            self.assertEqual("reused", second.file_actions[0].access)
            self.assertEqual("reused", third.file_actions[0].access)
            self.assertEqual((1, 2), engine.store.counters())

    async def test_control_stream_stays_open_through_terminal_checkpoint(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                    )
                ]
            )
            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: "1",
            )

            result = await adapter.run("modify")

            self.assertTrue(result.normal_terminal)
            events = factory.transports[0].events
            self.assertLess(
                events.index(
                    "received:item/fileChange/requestApproval"
                ),
                events.index("approval_completed:accept"),
            )
            self.assertLess(
                events.index("approval_completed:accept"),
                events.index(
                    "received:serverRequest/resolved",
                    events.index("approval_completed:accept"),
                ),
            )
            self.assertLess(
                events.index(
                    "received:serverRequest/resolved",
                    events.index("approval_completed:accept"),
                ),
                events.index(
                    "received:item/completed",
                    events.index("approval_completed:accept"),
                ),
            )
            self.assertLess(
                events.index(
                    "received:item/completed",
                    events.index("approval_completed:accept"),
                ),
                events.index("received:turn/completed"),
            )
            self.assertLess(
                events.index("received:turn/completed"),
                events.index("server_closed"),
            )

    async def test_thread_start_identity_reaches_human_without_initial_update(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            changes = [change()]
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                read_messages(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    call_id="read-item-1",
                    path="target.txt",
                )
            )
            messages.extend(
                [
                    started_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=changes,
                    ),
                    approval_request(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        request_id=0,
                    ),
                    resolved_request(
                        thread_id="thread-1",
                        request_id=0,
                    ),
                    completed_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=changes,
                    ),
                    completed_turn(
                        thread_id="thread-1",
                        turn_id="turn-1",
                    ),
                ]
            )
            factory = FakeTransportFactory([messages])
            callback_count = 0

            def choose_once() -> str:
                nonlocal callback_count
                callback_count += 1
                return "1"

            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=choose_once,
            )
            original_send = adapter._send
            approval_decisions: list[str] = []

            def assert_registered_before_send(
                message: dict[str, Any],
            ) -> None:
                result = message.get("result")
                if message.get("id") == 0 and isinstance(result, dict):
                    self.assertEqual(
                        "item-1",
                        adapter._approval_requests.get(0),
                    )
                    approval_decisions.append(result["decision"])
                original_send(message)

            with patch.object(
                adapter,
                "_send",
                side_effect=assert_registered_before_send,
            ):
                result = await adapter.run("modify")

            self.assertEqual(1, callback_count)
            self.assertEqual(["accept"], approval_decisions)
            self.assertEqual("NORMAL_TERMINAL", result.status)
            self.assertTrue(result.normal_terminal)
            self.assertIsNone(result.error_type)
            self.assertIsNotNone(result.runtime_identity)
            self.assertEqual({0: "item-1"}, adapter._approval_requests)
            self.assertEqual({0}, adapter._resolved_approval_requests)
            self.assertNotIn(
                "received:thread/settings/updated",
                factory.transports[0].events,
            )

    async def test_option_one_is_not_persisted_or_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                    )
                ]
            )
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: "1",
            )

            result = await adapter.run("allow once")

            self.assertEqual("NORMAL_TERMINAL", result.status)
            self.assertEqual((0, 0), engine.store.counters())
            event_types = {
                event["event_type"] for event in engine.store.read_events()
            }
            self.assertNotIn("HUMAN_DEFAULT_CREATED", event_types)
            self.assertNotIn("VERIFIED_SAVE", event_types)

    async def test_option_three_declines_without_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        item_status="declined",
                    )
                ]
            )
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: "3",
            )
            original_send = adapter._send

            def assert_registered_before_decline(
                message: dict[str, Any],
            ) -> None:
                result = message.get("result")
                if isinstance(result, dict) and "decision" in result:
                    self.assertEqual(
                        "item-1",
                        adapter._approval_requests.get(
                            "approval-item-1"
                        ),
                    )
                original_send(message)

            with patch.object(
                adapter,
                "_send",
                side_effect=assert_registered_before_decline,
            ):
                result = await adapter.run("deny")

            self.assertEqual("DENIED", result.status)
            self.assertFalse(result.normal_terminal)
            self.assertEqual((0, 0), engine.store.counters())
            self.assertEqual(1, len(result.file_actions))
            self.assertEqual("denied", result.file_actions[0].access)
            self.assertEqual("denied", result.file_actions[0].status)
            approvals = [
                message["result"]["decision"]
                for message in factory.transports[0].sent
                if "result" in message
                and "decision" in message["result"]
            ]
            self.assertEqual(["decline"], approvals)
            self.assertEqual(
                {"approval-item-1"},
                adapter._resolved_approval_requests,
            )

    async def test_incomplete_access_is_not_labeled_as_completed(
        self,
    ) -> None:
        cases = (
            ("1", False, "completed"),
            ("2", True, "failed"),
        )
        for index, (choice, include_completion, turn_status) in enumerate(
            cases,
            start=1,
        ):
            with self.subTest(choice=choice, turn_status=turn_status):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory))
                    factory = FakeTransportFactory(
                        [
                            file_run_messages(
                                repository,
                                thread_id=f"thread-{index}",
                                turn_id=f"turn-{index}",
                                item_id=f"item-{index}",
                                include_item_completion=include_completion,
                                turn_status=turn_status,
                            )
                        ]
                    )
                    _, adapter, _ = adapter_for(
                        repository,
                        factory,
                        choice=lambda: choice,
                    )

                    result = await adapter.run("incomplete access")

                    self.assertFalse(result.normal_terminal)
                    self.assertEqual((), result.file_actions)

    async def test_saved_permission_never_authorizes_distinct_same_run_item(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            same_change = [change()]
            messages.extend(
                read_messages(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    call_id="read-item-1",
                    path="target.txt",
                )
            )
            for item_id in ("item-1", "item-2"):
                messages.extend(
                    [
                        started_item(
                            thread_id="thread-1",
                            turn_id="turn-1",
                            item_id=item_id,
                            changes=same_change,
                        ),
                        approval_request(
                            thread_id="thread-1",
                            turn_id="turn-1",
                            item_id=item_id,
                            request_id=f"approval-{item_id}",
                        ),
                        resolved_request(
                            thread_id="thread-1",
                            request_id=f"approval-{item_id}",
                        ),
                        completed_item(
                            thread_id="thread-1",
                            turn_id="turn-1",
                            item_id=item_id,
                            changes=same_change,
                        ),
                    ]
                )
            messages.append(
                completed_turn(thread_id="thread-1", turn_id="turn-1")
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, output = adapter_for(
                repository,
                factory,
                choice=lambda: "2",
            )

            result = await adapter.run("same run repeat")

            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertEqual(
                "duplicate_file_action_item_after_completion",
                result.unsupported_reason,
            )
            self.assertEqual((0, 0), engine.store.counters())
            self.assertEqual(1, output.getvalue().count("Selection:"))
            self.assertLessEqual(len(result.file_actions), 1)
            decisions = [
                message["result"]["decision"]
                for message in factory.transports[0].sent
                if "result" in message
                and "decision" in message["result"]
            ]
            self.assertEqual(["accept", "decline"], decisions)
            self.assertFalse(
                any(
                    event["event_type"] == "VERIFIED_SAVE"
                    for event in engine.store.read_events()
                )
            )

    async def test_abnormal_fresh_run_leaves_match_pending(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                    ),
                    file_run_messages(
                        repository,
                        thread_id="thread-2",
                        turn_id="turn-2",
                        item_id="item-2",
                        turn_status="failed",
                    ),
                ]
            )
            choices = iter(("2",))
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: next(choices),
            )

            await adapter.run("first")
            second = await adapter.run("second")

            self.assertEqual("PENDING", second.status)
            self.assertFalse(second.normal_terminal)
            self.assertEqual("failed", second.turn_status)
            self.assertEqual(1, len(second.file_actions))
            self.assertEqual(
                "matched-not-verified",
                second.file_actions[0].access,
            )
            self.assertEqual((0, 0), engine.store.counters())
            self.assertTrue(
                any(
                    event["event_type"] == "CHECKPOINT_PENDING"
                    for event in engine.store.read_events()
                )
            )

    async def test_missing_item_completion_leaves_match_pending(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                    ),
                    file_run_messages(
                        repository,
                        thread_id="thread-2",
                        turn_id="turn-2",
                        item_id="item-2",
                        include_item_completion=False,
                    ),
                ]
            )
            choices = iter(("2",))
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: next(choices),
            )

            await adapter.run("first")
            second = await adapter.run("second")

            self.assertEqual("PENDING", second.status)
            self.assertFalse(second.normal_terminal)
            self.assertEqual(1, len(second.file_actions))
            self.assertEqual(
                "matched-not-verified",
                second.file_actions[0].access,
            )
            self.assertEqual((0, 0), engine.store.counters())

    async def test_machine_identity_and_wire_settings_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        include_settings_update=True,
                    )
                ]
            )
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: "1",
            )

            result = await adapter.run("identity")

            self.assertEqual("NORMAL_TERMINAL", result.status)
            self.assertTrue(result.normal_terminal)
            self.assertIsNone(result.error_type)
            self.assertIsNotNone(result.runtime_identity)
            identity = result.runtime_identity
            assert identity is not None
            self.assertEqual(CODEX_MODEL, identity.model)
            self.assertEqual(
                CODEX_REASONING_EFFORT,
                identity.reasoning_effort,
            )
            self.assertEqual(CODEX_SERVICE_TIER, identity.service_tier)
            self.assertEqual(
                CODEX_CLI_VERSION,
                identity.codex_cli_version,
            )
            self.assertEqual("chatgpt", identity.account_type)
            sent = factory.transports[0].sent
            thread_start = next(
                message for message in sent
                if message.get("method") == "thread/start"
            )
            turn_start = next(
                message for message in sent
                if message.get("method") == "turn/start"
            )
            self.assertEqual(
                {
                    "features": {
                        "apps": False,
                        "hooks": False,
                        "multi_agent": False,
                        "remote_plugin": False,
                        "shell_tool": False,
                        "skill_mcp_dependency_install": False,
                    },
                    "mcp_servers": {},
                    "model_reasoning_effort": CODEX_REASONING_EFFORT,
                    "plugins": {},
                },
                thread_start["params"]["config"],
            )
            self.assertTrue(thread_start["params"]["ephemeral"])
            self.assertEqual(
                "read-only",
                thread_start["params"]["sandbox"],
            )
            self.assertEqual(CODEX_MODEL, turn_start["params"]["model"])
            self.assertEqual(
                CODEX_REASONING_EFFORT,
                turn_start["params"]["effort"],
            )
            self.assertEqual(
                CODEX_SERVICE_TIER,
                turn_start["params"]["serviceTier"],
            )
            self.assertEqual(
                {"networkAccess": False, "type": "readOnly"},
                turn_start["params"]["sandboxPolicy"],
            )
            self.assertEqual(ADAPTER_NAME, engine.adapter)
            self.assertEqual(CODEX_CLI_VERSION, engine.adapter_version)
            self.assertIn(
                "received:thread/settings/updated",
                factory.transports[0].events,
            )

    async def test_conflicting_settings_update_stays_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = file_run_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
                item_id="item-1",
                item_status="declined",
                include_settings_update=True,
            )
            matching_update = next(
                message
                for message in messages
                if message.get("method") == "thread/settings/updated"
            )
            matching_settings = matching_update["params"]["threadSettings"]
            update_index = messages.index(matching_update)
            messages[update_index] = {
                "method": "thread/settings/updated",
                "params": {
                    "threadId": "thread-1",
                    "threadSettings": {
                        **matching_settings,
                        "serviceTier": "flex",
                    },
                },
            }
            messages.insert(update_index + 1, matching_update)
            factory = FakeTransportFactory([messages])
            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("must not prompt"),
            )

            result = await adapter.run("conflicting settings")

            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertFalse(result.normal_terminal)
            self.assertEqual(
                "CodexRuntimeIdentityError",
                result.error_type,
            )
            self.assertEqual(
                "unsupported_read_request_shape",
                result.unsupported_reason,
            )
            self.assertIsNone(result.runtime_identity)
            self.assertFalse(adapter._settings_verified)
            self.assertEqual(
                {"approval-item-1": "item-1"},
                adapter._approval_requests,
            )
            self.assertEqual(
                {"approval-item-1"},
                adapter._resolved_approval_requests,
            )
            approvals = [
                message["result"]["decision"]
                for message in factory.transports[0].sent
                if "result" in message
                and "decision" in message["result"]
            ]
            self.assertEqual(["decline"], approvals)

    async def test_identity_mismatches_fail_closed_before_turn(self) -> None:
        cases = (
            {"model": "other-model"},
            {"effort": "xhigh"},
            {"service_tier": "flex"},
            {"account_type": "apiKey"},
            {"catalog_effort": "high"},
            {"catalog_tier": "flex"},
            {"model_provider": "other"},
            {"approval_policy": "never"},
            {"approvals_reviewer": "auto_review"},
            {"sandbox_type": "workspaceWrite"},
            {"network_access": True},
            {"effective_cwd": "/tmp/other"},
            {"ephemeral": False},
        )
        for index, overrides in enumerate(cases, start=1):
            with self.subTest(overrides=overrides):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory))
                    factory = FakeTransportFactory(
                        [
                            file_run_messages(
                                repository,
                                thread_id=f"thread-{index}",
                                turn_id=f"turn-{index}",
                                item_id=f"item-{index}",
                                **overrides,
                            )
                        ]
                    )
                    _, adapter, _ = adapter_for(
                        repository,
                        factory,
                        choice=lambda: self.fail("must not prompt"),
                    )

                    with self.assertRaises(CodexAdapterFailure):
                        await adapter.run("mismatch")

                    self.assertTrue(factory.transports[0].closed)

    async def test_cli_version_mismatch_fails_before_initialize(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                    )
                ],
                versions=["0.0.0"],
            )
            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("must not prompt"),
            )

            with self.assertRaises(CodexAdapterFailure):
                await adapter.run("version mismatch")

            self.assertEqual([], factory.transports[0].sent)
            self.assertTrue(factory.transports[0].closed)

    async def test_add_and_update_map_to_exact_decision_types(self) -> None:
        cases = (
            ("update", "target.txt", "MODIFY_FILE"),
            ("add", "new.txt", "CREATE_FILE"),
        )
        for index, (kind, path, expected) in enumerate(cases, start=1):
            with self.subTest(kind=kind):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory))
                    factory = FakeTransportFactory(
                        [
                            file_run_messages(
                                repository,
                                thread_id=f"thread-{index}",
                                turn_id=f"turn-{index}",
                                item_id=f"item-{index}",
                                file_changes=[
                                    change(path=path, kind=kind)
                                ],
                            )
                        ]
                    )
                    engine, adapter, _ = adapter_for(
                        repository,
                        factory,
                        choice=lambda: "1",
                    )

                    result = await adapter.run("map")

                    self.assertTrue(result.normal_terminal)
                    event = engine.store.read_events()[0]
                    self.assertEqual(expected, event["decision_type"])
                    self.assertEqual(path, event["normalized_scope"])

    async def test_unsupported_mutations_decline_without_protocol_events(
        self,
    ) -> None:
        invalid_changes = (
            [change(), change(path="other.txt", kind="add")],
            [change(kind="delete")],
            [change(move_path="renamed.txt")],
            [change(path="../outside.txt")],
        )
        for index, changes in enumerate(invalid_changes, start=1):
            with self.subTest(changes=changes):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory))
                    factory = FakeTransportFactory(
                        [
                            file_run_messages(
                                repository,
                                thread_id=f"thread-{index}",
                                turn_id=f"turn-{index}",
                                item_id=f"item-{index}",
                                file_changes=changes,
                                item_status="declined",
                            )
                        ]
                    )
                    engine, adapter, _ = adapter_for(
                        repository,
                        factory,
                        choice=lambda: self.fail("must not prompt"),
                    )

                    result = await adapter.run("unsupported")

                    self.assertEqual("UNSUPPORTED_MUTATION", result.status)
                    self.assertFalse(result.normal_terminal)
                    self.assertEqual(
                        "unsupported_file_change_shape",
                        result.unsupported_reason,
                    )
                    self.assertEqual([], engine.store.read_events())
                    responses = [
                        message["result"]["decision"]
                        for message in factory.transports[0].sent
                        if "result" in message
                        and "decision" in message["result"]
                    ]
                    self.assertEqual(["decline"], responses)

    async def test_command_approval_is_declined_as_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                [
                    approval_request(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="command-1",
                        request_id="command-approval",
                        method=(
                            "item/commandExecution/requestApproval"
                        ),
                    ),
                    resolved_request(
                        thread_id="thread-1",
                        request_id="command-approval",
                    ),
                    completed_turn(
                        thread_id="thread-1",
                        turn_id="turn-1",
                    ),
                ]
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("must not prompt"),
            )
            original_send = adapter._send

            def assert_registered_before_decline(
                message: dict[str, Any],
            ) -> None:
                result = message.get("result")
                if isinstance(result, dict) and "decision" in result:
                    self.assertEqual(
                        "command-1",
                        adapter._approval_requests.get(
                            "command-approval"
                        ),
                    )
                original_send(message)

            with patch.object(
                adapter,
                "_send",
                side_effect=assert_registered_before_decline,
            ):
                result = await adapter.run("shell mutation")

            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertIsNone(result.error_type)
            self.assertEqual(
                "unsupported_request_method:commandExecution",
                result.unsupported_reason,
            )
            self.assertEqual([], engine.store.read_events())
            self.assertEqual(
                {"command-approval"},
                adapter._resolved_approval_requests,
            )
            response = next(
                message
                for message in factory.transports[0].sent
                if message.get("id") == "command-approval"
            )
            self.assertEqual(
                {"decision": "decline"},
                response["result"],
            )

    async def test_all_unsupported_item_types_are_bounded_and_fail_closed(
        self,
    ) -> None:
        item_types = (
            "collabAgentToolCall",
            "commandExecution",
            "dynamicToolCall",
            "hookPrompt",
            "imageGeneration",
            "mcpToolCall",
            "subAgentActivity",
        )
        for index, item_type in enumerate(item_types, start=1):
            with self.subTest(item_type=item_type):
                with tempfile.TemporaryDirectory() as directory:
                    repository = create_repository(Path(directory))
                    thread_id = f"thread-{index}"
                    turn_id = f"turn-{index}"
                    messages = handshake_messages(
                        repository,
                        thread_id=thread_id,
                        turn_id=turn_id,
                    )
                    messages.extend(
                        [
                            {
                                "method": "item/started",
                                "params": {
                                    "item": {
                                        "id": "PRIVATE_ITEM_ID",
                                        "private": "PRIVATE_PAYLOAD",
                                        "type": item_type,
                                    },
                                    "threadId": thread_id,
                                    "turnId": turn_id,
                                },
                            },
                            completed_turn(
                                thread_id=thread_id,
                                turn_id=turn_id,
                            ),
                        ]
                    )
                    factory = FakeTransportFactory([messages])
                    engine, adapter, _ = adapter_for(
                        repository,
                        factory,
                        choice=lambda: self.fail("must not prompt"),
                    )

                    result = await adapter.run("PRIVATE_PROMPT")

                    self.assertEqual(
                        "UNSUPPORTED_MUTATION",
                        result.status,
                    )
                    self.assertFalse(result.normal_terminal)
                    expected_reason = (
                        "unsupported_dynamic_tool"
                        if item_type == "dynamicToolCall"
                        else f"unsupported_item_type:{item_type}"
                    )
                    self.assertEqual(expected_reason, result.unsupported_reason)
                    self.assertNotIn(
                        "PRIVATE",
                        result.unsupported_reason,
                    )
                    self.assertNotIn("PRIVATE", result.final_message)
                    self.assertEqual([], engine.store.read_events())

    async def test_unknown_request_method_uses_generic_bounded_reason(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                [
                    {
                        "id": "PRIVATE_REQUEST_ID",
                        "method": "PRIVATE_METHOD",
                        "params": {
                            "credential": "PRIVATE_CREDENTIAL",
                            "itemId": "PRIVATE_ITEM_ID",
                            "prompt": "PRIVATE_PROMPT",
                            "threadId": "thread-1",
                            "turnId": "turn-1",
                        },
                    },
                    resolved_request(
                        thread_id="thread-1",
                        request_id="PRIVATE_REQUEST_ID",
                    ),
                    completed_turn(
                        thread_id="thread-1",
                        turn_id="turn-1",
                    ),
                ]
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("must not prompt"),
            )

            result = await adapter.run("PRIVATE_PROMPT")

            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertFalse(result.normal_terminal)
            self.assertEqual(
                "unsupported_request_method:other",
                result.unsupported_reason,
            )
            self.assertNotIn("PRIVATE", result.unsupported_reason)
            self.assertNotIn("PRIVATE", result.final_message)
            self.assertEqual([], engine.store.read_events())

    async def test_unsupported_reason_resets_for_each_fresh_run(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            first_messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            first_messages.extend(
                [
                    approval_request(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="command-1",
                        request_id="command-approval",
                        method=(
                            "item/commandExecution/requestApproval"
                        ),
                    ),
                    resolved_request(
                        thread_id="thread-1",
                        request_id="command-approval",
                    ),
                    completed_turn(
                        thread_id="thread-1",
                        turn_id="turn-1",
                    ),
                ]
            )
            second_messages = handshake_messages(
                repository,
                thread_id="thread-2",
                turn_id="turn-2",
            )
            second_messages.extend(
                [
                    {
                        "method": "item/started",
                        "params": {
                            "item": {
                                "id": "dynamic-1",
                                "type": "dynamicToolCall",
                            },
                            "threadId": "thread-2",
                            "turnId": "turn-2",
                        },
                    },
                    completed_turn(
                        thread_id="thread-2",
                        turn_id="turn-2",
                    ),
                ]
            )
            factory = FakeTransportFactory(
                [first_messages, second_messages]
            )
            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("must not prompt"),
            )

            first = await adapter.run("first unsupported")
            second = await adapter.run("second unsupported")

            self.assertEqual(
                "unsupported_request_method:commandExecution",
                first.unsupported_reason,
            )
            self.assertEqual(
                "unsupported_dynamic_tool",
                second.unsupported_reason,
            )

    async def test_image_generation_cannot_promote_pending_match(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            first_messages = file_run_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
                item_id="file-1",
            )
            second_messages = file_run_messages(
                repository,
                thread_id="thread-2",
                turn_id="turn-2",
                item_id="file-2",
            )
            secret_values = (
                "PROMPT_SECRET",
                "FILE_CONTENT_SECRET",
                "PRIVATE_ITEM_ID",
                "PRIVATE_COMMAND_ID",
                "PRIVATE_REQUEST_ID",
                "PRIVATE_PATH",
                "CREDENTIAL_SECRET",
                "RAW_JSON_SECRET",
            )
            image_item = {
                "credential": "CREDENTIAL_SECRET",
                "fileContent": "FILE_CONTENT_SECRET",
                "id": "PRIVATE_ITEM_ID",
                "rawPayload": "RAW_JSON_SECRET",
                "revisedPrompt": "PROMPT_SECRET",
                "savedPath": "PRIVATE_PATH",
                "status": "completed",
                "type": "imageGeneration",
            }
            command_request = approval_request(
                thread_id="thread-2",
                turn_id="turn-2",
                item_id="PRIVATE_COMMAND_ID",
                request_id="PRIVATE_REQUEST_ID",
                method="item/commandExecution/requestApproval",
            )
            command_request["params"]["credential"] = "CREDENTIAL_SECRET"
            second_messages[-1:-1] = [
                completed_agent_message(
                    thread_id="thread-2",
                    turn_id="turn-2",
                    text="Original Codex answer.",
                ),
                {
                    "method": "item/started",
                    "params": {
                        "item": image_item,
                        "threadId": "thread-2",
                        "turnId": "turn-2",
                    },
                },
                {
                    "method": "item/completed",
                    "params": {
                        "item": image_item,
                        "threadId": "thread-2",
                        "turnId": "turn-2",
                    },
                },
                command_request,
                resolved_request(
                    thread_id="thread-2",
                    request_id="PRIVATE_REQUEST_ID",
                ),
            ]
            factory = FakeTransportFactory(
                [first_messages, second_messages]
            )
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: "2",
            )

            first = await adapter.run("create default")
            result = await adapter.run("PROMPT_SECRET")

            self.assertEqual("NORMAL_TERMINAL", first.status)
            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertFalse(result.normal_terminal)
            self.assertEqual("PENDING", result.checkpoint_outcomes[-1].status)
            self.assertEqual(
                "unsupported_item_type:imageGeneration",
                result.unsupported_reason,
            )
            self.assertEqual(1, len(result.file_actions))
            self.assertEqual(
                "matched-not-verified",
                result.file_actions[0].access,
            )
            self.assertEqual(
                "Original Codex answer.\n\n"
                "Decision OS verification: not verified "
                "(unsupported_item_type:imageGeneration).",
                result.final_message,
            )
            for secret in secret_values:
                self.assertNotIn(secret, result.unsupported_reason)
                self.assertNotIn(secret, result.final_message)
            self.assertEqual((0, 0), engine.store.counters())

    async def test_completed_file_without_approval_is_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            changes = [change()]
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            messages.extend(
                [
                    started_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=changes,
                    ),
                    completed_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=changes,
                    ),
                    completed_turn(
                        thread_id="thread-1",
                        turn_id="turn-1",
                    ),
                ]
            )
            factory = FakeTransportFactory([messages])
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: self.fail("must not prompt"),
            )

            result = await adapter.run("bypass")

            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertFalse(result.normal_terminal)
            self.assertEqual(
                "unapproved_file_completion",
                result.unsupported_reason,
            )
            self.assertEqual([], engine.store.read_events())

    async def test_post_approval_patch_change_cannot_promote(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            original = [change()]
            altered = [change(diff="@@ -1 +1 @@\n-one\n+three\n")]
            second = handshake_messages(
                repository,
                thread_id="thread-2",
                turn_id="turn-2",
            )
            second.extend(
                read_messages(
                    thread_id="thread-2",
                    turn_id="turn-2",
                    call_id="read-item-2",
                    path="target.txt",
                )
            )
            second.extend(
                [
                    started_item(
                        thread_id="thread-2",
                        turn_id="turn-2",
                        item_id="item-2",
                        changes=original,
                    ),
                    approval_request(
                        thread_id="thread-2",
                        turn_id="turn-2",
                        item_id="item-2",
                        request_id="approval-item-2",
                    ),
                    resolved_request(
                        thread_id="thread-2",
                        request_id="approval-item-2",
                    ),
                    patch_updated(
                        thread_id="thread-2",
                        turn_id="turn-2",
                        item_id="item-2",
                        changes=altered,
                    ),
                    completed_item(
                        thread_id="thread-2",
                        turn_id="turn-2",
                        item_id="item-2",
                        changes=altered,
                    ),
                    completed_turn(
                        thread_id="thread-2",
                        turn_id="turn-2",
                    ),
                ]
            )
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                    ),
                    second,
                ]
            )
            choices = iter(("2",))
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: next(choices),
            )

            await adapter.run("first")
            result = await adapter.run("second")

            self.assertEqual("PENDING", result.status)
            self.assertFalse(result.normal_terminal)
            self.assertEqual((0, 0), engine.store.counters())

    async def test_missing_resolved_request_cannot_promote(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            second = file_run_messages(
                repository,
                thread_id="thread-2",
                turn_id="turn-2",
                item_id="item-2",
            )
            second = [
                message
                for message in second
                if not (
                    message.get("method") == "serverRequest/resolved"
                    and message.get("params", {}).get("requestId")
                    == "approval-item-2"
                )
            ]
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                    ),
                    second,
                ]
            )
            choices = iter(("2",))
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: next(choices),
            )

            await adapter.run("first")
            result = await adapter.run("second")

            self.assertEqual("PENDING", result.status)
            self.assertFalse(result.normal_terminal)
            self.assertEqual((0, 0), engine.store.counters())

    async def test_turn_events_before_start_response_are_correlated(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            base = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
                include_settings_update=True,
            )
            turn_response = base[4]
            settings = base[5]
            changes = [change()]
            messages = base[:4]
            messages.extend(
                [
                    settings,
                    {
                        "method": "turn/started",
                        "params": {
                            "threadId": "thread-1",
                            "turn": {
                                "id": "turn-1",
                                "items": [],
                                "status": "inProgress",
                            },
                        },
                    },
                ]
            )
            messages.extend(
                read_messages(
                    thread_id="thread-1",
                    turn_id="turn-1",
                    call_id="read-item-1",
                    path="target.txt",
                )
            )
            messages.extend(
                [
                    started_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=changes,
                    ),
                    approval_request(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        request_id="approval-item-1",
                    ),
                    resolved_request(
                        thread_id="thread-1",
                        request_id="approval-item-1",
                    ),
                    completed_item(
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                        changes=changes,
                    ),
                    turn_response,
                    completed_turn(
                        thread_id="thread-1",
                        turn_id="turn-1",
                    ),
                ]
            )
            factory = FakeTransportFactory([messages])
            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: "1",
            )

            result = await adapter.run("early events")

            self.assertEqual("NORMAL_TERMINAL", result.status)
            self.assertTrue(result.normal_terminal)

    async def test_model_catalog_pagination_finds_required_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            selected_page = messages[2]
            selected_page["id"] = 4
            messages[2] = {
                "id": 3,
                "result": {
                    "data": [],
                    "nextCursor": "page-2",
                },
            }
            messages[3]["id"] = 5
            messages[4]["id"] = 6
            messages.insert(3, selected_page)
            messages.append(
                completed_turn(
                    thread_id="thread-1",
                    turn_id="turn-1",
                )
            )
            factory = FakeTransportFactory([messages])
            _, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: "1",
            )

            result = await adapter.run("paged catalog")

            self.assertTrue(result.normal_terminal)
            catalog_requests = [
                message
                for message in factory.transports[0].sent
                if message.get("method") == "model/list"
            ]
            self.assertEqual(2, len(catalog_requests))
            self.assertEqual(
                "page-2",
                catalog_requests[1]["params"]["cursor"],
            )

    def test_subprocess_transport_frames_jsonl_and_isolates_tools(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "codex"
            executable.write_text("", encoding="utf-8")
            process = FakeProcess('{"id":1,"result":{"ok":true}}\n')
            completed = subprocess.CompletedProcess(
                args=(str(executable), "--version"),
                returncode=0,
                stdout=f"codex-cli {CODEX_CLI_VERSION}\n",
                stderr="",
            )
            with (
                patch(
                    "decision_os.acceleration.codex_adapter.subprocess.run",
                    return_value=completed,
                ),
                patch(
                    "decision_os.acceleration.codex_adapter.subprocess.Popen",
                    return_value=process,
                ) as popen,
            ):
                transport = _SubprocessTransport(executable)
                transport.start()
                transport.send(
                    {"method": "initialized", "params": {}}
                )
                written = process.stdin.getvalue()
                received = transport.receive()
                transport.close()

            self.assertEqual(CODEX_CLI_VERSION, transport.version)
            self.assertEqual(
                '{"method":"initialized","params":{}}\n',
                written,
            )
            self.assertEqual({"id": 1, "result": {"ok": True}}, received)
            command = popen.call_args.args[0]
            self.assertEqual("app-server", command[-1])
            self.assertIn("features.hooks=false", command)
            self.assertIn("features.shell_tool=false", command)
            self.assertIn("mcp_servers={}", command)
            self.assertIn("plugins={}", command)
            self.assertTrue(process.terminated)
            self.assertFalse(process.killed)

    def test_subprocess_transport_rejects_invalid_json_and_eof(self) -> None:
        cases = ("not-json\n", "")
        for payload in cases:
            with self.subTest(payload=payload):
                with tempfile.TemporaryDirectory() as directory:
                    executable = Path(directory) / "codex"
                    executable.write_text("", encoding="utf-8")
                    process = FakeProcess(payload)
                    completed = subprocess.CompletedProcess(
                        args=(str(executable), "--version"),
                        returncode=0,
                        stdout=f"codex-cli {CODEX_CLI_VERSION}\n",
                        stderr="",
                    )
                    with (
                        patch(
                            "decision_os.acceleration.codex_adapter.subprocess.run",
                            return_value=completed,
                        ),
                        patch(
                            "decision_os.acceleration.codex_adapter.subprocess.Popen",
                            return_value=process,
                        ),
                    ):
                        transport = _SubprocessTransport(executable)
                        transport.start()
                        with self.assertRaises(CodexAdapterFailure):
                            transport.receive()
                        transport.close()

    async def test_model_reroute_prevents_pending_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            second = file_run_messages(
                repository,
                thread_id="thread-2",
                turn_id="turn-2",
                item_id="item-2",
            )
            second.insert(
                -1,
                {
                    "method": "model/rerouted",
                    "params": {
                        "fromModel": CODEX_MODEL,
                        "toModel": "other-model",
                    },
                },
            )
            factory = FakeTransportFactory(
                [
                    file_run_messages(
                        repository,
                        thread_id="thread-1",
                        turn_id="turn-1",
                        item_id="item-1",
                    ),
                    second,
                ]
            )
            choices = iter(("2",))
            engine, adapter, _ = adapter_for(
                repository,
                factory,
                choice=lambda: next(choices),
            )

            await adapter.run("first")
            result = await adapter.run("second")

            self.assertEqual("PENDING", result.status)
            self.assertFalse(result.normal_terminal)
            self.assertEqual(
                "CodexRuntimeIdentityError",
                result.error_type,
            )
            self.assertEqual((0, 0), engine.store.counters())


if __name__ == "__main__":
    unittest.main()
