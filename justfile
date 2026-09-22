# don't clear screens after tests, regardless of current environment
unexport UTR_CLEAR_PRE_RUN

set quiet
set lazy # introduced in 1.47.0

_default:
    just --list

_test:
    uv run -- pytest --quiet

dev *args:
  uv run -- t {{ args }}

# run unit tests against all supported Python versions
[positional-arguments]
test-versions *args:
  # this handles the build and installs magically - it's very cool
  uv run -- tox -p "$@"

lint *args:
  uv run -- ruff check {{ args }}

format *args:
  uv run -- ruff format {{ args }}

typecheck:
    uv run -- pyright

# perform all checks, but don't change any files
validate: lint format typecheck test-versions

bump level: _test lint (format "--check") typecheck
  uv version --bump {{ level }}

package_version := `uv run universal-test-runner --version`
[confirm("This will release the package as written. Have you already run `just bump LEVEL`? (yN)")]
release:
  rm -rf dist
  uv build
  uv publish
  gh release create v{{ package_version }} --notes "See [the changelog](https://github.com/xavdid/potent/blob/main/CHANGELOG.md#{{ replace(package_version, ".", "") }}) for detailed information."
