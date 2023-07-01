import json
import os
import sys
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path


@dataclass(frozen=True)
class Context:
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
    def _load_file(self, filename: str) -> str:
        return Path(self.cwd, filename).read_text("utf-8")

    def read_file(self, filename: str) -> list[str]:
        return self._load_file(filename).splitlines()

    def read_json(self, filename: str):
        return json.loads(self._load_file(filename))

    def has_files(self, *filenames: str) -> bool:
        return bool(self.filenames) and all(f in self.filenames for f in filenames)

    def has_test_script_and_lockfile(self, lockfile: str) -> bool:
        if not self.has_files("package.json", lockfile):
            return False

        pkg = self.read_json("package.json")
        return bool(pkg.get("scripts", {}).get("test"))

    def debug(self, message: str, indent=0):
        if not self.debugging or not message:
            return

        print(f"[universal-test-runner]: {' '*indent}{message}")
