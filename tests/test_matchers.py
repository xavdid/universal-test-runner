from dataclasses import dataclass, field
from pathlib import Path

import pytest

import universal_test_runner.matchers as matchers
from universal_test_runner.context import Context


def test_export():
    """
    this function asserts that every defined Matcher in `matchers.py` is included in the exported `MATCHERS` list _and_ nothing is double-counted.
    """
    matcher_funcs = [
        export
        for export in dir(matchers)
        if isinstance(getattr(matchers, export), matchers.Matcher)
    ]

    assert len(matchers.ALL_MATCHERS) == len(matcher_funcs)
    assert len(set(matchers.ALL_MATCHERS)) == len(matchers.ALL_MATCHERS)
    assert matchers.ALL_MATCHERS.index(matchers.go_multi) < matchers.ALL_MATCHERS.index(
        matchers.go_single
    ), "must run go_multi before go_single"


@pytest.mark.parametrize(
    ["matcher", "result"],
    [
        (matchers.pytest, ["pytest"]),
        (matchers.py, ["python", "tests.py"]),
        (matchers.go_single, ["go", "test"]),
        (matchers.go_multi, ["go", "test", "./..."]),
        (matchers.elixir, ["mix", "test"]),
        (matchers.rust, ["cargo", "test"]),
        (matchers.clojure, ["lein", "test"]),
    ],
    ids=lambda p: repr(p) if isinstance(p, matchers.Matcher) else None,
)
def test_resulting_commands(matcher: matchers.Matcher, result: list[str]):
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
    def fail(matcher: matchers.Matcher):
        return MatcherTestCase(matcher, passes=False)


matching_tests: list[MatcherTestCase] = [
    # each matcher depends on at least one file, so every matcher with no files should be negative
    *[MatcherTestCase.fail(m) for m in matchers.ALL_MATCHERS],
    # simple cases
    MatcherTestCase(matchers.pytest, [".pytest_cache"]),
    MatcherTestCase(matchers.py, ["tests.py"]),
    MatcherTestCase(matchers.elixir, ["mix.exs"]),
    MatcherTestCase(matchers.rust, ["Cargo.toml"]),
    MatcherTestCase(matchers.clojure, ["project.clj"]),
    # go
    # these both path, so ordering matters
    MatcherTestCase(matchers.go_multi, ["go.mod"]),
    MatcherTestCase(matchers.go_single, ["go.mod"]),
    MatcherTestCase(matchers.go_multi, ["go.mod"], args=["whatever"], passes=False),
    MatcherTestCase(matchers.go_single, ["go.mod"], args=["token"]),
    MatcherTestCase(matchers.go_single, ["parser_test.go"]),
]


@pytest.mark.parametrize(
    "test_case",
    matching_tests,
    ids=repr,
)
def test_matches(test_case: MatcherTestCase):
    context = Context([Path(f) for f in test_case.files], test_case.args)
    assert test_case.matcher.test(context) == test_case.passes
