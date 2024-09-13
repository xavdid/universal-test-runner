import pytest

from universal_test_runner.commands import any_pytest_str, dig


@pytest.mark.parametrize(
    ["obj", "path", "default", "expected"],
    [
        # basic
        ({"here": "there"}, ["here"], "default", "there"),
        ({"here": "there"}, ["gone"], "default", "default"),
        # deep
        (
            {"tool": {"pytest": {"ini_options": "neat"}}},
            ["tool", "pytest", "ini_options"],
            "deafult",
            "neat",
        ),
        # deep missing
        (
            {"tool": {"pytest": {"ini_options": "neat"}}},
            ["tool", "pytest", "missing"],
            "deafult",
            "deafult",
        ),
        # path longer than object
        ({"a": {"b": {}}}, ["a", "b", "c"], 3, 3),
        # recurse through non-dict
        ({"a": {"b": [1, 2]}}, ["a", "b", "c"], 3, 3),
        # found key, but type mismatch
        ({"a": {"b": 3}}, ["a", "b"], [], []),
    ],
)
def test_dig(obj: dict, path: list[str], default, expected):
    assert dig(obj, path, default) == expected


@pytest.mark.parametrize(
    ["items", "expected"],
    [
        (["a", "b", "c"], False),
        (["a", "b", "c", "pytest"], True),
        ([], False),
        (["pytest=1"], True),
        (["ppytest=1"], False),
    ],
)
def test_any_pytest_str(items, expected):
    assert any_pytest_str(*items) == expected
