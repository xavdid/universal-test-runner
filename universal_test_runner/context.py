from functools import cache
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Context:
    # TODO: clean this up; could do the dict transform in a builder method?
    paths: list[Path]
    args: list[str]

    _file_cache: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.files = {p.name: p for p in self.paths}

    @staticmethod
    def from_strings(paths: list[str], args: Optional[list[str]] = None):
        return Context([Path(f) for f in paths], args or [])

    # can't use functools.cache because the dataclass isn't hashable (because of its lists?)
    # TODO: I swear this is fixable
    # @cache
    def _load_file(self, filename: str) -> str:
        if filename in self._file_cache:
            return self._file_cache[filename]

        text = self.files[filename].read_text()
        self._file_cache[filename] = text

        return text

    def read_file(self, filename: str):
        return self._load_file(filename).splitlines()

    def read_json(self, filename: str):
        return json.loads(self._load_file(filename))
