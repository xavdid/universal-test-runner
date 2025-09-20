# don't clear screens after tests, regardless of current environment
unexport UTR_CLEAR_PRE_RUN

_default:
    just --list

@test *options:
    uv run -- pytest {{options}}

# test against all supported python verions
@tox:
    # run a single version with tox -q -e py39
    uv run -- tox -p

@lint:
    uv run -- ruff check --quiet .
    uv run -- ruff format --check --quiet .

# lint&fix files, useful for a pre-commit hook
@lint-fix:
    uv run -- ruff check --fix --quiet .
    uv run -- ruff format --quiet .

@typecheck:
    uv run -- pyright -p pyproject.toml

# perform all checks, but don't change any files
@validate: tox lint typecheck

@release: validate
    rm -rf dist
    uv sync --group release
    uv run -- python -m build
    uv run -- python -m twine check dist/*

    # give upload api key at runtime
    python -m twine upload dist/*
