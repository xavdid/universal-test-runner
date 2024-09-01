import json
import re
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional

from universal_test_runner.context import Context


@dataclass(frozen=True)  # frozen so I can hash them for tests
class Command:
    """
    Encapsulates:
        - a test command to run
        - a set of conditions needed for this command to apply

    Also includes some convenience methods for producing `Command` instances that follow certain simple patterns
    """

    name: str
    should_run: Callable[[Context], Optional[bool]]
    _test_command: str
    debug_line: str

    @property
    def test_command(self) -> list[str]:
        return self._test_command.split()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.name}>"

    @staticmethod
    def basic_builder(name: str, file: str, command: str) -> "Command":
        """
        shorthand builder for running a command if a single file is in the file list
        """
        return Command(
            name,
            lambda c: c.has_files(file),
            command,
            debug_line=f'looking for: "{file}"',
        )

    @staticmethod
    def js_builder(name: str, lockfile: str) -> "Command":
        return Command(
            name,
            lambda c: c.has_test_script_and_lockfile(lockfile),
            f"{name} test",
            debug_line=f'looking for: "package.json", a "scripts.test" property, and a "{lockfile}"',
        )


# for go modules with nested packages, running `go test` on its own runs no test.
# so we have to include the ./... to pick up all packages
go_multi = Command(
    "go_multi",
    lambda c: c.has_files("go.mod") and not c.args,
    "go test ./...",
    debug_line='looking for: "go.mod" and no arguments',
)
# however, if we're in the package root and there's a test file here, then we can just run
go_single = Command(
    "go_single",
    lambda c: c.has_files("go.mod")
    or any(re.search(r"_test.go$", f) for f in c.filenames),
    "go test",
    debug_line='looking for: "go.mod" or a file named "..._test.go"',
)

makefile = Command(
    "makefile",
    lambda c: c.has_files("Makefile")
    and any(line.startswith("test:") for line in c.read_file("Makefile")),
    "make test",
    debug_line='looking for: a "Makefile" and a "test:" line',
)


def _matches_justfile(c: Context) -> bool:
    # TODO: better capitalization support? the file is supposed to be case-insensitive
    if not c.has_files("justfile"):
        return False

    # try to call `just` and get the JSON structure
    try:
        result = subprocess.run(
            # unstable flag isn't needed now that https://github.com/casey/just/issues/1632 is merged
            # but all users may not have it yet and I don't expect the format to change
            ["just", "--dump", "--dump-format", "json", "--unstable"],
            capture_output=True,
            cwd=c.cwd,
            check=True,
        )
        file = json.loads(result.stdout)
        return "test" in file.get("recipes", {})

    except (FileNotFoundError, subprocess.CalledProcessError):
        # either:
        # - just isn't installed
        # - something else went wrong (probably an invalid justfile)
        # in either case, fall back to a more basic check and let `just` error out if relevant
        return any(re.match(r"^@?test(:| )", line) for line in c.read_file("justfile"))


justfile = Command(
    "justfile",
    _matches_justfile,
    "just test",
    debug_line='looking for: a "justfile" and a "test" or "@test" line',
)

npm = Command.js_builder("npm", "package-lock.json")
yarn = Command.js_builder("yarn", "yarn.lock")
pnpm = Command.js_builder("pnpm", "pnpm-lock.yaml")
bun = Command.basic_builder("bun", "bun.lockb", "bun test")

# TODO:
# - ruby?

# misc simple cases
pytest = Command.basic_builder("pytest", ".pytest_cache", "pytest")
py = Command.basic_builder("py", "tests.py", "python tests.py")
django = Command.basic_builder("django", "manage.py", "./manage.py test")
elixir = Command.basic_builder("elixir", "mix.exs", "mix test")
rust = Command.basic_builder("rust", "Cargo.toml", "cargo test")
clojure = Command.basic_builder("clojure", "project.clj", "lein test")
exercism = Command.basic_builder("exercism", ".exercism", "exercism test --")
advent_of_code = Command.basic_builder("advent of code", "advent", "./advent")

# these are checked in order
ALL_COMMANDS: list[Command] = [
    justfile,
    exercism,
    makefile,
    advent_of_code,
    django,
    # anything that could run pytest should go before it
    pytest,
    py,
    # ensure ordering for go commands
    go_multi,
    go_single,
    elixir,
    rust,
    clojure,
    npm,
    yarn,
    pnpm,
    bun,
]

NUM_COMMANDS = len(ALL_COMMANDS)


def find_test_command(context: Context) -> list[str]:
    context.debug("checking each handler for first match")
    for i, command in enumerate(ALL_COMMANDS):
        context.debug(
            f"Checking command {i+1:02}/{NUM_COMMANDS}: {command.name}", indent=2
        )
        context.debug(command.debug_line, indent=4)
        if command.should_run(context):
            context.debug("matched!", indent=4)
            context.debug(f"would have run: `{command._test_command}`", indent=6)
            return [*command.test_command, *context.args]

        context.debug("no match, continuing", indent=4)

    # LOAD BEARING - the homebrew formula expects "no matching test handler" to be present if there's no match
    context.debug(
        "no matching test handler. To add a new one, please file an issue: https://github.com/xavdid/universal-test-runner/issues"
    )
    return []
