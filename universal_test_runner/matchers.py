import re
from dataclasses import dataclass
from typing import Callable, Optional

from universal_test_runner.context import Context


@dataclass(frozen=True)
class Matcher:
    test: Callable[[Context], Optional[bool]]
    _command: str

    @property
    def command(self) -> list[str]:
        return self._command.split()

    def __repr__(self) -> str:
        return f"<Matcher command={self._command}>"

    @staticmethod
    def basic(file: str, command: str):
        return Matcher(lambda c: file in c.files, command)


# for go modules with nested packages, running `go test` on its own runs no test.
# so we have to include the ./... to pick up all packages
go_multi = Matcher(lambda c: "go.mod" in c.files and not c.args, "go test ./...")
# however, if we're in the package root and there's a test file here, then we can just run
go_single = Matcher(
    lambda c: "go.mod" in c.files or any(re.search(r"_test.go$", f) for f in c.files),
    "go test",
)

# misc simple cases
pytest = Matcher.basic(".pytest_cache", "pytest")
py = Matcher.basic("tests.py", "python tests.py")
elixir = Matcher.basic("mix.exs", "mix test")
rust = Matcher.basic("Cargo.toml", "cargo test")
clojure = Matcher.basic("project.clj", "lein test")

# these are checked in order
ALL_MATCHERS: list[Matcher] = [
    pytest,
    py,
    # ensure ordering here
    go_multi,
    go_single,
    elixir,
    rust,
    clojure,
]
