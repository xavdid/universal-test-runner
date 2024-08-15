import json
from pathlib import Path
from typing import Callable, Optional, Protocol

import pytest

from universal_test_runner.context import Context

OptionalStrList = Optional[list[str]]


@pytest.fixture
def touch_files(tmp_path: Path):
    def _touch(files: list[str]):
        for file in files:
            (tmp_path / file).touch()

    return _touch


class ContextBuilderFunc(Protocol):
    def __call__(
        self,
        files: OptionalStrList = None,
        args: OptionalStrList = None,
        debugging=False,
    ) -> Context: ...


@pytest.fixture
def build_context(tmp_path: Path, touch_files) -> ContextBuilderFunc:
    def _build(
        files: OptionalStrList = None, args: OptionalStrList = None, debugging=False
    ):
        touch_files(files or [])
        # no need to clear cache here, since the unique-per-test
        # (and params) tmp_path marks all contexts as separate items
        # so, no interference
        return Context.build(str(tmp_path), args or [], debugging=debugging)

    return _build


class FileWriterFunc(Protocol):
    def __call__(self, filename: str, data: str) -> None: ...


@pytest.fixture
def write_file(tmp_path: Path) -> FileWriterFunc:
    def _write(filename: str, data: str):
        (tmp_path / filename).write_text(data)

    return _write


@pytest.fixture
def justfile_json() -> Callable[[str], str]:
    def _justfile(recipe_name: str):
        return json.dumps(
            {
                "aliases": {},
                "assignments": {},
                "first": "default",
                "recipes": {
                    "default": {
                        "attributes": [],
                        "body": [["just --list"]],
                        "dependencies": [],
                        "doc": None,
                        "name": "default",
                        "parameters": [],
                        "priors": 0,
                        "private": False,
                        "quiet": False,
                        "shebang": False,
                    },
                    recipe_name: {
                        "attributes": [],
                        "body": [["pytest ", [["variable", "options"]]]],
                        "dependencies": [],
                        "doc": None,
                        "name": "test",
                        "parameters": [
                            {
                                "default": None,
                                "export": False,
                                "kind": "star",
                                "name": "options",
                            }
                        ],
                        "priors": 0,
                        "private": False,
                        "quiet": True,
                        "shebang": False,
                    },
                },
                "settings": {
                    "allow_duplicate_recipes": False,
                    "dotenv_load": None,
                    "export": False,
                    "fallback": False,
                    "ignore_comments": False,
                    "positional_arguments": False,
                    "shell": None,
                    "tempdir": None,
                    "windows_powershell": False,
                    "windows_shell": None,
                },
                "warnings": [],
            }
        )

    return _justfile
