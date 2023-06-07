import re
from dataclasses import dataclass
from typing import Callable, Optional

from universal_test_runner.context import Context

# TODO: add user-enableable debug logs


@dataclass(frozen=True)
class Matcher:
    name: str
    matches: Callable[[Context], Optional[bool]]
    _command: str

    @property
    def command(self) -> list[str]:
        return self._command.split()

    def __repr__(self) -> str:
        return f"<Matcher {self.name}>"

    @staticmethod
    def basic(name: str, file: str, command: str):
        """
        shorthand for running a command if a single file is in the file list
        """
        return Matcher(name, lambda c: file in c.files, command)


# for go modules with nested packages, running `go test` on its own runs no test.
# so we have to include the ./... to pick up all packages
go_multi = Matcher(
    "go_multi", lambda c: "go.mod" in c.files and not c.args, "go test ./..."
)
# however, if we're in the package root and there's a test file here, then we can just run
go_single = Matcher(
    "go_single",
    lambda c: "go.mod" in c.files or any(re.search(r"_test.go$", f) for f in c.files),
    "go test",
)

# TODO:
# - js
# - makefile?
# - ruby?

# misc simple cases
pytest = Matcher.basic("pytest", ".pytest_cache", "pytest")
py = Matcher.basic("py", "tests.py", "python tests.py")
elixir = Matcher.basic("elixir", "mix.exs", "mix test")
rust = Matcher.basic("rust", "Cargo.toml", "cargo test")
clojure = Matcher.basic("clojure", "project.clj", "lein test")

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
