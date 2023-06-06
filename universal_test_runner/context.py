import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Context:
    paths: list[Path]
    args: list[str]

    def __post_init__(self):
        self.files = {p.name for p in self.paths}
