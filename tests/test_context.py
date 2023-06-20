import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tests.conftest import ContextBuilderFunc, FileWriterFunc
from universal_test_runner.context import Context


def test_builder(build_context: ContextBuilderFunc, tmp_path):
    c = build_context(["a", "b", "c"], ["q", "-w", "--cool"])

    assert c.cwd == str(tmp_path)
    assert c.filenames == frozenset("abc")
    assert c.args == ("q", "-w", "--cool")


@patch("sys.argv", new=["test-runner", "q", "-w", "--cool"])
@patch("os.getcwd")
@pytest.mark.parametrize("debugging", [True, False])
def test_invocation_builder(
    mock_cwd: Mock, tmp_path: Path, touch_files, debugging: bool
):
    mock_cwd.return_value = str(tmp_path)

    touch_files(["a.txt", "b.txt"])

    c = Context.from_invocation(debugging=debugging)

    assert c.cwd == str(tmp_path)
    assert c.args == ("q", "-w", "--cool")
    assert c.filenames == frozenset(["a.txt", "b.txt"])
    assert c.debugging == debugging


def test_read_file_uses_cache(build_context: ContextBuilderFunc, tmp_path: Path):
    filename = "my_file.txt"
    f = tmp_path / filename
    f.write_text("cool\n  words\non\nlines")

    c = build_context([filename])

    assert c.read_file(filename) == ["cool", "  words", "on", "lines"]

    # delete file, can still read
    f.unlink()
    assert c.read_file(filename) == ["cool", "  words", "on", "lines"]


def test_load_json_uses_cache(build_context: ContextBuilderFunc, tmp_path: Path):
    filename = "my_file.json"
    f = tmp_path / filename
    f.write_text('{"a": true, \n\n"b": "cool", "d": [1,2,3]}')

    c = build_context([filename])

    assert c.read_json(filename) == {"a": True, "b": "cool", "d": [1, 2, 3]}

    # delete file, can still read
    f.unlink()
    assert c.read_json(filename) == {"a": True, "b": "cool", "d": [1, 2, 3]}


@pytest.mark.parametrize(
    ["files", "looking", "expected"],
    [
        (["a", "b", "c"], ["a"], True),
        (["a", "b", "c"], ["a", "b"], True),
        (["a", "b", "c"], ["a", "b", "c"], True),
        (["a", "b", "c"], ["a", "b", "c", "d"], False),
        ([], ["a", "b", "c", "d"], False),
        (["a"], ["b"], False),
        ([], [], False),
    ],
    ids=repr,
)
def test_has_files(
    files: list[str],
    looking: list[str],
    expected: bool,
    build_context: ContextBuilderFunc,
):
    assert build_context(files).has_files(*looking) == expected


NO_SCRIPTS = {"scripts": {"build": "tsc", "validate": "yarn"}}
SCRIPTS = {"scripts": {"build": "tsc", "test": "yarn"}}


@pytest.mark.parametrize(
    ["files", "lockfile", "data", "expected"],
    [
        (
            ["package.json", "package-lock.json"],
            "package-lock.json",
            SCRIPTS,
            True,
        ),
        (
            ["package.json"],
            "package-lock.json",
            NO_SCRIPTS,
            False,
        ),
        (
            ["package.json", "yarn.lock"],
            "yarn.lock",
            SCRIPTS,
            True,
        ),
        (["package.json"], "yarn.lock", NO_SCRIPTS, False),
        (
            ["package.json", "pnpm-lock.yaml"],
            "pnpm-lock.yaml",
            SCRIPTS,
            True,
        ),
        (["package.json"], "pnpm-lock.yaml", NO_SCRIPTS, False),
        ([], "pnpm-lock.yaml", NO_SCRIPTS, False),
    ],
)
def test_has_test_script_and_lockfile(
    files: list[str],
    lockfile: str,
    data,
    expected,
    build_context: ContextBuilderFunc,
    write_file: FileWriterFunc,
):
    write_file("package.json", json.dumps(data))
    c = build_context(files)

    assert c.has_test_script_and_lockfile(lockfile) == expected


def test_debugging(capsys, build_context: ContextBuilderFunc):
    c = build_context(debugging=True)
    c.debug("neat")
    c.debug("cool", indent=3)

    out, _ = capsys.readouterr()
    assert "neat" in out
    assert ":    cool" in out


def test_debugging_is_disableable(capsys, build_context: ContextBuilderFunc):
    c = build_context(debugging=False)
    c.debug("neat")
    c.debug("cool", indent=3)

    out, _ = capsys.readouterr()
    assert out == ""
