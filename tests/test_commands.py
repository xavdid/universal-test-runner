import json
import subprocess
from dataclasses import dataclass, field
from unittest.mock import Mock, patch

import pytest

import universal_test_runner.commands as commands
from tests.conftest import ContextBuilderFunc, FileWriterFunc
from universal_test_runner.context import load_toml

command_instances = [
    export
    for export in dir(commands)
    if isinstance(getattr(commands, export), commands.Command)
]


def test_export():
    """
    this function asserts that every defined Command in `command.py` is included in the exported `ALL_COMMANDS` list _and_ nothing is double-counted.
    """

    assert len(commands.ALL_COMMANDS) == len(
        command_instances
    ), "a command was written but not added to ALL_COMMANDS"
    assert len(set(commands.ALL_COMMANDS)) == len(commands.ALL_COMMANDS)
    assert commands.ALL_COMMANDS.index(commands.go_multi) < commands.ALL_COMMANDS.index(
        commands.go_single
    ), "must run go_multi before go_single"


simple_command_tests = [
    (commands.pytest, ["pytest"]),
    (commands.py, ["python", "tests.py"]),
    (commands.django, ["./manage.py", "test"]),
    (commands.go_single, ["go", "test"]),
    (commands.go_multi, ["go", "test", "./..."]),
    (commands.elixir, ["mix", "test"]),
    (commands.rust, ["cargo", "test"]),
    (commands.clojure, ["lein", "test"]),
    (commands.makefile, ["make", "test"]),
    (commands.npm, ["npm", "test"]),
    (commands.yarn, ["yarn", "test"]),
    (commands.pnpm, ["pnpm", "test"]),
    (commands.bun, ["bun", "test"]),
    (commands.justfile, ["just", "test"]),
    (commands.exercism, ["exercism", "test", "--"]),
    (commands.advent_of_code, ["./advent"]),
]


def test_all_commandss_have_simple_command_test():
    assert len(simple_command_tests) == len(
        command_instances
    ), "a command is missing from simple_command_tests"


@pytest.mark.parametrize(
    ["command", "result"],
    simple_command_tests,
    ids=[repr(m[0]) for m in simple_command_tests],
)
def test_simple_commands(command: commands.Command, result: list[str]):
    """
    a simple list of the commands for each command so we know if they change unexpectedly
    """
    assert command.test_command == result


@dataclass(frozen=True)
class CommandTestCase:
    command: commands.Command
    files: list[str] = field(default_factory=list)
    # what's the resulting command? if empty, means the test passes
    passes: bool = True
    args: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"{self.command} w/ files={self.files} & args={self.args} -> `{self.passes}`"


@pytest.mark.parametrize(
    "test_case",
    [
        # each command depends on at least one file, so each command with no files should not match
        *[CommandTestCase(m, passes=False) for m in commands.ALL_COMMANDS],
        # simple cases
        CommandTestCase(commands.pytest, [".pytest_cache"]),
        CommandTestCase(commands.pytest, ["pytest.ini"]),
        CommandTestCase(commands.py, ["tests.py"]),
        CommandTestCase(commands.django, ["manage.py"]),
        CommandTestCase(commands.elixir, ["mix.exs"]),
        CommandTestCase(commands.rust, ["Cargo.toml"]),
        CommandTestCase(commands.clojure, ["project.clj"]),
        # these both pass, so ordering in the master list matters
        CommandTestCase(commands.go_multi, ["go.mod"]),
        CommandTestCase(commands.go_single, ["go.mod"]),
        CommandTestCase(commands.go_multi, ["go.mod"], args=["whatever"], passes=False),
        CommandTestCase(commands.go_single, ["go.mod"], args=["token"]),
        CommandTestCase(commands.go_single, ["parser_test.go"]),
        CommandTestCase(commands.justfile, ["Justfile"], passes=False),
        CommandTestCase(commands.exercism, [".exercism"]),
        CommandTestCase(commands.advent_of_code, ["advent"]),
    ],
    ids=repr,
)
def test_matches(test_case: CommandTestCase, build_context: ContextBuilderFunc):
    """
    a basic assertion to check that a given set of files/args match a specific Command (in isolation)
    """
    context = build_context(test_case.files, test_case.args)
    assert test_case.command.should_run(context) == test_case.passes


