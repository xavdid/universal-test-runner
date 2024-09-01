import json
import subprocess
from dataclasses import dataclass, field
from unittest.mock import Mock, patch

import pytest

import universal_test_runner.matchers as matchers
from tests.conftest import ContextBuilderFunc, FileWriterFunc

matcher_funcs = [
    export
    for export in dir(matchers)
    if isinstance(getattr(matchers, export), matchers.Matcher)
]


def test_export():
    """
    this function asserts that every defined Matcher in `matchers.py` is included in the exported `MATCHERS` list _and_ nothing is double-counted.
    """

    assert len(matchers.ALL_MATCHERS) == len(
        matcher_funcs
    ), "a matcher was written but not added to ALL_MATCHERS"
    assert len(set(matchers.ALL_MATCHERS)) == len(matchers.ALL_MATCHERS)
    assert matchers.ALL_MATCHERS.index(matchers.go_multi) < matchers.ALL_MATCHERS.index(
        matchers.go_single
    ), "must run go_multi before go_single"


simple_command_tests = [
    (matchers.pytest, ["pytest"]),
    (matchers.py, ["python", "tests.py"]),
    (matchers.django, ["./manage.py", "test"]),
    (matchers.go_single, ["go", "test"]),
    (matchers.go_multi, ["go", "test", "./..."]),
    (matchers.elixir, ["mix", "test"]),
    (matchers.rust, ["cargo", "test"]),
    (matchers.clojure, ["lein", "test"]),
    (matchers.makefile, ["make", "test"]),
    (matchers.npm, ["npm", "test"]),
    (matchers.yarn, ["yarn", "test"]),
    (matchers.pnpm, ["pnpm", "test"]),
    (matchers.bun, ["bun", "test"]),
    (matchers.justfile, ["just", "test"]),
    (matchers.exercism, ["exercism", "test", "--"]),
    (matchers.advent_of_code, ["./advent"]),
]


def test_all_matchers_have_simple_command_test():
    assert len(simple_command_tests) == len(
        matcher_funcs
    ), "a matcher is missing from simple_command_tests"


@pytest.mark.parametrize(
    ["matcher", "result"],
    simple_command_tests,
    ids=[repr(m[0]) for m in simple_command_tests],
)
def test_simple_commands(matcher: matchers.Matcher, result: list[str]):
    """
    a simple list of the commands for each matcher so we know if they change unexpectedly
    """
    assert matcher.command == result


@dataclass
class MatcherTestCase:
    matcher: matchers.Matcher
    files: list[str] = field(default_factory=list)
    # what's the resulting command? if empty, means the test passes
    passes: bool = True
    args: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"{self.matcher} w/ files={self.files} & args={self.args} -> `{self.passes}`"


@pytest.mark.parametrize(
    "test_case",
    [
        # each matcher depends on at least one file, so each matcher with no files should not match
        *[MatcherTestCase(m, passes=False) for m in matchers.ALL_MATCHERS],
        # simple cases
        MatcherTestCase(matchers.pytest, [".pytest_cache"]),
        MatcherTestCase(matchers.py, ["tests.py"]),
        MatcherTestCase(matchers.django, ["manage.py"]),
        MatcherTestCase(matchers.elixir, ["mix.exs"]),
        MatcherTestCase(matchers.rust, ["Cargo.toml"]),
        MatcherTestCase(matchers.clojure, ["project.clj"]),
        # these both pass, so ordering in the master list matters
        MatcherTestCase(matchers.go_multi, ["go.mod"]),
        MatcherTestCase(matchers.go_single, ["go.mod"]),
        MatcherTestCase(matchers.go_multi, ["go.mod"], args=["whatever"], passes=False),
        MatcherTestCase(matchers.go_single, ["go.mod"], args=["token"]),
        MatcherTestCase(matchers.go_single, ["parser_test.go"]),
        MatcherTestCase(matchers.justfile, ["Justfile"], passes=False),
        MatcherTestCase(matchers.exercism, [".exercism"]),
        MatcherTestCase(matchers.advent_of_code, ["advent"]),
    ],
    ids=repr,
)
def test_matches(test_case: MatcherTestCase, build_context: ContextBuilderFunc):
    """
    a basic assertion to check that a given set of files/args match a specific Matcher (in isolation)
    """
    context = build_context(test_case.files, test_case.args)
    assert test_case.matcher.matches(context) == test_case.passes


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

    assert matchers.makefile.matches(c) == expected


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

    assert matchers.justfile.matches(c) == expected


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

    assert matchers.justfile.matches(c) == expected


@patch("subprocess.run")
def test_invalid_justfile(mock_run: Mock, build_context: ContextBuilderFunc):
    mock_run.side_effect = subprocess.CalledProcessError(1, "invalid justfile!")
    c = build_context(["justfile"])
    c._load_file.cache_clear()

    assert matchers.justfile.matches(c) is False
    # tried to load the file
    assert c._load_file.cache_info().currsize == 1
    assert c._load_file.cache_info().hits == 0
    assert c._load_file.cache_info().misses == 1


@dataclass
class CommandFinderTestCase:
    files: list[str]
    expected_command: str
    args: list[str] = field(default_factory=list)
    file_contents: list[tuple[str, str]] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"files={self.files}+{[name for name,_ in self.file_contents]} & args={self.args} -> `{self.expected_command}`"


@pytest.mark.parametrize(
    "test_case",
    [
        CommandFinderTestCase([".pytest_cache"], "pytest"),
        CommandFinderTestCase([".pytest_cache"], "pytest"),
        CommandFinderTestCase(["manage.py"], "./manage.py test"),
        CommandFinderTestCase(["manage.py", ".pytest_cache"], "./manage.py test"),
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
        CommandFinderTestCase([".pytest_cache", "manage.py"], "./manage.py test"),
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
    while other tests verify that a specific file passes a specific matcher,
    this makes assertions about the resulting command while running through the entire matching process

    it's useful for ensuring ordering of certain matchers
    """

    mock_run.side_effect = lambda *_, **__: pytest.fail(
        "this test shouldn't be shelling out at all"
    )

    for f in test_case.file_contents:
        write_file(*f)

    c = build_context(test_case.files, test_case.args)
    assert matchers.find_test_command(c) == test_case.expected_command.split()


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
            CommandFinderTestCase(
                [".pytest_cache", "manage.py", "justfile"], "./manage.py test"
            ),
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
    assert matchers.find_test_command(c) == test_case.expected_command.split()
