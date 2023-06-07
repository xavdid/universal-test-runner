from dataclasses import dataclass, field
from pathlib import Path
import pytest
from unittest.mock import Mock, patch
from universal_test_runner.context import Context
from universal_test_runner.runner import run_test_command, run


def test_no_matches(capsys):
    assert run_test_command(Context.from_strings([])) == 1
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
    def test_command_not_found(self, subp_run: Mock, capsys):
        subp_run.side_effect = FileNotFoundError

        assert run_test_command(Context.from_strings([".pytest_cache"])) == 1

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
    def test_matchers(self, subp_run: Mock, test_case: RunnerTestCase):
        run_test_command(Context.from_strings(test_case.files, test_case.args))

        subp_run.assert_called_once_with(test_case.expected_command.split())


@patch("sys.argv", new=["test-runner", "-a", "--b", "c"])
@patch("sys.exit")
@patch("universal_test_runner.runner.run_test_command")
@patch("os.getcwd")
def test_run(mock_cwd: Mock, mock_runner: Mock, mock_exit: Mock, tmp_path: Path):
    mock_cwd.return_value = str(tmp_path)

    files = [
        (tmp_path / "x.py"),
        (tmp_path / "y.py"),
        (tmp_path / "z.py"),
    ]
    for f in files:
        f.touch()

    run()

    mock_runner.assert_called_once_with(Context(files, ["-a", "--b", "c"]))
    mock_exit.assert_called_once_with(mock_runner.return_value)
