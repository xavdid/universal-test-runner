default:
    just --list

# error out if this isn't being run in a venv
_require-venv:
    #!/usr/bin/env python
    import sys
    sys.exit(sys.prefix == sys.base_prefix)

test *options:
    pytest {{options}}

@tox:
    tox -p

@lint:
    isort --check --quiet .
    black --check --quiet .

# lint&fix files, useful for a pre-commit hook
@lint-fix:
    isort --quiet .
    black --quiet .

@typecheck:
    pyright -p pyproject.toml

# perform all checks, but don't change any files
@validate: tox lint typecheck

# run the full ci pipeline
ci: && validate
    pip install .[test,ci]

# useful for reinstalling after changing dependencies
@reinstall: _require-venv
    pip install -e .[test]

@release: _require-venv validate
    rm -rf dist
    pip install -e .[release]
    python -m build
    # give upload api key at runtime
    python -m twine upload --username __token__ dist/*
