from pathlib import Path
from unittest.mock import patch

import pytest

from universal_test_runner.context import Context


def test_process_files():
    assert Context([Path("a"), Path("b"), Path("c")], []).files == {
        "a": Path("a"),
        "b": Path("b"),
        "c": Path("c"),
    }


def test_read_file_uses_cache(tmp_path: Path):
    filename = "my_file.txt"
    f = tmp_path / filename
    f.write_text("cool\n  words\non\nlines")

    c = Context([f], [])

    assert c.read_file(filename) == ["cool", "  words", "on", "lines"]
    assert list(c._file_cache.keys()) == ["my_file.txt"]

    with patch("pathlib.Path.read_text") as p:
        assert c.read_file(filename) == ["cool", "  words", "on", "lines"]

        # subsequent reads don't read the file again
        p.assert_not_called()


def test_load_json_uses_cache(tmp_path: Path):
    filename = "my_file.json"
    f = tmp_path / filename
    f.write_text('{"a": true, \n\n"b": "cool", "d": [1,2,3]}')

    c = Context([f], [])

    assert c.read_json(filename) == {"a": True, "b": "cool", "d": [1, 2, 3]}
    assert list(c._file_cache.keys()) == ["my_file.json"]

    with patch("pathlib.Path.read_text") as p:
        assert c.read_json(filename) == {"a": True, "b": "cool", "d": [1, 2, 3]}

        # subsequent reads don't read the file again
        p.assert_not_called()


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
def test_has_files(files: list[str], looking: list[str], expected: bool):
    assert Context.from_strings(files).has_files(*looking) == expected
