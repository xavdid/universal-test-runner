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
            lambda c: c.has_all_files(file),
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
    lambda c: c.has_all_files("go.mod") and not c.args,
    "go test ./...",
    debug_line='looking for: "go.mod" and no arguments',
)
# however, if we're in the package root and there's a test file here, then we can just run
go_single = Command(
    "go_single",
    lambda c: c.has_all_files("go.mod")
    or any(re.search(r"_test.go$", f) for f in c.filenames),
    "go test",
    debug_line='looking for: "go.mod" or a file named "..._test.go"',
)

makefile = Command(
    "makefile",
    lambda c: c.has_all_files("Makefile")
    and any(line.startswith("test:") for line in c.read_file("Makefile")),
    "make test",
    debug_line='looking for: a "Makefile" and a "test:" line',
)


def _matches_justfile(c: Context) -> bool:
    # TODO: better capitalization support? the file is supposed to be case-insensitive
    if not c.has_all_files("justfile"):
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
# don't use JS builder because it doesn't need a `test` property in pkg.json
bun = Command.basic_builder("bun", "bun.lockb", "bun test")

# TODO:
# - ruby?

PYPROJECT_TOML = "pyproject.toml"


def any_pytest_str(*deps: str) -> bool:
    return any(d.startswith("pytest") for d in deps)


def _matches_pytest(c: Context) -> bool:
    # the simplest case is if pytest has been run before and the cache is present
    # failing that, we can look for configuration in a few places
    # failing that, we can try all the places one could put dev dependencies

    # https://docs.pytest.org/en/6.2.x/customize.html#pytest-ini
    if c.has_any_files(".pytest_cache", "pytest.ini"):
        return True

    # https://docs.pytest.org/en/6.2.x/customize.html#tox-ini
    if any(line == "[pytest]" for line in c.read_file("tox.ini")):
        return True

    # https://docs.pytest.org/en/6.2.x/customize.html#setup-cfg
    if any(line == "[tool:pytest]" for line in c.read_file("setup.cfg")):
        return True

    # pyproject has a lot of info by different bundlers
    if c.has_all_files(PYPROJECT_TOML):
        if pyproject := c.read_toml(PYPROJECT_TOML):
            # first, check for a pytest configuration block
            # https://docs.pytest.org/en/6.2.x/customize.html#pyproject-toml
            if pyproject.get("tool", {}).get("pytest", {}).get("ini_options"):
                return True

            # pip looks for `name==1.2.3` or `name <= 1.2.3` style strings in a few places
            # https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#dependencies-optional-dependencies
            if any_pytest_str(
                # check dev-deps first
                # TODO: a dig method
                *pyproject.get("project", {})
                .get("optional-dependencies", {})
                .get("test", []),
                *pyproject.get("project", {})
                .get("optional-dependencies", {})
                .get("tests", []),
                *pyproject.get("project", {}).get("dependencies", []),
            ):
                return True

            # each package manager does this slightly differently, because of course it does

            # uv
            # https://docs.astral.sh/uv/concepts/dependencies/#development-dependencies
            if (
                dev_deps := pyproject.get("tool", {})
                .get("uv", {})
                .get("dev-dependencies", [])
            ) and any_pytest_str(*dev_deps):
                return True

            # poetry
            # https://python-poetry.org/docs/managing-dependencies/#dependency-groups
            for k in "test", "dev":
                if "pytest" in pyproject.get("tool", {}).get("poetry", {}).get(
                    "group", {}
                ).get(k, {}).get("dependencies", {}):
                    return True

            # pdm
            # https://pdm-project.org/latest/usage/dependency/#add-development-only-dependencies
            if any_pytest_str(
                *pyproject.get("tool", {})
                .get("pdm", {})
                .get("dev-dependencies", {})
                .get("test", [])
            ):
                return True

        else:
            # file is present, but tomllib isn't. Do a best effort search?
            contents = c.load_file(PYPROJECT_TOML)
            # could have a config key or could mention a pytest==1.2.3 dep, hard to say
            if "[tool.pytest.ini_options]" in contents or bool(
                re.search(r"\"pytest ?[<=>]?", contents)
            ):
                return True

    return False


# misc simple cases
pytest = Command(
    "pytest",
    _matches_pytest,
    "pytest",
    debug_line='looking for: a ".pytest_cache", pytest configuration files, or a dependency on pytest in "pyproject.toml" (from any popular package manager)',
)
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
    # pytest has django plugins, so if there's both, assume they want pytest
    pytest,
    django,
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
