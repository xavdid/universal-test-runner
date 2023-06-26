import json
from dataclasses import dataclass, field

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

    @staticmethod
    def failing_case(matcher: matchers.Matcher):
        return MatcherTestCase(matcher, passes=False)


@pytest.mark.parametrize(
    "test_case",
    [
        # each matcher depends on at least one file, so each matcher with no files should not match
        *[MatcherTestCase.failing_case(m) for m in matchers.ALL_MATCHERS],
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


@dataclass
class CommandFinderTestCase:
    files: list[str]
    expected_command: str
    args: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"files={self.files} & args={self.args} -> `{self.expected_command}`"


@pytest.mark.parametrize(
    "test_case",
    [
        CommandFinderTestCase([".pytest_cache"], "pytest"),
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
    ],
    ids=repr,
)
def test_find_test_command(
    test_case: CommandFinderTestCase, build_context: ContextBuilderFunc
):
    """
    while other tests verify that a specific file passes a specific matcher,
    this makes assertions about the resulting command while running through the entire matching process
    """
    c = build_context(test_case.files, test_case.args)
    assert matchers.find_test_command(c) == test_case.expected_command.split()


def test_find_test_command_makefile(
    build_context: ContextBuilderFunc, write_file: FileWriterFunc
):
    write_file("Makefile", "test: cool")
    c = build_context(["Makefile"])
    assert matchers.find_test_command(c) == ["make", "test"]


@pytest.mark.parametrize(
    ["lockfile", "command"],
    [
        ("package-lock.json", "npm"),
        ("yarn.lock", "yarn"),
        ("pnpm-lock.yaml", "pnpm"),
    ],
)
def test_find_test_command_pkgjson(
    lockfile: str,
    command: str,
    build_context: ContextBuilderFunc,
    write_file: FileWriterFunc,
):
    write_file(
        "package.json", json.dumps({"name": "whatever", "scripts": {"test": "ok"}})
    )

    c = build_context([lockfile])
    assert matchers.find_test_command(c) == [command, "test"]
