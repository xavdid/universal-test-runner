from pathlib import Path
from unittest.mock import Mock, patch

from universal_test_runner.context import Context
from universal_test_runner.runner import run, run_test_command


@patch("subprocess.run")
def test_run_command(subp_run: Mock):
    subp_run.return_value = Mock(returncode=0)

    assert run_test_command(["a", "-b", "--c"]) == 0

    subp_run.assert_called_once_with(["a", "-b", "--c"])


@patch("subprocess.run")
def test_no_matches(subp_run: Mock, capsys):
    assert run_test_command([]) == 1

    out, _ = capsys.readouterr()
    assert "no testing method found" in out

    subp_run.assert_not_called()


@patch("subprocess.run")
def test_command_not_found(subp_run: Mock, capsys):
    subp_run.side_effect = FileNotFoundError

    assert run_test_command(["pytest"]) == 1

    out, _ = capsys.readouterr()
    assert "command not found:" in out

    subp_run.assert_called_once_with(["pytest"])


@patch("sys.argv", new=["test-runner", "a", "-b", "--c"])
@patch("sys.exit")
@patch("universal_test_runner.runner.find_test_command")
@patch("universal_test_runner.runner.run_test_command")
@patch("os.getcwd")
def test_run(
    mock_cwd: Mock,
    mock_test_runner: Mock,
    mock_command_finder: Mock,
    mock_exit: Mock,
    tmp_path: Path,
    touch_files,
):
    files = ["a.txt", "b.txt", "c.txt"]
    touch_files(files)

    mock_cwd.return_value = str(tmp_path)

    mock_command_finder.return_value = ["my", "test", "command"]

    run()

    mock_command_finder.assert_called_once_with(
        Context(str(tmp_path), frozenset(files), ("a", "-b", "--c"))
    )
    mock_test_runner.assert_called_once_with(["my", "test", "command"])
    mock_exit.assert_called_once_with(mock_test_runner.return_value)
