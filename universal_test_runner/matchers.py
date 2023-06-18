import re
from dataclasses import dataclass
from typing import Callable, Optional

from universal_test_runner.context import Context

# TODO: add user-enableable debug logs


@dataclass(frozen=True)  # frozen so I can hash them for tests
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
    def basic_builder(name: str, file: str, command: str) -> "Matcher":
        """
        shorthand builder for running a command if a single file is in the file list
        """
        return Matcher(name, lambda c: c.has_files(file), command)

    @staticmethod
    def js_builder(name: str, lockfile: str) -> "Matcher":
        return Matcher(
            name, lambda c: c.has_test_script_and_lockfile(lockfile), f"{name} test"
        )


# for go modules with nested packages, running `go test` on its own runs no test.
# so we have to include the ./... to pick up all packages
go_multi = Matcher(
    "go_multi", lambda c: c.has_files("go.mod") and not c.args, "go test ./..."
)
# however, if we're in the package root and there's a test file here, then we can just run
go_single = Matcher(
    "go_single",
    lambda c: c.has_files("go.mod") or any(re.search(r"_test.go$", f) for f in c.files),
    "go test",
)

makefile = Matcher(
    "makefile",
    lambda c: c.has_files("Makefile")
    and any(l.startswith("test:") for l in c.read_file("Makefile")),
    "make test",
)

npm = Matcher.js_builder("npm", "package-lock.json")
yarn = Matcher.js_builder("yarn", "yarn.lock")
pnpm = Matcher.js_builder("pnpm", "pnpm-lock.yaml")

# TODO:
# - ruby?

# misc simple cases
pytest = Matcher.basic_builder("pytest", ".pytest_cache", "pytest")
py = Matcher.basic_builder("py", "tests.py", "python tests.py")
elixir = Matcher.basic_builder("elixir", "mix.exs", "mix test")
rust = Matcher.basic_builder("rust", "Cargo.toml", "cargo test")
clojure = Matcher.basic_builder("clojure", "project.clj", "lein test")

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
    npm,
    yarn,
    pnpm,
    makefile,
]