@pytest.mark.parametrize(
    ["text", "expected"],
    [
        (
            "# Run all the tests\ntest:\ngo test $(TEST_OPTIONS) -failfast -race -coverpkg=./... -covermode=atomic -coverprofile=coverage.txt $(SOURCE_FILES) -run $(TEST_PATTERN) -timeout=2m\n.PHONY: test",
            True,
        ),
        (
            "# Run all the tests\nvalidate:\ngo test $(TEST_OPTIONS) -failfast -race -coverpkg=./... -covermode=atomic -coverprofile=coverage.txt $(SOURCE_FILES) -run $(TEST_PATTERN) -timeout=2m\n.PHONY: test",
            False,
        ),
    ],
)
def test_makefile(
    text, expected, write_file: FileWriterFunc, build_context: ContextBuilderFunc
):
    write_file("Makefile", text)
    c = build_context()

    assert commands.makefile.should_run(c) == expected


@pytest.mark.parametrize(
    ["text", "expected"],
    [
        ("test *options:\n    pytest {{options}}", True),
        ("test:\n    pytest", True),
        ("@test *options:\n    pytest {{options}}", True),
        ("@test:\n    pytest", True),
        ("validate:\n    pytest {{options}}", False),
        ("validate *options:\n    pytest {{options}}", False),
        ("@validate:\n    pytest {{options}}", False),
        ("@validate *options:\n    pytest {{options}}", False),
        ("testacular:\n    pytest", False),
        ("testacular *options:\n    pytest {{options}}", False),
        ("@testacular:\n    pytest", False),
        ("@testacular *options:\n    pytest {{options}}", False),
    ],
)
@patch("subprocess.run")
def test_parse_justfile(
    mock_run: Mock,
    text,
    expected,
    write_file: FileWriterFunc,
    build_context: ContextBuilderFunc,
):
    """
    this test is relevant when `just` isn't installed and we're parsing the file manually
    """
    mock_run.side_effect = FileNotFoundError()
    write_file("justfile", text)
    c = build_context()

    assert commands.justfile.should_run(c) == expected


@pytest.mark.parametrize(
    ["recipe", "expected"], [("test", True), ("validate", False), ("testacular", False)]
)
@patch("subprocess.run")
def test_dump_justfile(
    mock_run: Mock,
    justfile_json,
    recipe: str,
    expected: bool,
    build_context: ContextBuilderFunc,
):
    mock_run.return_value.stdout = justfile_json(recipe)
    c = build_context(["justfile"])

    assert commands.justfile.should_run(c) == expected


@patch("subprocess.run")
def test_invalid_justfile(mock_run: Mock, build_context: ContextBuilderFunc):
    mock_run.side_effect = subprocess.CalledProcessError(1, "invalid justfile!")
    c = build_context(["justfile"])
    c.load_file.cache_clear()

    assert commands.justfile.should_run(c) is False
    # tried to load the file
    assert c.load_file.cache_info().currsize == 1
    assert c.load_file.cache_info().hits == 0
    assert c.load_file.cache_info().misses == 1


@dataclass(frozen=True)
class CommandFinderTestCase:
    files: list[str]
    expected_command: str
    args: list[str] = field(default_factory=list)
    file_contents: list[tuple[str, str]] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"files={self.files + [name for name,_ in self.file_contents]} & args={self.args} -> `{self.expected_command}`"


