import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# from functools import cache


@dataclass
class Context:
    # TODO: clean this up; could do the dict transform in a builder method?
    paths: list[Path]
    args: list[str]

    _file_cache: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        # mapping of name to full path, so I can both:
        # - check if a file exists quickly
        # - access the path object for reading
        self.files = {p.name: p for p in self.paths}

    @staticmethod
    def from_strings(paths: list[str], args: Optional[list[str]] = None):
        """
        build a Context with pure strings instead of actual path objects
        """
        return Context([Path(f) for f in paths], args or [])

    # can't use functools.cache because the dataclass isn't hashable (because of its lists?)
    # TODO: I swear this is fixable; remove custom file cache
    # @cache
    def _load_file(self, filename: str) -> str:
        if filename in self._file_cache:
            return self._file_cache[filename]

        text = self.files[filename].read_text()
        self._file_cache[filename] = text

        return text

    def read_file(self, filename: str) -> list[str]:
        return self._load_file(filename).splitlines()

    def read_json(self, filename: str):
        return json.loads(self._load_file(filename))

    def has_files(self, *filenames: str) -> bool:
        return bool(self.files) and all(f in self.files for f in filenames)
