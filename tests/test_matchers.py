from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

import universal_test_runner.matchers as matchers
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
        # each matcher depends on at least one file, so every matcher with no files should be negative
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
def test_matches(test_case: MatcherTestCase):
    context = Context.from_strings(test_case.files, test_case.args)
    assert test_case.matcher.matches(context) == test_case.passes


def test_makefile(tmp_path: Path):
    f = tmp_path / "Makefile"
    f.write_text(
        "# Run all the tests\ntest:\ngo test $(TEST_OPTIONS) -failfast -race -coverpkg=./... -covermode=atomic -coverprofile=coverage.txt $(SOURCE_FILES) -run $(TEST_PATTERN) -timeout=2m\n.PHONY: test"
    )
    context = Context([f], [])
    assert matchers.makefile.matches(context)


def test_makefile_no_test_command(tmp_path: Path):
    f = tmp_path / "Makefile"
    f.write_text(
        "# Run all the tests\nvalidate:\ngo test $(TEST_OPTIONS) -failfast -race -coverpkg=./... -covermode=atomic -coverprofile=coverage.txt $(SOURCE_FILES) -run $(TEST_PATTERN) -timeout=2m\n.PHONY: test"
    )
    context = Context([f], [])
    assert not matchers.makefile.matches(context)


def test_has_test_script():
    assert matchers.has_test_script({"scripts": {"build": "tsc", "test": "yarn"}})


def test_has_no_test_script():
    assert not matchers.has_test_script(
        {"scripts": {"build": "tsc", "validate": "yarn"}}
    )


def test_has_no__scripts():
    assert not matchers.has_test_script({})


@pytest.mark.parametrize(
    ["c", "lockfile", "expected"],
    [
        (
            Context.from_strings(["package.json", "package-lock.json"]),
            "package-lock.json",
            True,
        ),
        (Context.from_strings(["package.json"]), "package-lock.json", False),
        (
            Context.from_strings(["package.json", "yarn.lock"]),
            "yarn.lock",
            True,
        ),
        (Context.from_strings(["package.json"]), "yarn.lock", False),
        (
            Context.from_strings(["package.json", "pnpm-lock.yaml"]),
            "pnpm-lock.yaml",
            True,
        ),
        (Context.from_strings(["package.json"]), "pnpm-lock.yaml", False),
        (Context.from_strings([]), "pnpm-lock.yaml", False),
    ],
)
@patch("pathlib.Path.read_text")
def test_has_test_script_and_lockfile(
    mock_read: Mock, c: Context, lockfile: str, expected
):
    if expected:
        mock_read.return_value = '{"scripts": {"build": "tsc", "test": "yarn"}}'
    else:
        mock_read.return_value = "{}"

    assert matchers.has_test_script_and_lockfile(c, lockfile) == expected