@pytest.mark.parametrize(
    "test_case",
    [
        CommandFinderTestCase([".pytest_cache"], "pytest"),
        CommandFinderTestCase(["pytest.ini"], "pytest"),
        CommandFinderTestCase(
            [],
            "pytest",
            file_contents=[
                ("pyproject.toml", '[tool.pytest.ini_options]\nminversion = "6.0"')
            ],
        ),
        CommandFinderTestCase(
            [],
            "pytest",
            file_contents=[("setup.cfg", "[tool:pytest]\nminversion = 6.0")],
        ),
        CommandFinderTestCase(
            [],
            "pytest",
            file_contents=[("tox.ini", "[pytest]\nminversion = 6.0")],
        ),
        CommandFinderTestCase(["manage.py"], "./manage.py test"),
        CommandFinderTestCase(["manage.py", ".pytest_cache"], "pytest"),
        CommandFinderTestCase(["tests.py"], "python tests.py"),
        CommandFinderTestCase(["go.mod"], "go test ./..."),
        CommandFinderTestCase(
            ["go.mod"], args=["parser"], expected_command="go test parser"
        ),
        CommandFinderTestCase(["parser_test.go"], "go test"),
        CommandFinderTestCase(
            ["parser_test.go"], args=["-v"], expected_command="go test -v"
        ),
        CommandFinderTestCase(["mix.exs"], "mix test"),
        CommandFinderTestCase(["Cargo.toml"], "cargo test"),
        CommandFinderTestCase(["project.clj"], "lein test"),
        CommandFinderTestCase([], ""),
        # basic content tests
        CommandFinderTestCase(
            [], "make test", file_contents=[("Makefile", "test: cool")]
        ),
        # js matches based on script and lockfile
        *[
            CommandFinderTestCase(
                [lockfile],
                f"{cmd} test",
                file_contents=[
                    (
                        "package.json",
                        json.dumps({"name": "whatever", "scripts": {"test": "ok"}}),
                    )
                ],
            )
            for lockfile, cmd in [
                ("package-lock.json", "npm"),
                ("yarn.lock", "yarn"),
                ("pnpm-lock.yaml", "pnpm"),
            ]
        ],
        # no match without the script
        *[
            CommandFinderTestCase(
                [lockfile],
                "",
                file_contents=[
                    (
                        "package.json",
                        json.dumps({"name": "whatever", "scripts": {"xtest": "ok"}}),
                    )
                ],
            )
            for lockfile in [
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
            ]
        ],
        # bun doesn't care about package.json
        CommandFinderTestCase(["bun.lockb"], "bun test"),
        # bun wins ties only if there's no explicit "scripts.test" property
        CommandFinderTestCase(
            ["bun.lockb", "yarn.lock"],
            "bun test",
            file_contents=[
                ("package.json", json.dumps({"scripts": {"xtest": "whatever"}}))
            ],
        ),
        CommandFinderTestCase(
            ["bun.lockb", "yarn.lock"],
            "yarn test",
            file_contents=[
                ("package.json", json.dumps({"scripts": {"test": "whatever"}}))
            ],
        ),
        # if a task runner runs pytest, defer to the runner
        CommandFinderTestCase(
            [".pytest_cache"], "make test", file_contents=[("Makefile", "test: cool")]
        ),
        CommandFinderTestCase(
            [".pytest_cache", "manage.py"],
            "make test",
            file_contents=[("Makefile", "test:\n  cool")],
        ),
        CommandFinderTestCase(
            ["manage.py"],
            "make test",
            file_contents=[("Makefile", "test:\n  cool")],
        ),
        # exercism takes precedence over makefiles
        CommandFinderTestCase([".exercism", "Makefile"], "exercism test --"),
        CommandFinderTestCase(
            ["advent"], "make test", file_contents=[("Makefile", "test: cool")]
        ),
        CommandFinderTestCase(["advent", ".pytest_cache"], "./advent"),
    ],
    ids=repr,
)
@patch("subprocess.run")
def test_find_test_command(
    mock_run: Mock,
    test_case: CommandFinderTestCase,
    build_context: ContextBuilderFunc,
    write_file: FileWriterFunc,
):
    """
    while other tests verify that a specific file passes a specific command,
    this makes assertions about the resulting command while running through the entire matching process

    it's useful for ensuring ordering of certain commands
    """

    mock_run.side_effect = lambda *_, **__: pytest.fail(
        "this test shouldn't be shelling out at all"
    )

    for f in test_case.file_contents:
        write_file(*f)

    c = build_context(test_case.files, test_case.args)
    assert commands.find_test_command(c) == test_case.expected_command.split()


