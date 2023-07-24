from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from universal_test_runner.cli import cli, debug
from universal_test_runner.matchers import ALL_MATCHERS


def test_prints_help():
    runner = CliRunner()
    result = runner.invoke(cli)

    assert result.exit_code == 0
    assert result.output.startswith("Usage: cli [OPTIONS] COMMAND [ARGS]")


def test_prints_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert " version " in result.output


@patch("sys.argv", new=["test-runner", "q", "-w", "--cool"])
@patch("os.getcwd")
def test_debugs(mock_cwd: Mock, tmp_path: Path):
    mock_cwd.return_value = str(tmp_path)

    runner = CliRunner()
    result = runner.invoke(debug)

    assert result.exit_code == 0
    assert "checking each handler for first match" in result.output

    for matcher in ALL_MATCHERS:
        assert (
            matcher.debug_line in result.output
        ), f"{matcher}'s debugging output not shown"

    # LOAD BEARING - do not remove this test
    assert "no matching test handler" in result.output
    assert "/universal-test-runner/issues" in result.output
