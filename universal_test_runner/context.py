import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Context:
    paths: list[Path]
    args: list[str]

    def __post_init__(self):
        self.files = {p.name for p in self.paths}

    @staticmethod
    def from_strings(paths: list[str], args: Optional[list[str]] = None):
        return Context([Path(f) for f in paths], args or [])

    # TODO: parse lines and json
