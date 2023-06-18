import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path


@dataclass(frozen=True)
class Context:
    cwd: str
    filenames: frozenset[str]
    args: tuple[str, ...]

    @staticmethod
    def build(cwd: str, args: list[str]):
        return Context(cwd, frozenset(p.name for p in Path(cwd).iterdir()), tuple(args))

    @cache
    def _load_file(self, filename: str) -> str:
        return Path(self.cwd, filename).read_text()

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
