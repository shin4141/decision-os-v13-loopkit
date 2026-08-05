from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import tempfile
import unittest
import urllib.error
import urllib.request

from scripts.qualify_companion_process import (
    CANONICAL_LISTENER_HOST,
    CANONICAL_MODULE,
    PASS,
    RUNTIME_LAUNCHER_MODULE_MISMATCH,
    RUNTIME_LAUNCHER_SOURCE_MISMATCH,
    RUNTIME_LISTENER_MISSING,
    RUNTIME_LISTENER_MULTIPLE_OWNERS,
    RUNTIME_PROCESS_COMMAND_MISMATCH,
    RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE,
    RUNTIME_PROCESS_EXECUTABLE_MISMATCH,
    RUNTIME_PROCESS_MISSING,
    RUNTIME_PROCESS_MODULE_MISMATCH,
    RUNTIME_PROCESS_PARENT_AMBIGUOUS,
    RUNTIME_PRODUCT_TREE_MISMATCH,
    ListenerEvidence,
    ProcessEvidence,
    QualificationConfig,
    qualify_companion_process,
    qualify_process_evidence,
    product_tree_sha256,
)


EXPECTED_PRODUCT_TREE = (
    "815613804a6028a33806afe096ca072c80515ee8ebb73514b96f85ca02f784d6"
)
LIVE_RUNTIME = Path(
    "/Users/sn/Library/Application Support/Decision OS Companion/runtime"
)
LIVE_APPLET = Path(
    "/Users/sn/Applications/Decision OS Companion.app/Contents/MacOS/applet"
)
LIVE_PYTHON = Path("/opt/homebrew/bin/python3")


class _FakeCollector:
    def __init__(
        self,
        listener: ListenerEvidence,
        processes: dict[int, ProcessEvidence],
        expected_executable: str,
    ) -> None:
        self._listener = listener
        self._processes = processes
        self._expected_executable = expected_executable

    def listener(self, host: str, port: int) -> ListenerEvidence:
        return self._listener

    def process(self, pid: int) -> ProcessEvidence | None:
        return self._processes.get(pid)

    def expected_process_executable(self, expected_python: Path) -> str:
        return self._expected_executable


class CompanionProcessQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.python = "/canonical/Python"
        self.owner = ProcessEvidence(
            pid=41,
            parent_pid=7,
            executable=self.python,
            argv=(self.python, "-m", CANONICAL_MODULE),
        )

    def qualify(
        self,
        *,
        listener: ListenerEvidence | None = None,
        processes: dict[int, ProcessEvidence] | None = None,
        expected_python: str | None = None,
    ):
        return qualify_process_evidence(
            listener=listener or ListenerEvidence(True, (41,)),
            processes=processes or {41: self.owner},
            expected_process_executable=expected_python or self.python,
            expected_module=CANONICAL_MODULE,
        )

    def test_t1_canonical_module_invocation_is_accepted(self) -> None:
        self.assertEqual(PASS, self.qualify().code)

    def test_t2_runtime_run_py_is_not_required(self) -> None:
        self.assertNotIn("runtime/run.py", self.owner.argv)
        self.assertEqual(PASS, self.qualify().code)

    def test_t3_another_module_is_rejected_exactly(self) -> None:
        other = replace(
            self.owner,
            argv=(self.python, "-m", "decision_os.other"),
        )
        self.assertEqual(
            RUNTIME_PROCESS_MODULE_MISMATCH,
            self.qualify(processes={41: other}).code,
        )

    def test_t4_another_python_executable_is_rejected_exactly(self) -> None:
        other = replace(
            self.owner,
            executable="/different/Python",
            argv=("/different/Python", "-m", CANONICAL_MODULE),
        )
        self.assertEqual(
            RUNTIME_PROCESS_EXECUTABLE_MISMATCH,
            self.qualify(processes={41: other}).code,
        )

    def test_t5_listener_owner_without_process_is_missing(self) -> None:
        result = self.qualify(
            listener=ListenerEvidence(True, (41,)),
            processes={99: self.owner},
        )
        self.assertEqual(RUNTIME_PROCESS_MISSING, result.code)

    def test_t6_matching_non_owner_does_not_satisfy_listener_binding(self) -> None:
        actual_owner = replace(
            self.owner,
            pid=52,
            argv=(self.python, "-m", "decision_os.other"),
        )
        result = self.qualify(
            listener=ListenerEvidence(True, (52,)),
            processes={41: self.owner, 52: actual_owner},
        )
        self.assertEqual(RUNTIME_PROCESS_MODULE_MISMATCH, result.code)

    def test_t7_multiple_listener_owners_fail_closed(self) -> None:
        result = self.qualify(listener=ListenerEvidence(True, (41, 52)))
        self.assertEqual(RUNTIME_LISTENER_MULTIPLE_OWNERS, result.code)

    def test_t8_raw_substring_spoofing_does_not_pass(self) -> None:
        spoof = replace(
            self.owner,
            argv=(
                self.python,
                "-c",
                "print('-m decision_os.companion')",
            ),
        )
        self.assertEqual(
            RUNTIME_PROCESS_COMMAND_MISMATCH,
            self.qualify(processes={41: spoof}).code,
        )

    def test_t9_malformed_process_evidence_fails_closed(self) -> None:
        malformed = replace(self.owner, executable="", argv=())
        self.assertEqual(
            RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE,
            self.qualify(processes={41: malformed}).code,
        )

    def test_absent_listener_is_distinct_from_missing_process(self) -> None:
        result = self.qualify(listener=ListenerEvidence(False, ()))
        self.assertEqual(RUNTIME_LISTENER_MISSING, result.code)

    def test_expected_applet_parent_ambiguity_fails_closed(self) -> None:
        result = qualify_process_evidence(
            listener=ListenerEvidence(True, (41,)),
            processes={41: self.owner},
            expected_process_executable=self.python,
            expected_module=CANONICAL_MODULE,
            expected_applet=Path("/canonical/applet"),
        )
        self.assertEqual(RUNTIME_PROCESS_PARENT_AMBIGUOUS, result.code)


class CompanionRuntimeBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.runtime = root / "runtime"
        self.repository = root / "repository"
        (self.runtime / "decision_os").mkdir(parents=True)
        (self.runtime / "decision_os/__init__.py").write_text(
            "# bounded fixture\n",
            encoding="utf-8",
        )
        (self.runtime / "macos").mkdir()
        (self.repository / "macos").mkdir(parents=True)
        launcher = (
            'set launchCommand to pythonBinary & " -m decision_os.companion"\n'
        )
        for root_path in (self.runtime, self.repository):
            (root_path / "macos/DecisionOSCompanion.applescript").write_text(
                launcher,
                encoding="utf-8",
            )
        self.product_tree = product_tree_sha256(self.runtime)
        self.python = self.runtime / "Python"
        self.python.write_text("fixture\n", encoding="utf-8")
        self.applet = self.runtime / "applet"
        self.applet.write_text("fixture\n", encoding="utf-8")
        self.config = QualificationConfig(
            runtime_root=self.runtime,
            repository_root=self.repository,
            expected_product_tree=self.product_tree,
            expected_python=self.python,
            listener_host=CANONICAL_LISTENER_HOST,
            listener_port=64203,
            expected_module=CANONICAL_MODULE,
        )
        owner = ProcessEvidence(
            41,
            7,
            str(self.python),
            (str(self.python), "-m", CANONICAL_MODULE),
        )
        self.collector = _FakeCollector(
            ListenerEvidence(True, (41,)),
            {41: owner},
            str(self.python),
        )

    def test_t10_installed_runtime_tree_mismatch_blocks_pass(self) -> None:
        result = qualify_companion_process(
            replace(self.config, expected_product_tree="0" * 64),
            collector=self.collector,
        )
        self.assertEqual(RUNTIME_PRODUCT_TREE_MISMATCH, result.code)

    def test_t11_installed_launcher_source_mismatch_blocks_pass(self) -> None:
        (self.runtime / "macos/DecisionOSCompanion.applescript").write_text(
            'set launchCommand to pythonBinary & " -m decision_os.other"\n',
            encoding="utf-8",
        )
        result = qualify_companion_process(
            self.config,
            collector=self.collector,
        )
        self.assertEqual(RUNTIME_LAUNCHER_SOURCE_MISMATCH, result.code)

    def test_launcher_without_canonical_module_blocks_pass(self) -> None:
        changed = 'set launchCommand to pythonBinary & " -m decision_os.other"\n'
        for root_path in (self.runtime, self.repository):
            (root_path / "macos/DecisionOSCompanion.applescript").write_text(
                changed,
                encoding="utf-8",
            )
        result = qualify_companion_process(
            self.config,
            collector=self.collector,
        )
        self.assertEqual(RUNTIME_LAUNCHER_MODULE_MISMATCH, result.code)


@unittest.skipUnless(
    os.environ.get("DECISION_OS_TEST_LIVE_COMPANION") == "1",
    "current installed Companion replay is explicitly enabled",
)
class CurrentInstalledCompanionTests(unittest.TestCase):
    @staticmethod
    def config() -> QualificationConfig:
        repository = Path(__file__).resolve().parents[1]
        return QualificationConfig(
            runtime_root=LIVE_RUNTIME,
            repository_root=repository,
            expected_product_tree=EXPECTED_PRODUCT_TREE,
            expected_python=LIVE_PYTHON,
            listener_host=CANONICAL_LISTENER_HOST,
            listener_port=int(
                os.environ.get("DECISION_OS_TEST_COMPANION_PORT", "64203")
            ),
            expected_module=CANONICAL_MODULE,
            expected_applet=LIVE_APPLET,
        )

    def test_t12_current_canonical_installed_process_passes(self) -> None:
        result = qualify_companion_process(self.config())
        self.assertEqual(PASS, result.code)
        self.assertTrue(result.passed)
        self.assertEqual(EXPECTED_PRODUCT_TREE, result.details["installed_product_tree"])
        self.assertTrue(result.details["applet_parent_verified"])

    def test_t13_unauthenticated_request_returns_401(self) -> None:
        config = self.config()
        request = urllib.request.Request(
            f"http://{config.listener_host}:{config.listener_port}/api/state"
        )
        with self.assertRaises(urllib.error.HTTPError) as raised:
            urllib.request.urlopen(request, timeout=3)
        self.assertEqual(401, raised.exception.code)
        raised.exception.close()


if __name__ == "__main__":
    unittest.main()
