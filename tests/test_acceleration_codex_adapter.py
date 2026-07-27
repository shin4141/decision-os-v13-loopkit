from __future__ import annotations

from collections import deque
import io
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
    CodexApproval,
    CodexLifecycleEvent,
    _SubprocessTransport,
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
            self.assertEqual("one-time", result.file_actions[0].access)
            self.assertEqual("approved", result.file_actions[0].status)
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
                events.index("received:serverRequest/resolved"),
            )
            self.assertLess(
                events.index("received:serverRequest/resolved"),
                events.index("received:item/completed"),
            )
            self.assertLess(
                events.index("received:item/completed"),
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
            approvals = [
                message["result"]["decision"]
                for message in factory.transports[0].sent
                if "result" in message
            ]
            self.assertEqual(["decline"], approvals)
            self.assertEqual(
                {"approval-item-1"},
                adapter._resolved_approval_requests,
            )

    async def test_same_run_repeat_never_becomes_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = create_repository(Path(directory))
            messages = handshake_messages(
                repository,
                thread_id="thread-1",
                turn_id="turn-1",
            )
            same_change = [change()]
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

            self.assertEqual("NORMAL_TERMINAL", result.status)
            self.assertEqual((0, 0), engine.store.counters())
            self.assertEqual(1, output.getvalue().count("Selection:"))
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
            matching_update = messages[5]
            matching_settings = matching_update["params"]["threadSettings"]
            messages[5] = {
                "method": "thread/settings/updated",
                "params": {
                    "threadId": "thread-1",
                    "threadSettings": {
                        **matching_settings,
                        "serviceTier": "flex",
                    },
                },
            }
            messages.insert(6, matching_update)
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
                    self.assertEqual([], engine.store.read_events())
                    responses = [
                        message["result"]["decision"]
                        for message in factory.transports[0].sent
                        if "result" in message
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
            image_item = {
                "id": "image-1",
                "revisedPrompt": "generated artifact",
                "savedPath": "generated.png",
                "status": "completed",
                "type": "imageGeneration",
            }
            second_messages[-1:-1] = [
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
            result = await adapter.run("unsupported image")

            self.assertEqual("NORMAL_TERMINAL", first.status)
            self.assertEqual("UNSUPPORTED_MUTATION", result.status)
            self.assertFalse(result.normal_terminal)
            self.assertEqual("PENDING", result.checkpoint_outcomes[-1].status)
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
                if message.get("method") != "serverRequest/resolved"
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
