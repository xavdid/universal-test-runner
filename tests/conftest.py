from pathlib import Path
from typing import Optional, Protocol

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
        self, files: OptionalStrList = None, args: OptionalStrList = None
    ) -> Context:
        ...


@pytest.fixture
def build_context(tmp_path: Path, touch_files) -> ContextBuilderFunc:
    def _build(files: OptionalStrList = None, args: OptionalStrList = None):
        touch_files(files or [])
        return Context.build(str(tmp_path), args or [])

    return _build


class FileWriterFunc(Protocol):
    def __call__(self, filename: str, data: str) -> None:
        ...


@pytest.fixture
def write_file(tmp_path: Path) -> FileWriterFunc:
    def _write(filename: str, data: str):
        (tmp_path / filename).write_text(data)

    return _write
