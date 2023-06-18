import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

import universal_test_runner.matchers as matchers
from tests.conftest import ContextBuilderFunc, FileWriterFunc
from universal_test_runner.context import Context

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
    ), "a matcher is missing its simple command test"


@pytest.mark.parametrize(
    ["matcher", "result"],
    simple_command_tests,
    ids=lambda p: repr(p) if isinstance(p, matchers.Matcher) else None,
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
