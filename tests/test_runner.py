from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.conftest import ContextBuilderFunc
from universal_test_runner.context import Context
from universal_test_runner.runner import run, run_test_command


def test_no_matches(capsys, build_context: ContextBuilderFunc):
    assert run_test_command(build_context()) == 1
    out, _ = capsys.readouterr()
    assert "no testing method" in out


@dataclass
class RunnerTestCase:
    files: list[str]
    expected_command: str
    args: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"files={self.files} & args={self.args} -> `{self.expected_command}`"


@patch("subprocess.run")
class TestRunner:
    def test_command_not_found(
        self, subp_run: Mock, capsys, build_context: ContextBuilderFunc
    ):
        subp_run.side_effect = FileNotFoundError

        assert run_test_command(build_context([".pytest_cache"])) == 1

        out, _ = capsys.readouterr()
        assert "command not found:" in out

    @pytest.mark.parametrize(
        "test_case",
        [
            RunnerTestCase([".pytest_cache"], "pytest"),
            RunnerTestCase(["tests.py"], "python tests.py"),
            RunnerTestCase(["go.mod"], "go test ./..."),
            RunnerTestCase(
                ["go.mod"], args=["parser"], expected_command="go test parser"
            ),
            RunnerTestCase(["parser_test.go"], "go test"),
            RunnerTestCase(
                ["parser_test.go"], args=["-v"], expected_command="go test -v"
            ),
            RunnerTestCase(["mix.exs"], "mix test"),
            RunnerTestCase(["Cargo.toml"], "cargo test"),
            RunnerTestCase(["project.clj"], "lein test"),
        ],
        ids=repr,
    )
    def test_matchers(
        self,
        subp_run: Mock,
        test_case: RunnerTestCase,
        build_context: ContextBuilderFunc,
    ):
        run_test_command(build_context(test_case.files, test_case.args))

        subp_run.assert_called_once_with(test_case.expected_command.split())


@patch("sys.argv", new=["test-runner", "-a", "--b", "c"])
@patch("sys.exit")
@patch("universal_test_runner.runner.run_test_command")
@patch("os.getcwd")
def test_run(
    mock_cwd: Mock,
    mock_runner: Mock,
    mock_exit: Mock,
    tmp_path: Path,
    build_context: ContextBuilderFunc,
    touch_files,
):
    files = ["x.py", "y.py", "z.py"]
    touch_files(files)
    mock_cwd.return_value = str(tmp_path)

    run()

    mock_runner.assert_called_once_with(
        Context(str(tmp_path), frozenset(files), ("-a", "--b", "c"))
    )
    mock_exit.assert_called_once_with(mock_runner.return_value)
