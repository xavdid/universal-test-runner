import re
from dataclasses import dataclass
from typing import Callable, Optional

from universal_test_runner.context import Context


@dataclass(frozen=True)  # frozen so I can hash them for tests
class Matcher:
    name: str
    matches: Callable[[Context], Optional[bool]]
    _command: str
    debug_line: str

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
        return Matcher(
            name,
            lambda c: c.has_files(file),
            command,
            debug_line=f'looking for: "{file}"',
        )

    @staticmethod
    def js_builder(name: str, lockfile: str) -> "Matcher":
        return Matcher(
            name,
            lambda c: c.has_test_script_and_lockfile(lockfile),
            f"{name} test",
            debug_line=f'looking for: "package.json", a "scripts.test" property, and a "{lockfile}"',
        )


# for go modules with nested packages, running `go test` on its own runs no test.
# so we have to include the ./... to pick up all packages
go_multi = Matcher(
    "go_multi",
    lambda c: c.has_files("go.mod") and not c.args,
    "go test ./...",
    debug_line='looking for: "go.mod" and no arguments',
)
# however, if we're in the package root and there's a test file here, then we can just run
go_single = Matcher(
    "go_single",
    lambda c: c.has_files("go.mod")
    or any(re.search(r"_test.go$", f) for f in c.filenames),
    "go test",
    debug_line='looking for: "go.mod" or a file named "..._test.go"',
)

makefile = Matcher(
    "makefile",
    lambda c: c.has_files("Makefile")
    and any(l.startswith("test:") for l in c.read_file("Makefile")),
    "make test",
    debug_line='looking for: a "Makefile" and a "test:" line',
)

justfile = Matcher(
    "justfile",
    # TODO: better capitalization support? the file is supposed to be case-insensitive
    lambda c: c.has_files("justfile")
    # TODO: maybe use the JSON interface once https://github.com/casey/just/issues/1632 is closed
    # less guessing that way
    and any(
        l.startswith("test") or l.startswith("@test") for l in c.read_file("justfile")
    ),
    "just test",
    debug_line='looking for: a "justfile" and a "test" or "@test" line',
)

npm = Matcher.js_builder("npm", "package-lock.json")
yarn = Matcher.js_builder("yarn", "yarn.lock")
pnpm = Matcher.js_builder("pnpm", "pnpm-lock.yaml")

# TODO:
# - ruby?

# misc simple cases
pytest = Matcher.basic_builder("pytest", ".pytest_cache", "pytest")
py = Matcher.basic_builder("py", "tests.py", "python tests.py")
django = Matcher.basic_builder("django", "manage.py", "./manage.py test")
elixir = Matcher.basic_builder("elixir", "mix.exs", "mix test")
rust = Matcher.basic_builder("rust", "Cargo.toml", "cargo test")
clojure = Matcher.basic_builder("clojure", "project.clj", "lein test")

# these are checked in order
ALL_MATCHERS: list[Matcher] = [
    justfile,
    makefile,
    # make sure django goes before pytest, since django can use pytest
    # (there's a test to confirm this behavior)
    django,
    pytest,
    py,
    # ensure ordering for go matchers
    go_multi,
    go_single,
    elixir,
    rust,
    clojure,
    npm,
    yarn,
    pnpm,
]

NUM_MATCHERS = len(ALL_MATCHERS)


def find_test_command(context: Context) -> list[str]:
    context.debug("checking each handler for first match")
    for i, matcher in enumerate(ALL_MATCHERS):
        context.debug(
            f"Checking matcher {i+1:02}/{NUM_MATCHERS}: {matcher.name}", indent=2
        )
        context.debug(matcher.debug_line, indent=4)
        if matcher.matches(context):
            context.debug("matched!", indent=4)
            context.debug(f"would have run: `{matcher._command}`", indent=6)
            return [*matcher.command, *context.args]

        context.debug("no match, continuing", indent=4)

    context.debug(
        "no matching test handler. To add a new one, please file an issue: https://github.com/xavdid/universal-test-runner/issues"
    )
    return []
