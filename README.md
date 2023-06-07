# universal-test-runner

The universal test runner is a zero-configuration, language-aware way to run your unit tests.

<!-- If you're working on a JS project, it runs `[your package manager here] test`. You've run `pytest` in this folder before? `pytest` it is. Rust project? `cargo test` coming right up. -->

If you've run `pytest` in this folder before, this tool invokes `pytest`. Rust project? `cargo test` coming right up. Is also clever about running all your `go` module tests (regardless of how they're organized). No matter the command, all args are passed directly into the test runner.

Currently [supports](#supported-languages) 5 languages, with [more on the way](#upcoming-languages).

## Installation

UTR is available on PyPi:

```bash
pipx install universal-test-runner
```

## Design Philosophy

1. The runner itself should need no configuration - it Just Works
2. It should pass all arguments through to the underlying test command
3. It should have wide language and test runner support; please open an issue if your use case isn't supported!

## Usage

Once installed, the command `t` will be available. Run that in a folder with tests and it'll do its best to run your unit tests.

```
% t
====================== test session starts ======================
platform darwin -- Python 3.11.0, pytest-7.3.1, pluggy-1.0.0
rootdir: /Users/david/projects/universal-test-runner
collected 37 items

tests/test_matchers.py .........................          [ 67%]
tests/test_runner.py ............                         [100%]

====================== 37 passed in 0.04s =======================
```

If it can't guess the testing method, it will tell you so. Feel free to open an issue to request wider language support!

## Supported Languages

1. Python
   - uses `pytest` if you've run `pytest` before
   - looks for a `tests.py` file if not
2. Rust
   - `cargo test`
3. Go
   - if there's a `X_test.go`, then runs a plain `go test`
   - if you pass any args at all, runs `go test your-args-here`
   - otherwise, runs `go test ./...`
4. Elixir
   - runs `mix test`
5. Clojure
   - runs `lein test`

### Upcoming Languages

1. JS/TS
   - if there's a `package.json` and it has a `test` script, runs `[package manager] test`, where `[package manager]` is:
     - `yarn` if there's a `yarn.lock`
     - `pnpm` if there's a `pnpm-lock.yaml`
     - `npm` otherwise
2. Makefile
   - looks for a line that starts with `test:`

## Motivation

I work in a few languages at a time, so I've actually had a [version of this in my dotfiles](https://github.com/xavdid/dotfiles/blob/6bd5f56b1f9ad2dcef9f8b72413d30779b378aef/node/aliases.zsh#L45-L73) for a while. Also, as I've been doing [Exercism's #12in23 program](https://exercism.org/challenges/12in23), I'm _really_ switching languages. It's nice not to have to re-learn any muscle memory. Plus, increasingly complex `bash` was holding me back.

## Development

This section is people making changes to this package.

When in a virtual environment, run the following:

```bash
pip install -e '.[test]'
```

This installs the package in `--edit` mode and makes its dependencies available. You can now run `reddit-user-to-sqlite` to invoke the CLI.

### Running Tests

In your virtual environment, a simple `pytest` should run the unit test suite. You can also run `pyright` for type checking.

### Releasing New Versions

> these notes are mostly for myself (or other contributors)

0. ensure tests pass (`pytest`)
1. install release tooling (`pip install -e '.[release]'`)
2. build the package (`python -m build`)
3. upload the release (`python -m twine upload dist/*`)
   1. give your username as `__token__`
   2. give your password as your stored API key
   3. If you're getting invalid password, verify that `~/.pypirc` is empty