@pytest.mark.parametrize(
    ["test_case", "recipe"],
    [
        (CommandFinderTestCase(["justfile"], "just test"), "test"),
        (CommandFinderTestCase(["justfile"], ""), "xtest"),
        (CommandFinderTestCase([".pytest_cache", "justfile"], "just test"), "test"),
        (CommandFinderTestCase([".pytest_cache", "justfile"], "pytest"), "xtest"),
        (
            CommandFinderTestCase(
                [".pytest_cache", "manage.py", "justfile"], "just test"
            ),
            "test",
        ),
        (
            CommandFinderTestCase([".pytest_cache", "manage.py", "justfile"], "pytest"),
            "xtest",
        ),
        (CommandFinderTestCase([".exercism", "justfile"], "just test"), "test"),
        (CommandFinderTestCase([".exercism", "justfile"], "exercism test --"), "xtest"),
        (CommandFinderTestCase(["justfile", "advent"], "just test"), "test"),
        (CommandFinderTestCase(["justfile", "advent"], "./advent"), "xtest"),
    ],
)
@patch("subprocess.run")
def test_find_command_test_runner_priority(
    mock_run: Mock,
    test_case: CommandFinderTestCase,
    recipe,
    build_context: ContextBuilderFunc,
    justfile_json,
):
    """
    like the above, but `just` is installed and returns valid json (if required)
    """
    mock_run.return_value.stdout = justfile_json(recipe)

    c = build_context(test_case.files, test_case.args)
    assert commands.find_test_command(c) == test_case.expected_command.split()


@pytest.mark.parametrize(
    "file_contents",
    [
        '[tool.pytest]\nini_options = { minversion = "6.0" }',
        '[tool.poetry.group.test.dependencies]\npytest = "^6.0.0"\npytest-mock = "*"',
        '[tool.poetry.group.dev.dependencies]\npytest = "~7.0.0"',
    ],
)
def test_non_simple_toml_parsing(
    file_contents, build_context: ContextBuilderFunc, write_file: FileWriterFunc
):
    """
    Python <= 3.10 doesn't ship with tomllib and each of these tests is non-simple. Each works with good parsing, but fails on older versions. I could skip this test on older versions, but I can also just search for (and find) nothing.

    Can remove the failure cases after 2026-10-31
    https://endoflife.date/python
    """

    write_file("pyproject.toml", file_contents)
    c = build_context(["pyproject.toml"])
    expected = ["pytest"] if load_toml else []

    assert commands.find_test_command(c) == expected


@pytest.mark.parametrize(
    "file_contents",
    [
        '[project]\ndependencies = [ "httpx", "pytest" ]',
        '[project.optional-dependencies]\ntest = ["pytest==2"]',
        '[project.optional-dependencies]\ntests = ["pytest >= 3"]',
        '[tool.uv]\ndev-dependencies = [\n  "pytest >=8.1.1,<9"\n]',
        '[tool.pdm.dev-dependencies]\ntest = ["pytest>= 3"]',
    ],
)
def test_toml_parsing(
    file_contents, build_context: ContextBuilderFunc, write_file: FileWriterFunc
):
    """
    There are a few cases where, even without tomllib, we can pull a pytest dep out of a file. These should pass on all Python versions.
    """

    write_file("pyproject.toml", file_contents)
    c = build_context(["pyproject.toml"])

    assert commands.find_test_command(c) == ["pytest"]
