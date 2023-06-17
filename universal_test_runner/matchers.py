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
        return Matcher(name, lambda c: c.has_files(file), command)


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

has_test_script = lambda d: bool(d.get("scripts", {}).get("test"))


def has_test_script_and_lockfile(c: Context, lockfile: str) -> bool:
    return c.has_files("package.json", lockfile) and has_test_script(
        c.read_json("package.json")
    )


def build_js_matcher(name: str, lockfile: str):
    return Matcher(
        name, lambda c: has_test_script_and_lockfile(c, lockfile), f"{name} test"
    )


npm = build_js_matcher("npm", "package-lock.json")
yarn = build_js_matcher("yarn", "yarn.lock")
pnpm = build_js_matcher("pnpm", "pnpm-lock.yaml")

# TODO:
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
    npm,
    yarn,
    pnpm,
    makefile,
]
