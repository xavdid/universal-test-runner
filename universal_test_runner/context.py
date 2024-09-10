import json
import os
import sys
from dataclasses import dataclass, field
from functools import cache
from importlib.util import find_spec
from pathlib import Path
from typing import Callable, Iterable, Optional

if find_spec("tomllib"):
    from tomllib import loads as load_toml
else:
    load_toml = None


Checker = Callable[[Iterable[object]], bool]


@dataclass(frozen=True)
class Context:
    """
    An immutable object with helpers for detecting and reading the files in a directory.
    It prioritizes caching heavily for file reads to make repeated checks against the same files cheap.
    """

    cwd: str
    filenames: frozenset[str]
    args: tuple[str, ...]
    debugging: bool = field(compare=False, default=False)

    @staticmethod
    def build(cwd: str, args: list[str], debugging: bool = False):
        """
        does the transforming of typical inputs into the data the context actually needs
        """
        return Context(
            cwd,
            frozenset(p.name for p in Path(cwd).iterdir()),
            tuple(args),
            debugging=debugging,
        )

    @staticmethod
    def from_invocation(debugging: bool = False):
        """
        used by the CLI to auto-capture info about the working directory
        """
        return Context.build(os.getcwd(), sys.argv[1:], debugging=debugging)

    @cache
    def load_file(self, filename: str) -> str:
        """
        get the contents of a file as a string
        """
        # readers don't have to check that a file exists
        if filename not in self.filenames:
            return ""
        return Path(self.cwd, filename).read_text("utf-8")

    def read_file(self, filename: str) -> list[str]:
        """
        get the lines of a file
        """
        if filename not in self.filenames:
            return []
        return self.load_file(filename).splitlines()

    @cache
    def read_json(self, filename: str):
        try:
            return json.loads(self.load_file(filename))
        except json.decoder.JSONDecodeError:
            return {}

    @cache
    def read_toml(self, filename: str) -> Optional[dict]:
        if load_toml:
            return load_toml(self.load_file(filename))
        return {}

    def _has_files(self, checker: Checker, *filenames: str) -> bool:
        return bool(self.filenames) and checker(f in self.filenames for f in filenames)

    def has_all_files(self, *filenames: str) -> bool:
        return self._has_files(all, *filenames)

    def has_any_files(self, *filenames: str) -> bool:
        return self._has_files(any, *filenames)

    def has_test_script_and_lockfile(self, lockfile: str) -> bool:
        if not self.has_all_files("package.json", lockfile):
            return False

        pkg = self.read_json("package.json")
        return bool(pkg.get("scripts", {}).get("test"))

    def debug(self, message: str, indent=0):
        if not self.debugging or not message:
            return

        print(f"[universal-test-runner]: {' '*indent}{message}")
