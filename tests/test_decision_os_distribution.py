from __future__ import annotations

import io
from pathlib import Path
import unittest

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 runtime support
    tomllib = None

from decision_os.cli import EXIT_USAGE, main


REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"


@unittest.skipUnless(tomllib is not None, "tomllib is available on Python 3.11+")
class DistributionMetadataTest(unittest.TestCase):
    def metadata(self) -> dict[str, object]:
        with PYPROJECT.open("rb") as stream:
            return tomllib.load(stream)

    def test_build_backend_is_pinned_and_runtime_dependencies_are_empty(
        self,
    ) -> None:
        metadata = self.metadata()

        self.assertEqual(
            metadata["build-system"],
            {
                "requires": ["flit_core==3.12.0"],
                "build-backend": "flit_core.buildapi",
            },
        )
        self.assertEqual(metadata["project"]["dependencies"], [])

    def test_distribution_metadata_and_import_package_are_explicit(self) -> None:
        metadata = self.metadata()
        project = metadata["project"]

        self.assertEqual(project["name"], "decision-os-v13-loopkit")
        self.assertEqual(project["version"], "0.2.0")
        self.assertEqual(project["requires-python"], ">=3.10")
        self.assertEqual(project["license"], "MIT")
        self.assertEqual(project["license-files"], ["LICENSE"])
        self.assertEqual(
            metadata["tool"]["flit"]["module"]["name"],
            "decision_os",
        )

    def test_console_script_targets_the_existing_cli_callable(self) -> None:
        metadata = self.metadata()

        self.assertEqual(
            metadata["project"]["scripts"],
            {"decision-os": "decision_os.cli:main"},
        )


class DistributionEntrypointContractTest(unittest.TestCase):
    def test_entrypoint_callable_returns_the_existing_usage_exit(self) -> None:
        output = io.StringIO()

        exit_code = main([], stdout=output)

        self.assertEqual(exit_code, EXIT_USAGE)
        self.assertIn('"check":"cli.usage"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
